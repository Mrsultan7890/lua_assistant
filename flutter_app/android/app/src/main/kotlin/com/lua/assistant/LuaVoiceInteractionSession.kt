package com.lua.assistant

import android.content.Context
import android.os.Bundle
import android.service.voice.VoiceInteractionSession
import android.util.Log

class LuaVoiceInteractionSession(context: Context) : VoiceInteractionSession(context) {
    
    companion object {
        private const val TAG = "LuaVoiceSession"
    }
    
    override fun onShow(args: Bundle?, showFlags: Int) {
        super.onShow(args, showFlags)
        Log.d(TAG, "Voice interaction session shown")
        
        // Launch LUA Assistant
        val intent = android.content.Intent(context, MainActivity::class.java)
        intent.flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
        intent.putExtra("voice_session_active", true)
        context.startActivity(intent)
    }
    
    override fun onHide() {
        super.onHide()
        Log.d(TAG, "Voice interaction session hidden")
    }
    
    override fun onHandleAssist(data: Bundle?) {
        super.onHandleAssist(data)
        Log.d(TAG, "Handling assist request")
        
        // Show LUA Assistant interface
        show(data, 0)
    }
}