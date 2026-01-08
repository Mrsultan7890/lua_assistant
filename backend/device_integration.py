import subprocess
import os
import platform
import json
from datetime import datetime

class DeviceIntegration:
    def __init__(self):
        self.system = platform.system().lower()
        self.android_packages = {
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
            'camera': 'com.android.camera2',
            'gallery': 'com.google.android.apps.photos',
            'settings': 'com.android.settings'
        }
    
    def launch_app(self, app_name, package_name=None):
        """Launch an application"""
        try:
            if not package_name:
                package_name = self.android_packages.get(app_name.lower())
            
            if package_name:
                return {
                    'success': True,
                    'message': f'Launching {app_name}',
                    'package': package_name,
                    'action': 'app_launch'
                }
            else:
                return {
                    'success': False,
                    'error': f'App {app_name} not found',
                    'action': 'app_launch_failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'app_launch_error'
            }
    
    def make_call(self, phone_number=None, contact_name=None):
        """Make a phone call"""
        try:
            if phone_number:
                return {
                    'success': True,
                    'message': f'Calling {phone_number}',
                    'phone_number': phone_number,
                    'action': 'make_call'
                }
            elif contact_name:
                return {
                    'success': True,
                    'message': f'Calling {contact_name}',
                    'contact_name': contact_name,
                    'action': 'make_call'
                }
            else:
                return {
                    'success': False,
                    'error': 'No phone number or contact specified',
                    'action': 'call_failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'call_error'
            }
    
    def send_sms(self, contact_name, message):
        """Send SMS message"""
        try:
            return {
                'success': True,
                'message': f'Sending SMS to {contact_name}: {message}',
                'contact': contact_name,
                'sms_message': message,
                'action': 'send_sms'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'sms_error'
            }
    
    def set_reminder(self, title, time_str):
        """Set a reminder"""
        try:
            return {
                'success': True,
                'message': f'Reminder set: {title} at {time_str}',
                'title': title,
                'time': time_str,
                'action': 'set_reminder'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'reminder_error'
            }
    
    def control_music(self, action):
        """Control music playback"""
        try:
            actions = {
                'play_music': 'Playing music',
                'pause_music': 'Pausing music',
                'next_track': 'Playing next track',
                'previous_track': 'Playing previous track',
                'volume_up': 'Volume increased',
                'volume_down': 'Volume decreased'
            }
            
            message = actions.get(action, f'Music action: {action}')
            
            return {
                'success': True,
                'message': message,
                'action': action
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'music_error'
            }
    
    def control_camera(self, mode='default'):
        """Control camera"""
        try:
            if mode == 'front':
                message = 'Opening front camera for selfie'
            else:
                message = 'Opening camera'
            
            return {
                'success': True,
                'message': message,
                'mode': mode,
                'action': 'open_camera'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'camera_error'
            }
    
    def get_device_info(self):
        """Get device information"""
        try:
            return {
                'system': self.system,
                'platform': platform.platform(),
                'available_apps': list(self.android_packages.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'system': 'unknown'
            }