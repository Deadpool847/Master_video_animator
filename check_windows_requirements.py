#!/usr/bin/env python3
"""
Windows Requirements Checker for Video Art Masterpiece
Checks if all required software is installed and properly configured
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_command(command, shell=True):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check Python installation"""
    print("🐍 Checking Python...")
    
    success, output, error = run_command("python --version")
    if success and "Python" in output:
        version = output.replace("Python ", "")
        major, minor = map(int, version.split(".")[:2])
        
        if major == 3 and minor >= 11:
            print(f"   ✅ Python {version} (Good)")
            return True
        else:
            print(f"   ⚠️ Python {version} (Need 3.11+)")
            return False
    else:
        print("   ❌ Python not found or not in PATH")
        print("   📥 Download from: https://www.python.org/downloads/")
        return False

def check_pip():
    """Check pip installation"""
    print("📦 Checking pip...")
    
    success, output, error = run_command("pip --version")
    if success:
        print(f"   ✅ {output}")
        return True
    else:
        print("   ❌ pip not found")
        return False

def check_nodejs():
    """Check Node.js installation"""
    print("📗 Checking Node.js...")
    
    success, output, error = run_command("node --version")
    if success:
        version = output.replace("v", "")
        major = int(version.split(".")[0])
        
        if major >= 18:
            print(f"   ✅ Node.js {version} (Good)")
        else:
            print(f"   ⚠️ Node.js {version} (Need 18+)")
            return False
    else:
        print("   ❌ Node.js not found")
        print("   📥 Download from: https://nodejs.org/")
        return False
    
    # Check npm
    success, output, error = run_command("npm --version")
    if success:
        print(f"   ✅ npm {output}")
        return True
    else:
        print("   ❌ npm not found")
        return False

def check_mongodb():
    """Check MongoDB installation"""
    print("🗄️ Checking MongoDB...")
    
    # Check if MongoDB service exists
    success, output, error = run_command('sc query "MongoDB"')
    if success:
        if "RUNNING" in output:
            print("   ✅ MongoDB service is running")
        else:
            print("   ⚠️ MongoDB service exists but not running")
            print("   🔧 Try: net start MongoDB")
    else:
        print("   ❌ MongoDB service not found")
        print("   📥 Download from: https://www.mongodb.com/try/download/community")
        return False
    
    # Check mongod executable
    mongod_paths = [
        r"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe"
    ]
    
    for path in mongod_paths:
        if Path(path).exists():
            success, output, error = run_command(f'"{path}" --version')
            if success:
                version_line = output.split('\n')[0] if output else "Unknown version"
                print(f"   ✅ {version_line}")
                return True
    
    print("   ❌ mongod executable not found")
    return False

def check_ffmpeg():
    """Check FFmpeg installation"""
    print("🎬 Checking FFmpeg...")
    
    # Check in PATH
    if shutil.which('ffmpeg'):
        success, output, error = run_command("ffmpeg -version")
        if success:
            version_line = output.split('\n')[0] if output else "Unknown version"
            print(f"   ✅ {version_line}")
            return True
    
    # Check common Windows locations
    ffmpeg_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe"
    ]
    
    for path in ffmpeg_paths:
        if Path(path).exists():
            print(f"   ⚠️ FFmpeg found at {path} but not in PATH")
            print("   🔧 Add to PATH or run: choco install ffmpeg")
            return True
    
    print("   ❌ FFmpeg not found")
    print("   📥 Install with: choco install ffmpeg")
    print("   📥 Or download from: https://www.gyan.dev/ffmpeg/builds/")
    return False

def check_git():
    """Check Git installation"""
    print("📚 Checking Git...")
    
    success, output, error = run_command("git --version")
    if success:
        print(f"   ✅ {output}")
        return True
    else:
        print("   ❌ Git not found")
        print("   📥 Download from: https://git-scm.com/download/win")
        return False

