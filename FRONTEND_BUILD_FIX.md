# 🔧 Frontend Build Fix - Exit Code 127 Solution

## 🚨 Problem: "npm run build" Failed (Exit Code 127)

**Error**: `process "/bin/sh -c npm run build" did not complete successfully: exit code: 127`

**Cause**: Exit code 127 = "Command not found" - the build script isn't properly configured.

## 🎯 Quick Fix Commands

### Method 1: Automated Fix Script
```bash
# Windows
fix-frontend-build.bat

# Linux/Mac  
chmod +x fix-frontend-build.bat && ./fix-frontend-build.bat
```

### Method 2: Manual Fix
```bash
# Clean and rebuild with simple approach
docker rmi video-art-frontend
docker build -t video-art-frontend -f Dockerfile.frontend.simple . --progress=plain
docker compose up -d
```

### Method 3: Step-by-Step Debug
```bash
# Build with debug output
docker build -t video-art-frontend -f Dockerfile.frontend . --progress=plain --no-cache

# If it fails, check what's wrong:
docker run --rm -it node:18-alpine sh
# Inside container:
# npm --version
# npx --version  
# npm run --help
```

## 🛠️ Root Cause Solutions

### Issue 1: Craco Dependencies
The package.json uses `craco` which needs proper installation:

```dockerfile
# In Dockerfile - Install craco specifically
RUN npm install @craco/craco@7.1.0 --legacy-peer-deps
RUN npm install react-scripts@5.0.1 --legacy-peer-deps
```

### Issue 2: Build Script Missing
Verify package.json has correct scripts:

```json
{
  "scripts": {
    "start": "craco start",
    "build": "craco build", 
    "test": "craco test"
  }
}
```

### Issue 3: Node Version Compatibility
Use specific Node version that works with React 19:

```dockerfile
FROM node:18-alpine  # ✅ Works
FROM node:20-alpine  # ⚠️ May have issues with React 19
```

## 🔄 Alternative Build Strategies

### Strategy 1: Use Simple React Build
```dockerfile
FROM node:18-alpine
WORKDIR /app
RUN npx create-react-app .
COPY frontend/src/ /app/src/
RUN npm run build
```

### Strategy 2: Use Yarn Instead of NPM
```dockerfile
RUN yarn install
RUN yarn build
```

### Strategy 3: Build Outside Docker
```bash
# Build on host, then copy to container
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

# Simple nginx container
docker run -d -p 3000:80 -v $(pwd)/frontend/build:/usr/share/nginx/html nginx:alpine
```

## ✅ Success Verification

After fix, verify with:
```bash
# Check build output
docker images | grep video-art-frontend

# Test container
docker run --rm -p 3000:3000 video-art-frontend

# Full system test
docker compose up -d
curl http://localhost:3000
```

## 🆘 Emergency Fallbacks

If all else fails:

### Fallback 1: Use Pre-built Image
```dockerfile
FROM nginx:alpine
COPY frontend/build /usr/share/nginx/html  
# (if you have a working build directory)
```

### Fallback 2: Serve with Python
```bash
cd frontend
python -m http.server 3000
```

### Fallback 3: Use Different Base Image
```dockerfile
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y nodejs npm
# ... rest of build
```

---

**🎯 One of these methods will definitely resolve the exit code 127 error!**