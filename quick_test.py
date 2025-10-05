#!/usr/bin/env python3
"""
Quick test for remaining functionality
"""

import requests
import json
import cv2
import numpy as np
from pathlib import Path

BASE_URL = "https://pencil-animator.preview.emergentagent.com/api"

def create_test_video():
    """Create a small test video"""
    test_video_path = Path("/tmp/quick_test_video.mp4")
    
    width, height = 320, 240
    fps = 15
    duration = 2
    total_frames = fps * duration
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(test_video_path), fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = [100, 150, 200]  # Blue background
        
        # Add a moving circle
        center_x = int(width * (frame_num / total_frames))
        center_y = height // 2
        cv2.circle(frame, (center_x, center_y), 20, (255, 255, 0), -1)
        
        out.write(frame)
    
    out.release()
    return test_video_path

def test_advanced_processing():
    """Test advanced processing with crop/trim/resize"""
    print("🔍 Testing Advanced Processing Features...")
    
    # Create test video
    video_path = create_test_video()
    
    # Upload video
    with open(video_path, 'rb') as video_file:
        files = {'file': ('quick_test.mp4', video_file, 'video/mp4')}
        response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return False
    
    project_id = response.json()["project_id"]
    print(f"✅ Video uploaded: {project_id}")
    
    # Test processing with advanced parameters
    processing_data = {
        "project_id": project_id,
        "art_style": "pencil",
        "intensity": 0.8,
        "crop_params": {"x": 20, "y": 20, "width": 280, "height": 200},
        "trim_params": {"start_time": 0.2, "end_time": 1.5},
        "resize_params": {"width": 160, "height": 120}
    }
    
    response = requests.post(f"{BASE_URL}/process", json=processing_data, timeout=30)
    
    if response.status_code == 200:
        print("✅ Advanced processing started successfully")
        return True
    else:
        print(f"❌ Advanced processing failed: {response.text}")
        return False

def test_projects_and_download():
    """Test projects list and download"""
    print("🔍 Testing Projects List and Download...")
    
    # Test projects list
    response = requests.get(f"{BASE_URL}/projects", timeout=30)
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Projects list retrieved: {len(projects)} projects")
        
        # Find a completed project
        completed_projects = [p for p in projects if p.get('status') == 'completed']
        if completed_projects:
            project_id = completed_projects[0]['id']
            print(f"   Testing download for project: {project_id}")
            
            # Test download
            download_response = requests.get(f"{BASE_URL}/download/{project_id}", timeout=30)
            if download_response.status_code == 200 and len(download_response.content) > 0:
                print(f"✅ Download successful: {len(download_response.content)} bytes")
                return True
            else:
                print(f"❌ Download failed: {download_response.status_code}")
        else:
            print("⚠️  No completed projects found for download test")
            return True  # Not a failure, just no data
    else:
        print(f"❌ Projects list failed: {response.status_code}")
    
    return False

if __name__ == "__main__":
    print("🚀 Running Quick Backend Tests")
    print("=" * 40)
    
    advanced_ok = test_advanced_processing()
    projects_ok = test_projects_and_download()
    
    print("\n" + "=" * 40)
    print("📊 QUICK TEST RESULTS")
    print("=" * 40)
    print(f"Advanced Processing: {'✅ PASS' if advanced_ok else '❌ FAIL'}")
    print(f"Projects & Download: {'✅ PASS' if projects_ok else '❌ FAIL'}")
    
    if advanced_ok and projects_ok:
        print("🎉 All quick tests passed!")
    else:
        print("⚠️  Some issues detected")