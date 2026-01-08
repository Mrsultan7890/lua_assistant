import json
import os
from datetime import datetime
from collections import defaultdict

class LuaAILearning:
    def __init__(self, db_path='lua_assistant.db'):
        self.db_path = db_path
        self.user_models = {}
        self.command_patterns = {}
        self.context_memory = defaultdict(list)
        
    def predict_intent(self, user_id, command_text, context=None):
        """Predict intent from command text"""
        try:
            command_lower = command_text.lower()
            
            # Simple intent classification
            if any(word in command_lower for word in ['open', 'launch', 'start']):
                intent = 'open_app'
                confidence = 0.8
            elif any(word in command_lower for word in ['call', 'phone', 'dial']):
                intent = 'make_call'
                confidence = 0.8
            elif any(word in command_lower for word in ['message', 'sms', 'text']):
                intent = 'send_message'
                confidence = 0.8
            elif any(word in command_lower for word in ['remind', 'reminder', 'alert']):
                intent = 'set_reminder'
                confidence = 0.8
            elif any(word in command_lower for word in ['music', 'play', 'song']):
                intent = 'control_music'
                confidence = 0.8
            elif any(word in command_lower for word in ['camera', 'photo', 'selfie']):
                intent = 'control_camera'
                confidence = 0.8
            elif any(word in command_lower for word in ['weather', 'temperature']):
                intent = 'get_weather'
                confidence = 0.8
            else:
                intent = 'unknown'
                confidence = 0.3
            
            return {
                'intent': intent,
                'confidence': confidence,
                'user_id': user_id
            }
            
        except Exception as e:
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def learn_from_interaction(self, user_id, command_text, action, success, context=None):
        """Learn from user interactions"""
        try:
            # Store interaction data
            interaction = {
                'user_id': user_id,
                'command': command_text,
                'action': action,
                'success': success,
                'timestamp': datetime.now().isoformat(),
                'context': context or {}
            }
            
            # Add to user's learning history
            if user_id not in self.user_models:
                self.user_models[user_id] = []
            
            self.user_models[user_id].append(interaction)
            
            # Keep only recent interactions (last 100)
            if len(self.user_models[user_id]) > 100:
                self.user_models[user_id] = self.user_models[user_id][-100:]
            
            return True
            
        except Exception as e:
            print(f"Learning error: {e}")
            return False
    
    def get_user_insights(self, user_id):
        """Get AI-powered user insights"""
        try:
            if user_id not in self.user_models:
                return {
                    'total_interactions': 0,
                    'success_rate': 0,
                    'common_commands': [],
                    'insights': []
                }
            
            interactions = self.user_models[user_id]
            total = len(interactions)
            successful = sum(1 for i in interactions if i.get('success', False))
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Get common commands
            commands = [i['command'] for i in interactions]
            command_counts = {}
            for cmd in commands:
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
            
            common_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_interactions': total,
                'success_rate': round(success_rate, 2),
                'common_commands': common_commands,
                'insights': [
                    f"You've used LUA {total} times",
                    f"Success rate: {success_rate:.1f}%",
                    f"Most used command: {common_commands[0][0] if common_commands else 'None'}"
                ]
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_interactions': 0,
                'success_rate': 0
            }
    
    def get_personalized_suggestions(self, user_id):
        """Get personalized suggestions for user"""
        try:
            suggestions = [
                "Try saying 'Hey LUA, open WhatsApp'",
                "You can ask me to call someone by saying 'Call John'",
                "Set reminders with 'Remind me to call mom at 3 PM'",
                "Control music with 'Play music' or 'Next song'",
                "Take photos with 'Take a selfie' or 'Open camera'"
            ]
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            return ["Ask me anything! I'm here to help."]