#!/usr/bin/env python3
"""
Windows Compatibility Fixes for Video Art Masterpiece
This script applies necessary fixes for running on Windows systems
"""

import os
import sys
import shutil
import platform
from pathlib import Path

def is_windows():
    """Check if running on Windows"""
    return platform.system().lower() == 'windows'

def find_ffmpeg_path():
    """Find FFmpeg executable path on Windows"""
    # Common FFmpeg locations on Windows
    possible_paths = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
        shutil.which('ffmpeg')  # Check PATH
    ]
    
    for path in possible_paths:
        if path and Path(path).exists():
            return str(Path(path))
    
    return 'ffmpeg'  # Fallback to PATH

def apply_windows_fixes():
    """Apply Windows-specific fixes to the application"""
    
    if not is_windows():
        print("ℹ️ Not running on Windows, skipping Windows-specific fixes.")
        return
    
    print("🔧 Applying Windows compatibility fixes...")
    
    # 1. Fix FFmpeg path in backend code
    backend_file = Path('backend/server.py')
    if backend_file.exists():
        print("📝 Fixing FFmpeg path in backend...")
        
        with open(backend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace hardcoded FFmpeg path
        ffmpeg_path = find_ffmpeg_path()
        content = content.replace("'/usr/bin/ffmpeg'", f"r'{ffmpeg_path}'")
        content = content.replace('"/usr/bin/ffmpeg"', f'r"{ffmpeg_path}"')
        
        # Fix disk usage path
        content = content.replace('shutil.disk_usage("/app")', 'shutil.disk_usage(".")')
        
        # Fix path for module imports
        content = content.replace("sys.path.append('/app')", "sys.path.append('.')")
        
        with open(backend_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Backend FFmpeg path fixed")
    
    # 2. Fix paths in simple_video_processor.py
    processor_file = Path('simple_video_processor.py')
    if processor_file.exists():
        print("📝 Fixing paths in video processor...")
        
        with open(processor_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Import platform detection at the top
        if 'import platform' not in content:
            content = content.replace('import logging', 'import logging\nimport platform')
        
        # Add Windows FFmpeg path detection
        ffmpeg_detection = f'''
def get_ffmpeg_path():
    """Get FFmpeg path for current platform"""
    if platform.system().lower() == 'windows':
        return r'{ffmpeg_path}'
    return 'ffmpeg'
'''
        
        if 'def get_ffmpeg_path():' not in content:
            content = content.replace('import platform', f'import platform{ffmpeg_detection}')
        
        # Replace FFmpeg usage
        content = content.replace("'ffmpeg'", "get_ffmpeg_path()")
        
        with open(processor_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Video processor paths fixed")
    
    # 3. Create Windows-specific requirements.txt
    create_windows_requirements()
    
    # 4. Create Windows batch files for easy startup
    create_windows_batch_files()
    
    print("🎉 Windows compatibility fixes applied successfully!")
    print(f"📍 FFmpeg path detected: {ffmpeg_path}")

def create_windows_requirements():
    """Create Windows-specific requirements.txt with compatible versions"""
    
    windows_requirements = """fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1
motor==3.3.2
python-dotenv==1.0.0
opencv-python==4.8.1.78
numpy==1.25.2
pillow==10.1.0
requests==2.31.0
pathlib2==2.3.7; python_version<"3.4"
"""
    
    backend_req_file = Path('backend/requirements_windows.txt')
    with open(backend_req_file, 'w', encoding='utf-8') as f:
        f.write(windows_requirements)
    
    print("✅ Windows-specific requirements.txt created")

def create_windows_batch_files():
    """Create Windows batch files for easy startup"""
    
    # Backend startup batch
    backend_batch = """@echo off
echo 🎨 Starting Video Art Masterpiece Backend...
echo.

REM Activate virtual environment
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
) else (
    echo ❌ Virtual environment not found! Please run setup first.
    pause
    exit /b 1
)

REM Start backend server
echo ✅ Starting FastAPI server...
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

pause
"""

    frontend_batch = """@echo off
echo ⚛️ Starting Video Art Masterpiece Frontend...
echo.

REM Check if node_modules exists
cd frontend
if not exist node_modules (
    echo 📦 Installing dependencies...
    yarn install
)

REM Start frontend server
echo ✅ Starting React development server...
yarn start

pause
"""

    setup_batch = """@echo off
echo 🔧 Setting up Video Art Masterpiece...
echo.

REM Create virtual environment
echo 📦 Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment!
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\\Scripts\\activate.bat

REM Install backend dependencies
echo 🐍 Installing Python dependencies...
cd backend
pip install --upgrade pip
pip install -r requirements_windows.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies!
    pause
    exit /b 1
)

REM Install frontend dependencies
echo ⚛️ Installing Node.js dependencies...
cd ..\\frontend
yarn install
if errorlevel 1 (
    echo ❌ Failed to install Node.js dependencies!
    echo Trying with npm...
    npm install
)

echo.
echo 🎉 Setup complete!
echo.
echo To start the application:
echo 1. Run start_backend.bat
echo 2. Run start_frontend.bat in another terminal
echo 3. Open http://localhost:3000 in your browser
echo.
pause
"""

    # Write batch files
    with open('start_backend.bat', 'w', encoding='utf-8') as f:
        f.write(backend_batch)
    
    with open('start_frontend.bat', 'w', encoding='utf-8') as f:
        f.write(frontend_batch)
    
    with open('setup_windows.bat', 'w', encoding='utf-8') as f:
        f.write(setup_batch)
    
    print("✅ Windows batch files created:")
    print("   - setup_windows.bat (run first)")
    print("   - start_backend.bat")
    print("   - start_frontend.bat")

def create_vscode_settings():
    """Create VS Code settings for Windows"""
    
    vscode_dir = Path('.vscode')
    vscode_dir.mkdir(exist_ok=True)
    
    # Settings.json
    settings = {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.terminal.activateEnvironment": True,
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": False,
        "python.linting.flake8Enabled": True,
        "terminal.integrated.defaultProfile.windows": "Command Prompt",
        "files.associations": {
            "*.py": "python"
        },
        "files.encoding": "utf8",
        "files.eol": "\n"
    }
    
    import json
    with open(vscode_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=4)
    
    # Launch.json for debugging
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Backend FastAPI",
                "type": "python",
                "request": "launch",
                "module": "uvicorn",
                "args": [
                    "backend.server:app",
                    "--host", "0.0.0.0",
                    "--port", "8001",
                    "--reload"
                ],
                "console": "integratedTerminal",
                "cwd": "${workspaceFolder}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }
            }
        ]
    }
    
    with open(vscode_dir / 'launch.json', 'w') as f:
        json.dump(launch_config, f, indent=4)
    
    print("✅ VS Code configuration files created")

if __name__ == "__main__":
    print("🎨 Video Art Masterpiece - Windows Setup")
    print("=" * 50)
    
    # Apply all fixes
    apply_windows_fixes()
    create_vscode_settings()
    
    print("\n🎉 Windows setup complete!")
    print("\nNext steps:")
    print("1. Run setup_windows.bat to install dependencies")
    print("2. Run start_backend.bat to start the backend")
    print("3. Run start_frontend.bat to start the frontend")
    print("4. Open http://localhost:3000 in your browser")
    print("\nEnjoy creating video masterpieces on Windows! 🎬✨")