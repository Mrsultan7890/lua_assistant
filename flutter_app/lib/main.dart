import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:permission_handler/permission_handler.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:async';
import 'dart:io';

void main() {
  runApp(LuaApp());
}

class LuaApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LUA Assistant',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        primaryColor: Color(0xFF1a237e),
        scaffoldBackgroundColor: Color(0xFF0d1421),
        cardColor: Color(0xFF1e2746),
        textTheme: TextTheme(
          bodyLarge: TextStyle(color: Colors.white),
          bodyMedium: TextStyle(color: Colors.white70),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: Color(0xFF1a237e),
          foregroundColor: Colors.white,
        ),
      ),
      home: LuaHomePage(),
    );
  }
}

class LuaHomePage extends StatefulWidget {
  @override
  _LuaHomePageState createState() => _LuaHomePageState();
}

class _LuaHomePageState extends State<LuaHomePage>
    with TickerProviderStateMixin {
  
  // Core components
  late stt.SpeechToText _speech;
  late FlutterTts _flutterTts;
  
  // State variables
  bool _isListening = false;
  bool _isAlwaysListening = false;
  bool _isInitialized = false;
  bool _speechAvailable = false; // Track if speech is actually available
  String _text = 'Initializing...';
  String _response = '';
  double _confidence = 1.0;
  
  // Animation controllers
  late AnimationController _pulseController;
  late AnimationController _waveController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _waveAnimation;
  
  // Theme variables
  late Timer _themeTimer;
  String _currentTheme = 'night'; // night, dawn, day, dusk
  
  // Backend configuration
  String _backendUrl = 'https://socialcoddy.run.place';
  String _userId = 'default';
  
  // Statistics
  int _totalCommands = 0;
  List<Map<String, dynamic>> _recentCommands = [];
  
  @override
  void initState() {
    super.initState();
    _initializeApp();
  }
  
  @override
  void dispose() {
    _pulseController.dispose();
    _waveController.dispose();
    _themeTimer.cancel();
    _stopAlwaysListening();
    super.dispose();
  }
  
  Future<void> _initializeApp() async {
    await _requestPermissions();
    await _initializeSpeech();
    await _initializeTTS();
    await _loadSettings();
    _setupAnimations();
    _setupThemeTimer();
    
    setState(() {
      _isInitialized = true;
    });
    
    // Start background service for notification only
    await _startBackgroundService();
    
    // Auto-start Flutter speech recognition if available
    if (_speechAvailable) {
      print('Starting always listening mode...');
      _startAlwaysListening();
    } else {
      print('Speech not available');
    }
  }
  
  Future<void> _startBackgroundService() async {
    try {
      const platform = MethodChannel('lua_assistant/system');
      
      // Set up wake word detection listeners
      platform.setMethodCallHandler((call) async {
        if (call.method == 'wakeWordDetected') {
          print('Wake word detected by background service!');
          _handleBackgroundWakeWord();
        } else if (call.method == 'accessibilityWakeWord') {
          print('Wake word detected by accessibility service!');
          _handleAccessibilityWakeWord();
        }
      });
      
      await platform.invokeMethod('startBackgroundService');
      await platform.invokeMethod('requestBatteryOptimization');
      
      // Enable accessibility service for true background listening
      await platform.invokeMethod('enableAccessibilityService');
      
      print('Background service started for notification');
    } catch (e) {
      print('Background service error: $e');
    }
  }
  
  void _handleAccessibilityWakeWord() {
    print('Handling accessibility wake word detection...');
    
    if (mounted) {
      setState(() {
        _text = 'LUA activated by accessibility! What can I do for you?';
        _response = '';
      });
    }
    
    _speak('Yes, I\'m listening! How can I help you?');
    
    Timer(Duration(seconds: 2), () {
      _listenForCommand();
    });
  }
  
  void _handleBackgroundWakeWord() {
    print('Handling background wake word detection...');
    
    // Stop any existing Flutter speech recognition to avoid conflicts
    if (_isListening) {
      _speech.stop();
    }
    
    // Activate assistant immediately
    if (mounted) {
      setState(() {
        _isAlwaysListening = false; // Background service handles wake word
        _isListening = false;
        _text = 'LUA activated from background! What can I do for you?';
        _response = '';
      });
    }
    
    // Speak activation message
    _speak('Yes, I\'m here! How can I help you?');
    
    // Start listening for command after a short delay
    Timer(Duration(seconds: 2), () {
      _listenForCommand();
    });
  }
  
  Future<void> _requestPermissions() async {
    print('Requesting permissions...');
    
    var micStatus = await Permission.microphone.request();
    print('Microphone permission: $micStatus');
    
    if (micStatus != PermissionStatus.granted) {
      _showError('Microphone permission is required for voice recognition');
      print('Microphone permission denied');
    }
    
    await Permission.phone.request();
    await Permission.sms.request();
    await Permission.camera.request();
    await Permission.storage.request();
    
    print('All permissions requested');
  }
  
  Future<void> _initializeSpeech() async {
    try {
      _speech = stt.SpeechToText();
      print('Initializing speech recognition...');
      
      bool? available = await _speech.initialize(
        onStatus: _onSpeechStatus,
        onError: _onSpeechError,
      );
      
      // Handle null case properly
      available = available ?? false;
      
      print('Speech recognition available: $available');
      
      if (mounted) {
        setState(() {
          _speechAvailable = available ?? false;
          if (available ?? false) {
            _text = 'Ready! Say "Hey LUA" or tap Test Speech';
          } else {
            _text = 'Speech not available. Use Test Speech button';
          }
        });
      }
      
      if (!available) {
        _showError('Speech recognition not available - using fallback mode');
        print('Speech recognition initialization failed');
      } else {
        print('Speech recognition initialized successfully');
      }
    } catch (e) {
      print('Speech initialization error: $e');
      if (mounted) {
        setState(() {
          _speechAvailable = false;
          _text = 'Speech error. Use Test Speech button';
        });
      }
      _showError('Speech initialization failed: $e');
    }
  }
  
  Future<void> _initializeTTS() async {
    _flutterTts = FlutterTts();
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setPitch(1.0);
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setVolume(0.8);
  }
  
  Future<void> _loadSettings() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _backendUrl = prefs.getString('backend_url') ?? 'https://socialcoddy.run.place';
    _userId = prefs.getString('user_id') ?? 'user_${DateTime.now().millisecondsSinceEpoch}';
    _totalCommands = prefs.getInt('total_commands') ?? 0;
    
    await prefs.setString('user_id', _userId);
  }
  
  void _setupAnimations() {
    _pulseController = AnimationController(
      duration: Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _waveController = AnimationController(
      duration: Duration(milliseconds: 2000),
      vsync: this,
    );
    
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    
    _waveAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _waveController, curve: Curves.easeInOut),
    );
    
    _pulseController.repeat(reverse: true);
  }
  
  void _setupThemeTimer() {
    _updateTheme(); // Set initial theme
    _themeTimer = Timer.periodic(Duration(minutes: 30), (timer) {
      _updateTheme();
    });
  }
  
  void _updateTheme() {
    final now = DateTime.now();
    final hour = now.hour;
    
    String newTheme;
    if (hour >= 5 && hour < 8) {
      newTheme = 'dawn'; // Dawn: 5-8 AM
    } else if (hour >= 8 && hour < 18) {
      newTheme = 'day'; // Day: 8 AM - 6 PM
    } else if (hour >= 18 && hour < 21) {
      newTheme = 'dusk'; // Dusk: 6-9 PM
    } else {
      newTheme = 'night'; // Night: 9 PM - 5 AM
    }
    
    if (newTheme != _currentTheme) {
      setState(() {
        _currentTheme = newTheme;
      });
    }
  }
  
  Map<String, dynamic> _getThemeColors() {
    switch (_currentTheme) {
      case 'dawn':
        return {
          'background': [Color(0xFF2d1b69), Color(0xFF11998e), Color(0xFFf093fb)],
          'moon': [Color(0xFFffd89b), Color(0xFF19547b)],
          'text': Color(0xFFffd89b),
          'accent': Color(0xFFf093fb),
          'icon': Icons.wb_twilight,
        };
      case 'day':
        return {
          'background': [Color(0xFF74b9ff), Color(0xFF0984e3), Color(0xFFfdcb6e)],
          'moon': [Color(0xFFfdcb6e), Color(0xFFe17055)], // Sun colors
          'text': Color(0xFF2d3436),
          'accent': Color(0xFFe17055),
          'icon': Icons.wb_sunny,
        };
      case 'dusk':
        return {
          'background': [Color(0xFF667eea), Color(0xFF764ba2), Color(0xFFf093fb)],
          'moon': [Color(0xFFfd79a8), Color(0xFFfdcb6e)],
          'text': Color(0xFFdda0dd),
          'accent': Color(0xFFfd79a8),
          'icon': Icons.wb_twilight,
        };
      default: // night
        return {
          'background': [Color(0xFF0a0a2e), Color(0xFF16213e), Color(0xFF0f3460)],
          'moon': [Color(0xFFf5f5dc), Color(0xFFe6e6fa), Color(0xFFd3d3d3)],
          'text': Color(0xFFf5f5dc),
          'accent': Color(0xFF00bcd4),
          'icon': Icons.nightlight_round,
        };
    }
  }
  
  void _onSpeechStatus(String status) {
    print('Speech status: $status');
    
    if (status == 'notListening' && _isAlwaysListening) {
      Timer(Duration(milliseconds: 500), () {
        if (_isAlwaysListening) {
          _startAlwaysListening();
        }
      });
    }
  }
  
  void _onSpeechError(dynamic error) {
    print('Speech error: $error');
    if (_isAlwaysListening) {
      Timer(Duration(seconds: 2), () => _startAlwaysListening());
    }
  }
  
  Future<void> _startAlwaysListening() async {
    if (!_speechAvailable) return;
    
    if (mounted) {
      setState(() {
        _isAlwaysListening = true;
        _isListening = true;
        _text = 'Listening for "Hey LUA"...';
      });
    }
    
    _waveController.repeat();
    
    try {
      await _speech.listen(
        onResult: _onAlwaysListeningResult,
        listenFor: Duration(seconds: 30),
        pauseFor: Duration(seconds: 1),
        cancelOnError: false,
        partialResults: true,
      );
    } catch (e) {
      print('Speech error: $e');
      if (_isAlwaysListening) {
        Timer(Duration(seconds: 1), () => _startAlwaysListening());
      }
    }
  }
  
  void _onAlwaysListeningResult(result) {
    String recognizedWords = result.recognizedWords.toLowerCase();
    print('Recognized: "$recognizedWords"');
    
    // Check for wake word
    if (recognizedWords.contains('hey lua') || 
        recognizedWords.contains('hey lula') ||
        recognizedWords.contains('lua')) {
      print('Wake word detected!');
      _activateAssistant();
      return;
    }
    
    // Restart listening immediately after each result
    if (_isAlwaysListening && result.finalResult) {
      Timer(Duration(milliseconds: 100), () {
        if (_isAlwaysListening) {
          _startAlwaysListening();
        }
      });
    }
  }
  
  void _activateAssistant() {
    // Stop always listening temporarily
    if (mounted) {
      setState(() {
        _isAlwaysListening = false;
        _isListening = false;
        _text = 'LUA activated! What can I do for you?';
      });
    }
    
    _waveController.stop();
    _speech.stop();
    
    _speak('Yes, how can I help you?');
    _pulseController.forward();
    
    Timer(Duration(seconds: 2), () => _listenForCommand());
  }
  
  Future<void> _listenForCommand() async {
    if (mounted) {
      setState(() {
        _isListening = true;
        _text = 'Listening for your command...';
      });
    }
    
    try {
      await _speech.listen(
        onResult: (result) {
          if (result.finalResult) {
            _processVoiceCommand(result.recognizedWords);
          } else {
            if (mounted) {
              setState(() {
                _text = result.recognizedWords;
                _confidence = result.confidence;
              });
            }
          }
        },
        listenFor: Duration(seconds: 15),
        pauseFor: Duration(seconds: 2),
        cancelOnError: false,
        partialResults: true,
        onSoundLevelChange: (level) {
          if (level > 0.2) {
            print('Command sound detected: $level');
          }
        },
      );
    } catch (e) {
      print('Command listen error: $e');
      Timer(Duration(seconds: 2), () => _startAlwaysListening());
    }
  }
  
  void _stopAlwaysListening() {
    if (mounted) {
      setState(() {
        _isAlwaysListening = false;
        _isListening = false;
        _text = 'LUA is sleeping. Tap to wake up.';
      });
    }
    
    _speech.stop();
    _waveController.stop();
    _pulseController.reset();
  }
  
  Future<void> _processVoiceCommand(String command) async {
    if (command.trim().isEmpty) return;
    
    if (mounted) {
      setState(() {
        _text = command;
        _response = 'Processing...';
      });
    }
    
    try {
      final response = await http.post(
        Uri.parse('$_backendUrl/api/process_voice'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'text': command,
          'user_id': _userId,
          'context': {
            'timestamp': DateTime.now().toIso8601String(),
            'app_state': 'active'
          }
        }),
      );
      
      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        await _handleCommandResult(result);
        _updateStats(command, result);
        
        if (result.containsKey('emotion')) {
          final emotion = result['emotion'];
          _showEmotionalResponse(emotion);
        }
      } else {
        _showError('Backend connection failed');
      }
    } catch (e) {
      _showError('Error: $e');
    }
    
    Timer(Duration(seconds: 5), () {
      if (mounted) {
        setState(() {
          _isListening = false;
        });
      }
      _startAlwaysListening();
    });
  }
  
  Future<void> _handleCommandResult(Map<String, dynamic> result) async {
    String responseText = result['response'] ?? 'Command executed';
    String action = result['action'] ?? 'unknown';
    
    setState(() {
      _response = responseText;
    });
    
    await _speak(responseText);
    
    // Show execution status
    print('Executing action: $action');
    
    try {
      switch (action) {
        case 'make_call':
          await _makeCall(result['phone_number'] ?? result['contact_name']);
          _showSuccess('Call initiated');
          break;
        case 'send_sms':
          await _sendSMS(result['contact'], result['message']);
          _showSuccess('SMS app opened');
          break;
        case 'open_app':
          await _openApp(result['package'] ?? result['app_name']);
          _showSuccess('App launched');
          break;
        case 'play_music':
        case 'pause_music':
        case 'next_track':
        case 'previous_track':
          await _controlMusic(action);
          _showSuccess('Music control executed');
          break;
        case 'open_camera':
          await _openCamera(result['mode'] ?? 'default');
          _showSuccess('Camera opened');
          break;
        case 'set_reminder':
          await _setReminder(result['title'], result['time']);
          _showSuccess('Reminder set');
          break;
        case 'unknown':
          _showError('Command not recognized');
          break;
        default:
          print('Action executed: $action');
      }
    } catch (e) {
      _showError('Failed to execute: $e');
      print('Execution error: $e');
    }
  }
  
  Future<void> _makeCall(String contact) async {
    try {
      String url = 'tel:$contact';
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url));
      } else {
        _showError('Cannot make call');
      }
    } catch (e) {
      _showError('Call failed: $e');
    }
  }
  
  Future<void> _sendSMS(String contact, String message) async {
    try {
      String url = 'sms:$contact?body=${Uri.encodeComponent(message)}';
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url));
      } else {
        _showError('Cannot send SMS');
      }
    } catch (e) {
      _showError('SMS failed: $e');
    }
  }
  
  Future<void> _openApp(String appIdentifier) async {
    try {
      // Use platform channel for app opening
      const platform = MethodChannel('lua_assistant/system');
      await platform.invokeMethod('openApp', {'packageName': appIdentifier});
    } catch (e) {
      _showError('Could not open app: $appIdentifier');
    }
  }
  
  Future<void> _controlMusic(String action) async {
    try {
      String intent;
      switch (action) {
        case 'play_music':
          intent = 'android.intent.action.MUSIC_PLAYER';
          break;
        case 'pause_music':
          intent = 'android.media.AUDIO_BECOMING_NOISY';
          break;
        default:
          intent = 'android.intent.action.MUSIC_PLAYER';
      }
      
      if (await canLaunchUrl(Uri.parse('intent://music'))) {
        await launchUrl(Uri.parse('intent://music'));
      } else {
        // Try to open default music app
        await _openApp('music');
      }
    } catch (e) {
      _showError('Music control failed: $e');
    }
  }
  
  Future<void> _openCamera(String mode) async {
    try {
      String url = 'intent://camera';
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url));
      } else {
        await _openApp('camera');
      }
    } catch (e) {
      _showError('Camera failed: $e');
    }
  }
  
  Future<void> _setReminder(String title, String time) async {
    try {
      String url = 'intent://reminder?title=${Uri.encodeComponent(title)}&time=${Uri.encodeComponent(time)}';
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url));
      } else {
        _showError('Please set reminder manually: $title at $time');
      }
    } catch (e) {
      _showError('Reminder failed: $e');
    }
  }
  
  Future<void> _speak(String text) async {
    try {
      await _flutterTts.speak(text);
    } catch (e) {
      print('TTS error: $e');
    }
  }
  
  void _updateStats(String command, Map<String, dynamic> result) {
    setState(() {
      _totalCommands++;
      _recentCommands.insert(0, {
        'command': command,
        'response': result['response'],
        'timestamp': DateTime.now(),
        'success': result['action'] != 'unknown',
      });
      
      if (_recentCommands.length > 10) {
        _recentCommands.removeLast();
      }
    });
    
    _saveStats();
  }
  
  Future<void> _saveStats() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setInt('total_commands', _totalCommands);
  }
  
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }
  
  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: Color(0xFF00bcd4)),
              SizedBox(height: 20),
              Text(
                'Initializing LUA...',
                style: TextStyle(color: Colors.white, fontSize: 18),
              ),
            ],
          ),
        ),
      );
    }
    
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: _getThemeColors()['background'],
            stops: [0.0, 0.5, 1.0],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildHeader(),
              Expanded(child: _buildVoiceInterface()),
              _buildQuickActions(),
              _buildControlPanel(),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildHeader() {
    final themeColors = _getThemeColors();
    
    return Container(
      padding: EdgeInsets.all(16),
      child: Row(
        children: [
          // Dynamic time-based icon with glow effect
          Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [
                  themeColors['text'].withOpacity(0.3),
                  themeColors['text'].withOpacity(0.1),
                ],
              ),
              boxShadow: [
                BoxShadow(
                  color: themeColors['accent'].withOpacity(0.4),
                  blurRadius: 15,
                  spreadRadius: 3,
                ),
              ],
            ),
            child: Icon(
              themeColors['icon'],
              color: themeColors['text'],
              size: 28,
            ),
          ),
          SizedBox(width: 12),
          Text(
            'LUA',
            style: TextStyle(
              color: themeColors['text'],
              fontSize: 28,
              fontWeight: FontWeight.bold,
              shadows: [
                Shadow(
                  color: themeColors['accent'].withOpacity(0.5),
                  blurRadius: 10,
                ),
              ],
            ),
          ),
          SizedBox(width: 8),
          // Removed emoji for cleaner look
          Spacer(),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: _isAlwaysListening 
                    ? [Color(0xFF4caf50), Color(0xFF66bb6a)]
                    : [Color(0xFFf44336), Color(0xFFef5350)],
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: (_isAlwaysListening ? Colors.green : Colors.red).withOpacity(0.3),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Text(
              _isAlwaysListening ? 'ACTIVE' : 'SLEEPING',
              style: TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildVoiceInterface() {
    final themeColors = _getThemeColors();
    
    return Container(
      padding: EdgeInsets.all(20),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Dynamic Sky with Moon/Sun Design
          Container(
            width: 280,
            height: 280,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: themeColors['background'],
              ),
              boxShadow: [
                BoxShadow(
                  color: themeColors['accent'].withOpacity(0.3),
                  blurRadius: 30,
                  spreadRadius: 10,
                ),
              ],
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Dynamic background elements (stars for night, clouds for day)
                if (_currentTheme == 'night') ...
                  List.generate(15, (index) => Positioned(
                    top: (index * 17.0) % 200 + 20,
                    left: (index * 23.0) % 200 + 20,
                    child: Container(
                      width: 2,
                      height: 2,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.8),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ))
                else if (_currentTheme == 'day') ...
                  List.generate(8, (index) => Positioned(
                    top: (index * 25.0) % 180 + 30,
                    left: (index * 35.0) % 180 + 30,
                    child: Container(
                      width: 20 + (index % 3) * 5,
                      height: 12 + (index % 2) * 3,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.6),
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  )),
                
                // Animated glow rings
                if (_isListening) ...[
                  AnimatedBuilder(
                    animation: _waveAnimation,
                    builder: (context, child) {
                      return Container(
                        width: 200 + (_waveAnimation.value * 40),
                        height: 200 + (_waveAnimation.value * 40),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: themeColors['text'].withOpacity(0.3),
                            width: 1,
                          ),
                        ),
                      );
                    },
                  ),
                  
                  AnimatedBuilder(
                    animation: _waveAnimation,
                    builder: (context, child) {
                      return Container(
                        width: 160 + (_waveAnimation.value * 25),
                        height: 160 + (_waveAnimation.value * 25),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: themeColors['text'].withOpacity(0.5),
                            width: 1,
                          ),
                        ),
                      );
                    },
                  ),
                ],
                
                // Main Moon/Sun
                AnimatedBuilder(
                  animation: _pulseAnimation,
                  builder: (context, child) {
                    return Transform.scale(
                      scale: _isListening ? _pulseAnimation.value : 1.0,
                      child: Container(
                        width: 120,
                        height: 120,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: RadialGradient(
                            colors: themeColors['moon'],
                            stops: [0.0, 0.7, 1.0],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: themeColors['text'].withOpacity(0.8),
                              blurRadius: 25,
                              spreadRadius: 8,
                            ),
                            BoxShadow(
                              color: themeColors['accent'].withOpacity(0.4),
                              blurRadius: 40,
                              spreadRadius: 15,
                            ),
                          ],
                        ),
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            // Surface details (craters for moon, rays for sun)
                            if (_currentTheme == 'night') ...[
                              Positioned(
                                top: 25, left: 30,
                                child: Container(
                                  width: 8, height: 8,
                                  decoration: BoxDecoration(
                                    color: Color(0xFFd3d3d3).withOpacity(0.6),
                                    shape: BoxShape.circle,
                                  ),
                                ),
                              ),
                              Positioned(
                                top: 45, right: 25,
                                child: Container(
                                  width: 6, height: 6,
                                  decoration: BoxDecoration(
                                    color: Color(0xFFd3d3d3).withOpacity(0.4),
                                    shape: BoxShape.circle,
                                  ),
                                ),
                              ),
                            ],
                            
                            // Microphone icon
                            Icon(
                              _isListening ? Icons.mic : Icons.mic_off,
                              size: 40,
                              color: _currentTheme == 'day' ? Colors.white : Color(0xFF4a4a4a),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
          
          SizedBox(height: 30),
          
          // Text container with dynamic theme
          Container(
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  themeColors['background'][0].withOpacity(0.9),
                  themeColors['background'][1].withOpacity(0.8),
                ],
              ),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: themeColors['text'].withOpacity(0.3),
                width: 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: themeColors['accent'].withOpacity(0.1),
                  blurRadius: 15,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Column(
              children: [
                Text(
                  _text,
                  style: TextStyle(
                    fontSize: 16,
                    color: themeColors['text'],
                    fontWeight: FontWeight.w500,
                    shadows: [
                      Shadow(
                        color: themeColors['accent'].withOpacity(0.5),
                        blurRadius: 10,
                      ),
                    ],
                  ),
                  textAlign: TextAlign.center,
                ),
                
                if (_response.isNotEmpty) ...[
                  SizedBox(height: 10),
                  Divider(color: themeColors['text'].withOpacity(0.3)),
                  SizedBox(height: 10),
                  Text(
                    _response,
                    style: TextStyle(
                      fontSize: 14,
                      color: themeColors['accent'],
                      shadows: [
                        Shadow(
                          color: themeColors['accent'].withOpacity(0.5),
                          blurRadius: 8,
                        ),
                      ],
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                
                if (_isListening && _confidence < 1.0) ...[
                  SizedBox(height: 10),
                  LinearProgressIndicator(
                    value: _confidence,
                    backgroundColor: themeColors['background'][0],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      themeColors['text'],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildQuickActions() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          Text(
            'Quick Commands',
            style: TextStyle(
              fontSize: 16,
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildQuickAction(Icons.phone, 'Call', () {
                _processVoiceCommand('make a call');
              }),
              _buildQuickAction(Icons.message, 'Message', () {
                _processVoiceCommand('send a message');
              }),
              _buildQuickAction(Icons.alarm, 'Reminder', () {
                _processVoiceCommand('set a reminder');
              }),
              _buildQuickAction(Icons.music_note, 'Music', () {
                _processVoiceCommand('play music');
              }),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildQuickAction(IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Color(0xFF1e2746),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Color(0xFF00bcd4).withOpacity(0.3),
          ),
        ),
        child: Column(
          children: [
            Icon(icon, color: Color(0xFF00bcd4), size: 24),
            SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: Colors.white,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildControlPanel() {
    return Container(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              GestureDetector(
                onTap: () {
                  if (_speechAvailable) {
                    if (_isAlwaysListening) {
                      _stopAlwaysListening();
                    } else {
                      _startAlwaysListening();
                    }
                  } else {
                    _showError('Speech not available. Use Test Speech or Diagnostics');
                  }
                },
                child: Container(
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  decoration: BoxDecoration(
                    color: _isAlwaysListening ? Color(0xFF00bcd4) : Color(0xFF1e2746),
                    borderRadius: BorderRadius.circular(25),
                    border: Border.all(
                      color: Color(0xFF00bcd4),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _speechAvailable 
                            ? (_isAlwaysListening ? Icons.hearing : Icons.hearing_disabled)
                            : Icons.error,
                        color: _speechAvailable 
                            ? (_isAlwaysListening ? Colors.white : Color(0xFF00bcd4))
                            : Colors.red,
                        size: 20,
                      ),
                      SizedBox(width: 8),
                      Text(
                        _speechAvailable 
                            ? (_isAlwaysListening ? 'Always On' : 'Tap to Wake')
                            : 'Speech Error',
                        style: TextStyle(
                          color: _speechAvailable 
                              ? (_isAlwaysListening ? Colors.white : Color(0xFF00bcd4))
                              : Colors.red,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              
              GestureDetector(
                onTap: () => _showStatsDialog(),
                child: Container(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Color(0xFF1e2746),
                    borderRadius: BorderRadius.circular(25),
                    border: Border.all(
                      color: Color(0xFF00bcd4).withOpacity(0.3),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.analytics, color: Color(0xFF00bcd4), size: 20),
                      SizedBox(width: 8),
                      Text(
                        '$_totalCommands',
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
          
          SizedBox(height: 12),
          
          // Test button for manual speech recognition
          GestureDetector(
            onTap: _testSpeechRecognition,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: BoxDecoration(
                color: Color(0xFFff9800),
                borderRadius: BorderRadius.circular(25),
                border: Border.all(
                  color: Color(0xFFff9800),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.mic_external_on, color: Colors.white, size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Test Speech',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          SizedBox(height: 8),
          
          // Diagnostic button
          GestureDetector(
            onTap: _showDiagnostics,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Color(0xFF9c27b0),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                'Diagnostics',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  void _showDiagnostics() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1e2746),
        title: Text(
          'LUA Diagnostics',
          style: TextStyle(color: Colors.white),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('App Initialized: $_isInitialized', style: TextStyle(color: Colors.white)),
            Text('Speech Available: $_speechAvailable', style: TextStyle(color: Colors.white)),
            Text('Always Listening: $_isAlwaysListening', style: TextStyle(color: Colors.white)),
            Text('Currently Listening: $_isListening', style: TextStyle(color: Colors.white)),
            Text('Backend URL: $_backendUrl', style: TextStyle(color: Colors.white)),
            SizedBox(height: 10),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(context);
                await _testBackgroundService();
              },
              child: Text('Test Background Service'),
            ),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(context);
                await _reinitializeSpeech();
              },
              child: Text('Reinitialize Speech'),
            ),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(context);
                await _checkPermissions();
              },
              child: Text('Check Permissions'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close', style: TextStyle(color: Color(0xFF00bcd4))),
          ),
        ],
      ),
    );
  }
  
  Future<void> _testBackgroundService() async {
    try {
      const platform = MethodChannel('lua_assistant/system');
      
      // Test if background service is running
      await platform.invokeMethod('startBackgroundService');
      _showSuccess('Background service test completed - check notification');
      
      // Simulate wake word detection for testing
      Timer(Duration(seconds: 2), () {
        _handleBackgroundWakeWord();
      });
      
    } catch (e) {
      _showError('Background service test failed: $e');
    }
  }
  
  Future<void> _reinitializeSpeech() async {
    print('Reinitializing speech recognition...');
    setState(() {
      _text = 'Reinitializing speech...';
    });
    
    try {
      await _speech.stop();
      await Future.delayed(Duration(seconds: 1));
      await _initializeSpeech();
      _showSuccess('Speech reinitialized');
    } catch (e) {
      print('Reinitialization error: $e');
      _showError('Reinitialization failed: $e');
    }
  }
  
  Future<void> _checkPermissions() async {
    print('Checking permissions...');
    
    var micStatus = await Permission.microphone.status;
    var phoneStatus = await Permission.phone.status;
    
    String permissionInfo = 'Microphone: $micStatus\nPhone: $phoneStatus';
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1e2746),
        title: Text('Permissions Status', style: TextStyle(color: Colors.white)),
        content: Text(permissionInfo, style: TextStyle(color: Colors.white)),
        actions: [
          if (micStatus != PermissionStatus.granted)
            TextButton(
              onPressed: () async {
                Navigator.pop(context);
                await Permission.microphone.request();
                _checkPermissions();
              },
              child: Text('Request Mic', style: TextStyle(color: Color(0xFF00bcd4))),
            ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close', style: TextStyle(color: Color(0xFF00bcd4))),
          ),
        ],
      ),
    );
  }
  
  void _showEmotionalResponse(Map<String, dynamic> emotion) {
    final String detectedEmotion = emotion['detected'] ?? 'neutral';
    final String emotionalResponse = emotion['emotional_response'] ?? '';
    final List<dynamic> suggestions = emotion['suggestions'] ?? [];
    
    if (detectedEmotion != 'neutral' && emotionalResponse.isNotEmpty) {
      setState(() {
        _response = emotionalResponse;
      });
      
      _speak(emotionalResponse);
      
      if (suggestions.isNotEmpty) {
        _showEmotionalSuggestions(suggestions.cast<String>());
      }
    }
  }
  
  void _showEmotionalSuggestions(List<String> suggestions) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1e2746),
        title: Text(
          'I noticed you might need some help',
          style: TextStyle(color: Colors.white),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: suggestions.map((suggestion) => Padding(
            padding: EdgeInsets.symmetric(vertical: 4),
            child: Text(
              '• $suggestion',
              style: TextStyle(color: Colors.white70),
            ),
          )).toList(),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Thanks', style: TextStyle(color: Color(0xFF00bcd4))),
          ),
        ],
      ),
    );
  }
  
  void _showStatsDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1e2746),
        title: Text(
          'LUA Statistics',
          style: TextStyle(color: Colors.white),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Total Commands: $_totalCommands',
              style: TextStyle(color: Colors.white),
            ),
            SizedBox(height: 10),
            Text(
              'Recent Commands:',
              style: TextStyle(color: Color(0xFF00bcd4), fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 5),
            ..._recentCommands.take(5).map((cmd) => Padding(
              padding: EdgeInsets.symmetric(vertical: 2),
              child: Text(
                '• ${cmd['command']}',
                style: TextStyle(color: Colors.white70, fontSize: 12),
              ),
            )).toList(),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close', style: TextStyle(color: Color(0xFF00bcd4))),
          ),
        ],
      ),
    );
  }
  
  Future<void> _testSpeechRecognition() async {
    print('Testing speech recognition manually...');
    
    setState(() {
      _text = 'Testing... Say something!';
      _isListening = true;
    });
    
    try {
      if (!_speechAvailable) {
        await _initializeSpeech();
      }
      
      if (!_speechAvailable) {
        _showError('Speech recognition not available');
        setState(() {
          _isListening = false;
          _text = 'Speech not available';
        });
        return;
      }
      
      print('Starting test listening...');
      bool? started = await _speech.listen(
        onResult: (result) {
          print('Test result: ${result.recognizedWords}');
          setState(() {
            _text = 'Heard: ${result.recognizedWords}';
          });
          
          if (result.finalResult) {
            setState(() {
              _isListening = false;
            });
            
            String words = result.recognizedWords.toLowerCase();
            if (words.contains('hey lua') || words.contains('hey lula')) {
              _showSuccess('Wake word detected!');
              _activateAssistant();
            } else {
              _showSuccess('Speech working! Try saying "Hey LUA"');
              Timer(Duration(seconds: 2), () {
                if (_speechAvailable) {
                  _startAlwaysListening();
                }
              });
            }
          }
        },
        listenFor: Duration(seconds: 10),
        pauseFor: Duration(seconds: 1),
        partialResults: true,
        onSoundLevelChange: (level) {
          print('Test sound level: $level');
          if (level > 0.1) {
            print('Good sound detected: $level');
          }
        },
      );
      
      // Handle null case properly
      started = started ?? false;
      
      print('Test listening started: $started');
      
      if (!started) {
        _showError('Failed to start test listening');
        setState(() {
          _isListening = false;
          _text = 'Test failed to start';
        });
      }
    } catch (e) {
      print('Test speech error: $e');
      _showError('Test failed: $e');
      setState(() {
        _isListening = false;
        _text = 'Test error: $e';
      });
    }
  }
}