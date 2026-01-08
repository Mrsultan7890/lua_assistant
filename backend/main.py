#!/usr/bin/env python3
"""
LUA Assistant - Complete Backend Integration
Combines all modules for production deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import threading
import time
from datetime import datetime
import json
import logging
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class LuaBackend:
    def __init__(self):
        self.is_listening = False
        self.active_users = {}
        self.command_queue = []
        self.response_cache = {}
        self.seen_users = self._load_seen_users()  # Load from persistent storage
        
        logger.info("LUA Backend initialized successfully")
    
    def _load_seen_users(self):
        """Load seen users from file or return empty set"""
        try:
            import json
            with open('/tmp/lua_seen_users.json', 'r') as f:
                return set(json.load(f))
        except:
            return set()
    
    def _save_seen_users(self):
        """Save seen users to file"""
        try:
            import json
            with open('/tmp/lua_seen_users.json', 'w') as f:
                json.dump(list(self.seen_users), f)
        except Exception as e:
            logger.error(f"Failed to save seen users: {e}")
    
    def is_first_time_user(self, user_id):
        """Check if user is using LUA for the first time"""
        return user_id not in self.seen_users
    
    def mark_user_as_seen(self, user_id):
        """Mark user as seen"""
        self.seen_users.add(user_id)
        self._save_seen_users()
    
    def handle_first_time_user(self):
        """Handle first time user with welcome message and help"""
        welcome_text = """
Welcome to LUA Assistant! I'm your personal voice assistant.

Here's what I can do for you:

📞 CALLS: "Call John" or "Phone 9876543210"
💬 MESSAGES: "Send message to mom saying I'm coming home"
📱 APPS: "Open camera", "Launch WhatsApp", "Start music"
🎵 MUSIC: "Play music", "Pause", "Next song", "Volume up"
📷 CAMERA: "Take photo", "Open camera", "Selfie mode"
⏰ REMINDERS: "Remind me to call doctor at 5 PM"
🌤️ WEATHER: "What's the weather?", "Temperature today"

🔒 IMPORTANT PRIVACY TIP: For your security, please disable microphone and camera permissions for Instagram, YouTube, TikTok, Facebook and other social media apps. These apps can secretly record your conversations and steal your personal data when permissions are enabled. Protect your privacy!

Just say "Hey LUA" anytime to activate me. Try it now!
        """
        
        return {
            'action': 'welcome',
            'response': welcome_text.strip(),
            'success': True
        }
    
    def process_command(self, user_id, command_text, context=None):
        """Process command with basic text analysis"""
        try:
            start_time = time.time()
            logger.info(f"Processing command from user {user_id}: {command_text}")
            logger.info(f"Seen users: {list(self.seen_users)}")
            
            # Check if first time user (only for very first interaction)
            if self.is_first_time_user(user_id) and command_text.lower().strip() in ['', 'hello', 'hi', 'hey']:
                logger.info(f"First time user with greeting: {user_id}")
                self.mark_user_as_seen(user_id)
                return self.handle_first_time_user()
            
            # Mark user as seen for any command
            if self.is_first_time_user(user_id):
                logger.info(f"Marking new user as seen: {user_id}")
                self.mark_user_as_seen(user_id)
            
            # Basic command processing
            result = self.execute_command(command_text, context)
            
            # Log performance
            processing_time = time.time() - start_time
            logger.info(f"Command processed in {processing_time:.2f}s: {command_text}")
            
            return result
            
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return {
                'action': 'error',
                'response': 'Sorry, I encountered an error processing your command',
                'error': str(e)
            }
    
    def execute_command(self, command_text, context):
        """Execute command based on text analysis"""
        try:
            command_lower = command_text.lower()
            
            # Help command with privacy warning
            if any(word in command_lower for word in ['help', 'commands', 'what can you do']):
                return self.handle_help_command()
            
            # Check for reminders first (before calls)
            elif any(word in command_lower for word in ['remind', 'reminder', 'alert']):
                return self.handle_reminder(command_text)
            
            elif any(word in command_lower for word in ['open', 'launch', 'start']):
                return self.handle_app_launch(command_text)
            
            elif any(word in command_lower for word in ['call', 'phone', 'dial']):
                return self.handle_phone_call(command_text)
            
            elif any(word in command_lower for word in ['message', 'sms', 'text']):
                return self.handle_sms(command_text)
            
            elif any(word in command_lower for word in ['music', 'play', 'song']):
                return self.handle_music_control(command_text)
            
            elif any(word in command_lower for word in ['camera', 'photo', 'selfie']):
                return self.handle_camera_control(command_text)
            
            elif any(word in command_lower for word in ['weather', 'temperature']):
                return self.handle_weather_request(command_text)
            
            else:
                return {
                    'action': 'unknown',
                    'response': 'I understand you said: ' + command_text + '. Say "help" to see available commands.',
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                'action': 'error',
                'response': f'Error executing command: {str(e)}'
            }
    
    def handle_help_command(self):
        """Handle help command with privacy warning"""
        help_text = """
