package com.lua.assistant

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.Handler
import android.os.Looper
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.app.NotificationCompat
import java.util.*

class BackgroundService : Service(), RecognitionListener {
    
    companion object {
        const val CHANNEL_ID = "LUA_BACKGROUND_SERVICE"
        const val NOTIFICATION_ID = 1
    }
    
    private lateinit var notificationManager: NotificationManager
    private lateinit var handler: Handler
    private lateinit var updateRunnable: Runnable
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        notificationManager = getSystemService(NotificationManager::class.java)
        handler = Handler(Looper.getMainLooper())
        
        // Initialize speech recognizer
        initializeSpeechRecognizer()
        
        // Update notification every 30 minutes for theme change
        updateRunnable = object : Runnable {
            override fun run() {
                updateNotification()
                handler.postDelayed(this, 30 * 60 * 1000) // 30 minutes
            }
        }
    }
    
    private fun initializeSpeechRecognizer() {
        if (SpeechRecognizer.isRecognitionAvailable(this)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
            speechRecognizer?.setRecognitionListener(this)
            startListening()
        }
    }
    
    private fun startListening() {
        if (!isListening && speechRecognizer != null) {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US")
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
                putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 3000)
                putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 3000)
            }
            
            try {
                android.util.Log.d("LUA_BG_SERVICE", "Starting speech recognition...")
                speechRecognizer?.startListening(intent)
                isListening = true
            } catch (e: Exception) {
                android.util.Log.e("LUA_BG_SERVICE", "Error starting speech recognition: ${e.message}")
                // Retry after 3 seconds
                handler.postDelayed({ startListening() }, 3000)
            }
        }
    }
    
    override fun onResults(results: Bundle?) {
        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        if (matches != null && matches.isNotEmpty()) {
            val spokenText = matches[0].lowercase()
            android.util.Log.d("LUA_BG_SERVICE", "Heard: '$spokenText'")
            
            // Check for wake word
            if (spokenText.contains("hey lua") || 
                spokenText.contains("hey lula") ||
                spokenText.contains("hey loo") ||
                spokenText.contains("lua")) {
                
                android.util.Log.d("LUA_BG_SERVICE", "Wake word detected: '$spokenText'")
                
                // Wake word detected - open app
                val intent = Intent(this, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                    putExtra("wake_word_detected", true)
                }
                startActivity(intent)
            }
        }
        
        // Restart listening
        isListening = false
        handler.postDelayed({ startListening() }, 1000)
    }
    
    override fun onPartialResults(partialResults: Bundle?) {
        // Handle partial results if needed
    }
    
    override fun onError(error: Int) {
        isListening = false
        // Restart listening after error
        handler.postDelayed({ startListening() }, 2000)
    }
    
    override fun onReadyForSpeech(params: Bundle?) {}
    override fun onBeginningOfSpeech() {}
    override fun onRmsChanged(rmsdB: Float) {}
    override fun onBufferReceived(buffer: ByteArray?) {}
    override fun onEndOfSpeech() {}
    override fun onEvent(eventType: Int, params: Bundle?) {}
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
        
        // Start periodic updates
        handler.post(updateRunnable)
        
        return START_STICKY
    }
    
    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacks(updateRunnable)
        speechRecognizer?.destroy()
        speechRecognizer = null
    }
    
    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "LUA Background Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps LUA Assistant running in background"
                setShowBadge(false)
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun getThemeBasedContent(): Pair<String, String> {
        val calendar = Calendar.getInstance()
        val hour = calendar.get(Calendar.HOUR_OF_DAY)
        
        return when (hour) {
            in 5..7 -> Pair(
                "🌅 LUA Assistant - Dawn Mode",
                "Good morning! Listening for 'Hey LUA'..."
            )
            in 8..17 -> Pair(
                "☀️ LUA Assistant - Day Mode", 
                "Good day! Listening for 'Hey LUA'..."
            )
            in 18..20 -> Pair(
                "🌆 LUA Assistant - Dusk Mode",
                "Good evening! Listening for 'Hey LUA'..."
            )
            else -> Pair(
                "🌙 LUA Assistant - Night Mode",
                "Good night! Listening for 'Hey LUA'..."
            )
        }
    }
    
    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val (title, content) = getThemeBasedContent()
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(content)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "$content\n\n🎤 Always listening for voice commands\n📱 Tap to open LUA Assistant\n🔊 Say 'Hey LUA' to activate"
            ))
            .build()
    }
    
    private fun updateNotification() {
        val notification = createNotification()
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}