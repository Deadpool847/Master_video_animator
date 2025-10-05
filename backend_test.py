#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Video Art Converter
Tests all video processing functionality including upload, processing, status tracking, and download
"""

import requests
import json
import time
import os
import cv2
import numpy as np
from pathlib import Path
import tempfile
import base64

# Configuration
BASE_URL = "https://pencil-animator.preview.emergentagent.com/api"
TEST_TIMEOUT = 30  # seconds for API calls
PROCESSING_TIMEOUT = 120  # seconds for video processing

class VideoArtConverterTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "health_check": False,
            "video_upload": False,
            "video_preview": False,
            "pencil_processing": False,
            "cartoon_processing": False,
            "status_tracking": False,
            "projects_list": False,
            "video_download": False,
            "crop_functionality": False,
            "trim_functionality": False,
            "resize_functionality": False
        }
        self.project_ids = []
        self.test_video_path = None
        
    def create_test_video(self):
        """Create a small test video file for testing"""
        try:
            print("Creating test video file...")
            
            # Create a temporary video file
            temp_dir = Path("/tmp")
            self.test_video_path = temp_dir / "test_video.mp4"
            
            # Video properties
            width, height = 640, 480
            fps = 30
            duration = 3  # 3 seconds
            total_frames = fps * duration
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(self.test_video_path), fourcc, fps, (width, height))
            
            # Generate frames with moving colored rectangle
            for frame_num in range(total_frames):
                # Create a frame with gradient background
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # Add gradient background
                for y in range(height):
                    frame[y, :] = [int(255 * y / height), 100, int(255 * (1 - y / height))]
                
                # Add moving rectangle
                rect_size = 50
                x_pos = int((width - rect_size) * (frame_num / total_frames))
                y_pos = height // 2 - rect_size // 2
                
                cv2.rectangle(frame, (x_pos, y_pos), (x_pos + rect_size, y_pos + rect_size), (0, 255, 255), -1)
                
                # Add frame number text
                cv2.putText(frame, f"Frame {frame_num}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                out.write(frame)
            
            out.release()
            
            if self.test_video_path.exists():
                print(f"✅ Test video created: {self.test_video_path} ({self.test_video_path.stat().st_size} bytes)")
                return True
            else:
                print("❌ Failed to create test video")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test video: {e}")
            return False
    
    def test_health_check(self):
        """Test API health check endpoint"""
        try:
            print("\n🔍 Testing API Health Check...")
            response = self.session.get(f"{BASE_URL}/", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Video Art Converter API" in data["message"]:
                    print("✅ Health check passed")
                    self.test_results["health_check"] = True
                    return True
                else:
                    print(f"❌ Unexpected health check response: {data}")
            else:
                print(f"❌ Health check failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        return False
    
    def test_video_upload(self):
        """Test video upload functionality"""
        try:
            print("\n🔍 Testing Video Upload...")
            
            if not self.test_video_path or not self.test_video_path.exists():
                print("❌ Test video not available")
                return False
            
            with open(self.test_video_path, 'rb') as video_file:
                files = {'file': ('test_video.mp4', video_file, 'video/mp4')}
                response = self.session.post(f"{BASE_URL}/upload", files=files, timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if "project_id" in data and "metadata" in data:
                    project_id = data["project_id"]
                    self.project_ids.append(project_id)
                    metadata = data["metadata"]
                    
                    print(f"✅ Video uploaded successfully")
                    print(f"   Project ID: {project_id}")
                    print(f"   Duration: {metadata.get('duration', 'N/A')}s")
                    print(f"   Dimensions: {metadata.get('width', 'N/A')}x{metadata.get('height', 'N/A')}")
                    print(f"   FPS: {metadata.get('fps', 'N/A')}")
                    print(f"   Size: {metadata.get('size_mb', 'N/A'):.2f} MB")
                    
                    self.test_results["video_upload"] = True
                    return True
                else:
                    print(f"❌ Invalid upload response: {data}")
            else:
                print(f"❌ Upload failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
        
        return False
    
    def test_video_preview(self):
        """Test video preview functionality"""
        try:
            print("\n🔍 Testing Video Preview...")
            
            if not self.project_ids:
                print("❌ No project ID available for preview test")
                return False
            
            project_id = self.project_ids[0]
            response = self.session.get(f"{BASE_URL}/preview/{project_id}", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if "preview_frames" in data and len(data["preview_frames"]) > 0:
                    frames_count = len(data["preview_frames"])
                    print(f"✅ Preview generated successfully with {frames_count} frames")
                    
                    # Validate base64 format
                    for i, frame in enumerate(data["preview_frames"]):
                        if frame.startswith("data:image/jpeg;base64,"):
                            print(f"   Frame {i+1}: Valid base64 format")
                        else:
                            print(f"   Frame {i+1}: Invalid format")
                            return False
                    
                    self.test_results["video_preview"] = True
                    return True
                else:
                    print(f"❌ Invalid preview response: {data}")
            else:
                print(f"❌ Preview failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Preview error: {e}")
        
        return False
    
    def test_video_processing(self, art_style="pencil", intensity=0.7):
        """Test video processing with artistic effects"""
        try:
            print(f"\n🔍 Testing {art_style.title()} Processing...")
            
            if not self.project_ids:
                print("❌ No project ID available for processing test")
                return False
            
            project_id = self.project_ids[0]
            
            # Start processing
            processing_data = {
                "project_id": project_id,
                "art_style": art_style,
                "intensity": intensity
            }
            
            response = self.session.post(f"{BASE_URL}/process", json=processing_data, timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "started" in data["message"].lower():
                    print(f"✅ {art_style.title()} processing started successfully")
                    
                    # Monitor processing status
                    return self.monitor_processing_status(project_id, art_style)
                else:
                    print(f"❌ Invalid processing response: {data}")
            else:
                print(f"❌ Processing failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
        
        return False
    
    def monitor_processing_status(self, project_id, art_style):
        """Monitor processing status until completion"""
        try:
            print(f"   Monitoring {art_style} processing status...")
            start_time = time.time()
            
            while time.time() - start_time < PROCESSING_TIMEOUT:
                response = self.session.get(f"{BASE_URL}/status/{project_id}", timeout=TEST_TIMEOUT)
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "unknown")
                    progress = status_data.get("progress", 0)
                    message = status_data.get("message", "")
                    
                    print(f"   Status: {status}, Progress: {progress:.1f}% - {message}")
                    
                    if status == "completed":
                        print(f"✅ {art_style.title()} processing completed successfully")
                        if art_style == "pencil":
                            self.test_results["pencil_processing"] = True
                        elif art_style == "cartoon":
                            self.test_results["cartoon_processing"] = True
                        self.test_results["status_tracking"] = True
                        return True
                    elif status == "failed":
                        print(f"❌ {art_style.title()} processing failed: {message}")
                        return False
                    
                    time.sleep(2)  # Wait 2 seconds before next status check
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    return False
            
            print(f"❌ {art_style.title()} processing timeout after {PROCESSING_TIMEOUT} seconds")
            return False
            
        except Exception as e:
            print(f"❌ Status monitoring error: {e}")
            return False
    
    def test_projects_list(self):
        """Test projects listing functionality"""
        try:
            print("\n🔍 Testing Projects List...")
            
            response = self.session.get(f"{BASE_URL}/projects", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                projects = response.json()
                if isinstance(projects, list) and len(projects) > 0:
                    print(f"✅ Projects list retrieved successfully ({len(projects)} projects)")
                    
                    # Check if our test project is in the list
                    for project in projects:
                        if project.get("id") in self.project_ids:
                            print(f"   Found test project: {project.get('filename', 'N/A')}")
                            print(f"   Status: {project.get('status', 'N/A')}")
                            print(f"   Art Style: {project.get('art_style', 'N/A')}")
                    
                    self.test_results["projects_list"] = True
                    return True
                else:
                    print(f"❌ Invalid projects response: {projects}")
            else:
                print(f"❌ Projects list failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Projects list error: {e}")
        
        return False
    
    def test_video_download(self):
        """Test video download functionality"""
        try:
            print("\n🔍 Testing Video Download...")
            
            if not self.project_ids:
                print("❌ No project ID available for download test")
                return False
            
            project_id = self.project_ids[0]
            response = self.session.get(f"{BASE_URL}/download/{project_id}", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'video/mp4':
                    content_length = len(response.content)
                    print(f"✅ Video download successful ({content_length} bytes)")
                    
                    # Save downloaded video for verification
                    download_path = Path("/tmp/downloaded_video.mp4")
                    with open(download_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   Downloaded video saved to: {download_path}")
                    self.test_results["video_download"] = True
                    return True
                else:
                    print(f"❌ Invalid content type: {response.headers.get('content-type')}")
            else:
                print(f"❌ Download failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Download error: {e}")
        
        return False
    
    def test_advanced_features(self):
        """Test advanced video editing features (crop, trim, resize)"""
        try:
            print("\n🔍 Testing Advanced Video Editing Features...")
            
            if not self.project_ids:
                print("❌ No project ID available for advanced features test")
                return False
            
            # Upload another video for advanced testing
            if not self.create_test_video():
                return False
            
            # Test with crop, trim, and resize parameters
            with open(self.test_video_path, 'rb') as video_file:
                files = {'file': ('test_video_advanced.mp4', video_file, 'video/mp4')}
                response = self.session.post(f"{BASE_URL}/upload", files=files, timeout=TEST_TIMEOUT)
            
            if response.status_code != 200:
                print("❌ Failed to upload video for advanced testing")
                return False
            
            advanced_project_id = response.json()["project_id"]
            
            # Test processing with crop, trim, and resize
            processing_data = {
                "project_id": advanced_project_id,
                "art_style": "cartoon",
                "intensity": 0.5,
                "crop_params": {"x": 50, "y": 50, "width": 400, "height": 300},
                "trim_params": {"start_time": 0.5, "end_time": 2.0},
                "resize_params": {"width": 320, "height": 240}
            }
            
            response = self.session.post(f"{BASE_URL}/process", json=processing_data, timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                print("✅ Advanced processing started with crop/trim/resize")
                
                # Monitor this processing
                if self.monitor_processing_status(advanced_project_id, "advanced"):
                    self.test_results["crop_functionality"] = True
                    self.test_results["trim_functionality"] = True
                    self.test_results["resize_functionality"] = True
                    return True
            else:
                print(f"❌ Advanced processing failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Advanced features error: {e}")
        
        return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Video Art Converter Backend API Tests")
        print("=" * 60)
        
        # Create test video
        if not self.create_test_video():
            print("❌ Cannot proceed without test video")
            return False
        
        # Run tests in sequence
        test_sequence = [
            ("Health Check", self.test_health_check),
            ("Video Upload", self.test_video_upload),
            ("Video Preview", self.test_video_preview),
            ("Pencil Processing", lambda: self.test_video_processing("pencil")),
            ("Cartoon Processing", lambda: self.test_video_processing("cartoon")),
            ("Projects List", self.test_projects_list),
            ("Video Download", self.test_video_download),
            ("Advanced Features", self.test_advanced_features)
        ]
        
        for test_name, test_func in test_sequence:
            try:
                success = test_func()
                if not success:
                    print(f"⚠️  {test_name} test failed, continuing with remaining tests...")
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
        
        # Print final results
        self.print_test_summary()
        
        return self.get_overall_success()
    
    def print_test_summary(self):
        """Print comprehensive test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<35} {status}")
        
        print("-" * 60)
        print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Video Art Converter backend is working perfectly!")
        elif passed >= total * 0.8:
            print("✅ Most tests passed. Minor issues detected.")
        else:
            print("❌ Multiple critical issues detected. Backend needs attention.")
    
    def get_overall_success(self):
        """Return overall test success status"""
        critical_tests = ["health_check", "video_upload", "pencil_processing", "cartoon_processing"]
        return all(self.test_results[test] for test in critical_tests)
    
    def cleanup(self):
        """Clean up test files"""
        try:
            if self.test_video_path and self.test_video_path.exists():
                self.test_video_path.unlink()
                print("🧹 Test video cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

def main():
    """Main test execution"""
    tester = VideoArtConverterTester()
    
    try:
        success = tester.run_all_tests()
        return success
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)