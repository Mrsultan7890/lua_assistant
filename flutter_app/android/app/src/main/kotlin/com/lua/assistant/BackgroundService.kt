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
import androidx.core.app.NotificationCompat
import java.util.*

class BackgroundService : Service() {
    
    companion object {
        const val CHANNEL_ID = "LUA_BACKGROUND_SERVICE"
        const val NOTIFICATION_ID = 1
    }
    
    private lateinit var notificationManager: NotificationManager
    private lateinit var handler: Handler
    private lateinit var updateRunnable: Runnable
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        notificationManager = getSystemService(NotificationManager::class.java)
        handler = Handler(Looper.getMainLooper())
        
        // Update notification every 30 minutes for theme change
        updateRunnable = object : Runnable {
            override fun run() {
                updateNotification()
                handler.postDelayed(this, 30 * 60 * 1000) // 30 minutes
            }
        }
    }
    
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
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "$content\n\n🎤 Always listening for voice commands\n📱 Tap to open LUA Assistant"
            ))
            .build()
    }
    
    private fun updateNotification() {
        val notification = createNotification()
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}