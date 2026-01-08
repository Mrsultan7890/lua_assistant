package com.lua.assistant

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.view.accessibility.AccessibilityEvent
import android.os.Bundle

class LuaAccessibilityService : AccessibilityService(), RecognitionListener {
    
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false
    private val handler = Handler(Looper.getMainLooper())
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        android.util.Log.d("LUA_ACCESSIBILITY", "Service connected")
        initializeSpeechRecognizer()
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
            }
            
            try {
                speechRecognizer?.startListening(intent)
                isListening = true
                android.util.Log.d("LUA_ACCESSIBILITY", "Started listening")
            } catch (e: Exception) {
                android.util.Log.e("LUA_ACCESSIBILITY", "Error starting speech: ${e.message}")
                handler.postDelayed({ startListening() }, 3000)
            }
        }
    }
    
    override fun onResults(results: Bundle?) {
        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        if (matches != null && matches.isNotEmpty()) {
            val spokenText = matches[0].lowercase()
            android.util.Log.d("LUA_ACCESSIBILITY", "Heard: '$spokenText'")
            
            if (spokenText.contains("hey lua") || 
                spokenText.contains("hey lula") ||
                spokenText.contains("lua")) {
                
                android.util.Log.d("LUA_ACCESSIBILITY", "Wake word detected!")
                openLuaApp()
            }
        }
        
        isListening = false
        handler.postDelayed({ startListening() }, 1000)
    }
    
    private fun openLuaApp() {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("accessibility_wake_word", true)
        }
        startActivity(intent)
    }
    
    override fun onPartialResults(partialResults: Bundle?) {}
    override fun onError(error: Int) {
        android.util.Log.e("LUA_ACCESSIBILITY", "Speech error: $error")
        isListening = false
        handler.postDelayed({ startListening() }, 2000)
    }
    
    override fun onReadyForSpeech(params: Bundle?) {}
    override fun onBeginningOfSpeech() {}
    override fun onRmsChanged(rmsdB: Float) {}
    override fun onBufferReceived(buffer: ByteArray?) {}
    override fun onEndOfSpeech() {}
    override fun onEvent(eventType: Int, params: Bundle?) {}
    
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Required by AccessibilityService but not used for voice recognition
    }
    
    override fun onInterrupt() {
        android.util.Log.d("LUA_ACCESSIBILITY", "Service interrupted")
    }
    
    override fun onDestroy() {
        super.onDestroy()
        speechRecognizer?.destroy()
        speechRecognizer = null
    }
}