def check_vscode():
    """Check VS Code installation"""
    print("💻 Checking VS Code...")
    
    success, output, error = run_command("code --version")
    if success:
        version = output.split('\n')[0] if output else "Unknown version"
        print(f"   ✅ VS Code {version}")
        return True
    else:
        print("   ❌ VS Code not found")
        print("   📥 Download from: https://code.visualstudio.com/")
        return False

def check_ports():
    """Check if required ports are available"""
    print("🔌 Checking ports...")
    
    ports = {
        "3000": "Frontend (React)",
        "8001": "Backend (FastAPI)", 
        "27017": "Database (MongoDB)"
    }
    
    all_clear = True
    for port, service in ports.items():
        success, output, error = run_command(f"netstat -an | findstr :{port}")
        if success and output.strip():
            print(f"   ⚠️ Port {port} ({service}) is in use")
            all_clear = False
        else:
            print(f"   ✅ Port {port} ({service}) available")
    
    return all_clear

def check_disk_space():
    """Check available disk space"""
    print("💾 Checking disk space...")
    
    try:
        free_bytes = shutil.disk_usage('.').free
        free_gb = free_bytes / (1024**3)
        
        if free_gb >= 10:
            print(f"   ✅ {free_gb:.1f} GB available (Good)")
            return True
        else:
            print(f"   ⚠️ {free_gb:.1f} GB available (Need 10+ GB)")
            return False
    except Exception as e:
        print(f"   ❌ Could not check disk space: {e}")
        return False

def check_windows_version():
    """Check Windows version"""
    print("🪟 Checking Windows version...")
    
    try:
        version_info = platform.platform()
        windows_version = platform.version()
        
        print(f"   ℹ️ {version_info}")
        
        # Check if it's Windows 10/11
        if "Windows-10" in version_info or "Windows-11" in version_info:
            print("   ✅ Supported Windows version")
            return True
        else:
            print("   ⚠️ Older Windows version detected")
            print("   💡 Windows 10/11 recommended for best compatibility")
            return True  # Don't fail for older Windows
    except Exception as e:
        print(f"   ❌ Could not determine Windows version: {e}")
        return False

def main():
    """Main requirements checker"""
    print("🎨 Video Art Masterpiece - Windows Requirements Checker")
    print("=" * 60)
    print()
    
    if not platform.system().lower().startswith('win'):
        print("❌ This checker is designed for Windows systems.")
        print("ℹ️ You appear to be running on:", platform.system())
        return False
    
    checks = [
        ("System", check_windows_version),
        ("Disk Space", check_disk_space),
        ("Python", check_python),
        ("pip", check_pip),
        ("Node.js", check_nodejs),
        ("MongoDB", check_mongodb),
        ("FFmpeg", check_ffmpeg),
        ("Git", check_git),
        ("VS Code", check_vscode),
        ("Ports", check_ports)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"   ❌ Error checking {name}: {e}")
            results[name] = False
        print()
    
    # Summary
    print("=" * 60)
    print("📊 REQUIREMENTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<15} {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All requirements met! You're ready to run Video Art Masterpiece!")
        print("\nNext steps:")
        print("1. Run: setup_windows.bat")
        print("2. Run: start_backend.bat")
        print("3. Run: start_frontend.bat")
        print("4. Open: http://localhost:3000")
        return True
    else:
        print(f"\n⚠️ {total - passed} requirements need attention.")
        print("\nPlease install missing components and run this checker again.")
        
        # Provide specific next steps
        critical_missing = []
        if not results.get("Python"): critical_missing.append("Python 3.11+")
        if not results.get("Node.js"): critical_missing.append("Node.js 18+")
        if not results.get("MongoDB"): critical_missing.append("MongoDB")
        if not results.get("FFmpeg"): critical_missing.append("FFmpeg")
        
        if critical_missing:
            print(f"\n🚨 Critical missing components: {', '.join(critical_missing)}")
        
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 60)
    print("For detailed installation instructions, see:")
    print("📄 WINDOWS_SETUP_INSTRUCTIONS.txt")
    print("🛠️ WINDOWS_TROUBLESHOOTING.txt")
    print("=" * 60)
    
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)