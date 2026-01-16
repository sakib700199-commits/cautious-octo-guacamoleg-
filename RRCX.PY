# -*- coding: utf-8 -*-
import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import random
import hashlib

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "🤖 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 🦁 𝐢𝐬 𝐑𝐮𝐧𝐧𝐢𝐧𝐠!"
@app.route('/health')
def health():
    return {"𝐬𝐭𝐚𝐭𝐮𝐬": "𝐡𝐞𝐚𝐥𝐭𝐡𝐲", "𝐮𝐩𝐭𝐢𝐦𝐞": get_uptime()}
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ 𝐅𝐥𝐚𝐬𝐤 𝐊𝐞𝐞𝐩-𝐀𝐥𝐢𝐯𝐞 𝐬𝐞𝐫𝐯𝐞𝐫 𝐬𝐭𝐚𝐫𝐭𝐞𝐝.")

# --- Configuration ---
TOKEN = '8391801535:AAHYBYDKlMNK90fnlslkXLQpJdC2weNoTHk'
OWNER_ID = 8128852482
ADMIN_ID = 8128852482
YOUR_USERNAME = '@ruhivig85'
UPDATE_CHANNEL = 'http://t.me/Qne_hosting_ruhi_bot'

# Folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# --- MODIFIED: File upload limits - REMOVED ALL LIMITS ---
# All users now have unlimited uploads
FREE_USER_LIMIT = float('inf')  # Changed from 10
SUBSCRIBED_USER_LIMIT = float('inf')  # Changed from 15
ADMIN_LIMIT = float('inf')
OWNER_LIMIT = float('inf')

# Create necessary directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Initialize bot - REMOVED parse_mode='HTML'
bot = telebot.TeleBot(TOKEN)

# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
bot_start_time = datetime.now()

# --- Enhanced task management for heavy tasks ---
task_queue = []
task_queue_lock = threading.Lock()
MAX_CONCURRENT_TASKS = 5
active_tasks = 0

def manage_task_queue():
    """Manage heavy tasks to prevent overload"""
    global active_tasks
    while True:
        time.sleep(1)
        with task_queue_lock:
            if task_queue and active_tasks < MAX_CONCURRENT_TASKS:
                task = task_queue.pop(0)
                active_tasks += 1
                threading.Thread(target=execute_task, args=(task,)).start()

def execute_task(task):
    """Execute a task with proper resource management"""
    global active_tasks
    try:
        task['function'](*task.get('args', []), **task.get('kwargs', {}))
    finally:
        with task_queue_lock:
            active_tasks -= 1

def add_task_to_queue(func, *args, **kwargs):
    """Add a heavy task to the queue"""
    with task_queue_lock:
        task_queue.append({
            'function': func,
            'args': args,
            'kwargs': kwargs
        })

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Custom Font Converter ---
def apply_custom_font(text):
    """Apply custom bold font to ALL text outputs"""
    font_map = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
        'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
        'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
        'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠',
        'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧',
        'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮',
        'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔',
        '7': '𝟕', '8': '𝟖', '9': '𝟗'
    }
    
    result = []
    for char in text:
        if char in font_map:
            result.append(font_map[char])
        else:
            result.append(char)
    
    return ''.join(result)

