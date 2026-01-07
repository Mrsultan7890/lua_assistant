package com.lua.assistant

import android.content.Intent
import android.net.Uri
import android.provider.MediaStore
import android.provider.AlarmClock
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val CAMERA_CHANNEL = "lua_assistant/camera"
    private val REMINDER_CHANNEL = "lua_assistant/reminder"
    private val SYSTEM_CHANNEL = "lua_assistant/system"
    
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        // Camera channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CAMERA_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "openCamera" -> {
                        val mode = call.argument<String>("mode") ?: "default"
                        openCamera(mode, result)
                    }
                    else -> result.notImplemented()
                }
            }
        
        // Reminder channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, REMINDER_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "setReminder" -> {
                        val title = call.argument<String>("title") ?: "Reminder"
                        val time = call.argument<String>("time") ?: "now"
                        setReminder(title, time, result)
                    }
                    else -> result.notImplemented()
                }
            }
        
        // System channel
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, SYSTEM_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "openApp" -> {
                        val packageName = call.argument<String>("packageName") ?: ""
                        openApp(packageName, result)
                    }
                    else -> result.notImplemented()
                }
            }
    }
    
    private fun openCamera(mode: String, result: MethodChannel.Result) {
        try {
            val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            
            if (mode == "front") {
                intent.putExtra("android.intent.extras.CAMERA_FACING", 1)
            }
            
            if (intent.resolveActivity(packageManager) != null) {
                startActivity(intent)
                result.success("Camera opened")
            } else {
                result.error("NO_CAMERA", "Camera app not found", null)
            }
        } catch (e: Exception) {
            result.error("CAMERA_ERROR", e.message, null)
        }
    }
    
    private fun setReminder(title: String, time: String, result: MethodChannel.Result) {
        try {
            val intent = Intent(AlarmClock.ACTION_SET_ALARM).apply {
                putExtra(AlarmClock.EXTRA_MESSAGE, title)
                putExtra(AlarmClock.EXTRA_SKIP_UI, true)
            }
            
            if (intent.resolveActivity(packageManager) != null) {
                startActivity(intent)
                result.success("Reminder set")
            } else {
                result.error("NO_ALARM", "Alarm app not found", null)
            }
        } catch (e: Exception) {
            result.error("REMINDER_ERROR", e.message, null)
        }
    }
    
    private fun openApp(packageName: String, result: MethodChannel.Result) {
        try {
            val intent = packageManager.getLaunchIntentForPackage(packageName)
            if (intent != null) {
                startActivity(intent)
                result.success("App opened")
            } else {
                result.error("APP_NOT_FOUND", "App not installed: $packageName", null)
            }
        } catch (e: Exception) {
            result.error("APP_ERROR", e.message, null)
        }
    }
}