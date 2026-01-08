package com.lua.assistant

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.os.Build
import android.provider.Settings
import android.view.accessibility.AccessibilityEvent
import android.util.Log
import java.io.IOException

class SystemControlService : AccessibilityService() {
    
    companion object {
        private const val TAG = "SystemControl"
    }
    
    override fun onServiceConnected() {
        super.onServiceConnected()
        
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPES_ALL_MASK
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS or
                   AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                   AccessibilityServiceInfo.FLAG_REQUEST_ENHANCED_WEB_ACCESSIBILITY or
                   AccessibilityServiceInfo.FLAG_REQUEST_TOUCH_EXPLORATION_MODE
            notificationTimeout = 100
        }
        
        serviceInfo = info
        Log.d(TAG, "System Control Service Connected - Full System Access Enabled")
    }
    
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Monitor all system events for voice commands
    }
    
    override fun onInterrupt() {
        Log.d(TAG, "System Control Service Interrupted")
    }
    
    // System Control Functions
    fun executeSystemCommand(command: String): Boolean {
        return try {
            when (command.lowercase()) {
                "reboot" -> {
                    Runtime.getRuntime().exec("su -c 'reboot'")
                    true
                }
                "shutdown" -> {
                    Runtime.getRuntime().exec("su -c 'reboot -p'")
                    true
                }
                "screenshot" -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                        performGlobalAction(GLOBAL_ACTION_TAKE_SCREENSHOT)
                    }
                    true
                }
                "home" -> {
                    performGlobalAction(GLOBAL_ACTION_HOME)
                    true
                }
                "back" -> {
                    performGlobalAction(GLOBAL_ACTION_BACK)
                    true
                }
                "recent" -> {
                    performGlobalAction(GLOBAL_ACTION_RECENTS)
                    true
                }
                "notifications" -> {
                    performGlobalAction(GLOBAL_ACTION_NOTIFICATIONS)
                    true
                }
                "quick_settings" -> {
                    performGlobalAction(GLOBAL_ACTION_QUICK_SETTINGS)
                    true
                }
                "lock_screen" -> {
                    performGlobalAction(GLOBAL_ACTION_LOCK_SCREEN)
                    true
                }
                "power_dialog" -> {
                    performGlobalAction(GLOBAL_ACTION_POWER_DIALOG)
                    true
                }
                else -> false
            }
        } catch (e: Exception) {
            Log.e(TAG, "System command failed: ${e.message}")
            false
        }
    }
    
    fun changeSystemSettings(setting: String, value: String): Boolean {
        return try {
            when (setting) {
                "brightness" -> {
                    Settings.System.putInt(contentResolver, Settings.System.SCREEN_BRIGHTNESS, value.toInt())
                    true
                }
                "volume" -> {
                    Runtime.getRuntime().exec("su -c 'media volume --set $value'")
                    true
                }
                "wifi" -> {
                    val state = if (value == "on") "enable" else "disable"
                    Runtime.getRuntime().exec("su -c 'svc wifi $state'")
                    true
                }
                "bluetooth" -> {
                    val state = if (value == "on") "enable" else "disable"
                    Runtime.getRuntime().exec("su -c 'svc bluetooth $state'")
                    true
                }
                "airplane_mode" -> {
                    val mode = if (value == "on") "1" else "0"
                    Settings.Global.putInt(contentResolver, Settings.Global.AIRPLANE_MODE_ON, mode.toInt())
                    true
                }
                else -> false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Settings change failed: ${e.message}")
            false
        }
    }
}