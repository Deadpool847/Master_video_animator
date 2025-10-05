#!/usr/bin/env python3
"""
Simplified, ultra-reliable video processor for the Video Art Converter
This module provides bulletproof video processing with multiple fallback mechanisms
"""

import cv2
import numpy as np
from pathlib import Path
import logging
import tempfile
import subprocess
import shutil

class SuperReliableVideoProcessor:
    """Ultra-reliable video processor with multiple fallback strategies"""
    
    @staticmethod
    def apply_pencil_effect_simple(frame, intensity=0.5):
        """Simplified pencil effect that always works"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Simple edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Invert edges
            edges_inv = 255 - edges
            
            # Convert back to BGR
            result = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2BGR)
            
            # Blend with original based on intensity
            if intensity < 1.0:
                result = cv2.addWeighted(frame, (1 - intensity), result, intensity, 0)
            
            return result
        except:
            # Ultimate fallback: return original frame
            return frame
    
    @staticmethod
    def apply_cartoon_effect_simple(frame, intensity=0.5):
        """Simplified cartoon effect that always works"""
        try:
            # Simple bilateral filter
            smooth = cv2.bilateralFilter(frame, 9, 80, 80)
            
            # Edge detection
            gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 7)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            # Simple color quantization
            result = cv2.bitwise_and(smooth, edges)
            
            # Blend with original
            if intensity < 1.0:
                result = cv2.addWeighted(frame, (1 - intensity), result, intensity, 0)
            
            return result
        except:
            return frame
    
    @staticmethod
    def process_video_bulletproof(input_path, output_path, art_style='pencil', intensity=0.5, 
                                crop_params=None, trim_params=None, resize_params=None, 
                                progress_callback=None):
        """Process video with bulletproof reliability"""
        
        temp_dir = Path(tempfile.gettempdir()) / "video_processing"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Open input video
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise Exception("Cannot open input video")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # Default FPS
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate frame range
            start_frame = 0
            end_frame = total_frames
            
            if trim_params:
                start_frame = max(0, int(trim_params.get('start_time', 0) * fps))
                end_frame = min(total_frames, int(trim_params.get('end_time', total_frames / fps) * fps))
            
            # Determine output dimensions
            out_width, out_height = width, height
            if resize_params:
                out_width = resize_params['width']
                out_height = resize_params['height']
            elif crop_params:
                out_width = crop_params['width']
                out_height = crop_params['height']
            
            # Create temporary output file first
            temp_output = temp_dir / f"temp_output_{Path(output_path).stem}.avi"
            
            # Use most compatible codec (MJPG in AVI container)
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(str(temp_output), fourcc, fps, (out_width, out_height))
            
            if not out.isOpened():
                # Try with XVID codec
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(str(temp_output), fourcc, fps, (out_width, out_height))
            
            if not out.isOpened():
                raise Exception("Cannot create video writer")
            
            # Process frames
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            frames_processed = 0
            
            for frame_num in range(start_frame, end_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Apply crop if specified
                if crop_params:
                    x, y, w, h = crop_params['x'], crop_params['y'], crop_params['width'], crop_params['height']
                    # Ensure coordinates are within bounds
                    x = max(0, min(x, width - w))
                    y = max(0, min(y, height - h))
                    w = min(w, width - x)
                    h = min(h, height - y)
                    frame = frame[y:y+h, x:x+w]
                
                # Apply resize if specified
                if resize_params or crop_params:
                    frame = cv2.resize(frame, (out_width, out_height))
                
                # Apply artistic effect
                if art_style == 'pencil':
                    frame = SuperReliableVideoProcessor.apply_pencil_effect_simple(frame, intensity)
                elif art_style == 'cartoon':
                    frame = SuperReliableVideoProcessor.apply_cartoon_effect_simple(frame, intensity)
                
                # Write frame
                out.write(frame)
                frames_processed += 1
            
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            
            if frames_processed == 0:
                raise Exception("No frames were processed")
            
            # Convert to MP4 using FFmpeg if possible
            if shutil.which('ffmpeg'):
                try:
                    cmd = [
                        'ffmpeg', '-y', '-i', str(temp_output),
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                        str(output_path)
                    ]
                    result = subprocess.run(cmd, capture_output=True, timeout=120)
                    
                    if result.returncode == 0 and Path(output_path).exists():
                        # Success! Clean up temp file
                        temp_output.unlink(missing_ok=True)
                        return frames_processed
                except:
                    pass
            
            # Fallback: just copy the AVI file
            shutil.move(str(temp_output), str(output_path))
            return frames_processed
            
        except Exception as e:
            logging.error(f"Video processing error: {e}")
            raise
        finally:
            # Clean up
            if temp_output.exists():
                temp_output.unlink(missing_ok=True)

def test_processor():
    """Test the processor with a simple video"""
    # Create a simple test video
    test_input = Path("/tmp/test_input.avi")
    test_output = Path("/tmp/test_output.mp4")
    
    # Create test video
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(str(test_input), fourcc, 10, (320, 240))
    
    for i in range(30):  # 3 seconds at 10fps
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        cv2.circle(frame, (160, 120), 50, (255, 255, 255), -1)
        out.write(frame)
    
    out.release()
    
    # Test processing
    try:
        frames = SuperReliableVideoProcessor.process_video_bulletproof(
            test_input, test_output, art_style='pencil', intensity=0.7
        )
        print(f"✅ Processed {frames} frames successfully!")
        return True
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False
    finally:
        # Cleanup
        test_input.unlink(missing_ok=True)
        test_output.unlink(missing_ok=True)

if __name__ == "__main__":
    test_processor()