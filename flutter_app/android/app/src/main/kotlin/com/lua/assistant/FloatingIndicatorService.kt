package com.lua.assistant

import android.app.Service
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.ImageView
import android.widget.TextView
import java.util.*

class FloatingIndicatorService : Service() {
    
    private lateinit var windowManager: WindowManager
    private var floatingView: View? = null
    private var isShowing = false
    
    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            "SHOW_INDICATOR" -> showFloatingIndicator()
            "HIDE_INDICATOR" -> hideFloatingIndicator()
            "UPDATE_THEME" -> updateIndicatorTheme()
        }
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private fun showFloatingIndicator() {
        if (isShowing) return
        
        try {
            val inflater = LayoutInflater.from(this)
            floatingView = inflater.inflate(android.R.layout.simple_list_item_2, null)
            
            // Configure the floating view
            val textView1 = floatingView?.findViewById<TextView>(android.R.id.text1)
            val textView2 = floatingView?.findViewById<TextView>(android.R.id.text2)
            
            val (title, subtitle) = getThemeBasedContent()
            textView1?.text = title
            textView2?.text = subtitle
            
            // Set layout parameters
            val layoutFlag = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            } else {
                WindowManager.LayoutParams.TYPE_PHONE
            }
            
            val params = WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                layoutFlag,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
            )
            
            params.gravity = Gravity.TOP or Gravity.END
            params.x = 0
            params.y = 100
            
            windowManager.addView(floatingView, params)
            isShowing = true
            
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun hideFloatingIndicator() {
        if (!isShowing || floatingView == null) return
        
        try {
            windowManager.removeView(floatingView)
            floatingView = null
            isShowing = false
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun updateIndicatorTheme() {
        if (!isShowing || floatingView == null) return
        
        val textView1 = floatingView?.findViewById<TextView>(android.R.id.text1)
        val textView2 = floatingView?.findViewById<TextView>(android.R.id.text2)
        
        val (title, subtitle) = getThemeBasedContent()
        textView1?.text = title
        textView2?.text = subtitle
    }
    
    private fun getThemeBasedContent(): Pair<String, String> {
        val calendar = Calendar.getInstance()
        val hour = calendar.get(Calendar.HOUR_OF_DAY)
        
        return when (hour) {
            in 5..7 -> Pair("🌅 LUA", "Dawn Mode")
            in 8..17 -> Pair("☀️ LUA", "Day Mode")
            in 18..20 -> Pair("🌆 LUA", "Dusk Mode")
            else -> Pair("🌙 LUA", "Night Mode")
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        hideFloatingIndicator()
    }
}