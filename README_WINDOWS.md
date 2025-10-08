# 🎨 Video Art Masterpiece - Windows Quick Start

Transform any video into stunning artistic masterpieces on Windows!

## 🚀 Quick Setup (5 Minutes)

### 1️⃣ Check Requirements
```cmd
python check_windows_requirements.py
```

### 2️⃣ Install Dependencies
```cmd
setup_windows.bat
```

### 3️⃣ Start Application
```cmd
# Terminal 1
start_backend.bat

# Terminal 2 
start_frontend.bat
```

### 4️⃣ Open Browser
Navigate to: **http://localhost:3000**

## 📋 Prerequisites

- ✅ Windows 10/11 (64-bit)
- ✅ 8GB+ RAM (16GB recommended)
- ✅ 10GB+ free disk space

## 📥 Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| Python | 3.11+ | https://python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| MongoDB | 5.0+ | https://mongodb.com/try/download/community |
| FFmpeg | Latest | `choco install ffmpeg` |
| VS Code | Latest | https://code.visualstudio.com/ |

⚠️ **Important**: Check "Add to PATH" when installing Python!

## 🎨 Features

- **6 Artistic Effects**: Pencil, Cartoon, Oil Painting, Watercolor, Anime, Vintage
- **AI Recommendations**: Smart effect suggestions based on video content
- **Advanced Editing**: Crop, trim, resize with real-time preview
- **Gallery System**: Beautiful thumbnails and instant preview
- **100% Offline**: No external APIs required

## 📁 Project Structure
```
C:\VideoArtMasterpiece\
├── 🎬 setup_windows.bat         # One-click setup
├── 🚀 start_backend.bat         # Start API server
├── ⚛️ start_frontend.bat        # Start web interface
├── 🧪 check_windows_requirements.py
├── 📄 WINDOWS_SETUP_INSTRUCTIONS.txt
├── 🛠️ WINDOWS_TROUBLESHOOTING.txt
├── backend\                     # FastAPI + OpenCV
├── frontend\                    # React + Tailwind
└── 🎨 video-art-masterpiece.code-workspace
```

## 🔧 VS Code Setup

1. Install recommended extensions:
   - Python (Microsoft)
   - JavaScript and TypeScript Nightly
   - Tailwind CSS IntelliSense
   - Thunder Client

2. Open workspace:
   ```cmd
   code video-art-masterpiece.code-workspace
   ```

3. Use built-in tasks (Ctrl+Shift+P → "Tasks: Run Task"):
   - 🔧 Setup Windows Environment
   - 🚀 Start Backend
   - ⚛️ Start Frontend
   - 🧪 Test Application

## 🛠️ Troubleshooting

### Common Issues:

❌ **"python is not recognized"**
```cmd
# Reinstall Python with "Add to PATH" checked
```

❌ **MongoDB connection failed**
```cmd
net start MongoDB
```

❌ **FFmpeg not found**
```cmd
# Install Chocolatey first, then:
choco install ffmpeg
```

❌ **Port already in use**
```cmd
# Kill process using port 3000/8001
netstat -ano | findstr :3000
taskkill /PID <process_id> /F
```

See **WINDOWS_TROUBLESHOOTING.txt** for complete solutions.

## 🎯 Usage

1. **Upload Video**: Drag & drop any video file (.mp4, .avi, .mov)
2. **Choose Style**: Select from 6 artistic effects
3. **AI Analysis**: Get smart recommendations based on content
4. **Advanced Edit**: Crop, trim, resize as needed  
5. **Process**: Create your masterpiece with real-time progress
6. **Preview**: Watch result in-browser before download
7. **Download**: Get high-quality artistic video

## 📊 Performance Tips

- **Close** unnecessary applications during processing
- **Use SSD** storage for better performance  
- **Add exclusions** to Windows Defender for project folder
- **Start small** with videos under 100MB for testing

## 🎉 Success! 

Once running, you'll see:
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend API: http://localhost:8001
- 🗄️ Database: MongoDB on port 27017

## 🆘 Need Help?

1. Run: `python check_windows_requirements.py`
2. Check: **WINDOWS_TROUBLESHOOTING.txt** 
3. View logs in Command Prompt terminals
4. Check Windows Event Viewer for system errors

---

**🎨 Ready to create video masterpieces? Let's go!** 🚀