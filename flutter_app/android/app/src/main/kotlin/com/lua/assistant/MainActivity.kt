package com.lua.assistant

import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val CHANNEL = "lua_assistant/system"
    
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "openApp" -> {
                    val packageName = call.argument<String>("packageName")
                    if (packageName != null) {
                        openApp(packageName, result)
                    } else {
                        result.error("INVALID_ARGUMENT", "Package name is required", null)
                    }
                }
                "startBackgroundService" -> {
                    startBackgroundService(result)
                }
                "stopBackgroundService" -> {
                    stopBackgroundService(result)
                }
                "showFloatingIndicator" -> {
                    showFloatingIndicator(result)
                }
                "hideFloatingIndicator" -> {
                    hideFloatingIndicator(result)
                }
                "showRecentApps" -> {
                    showRecentApps(result)
                }
                "requestBatteryOptimization" -> {
                    requestBatteryOptimization(result)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }
    
    private fun openApp(packageName: String, result: MethodChannel.Result) {
        try {
            val intent = packageManager.getLaunchIntentForPackage(packageName)
            if (intent != null) {
                startActivity(intent)
                result.success("App opened successfully")
            } else {
                // Try to find app by name
                val apps = packageManager.getInstalledApplications(PackageManager.GET_META_DATA)
                val matchingApp = apps.find { 
                    it.loadLabel(packageManager).toString().lowercase().contains(packageName.lowercase())
                }
                
                if (matchingApp != null) {
                    val launchIntent = packageManager.getLaunchIntentForPackage(matchingApp.packageName)
                    if (launchIntent != null) {
                        startActivity(launchIntent)
                        result.success("App opened successfully")
                    } else {
                        result.error("APP_NOT_LAUNCHABLE", "App found but cannot be launched", null)
                    }
                } else {
                    result.error("APP_NOT_FOUND", "App not found: $packageName", null)
                }
            }
        } catch (e: Exception) {
            result.error("OPEN_APP_ERROR", "Failed to open app: ${e.message}", null)
        }
    }
    
    private fun startBackgroundService(result: MethodChannel.Result) {
        try {
            val serviceIntent = Intent(this, BackgroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
            result.success("Background service started")
        } catch (e: Exception) {
            result.error("SERVICE_ERROR", "Failed to start background service: ${e.message}", null)
        }
    }
    
    private fun stopBackgroundService(result: MethodChannel.Result) {
        try {
            val serviceIntent = Intent(this, BackgroundService::class.java)
            stopService(serviceIntent)
            result.success("Background service stopped")
        } catch (e: Exception) {
            result.error("SERVICE_ERROR", "Failed to stop background service: ${e.message}", null)
        }
    }
    
    private fun showFloatingIndicator(result: MethodChannel.Result) {
        try {
            val serviceIntent = Intent(this, FloatingIndicatorService::class.java)
            serviceIntent.action = "SHOW_INDICATOR"
            startService(serviceIntent)
            result.success("Floating indicator shown")
        } catch (e: Exception) {
            result.error("INDICATOR_ERROR", "Failed to show floating indicator: ${e.message}", null)
        }
    }
    
    private fun hideFloatingIndicator(result: MethodChannel.Result) {
        try {
            val serviceIntent = Intent(this, FloatingIndicatorService::class.java)
            serviceIntent.action = "HIDE_INDICATOR"
            startService(serviceIntent)
            result.success("Floating indicator hidden")
        } catch (e: Exception) {
            result.error("INDICATOR_ERROR", "Failed to hide floating indicator: ${e.message}", null)
        }
    }
    
    private fun showRecentApps(result: MethodChannel.Result) {
        try {
            val intent = Intent("android.intent.action.SHOW_RECENT_APPS")
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
            startActivity(intent)
            result.success("Recent apps shown")
        } catch (e: Exception) {
            // Fallback method
            try {
                val intent = Intent()
                intent.component = android.content.ComponentName(
                    "com.android.systemui",
                    "com.android.systemui.recent.RecentsActivity"
                )
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                startActivity(intent)
                result.success("Recent apps shown (fallback)")
            } catch (e2: Exception) {
                result.error("RECENT_APPS_ERROR", "Failed to show recent apps: ${e2.message}", null)
            }
        }
    }
    
    private fun requestBatteryOptimization(result: MethodChannel.Result) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                intent.data = Uri.parse("package:$packageName")
                startActivity(intent)
                result.success("Battery optimization request sent")
            } else {
                result.success("Battery optimization not needed on this Android version")
            }
        } catch (e: Exception) {
            result.error("BATTERY_ERROR", "Failed to request battery optimization: ${e.message}", null)
        }
    }
}