def send_formatted_message(chat_id, text, reply_markup=None):
    """Send message with custom font without HTML parsing issues"""
    try:
        # Apply custom font to the text
        formatted_text = apply_custom_font(text)
        
        # Send without parse_mode to avoid HTML issues
        return bot.send_message(chat_id, formatted_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error sending formatted message: {e}")
        # Fallback: send without custom font
        return bot.send_message(chat_id, text, reply_markup=reply_markup)

def edit_formatted_message(chat_id, message_id, text, reply_markup=None):
    """Edit message with custom font without HTML parsing issues"""
    try:
        # Apply custom font to the text
        formatted_text = apply_custom_font(text)
        
        # Edit without parse_mode to avoid HTML issues
        return bot.edit_message_text(formatted_text, chat_id, message_id, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error editing formatted message: {e}")
        return None

# --- Enhanced Animation Functions ---
def send_command_animation(chat_id, command_name, final_output):
    """Show animation for EVERY command execution"""
    try:
        action_text = apply_custom_font(f"Executing: {command_name}")
        msg = None
        
        for i in range(5):
            percent = int((i / 4) * 100)
            bar = "🟩" * i + "⬜" * (4 - i)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {action_text}"
            
            if i == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except:
                    pass
            time.sleep(0.3)
        
        # Apply custom font to final output
        formatted_output = apply_custom_font(final_output)
        
        try:
            bot.edit_message_text(formatted_output, chat_id, msg.message_id)
        except:
            bot.send_message(chat_id, formatted_output)
        return msg
    except Exception as e:
        logger.error(f"Animation error: {e}")
        formatted_output = apply_custom_font(final_output)
        return bot.send_message(chat_id, formatted_output)

def send_simple_animation(chat_id, text, duration=2):
    """Simple animation for quick operations"""
    try:
        msg = None
        steps = 3
        for i in range(steps + 1):
            percent = int((i / steps) * 100)
            bar = "🟩" * i + "⬜" * (steps - i)
            display = f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({percent}%)\n[{bar}] {apply_custom_font(text)}"
            
            if i == 0:
                msg = bot.send_message(chat_id, display)
            else:
                try:
                    bot.edit_message_text(display, chat_id, msg.message_id)
                except:
                    pass
            time.sleep(duration / steps)
        return msg
    except Exception as e:
        logger.error(f"Simple animation error: {e}")
        return bot.send_message(chat_id, apply_custom_font(text))

# --- Utility Functions with Custom Font ---
def get_uptime():
    """Get bot uptime as string with custom font"""
    uptime = datetime.now() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return apply_custom_font(f"{days}d {hours}h {minutes}m {seconds}s")

def format_size(size_bytes):
    """Format bytes to human readable size with custom font"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return apply_custom_font(f"{size_bytes:.2f} {unit}")
        size_bytes /= 1024
    return apply_custom_font(f"{size_bytes:.2f} PB")

# --- Database Functions with Auto-Restart System ---
def init_db():
    """Initialize the database with auto-restart tables"""
    logger.info(apply_custom_font(f"Initializing database at: {DATABASE_PATH}"))
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        
        # Existing tables
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
(user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
(user_id INTEGER, file_name TEXT, file_type TEXT, upload_time TEXT,
file_size INTEGER, PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
(user_id INTEGER PRIMARY KEY, username TEXT, first_seen TEXT, last_seen TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
(user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS bot_logs
(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT,
details TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS running_scripts
(script_key TEXT PRIMARY KEY, user_id INTEGER, file_name TEXT,
start_time TEXT, pid INTEGER)''')
        
        # NEW: Auto-restart persistent scripts table
        c.execute('''CREATE TABLE IF NOT EXISTS persistent_scripts (
            script_key TEXT PRIMARY KEY,
            user_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            status TEXT,
            pid INTEGER,
            start_time TEXT,
            restart_count INTEGER DEFAULT 0,
            auto_restart BOOLEAN DEFAULT 1,
            last_updated TEXT
        )''')
        
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        
        conn.commit()
        conn.close()
        logger.info(apply_custom_font("Database initialized successfully with auto-restart system."))
    except Exception as e:
        logger.error(apply_custom_font(f"Database initialization error: {e}"))

def load_data():
    """Load data from database"""
    logger.info(apply_custom_font("Loading data from database..."))
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(apply_custom_font(f"Invalid expiry format for user {user_id}"))
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))
        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())
        conn.close()
        logger.info(apply_custom_font(f"Data loaded: {len(active_users)} users, {len(user_subscriptions)} subs, {len(admin_ids)} admins"))
    except Exception as e:
        logger.error(apply_custom_font(f"Error loading data: {e}"))

def save_script_state(script_key, user_id, file_name, file_path, file_type, pid, status='running'):
    """Save script state to database for auto-recovery"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute('''INSERT OR REPLACE INTO persistent_scripts 
                    (script_key, user_id, file_name, file_path, file_type, status, pid, start_time, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (script_key, user_id, file_name, file_path, file_type, status, pid, now, now))
        conn.commit()
        conn.close()
        logger.info(f"💾 Saved state for {script_key}")
    except Exception as e:
        logger.error(f"Error saving script state: {e}")

def update_script_status(script_key, status, pid=None):
    """Update script status in database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        if pid:
            c.execute('''UPDATE persistent_scripts SET status = ?, pid = ?, last_updated = ?
                        WHERE script_key = ?''',
                      (status, pid, now, script_key))
        else:
            c.execute('''UPDATE persistent_scripts SET status = ?, last_updated = ?
                        WHERE script_key = ?''',
                      (status, now, script_key))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating script status: {e}")

def log_action(user_id, action, details):
    """Log user action with custom font"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT INTO bot_logs (user_id, action, details, timestamp)
VALUES (?, ?, ?, ?)''',
                  (user_id, apply_custom_font(action), apply_custom_font(details), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(apply_custom_font(f"Error logging action: {e}"))

# Initialize DB and Load Data
init_db()
load_data()

# --- Auto-Restart System Functions ---
def recover_running_scripts():
    """Recover all scripts that were running before crash"""
    try:
        logger.info("🔄 Recovering previously running scripts...")
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Get all scripts marked as running
        c.execute('''SELECT script_key, user_id, file_name, file_path, file_type 
                    FROM persistent_scripts 
                    WHERE status = 'running' AND auto_restart = 1''')
        scripts = c.fetchall()
        
        recovered = 0
        for script_key, user_id, file_name, file_path, file_type in scripts:
            try:
                # Check if file still exists
                if os.path.exists(file_path):
                    # Create a fake message object for the run function
                    class FakeMessage:
                        def __init__(self, user_id):
                            self.chat = type('obj', (object,), {'id': user_id})()
                            self.from_user = type('obj', (object,), {'id': user_id})()
                    
                    fake_msg = FakeMessage(user_id)
                    user_folder = os.path.dirname(file_path)
                    
                    # Auto-restart the script using task queue
                    if file_type == 'py':
                        add_task_to_queue(run_script, file_path, user_id, user_folder, 
                                         file_name, fake_msg, 1)
                    elif file_type == 'js':
                        add_task_to_queue(run_js_script, file_path, user_id, user_folder, 
                                         file_name, fake_msg, 1)
                    
                    recovered += 1
                    logger.info(f"✅ Auto-restarted: {file_name} for user {user_id}")
                    
                    # Send notification to user
                    try:
                        notify_script_restart(user_id, file_name, True)
                    except:
                        pass
                    
                    time.sleep(1)  # Prevent overload
                else:
                    # File doesn't exist anymore
                    c.execute('''UPDATE persistent_scripts SET status = 'stopped' 
                                WHERE script_key = ?''', (script_key,))
            except Exception as e:
                logger.error(f"Failed to recover {script_key}: {e}")
                # Mark as crashed
                c.execute('''UPDATE persistent_scripts SET status = 'crashed' 
                            WHERE script_key = ?''', (script_key,))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Recovered {recovered} scripts")
        
        # Broadcast recovery completion to admin
        try:
            bot.send_message(OWNER_ID, 
                           f"🔄 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐫𝐞𝐜𝐨𝐯𝐞𝐫𝐲 𝐜𝐨𝐦𝐩𝐥𝐞𝐭𝐞\n📊 𝐑𝐞𝐜𝐨𝐯𝐞𝐫𝐞𝐝: {recovered} 𝐬𝐜𝐫𝐢𝐩𝐭𝐬")
        except:
            pass
            
    except Exception as e:
        logger.error(f"Recovery error: {e}")

def health_check_monitor():
    """Background thread to monitor script health"""
    while True:
        try:
            time.sleep(60)  # Check every minute
            
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            
            # Get all running scripts from database
            c.execute('''SELECT script_key, pid, file_name, user_id, file_path, file_type, restart_count
                        FROM persistent_scripts 
                        WHERE status = 'running' AND auto_restart = 1''')
            scripts = c.fetchall()
            
            for script_key, pid, file_name, user_id, file_path, file_type, restart_count in scripts:
                try:
                    if pid:
                        # Check if process is still alive
                        process = psutil.Process(pid)
                        if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                            logger.warning(f"Script {script_key} crashed, attempting auto-restart")
                            
                            # Mark as crashed
                            c.execute('''UPDATE persistent_scripts SET status = 'crashed' 
                                        WHERE script_key = ?''', (script_key,))
                            
                            # Auto-restart if restart count < 3
                            if restart_count < 3:
                                # Increment restart count
                                c.execute('''UPDATE persistent_scripts 
                                            SET restart_count = restart_count + 1 
                                            WHERE script_key = ?''', (script_key,))
                                
                                # Restart the script using task queue
                                if os.path.exists(file_path):
                                    class FakeMessage:
                                        def __init__(self, user_id):
                                            self.chat = type('obj', (object,), {'id': user_id})()
                                            self.from_user = type('obj', (object,), {'id': user_id})()
                                    
                                    fake_msg = FakeMessage(user_id)
                                    user_folder = os.path.dirname(file_path)
                                    
                                    if file_type == 'py':
                                        add_task_to_queue(run_script, file_path, user_id, user_folder, 
                                                         file_name, fake_msg, 1)
                                    elif file_type == 'js':
                                        add_task_to_queue(run_js_script, file_path, user_id, user_folder, 
                                                         file_name, fake_msg, 1)
                                    
                                    logger.info(f"🔄 Auto-restarted crashed script: {file_name}")
                            else:
                                logger.error(f"Script {script_key} exceeded max restart attempts")
                                # Disable auto-restart
                                c.execute('''UPDATE persistent_scripts SET auto_restart = 0 
                                            WHERE script_key = ?''', (script_key,))
                                notify_script_restart(user_id, file_name, False)
                                
                except psutil.NoSuchProcess:
                    # Process doesn't exist
                    c.execute('''UPDATE persistent_scripts SET status = 'crashed' 
                                WHERE script_key = ?''', (script_key,))
                    logger.warning(f"Process {pid} for {script_key} not found")
                    
                except Exception as e:
                    logger.error(f"Health check error for {script_key}: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            time.sleep(30)

def notify_script_restart(user_id, file_name, success=True):
    """Notify user about script restart"""
    try:
        if success:
            message = f"""
🔄 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐀𝐮𝐭𝐨-𝐑𝐞𝐬𝐭𝐚𝐫𝐭
📄 𝐅𝐢𝐥𝐞: {file_name}
✅ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐑𝐞𝐬𝐭𝐚𝐫𝐭𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲
⏰ 𝐓𝐢𝐦𝐞: {datetime.now().strftime('%H:%M:%S')}
🤖 𝐁𝐨𝐭: 𝐀𝐜𝐭𝐢𝐯𝐞
"""
        else:
            message = f"""
⚠️ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐀𝐮𝐭𝐨-𝐑𝐞𝐬𝐭𝐚𝐫𝐭 𝐅𝐚𝐢𝐥𝐞𝐝
📄 𝐅𝐢𝐥𝐞: {file_name}
❌ 𝐒𝐭𝐚𝐭𝐮𝐬: 𝐅𝐚𝐢𝐥𝐞𝐝 𝐭𝐨 𝐫𝐞𝐬𝐭𝐚𝐫𝐭
🔧 𝐀𝐜𝐭𝐢𝐨𝐧: 𝐂𝐡𝐞𝐜𝐤 𝐟𝐢𝐥𝐞 𝐚𝐧𝐝 𝐭𝐫𝐲 𝐦𝐚𝐧𝐮𝐚𝐥𝐥𝐲
"""
        
        bot.send_message(user_id, message)
    except:
        pass  # User might have blocked bot

def save_all_running_states():
    """Save all running script states before shutdown"""
    logger.info("💾 Saving all running script states...")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        for script_key, script_info in bot_scripts.items():
            if script_info.get('process') and script_info['process'].poll() is None:
                c.execute('''UPDATE persistent_scripts SET status = 'running', 
                            pid = ?, last_updated = ?
                            WHERE script_key = ?''',
                         (script_info['process'].pid, datetime.now().isoformat(), script_key))
        
        conn.commit()
        conn.close()
        logger.info("✅ All script states saved")
    except Exception as e:
        logger.error(f"Error saving states: {e}")

# --- Enhanced ZIP Analysis Functions ---
def analyze_zip_project(zip_path, extract_path):
    """
    Analyze ZIP project intelligently
    Returns: (project_type, entry_file, requirements_file, project_dir)
    project_type: 'py', 'js', 'mixed', 'unknown'
    """
    try:
        logger.info(f"🔍 Analyzing ZIP: {zip_path}")
        
        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Walk through all files
        all_files = []
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_path)
                all_files.append((rel_path, file, file_path))
        
        # Check for project indicators
        has_package_json = False
        has_requirements_txt = False
        has_python_files = []
        has_node_entry = False
        node_entry_file = None
        package_json_path = None
        
        python_entry_patterns = ['main.py', 'bot.py', 'app.py', 'server.py', 'index.py', 'start.py', 'run.py', 'Insta.py']
        
        for rel_path, file, file_path in all_files:
            # Check for package.json
            if file.lower() == 'package.json':
                has_package_json = True
                package_json_path = file_path
                
                # Read package.json
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                    
                    # Check if main field exists
                    if 'main' in package_data:
                        main_file = package_data['main']
                        # Check if main file exists
                        main_file_path = os.path.join(os.path.dirname(file_path), main_file)
                        if os.path.exists(main_file_path):
                            has_node_entry = True
                            node_entry_file = main_file_path
                            logger.info(f"✅ Found valid Node.js entry: {main_file}")
                        else:
                            logger.warning(f"⚠️ Node.js main file not found: {main_file}")
                except Exception as e:
                    logger.error(f"Error reading package.json: {e}")
            
            # Check for requirements.txt
            elif file.lower() == 'requirements.txt':
                has_requirements_txt = True
            
            # Check for Python entry files
            elif file.lower().endswith('.py'):
                if file.lower() in python_entry_patterns:
                    has_python_files.append((file_path, rel_path))
                elif len(has_python_files) == 0:  # Add any .py file if no entry found
                    has_python_files.append((file_path, rel_path))
        
        # Decision logic
        if has_node_entry and has_python_files:
            logger.info("🔀 Mixed project detected (both Node.js and Python)")
            # Prefer Python when both exist (safer for TCP bots)
            if len(has_python_files) > 0:
                # Sort Python files by priority
                sorted_python_files = sorted(has_python_files, 
                                           key=lambda x: python_entry_patterns.index(x[1].lower()) 
                                           if x[1].lower() in python_entry_patterns else 999)
                entry_file = sorted_python_files[0][0]
                logger.info(f"🤖 Selected Python entry: {os.path.basename(entry_file)}")
                return 'py', entry_file, has_requirements_txt, extract_path
            else:
                return 'js', node_entry_file, False, extract_path
        
        elif has_node_entry:
            logger.info("🟨 Node.js project detected")
            return 'js', node_entry_file, False, extract_path
        
        elif len(has_python_files) > 0:
            logger.info("🐍 Python project detected")
            # Sort Python files by priority
            sorted_python_files = sorted(has_python_files, 
                                       key=lambda x: python_entry_patterns.index(x[1].lower()) 
                                       if x[1].lower() in python_entry_patterns else 999)
            entry_file = sorted_python_files[0][0]
            return 'py', entry_file, has_requirements_txt, extract_path
        
        else:
            logger.warning("❓ Unknown project type")
            # Try to find any .py or .js file
            for rel_path, file, file_path in all_files:
                if file.lower().endswith('.py'):
                    return 'py', file_path, False, extract_path
                elif file.lower().endswith('.js'):
                    return 'js', file_path, False, extract_path
            
            return 'unknown', None, False, extract_path
            
    except Exception as e:
        logger.error(f"Error analyzing ZIP: {e}")
        return 'error', None, False, None

def install_python_dependencies(requirements_path, project_dir, message_obj):
    """Install Python dependencies from requirements.txt"""
    try:
        if os.path.exists(requirements_path):
            logger.info(f"📦 Installing Python dependencies from {requirements_path}")
            
            # Read requirements
            with open(requirements_path, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            if requirements:
                msg = send_simple_animation(message_obj.chat.id, 
                                          f"Installing {len(requirements)} dependencies...", 3)
                
                success_count = 0
                failed_count = 0
                
                for req in requirements[:10]:  # Limit to first 10 dependencies
                    try:
                        result = subprocess.run(
                            [sys.executable, '-m', 'pip', 'install', req],
                            capture_output=True, text=True, timeout=60,
                            cwd=project_dir
                        )
                        if result.returncode == 0:
                            success_count += 1
                        else:
                            failed_count += 1
                            logger.warning(f"Failed to install {req}: {result.stderr[:200]}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error installing {req}: {e}")
                
                try:
                    bot.edit_message_text(
                        f"✅ {apply_custom_font('Dependencies installed!')}\n"
                        f"✅ {apply_custom_font('Success')}: {success_count}\n"
                        f"❌ {apply_custom_font('Failed')}: {failed_count}",
                        message_obj.chat.id, msg.message_id
                    )
                except:
                    pass
                
                return True
        return True  # Return True even if no requirements.txt
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

# --- Helper Functions ---
def get_user_folder(user_id):
    """Get or create user's folder"""
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    """Get file upload limit for user - MODIFIED: ALL USERS HAVE NO LIMITS"""
    # All users now have unlimited uploads
    return float('inf')

def get_user_file_count(user_id):
    """Get number of files uploaded by user"""
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    """Check if a bot script is running"""
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                cleanup_script(script_key)
            return is_running
        except psutil.NoSuchProcess:
            cleanup_script(script_key)
            return False
        except Exception as e:
            logger.error(f"Error checking process: {e}")
            return False
    return False

def cleanup_script(script_key):
    """Clean up script resources"""
    if script_key in bot_scripts:
        script_info = bot_scripts[script_key]
        if 'log_file' in script_info and hasattr(script_info['log_file'], 'close'):
            try:
                if not script_info['log_file'].closed:
                    script_info['log_file'].close()
            except:
                pass
        del bot_scripts[script_key]
        logger.info(f"Cleaned up script: {script_key}")
        update_script_status(script_key, 'stopped')

def kill_process_tree(process_info):
    """Kill a process and all its children"""
    script_key = process_info.get('script_key', 'N/A')
    pid = None
    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close'):
            try:
                if not process_info['log_file'].closed:
                    process_info['log_file'].close()
            except:
                pass
        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
            pid = process.pid
            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                gone, alive = psutil.wait_procs(children, timeout=2)
                for p in alive:
                    try:
                        p.kill()
                    except:
                        pass
                try:
                    parent.terminate()
                    parent.wait(timeout=2)
                except psutil.TimeoutExpired:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
            except psutil.NoSuchProcess:
                logger.warning(f"Process {pid} already gone")
            except Exception as e:
                logger.error(f"Error killing process: {e}")
    except Exception as e:
        logger.error(f"Error in kill_process_tree: {e}")

# --- Package Installation ---
TELEGRAM_MODULES = {
    'telebot': 'pytelegrambotapi',
    'telegram': 'python-telegram-bot',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'aiogram': 'aiogram',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'dotenv': 'python-dotenv',
    'yaml': 'pyyaml',
    'aiohttp': 'aiohttp',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'requests': 'requests',
    'flask': 'flask',
    'django': 'django',
    'fastapi': 'fastapi',
}

def attempt_install_pip(module_name, message):
    """Attempt to install a Python package with animation"""
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
    if package_name is None:
        return False
    try:
        msg = send_simple_animation(message.chat.id, f"Installing {package_name}...", 2)
        command = [sys.executable, '-m', 'pip', 'install', package_name]
        result = subprocess.run(command, capture_output=True, text=True, check=False,
                                encoding='utf-8', errors='ignore', timeout=120)
        if result.returncode == 0:
            try:
                bot.edit_message_text(
                    f"✅ {apply_custom_font('Package Installed!')}\n📦 {package_name} {apply_custom_font('installed successfully!')}",
                    message.chat.id, msg.message_id
                )
            except:
                bot.send_message(message.chat.id, f"✅ {apply_custom_font('Package')} {package_name} {apply_custom_font('installed!')}")
            return True
        else:
            error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
            try:
                bot.edit_message_text(
                    f"❌ {apply_custom_font('Installation Failed')}\n{error_msg}",
                    message.chat.id, msg.message_id
                )
            except:
                pass
            return False
    except subprocess.TimeoutExpired:
        bot.send_message(message.chat.id, f"⏱️ {apply_custom_font('Installation timed out for')} {package_name}")
        return False
    except Exception as e:
        logger.error(f"Install error: {e}")
        return False

# --- Improved Script Running Functions with Better Error Handling ---
def run_script(script_path, script_owner_id, user_folder, file_name, message_obj, attempt=1):
    """Run Python script with improved error handling - MODIFIED for heavy task handling"""
    max_attempts = 3
    if attempt > max_attempts:
        bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Failed to run')} '{file_name}' {apply_custom_font('after')} {max_attempts} {apply_custom_font('attempts')}.")
        return
    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"Running script: {script_path} (Attempt {attempt})")
    try:
        if not os.path.exists(script_path):
            bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Script')} '{file_name}' {apply_custom_font('not found!')}")
            return
        
        # Check for syntax errors with better error handling
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                script_content = f.read()
            # Try to compile to check syntax
            compile(script_content, script_path, 'exec')
        except SyntaxError as e:
            error_msg = f"""
╔══════════════════════════════════════╗
║      ❌ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐘𝐍𝐓𝐀𝐗 𝐄𝐑𝐑𝐎𝐑 ❌    ║
╠══════════════════════════════════════╣
║
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ 🔍 {apply_custom_font('Error at line')}: {e.lineno}
║ 📝 {apply_custom_font('Message')}: {e.msg}
║
║ 💡 {apply_custom_font('Tip')}: {apply_custom_font('Fix syntax errors and upload again')}
║
╚══════════════════════════════════════╝
"""
            bot.send_message(message_obj.chat.id, error_msg)
            logger.error(f"Syntax error in {script_path}: {e}")
            return
        except Exception as e:
            logger.warning(f"Could not parse script: {e}")
            # Continue anyway - some scripts might have encoding issues but still run
        
        terminal_msg = f"""
╔══════════════════════════════════════╗
║      🚀 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐓𝐀𝐑𝐓𝐈𝐍𝐆 🚀     ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ 👤 {apply_custom_font('User')}: {script_owner_id}
║ 🔄 {apply_custom_font('Attempt')}: {attempt}/{max_attempts}
╚══════════════════════════════════════╝
"""
        msg = send_command_animation(message_obj.chat.id, "run_script", terminal_msg)
        
        log_file_path = os.path.join(LOGS_DIR, f"{script_key}.log")
        log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        
        # Run with Python
        process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=user_folder,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1
        )
        
        # Save script state for auto-recovery
        save_script_state(script_key, script_owner_id, file_name, script_path, 'py', process.pid, 'running')
        
        bot_scripts[script_key] = {
            'process': process,
            'file_name': file_name,
            'user_id': script_owner_id,
            'start_time': datetime.now(),
            'log_file': log_file,
            'log_path': log_file_path,
            'script_key': script_key,
            'script_path': script_path
        }
        
        # Wait a bit to see if script starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            success_msg = f"""
╔══════════════════════════════════════╗
║     ✅ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 ✅      ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ 🆔 {apply_custom_font('PID')}: {process.pid}
║ ⏱️ {apply_custom_font('Started')}: {datetime.now().strftime('%H:%M:%S')}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
╚══════════════════════════════════════╝
"""
            try:
                bot.edit_message_text(success_msg, message_obj.chat.id, msg.message_id)
            except:
                bot.send_message(message_obj.chat.id, success_msg)
            log_action(script_owner_id, "SCRIPT_START", f"Started {file_name} (PID: {process.pid})")
        else:
            log_file.close()
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                error_output = f.read()[-1500:]
            
            # Check for specific errors
            import_error_match = re.search(r"ModuleNotFoundError: No module named '(.+?)'", error_output)
            syntax_error_match = re.search(r"SyntaxError: (.+)", error_output)
            other_error_match = re.search(r"Error: (.+)", error_output)
            
            if import_error_match:
                module_name = import_error_match.group(1).strip()
                if attempt_install_pip(module_name, message_obj):
                    time.sleep(2)
                    run_script(script_path, script_owner_id, user_folder, file_name, message_obj, attempt + 1)
                    return
            elif syntax_error_match:
                error_details = syntax_error_match.group(1)
                error_msg = f"""
╔══════════════════════════════════════╗
║      ❌ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐘𝐍𝐓𝐀𝐗 𝐄𝐑𝐑𝐎𝐑 ❌    ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ ❗ {apply_custom_font('Exit Code')}: {process.returncode}
║ 📝 {apply_custom_font('Error')}: {error_details[:100]}
╠══════════════════════════════════════╣
{error_output[:300]}
╚══════════════════════════════════════╝
"""
            else:
                error_msg = f"""
╔══════════════════════════════════════╗
║     ❌ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐅𝐀𝐈𝐋𝐄𝐃 ❌       ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ ❗ {apply_custom_font('Exit Code')}: {process.returncode}
╠══════════════════════════════════════╣
{error_output[:400]}
╚══════════════════════════════════════╝
"""
            try:
                bot.edit_message_text(error_msg, message_obj.chat.id, msg.message_id)
            except:
                bot.send_message(message_obj.chat.id, error_msg)
            cleanup_script(script_key)
            update_script_status(script_key, 'crashed')
    except Exception as e:
        logger.error(f"Error running script: {e}", exc_info=True)
        bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Error')}: {str(e)[:200]}")

def run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj, attempt=1):
    """Run JavaScript/Node.js script with improved error handling"""
    max_attempts = 3
    if attempt > max_attempts:
        bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Failed to run')} '{file_name}' {apply_custom_font('after')} {max_attempts} {apply_custom_font('attempts')}.")
        return
    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"Running JS script: {script_path} (Attempt {attempt})")
    try:
        if not os.path.exists(script_path):
            bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Script')} '{file_name}' {apply_custom_font('not found!')}")
            return
        
        terminal_msg = f"""
╔══════════════════════════════════════╗
║      🟢 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐍𝐎𝐃𝐄.𝐉𝐒 🟢     ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ 👤 {apply_custom_font('User')}: {script_owner_id}
║ 🔄 {apply_custom_font('Attempt')}: {attempt}/{max_attempts}
╚══════════════════════════════════════╝
"""
        msg = send_command_animation(message_obj.chat.id, "run_js_script", terminal_msg)
        
        log_file_path = os.path.join(LOGS_DIR, f"{script_key}.log")
        log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        
        process = subprocess.Popen(
            ['node', script_path],
            cwd=user_folder,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1
        )
        
        # Save script state for auto-recovery
        save_script_state(script_key, script_owner_id, file_name, script_path, 'js', process.pid, 'running')
        
        bot_scripts[script_key] = {
            'process': process,
            'file_name': file_name,
            'user_id': script_owner_id,
            'start_time': datetime.now(),
            'log_file': log_file,
            'log_path': log_file_path,
            'script_key': script_key,
            'script_path': script_path,
            'type': 'js'
        }
        
        time.sleep(2)
        
        if process.poll() is None:
            success_msg = f"""
╔══════════════════════════════════════╗
║     ✅ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 ✅      ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ 🆔 {apply_custom_font('PID')}: {process.pid}
║ ⏱️ {apply_custom_font('Started')}: {datetime.now().strftime('%H:%M:%S')}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
╚══════════════════════════════════════╝
"""
            try:
                bot.edit_message_text(success_msg, message_obj.chat.id, msg.message_id)
            except:
                bot.send_message(message_obj.chat.id, success_msg)
        else:
            log_file.close()
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                error_output = f.read()[-1500:]
            
            match = re.search(r"Cannot find module '(.+?)'", error_output)
            if match:
                module_name = match.group(1).strip()
                # Try npm install
                try:
                    npm_msg = send_simple_animation(message_obj.chat.id, f"Installing {module_name} via npm...", 2)
                    subprocess.run(['npm', 'install', module_name], cwd=user_folder, 
                                  capture_output=True, timeout=60)
                    time.sleep(2)
                    run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj, attempt + 1)
                    return
                except:
                    pass
            
            error_msg = f"""
╔══════════════════════════════════════╗
║     ❌ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐅𝐀𝐈𝐋𝐄𝐃 ❌       ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font('File')}: {file_name[:25]}
║ ❗ {apply_custom_font('Exit Code')}: {process.returncode}
╠══════════════════════════════════════╣
{error_output[:400]}
╚══════════════════════════════════════╝
"""
            try:
                bot.edit_message_text(error_msg, message_obj.chat.id, msg.message_id)
            except:
                bot.send_message(message_obj.chat.id, error_msg)
            cleanup_script(script_key)
            update_script_status(script_key, 'crashed')
    except FileNotFoundError:
        bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Node.js not found! Install Node.js first')}.")
    except Exception as e:
        logger.error(f"Error running JS script: {e}", exc_info=True)
        bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Error')}: {str(e)[:200]}")

# --- ZIP Project Runner with Better Error Handling ---
def run_zip_project(zip_path, script_owner_id, original_filename, message_obj):
    """Run a ZIP project with intelligent analysis and better error handling"""
    try:
        # Create temp directory for extraction
        temp_dir = tempfile.mkdtemp(prefix=f"exu_{script_owner_id}_")
        logger.info(f"📦 Extracting ZIP to: {temp_dir}")
        
        # Analyze the ZIP project
        project_type, entry_file, has_requirements, project_dir = analyze_zip_project(zip_path, temp_dir)
        
        if project_type == 'error' or not entry_file:
            bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Failed to analyze ZIP project!')}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return
        
        # Show analysis results
        analysis_msg = f"""
╔══════════════════════════════════════╗
║      🔍 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐀𝐍𝐀𝐋𝐘𝐒𝐈𝐒 🔍     ║
╠══════════════════════════════════════╣
║ 📦 {apply_custom_font('Project')}: {original_filename}
║ 🏷️ {apply_custom_font('Type')}: {project_type.upper()}
║ 📄 {apply_custom_font('Entry')}: {os.path.basename(entry_file)}
║ 📊 {apply_custom_font('Requirements')}: {'✅' if has_requirements else '❌'}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
╚══════════════════════════════════════╝
"""
        send_command_animation(message_obj.chat.id, "analyze_zip", analysis_msg)
        
        # Handle based on project type
        if project_type == 'py':
            # Install dependencies if requirements.txt exists
            if has_requirements:
                requirements_path = os.path.join(project_dir, 'requirements.txt')
                install_python_dependencies(requirements_path, project_dir, message_obj)
                time.sleep(2)
            
            # Run Python script
            add_task_to_queue(run_script, entry_file, script_owner_id, project_dir, 
                            f"{original_filename}_project", message_obj, 1)
            
            # Save to user files as a project
            if script_owner_id not in user_files:
                user_files[script_owner_id] = []
            user_files[script_owner_id].append((f"{original_filename}_project", 'zip_py'))
            
        elif project_type == 'js':
            # Try to install npm packages if package.json exists
            package_json_path = os.path.join(project_dir, 'package.json')
            if os.path.exists(package_json_path):
                try:
                    npm_msg = send_simple_animation(message_obj.chat.id, "Installing npm packages...", 3)
                    subprocess.run(['npm', 'install'], cwd=project_dir, 
                                  capture_output=True, timeout=120)
                except:
                    pass
            
            # Run JavaScript script
            add_task_to_queue(run_js_script, entry_file, script_owner_id, project_dir, 
                            f"{original_filename}_project", message_obj, 1)
            
            # Save to user files as a project
            if script_owner_id not in user_files:
                user_files[script_owner_id] = []
            user_files[script_owner_id].append((f"{original_filename}_project", 'zip_js'))
            
        else:
            bot.send_message(message_obj.chat.id, 
                           f"❌ {apply_custom_font('Unsupported project type or no entry file found!')}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        logger.error(f"Error running ZIP project: {e}", exc_info=True)
        bot.send_message(message_obj.chat.id, f"❌ {apply_custom_font('Error running ZIP project')}: {str(e)[:200]}")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

# --- Keyboard Layouts ---
def get_main_keyboard(user_id):
    """Get main keyboard based on user type"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user_id == OWNER_ID or user_id in admin_ids:
        markup.row("📢 " + apply_custom_font("Updates"), "📤 " + apply_custom_font("Upload"))
        markup.row("📂 " + apply_custom_font("Files"), "🟢 " + apply_custom_font("Running"))
        markup.row("⚡ " + apply_custom_font("Speed"), "📊 " + apply_custom_font("Stats"))
        markup.row("💳 " + apply_custom_font("Subscriptions"), "📢 " + apply_custom_font("Broadcast"))
        markup.row("🔒 " + apply_custom_font("Lock"), "👑 " + apply_custom_font("Admin"))
        markup.row("📞 " + apply_custom_font("Contact"))
    else:
        markup.row("📢 " + apply_custom_font("Updates"), "📤 " + apply_custom_font("Upload"))
        markup.row("📂 " + apply_custom_font("Files"), "🟢 " + apply_custom_font("My Bots"))
        markup.row("⚡ " + apply_custom_font("Speed"), "📊 " + apply_custom_font("My Stats"))
        markup.row("📞 " + apply_custom_font("Contact"))
    return markup

def get_file_actions_keyboard(file_name, is_running=False):
    """Get inline keyboard for file actions"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.add(
            types.InlineKeyboardButton("🛑 " + apply_custom_font("Stop"), callback_data=f"stop_{file_name}"),
            types.InlineKeyboardButton("📋 " + apply_custom_font("Logs"), callback_data=f"logs_{file_name}")
        )
        markup.add(
            types.InlineKeyboardButton("🔄 " + apply_custom_font("Restart"), callback_data=f"restart_{file_name}")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("▶️ " + apply_custom_font("Run"), callback_data=f"run_{file_name}"),
            types.InlineKeyboardButton("🗑️ " + apply_custom_font("Delete"), callback_data=f"delete_{file_name}")
        )
        markup.add(
            types.InlineKeyboardButton("📥 " + apply_custom_font("Download"), callback_data=f"download_{file_name}")
        )
        markup.add(types.InlineKeyboardButton("🔙 " + apply_custom_font("Back"), callback_data="back_to_files"))
    return markup

# --- Command Handlers with Button Execution ---
@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command with animation - MODIFIED to show unlimited limits"""
    user_id = message.from_user.id
    username = message.from_user.username or apply_custom_font("Unknown")
    active_users.add(user_id)
    
    # Show animation for start command
    welcome_text = f"""
╔══════════════════════════════════════╗
║    🤖 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 🦁                 ║
╠══════════════════════════════════════╣
║
║  👋 {apply_custom_font('Welcome')}, {apply_custom_font(message.from_user.first_name)}!
║
║  📤 {apply_custom_font('Upload & Host your bot files')}
║  🚀 {apply_custom_font('Run Python & Node.js scripts')}
║  📊 {apply_custom_font('Monitor your running bots')}
║  💾 {apply_custom_font('Manage your files easily')}
║
╠══════════════════════════════════════╣
║  📌 {apply_custom_font('Your Limits')}:
║  📁 {apply_custom_font('Files')}: {get_user_file_count(user_id)}/∞ {apply_custom_font('(UNLIMITED)')}
║  💳 {apply_custom_font('Status')}: {'👑 ' + apply_custom_font('Owner') if user_id == OWNER_ID else '⭐ ' + apply_custom_font('Admin') if user_id in admin_ids else '🌟 ' + apply_custom_font('Premium') if user_id in user_subscriptions else '👤 ' + apply_custom_font('Free')}
║
╠══════════════════════════════════════╣
║  🔄 {apply_custom_font('Auto-Restart')}: ✅
║  🤖 {apply_custom_font('Crash Recovery')}: ✅
║  ⚡ {apply_custom_font('24/7 Uptime')}: ✅
║  📈 {apply_custom_font('Unlimited Uploads')}: ✅
║
╚══════════════════════════════════════╝
{apply_custom_font('Use buttons below to navigate!')} ⬇️
"""
    
    send_command_animation(message.chat.id, "/start", welcome_text)
    
    # Create keyboard with custom font
    send_formatted_message(message.chat.id, apply_custom_font("Choose an option:"), reply_markup=get_main_keyboard(user_id))
    log_action(user_id, "START", "Started the bot")

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handle /help command with animation"""
    help_text = """
╔══════════════════════════════════════╗
║       📚 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐇𝐄𝐋𝐏 📚          ║
╠══════════════════════════════════════╣
║
║ 📤 𝐅𝐢𝐥𝐞 𝐌𝐚𝐧𝐚𝐠𝐞𝐦𝐞𝐧𝐭:
║ • Upload - Upload unlimited files
║ • Files - View your files
║ • Delete - Delete a file
║
║ 🤖 𝐁𝐨𝐭 𝐂𝐨𝐧𝐭𝐫𝐨𝐥:
║ • Run - Run a script
║ • Stop - Stop a running script
║ • Logs - View script logs
║ • Running - See running scripts
║
║ 📊 𝐈𝐧𝐟𝐨𝐫𝐦𝐚𝐭𝐢𝐨𝐧:
║ • Stats - Bot statistics
║ • Speed - Check bot speed
║ • Status - Your account status
║
║ 🔄 𝐀𝐮𝐭𝐨-𝐑𝐞𝐬𝐭𝐚𝐫𝐭 𝐒𝐲𝐬𝐭𝐞𝐦:
║ • Scripts auto-restart on crash
║ • Server crash recovery
║ • 24/7 uptime guarantee
║ • Unlimited file uploads
║
╚══════════════════════════════════════╝
"""
    send_command_animation(message.chat.id, "/help", help_text)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Handle /stats command with animation"""
    # Show animation for stats command
    stats_text = f"""
╔══════════════════════════════════════╗
║       📊 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐒𝐓𝐀𝐓𝐒 📊         ║
╠══════════════════════════════════════╣
║
║ 🖥️ {apply_custom_font('CPU Usage')}: {psutil.cpu_percent()}%
║ 🧠 {apply_custom_font('Memory')}: {psutil.virtual_memory().percent}%
║ 💾 {apply_custom_font('Disk')}: {psutil.disk_usage('/').percent}%
║ ⏱️ {apply_custom_font('Uptime')}: {get_uptime()}
║ 🤖 {apply_custom_font('Running Bots')}: {len(bot_scripts)}
║ 👥 {apply_custom_font('Total Users')}: {len(active_users)}
║ 📁 {apply_custom_font('Total Files')}: {sum(len(files) for files in user_files.values())}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
║
╚══════════════════════════════════════╝
"""
    send_command_animation(message.chat.id, "/stats", stats_text)

@bot.message_handler(commands=['speed'])
def speed_command(message):
    """Handle /speed command with animation"""
    start_time = time.time()
    
    # Test speed with a simple operation
    test_result = sum(i*i for i in range(10000))
    
    latency = (time.time() - start_time) * 1000
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    
    speed_text = f"""
╔══════════════════════════════════════╗
║        ⚡ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐒𝐏𝐄𝐄𝐃 ⚡        ║
╠══════════════════════════════════════╣
║
║ 🏓 {apply_custom_font('Latency')}: {latency:.2f}ms
║ 🖥️ {apply_custom_font('CPU')}: {cpu}%
║ 🧠 {apply_custom_font('Memory')}: {memory}%
║ ⏱️ {apply_custom_font('Uptime')}: {get_uptime()}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
║
║ {'🟢 ' + apply_custom_font('Excellent!') if latency < 100 else '🟡 ' + apply_custom_font('Good') if latency < 500 else '🔴 ' + apply_custom_font('Slow')}
║
╚══════════════════════════════════════╝
"""
    send_command_animation(message.chat.id, "/speed", speed_text)

@bot.message_handler(commands=['running'])
def running_command(message):
    """Show running bots with animation"""
    user_id = message.from_user.id
    running_bots = []
    
    for script_key, info in bot_scripts.items():
        if info.get('process') and info['process'].poll() is None:
            if user_id == OWNER_ID or user_id in admin_ids or info.get('user_id') == user_id:
                uptime = datetime.now() - info.get('start_time', datetime.now())
                running_bots.append({
                    'file': info.get('file_name', 'Unknown'),
                    'user': info.get('user_id', 'Unknown'),
                    'pid': info.get('process', {}).pid if info.get('process') else 'N/A',
                    'uptime': str(uptime).split('.')[0]
                })
    
    if running_bots:
        text = """
╔══════════════════════════════════════╗
║      🟢 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐁𝐎𝐓𝐒 🟢           ║
╠══════════════════════════════════════╣
"""
        for i, bot_info in enumerate(running_bots, 1):
            text += f"║ {i}. 📄 {apply_custom_font(bot_info['file'][:20])}\n"
            text += f"║    👤 {apply_custom_font('User')}: {bot_info['user']}\n"
            text += f"║    🆔 {apply_custom_font('PID')}: {bot_info['pid']}\n"
            text += f"║    ⏱️ {apply_custom_font('Uptime')}: {bot_info['uptime']}\n"
            text += "║ ──────────────────────────────────\n"
        text += "╚══════════════════════════════════════╝"
    else:
        text = """
╔══════════════════════════════════════╗
║      🔴 𝐍𝐎 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐁𝐎𝐓𝐒 🔴        ║
╠══════════════════════════════════════╣
║
║ 𝐍𝐨 𝐬𝐜𝐫𝐢𝐩𝐭𝐬 𝐚𝐫𝐞 𝐜𝐮𝐫𝐫𝐞𝐧𝐭𝐥𝐲 𝐫𝐮𝐧𝐧𝐢𝐧𝐠.
║ 𝐔𝐩𝐥𝐨𝐚𝐝 𝐚 𝐟𝐢𝐥𝐞 𝐚𝐧𝐝 𝐫𝐮𝐧 𝐢𝐭!
║
╚══════════════════════════════════════╝
"""
    
    send_command_animation(message.chat.id, "/running", text)

@bot.message_handler(commands=['lock'])
def lock_command(message):
    """Lock/Unlock bot with animation"""
    global bot_locked
    user_id = message.from_user.id
    
    if user_id != OWNER_ID and user_id not in admin_ids:
        send_command_animation(message.chat.id, "/lock", "❌ " + apply_custom_font("You don't have permission!"))
        return
    
    bot_locked = not bot_locked
    status = "🔒 " + apply_custom_font("LOCKED") if bot_locked else "🔓 " + apply_custom_font("UNLOCKED")
    
    lock_text = f"""
╔══════════════════════════════════════╗
║         🔐 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐒𝐓𝐀𝐓𝐔𝐒 🔐       ║
╠══════════════════════════════════════╣
║
║ {apply_custom_font('Status')}: {status}
║ {apply_custom_font('By')}: {apply_custom_font(message.from_user.first_name)}
║ {apply_custom_font('Time')}: {datetime.now().strftime('%H:%M:%S')}
║
╚══════════════════════════════════════╝
"""
    send_command_animation(message.chat.id, "/lock", lock_text)

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    """Broadcast message to all users (Admin only)"""
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        send_command_animation(message.chat.id, "/broadcast", "❌ " + apply_custom_font("You don't have permission!"))
        return
    
    msg = bot.reply_to(message, "📢 " + apply_custom_font("Send the message you want to broadcast:"))
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """Process broadcast message"""
    broadcast_text = message.text
    if not broadcast_text:
        send_command_animation(message.chat.id, "broadcast", "❌ " + apply_custom_font("Please send a text message!"))
        return
    
    progress_msg = bot.send_message(message.chat.id, "📢 " + apply_custom_font("Starting EXU CODER broadcast..."))
    success = 0
    failed = 0
    total = len(active_users)
    
    for i, user_id in enumerate(active_users):
        try:
            formatted_msg = f"""
╔══════════════════════════════════════╗
║      📢 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 🦁 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓 📢    ║
╠══════════════════════════════════════╣
║
{broadcast_text}
║
╚══════════════════════════════════════╝
"""
            bot.send_message(user_id, formatted_msg)
            success += 1
        except:
            failed += 1
        
        # Update progress every 10 users
        if (i + 1) % 10 == 0:
            try:
                bar_length = 4
                progress = min((i + 1) * bar_length // total, bar_length)
                bar = "🟩" * progress + "⬜" * (bar_length - progress)
                bot.edit_message_text(
                    f"⚙️ 𝐋ᴏᴀᴅɪɴɢ... ({int((i+1)/total*100)}%)\n[{bar}] " + apply_custom_font("Broadcasting..."),
                    message.chat.id, progress_msg.message_id
                )
            except:
                pass
    
    result_text = f"""
╔══════════════════════════════════════╗
║     ✅ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓 ✅      ║
╠══════════════════════════════════════╣
║
║ 📤 {apply_custom_font('Total')}: {total}
║ ✅ {apply_custom_font('Success')}: {success}
║ ❌ {apply_custom_font('Failed')}: {failed}
║
╚══════════════════════════════════════╝
"""
    try:
        bot.edit_message_text(result_text, message.chat.id, progress_msg.message_id)
    except:
        bot.send_message(message.chat.id, result_text)

# --- Text Message Handlers (Button Execution) ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Handle text messages (button presses)"""
    user_id = message.from_user.id
    text = message.text
    active_users.add(user_id)
    
    if bot_locked and user_id not in admin_ids and user_id != OWNER_ID:
        send_command_animation(message.chat.id, "command", "🔒 " + apply_custom_font("Bot is locked!"))
        return
    
    # Remove custom font for comparison
    text_for_check = text.replace('𝐔', 'U').replace('𝐩', 'p').replace('𝐥', 'l').replace('𝐨', 'o').replace('𝐚', 'a').replace('𝐝', 'd')
    text_for_check = text_for_check.replace('𝐅', 'F').replace('𝐢', 'i').replace('𝐞', 'e').replace('𝐬', 's')
    text_for_check = text_for_check.replace('𝐑', 'R').replace('𝐮', 'u').replace('𝐧', 'n').replace('𝐠', 'g')
    text_for_check = text_for_check.replace('𝐒', 'S').replace('𝐭', 't').replace('𝐜', 'c').replace('𝐤', 'k')
    text_for_check = text_for_check.replace('𝐌', 'M').replace('𝐲', 'y').replace('𝐁', 'B').replace('𝐂', 'C')
    text_for_check = text_for_check.replace('𝐀', 'A').replace('𝐦', 'm').replace('𝐈', 'I').replace('𝐕', 'V')
    
    # Check for specific button patterns without font
    if "Updates" in text or "𝐔𝐩𝐝𝐚𝐭𝐞𝐬" in text:
        send_command_animation(message.chat.id, "Updates", 
                             f"📢 {apply_custom_font('Join our EXU CODER updates')}:\n{UPDATE_CHANNEL}")
    elif "Upload" in text or "𝐔𝐩𝐥𝐨𝐚𝐝" in text:
        handle_upload_request(message)
    elif "Files" in text or "𝐅𝐢𝐥𝐞𝐬" in text:
        show_user_files(message)
    elif ("Running" in text or "My Bots" in text or 
          "𝐑𝐮𝐧𝐧𝐢𝐧𝐠" in text or "𝐌𝐲 𝐁𝐨𝐭𝐬" in text):
        running_command(message)
    elif "Speed" in text or "𝐒𝐩𝐞𝐞𝐝" in text:
        speed_command(message)
    elif "Stats" in text or "My Stats" in text or "𝐒𝐭𝐚𝐭𝐬" in text or "𝐌𝐲 𝐒𝐭𝐚𝐭𝐬" in text:
        stats_command(message)
    elif "Subscriptions" in text or "𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧𝐬" in text:
        show_subscriptions(message)
    elif "Broadcast" in text or "𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭" in text:
        broadcast_command(message)
    elif "Lock" in text or "𝐋𝐨𝐜𝐤" in text:
        lock_command(message)
    elif "Admin" in text or "𝐀𝐝𝐦𝐢𝐧" in text:
        show_admin_panel(message)
    elif "Contact" in text or "𝐂𝐨𝐧𝐭𝐚𝐜𝐭" in text:
        send_command_animation(message.chat.id, "Contact", 
                             f"📞 {apply_custom_font('Contact')}: {YOUR_USERNAME}")
    else:
        # Show main menu
        start_command(message)

def handle_upload_request(message):
    """Handle file upload request - MODIFIED: No limits check"""
    user_id = message.from_user.id
    current_count = get_user_file_count(user_id)
    
    upload_text = f"""
╔══════════════════════════════════════╗
║       📤 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐔𝐏𝐋𝐎𝐀𝐃 📤       ║
╠══════════════════════════════════════╣
║
║ {apply_custom_font('Send your file now!')}
║
║ {apply_custom_font('Supported formats')}:
║ • {apply_custom_font('Python')} (.py)
║ • {apply_custom_font('JavaScript')} (.js)
║ • {apply_custom_font('ZIP archives')} (.zip)
║
║ 📁 {apply_custom_font('Files')}: {current_count} {apply_custom_font('(UNLIMITED UPLOADS)')}
║
╚══════════════════════════════════════╝
"""
    send_command_animation(message.chat.id, "Upload", upload_text)

def show_user_files(message):
    """Show user's files with actions"""
    user_id = message.from_user.id
    files = user_files.get(user_id, [])
    
    if not files:
        text = """
╔══════════════════════════════════════╗
║       📂 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐅𝐈𝐋𝐄𝐒 📂       ║
╠══════════════════════════════════════╣
║
║ 𝐘𝐨𝐮 𝐡𝐚𝐯𝐞𝐧'𝐭 𝐮𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐚𝐧𝐲 𝐟𝐢𝐥𝐞𝐬 𝐲𝐞𝐭!
║
║ 𝐔𝐬𝐞 📤 𝐔𝐩𝐥𝐨𝐚𝐝 𝐭𝐨 𝐠𝐞𝐭 𝐬𝐭𝐚𝐫𝐭𝐞𝐝.
║
╚══════════════════════════════════════╝
"""
        send_command_animation(message.chat.id, "Files", text)
        return
    
    text = """
╔══════════════════════════════════════╗
║       📂 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐅𝐈𝐋𝐄𝐒 📂       ║
╠══════════════════════════════════════╣
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i, (file_name, file_type) in enumerate(files, 1):
        is_running = is_bot_running(user_id, file_name)
        status = "🟢" if is_running else "🔴"
        type_icon = "🐍" if file_type == "py" else "🟨" if file_type == "js" else "📦" if "zip" in file_type else "📄"
        text += f"║ {i}. {status} {type_icon} {apply_custom_font(file_name[:25])}\n"
        markup.add(types.InlineKeyboardButton(
            f"{status} {apply_custom_font(file_name[:15])}",
            callback_data=f"file_{file_name}"
        ))
    
    text += "╚══════════════════════════════════════╝\n" + apply_custom_font("Select a file for actions:")
    
    send_command_animation(message.chat.id, "Files", text)
    
    # Edit message to add buttons
    try:
        bot.edit_message_reply_markup(message.chat.id, message.message_id + 1, reply_markup=markup)
    except:
        send_formatted_message(message.chat.id, apply_custom_font("Select a file:"), reply_markup=markup)

def show_subscriptions(message):
    """Show subscription management (Admin only)"""
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        send_command_animation(message.chat.id, "Subscriptions", "❌ " + apply_custom_font("Admin only!"))
        return
    
    active_subs = {uid: data for uid, data in user_subscriptions.items()
                   if data['expiry'] > datetime.now()}
    text = f"""
╔══════════════════════════════════════╗
║     💳 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐔𝐁𝐒𝐂𝐑𝐈𝐏𝐓𝐈𝐎𝐍𝐒 💳   ║
╠══════════════════════════════════════╣
║
║ {apply_custom_font('Active')}: {len(active_subs)}
║ {apply_custom_font('Total Ever')}: {len(user_subscriptions)}
║ {apply_custom_font('All users have unlimited uploads')}
║
"""
    for uid, data in list(active_subs.items())[:10]:
        remaining = data['expiry'] - datetime.now()
        text += f"║ 👤 {uid}: {remaining.days}d {apply_custom_font('left')}\n"
    
    text += """║
╠══════════════════════════════════════╣
║ {apply_custom_font('Add sub')}: /subscribe <id> <days>
╚══════════════════════════════════════╝
"""
    send_command_animation(message.chat.id, "Subscriptions", text)

def show_admin_panel(message):
    """Show admin panel"""
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        send_command_animation(message.chat.id, "Admin", "❌ " + apply_custom_font("Admin only!"))
        return
    
    # Get auto-restart stats
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM persistent_scripts WHERE status = 'running' ''')
    running = c.fetchone()[0] or 0
    
    c.execute('''SELECT COUNT(*) FROM persistent_scripts WHERE auto_restart = 1''')
    auto_restart = c.fetchone()[0] or 0
    
    c.execute('''SELECT COUNT(*) FROM persistent_scripts WHERE status = 'crashed' ''')
    crashed = c.fetchone()[0] or 0
    
    # Get total files count
    total_files = sum(len(files) for files in user_files.values())
    conn.close()
    
    admin_text = f"""
╔══════════════════════════════════════╗
║       👑 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐀𝐃𝐌𝐈𝐍 👑       ║
╠══════════════════════════════════════╣
║
║ 📊 {apply_custom_font('Statistics')}:
║ • {apply_custom_font('Total Users')}: {len(active_users)}
║ • {apply_custom_font('Active Subs')}: {len([u for u, d in user_subscriptions.items() if d['expiry'] > datetime.now()])}
║ • {apply_custom_font('Running Bots')}: {len([k for k in bot_scripts if bot_scripts[k].get('process')])}
║ • {apply_custom_font('Total Files')}: {total_files}
║ • {apply_custom_font('Admins')}: {len(admin_ids)}
║
║ 🔄 {apply_custom_font('Auto-Restart')}:
║ • {apply_custom_font('Running')}: {running}
║ • {apply_custom_font('Auto-restart')}: {auto_restart}
║ • {apply_custom_font('Crashed')}: {crashed}
║
║ ⚙️ {apply_custom_font('Controls')}:
║ • {apply_custom_font('Broadcast - Send to all')}
║ • {apply_custom_font('Subscribe - Add subscription')}
║ • {apply_custom_font('Lock - Lock/unlock bot')}
║ • {apply_custom_font('Stopall - Stop all bots')}
║
╚══════════════════════════════════════╝
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛑 " + apply_custom_font("Stop All"), callback_data="admin_stopall"),
        types.InlineKeyboardButton("🔄 " + apply_custom_font("Auto-Restart"), callback_data="admin_autorestart")
    )
    markup.add(
        types.InlineKeyboardButton("📊 " + apply_custom_font("Full Stats"), callback_data="admin_fullstats"),
        types.InlineKeyboardButton("📋 " + apply_custom_font("View Logs"), callback_data="admin_logs")
    )
    
    send_command_animation(message.chat.id, "Admin", admin_text)
    
    # Edit message to add buttons
    try:
        bot.edit_message_reply_markup(message.chat.id, message.message_id + 1, reply_markup=markup)
    except:
        send_formatted_message(message.chat.id, apply_custom_font("Admin Controls:"), reply_markup=markup)

# --- Enhanced File Upload Handler with ZIP Support ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Handle document uploads with animation - MODIFIED: No limits"""
    user_id = message.from_user.id
    
    file_name = message.document.file_name
    file_size = message.document.file_size
    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    
    allowed_extensions = ['py', 'js', 'zip', 'json', 'txt', 'env']
    if file_ext not in allowed_extensions:
        send_command_animation(message.chat.id, "upload", 
                             f"❌ {apply_custom_font('Unsupported type')}: .{file_ext}")
        return
    
    # Show upload animation
    upload_msg = send_simple_animation(message.chat.id, f"Uploading {file_name}...")
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # Update user files
        if user_id not in user_files:
            user_files[user_id] = []
        user_files[user_id] = [(n, t) for n, t in user_files[user_id] if n != file_name]
        user_files[user_id].append((file_name, file_ext))
        
        # Save to database
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO user_files
            (user_id, file_name, file_type, upload_time, file_size)
            VALUES (?, ?, ?, ?, ?)''',
                      (user_id, file_name, file_ext, datetime.now().isoformat(), file_size))
            conn.commit()
            conn.close()
        except:
            pass
        
        success_text = f"""
╔══════════════════════════════════════╗
║       ✅ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐔𝐂𝐂𝐄𝐒𝐒 ✅       ║
╠══════════════════════════════════════╣
║
║ 📄 {apply_custom_font('File')}: {apply_custom_font(file_name[:25])}
║ 📦 {apply_custom_font('Size')}: {format_size(file_size)}
║ ✅ {apply_custom_font('Upload complete!')}
║ ∞  {apply_custom_font('UNLIMITED UPLOADS')}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
║
╚══════════════════════════════════════╝
"""
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        if file_ext in ['py', 'js']:
            markup.add(
                types.InlineKeyboardButton("▶️ " + apply_custom_font("Run Now"), callback_data=f"run_{file_name}"),
                types.InlineKeyboardButton("📂 " + apply_custom_font("View Files"), callback_data="back_to_files")
            )
        elif file_ext == 'zip':
            markup.add(
                types.InlineKeyboardButton("🔍 " + apply_custom_font("Analyze & Run"), callback_data=f"analyze_zip_{file_name}"),
                types.InlineKeyboardButton("📂 " + apply_custom_font("View Files"), callback_data="back_to_files")
            )
        else:
            markup.add(types.InlineKeyboardButton("📂 " + apply_custom_font("View Files"), callback_data="back_to_files"))
        
        try:
            bot.edit_message_text(success_text, message.chat.id, upload_msg.message_id,
                                  reply_markup=markup)
        except:
            bot.send_message(message.chat.id, success_text, reply_markup=markup)
            
    except Exception as e:
        error_text = f"""
╔══════════════════════════════════════╗
║       ❌ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐄𝐑𝐑𝐎𝐑 ❌        ║
╠══════════════════════════════════════╣
║
║ ❌ {apply_custom_font('Upload failed!')}
║ 🔍 {apply_custom_font('Error')}: {str(e)[:50]}
║
╚══════════════════════════════════════╝
"""
        try:
            bot.edit_message_text(error_text, message.chat.id, upload_msg.message_id)
        except:
            bot.send_message(message.chat.id, error_text)

# --- Callback Query Handler ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle all callback queries"""
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data.startswith("file_"):
            file_name = data[5:]
            show_file_actions(call, file_name)
        elif data.startswith("run_"):
            file_name = data[4:]
            run_user_script(call, file_name)
        elif data.startswith("stop_"):
            file_name = data[5:]
            stop_user_script(call, file_name)
        elif data.startswith("delete_"):
            file_name = data[7:]
            delete_user_file(call, file_name)
        elif data.startswith("download_"):
            file_name = data[9:]
            download_user_file(call, file_name)
        elif data.startswith("logs_"):
            file_name = data[5:]
            show_script_logs(call, file_name)
        elif data.startswith("restart_"):
            file_name = data[8:]
            restart_user_script(call, file_name)
        elif data.startswith("analyze_zip_"):
            file_name = data[12:]
            analyze_and_run_zip(call, file_name)
        elif data == "back_to_files":
            show_user_files_callback(call)
        elif data == "admin_stopall":
            stop_all_bots(call)
        elif data == "admin_autorestart":
            show_auto_restart_panel(call)
        elif data == "admin_fullstats":
            stats_command(call.message)
            bot.answer_callback_query(call.id, "📊 " + apply_custom_font("Stats refreshed!"))
        elif data == "admin_logs":
            show_admin_logs(call)
        elif data.startswith("confirm_delete_"):
            file_name = data[15:]
            confirm_delete_file(call, file_name)
        elif data.startswith("cancel_delete_"):
            bot.answer_callback_query(call.id, "❌ " + apply_custom_font("Cancelled"))
            show_user_files_callback(call)
    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        bot.answer_callback_query(call.id, f"❌ {apply_custom_font('Error')}: {str(e)[:50]}")

def analyze_and_run_zip(call, file_name):
    """Analyze and run a ZIP project"""
    user_id = call.from_user.id
    user_folder = get_user_folder(user_id)
    zip_path = os.path.join(user_folder, file_name)
    
    if not os.path.exists(zip_path):
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("ZIP file not found!"))
        return
    
    bot.answer_callback_query(call.id, "🔍 " + apply_custom_font("Analyzing ZIP..."))
    
    # Run ZIP project using task queue for heavy task handling
    add_task_to_queue(run_zip_project, zip_path, user_id, file_name, call.message)

def show_file_actions(call, file_name):
    """Show actions for a specific file"""
    user_id = call.from_user.id
    is_running = is_bot_running(user_id, file_name)
    file_type = "py"
    for name, ftype in user_files.get(user_id, []):
        if name == file_name:
            file_type = ftype
            break
    
    type_icon = "🐍" if file_type == "py" else "🟨" if file_type == "js" else "📦" if "zip" in file_type else "📄"
    status = "🟢 " + apply_custom_font("Running") if is_running else "🔴 " + apply_custom_font("Stopped")
    text = f"""
╔══════════════════════════════════════╗
║       📄 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐅𝐈𝐋𝐄 📄         ║
╠══════════════════════════════════════╣
║
║ {type_icon} {apply_custom_font('Name')}: {apply_custom_font(file_name[:25])}
║ 📁 {apply_custom_font('Type')}: {file_type.upper()}
║ 📊 {apply_custom_font('Status')}: {status}
║ 🔄 {apply_custom_font('Auto-restart')}: ✅
║
╚══════════════════════════════════════╝
"""
    markup = get_file_actions_keyboard(file_name, is_running)
    
    # Special handling for ZIP files
    if file_type == 'zip':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔍 " + apply_custom_font("Analyze & Run"), callback_data=f"analyze_zip_{file_name}"),
            types.InlineKeyboardButton("🗑️ " + apply_custom_font("Delete"), callback_data=f"delete_{file_name}")
        )
        markup.add(
            types.InlineKeyboardButton("📥 " + apply_custom_font("Download"), callback_data=f"download_{file_name}")
        )
        markup.add(types.InlineKeyboardButton("🔙 " + apply_custom_font("Back"), callback_data="back_to_files"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    bot.answer_callback_query(call.id)

def run_user_script(call, file_name):
    """Run a user's script"""
    user_id = call.from_user.id
    user_folder = get_user_folder(user_id)
    script_path = os.path.join(user_folder, file_name)
    
    if not os.path.exists(script_path):
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("File not found!"))
        return
    
    if is_bot_running(user_id, file_name):
        bot.answer_callback_query(call.id, "⚠️ " + apply_custom_font("Already running!"))
        return
    
    bot.answer_callback_query(call.id, "🚀 " + apply_custom_font("Starting..."))
    
    if file_name.endswith('.py'):
        add_task_to_queue(run_script, script_path, user_id, user_folder, file_name, call.message)
    elif file_name.endswith('.js'):
        add_task_to_queue(run_js_script, script_path, user_id, user_folder, file_name, call.message)
    else:
        bot.send_message(call.message.chat.id, "❌ " + apply_custom_font("Unsupported type!"))

def stop_user_script(call, file_name):
    """Stop a running script"""
    user_id = call.from_user.id
    script_key = f"{user_id}_{file_name}"
    
    if script_key not in bot_scripts:
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("Script not running!"))
        return
    
    bot.answer_callback_query(call.id, "🛑 " + apply_custom_font("Stopping..."))
    
    stop_text = f"""
╔══════════════════════════════════════╗
║       🛑 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐓𝐎𝐏𝐏𝐈𝐍𝐆 🛑     ║
╠══════════════════════════════════════╣
║
║ 📄 {apply_custom_font(file_name[:25])}
║ ⏳ {apply_custom_font('Please wait...')}
║
╚══════════════════════════════════════╝
"""
    
    try:
        bot.edit_message_text(stop_text, call.message.chat.id, call.message.message_id)
    except:
        pass
    
    script_info = bot_scripts.get(script_key)
    if script_info:
        kill_process_tree(script_info)
        cleanup_script(script_key)
        update_script_status(script_key, 'stopped')
        
        time.sleep(1)
        success_text = f"""
╔══════════════════════════════════════╗
║       ✅ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐒𝐓𝐎𝐏𝐏𝐄𝐃 ✅      ║
╠══════════════════════════════════════╣
║
║ 📄 {apply_custom_font(file_name[:25])}
║ ✅ {apply_custom_font('Successfully stopped!')}
║
╚══════════════════════════════════════╝
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("▶️ " + apply_custom_font("Run Again"), callback_data=f"run_{file_name}"),
            types.InlineKeyboardButton("🔙 " + apply_custom_font("Back"), callback_data="back_to_files")
        )
        
        try:
            bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id,
                                  reply_markup=markup)
        except:
            bot.send_message(call.message.chat.id, success_text, reply_markup=markup)
        
        log_action(user_id, "SCRIPT_STOP", f"Stopped {file_name}")

def delete_user_file(call, file_name):
    """Confirm file deletion"""
    user_id = call.from_user.id
    
    if is_bot_running(user_id, file_name):
        bot.answer_callback_query(call.id, "⚠️ " + apply_custom_font("Stop the script first!"))
        return
    
    confirm_text = f"""
╔══════════════════════════════════════╗
║      ⚠️ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐃𝐄𝐋𝐄𝐓𝐄? ⚠️      ║
╠══════════════════════════════════════╣
║
║ {apply_custom_font('Are you sure?')}
║ 📄 {apply_custom_font(file_name[:25])}
║
║ ⚠️ {apply_custom_font('This cannot be undone!')}
║
╚══════════════════════════════════════╝
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ " + apply_custom_font("Yes, Delete"), callback_data=f"confirm_delete_{file_name}"),
        types.InlineKeyboardButton("❌ " + apply_custom_font("No"), callback_data=f"cancel_delete_{file_name}")
    )
    
    try:
        bot.edit_message_text(confirm_text, call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
    except:
        pass
    
    bot.answer_callback_query(call.id)

def confirm_delete_file(call, file_name):
    """Actually delete the file"""
    user_id = call.from_user.id
    user_folder = get_user_folder(user_id)
    file_path = os.path.join(user_folder, file_name)
    
    delete_text = f"""
╔══════════════════════════════════════╗
║       🗑️ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐃𝐄𝐋𝐄𝐓𝐈𝐍𝐆 🗑️     ║
╠══════════════════════════════════════╣
║
║ 📄 {apply_custom_font(file_name[:25])}
║ ⏳ {apply_custom_font('Please wait...')}
║
╚══════════════════════════════════════╝
"""
    
    try:
        bot.edit_message_text(delete_text, call.message.chat.id, call.message.message_id)
    except:
        pass
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            
            # Update user files
            if user_id in user_files:
                user_files[user_id] = [(n, t) for n, t in user_files[user_id] if n != file_name]
            
            # Remove from database
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                c = conn.cursor()
                c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
                c.execute('DELETE FROM persistent_scripts WHERE user_id = ? AND file_name = ?', (user_id, file_name))
                conn.commit()
                conn.close()
            except:
                pass
            
            time.sleep(1)
            success_text = f"""
╔══════════════════════════════════════╗
║       ✅ 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐃𝐄𝐋𝐄𝐓𝐄𝐃 ✅       ║
╠══════════════════════════════════════╣
║
║ 📄 {apply_custom_font(file_name[:25])}
║ ✅ {apply_custom_font('Successfully deleted!')}
║
╚══════════════════════════════════════╝
"""
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📂 " + apply_custom_font("Back to Files"), callback_data="back_to_files"))
            
            try:
                bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id,
                                      reply_markup=markup)
            except:
                bot.send_message(call.message.chat.id, success_text, reply_markup=markup)
            
            bot.answer_callback_query(call.id, "✅ " + apply_custom_font("Deleted!"))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {apply_custom_font('Error')}: {str(e)[:30]}")

def download_user_file(call, file_name):
    """Send file to user"""
    user_id = call.from_user.id
    user_folder = get_user_folder(user_id)
    file_path = os.path.join(user_folder, file_name)
    
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("File not found!"))
        return
    
    bot.answer_callback_query(call.id, "📥 " + apply_custom_font("Sending..."))
    
    try:
        with open(file_path, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption=f"📄 {file_name}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ {apply_custom_font('Error')}: {str(e)[:100]}")

def show_script_logs(call, file_name):
    """Show logs for a script"""
    user_id = call.from_user.id
    script_key = f"{user_id}_{file_name}"
    log_path = os.path.join(LOGS_DIR, f"{script_key}.log")
    
    if not os.path.exists(log_path):
        bot.answer_callback_query(call.id, "📋 " + apply_custom_font("No logs"))
        return
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.read()[-2000:]
            if not logs.strip():
                logs = apply_custom_font("No output yet...")
        
        log_text = f"""
╔══════════════════════════════════════╗
║       📋 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐋𝐎𝐆𝐒 📋         ║
╠══════════════════════════════════════╣
║ 📄 {apply_custom_font(file_name[:25])}
╠══════════════════════════════════════╣
{logs[:1500]}
╚══════════════════════════════════════╝
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔄 " + apply_custom_font("Refresh"), callback_data=f"logs_{file_name}"),
            types.InlineKeyboardButton("🔙 " + apply_custom_font("Back"), callback_data=f"file_{file_name}")
        )
        
        try:
            bot.edit_message_text(log_text, call.message.chat.id, call.message.message_id,
                                  reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "📋 " + apply_custom_font("Logs unchanged"))
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {apply_custom_font('Error')}: {str(e)[:30]}")

def restart_user_script(call, file_name):
    """Restart a script"""
    user_id = call.from_user.id
    script_key = f"{user_id}_{file_name}"
    
    if script_key in bot_scripts:
        script_info = bot_scripts.get(script_key)
        if script_info:
            kill_process_tree(script_info)
            cleanup_script(script_key)
            time.sleep(1)
    
    run_user_script(call, file_name)

def show_user_files_callback(call):
    """Show files via callback"""
    class FakeMessage:
        def __init__(self, call):
            self.chat = call.message.chat
            self.from_user = call.from_user
    
    show_user_files(FakeMessage(call))
    bot.answer_callback_query(call.id)

def stop_all_bots(call):
    """Stop all running bots (Admin only)"""
    user_id = call.from_user.id
    
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("Admin only!"))
        return
    
    bot.answer_callback_query(call.id, "🛑 " + apply_custom_font("Stopping all EXU CODER bots..."))
    
    stopped = 0
    for script_key in list(bot_scripts.keys()):
        try:
            script_info = bot_scripts[script_key]
            kill_process_tree(script_info)
            cleanup_script(script_key)
            update_script_status(script_key, 'stopped')
            stopped += 1
        except:
            pass
    
    bot.send_message(call.message.chat.id, f"✅ {apply_custom_font('Stopped')} {stopped} {apply_custom_font('bots!')}")

def show_auto_restart_panel(call):
    """Show auto-restart management panel"""
    user_id = call.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("Admin only!"))
        return
    
    # Get stats
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM persistent_scripts WHERE status = 'running' ''')
    running = c.fetchone()[0] or 0
    
    c.execute('''SELECT COUNT(*) FROM persistent_scripts WHERE auto_restart = 1''')
    auto_restart = c.fetchone()[0] or 0
    
    c.execute('''SELECT COUNT(*) FROM persistent_scripts WHERE status = 'crashed' ''')
    crashed = c.fetchone()[0] or 0
    conn.close()
    
    panel_text = f"""
╔══════════════════════════════════════╗
║     🔄 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑: 𝐀𝐔𝐓𝐎-𝐑𝐄𝐒𝐓𝐀𝐑𝐓 🔄   ║
╠══════════════════════════════════════╣
║
║ 📊 {apply_custom_font('Statistics')}:
║ • {apply_custom_font('Running')}: {running}
║ • {apply_custom_font('Auto-restart enabled')}: {auto_restart}
║ • {apply_custom_font('Crashed')}: {crashed}
║ • {apply_custom_font('Total tracked')}: {running + crashed}
║
║ ⚙️ {apply_custom_font('Controls')}:
║ • {apply_custom_font('Recover all scripts')}
║ • {apply_custom_font('Disable/Enable auto-restart')}
║ • {apply_custom_font('Clear crashed records')}
║ • {apply_custom_font('Manual recovery')}
║
╚══════════════════════════════════════╝
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 " + apply_custom_font("Recover All"), callback_data="recover_all"),
        types.InlineKeyboardButton("🛑 " + apply_custom_font("Disable Auto-Restart"), callback_data="disable_auto")
    )
    markup.add(
        types.InlineKeyboardButton("🚀 " + apply_custom_font("Enable Auto-Restart"), callback_data="enable_auto"),
        types.InlineKeyboardButton("🗑️ " + apply_custom_font("Clear Crashed"), callback_data="clear_crashed")
    )
    markup.add(
        types.InlineKeyboardButton("📊 " + apply_custom_font("Refresh Stats"), callback_data="refresh_auto"),
        types.InlineKeyboardButton("🔙 " + apply_custom_font("Back"), callback_data="back_to_admin")
    )
    
    try:
        bot.edit_message_text(panel_text, call.message.chat.id, call.message.message_id,
                              reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, panel_text, reply_markup=markup)
    
    bot.answer_callback_query(call.id)

def show_admin_logs(call):
    """Show admin logs"""
    user_id = call.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        bot.answer_callback_query(call.id, "❌ " + apply_custom_font("Admin only!"))
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id, action, details, timestamp FROM bot_logs ORDER BY id DESC LIMIT 20')
        logs = c.fetchall()
        conn.close()
        
        if logs:
            text = "📋 " + apply_custom_font("EXU CODER: RECENT LOGS") + "\n"
            for log in logs:
                text += f"👤 {log[0]} | {log[1]}\n{log[2][:30]}...\n🕐 {log[3][:16]}\n"
        else:
            text = "📋 " + apply_custom_font("No logs.")
        
        bot.send_message(call.message.chat.id, text[:4000])
        bot.answer_callback_query(call.id, "📋 " + apply_custom_font("Logs sent!"))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ {apply_custom_font('Error')}: {str(e)[:30]}")

# --- Cleanup on Exit ---
def cleanup_on_exit():
    """Cleanup running processes on exit"""
    logger.info(apply_custom_font("Cleaning up EXU CODER..."))
    
    # Save running states first
    save_all_running_states()
    
    # Then cleanup
    for script_key in list(bot_scripts.keys()):
        try:
            script_info = bot_scripts[script_key]
            kill_process_tree(script_info)
        except:
            pass
    
    logger.info(apply_custom_font("Cleanup complete."))

atexit.register(cleanup_on_exit)

# --- Main Function with Auto-Restart System ---
def main():
    """Main function to run the bot with auto-restart system"""
    logger.info("=" * 50)
    logger.info("🤖 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 🦁 𝐁𝐨𝐭...")
    logger.info(apply_custom_font(f"Base Directory: {BASE_DIR}"))
    logger.info("=" * 50)
    
    # Start Flask keep-alive
    keep_alive()
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Start task queue manager for heavy tasks
    queue_thread = threading.Thread(target=manage_task_queue, daemon=True)
    queue_thread.start()
    logger.info("✅ Task queue manager started")
    
    # Start health monitor in background
    health_thread = threading.Thread(target=health_check_monitor, daemon=True)
    health_thread.start()
    logger.info("✅ Health monitor started")
    
    # Recover all previously running scripts
    recover_running_scripts()
    
    # Start bot polling
    while True:
        try:
            logger.info("🚀 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐛𝐨𝐭 𝐩𝐨𝐥𝐥𝐢𝐧𝐠...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except requests.exceptions.ConnectionError:
            logger.error(apply_custom_font("Connection error! Retrying..."))
            time.sleep(10)
        except Exception as e:
            logger.error(f"𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 𝐞𝐫𝐫𝐨𝐫: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()