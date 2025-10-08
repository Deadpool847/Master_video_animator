# 🐳 Video Art Masterpiece - Docker Edition

**🎨 Transform any video into artistic masterpieces with zero dependency hassles!**

## 🚀 One-Command Setup

### Windows:
```cmd
docker-setup.bat
```

### Linux/Mac:
```bash
./docker-setup.sh
```

**That's it!** No Python, Node.js, MongoDB, or FFmpeg installation required.

## 🎯 What You Get

After running the setup command:

✅ **Complete video processing pipeline** running in Docker  
✅ **Web interface** at http://localhost:3000  
✅ **API server** at http://localhost:8001  
✅ **MongoDB database** with persistent storage  
✅ **All dependencies** automatically installed and configured  

## 📋 Prerequisites

**Only Docker required:**

| Platform | Download | Requirements |
|----------|----------|--------------|
| Windows 10/11 | [Docker Desktop](https://www.docker.com/products/docker-desktop) | WSL2 enabled |
| macOS | [Docker Desktop](https://www.docker.com/products/docker-desktop) | macOS 10.15+ |
| Linux | [Docker Engine](https://docs.docker.com/engine/install/) | Any modern distro |

💾 **System Requirements:**
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space
- Docker Desktop running

## 🎨 Features Available

### 🎭 Artistic Effects:
- **Pencil Sketch**: Hand-drawn artistic style
- **Cartoon Animation**: Bold animated style  
- **Oil Painting**: Classic masterpiece effect
- **Watercolor**: Flowing artistic style
- **Anime Style**: Japanese animation look
- **Vintage Film**: Classic cinema effect

### 🔧 Advanced Features:
- **AI Recommendations**: Smart effect suggestions
- **Video Editing**: Crop, trim, resize with preview
- **Gallery System**: Beautiful thumbnails & instant preview  
- **Batch Processing**: Effect comparison grids
- **Real-time Progress**: Live processing updates
- **High Quality Output**: Professional video results

## 📁 Easy Management

### Quick Commands:
```bash
# Start application
docker compose up -d

# Stop application  
docker compose down

# View logs
docker compose logs -f

# Check status
docker compose ps
```

### Windows GUI Management:
```cmd
# Interactive manager
docker-manage.bat

# View logs easily  
docker-logs.bat
```

## 🛠️ Project Structure

```
video-art-masterpiece/
├── 🐳 Docker Files
│   ├── docker-compose.yml         # Main orchestration
│   ├── Dockerfile.backend         # Python/FastAPI
│   ├── Dockerfile.frontend        # React/Nginx
│   └── docker/                    # Config files
├── 🚀 Setup Scripts
│   ├── docker-setup.bat          # Windows setup
│   ├── docker-setup.sh           # Linux/Mac setup
│   ├── docker-manage.bat         # Windows manager
│   └── docker-logs.bat           # Windows log viewer
├── 📚 Documentation
│   ├── DOCKER_INSTRUCTIONS.md    # Complete guide
│   └── README_DOCKER.md          # This file
└── 💻 Application Code
    ├── backend/                   # FastAPI + OpenCV
    └── frontend/                  # React + Tailwind
```

## 🔍 Health Monitoring

The Docker setup includes automatic health checks:

### Service Status:
```bash
docker compose ps
# Should show all services as "healthy"
```

### Manual Health Checks:
```bash
# Backend API
curl http://localhost:8001/api/health

# Frontend  
curl http://localhost:3000/health

# Database connection
docker compose exec mongodb mongosh --eval "db.runCommand('ping')"
```

## 📊 Performance Optimization

### Docker Desktop Settings:
1. **Memory**: Allocate 8GB+ to Docker
2. **CPU**: Use all available cores  
3. **Storage**: Use SSD for Docker volumes
4. **Network**: Ensure good internet for initial image downloads

### Video Processing Tips:
- Start with small videos (< 100MB) for testing
- Close unnecessary applications during processing
- Monitor resource usage: `docker stats`

## 🚨 Troubleshooting

### Common Issues:

❌ **Docker Desktop not running**
```bash
# Start Docker Desktop application first
docker --version  # Should show version
```

❌ **Ports already in use**
```bash
# Stop other services using ports 3000, 8001, 27017
docker compose down
netstat -tulpn | grep :3000  # Linux/Mac
netstat -ano | findstr :3000  # Windows
```

❌ **Containers won't start**
```bash
# Check logs for errors
docker compose logs
# Try rebuilding
docker compose up --build -d
```

❌ **Out of disk space**
```bash
# Clean unused Docker data
docker system prune -a
# Check usage
docker system df
```

### Advanced Troubleshooting:

**Reset everything:**
```bash
# Complete cleanup and restart
docker compose down -v
docker system prune -a --volumes
docker compose up --build -d
```

**Access container shells:**
```bash
# Debug backend
docker compose exec backend bash

# Debug frontend  
docker compose exec frontend sh

# Access database
docker compose exec mongodb mongosh
```

## 🔄 Updates & Maintenance

### Update Application:
```bash
# Get latest code
git pull

# Rebuild and restart
docker compose down
docker compose up --build -d
```

### Backup Data:
```bash
# Create backup
docker run --rm -v video-art-mongodb-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Restore backup
docker run --rm -v video-art-mongodb-data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

## 🎯 Usage Workflow

1. **Start**: Run `docker-setup.bat` (Windows) or `./docker-setup.sh` (Linux/Mac)
2. **Open**: Navigate to http://localhost:3000 in your browser
3. **Upload**: Drag & drop any video file
4. **Choose**: Select artistic effect (pencil, cartoon, oil painting, etc.)
5. **Edit**: Optional crop, trim, resize with live preview
6. **Process**: Click "Create Masterpiece" and watch real-time progress
7. **Preview**: View result in-browser before downloading
8. **Download**: Get high-quality artistic video

## 🎉 Success Indicators

When everything is working correctly:

✅ `docker compose ps` shows 3 healthy containers  
✅ http://localhost:3000 loads the beautiful interface  
✅ http://localhost:8001/api/health returns `{"status":"healthy"}`  
✅ Video upload and processing works end-to-end  
✅ All 6 artistic effects are available  
✅ Preview and download functionality works  

## 📞 Need Help?

1. **Check logs**: `docker compose logs -f`
2. **Verify Docker**: Ensure Docker Desktop is running with sufficient resources
3. **Port conflicts**: Make sure ports 3000, 8001, 27017 are available
4. **Clean restart**: `docker compose down -v && docker compose up --build -d`

---

## 🎨 Ready to Create Masterpieces!

With Docker, Video Art Masterpiece runs identically on:
- ✅ Windows 10/11
- ✅ macOS (Intel & Apple Silicon)  
- ✅ Linux (Ubuntu, Debian, CentOS, etc.)

**No dependency conflicts. No installation hassles. Just pure video art creation!** 🚀

---

*Transform your videos into stunning artistic masterpieces with the power of Docker! 🎬✨*