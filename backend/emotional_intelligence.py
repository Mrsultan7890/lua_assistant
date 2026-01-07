import numpy as np
import librosa
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime
import json

class EmotionalIntelligence:
    def __init__(self):
        self.emotions = {
            0: 'neutral',
            1: 'happy', 
            2: 'sad',
            3: 'angry',
            4: 'fearful',
            5: 'disgusted',
            6: 'surprised',
            7: 'stressed'
        }
        
        self.emotion_responses = {
            'happy': [
                "You sound cheerful today! That's wonderful!",
                "I can hear the joy in your voice!",
                "Your positive energy is contagious!"
            ],
            'sad': [
                "I notice you might be feeling down. Is there anything I can help with?",
                "Would you like me to play some uplifting music?",
                "I'm here if you need to talk."
            ],
            'angry': [
                "You seem frustrated. Let me help you with that.",
                "Take a deep breath. How can I assist you?",
                "I understand you're upset. What can I do to help?"
            ],
            'stressed': [
                "You sound stressed. Would you like me to play some calming music?",
                "Let's take this one step at a time. How can I help?",
                "Maybe some relaxation techniques would help?"
            ],
            'fearful': [
                "Everything will be okay. I'm here to help.",
                "You're safe. What do you need assistance with?",
                "Let me help you feel more comfortable."
            ],
            'neutral': [
                "How can I help you today?",
                "What would you like me to do?",
                "I'm ready to assist you."
            ],
            'surprised': [
                "That's interesting! Tell me more.",
                "I can hear the surprise in your voice!",
                "What happened?"
            ],
            'disgusted': [
                "I understand your concern. How can I help?",
                "Let's work through this together.",
                "What's bothering you?"
            ]
        }
        
        self.user_emotion_history = {}
        self.scaler = StandardScaler()
        
    def extract_audio_features(self, audio_data, sample_rate=22050):
        """Extract features from audio for emotion detection"""
        try:
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfccs_mean = np.mean(mfccs, axis=1)
            
            # Extract spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            spectral_centroids_mean = np.mean(spectral_centroids)
            
            # Extract zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio_data)
            zcr_mean = np.mean(zcr)
            
            # Extract chroma features
            chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Extract tempo
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            
            # Combine all features
            features = np.concatenate([
                mfccs_mean,
                [spectral_centroids_mean, zcr_mean, tempo],
                chroma_mean
            ])
            
            return features
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return np.zeros(28)  # Return default feature vector
    
    def detect_emotion_from_text(self, text):
        """Simple text-based emotion detection"""
        text = text.lower()
        
        # Emotion keywords
        emotion_keywords = {
            'happy': ['happy', 'great', 'awesome', 'wonderful', 'excellent', 'good', 'love', 'amazing'],
            'sad': ['sad', 'depressed', 'down', 'upset', 'crying', 'terrible', 'awful', 'bad'],
            'angry': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', 'hate', 'stupid'],
            'stressed': ['stressed', 'worried', 'anxious', 'nervous', 'overwhelmed', 'pressure'],
            'fearful': ['scared', 'afraid', 'frightened', 'terrified', 'worried', 'nervous'],
            'surprised': ['wow', 'amazing', 'incredible', 'unbelievable', 'shocking', 'surprised']
        }
        
        emotion_scores = {}
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            detected_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            return detected_emotion
        
        return 'neutral'
    
    def detect_emotion_from_voice_patterns(self, text, confidence=0.8):
        """Detect emotion from voice patterns and speech characteristics"""
        # Analyze speech patterns
        word_count = len(text.split())
        avg_word_length = np.mean([len(word) for word in text.split()])
        
        # Short, choppy sentences might indicate stress/anger
        if word_count < 5 and avg_word_length < 4:
            return 'stressed'
        
        # Long, flowing sentences might indicate happiness
        if word_count > 15 and avg_word_length > 5:
            return 'happy'
        
        # Check for repeated words (might indicate stress)
        words = text.split()
        if len(words) != len(set(words)) and len(words) > 3:
            return 'stressed'
        
        return self.detect_emotion_from_text(text)
    
    def get_emotional_response(self, emotion, user_id="default"):
        """Get appropriate response based on detected emotion"""
        import random
        
        if emotion in self.emotion_responses:
            responses = self.emotion_responses[emotion]
            response = random.choice(responses)
            
            # Store emotion history
            self.store_emotion_history(user_id, emotion)
            
            return {
                'emotion': emotion,
                'response': response,
                'empathy_level': self.calculate_empathy_level(emotion),
                'suggestions': self.get_emotion_suggestions(emotion)
            }
        
        return {
            'emotion': 'neutral',
            'response': "How can I help you today?",
            'empathy_level': 0.5,
            'suggestions': []
        }
    
    def calculate_empathy_level(self, emotion):
        """Calculate empathy level based on emotion"""
        empathy_levels = {
            'sad': 0.9,
            'angry': 0.8,
            'fearful': 0.9,
            'stressed': 0.8,
            'disgusted': 0.7,
            'happy': 0.6,
            'surprised': 0.5,
            'neutral': 0.5
        }
        
        return empathy_levels.get(emotion, 0.5)
    
    def get_emotion_suggestions(self, emotion):
        """Get helpful suggestions based on emotion"""
        suggestions = {
            'sad': [
                "Would you like me to play some uplifting music?",
                "Should I tell you a joke?",
                "Would you like to hear some motivational quotes?"
            ],
            'angry': [
                "Would you like me to play some calming music?",
                "Should I help you with breathing exercises?",
                "Would you like to take a break?"
            ],
            'stressed': [
                "Would you like me to play relaxing sounds?",
                "Should I help you organize your tasks?",
                "Would you like some meditation guidance?"
            ],
            'fearful': [
                "Would you like me to stay with you?",
                "Should I call someone for you?",
                "Would you like some reassuring information?"
            ],
            'happy': [
                "Would you like me to play your favorite music?",
                "Should I help you share this joy?",
                "Would you like to celebrate somehow?"
            ]
        }
        
        return suggestions.get(emotion, [])
    
    def store_emotion_history(self, user_id, emotion):
        """Store user's emotion history for learning"""
        if user_id not in self.user_emotion_history:
            self.user_emotion_history[user_id] = []
        
        self.user_emotion_history[user_id].append({
            'emotion': emotion,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 emotions
        if len(self.user_emotion_history[user_id]) > 50:
            self.user_emotion_history[user_id] = self.user_emotion_history[user_id][-50:]
    
    def get_emotion_patterns(self, user_id):
        """Analyze user's emotion patterns"""
        if user_id not in self.user_emotion_history:
            return {}
        
        emotions = [entry['emotion'] for entry in self.user_emotion_history[user_id]]
        
        # Count emotion frequencies
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Calculate percentages
        total = len(emotions)
        emotion_percentages = {
            emotion: (count / total) * 100 
            for emotion, count in emotion_counts.items()
        }
        
        # Get recent trend (last 10 interactions)
        recent_emotions = emotions[-10:] if len(emotions) >= 10 else emotions
        recent_trend = recent_emotions[-1] if recent_emotions else 'neutral'
        
        return {
            'emotion_distribution': emotion_percentages,
            'recent_trend': recent_trend,
            'total_interactions': total,
            'dominant_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else 'neutral'
        }
    
    def adjust_response_style(self, user_id, base_response):
        """Adjust response style based on user's emotional patterns"""
        patterns = self.get_emotion_patterns(user_id)
        
        if not patterns:
            return base_response
        
        dominant_emotion = patterns.get('dominant_emotion', 'neutral')
        recent_trend = patterns.get('recent_trend', 'neutral')
        
        # Adjust tone based on patterns
        if dominant_emotion in ['sad', 'stressed'] or recent_trend in ['sad', 'stressed']:
            # Use more gentle, supportive tone
            return f"I understand this might be difficult. {base_response}"
        
        elif dominant_emotion == 'happy' or recent_trend == 'happy':
            # Use more enthusiastic tone
            return f"Great! {base_response}"
        
        elif dominant_emotion in ['angry', 'frustrated']:
            # Use calmer, more patient tone
            return f"I'm here to help. {base_response}"
        
        return base_response

# Usage example
if __name__ == "__main__":
    ei = EmotionalIntelligence()
    
    # Test emotion detection
    test_texts = [
        "I'm so happy today!",
        "I'm feeling really sad and down",
        "This is so frustrating and annoying!",
        "I'm worried about tomorrow's meeting"
    ]
    
    for text in test_texts:
        emotion = ei.detect_emotion_from_voice_patterns(text)
        response = ei.get_emotional_response(emotion, "test_user")
        print(f"Text: {text}")
        print(f"Emotion: {emotion}")
        print(f"Response: {response['response']}")
        print(f"Suggestions: {response['suggestions']}")
        print("---")