from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import pyttsx3
import json
import sqlite3
from datetime import datetime
import threading
import os
import re
import requests
import io
import wave
import base64
from werkzeug.utils import secure_filename
import libturso_client
from dotenv import load_dotenv
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize speech recognition and TTS
recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

# Turso Database Connection
TURSO_URL = os.getenv('TURSO_URL', 'file:lua_assistant.db')
TURSO_TOKEN = os.getenv('TURSO_TOKEN', '')

if TURSO_TOKEN:
    db_client = libturso_client.create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
else:
    db_client = None

class LuaAssistant:
    def __init__(self):
        self.commands = {
            'open': self.open_app,
            'call': self.make_call,
            'message': self.send_message,
            'reminder': self.set_reminder,
            'weather': self.get_weather,
            'music': self.control_music,
            'camera': self.control_camera,
            'gallery': self.open_gallery,
            'settings': self.open_settings,
            'calculator': self.open_calculator
        }
        
        self.app_packages = {
            'whatsapp': 'com.whatsapp',
            'instagram': 'com.instagram.android',
            'youtube': 'com.google.android.youtube',
            'facebook': 'com.facebook.katana',
            'twitter': 'com.twitter.android',
            'telegram': 'org.telegram.messenger',
            'chrome': 'com.android.chrome',
            'gmail': 'com.google.android.gm',
            'maps': 'com.google.android.apps.maps',
            'spotify': 'com.spotify.music',
            'netflix': 'com.netflix.mediaclient',
            'amazon': 'in.amazon.mShop.android.shopping',
            'flipkart': 'com.flipkart.android',
            'paytm': 'net.one97.paytm',
            'phonepe': 'com.phonepe.app',
            'gpay': 'com.google.android.apps.nbu.paisa.user',
            'camera': 'camera',
            'gallery': 'gallery',
            'settings': 'settings',
            'calculator': 'calculator',
            'contacts': 'contacts',
            'messages': 'messages',
            'phone': 'phone'
        }
        
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.user_patterns = {}
        self.load_user_patterns()
        
    def load_user_patterns(self):
        """Load learned patterns from database"""
        try:
            conn = sqlite3.connect('lua_assistant.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, pattern, action, confidence 
                FROM learning_patterns 
                WHERE confidence > 0.5
            ''')
            patterns = cursor.fetchall()
            
            for user_id, pattern, action, confidence in patterns:
                if user_id not in self.user_patterns:
                    self.user_patterns[user_id] = []
                self.user_patterns[user_id].append({
                    'pattern': pattern,
                    'action': action,
                    'confidence': confidence
                })
            conn.close()
        except:
            pass

    def process_command(self, text, user_id="default"):
        """Process voice command using AI and return action"""
        text = text.lower().strip()
        
        # Check for learned patterns first
        learned_action = self.check_learned_patterns(text, user_id)
        if learned_action:
            return learned_action
        
        # Intent recognition using keywords
        intent = self.extract_intent(text)
        
        if intent in self.commands:
            result = self.commands[intent](text)
            # Learn this pattern
            self.learn_pattern(user_id, text, intent, result)
            return result
        
        # Fuzzy matching for app names
        app_result = self.fuzzy_app_match(text)
        if app_result:
            self.learn_pattern(user_id, text, 'open', app_result)
            return app_result
        
        # Default response with suggestions
        suggestions = self.get_suggestions(text)
        return {
            "action": "unknown", 
            "response": f"Sorry, I didn't understand '{text}'. Did you mean: {', '.join(suggestions)}?",
            "suggestions": suggestions
        }

    def extract_intent(self, text):
        """Extract intent from text using keyword matching"""
        intent_keywords = {
            'open': ['open', 'launch', 'start', 'run'],
            'call': ['call', 'phone', 'dial', 'ring'],
            'message': ['message', 'text', 'sms', 'send'],
            'reminder': ['remind', 'reminder', 'alert', 'notify'],
            'weather': ['weather', 'temperature', 'forecast'],
            'music': ['play', 'music', 'song', 'pause', 'stop', 'next', 'previous'],
            'camera': ['camera', 'photo', 'picture', 'selfie'],
            'gallery': ['gallery', 'photos', 'images'],
            'settings': ['settings', 'preferences', 'config'],
            'calculator': ['calculator', 'calculate', 'math']
        }
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in text for keyword in keywords):
                return intent
        
        return None

    def check_learned_patterns(self, text, user_id):
        """Check if text matches any learned patterns"""
        if user_id not in self.user_patterns:
            return None
        
        for pattern_data in self.user_patterns[user_id]:
            similarity = self.calculate_similarity(text, pattern_data['pattern'])
            if similarity > 0.8:  # High similarity threshold
                return self.commands[pattern_data['action']](text)
        
        return None

    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts"""
        try:
            vectors = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return similarity
        except:
            return 0

    def learn_pattern(self, user_id, text, intent, result):
        """Learn new pattern from user interaction"""
        try:
            conn = sqlite3.connect('lua_assistant.db')
            cursor = conn.cursor()
            
            # Check if pattern exists
            cursor.execute('''
                SELECT id, confidence FROM learning_patterns
                WHERE user_id = ? AND pattern = ? AND action = ?
            ''', (user_id, text, intent))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update confidence
                new_confidence = min(existing[1] + 0.1, 1.0)
                cursor.execute('''
                    UPDATE learning_patterns 
                    SET confidence = ?, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_confidence, existing[0]))
            else:
                # Create new pattern
                cursor.execute('''
                    INSERT INTO learning_patterns (user_id, pattern, action, confidence)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, text, intent, 0.6))
            
            conn.commit()
            conn.close()
        except:
            pass

    def fuzzy_app_match(self, text):
        """Find best matching app using fuzzy matching"""
        best_match = None
        best_score = 0
        
        for app_name in self.app_packages.keys():
            if app_name in text:
                return self.open_app(f"open {app_name}")
            
            # Calculate similarity
            similarity = self.calculate_similarity(text, app_name)
            if similarity > best_score and similarity > 0.6:
                best_score = similarity
                best_match = app_name
        
        if best_match:
            return self.open_app(f"open {best_match}")
        
        return None

    def get_suggestions(self, text):
        """Get command suggestions based on input"""
        suggestions = []
        
        # Check for partial matches
        for command in self.commands.keys():
            if command in text or text in command:
                suggestions.append(f"{command} something")
        
        # Check for app names
        for app in list(self.app_packages.keys())[:5]:
            if app in text or text in app:
                suggestions.append(f"open {app}")
        
        if not suggestions:
            suggestions = ["open app", "call someone", "set reminder", "play music"]
        
        return suggestions[:3]

    def open_app(self, text):
        """Handle app opening commands with fuzzy matching"""
        # Extract app name from text
        app_name = self.extract_app_name(text)
        
        if app_name in self.app_packages:
            package = self.app_packages[app_name]
            return {
                "action": "open_app",
                "package": package,
                "app_name": app_name,
                "response": f"Opening {app_name.title()}"
            }
        
        # Fuzzy matching
        best_match = self.find_best_app_match(app_name)
        if best_match:
            package = self.app_packages[best_match]
            return {
                "action": "open_app",
                "package": package,
                "app_name": best_match,
                "response": f"Opening {best_match.title()}"
            }
        
        return {
            "action": "unknown", 
            "response": f"App '{app_name}' not found. Available apps: {', '.join(list(self.app_packages.keys())[:10])}"
        }

    def extract_app_name(self, text):
        """Extract app name from command text"""
        # Remove common words
        words = text.lower().split()
        stop_words = ['open', 'launch', 'start', 'run', 'the', 'app', 'application']
        app_words = [word for word in words if word not in stop_words]
        
        if app_words:
            return ' '.join(app_words)
        
        return text

    def find_best_app_match(self, app_name):
        """Find best matching app name"""
        best_match = None
        best_score = 0
        
        for available_app in self.app_packages.keys():
            similarity = self.calculate_similarity(app_name, available_app)
            if similarity > best_score and similarity > 0.5:
                best_score = similarity
                best_match = available_app
        
        return best_match

    def make_call(self, text):
        """Handle call commands with contact/number extraction"""
        # Extract phone number
        phone_pattern = r'\b\d{10}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_match = re.search(phone_pattern, text)
        
        if phone_match:
            phone_number = phone_match.group()
            return {
                "action": "make_call",
                "phone_number": phone_number,
                "response": f"Calling {phone_number}"
            }
        
        # Extract contact name
        contact_keywords = ['call', 'phone', 'dial']
        words = text.split()
        contact_name = None
        
        for i, word in enumerate(words):
            if word in contact_keywords and i + 1 < len(words):
                contact_name = ' '.join(words[i+1:]).strip()
                break
        
        if contact_name:
            return {
                "action": "make_call",
                "contact_name": contact_name,
                "response": f"Calling {contact_name}"
            }
        
        return {
            "action": "unknown",
            "response": "Please specify a contact name or phone number to call"
        }

    def send_message(self, text):
        """Handle SMS commands with contact and message extraction"""
        # Pattern: "send message to [contact] saying [message]"
        message_pattern = r'(?:send|text).*?(?:to|message)\s+([^\s]+).*?(?:saying|that|message)\s+(.+)'
        match = re.search(message_pattern, text, re.IGNORECASE)
        
        if match:
            contact = match.group(1)
            message = match.group(2)
            return {
                "action": "send_sms",
                "contact": contact,
                "message": message,
                "response": f"Sending message to {contact}: {message}"
            }
        
        # Simple pattern: "message [contact]"
        simple_pattern = r'(?:message|text|sms)\s+([^\s]+)'
        simple_match = re.search(simple_pattern, text, re.IGNORECASE)
        
        if simple_match:
            contact = simple_match.group(1)
            return {
                "action": "send_sms",
                "contact": contact,
                "message": "",
                "response": f"What message would you like to send to {contact}?",
                "requires_input": True
            }
        
        return {
            "action": "unknown",
            "response": "Please specify contact and message. Say 'send message to John saying hello'"
        }

    def set_reminder(self, text):
        """Handle reminder commands with time and title extraction"""
        # Time patterns
        time_patterns = [
            r'(?:at|in)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
            r'(?:in)\s+(\d+)\s*(?:minutes?|mins?|hours?|hrs?)',
            r'(?:tomorrow|today|tonight)',
            r'(?:at)\s+(\d{1,2})(?:\s*(?:am|pm|AM|PM))?'
        ]
        
        extracted_time = None
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_time = match.group(0)
                break
        
        # Extract reminder title
        reminder_keywords = ['remind', 'reminder', 'alert']
        title = text
        for keyword in reminder_keywords:
            if keyword in text:
                title = text.replace(keyword, '').strip()
                break
        
        # Clean up title
        if extracted_time:
            title = title.replace(extracted_time, '').strip()
        
        title = re.sub(r'\b(?:me|to|about|that)\b', '', title, flags=re.IGNORECASE).strip()
        
        return {
            "action": "set_reminder",
            "title": title or "Reminder",
            "time": extracted_time or "now",
            "response": f"Reminder set: {title} {extracted_time or ''}".strip()
        }

    def get_weather(self, text):
        """Handle weather commands with location extraction"""
        # Extract location
        location_pattern = r'(?:weather|temperature)\s+(?:in|at|for)\s+([a-zA-Z\s]+)'
        match = re.search(location_pattern, text, re.IGNORECASE)
        
        location = match.group(1).strip() if match else "current location"
        
        # Mock weather data (replace with real API)
        weather_data = {
            "temperature": "25°C",
            "condition": "Sunny",
            "humidity": "60%",
            "location": location
        }
        
        return {
            "action": "get_weather",
            "location": location,
            "weather_data": weather_data,
            "response": f"Weather in {location}: {weather_data['temperature']}, {weather_data['condition']}"
        }

    def control_music(self, text):
        """Handle music control commands with song/artist extraction"""
        if 'play' in text:
            # Extract song/artist name
            play_pattern = r'play\s+(.+?)(?:\s+by\s+(.+))?$'
            match = re.search(play_pattern, text, re.IGNORECASE)
            
            if match:
                song = match.group(1).strip()
                artist = match.group(2).strip() if match.group(2) else None
                response = f"Playing {song}"
                if artist:
                    response += f" by {artist}"
                
                return {
                    "action": "play_music",
                    "song": song,
                    "artist": artist,
                    "response": response
                }
            else:
                return {"action": "play_music", "response": "Playing music"}
        
        elif any(word in text for word in ['pause', 'stop']):
            return {"action": "pause_music", "response": "Pausing music"}
        
        elif any(word in text for word in ['next', 'skip']):
            return {"action": "next_track", "response": "Playing next track"}
        
        elif any(word in text for word in ['previous', 'back']):
            return {"action": "previous_track", "response": "Playing previous track"}
        
        elif any(word in text for word in ['volume', 'loud', 'quiet']):
            if any(word in text for word in ['up', 'increase', 'loud']):
                return {"action": "volume_up", "response": "Increasing volume"}
            elif any(word in text for word in ['down', 'decrease', 'quiet']):
                return {"action": "volume_down", "response": "Decreasing volume"}
        
        return {"action": "unknown", "response": "Music command not recognized"}

    def control_camera(self, text):
        """Handle camera commands"""
        if any(word in text for word in ['selfie', 'front']):
            return {"action": "open_camera", "mode": "front", "response": "Opening front camera for selfie"}
        elif any(word in text for word in ['photo', 'picture']):
            return {"action": "open_camera", "mode": "back", "response": "Opening camera to take photo"}
        else:
            return {"action": "open_camera", "mode": "default", "response": "Opening camera"}

    def open_gallery(self, text):
        """Handle gallery commands"""
        return {"action": "open_gallery", "response": "Opening gallery"}

    def open_settings(self, text):
        """Handle settings commands"""
        if 'wifi' in text:
            return {"action": "open_settings", "section": "wifi", "response": "Opening WiFi settings"}
        elif 'bluetooth' in text:
            return {"action": "open_settings", "section": "bluetooth", "response": "Opening Bluetooth settings"}
        else:
            return {"action": "open_settings", "section": "main", "response": "Opening settings"}

    def open_calculator(self, text):
        """Handle calculator commands"""
        return {"action": "open_calculator", "response": "Opening calculator"}

# Initialize assistant
lua = LuaAssistant()

@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Process voice input and return command"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        user_id = data.get('user_id', 'default')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        result = lua.process_command(text, user_id)
        
        # Log command for learning
        log_command(user_id, text, result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/speech_to_text', methods=['POST'])
def speech_to_text():
    """Convert speech to text using real speech recognition"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # Save temporary file
        temp_filename = secure_filename(audio_file.filename)
        temp_path = f"/tmp/{temp_filename}"
        audio_file.save(temp_path)
        
        # Process with speech recognition
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
            
        try:
            # Try Google Speech Recognition first
            text = recognizer.recognize_google(audio)
            confidence = 0.9
        except sr.UnknownValueError:
            try:
                # Fallback to Sphinx (offline)
                text = recognizer.recognize_sphinx(audio)
                confidence = 0.7
            except:
                text = ""
                confidence = 0.0
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            "text": text,
            "confidence": confidence
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/text_to_speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if text:
            # Configure TTS
            tts_engine.setProperty('rate', 150)
            tts_engine.setProperty('volume', 0.8)
            
            # Set voice (try to use female voice)
            voices = tts_engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        tts_engine.setProperty('voice', voice.id)
                        break
            
            # Generate speech
            tts_engine.say(text)
            tts_engine.runAndWait()
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/learn', methods=['POST'])
def learn_pattern():
    """Learn from user interactions"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        command = data.get('command', '')
        action = data.get('action', '')
        success = data.get('success', False)
        
        # Store learning data
        lua.learn_pattern(user_id, command, action, {"success": success})
        
        return jsonify({"status": "learned"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user_stats', methods=['GET'])
def get_user_stats():
    """Get user statistics"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        conn = sqlite3.connect('lua_assistant.db')
        cursor = conn.cursor()
        
        # Total commands
        cursor.execute("SELECT COUNT(*) FROM commands WHERE user_id = ?", (user_id,))
        total_commands = cursor.fetchone()[0]
        
        # Recent commands
        cursor.execute('''
            SELECT command_text, response, timestamp 
            FROM commands 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (user_id,))
        recent_commands = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "total_commands": total_commands,
            "recent_commands": [
                {
                    "command": cmd[0],
                    "response": cmd[1],
                    "timestamp": cmd[2]
                }
                for cmd in recent_commands
            ]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def log_command(user_id, command, result):
    """Log commands for analytics"""
    try:
        conn = sqlite3.connect('lua_assistant.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands (user_id, command_text, intent, response, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            command,
            result.get('action', 'unknown'),
            result.get('response', ''),
            result.get('action') != 'unknown'
        ))
        
        conn.commit()
        conn.close()
    except:
        pass

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "service": "LUA Assistant",
        "version": "1.0.0",
        "features": [
            "Speech Recognition",
            "AI Learning",
            "App Control",
            "Smart Commands"
        ]
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "LUA Assistant API",
        "version": "1.0.0",
        "endpoints": [
            "/api/process_voice",
            "/api/speech_to_text",
            "/api/text_to_speech",
            "/api/learn",
            "/api/user_stats",
            "/health"
        ]
    })

if __name__ == '__main__':
    # Initialize database
    from database.lua_db import LuaDatabase
    db = LuaDatabase()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)