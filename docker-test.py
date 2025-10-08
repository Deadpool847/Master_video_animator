#!/usr/bin/env python3
"""
Docker Setup Test for Video Art Masterpiece
Tests if the Docker environment is working correctly
"""

import requests
import time
import subprocess
import sys
import json

def run_command(command, shell=True):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Check if Docker is available and running"""
    print("🐳 Checking Docker...")
    
    success, output, error = run_command("docker --version")
    if not success:
        print("   ❌ Docker not found!")
        return False
    
    print(f"   ✅ {output}")
    
    # Check Docker Compose
    success, output, error = run_command("docker compose version")
    if not success:
        print("   ❌ Docker Compose not found!")
        return False
    
    print(f"   ✅ Docker Compose available")
    return True

def check_containers():
    """Check if containers are running"""
    print("📦 Checking containers...")
    
    success, output, error = run_command("docker compose ps --format json")
    if not success:
        print("   ❌ Could not check container status")
        return False
    
    try:
        containers = []
        for line in output.strip().split('\n'):
            if line.strip():
                containers.append(json.loads(line))
        
        expected_services = ['video-art-backend', 'video-art-frontend', 'video-art-mongodb']
        running_services = [c['Service'] for c in containers if c['State'] == 'running']
        
        for service in expected_services:
            if service in running_services:
                print(f"   ✅ {service} is running")
            else:
                print(f"   ❌ {service} not running")
                return False
        
        return len(running_services) >= 3
        
    except Exception as e:
        print(f"   ❌ Error parsing container status: {e}")
        return False

def test_backend_api():
    """Test backend API endpoints"""
    print("🔧 Testing Backend API...")
    
    base_url = "http://localhost:8001/api"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check: {data.get('status', 'unknown')}")
            
            # Check specific components
            if data.get('ffmpeg_available'):
                print("   ✅ FFmpeg available")
            else:
                print("   ⚠️ FFmpeg not available")
            
            if data.get('database_connected'):
                print("   ✅ Database connected")
            else:
                print("   ❌ Database not connected")
            
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"   ❌ Backend API unreachable: {e}")
        return False

def test_frontend():
    """Test frontend application"""
    print("🌐 Testing Frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("   ✅ Frontend is accessible")
            
            # Check if it contains expected content
            if "Video Art Masterpiece" in response.text:
                print("   ✅ Frontend content loaded correctly")
                return True
            else:
                print("   ⚠️ Frontend loaded but content might be incomplete")
                return True
        else:
            print(f"   ❌ Frontend not accessible: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"   ❌ Frontend unreachable: {e}")
        return False

def test_database():
    """Test database connectivity"""
    print("🗄️ Testing Database...")
    
    success, output, error = run_command('docker compose exec -T mongodb mongosh --eval "db.runCommand(\'ping\')" --quiet')
    if success:
        print("   ✅ Database is responsive")
        return True
    else:
        print("   ❌ Database connection failed")
        return False

def test_file_upload_simulation():
    """Simulate basic API functionality"""
    print("📤 Testing API functionality...")
    
    try:
        # Test projects endpoint
        response = requests.get("http://localhost:8001/api/projects", timeout=10)
        if response.status_code == 200:
            projects = response.json()
            print(f"   ✅ Projects API working ({len(projects)} projects)")
            return True
        else:
            print(f"   ❌ Projects API failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"   ❌ API test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎨 Video Art Masterpiece - Docker Environment Test")
    print("=" * 55)
    print()
    
    tests = [
        ("Docker Installation", check_docker),
        ("Container Status", check_containers),
        ("Backend API", test_backend_api),
        ("Frontend App", test_frontend),
        ("Database", test_database),
        ("API Functionality", test_file_upload_simulation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ Test error: {e}")
            results[test_name] = False
        print()
    
    # Summary
    print("=" * 55)
    print("📊 TEST SUMMARY")
    print("=" * 55)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎨 Video Art Masterpiece is ready for use!")
        print("\n🌐 Access the application:")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8001")
        print("\n🚀 Ready to create video masterpieces!")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed.")
        print("\n🔧 Troubleshooting steps:")
        
        if not results.get("Docker Installation"):
            print("   1. Install Docker Desktop and ensure it's running")
        
        if not results.get("Container Status"):
            print("   2. Run: docker compose up -d")
            print("   3. Check: docker compose ps")
        
        if not results.get("Backend API") or not results.get("Database"):
            print("   4. Check logs: docker compose logs backend")
            print("   5. Check logs: docker compose logs mongodb")
        
        if not results.get("Frontend App"):
            print("   6. Check logs: docker compose logs frontend")
        
        print("   7. Try clean restart: docker compose down -v && docker compose up --build -d")
        
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 55)
    print("For help, see:")
    print("📄 DOCKER_INSTRUCTIONS.md")
    print("🐳 README_DOCKER.md")
    print("=" * 55)
    
    sys.exit(0 if success else 1)