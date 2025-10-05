#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Video Art Converter
Tests every aspect from frontend to backend to ensure 100% reliability
"""

import requests
import json
import cv2
import numpy as np
from pathlib import Path
import time
import tempfile
import os

BASE_URL = "http://localhost:8001/api"
FRONTEND_URL = "http://localhost:3000"

def create_test_video(duration=3, resolution=(640, 480), filename="test_video.mp4"):
    """Create a test video with moving elements for testing"""
    temp_dir = Path(tempfile.gettempdir())
    video_path = temp_dir / filename
    
    width, height = resolution
    fps = 30
    total_frames = fps * duration
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, fps, resolution)
    
    for frame_num in range(total_frames):
        # Create colorful background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Gradient background
        for y in range(height):
            frame[y, :] = [
                int(255 * (y / height)),
                int(255 * ((height - y) / height)),
                100
            ]
        
        # Moving circle
        center_x = int(width * 0.1 + (width * 0.8 * (frame_num / total_frames)))
        center_y = height // 2 + int(50 * np.sin(frame_num * 0.1))
        cv2.circle(frame, (center_x, center_y), 30, (255, 255, 0), -1)
        
        # Moving rectangle
        rect_x = int(width * 0.8 - (width * 0.6 * (frame_num / total_frames)))
        cv2.rectangle(frame, (rect_x, 50), (rect_x + 80, 130), (0, 255, 255), -1)
        
        # Text with frame counter
        cv2.putText(frame, f"Frame {frame_num}", (20, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    return video_path

def test_system_health():
    """Test 1: System Health Check"""
    print("🏥 Testing System Health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ System Status: {health.get('status')}")
            print(f"   ✅ Disk Space: {health.get('disk_space_gb', 0)}GB")
            print(f"   ✅ FFmpeg: {health.get('ffmpeg_available')}")
            print(f"   ✅ Database: {health.get('database_connected')}")
            print(f"   ✅ OpenCV: {health.get('opencv_version')}")
            return health.get('status') == 'healthy'
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_frontend_loading():
    """Test 2: Frontend Loading"""
    print("🌐 Testing Frontend Loading...")
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("   ✅ Frontend loaded successfully")
            return True
        else:
            print(f"   ❌ Frontend failed to load: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Frontend error: {e}")
        return False

def test_video_upload_and_processing():
    """Test 3: Complete Video Upload and Processing Pipeline"""
    print("📤 Testing Video Upload and Processing...")
    
    # Create test video
    video_path = create_test_video(duration=2, resolution=(320, 240))
    
    try:
        # Test upload
        with open(video_path, 'rb') as video_file:
            files = {'file': ('test_video.mp4', video_file, 'video/mp4')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
            return False
        
        project_data = response.json()
        project_id = project_data["project_id"]
        print(f"   ✅ Video uploaded successfully: {project_id}")
        
        # Test preview generation
        preview_response = requests.get(f"{BASE_URL}/preview/{project_id}", timeout=30)
        if preview_response.status_code == 200:
            preview_data = preview_response.json()
            frame_count = len(preview_data.get('preview_frames', []))
            print(f"   ✅ Preview generated: {frame_count} frames")
        else:
            print(f"   ⚠️ Preview generation failed: {preview_response.status_code}")
        
        # Test pencil processing
        print("   🎨 Testing Pencil Effect Processing...")
        processing_data = {
            "project_id": project_id,
            "art_style": "pencil",
            "intensity": 0.7,
            "crop_params": {"x": 10, "y": 10, "width": 300, "height": 220},
            "trim_params": {"start_time": 0.2, "end_time": 1.8},
            "resize_params": {"width": 240, "height": 180}
        }
        
        process_response = requests.post(f"{BASE_URL}/process", json=processing_data, timeout=30)
        if process_response.status_code != 200:
            print(f"   ❌ Processing failed: {process_response.text}")
            return False
        
        print("   ✅ Processing started successfully")
        
        # Monitor processing status
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{BASE_URL}/status/{project_id}", timeout=10)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   📊 Status: {status['status']} - {status['progress']:.1f}% - {status.get('message', '')}")
                
                if status['status'] == 'completed':
                    print("   ✅ Processing completed successfully!")
                    break
                elif status['status'] == 'failed':
                    print(f"   ❌ Processing failed: {status.get('message')}")
                    return False
            
            time.sleep(2)
        else:
            print("   ⚠️ Processing timeout")
            return False
        
        # Test download
        print("   📥 Testing Download...")
        download_response = requests.get(f"{BASE_URL}/download/{project_id}", timeout=30)
        if download_response.status_code == 200 and len(download_response.content) > 1000:
            print(f"   ✅ Download successful: {len(download_response.content)} bytes")
            return True
        else:
            print(f"   ❌ Download failed: {download_response.status_code}")
            return False
    
    except Exception as e:
        print(f"   ❌ Processing pipeline error: {e}")
        return False
    
    finally:
        # Cleanup
        if video_path.exists():
            video_path.unlink()

def test_cartoon_processing():
    """Test 4: Cartoon Effect Processing"""
    print("🎭 Testing Cartoon Effect Processing...")
    
    video_path = create_test_video(duration=1, resolution=(400, 300))
    
    try:
        # Upload
        with open(video_path, 'rb') as video_file:
            files = {'file': ('cartoon_test.mp4', video_file, 'video/mp4')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
        
        if response.status_code != 200:
            return False
        
        project_id = response.json()["project_id"]
        
        # Process with cartoon effect
        processing_data = {
            "project_id": project_id,
            "art_style": "cartoon",
            "intensity": 0.8
        }
        
        process_response = requests.post(f"{BASE_URL}/process", json=processing_data, timeout=30)
        if process_response.status_code != 200:
            return False
        
        # Wait for completion
        for _ in range(30):  # 1 minute max for small video
            status_response = requests.get(f"{BASE_URL}/status/{project_id}", timeout=10)
            if status_response.status_code == 200:
                status = status_response.json()
                if status['status'] == 'completed':
                    print("   ✅ Cartoon processing completed!")
                    return True
                elif status['status'] == 'failed':
                    print(f"   ❌ Cartoon processing failed: {status.get('message')}")
                    return False
            time.sleep(2)
        
        return False
    
    except Exception as e:
        print(f"   ❌ Cartoon processing error: {e}")
        return False
    
    finally:
        if video_path.exists():
            video_path.unlink()

def test_error_handling():
    """Test 5: Error Handling and Edge Cases"""
    print("🛡️ Testing Error Handling...")
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Invalid file upload
    try:
        response = requests.post(f"{BASE_URL}/upload", 
                                files={'file': ('test.txt', b'not a video', 'text/plain')}, 
                                timeout=10)
        if response.status_code == 400:
            print("   ✅ Invalid file rejection works")
            tests_passed += 1
        else:
            print(f"   ❌ Invalid file not rejected: {response.status_code}")
    except:
        print("   ❌ Invalid file test failed")
    
    # Test 2: Non-existent project status
    try:
        response = requests.get(f"{BASE_URL}/status/non-existent-id", timeout=10)
        if response.status_code == 404:
            print("   ✅ Non-existent project handling works")
            tests_passed += 1
        else:
            print(f"   ❌ Non-existent project not handled: {response.status_code}")
    except:
        print("   ❌ Non-existent project test failed")
    
    # Test 3: Invalid processing request
    try:
        response = requests.post(f"{BASE_URL}/process", 
                                json={"project_id": "invalid", "art_style": "invalid"}, 
                                timeout=10)
        if response.status_code in [400, 404]:
            print("   ✅ Invalid processing request handling works")
            tests_passed += 1
        else:
            print(f"   ❌ Invalid processing not handled: {response.status_code}")
    except:
        print("   ❌ Invalid processing test failed")
    
    # Test 4: API root endpoint
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200 and "masterpiece" in response.text.lower():
            print("   ✅ API root endpoint works")
            tests_passed += 1
        else:
            print(f"   ❌ API root endpoint issue: {response.status_code}")
    except:
        print("   ❌ API root test failed")
    
    return tests_passed == total_tests

def test_concurrent_processing():
    """Test 6: Concurrent Processing Capability"""
    print("⚡ Testing Concurrent Processing...")
    
    try:
        # Create multiple test videos
        video_paths = []
        project_ids = []
        
        for i in range(2):  # Test with 2 concurrent processes
            video_path = create_test_video(duration=1, filename=f"concurrent_test_{i}.mp4")
            video_paths.append(video_path)
            
            # Upload
            with open(video_path, 'rb') as video_file:
                files = {'file': (f'concurrent_{i}.mp4', video_file, 'video/mp4')}
                response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                project_ids.append(response.json()["project_id"])
        
        if len(project_ids) != 2:
            print("   ❌ Failed to upload concurrent test videos")
            return False
        
        # Start processing both
        for i, project_id in enumerate(project_ids):
            processing_data = {
                "project_id": project_id,
                "art_style": "pencil" if i == 0 else "cartoon",
                "intensity": 0.5
            }
            requests.post(f"{BASE_URL}/process", json=processing_data, timeout=10)
        
        # Monitor both
        completed = 0
        for _ in range(60):  # 2 minutes max
            for project_id in project_ids:
                status_response = requests.get(f"{BASE_URL}/status/{project_id}", timeout=10)
                if status_response.status_code == 200:
                    status = status_response.json()
                    if status['status'] == 'completed':
                        completed += 1
            
            if completed >= 2:
                print("   ✅ Concurrent processing successful!")
                return True
            
            time.sleep(2)
        
        print("   ⚠️ Concurrent processing timeout")
        return False
    
    except Exception as e:
        print(f"   ❌ Concurrent processing error: {e}")
        return False
    
    finally:
        for video_path in video_paths:
            if video_path.exists():
                video_path.unlink()

def main():
    """Run comprehensive test suite"""
    print("🚀 STARTING COMPREHENSIVE END-TO-END TEST SUITE")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("System Health", test_system_health()))
    test_results.append(("Frontend Loading", test_frontend_loading()))
    test_results.append(("Video Upload & Processing", test_video_upload_and_processing()))
    test_results.append(("Cartoon Effect", test_cartoon_processing()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("Concurrent Processing", test_concurrent_processing()))
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 ALL TESTS PASSED! System is 100% reliable and ready!")
        return True
    else:
        print("⚠️ Some tests failed. System needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)