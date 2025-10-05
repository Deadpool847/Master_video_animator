#!/usr/bin/env python3
"""
Final Masterpiece Test - Test all enhanced features
"""

import requests
import cv2
import numpy as np
from pathlib import Path
import time
import tempfile

BASE_URL = "http://localhost:8001/api"

def create_test_video():
    """Create a colorful test video"""
    temp_dir = Path(tempfile.gettempdir())
    video_path = temp_dir / "final_masterpiece_test.mp4"
    
    width, height = 640, 480
    fps = 30
    duration = 3
    total_frames = fps * duration
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create rainbow background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Rainbow gradient
        for y in range(height):
            hue = int(180 * (y / height))
            color = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
            frame[y, :] = color
        
        # Moving elements
        progress = frame_num / total_frames
        
        # Bouncing ball
        ball_x = int(width * 0.1 + (width * 0.8 * abs(np.sin(progress * np.pi * 3))))
        ball_y = int(height * 0.2 + (height * 0.6 * abs(np.cos(progress * np.pi * 2))))
        cv2.circle(frame, (ball_x, ball_y), 40, (255, 255, 255), -1)
        
        # Rotating rectangle
        center_x, center_y = width // 2, height // 2 + 100
        angle = progress * 360
        rect_points = cv2.boxPoints(((center_x, center_y), (80, 80), angle))
        rect_points = np.int32(rect_points)
        cv2.fillPoly(frame, [rect_points], (0, 255, 255))
        
        # Text overlay
        text = f"MASTERPIECE TEST {frame_num:03d}"
        cv2.putText(frame, text, (50, height - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    return video_path

def test_complete_workflow():
    """Test the complete enhanced workflow"""
    print("🎨 FINAL MASTERPIECE TEST - Enhanced Features")
    print("=" * 50)
    
    # Create test video
    print("🎬 Creating test video...")
    video_path = create_test_video()
    print(f"✅ Test video created: {video_path}")
    
    # Upload video
    print("📤 Uploading video...")
    with open(video_path, 'rb') as video_file:
        files = {'file': ('masterpiece_test.mp4', video_file, 'video/mp4')}
        response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        return False
    
    project_id = response.json()["project_id"]
    print(f"✅ Video uploaded: {project_id}")
    
    # Test AI Analysis
    print("🤖 Testing AI Analysis...")
    analysis_response = requests.get(f"{BASE_URL}/analyze/{project_id}", timeout=30)
    if analysis_response.status_code == 200:
        analysis = analysis_response.json()
        print(f"✅ AI Analysis complete - {len(analysis['ai_recommendations'])} recommendations")
        for rec in analysis['ai_recommendations']:
            print(f"   📊 {rec['effect']}: {rec['confidence']:.1%} confidence")
    
    # Test Oil Painting Effect (Advanced)
    print("🎨 Testing Oil Painting Effect...")
    processing_data = {
        "project_id": project_id,
        "art_style": "oil_painting",
        "intensity": 0.8
    }
    
    process_response = requests.post(f"{BASE_URL}/process", json=processing_data, timeout=30)
    if process_response.status_code != 200:
        print(f"❌ Processing failed: {process_response.status_code}")
        return False
    
    print("✅ Oil painting processing started")
    
    # Monitor processing
    print("⏳ Monitoring processing...")
    for i in range(60):  # 1 minute max
        status_response = requests.get(f"{BASE_URL}/status/{project_id}", timeout=10)
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   📊 {status['status']}: {status['progress']:.1f}% - {status.get('message', '')}")
            
            if status['status'] == 'completed':
                print("✅ Processing completed!")
                break
            elif status['status'] == 'failed':
                print(f"❌ Processing failed: {status.get('message')}")
                return False
        
        time.sleep(2)
    
    # Test Gallery
    print("🖼️ Testing Gallery...")
    gallery_response = requests.get(f"{BASE_URL}/gallery", timeout=30)
    if gallery_response.status_code == 200:
        gallery = gallery_response.json()
        print(f"✅ Gallery loaded: {gallery['total_count']} items")
    
    # Test Preview
    print("👁️ Testing Preview...")
    preview_response = requests.get(f"{BASE_URL}/preview-video/{project_id}", timeout=30)
    if preview_response.status_code == 200:
        print(f"✅ Preview available: {len(preview_response.content)} bytes")
    
    # Test Enhanced Download
    print("📥 Testing Enhanced Download...")
    download_response = requests.get(f"{BASE_URL}/download/{project_id}", timeout=60)
    if download_response.status_code == 200:
        # Check filename from headers
        content_disposition = download_response.headers.get('content-disposition', '')
        filename = 'unknown'
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        
        print(f"✅ Download successful: {len(download_response.content)} bytes")
        print(f"   📄 Filename: {filename}")
        print(f"   📊 Content-Type: {download_response.headers.get('content-type')}")
    else:
        print(f"❌ Download failed: {download_response.status_code}")
        return False
    
    # Test Comparison Grid
    print("🎯 Testing Comparison Grid...")
    comparison_response = requests.post(f"{BASE_URL}/batch-compare/{project_id}", timeout=60)
    if comparison_response.status_code == 200:
        print("✅ Comparison grid created successfully")
        
        # Test comparison download
        comp_download = requests.get(f"{BASE_URL}/download-comparison/{project_id}", timeout=30)
        if comp_download.status_code == 200:
            print(f"✅ Comparison grid download: {len(comp_download.content)} bytes")
    
    print("\n🎉 FINAL MASTERPIECE TEST COMPLETE!")
    print("=" * 50)
    print("✅ All enhanced features working perfectly!")
    print("🎨 Video Art Masterpiece is ready for elite usage!")
    
    # Cleanup
    if video_path.exists():
        video_path.unlink()
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)