Here are my available commands:

📞 CALLS: "Call John" or "Phone 9876543210"
💬 MESSAGES: "Send message to mom saying I'm coming home"
📱 APPS: "Open camera", "Launch WhatsApp", "Start music"
🎵 MUSIC: "Play music", "Pause", "Next song", "Volume up"
📷 CAMERA: "Take photo", "Open camera", "Selfie mode"
⏰ REMINDERS: "Remind me to call doctor at 5 PM"
🌤️ WEATHER: "What's the weather?", "Temperature today"

🔒 PRIVACY WARNING: For your security, please disable microphone and camera permissions for Instagram, YouTube, TikTok, Facebook and other social media apps. These apps can access your conversations and personal data when permissions are enabled. Your privacy matters!

Say "Hey LUA" anytime to activate me!
        """
        
        return {
            'action': 'help',
            'response': help_text.strip(),
            'success': True
        }
    
    def handle_app_launch(self, command_text):
        """Handle app launching"""
        words = command_text.lower().split()
        stop_words = ['open', 'launch', 'start', 'run', 'the', 'app']
        app_words = [word for word in words if word not in stop_words]
        app_name = ' '.join(app_words) if app_words else 'unknown app'
        
        return {
            'action': 'open_app',
            'app_name': app_name,
            'package': f'com.{app_name.replace(" ", "").lower()}',
            'response': f'Opening {app_name.title()}',
            'success': True
        }
    
    def handle_phone_call(self, command_text):
        """Handle phone calls"""
        import re
        
        # Look for phone number
        phone_pattern = r'\b\d{10}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_match = re.search(phone_pattern, command_text)
        
        if phone_match:
            phone_number = phone_match.group()
            return {
                'action': 'make_call',
                'phone_number': phone_number,
                'response': f'Calling {phone_number}',
                'success': True
            }
        
        # Extract contact name
        words = command_text.split()
        contact_words = ['call', 'phone', 'dial']
        contact_name = None
        
        for i, word in enumerate(words):
            if word.lower() in contact_words and i + 1 < len(words):
                contact_name = ' '.join(words[i+1:]).strip()
                break
        
        if contact_name:
            return {
                'action': 'make_call',
                'contact_name': contact_name,
                'response': f'Calling {contact_name}',
                'success': True
            }
        
        return {
            'action': 'unknown',
            'response': 'Please specify a contact name or phone number',
            'success': False
        }
    
    def handle_sms(self, command_text):
        """Handle SMS sending"""
        import re
        
        # Pattern: "send message to [contact] saying [message]"
        message_pattern = r'(?:send|text).*?(?:to|message)\s+([^\s]+).*?(?:saying|that|message)\s+(.+)'
        match = re.search(message_pattern, command_text, re.IGNORECASE)
        
        if match:
            contact = match.group(1)
            message = match.group(2)
            
            return {
                'action': 'send_sms',
                'contact': contact,
                'message': message,
                'response': f'Sending message to {contact}: {message}',
                'success': True
            }
        
        return {
            'action': 'unknown',
            'response': 'Please specify contact and message. Say "send message to John saying hello"',
            'success': False
        }
    
    def handle_reminder(self, command_text):
        """Handle reminder setting"""
        import re
        
        # Extract time patterns
        time_patterns = [
            r'(?:at|in)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
            r'(?:in)\s+(\d+)\s*(?:minutes?|mins?|hours?|hrs?)',
            r'(?:tomorrow|today|tonight)'
        ]
        
        extracted_time = 'now'
        for pattern in time_patterns:
            match = re.search(pattern, command_text, re.IGNORECASE)
            if match:
                extracted_time = match.group(0)
                break
        
        # Extract title
        title = command_text
        for keyword in ['remind', 'reminder', 'alert']:
            title = title.replace(keyword, '').strip()
        
        if extracted_time != 'now':
            title = title.replace(extracted_time, '').strip()
        
        title = re.sub(r'\b(?:me|to|about|that)\b', '', title, flags=re.IGNORECASE).strip()
        title = title or 'Reminder'
        
        return {
            'action': 'set_reminder',
            'title': title,
            'time': extracted_time,
            'response': f'Reminder set: {title} at {extracted_time}',
            'success': True
        }
    
    def handle_music_control(self, command_text):
        """Handle music control"""
        command_lower = command_text.lower()
        
        if 'play' in command_lower:
            action = 'play_music'
            response = 'Playing music'
        elif any(word in command_lower for word in ['pause', 'stop']):
            action = 'pause_music'
            response = 'Pausing music'
        elif any(word in command_lower for word in ['next', 'skip']):
            action = 'next_track'
            response = 'Playing next track'
        elif any(word in command_lower for word in ['previous', 'back']):
            action = 'previous_track'
            response = 'Playing previous track'
        elif 'volume up' in command_lower:
            action = 'volume_up'
            response = 'Volume up'
        elif 'volume down' in command_lower:
            action = 'volume_down'
            response = 'Volume down'
        else:
            action = 'play_music'
            response = 'Playing music'
        
        return {
            'action': action,
            'response': response,
            'success': True
        }
    
    def handle_camera_control(self, command_text):
        """Handle camera control"""
        mode = 'default'
        if any(word in command_text.lower() for word in ['selfie', 'front']):
            mode = 'front'
        
        return {
            'action': 'open_camera',
            'mode': mode,
            'response': f'Opening camera ({mode} mode)',
            'success': True
        }
    
    def handle_weather_request(self, command_text):
        """Handle weather requests"""
        return {
            'action': 'get_weather',
            'location': 'current location',
            'weather_data': {
                'temperature': '25°C',
                'condition': 'Sunny',
                'humidity': '60%'
            },
            'response': 'Current weather: 25°C, Sunny with 60% humidity',
            'success': True
        }

# Initialize backend
lua_backend = LuaBackend()

# API Routes
@app.route('/', methods=['GET'])
def home():
    """API home endpoint"""
    return jsonify({
        'service': 'LUA Assistant Backend',
        'version': '1.0.0',
        'status': 'running',
        'features': [
            'Voice Command Processing',
            'Device Integration',
            'Smart Command Analysis',
            'Multi-platform Support'
        ],
        'endpoints': {
            'process_voice': '/api/process_voice',
            'user_stats': '/api/user_stats',
            'health': '/health'
        }
    })

@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Process voice command"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        command_text = data.get('text', '')
        context = data.get('context', {})
        
        if not command_text:
            return jsonify({'error': 'No command text provided'}), 400
        
        # Process command
        result = lua_backend.process_command(user_id, command_text, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user_stats', methods=['GET'])
def get_user_stats():
    """Get user statistics"""
    try:
        user_id = request.args.get('user_id', 'default')
        stats = {
            'user_id': user_id,
            'total_commands': 0,
            'success_rate': 100,
            'last_active': datetime.now().isoformat()
        }
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time(),
        'components': {
            'backend': 'running',
            'api': 'active',
            'users_seen': len(lua_backend.seen_users)
        }
    })

@app.route('/ping', methods=['GET', 'POST'])
def ping():
    """Simple ping endpoint to keep service awake"""
    return jsonify({
        'status': 'pong',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting LUA Assistant Backend on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)