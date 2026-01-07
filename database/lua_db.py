import sqlite3
import os
from datetime import datetime
import json

class LuaDatabase:
    def __init__(self, db_path="lua_assistant.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Commands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                command_text TEXT NOT NULL,
                intent TEXT,
                response TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                pattern TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # App usage statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                app_name TEXT NOT NULL,
                package_name TEXT,
                usage_count INTEGER DEFAULT 1,
                last_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, user_id, name=None):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (user_id, name) VALUES (?, ?)",
                (user_id, name)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # User already exists
        finally:
            conn.close()
    
    def log_command(self, user_id, command_text, intent, response, success):
        """Log a command execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands (user_id, command_text, intent, response, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, command_text, intent, response, success))
        
        conn.commit()
        conn.close()
    
    def update_learning_pattern(self, user_id, pattern, action):
        """Update or create learning pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if pattern exists
        cursor.execute('''
            SELECT id, usage_count, confidence FROM learning_patterns
            WHERE user_id = ? AND pattern = ? AND action = ?
        ''', (user_id, pattern, action))
        
        result = cursor.fetchone()
        
        if result:
            # Update existing pattern
            pattern_id, usage_count, confidence = result
            new_usage_count = usage_count + 1
            new_confidence = min(confidence + 0.1, 1.0)  # Increase confidence
            
            cursor.execute('''
                UPDATE learning_patterns
                SET usage_count = ?, confidence = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_usage_count, new_confidence, pattern_id))
        else:
            # Create new pattern
            cursor.execute('''
                INSERT INTO learning_patterns (user_id, pattern, action, confidence)
                VALUES (?, ?, ?, ?)
            ''', (user_id, pattern, action, 0.6))
        
        conn.commit()
        conn.close()
    
    def get_user_patterns(self, user_id, limit=10):
        """Get user's most used patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern, action, confidence, usage_count
            FROM learning_patterns
            WHERE user_id = ?
            ORDER BY confidence DESC, usage_count DESC
            LIMIT ?
        ''', (user_id, limit))
        
        patterns = cursor.fetchall()
        conn.close()
        
        return [
            {
                'pattern': p[0],
                'action': p[1],
                'confidence': p[2],
                'usage_count': p[3]
            }
            for p in patterns
        ]
    
    def update_app_usage(self, user_id, app_name, package_name):
        """Track app usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, usage_count FROM app_usage
            WHERE user_id = ? AND package_name = ?
        ''', (user_id, package_name))
        
        result = cursor.fetchone()
        
        if result:
            app_id, usage_count = result
            cursor.execute('''
                UPDATE app_usage
                SET usage_count = ?, last_opened = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (usage_count + 1, app_id))
        else:
            cursor.execute('''
                INSERT INTO app_usage (user_id, app_name, package_name)
                VALUES (?, ?, ?)
            ''', (user_id, app_name, package_name))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total commands
        cursor.execute(
            "SELECT COUNT(*) FROM commands WHERE user_id = ?",
            (user_id,)
        )
        total_commands = cursor.fetchone()[0]
        
        # Successful commands
        cursor.execute(
            "SELECT COUNT(*) FROM commands WHERE user_id = ? AND success = 1",
            (user_id,)
        )
        successful_commands = cursor.fetchone()[0]
        
        # Most used apps
        cursor.execute('''
            SELECT app_name, usage_count FROM app_usage
            WHERE user_id = ?
            ORDER BY usage_count DESC
            LIMIT 5
        ''', (user_id,))
        top_apps = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_commands': total_commands,
            'successful_commands': successful_commands,
            'success_rate': (successful_commands / total_commands * 100) if total_commands > 0 else 0,
            'top_apps': [{'name': app[0], 'count': app[1]} for app in top_apps]
        }

# Initialize database
if __name__ == "__main__":
    db = LuaDatabase()
    print("Database initialized successfully!")