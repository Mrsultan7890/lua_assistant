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
            }\n            \n            val params = WindowManager.LayoutParams(\n                WindowManager.LayoutParams.WRAP_CONTENT,\n                WindowManager.LayoutParams.WRAP_CONTENT,\n                layoutFlag,\n                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,\n                PixelFormat.TRANSLUCENT\n            )\n            \n            params.gravity = Gravity.TOP or Gravity.END\n            params.x = 0\n            params.y = 100\n            \n            windowManager.addView(floatingView, params)\n            isShowing = true\n            \n        } catch (e: Exception) {\n            e.printStackTrace()\n        }\n    }\n    \n    private fun hideFloatingIndicator() {\n        if (!isShowing || floatingView == null) return\n        \n        try {\n            windowManager.removeView(floatingView)\n            floatingView = null\n            isShowing = false\n        } catch (e: Exception) {\n            e.printStackTrace()\n        }\n    }\n    \n    private fun updateIndicatorTheme() {\n        if (!isShowing || floatingView == null) return\n        \n        val textView1 = floatingView?.findViewById<TextView>(android.R.id.text1)\n        val textView2 = floatingView?.findViewById<TextView>(android.R.id.text2)\n        \n        val (title, subtitle) = getThemeBasedContent()\n        textView1?.text = title\n        textView2?.text = subtitle\n    }\n    \n    private fun getThemeBasedContent(): Pair<String, String> {\n        val calendar = Calendar.getInstance()\n        val hour = calendar.get(Calendar.HOUR_OF_DAY)\n        \n        return when (hour) {\n            in 5..7 -> Pair(\"🌅 LUA\", \"Dawn Mode\")\n            in 8..17 -> Pair(\"☀️ LUA\", \"Day Mode\")\n            in 18..20 -> Pair(\"🌆 LUA\", \"Dusk Mode\")\n            else -> Pair(\"🌙 LUA\", \"Night Mode\")\n        }\n    }\n    \n    override fun onDestroy() {\n        super.onDestroy()\n        hideFloatingIndicator()\n    }\n}