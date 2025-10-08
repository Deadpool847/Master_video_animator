# 🚀 Bulletproof Docker Build Commands

## 🎯 Quick Commands (Choose One)

### Method 1: Automated Script (Recommended)
```bash
# Windows
docker-build-bulletproof.bat

# Linux/Mac  
./docker-build-bulletproof.sh
```

### Method 2: Manual Commands
```bash
# Clean previous builds
docker compose down -v
docker system prune -f

# Build and start
docker compose up --build -d

# Check status
docker compose ps
```

### Method 3: Step-by-Step Build
```bash
# 1. Clean environment
docker compose down -v
docker system prune -f

# 2. Build backend first
docker build -t video-art-backend -f Dockerfile.backend . --progress=plain

# 3. Build frontend
docker build -t video-art-frontend -f Dockerfile.frontend . --progress=plain

# 4. Start all services
docker compose up -d

# 5. Verify
docker compose ps
curl http://localhost:8001/api/health
```

## 🛠️ Troubleshooting Commands

### If Backend Build Fails:
```bash
# Try with host network
docker build -t video-art-backend -f Dockerfile.backend . --network=host

# Or try without cache
docker build -t video-art-backend -f Dockerfile.backend . --no-cache

# Check Docker resources
docker system df
docker system prune -a
```

### If Frontend Build Fails:
```bash
# Try alternative approach
docker build -t video-art-frontend -f Dockerfile.frontend . --network=host

# Or build with more verbose output
docker build -t video-art-frontend -f Dockerfile.frontend . --progress=plain --no-cache
```

### General Docker Issues:
```bash
# Restart Docker service (Linux)
sudo systemctl restart docker

# Clear everything and restart (Nuclear option)
docker system prune -a --volumes
docker compose up --build -d
```

## ✅ Success Verification

After build completes, verify with:
```bash
# Check containers
docker compose ps

# Test endpoints
curl http://localhost:8001/api/health
curl http://localhost:3000

# View logs
docker compose logs -f
```

## 🎯 Expected Output

**Successful build should show:**
```
NAME                    IMAGE               STATUS
video-art-backend       video-art-backend   Up (healthy)
video-art-frontend      video-art-frontend  Up (healthy)  
video-art-mongodb       mongo:7.0           Up (healthy)
```

**Working URLs:**
- 🌐 http://localhost:3000 (Frontend)
- 🔧 http://localhost:8001/api/health (Backend API)

## 🚨 Emergency Recovery

If everything fails:
```bash
# Complete reset
docker compose down -v
docker system prune -a --volumes
docker volume prune -f

# Restart Docker Desktop (Windows/Mac)
# Or restart Docker service (Linux): sudo systemctl restart docker

# Try build again
./docker-build-bulletproof.sh
```

---
**🎉 One of these methods will definitely work! The bulletproof scripts handle all edge cases.**