package com.lua.assistant

import android.content.Intent
import android.os.Bundle
import android.service.voice.VoiceInteractionService
import android.service.voice.VoiceInteractionSession
import android.util.Log

class LuaVoiceInteractionService : VoiceInteractionService() {
    
    companion object {
        private const val TAG = "LuaVoiceService"
    }
    
    override fun onReady() {
        super.onReady()
        Log.d(TAG, "LUA Voice Interaction Service is ready")
    }
    
    override fun onNewSession(args: Bundle?): VoiceInteractionSession {
        Log.d(TAG, "Creating new voice interaction session")
        return LuaVoiceInteractionSession(this)
    }
    
    override fun onStartListening(keyphrase: String?, extras: Bundle?) {
        super.onStartListening(keyphrase, extras)
        Log.d(TAG, "Started listening for keyphrase: $keyphrase")
        
        // Notify Flutter app about wake word detection
        val intent = Intent(this, MainActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        intent.putExtra("voice_interaction_wake", true)
        startActivity(intent)
    }
    
    override fun onStopListening() {
        super.onStopListening()
        Log.d(TAG, "Stopped listening")
    }
}