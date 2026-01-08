import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:async';

class LauncherHomeScreen extends StatefulWidget {
  final String currentTheme;
  final Map<String, dynamic> themeColors;
  final VoidCallback onLuaActivate;

  LauncherHomeScreen({
    required this.currentTheme,
    required this.themeColors,
    required this.onLuaActivate,
  });

  @override
  _LauncherHomeScreenState createState() => _LauncherHomeScreenState();
}

class _LauncherHomeScreenState extends State<LauncherHomeScreen> {
  List<Map<String, dynamic>> installedApps = [];
  bool isLauncherEnabled = true;
  late Timer _timeTimer;
  String currentTime = '';

  @override
  void initState() {
    super.initState();
    _loadLauncherSettings();
    _loadInstalledApps();
    _updateTime();
    _timeTimer = Timer.periodic(Duration(seconds: 1), (timer) => _updateTime());
  }

  @override
  void dispose() {
    _timeTimer.cancel();
    super.dispose();
  }

  Future<void> _loadLauncherSettings() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      isLauncherEnabled = prefs.getBool('launcher_enabled') ?? true;
    });
  }

  Future<void> _toggleLauncher() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: widget.themeColors['background'][0],
        title: Text(
          'LUA Launcher Settings',
          style: TextStyle(color: widget.themeColors['text']),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Choose launcher mode:',
              style: TextStyle(color: widget.themeColors['text']),
            ),
            SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () async {
                      SharedPreferences prefs = await SharedPreferences.getInstance();
                      await prefs.setBool('launcher_enabled', false);
                      Navigator.pop(context);
                      setState(() {
                        isLauncherEnabled = false;
                      });
                      // Open default launcher selector
                      try {
                        const platform = MethodChannel('lua_assistant/system');
                        await platform.invokeMethod('openLauncherSelector');
                      } catch (e) {
                        print('Launcher selector error: $e');
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                    ),
                    child: Text('Disable\nLauncher', textAlign: TextAlign.center),
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: widget.themeColors['accent'],
                    ),
                    child: Text('Keep\nEnabled', textAlign: TextAlign.center),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _updateTime() {
    final now = DateTime.now();
    setState(() {
      currentTime = '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';
    });
  }

  Future<void> _loadInstalledApps() async {
    try {
      const platform = MethodChannel('lua_assistant/system');
      final List<dynamic> apps = await platform.invokeMethod('getInstalledApps');
      
      setState(() {
        installedApps = apps.map((app) => {
          'name': app['name'] ?? 'Unknown',
          'package': app['package'] ?? '',
          'icon': app['icon'],
        }).toList();
      });
    } catch (e) {
      print('Error loading apps: $e');
      // Fallback with common apps
      setState(() {
        installedApps = [
          {'name': 'Phone', 'package': 'com.android.dialer', 'icon': Icons.phone},
          {'name': 'Messages', 'package': 'com.android.mms', 'icon': Icons.message},
          {'name': 'Camera', 'package': 'com.android.camera2', 'icon': Icons.camera_alt},
          {'name': 'Gallery', 'package': 'com.android.gallery3d', 'icon': Icons.photo},
          {'name': 'Settings', 'package': 'com.android.settings', 'icon': Icons.settings},
          {'name': 'Chrome', 'package': 'com.android.chrome', 'icon': Icons.web},
        ];
      });
    }
  }

  Future<void> _openApp(String packageName) async {
    try {
      const platform = MethodChannel('lua_assistant/system');
      await platform.invokeMethod('openApp', {'packageName': packageName});
    } catch (e) {
      print('Error opening app: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!isLauncherEnabled) {
      return Container(); // Return empty if launcher is disabled
    }

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: widget.themeColors['background'],
            stops: [0.0, 0.5, 1.0],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildStatusBar(),
              _buildTimeWidget(),
              Expanded(child: _buildAppGrid()),
              _buildBottomDock(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusBar() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            'LUA Launcher',
            style: TextStyle(
              color: widget.themeColors['text'],
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          GestureDetector(
            onTap: _toggleLauncher,
            child: Icon(
              Icons.settings,
              color: widget.themeColors['text'],
              size: 20,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimeWidget() {
    return Container(
      padding: EdgeInsets.all(20),
      child: Column(
        children: [
          Text(
            currentTime,
            style: TextStyle(
              color: widget.themeColors['text'],
              fontSize: 48,
              fontWeight: FontWeight.w300,
              shadows: [
                Shadow(
                  color: widget.themeColors['accent'].withOpacity(0.5),
                  blurRadius: 10,
                ),
              ],
            ),
          ),
          SizedBox(height: 8),
          Text(
            _getGreeting(),
            style: TextStyle(
              color: widget.themeColors['text'].withOpacity(0.8),
              fontSize: 16,
            ),
          ),
          SizedBox(height: 16),
          GestureDetector(
            onTap: widget.onLuaActivate,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    widget.themeColors['accent'],
                    widget.themeColors['accent'].withOpacity(0.8),
                  ],
                ),
                borderRadius: BorderRadius.circular(25),
                boxShadow: [
                  BoxShadow(
                    color: widget.themeColors['accent'].withOpacity(0.3),
                    blurRadius: 10,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.mic, color: Colors.white, size: 18),
                  SizedBox(width: 8),
                  Text(
                    'Hey LUA',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppGrid() {
    return Container(
      padding: EdgeInsets.all(16),
      child: GridView.builder(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 4,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: 0.8,
        ),
        itemCount: installedApps.length,
        itemBuilder: (context, index) {
          final app = installedApps[index];
          return _buildAppIcon(app);
        },
      ),
    );
  }

  Widget _buildAppIcon(Map<String, dynamic> app) {
    return GestureDetector(
      onTap: () => _openApp(app['package']),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              gradient: RadialGradient(
                colors: [
                  widget.themeColors['accent'].withOpacity(0.2),
                  widget.themeColors['accent'].withOpacity(0.1),
                ],
              ),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(
                color: widget.themeColors['accent'].withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Icon(
              app['icon'] ?? Icons.apps,
              color: widget.themeColors['text'],
              size: 30,
            ),
          ),
          SizedBox(height: 8),
          Text(
            app['name'],
            style: TextStyle(
              color: widget.themeColors['text'],
              fontSize: 12,
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildBottomDock() {
    final dockApps = installedApps.take(4).toList();
    
    return Column(
      children: [
        // Navigation buttons
        Container(
          margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                widget.themeColors['background'][0].withOpacity(0.8),
                widget.themeColors['background'][1].withOpacity(0.7),
              ],
            ),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: widget.themeColors['text'].withOpacity(0.2),
              width: 1,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              GestureDetector(
                onTap: () {
                  // Back button
                  SystemNavigator.pop();
                },
                child: Container(
                  padding: EdgeInsets.all(8),
                  child: Icon(
                    Icons.arrow_back,
                    color: widget.themeColors['text'],
                    size: 24,
                  ),
                ),
              ),
              GestureDetector(
                onTap: () {
                  // Home button - already on home
                },
                child: Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: widget.themeColors['accent'].withOpacity(0.3),
                  ),
                  child: Icon(
                    Icons.home,
                    color: widget.themeColors['accent'],
                    size: 24,
                  ),
                ),
              ),
              GestureDetector(
                onTap: () {
                  // Recent apps
                  _showRecentApps();
                },
                child: Container(
                  padding: EdgeInsets.all(8),
                  child: Icon(
                    Icons.apps,
                    color: widget.themeColors['text'],
                    size: 24,
                  ),
                ),
              ),
              GestureDetector(
                onTap: _toggleLauncher,
                child: Container(
                  padding: EdgeInsets.all(8),
                  child: Icon(
                    Icons.settings,
                    color: widget.themeColors['text'],
                    size: 24,
                  ),
                ),
              ),
            ],
          ),
        ),
        
        // App dock
        Container(
          margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                widget.themeColors['background'][0].withOpacity(0.9),
                widget.themeColors['background'][1].withOpacity(0.8),
              ],
            ),
            borderRadius: BorderRadius.circular(25),
            border: Border.all(
              color: widget.themeColors['text'].withOpacity(0.2),
              width: 1,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: dockApps.map((app) => GestureDetector(
              onTap: () => _openApp(app['package']),
              child: Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      widget.themeColors['accent'].withOpacity(0.3),
                      widget.themeColors['accent'].withOpacity(0.1),
                    ],
                  ),
                ),
                child: Icon(
                  app['icon'] ?? Icons.apps,
                  color: widget.themeColors['text'],
                  size: 24,
                ),
              ),
            )).toList(),
          ),
        ),
      ],
    );
  }

  void _showRecentApps() {
    // Show recent apps - Android system call
    try {
      const platform = MethodChannel('lua_assistant/system');
      platform.invokeMethod('showRecentApps');
    } catch (e) {
      print('Recent apps error: $e');
    }
  }
  
  String _getGreeting() {
    final hour = DateTime.now().hour;
    switch (widget.currentTheme) {
      case 'dawn':
        return 'Good Morning! 🌅';
      case 'day':
        return 'Good Day! ☀️';
      case 'dusk':
        return 'Good Evening! 🌆';
      default:
        return 'Good Night! 🌙';
    }
  }
}