import speech_recognition as sr
import pyttsx3
import pyaudio
import wave
import threading
import queue
import time
from datetime import datetime
import json
import os

class AdvancedSpeechProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Configure recognizer
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
        
        # Configure TTS
        self.setup_tts()
        
        # Real-time processing
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.is_listening = False
        self.stop_listening = None
        
    def setup_tts(self):
        """Configure text-to-speech engine"""
        try:
            # Set voice properties
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a female voice
                for voice in voices:
                    if any(keyword in voice.name.lower() for keyword in ['female', 'woman', 'zira', 'hazel']):
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 160)  # Speed
            self.tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
        except Exception as e:
            print(f"TTS setup error: {e}")
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            print("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold}")
            return True
        except Exception as e:
            print(f"Microphone calibration failed: {e}")
            return False
    
    def start_continuous_listening(self, callback):
        """Start continuous speech recognition"""
        try:
            if not self.calibrate_microphone():
                return False
            
            print("Starting continuous listening...")
            self.stop_listening = self.recognizer.listen_in_background(
                self.microphone, 
                callback,
                phrase_time_limit=5
            )
            self.is_listening = True
            return True
            
        except Exception as e:
            print(f"Failed to start continuous listening: {e}")
            return False
    
    def stop_continuous_listening(self):
        """Stop continuous speech recognition"""
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            self.is_listening = False
            print("Stopped continuous listening")
    
    def recognize_speech_from_audio(self, audio_data, language='en-US'):
        """Recognize speech from audio data with multiple engines"""
        results = []
        
        # Try Google Speech Recognition (online)
        try:
            text = self.recognizer.recognize_google(audio_data, language=language)
            results.append({
                'engine': 'google',
                'text': text,
                'confidence': 0.9
            })
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Google Speech Recognition error: {e}")
        
        # Try Sphinx (offline) as fallback
        try:
            text = self.recognizer.recognize_sphinx(audio_data)
            results.append({
                'engine': 'sphinx',
                'text': text,
                'confidence': 0.7
            })
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Sphinx error: {e}")
        
        # Return best result
        if results:
            return max(results, key=lambda x: x['confidence'])
        else:
            return {'engine': 'none', 'text': '', 'confidence': 0.0}
    
    def recognize_from_file(self, audio_file_path):
        """Recognize speech from audio file"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
            
            return self.recognize_speech_from_audio(audio)
            
        except Exception as e:
            print(f"File recognition error: {e}")
            return {'engine': 'error', 'text': '', 'confidence': 0.0}
    
    def speak_text(self, text, async_mode=True):
        """Convert text to speech"""
        try:
            if async_mode:
                # Non-blocking speech
                threading.Thread(target=self._speak_sync, args=(text,)).start()
            else:
                # Blocking speech
                self._speak_sync(text)
            return True
        except Exception as e:
            print(f"TTS error: {e}")
            return False
    
    def _speak_sync(self, text):
        """Synchronous speech synthesis"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Speech synthesis error: {e}")
    
    def save_audio_to_file(self, audio_data, filename):
        """Save audio data to WAV file"""
        try:
            with open(filename, "wb") as f:
                f.write(audio_data.get_wav_data())
            return True
        except Exception as e:
            print(f"Audio save error: {e}")
            return False
    
    def record_audio(self, duration=5):
        """Record audio for specified duration"""
        try:
            print(f"Recording for {duration} seconds...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=duration)
            print("Recording complete")
            return audio
        except Exception as e:
            print(f"Recording error: {e}")
            return None
    
    def get_available_microphones(self):
        """Get list of available microphones"""
        try:
            mics = sr.Microphone.list_microphone_names()
            return [{"index": i, "name": name} for i, name in enumerate(mics)]
        except Exception as e:
            print(f"Microphone list error: {e}")
            return []
    
    def set_microphone(self, device_index):
        """Set specific microphone device"""
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            return self.calibrate_microphone()
        except Exception as e:
            print(f"Microphone set error: {e}")
            return False
    
    def get_audio_levels(self):
        """Get current audio input levels"""
        try:
            with self.microphone as source:
                # Listen for a short duration to get audio level
                audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                # Calculate RMS (Root Mean Square) for audio level
                import audioop
                rms = audioop.rms(audio.get_wav_data(), 2)
                return min(rms / 1000, 100)  # Normalize to 0-100
        except:
            return 0
    
    def enhance_audio_quality(self, audio_data):
        """Enhance audio quality for better recognition"""
        try:
            # Convert to numpy array for processing
            import numpy as np
            import scipy.signal
            
            # Get raw audio data
            raw_data = audio_data.get_raw_data()
            
            # Convert to numpy array
            audio_array = np.frombuffer(raw_data, dtype=np.int16)
            
            # Apply noise reduction (simple high-pass filter)
            b, a = scipy.signal.butter(3, 300, btype='high', fs=audio_data.sample_rate)
            filtered_audio = scipy.signal.filtfilt(b, a, audio_array)
            
            # Normalize audio
            filtered_audio = filtered_audio / np.max(np.abs(filtered_audio))
            filtered_audio = (filtered_audio * 32767).astype(np.int16)
            
            # Create new AudioData object
            enhanced_audio = sr.AudioData(
                filtered_audio.tobytes(),
                audio_data.sample_rate,
                audio_data.sample_width
            )
            
            return enhanced_audio
            
        except Exception as e:
            print(f"Audio enhancement error: {e}")
            return audio_data  # Return original if enhancement fails

class SpeechCallback:
    """Callback handler for continuous speech recognition"""
    
    def __init__(self, speech_processor, command_processor):
        self.speech_processor = speech_processor
        self.command_processor = command_processor
        self.last_recognition_time = 0
        self.recognition_cooldown = 2  # seconds
    
    def __call__(self, recognizer, audio):
        """Handle recognized audio"""
        try:
            current_time = time.time()
            
            # Prevent too frequent recognitions
            if current_time - self.last_recognition_time < self.recognition_cooldown:
                return
            
            # Enhance audio quality
            enhanced_audio = self.speech_processor.enhance_audio_quality(audio)
            
            # Recognize speech
            result = self.speech_processor.recognize_speech_from_audio(enhanced_audio)
            
            if result['text'] and result['confidence'] > 0.5:
                print(f"Recognized: {result['text']} (confidence: {result['confidence']})")
                
                # Process command
                response = self.command_processor.process_command(result['text'])
                
                # Speak response
                if response.get('response'):
                    self.speech_processor.speak_text(response['response'])
                
                self.last_recognition_time = current_time
            
        except Exception as e:
            print(f"Speech callback error: {e}")

# Usage example
if __name__ == "__main__":
    # Initialize speech processor
    speech_processor = AdvancedSpeechProcessor()
    
    # Test microphone
    mics = speech_processor.get_available_microphones()
    print("Available microphones:")
    for mic in mics:
        print(f"  {mic['index']}: {mic['name']}")
    
    # Test TTS
    speech_processor.speak_text("LUA Assistant is ready!", async_mode=False)
    
    # Test recording
    print("Say something...")
    audio = speech_processor.record_audio(3)
    if audio:
        result = speech_processor.recognize_speech_from_audio(audio)
        print(f"You said: {result['text']} (confidence: {result['confidence']})")
        
        if result['text']:
            speech_processor.speak_text(f"I heard you say: {result['text']}")