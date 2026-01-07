#!/usr/bin/env python3
"""
LUA Assistant - Voice Cloning
Free voice cloning using Coqui TTS
"""

import os
import io
import wave
import logging
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

class VoiceCloner:
    def __init__(self):
        self.tts = None
        self.voice_models = {}
        self.current_voice = 'default'
        self.setup_tts()
    
    def setup_tts(self):
        """Initialize TTS models"""
        try:
            from TTS.api import TTS
            
            # Load default English model
            self.tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            
            # Available models
            self.available_models = {
                'english': 'tts_models/en/ljspeech/tacotron2-DDC',
                'multilingual': 'tts_models/multilingual/multi-dataset/your_tts',
                'fast': 'tts_models/en/ljspeech/fast_pitch'
            }
            
            logger.info("Voice cloning initialized successfully")
            
        except ImportError:
            logger.error("Coqui TTS not installed. Run: pip install coqui-tts")
            self.tts = None
        except Exception as e:
            logger.error(f"TTS setup error: {e}")
            self.tts = None
    
    def clone_voice_from_sample(self, audio_file_path: str, user_id: str) -> Dict:
        """Clone voice from audio sample"""
        try:
            if not self.tts:
                return {
                    'success': False,
                    'error': 'TTS not initialized'
                }
            
            # Load multilingual model for voice cloning
            if 'multilingual' not in self.voice_models:
                from TTS.api import TTS
                self.voice_models['multilingual'] = TTS(
                    self.available_models['multilingual']
                )
            
            # Create user voice directory
            voice_dir = f'/tmp/voices/{user_id}'
            os.makedirs(voice_dir, exist_ok=True)
            
            # Save reference audio
            reference_path = f'{voice_dir}/reference.wav'
            self._convert_to_wav(audio_file_path, reference_path)
            
            # Store voice reference
            self.voice_models[user_id] = {
                'reference_path': reference_path,
                'model': self.voice_models['multilingual']
            }
            
            return {
                'success': True,
                'message': f'Voice cloned successfully for user {user_id}',
                'voice_id': user_id,
                'reference_path': reference_path
            }
            
        except Exception as e:
            logger.error(f"Voice cloning error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_speech(self, text: str, voice_id: str = 'default', 
                       output_path: str = None) -> Dict:
        """Generate speech with cloned voice"""
        try:
            if not self.tts:
                return {
                    'success': False,
                    'error': 'TTS not initialized'
                }
            
            if not output_path:
                output_path = f'/tmp/speech_{voice_id}_{hash(text)}.wav'
            
            if voice_id == 'default' or voice_id not in self.voice_models:
                # Use default voice
                self.tts.tts_to_file(text=text, file_path=output_path)
            else:
                # Use cloned voice
                voice_data = self.voice_models[voice_id]
                voice_data['model'].tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker_wav=voice_data['reference_path']
                )
            
            return {
                'success': True,
                'audio_path': output_path,
                'text': text,
                'voice_id': voice_id,
                'message': 'Speech generated successfully'
            }
            
        except Exception as e:
            logger.error(f"Speech generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_available_voices(self) -> Dict:
        """List all available voices"""
        try:
            voices = {
                'default_models': list(self.available_models.keys()),
                'cloned_voices': list(self.voice_models.keys()),
                'current_voice': self.current_voice
            }
            
            return {
                'success': True,
                'voices': voices
            }
            
        except Exception as e:
            logger.error(f"List voices error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_voice(self, voice_id: str) -> Dict:
        """Set current voice"""
        try:
            if voice_id in self.available_models or voice_id in self.voice_models:
                self.current_voice = voice_id
                return {
                    'success': True,
                    'message': f'Voice set to {voice_id}',
                    'current_voice': voice_id
                }
            else:
                return {
                    'success': False,
                    'error': f'Voice {voice_id} not found'
                }
                
        except Exception as e:
            logger.error(f"Set voice error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_voice(self, voice_id: str) -> Dict:
        """Delete cloned voice"""
        try:
            if voice_id in self.voice_models:
                # Remove voice files
                voice_data = self.voice_models[voice_id]
                if 'reference_path' in voice_data:
                    try:
                        os.remove(voice_data['reference_path'])
                    except:
                        pass
                
                # Remove from memory
                del self.voice_models[voice_id]
                
                return {
                    'success': True,
                    'message': f'Voice {voice_id} deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Voice {voice_id} not found'
                }
                
        except Exception as e:
            logger.error(f"Delete voice error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_voice_info(self, voice_id: str) -> Dict:
        """Get voice information"""
        try:
            if voice_id in self.voice_models:
                voice_data = self.voice_models[voice_id]
                return {
                    'success': True,
                    'voice_id': voice_id,
                    'type': 'cloned',
                    'reference_path': voice_data.get('reference_path'),
                    'created': True
                }
            elif voice_id in self.available_models:
                return {
                    'success': True,
                    'voice_id': voice_id,
                    'type': 'default',
                    'model_path': self.available_models[voice_id]
                }
            else:
                return {
                    'success': False,
                    'error': f'Voice {voice_id} not found'
                }
                
        except Exception as e:
            logger.error(f"Get voice info error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_to_wav(self, input_path: str, output_path: str):
        """Convert audio file to WAV format"""
        try:
            import librosa
            import soundfile as sf
            
            # Load audio file
            audio, sr = librosa.load(input_path, sr=22050)
            
            # Save as WAV
            sf.write(output_path, audio, sr)
            
        except ImportError:
            # Fallback without librosa
            import shutil
            shutil.copy2(input_path, output_path)
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            raise
    
    def batch_generate_speech(self, texts: list, voice_id: str = 'default') -> Dict:
        """Generate multiple speech files"""
        try:
            results = []
            
            for i, text in enumerate(texts):
                output_path = f'/tmp/batch_speech_{voice_id}_{i}.wav'
                result = self.generate_speech(text, voice_id, output_path)
                results.append(result)
            
            return {
                'success': True,
                'results': results,
                'total_generated': len(results)
            }
            
        except Exception as e:
            logger.error(f"Batch generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }