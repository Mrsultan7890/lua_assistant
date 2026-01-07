#!/usr/bin/env python3
"""
LUA Assistant - Music Controller
Local music control without API keys
"""

import subprocess
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MusicController:
    def __init__(self):
        self.current_track = None
        self.is_playing = False
        self.volume = 50
        
    def play_music(self, query: str = None) -> Dict:
        """Play music - local or search"""
        try:
            if query:
                # Search and play specific song
                result = self._search_and_play(query)
            else:
                # Resume current or play default
                result = self._resume_playback()
            
            self.is_playing = True
            return {
                'success': True,
                'action': 'play_music',
                'message': f'Playing: {result.get("track", "music")}',
                'track_info': result
            }
            
        except Exception as e:
            logger.error(f"Play music error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to play music'
            }
    
    def pause_music(self) -> Dict:
        """Pause current playback"""
        try:
            # Android media control
            subprocess.run([
                'am', 'broadcast', 
                '-a', 'android.intent.action.MEDIA_BUTTON',
                '--es', 'android.intent.extra.KEY_EVENT', 'KEYCODE_MEDIA_PAUSE'
            ], check=True)
            
            self.is_playing = False
            return {
                'success': True,
                'action': 'pause_music',
                'message': 'Music paused'
            }
            
        except Exception as e:
            logger.error(f"Pause music error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to pause music'
            }
    
    def next_track(self) -> Dict:
        """Skip to next track"""
        try:
            subprocess.run([
                'am', 'broadcast',
                '-a', 'android.intent.action.MEDIA_BUTTON',
                '--es', 'android.intent.extra.KEY_EVENT', 'KEYCODE_MEDIA_NEXT'
            ], check=True)
            
            return {
                'success': True,
                'action': 'next_track',
                'message': 'Skipped to next track'
            }
            
        except Exception as e:
            logger.error(f"Next track error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to skip track'
            }
    
    def previous_track(self) -> Dict:
        """Go to previous track"""
        try:
            subprocess.run([
                'am', 'broadcast',
                '-a', 'android.intent.action.MEDIA_BUTTON',
                '--es', 'android.intent.extra.KEY_EVENT', 'KEYCODE_MEDIA_PREVIOUS'
            ], check=True)
            
            return {
                'success': True,
                'action': 'previous_track',
                'message': 'Playing previous track'
            }
            
        except Exception as e:
            logger.error(f"Previous track error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to go to previous track'
            }
    
    def set_volume(self, level: int) -> Dict:
        """Set volume level (0-100)"""
        try:
            level = max(0, min(100, level))
            
            # Android volume control
            subprocess.run([
                'media', 'volume', '--stream', '3', '--set', str(level)
            ], check=True)
            
            self.volume = level
            return {
                'success': True,
                'action': 'set_volume',
                'message': f'Volume set to {level}%',
                'volume': level
            }
            
        except Exception as e:
            logger.error(f"Set volume error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to set volume'
            }
    
    def get_current_track(self) -> Dict:
        """Get currently playing track info"""
        try:
            # Try to get current media info
            result = subprocess.run([
                'dumpsys', 'media_session'
            ], capture_output=True, text=True)
            
            # Parse media session info
            track_info = self._parse_media_info(result.stdout)
            
            return {
                'success': True,
                'track_info': track_info,
                'is_playing': self.is_playing,
                'volume': self.volume
            }
            
        except Exception as e:
            logger.error(f"Get current track error: {e}")
            return {
                'success': False,
                'error': str(e),
                'track_info': None
            }
    
    def search_local_music(self, query: str) -> List[Dict]:
        """Search local music files"""
        try:
            # Search in common music directories
            music_dirs = [
                '/sdcard/Music',
                '/sdcard/Download',
                '/storage/emulated/0/Music'
            ]
            
            found_tracks = []
            for music_dir in music_dirs:
                try:
                    result = subprocess.run([
                        'find', music_dir, '-name', f'*{query}*',
                        '-type', 'f', '(', '-name', '*.mp3',
                        '-o', '-name', '*.m4a', '-o', '-name', '*.wav', ')'
                    ], capture_output=True, text=True)
                    
                    if result.stdout:
                        tracks = result.stdout.strip().split('\n')
                        for track in tracks[:10]:  # Limit to 10 results
                            found_tracks.append({
                                'path': track,
                                'name': track.split('/')[-1],
                                'type': 'local'
                            })
                except:
                    continue
            
            return found_tracks
            
        except Exception as e:
            logger.error(f"Search local music error: {e}")
            return []
    
    def _search_and_play(self, query: str) -> Dict:
        """Search and play music"""
        # First try local music
        local_tracks = self.search_local_music(query)
        
        if local_tracks:
            track = local_tracks[0]
            # Play local file
            subprocess.run([
                'am', 'start',
                '-a', 'android.intent.action.VIEW',
                '-d', f'file://{track["path"]}',
                '-t', 'audio/*'
            ])
            
            return {
                'track': track['name'],
                'source': 'local',
                'path': track['path']
            }
        else:
            # Fallback to music app search
            subprocess.run([
                'am', 'start',
                '-a', 'android.media.action.MEDIA_PLAY_FROM_SEARCH',
                '--es', 'query', query
            ])
            
            return {
                'track': query,
                'source': 'search',
                'query': query
            }
    
    def _resume_playback(self) -> Dict:
        """Resume current playback"""
        subprocess.run([
            'am', 'broadcast',
            '-a', 'android.intent.action.MEDIA_BUTTON',
            '--es', 'android.intent.extra.KEY_EVENT', 'KEYCODE_MEDIA_PLAY'
        ])
        
        return {
            'track': 'Resumed playback',
            'source': 'resume'
        }
    
    def _parse_media_info(self, media_output: str) -> Dict:
        """Parse media session output"""
        try:
            # Extract basic info from dumpsys output
            lines = media_output.split('\n')
            track_info = {
                'title': 'Unknown',
                'artist': 'Unknown',
                'album': 'Unknown'
            }
            
            for line in lines:
                if 'title=' in line:
                    track_info['title'] = line.split('title=')[1].split(',')[0]
                elif 'artist=' in line:
                    track_info['artist'] = line.split('artist=')[1].split(',')[0]
                elif 'album=' in line:
                    track_info['album'] = line.split('album=')[1].split(',')[0]
            
            return track_info
            
        except Exception as e:
            logger.error(f"Parse media info error: {e}")
            return {'title': 'Unknown', 'artist': 'Unknown', 'album': 'Unknown'}