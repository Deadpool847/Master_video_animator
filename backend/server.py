from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import cv2
import numpy as np
import asyncio
import aiofiles
import shutil
import tempfile
import json
import base64
from threading import Thread
import time
import sys
sys.path.append('/app')
from simple_video_processor import SuperReliableVideoProcessor
from advanced_features import AdvancedArtisticEffects, SmartVideoAnalyzer, BatchVideoProcessor

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create directories for video processing
UPLOAD_DIR = ROOT_DIR / "uploads"
OUTPUT_DIR = ROOT_DIR / "outputs"
TEMP_DIR = ROOT_DIR / "temp"
GALLERY_DIR = ROOT_DIR / "gallery"  # Internal gallery for processed videos
PREVIEW_DIR = ROOT_DIR / "previews"  # Preview videos directory

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR, GALLERY_DIR, PREVIEW_DIR]:
    dir_path.mkdir(exist_ok=True)

# Define Models
class VideoProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_size: int
    duration: float
    width: int
    height: int
    fps: float
    status: str = "uploaded"  # uploaded, processing, completed, failed
    progress: float = 0.0
    art_style: Optional[str] = None  # pencil, cartoon, oil_painting, watercolor, anime, vintage_film
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    output_path: Optional[str] = None
    gallery_path: Optional[str] = None  # Internal gallery copy
    preview_path: Optional[str] = None  # Preview video path
    processing_params: Dict[str, Any] = Field(default_factory=dict)
    thumbnail: Optional[str] = None  # Base64 thumbnail

class VideoProjectCreate(BaseModel):
    filename: str

class ProcessingRequest(BaseModel):
    project_id: str
    art_style: str  # pencil or cartoon
    crop_params: Optional[Dict[str, int]] = None  # {x, y, width, height}
    trim_params: Optional[Dict[str, float]] = None  # {start_time, end_time}
    resize_params: Optional[Dict[str, int]] = None  # {width, height}
    intensity: float = 0.5  # 0.0 to 1.0

class ProcessingStatus(BaseModel):
    project_id: str
    status: str
    progress: float
    message: Optional[str] = None

# Global processing status tracking
processing_status = {}

# Cleanup function for stuck processes
def cleanup_processing_status():
    """Clean up old processing status entries"""
    current_time = time.time()
    to_remove = []
    for project_id, status in processing_status.items():
        # Remove entries older than 1 hour
        if hasattr(status, 'timestamp'):
            if current_time - status['timestamp'] > 3600:
                to_remove.append(project_id)
        else:
            # Add timestamp to existing entries
            status['timestamp'] = current_time
    
    for project_id in to_remove:
        del processing_status[project_id]

class VideoProcessor:
    @staticmethod
    def apply_pencil_sketch(frame, intensity=0.5):
        """Apply optimized pencil sketch effect to a frame"""
        # Resize frame for faster processing if it's too large
        height, width = frame.shape[:2]
        max_dimension = 720  # Limit processing size
        
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Optimized pencil sketch algorithm
        inv_gray = 255 - gray
        
        # Reduced blur intensity for faster processing
        blur_size = max(5, int(7 + (intensity * 8)))  # Range: 7-15 (smaller than before)
        if blur_size % 2 == 0:
            blur_size += 1
        blurred = cv2.GaussianBlur(inv_gray, (blur_size, blur_size), 0)
        
        # Create pencil sketch
        sketch = cv2.divide(gray, 255 - blurred, scale=256)
        
        # Simplified thresholding for speed
        sketch = cv2.adaptiveThreshold(sketch, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 8)
        
        # Convert to BGR
        sketch_bgr = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        
        # Resize back to original size if needed
        if max(height, width) > max_dimension:
            sketch_bgr = cv2.resize(sketch_bgr, (width, height))
        
        # Blend with original if intensity is not full
        if intensity < 1.0:
            original_resized = frame if max(height, width) <= max_dimension else cv2.resize(frame, (width, height))
            sketch_bgr = cv2.addWeighted(original_resized, (1 - intensity), sketch_bgr, intensity, 0)
        
        return sketch_bgr
    
    @staticmethod
    def apply_cartoon_effect(frame, intensity=0.5):
        """Apply optimized cartoon effect to a frame"""
        # Resize frame for faster processing if it's too large
        height, width = frame.shape[:2]
        max_dimension = 720
        
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Optimized cartoon effect
        # Reduce noise with faster bilateral filter
        bilateral = cv2.bilateralFilter(frame, 5, 80, 80)  # Reduced parameters for speed
        
        # Create edge mask
        gray = cv2.cvtColor(bilateral, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 8)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Faster color quantization
        k = max(4, int(6 + intensity * 3))  # Reduced colors for speed (6-9)
        h, w = bilateral.shape[:2]
        data = bilateral.reshape((-1, 3))
        data = np.float32(data)
        
        # Reduced iterations for faster k-means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        
        centers = np.uint8(centers)
        quantized_data = centers[labels.flatten()]
        quantized = quantized_data.reshape((h, w, 3))
        
        # Combine with edges
        cartoon = cv2.bitwise_and(quantized, edges)
        
        # Resize back to original if needed
        if max(height, width) > max_dimension:
            cartoon = cv2.resize(cartoon, (width, height))
        
        # Blend with original
        if intensity < 1.0:
            original_resized = frame if max(height, width) <= max_dimension else cv2.resize(frame, (width, height))
            cartoon = cv2.addWeighted(original_resized, (1 - intensity), cartoon, intensity, 0)
        
        return cartoon
    
    @staticmethod
    async def combine_chunks_opencv(temp_outputs, output_path):
        """Robust fallback method to combine chunks using OpenCV when FFmpeg fails"""
        try:
            if not temp_outputs:
                raise Exception("No chunks to combine")
            
            # Get properties from first chunk
            first_cap = cv2.VideoCapture(str(temp_outputs[0]))
            if not first_cap.isOpened():
                raise Exception("Cannot open first chunk for reading")
            
            fps = max(1.0, first_cap.get(cv2.CAP_PROP_FPS))  # Ensure valid FPS
            width = int(first_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(first_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            first_cap.release()
            
            # Try multiple codecs for output
            codecs_to_try = [
                ('mp4v', '.mp4'),
                ('XVID', '.avi'),
                ('MJPG', '.avi')
            ]
            
            out = None
            final_output_path = output_path
            
            for codec, ext in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    test_path = str(output_path).replace('.mp4', ext)
                    out = cv2.VideoWriter(test_path, fourcc, fps, (width, height))
                    
                    if out.isOpened():
                        final_output_path = Path(test_path)
                        break
                    else:
                        out.release()
                        out = None
                except Exception:
                    continue
            
            if out is None:
                raise Exception("Cannot create video writer with any codec")
            
            # Combine all chunks
            frames_written = 0
            for chunk_path in temp_outputs:
                cap = cv2.VideoCapture(str(chunk_path))
                if cap.isOpened():
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # Ensure frame dimensions match
                        if frame.shape[1] != width or frame.shape[0] != height:
                            frame = cv2.resize(frame, (width, height))
                        
                        out.write(frame)
                        frames_written += 1
                    cap.release()
            
            out.release()
            cv2.destroyAllWindows()
            
            if frames_written > 0:
                # If we used a different extension, move to expected location
                if final_output_path != output_path:
                    shutil.move(str(final_output_path), str(output_path))
                
                logging.info(f"Successfully combined {len(temp_outputs)} chunks using OpenCV fallback ({frames_written} frames)")
            else:
                raise Exception("No frames were written to output")
            
        except Exception as e:
            logging.error(f"OpenCV chunk combination failed: {e}")
            # Last resort: just copy the largest chunk
            if temp_outputs:
                largest_chunk = max(temp_outputs, key=lambda p: p.stat().st_size if p.exists() else 0)
                if largest_chunk.exists():
                    shutil.copy2(str(largest_chunk), str(output_path))
                    logging.info("Used largest chunk as fallback output")
    
    @staticmethod
    async def process_video_chunk(input_path, output_path, start_frame, end_frame, art_style, intensity, crop_params, resize_params, project_id):
        """Process a chunk of video frames with optimized performance"""
        cap = None
        out = None
        
        try:
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise Exception("Cannot open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Determine output dimensions
            if resize_params:
                width, height = resize_params['width'], resize_params['height']
            else:
                width, height = original_width, original_height
            
            if crop_params:
                width = crop_params['width']
                height = crop_params['height']
            
            # Remove existing output file to avoid FFmpeg prompts
            if output_path.exists():
                output_path.unlink()
            
            # Try multiple codecs for maximum compatibility
            codecs_to_try = [
                ('mp4v', '.mp4'),  # Most reliable
                ('XVID', '.avi'),  # Fallback 1
                ('MJPG', '.avi')   # Fallback 2
            ]
            
            out = None
            for codec, ext in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    test_path = str(output_path).replace('.mp4', ext)
                    out = cv2.VideoWriter(test_path, fourcc, fps, (width, height))
                    if out.isOpened():
                        # Update output path if we changed extension
                        output_path = Path(test_path)
                        break
                    else:
                        out.release()
                        out = None
                except Exception:
                    continue
            
            if out is None or not out.isOpened():
                raise Exception("Could not initialize video writer with any codec")
            
            # Jump to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_count = start_frame
            processed_frames = 0
            total_chunk_frames = end_frame - start_frame
            
            # Process frames with optimized batching
            batch_size = 5  # Process 5 frames at a time for better performance
            
            while frame_count < end_frame and cap.isOpened():
                frames_batch = []
                
                # Read batch of frames
                for _ in range(batch_size):
                    if frame_count >= end_frame:
                        break
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames_batch.append(frame)
                    frame_count += 1
                
                if not frames_batch:
                    break
                
                # Process batch
                for frame in frames_batch:
                    # Apply crop if specified
                    if crop_params:
                        x, y, w, h = crop_params['x'], crop_params['y'], crop_params['width'], crop_params['height']
                        # Ensure crop coordinates are within bounds
                        x = max(0, min(x, original_width - w))
                        y = max(0, min(y, original_height - h))
                        frame = frame[y:y+h, x:x+w]
                    
                    # Apply resize if specified
                    if resize_params:
                        frame = cv2.resize(frame, (resize_params['width'], resize_params['height']))
                    
                    # Apply artistic effect
                    if art_style == 'pencil':
                        frame = VideoProcessor.apply_pencil_sketch(frame, intensity)
                    elif art_style == 'cartoon':
                        frame = VideoProcessor.apply_cartoon_effect(frame, intensity)
                    
                    if out.isOpened():
                        out.write(frame)
                    processed_frames += 1
                
                # Update progress every batch
                progress = min(95, (processed_frames / total_chunk_frames) * 100)
                processing_status[project_id] = {
                    'status': 'processing',
                    'progress': progress,
                    'message': f'Processing {art_style} effect: {processed_frames}/{total_chunk_frames} frames'
                }
                
                # Allow other async tasks to run
                await asyncio.sleep(0.001)
            
            return True
            
        except Exception as e:
            logging.error(f"Error processing chunk: {e}")
            processing_status[project_id] = {
                'status': 'failed',
                'progress': 0,
                'message': f'Processing error: {str(e)}'
            }
            return False
            
        finally:
            if cap:
                cap.release()
            if out:
                out.release()
            # Clean up memory
            cv2.destroyAllWindows()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Video Art Converter API - Ready to create masterpieces!"}

@api_router.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        # Check disk space
        import shutil
        disk_usage = shutil.disk_usage("/app")
        free_gb = disk_usage.free / (1024**3)
        
        # Check FFmpeg availability
        ffmpeg_available = Path('/usr/bin/ffmpeg').exists()
        
        # Check database connection
        db_healthy = False
        try:
            await db.video_projects.find_one({})
            db_healthy = True
        except Exception:
            pass
        
        # Check OpenCV
        opencv_version = cv2.__version__
        
        health_status = {
            "status": "healthy" if all([free_gb > 1, ffmpeg_available, db_healthy]) else "degraded",
            "disk_space_gb": round(free_gb, 2),
            "ffmpeg_available": ffmpeg_available,
            "database_connected": db_healthy,
            "opencv_version": opencv_version,
            "active_processes": len(processing_status),
            "directories_ready": all([
                UPLOAD_DIR.exists(),
                OUTPUT_DIR.exists(),
                TEMP_DIR.exists()
            ])
        }
        
        return health_status
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@api_router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file with comprehensive validation and chunked processing support"""
    try:
        # Input validation
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file content type and extension
        valid_video_types = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo']
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        
        is_valid_type = file.content_type and file.content_type in valid_video_types
        is_valid_extension = any(file.filename.lower().endswith(ext) for ext in valid_extensions)
        
        if not (is_valid_type or is_valid_extension):
            raise HTTPException(status_code=400, detail="File must be a video format (.mp4, .avi, .mov, etc.)")
        
        # Check file size (max 2GB for safety)
        content = await file.read()
        if len(content) > 2 * 1024 * 1024 * 1024:  # 2GB
            raise HTTPException(status_code=413, detail="File too large (max 2GB)")
        
        if len(content) < 1000:  # Minimum viable video size
            raise HTTPException(status_code=400, detail="File too small or corrupted")
        
        project_id = str(uuid.uuid4())
        # Sanitize filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ".-_")
        if not safe_filename:
            safe_filename = "uploaded_video.mp4"
        
        file_path = UPLOAD_DIR / f"{project_id}_{safe_filename}"
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Extract video metadata
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Invalid video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        # Create project record
        project = VideoProject(
            id=project_id,
            filename=file.filename,
            original_size=len(content),
            duration=duration,
            width=width,
            height=height,
            fps=fps
        )
        
        # Save to database
        await db.video_projects.insert_one(project.dict())
        
        return {
            "project_id": project_id,
            "message": "Video uploaded successfully",
            "metadata": {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
                "size_mb": len(content) / (1024 * 1024)
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logging.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.post("/process")
async def process_video(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Start video processing with artistic effects and comprehensive validation"""
    try:
        # Validate art style
        valid_styles = ['pencil', 'cartoon', 'oil_painting', 'watercolor', 'anime', 'vintage_film']
        if request.art_style not in valid_styles:
            raise HTTPException(status_code=400, detail=f"Art style must be one of: {', '.join(valid_styles)}")
        
        # Validate intensity
        if not (0.0 <= request.intensity <= 1.0):
            raise HTTPException(status_code=400, detail="Intensity must be between 0.0 and 1.0")
        # Get project from database
        project_doc = await db.video_projects.find_one({"id": request.project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Clean up old processing entries
        cleanup_processing_status()
        
        # Initialize processing status
        processing_status[request.project_id] = {
            'status': 'starting',
            'progress': 0,
            'message': 'Initializing processing...',
            'timestamp': time.time()
        }
        
        # Update project status
        await db.video_projects.update_one(
            {"id": request.project_id},
            {"$set": {"status": "processing", "art_style": request.art_style, "processing_params": request.dict()}}
        )
        
        # Start background processing
        background_tasks.add_task(
            process_video_background,
            request.project_id,
            request.art_style,
            request.intensity,
            request.crop_params,
            request.trim_params,
            request.resize_params
        )
        
        return {"message": "Processing started", "project_id": request.project_id}
        
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logging.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_video_background(project_id: str, art_style: str, intensity: float, crop_params: Optional[Dict], trim_params: Optional[Dict], resize_params: Optional[Dict]):
    """Background task for super-reliable video processing"""
    try:
        # Get input file path
        input_path = None
        for file_path in UPLOAD_DIR.glob(f"{project_id}_*"):
            input_path = file_path
            break
        
        if not input_path:
            raise Exception("Input video file not found")
        
        output_filename = f"{project_id}_{art_style}_output.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        # Update status to processing
        processing_status[project_id] = {
            'status': 'processing',
            'progress': 10,
            'message': f'Starting {art_style} effect processing...',
            'timestamp': time.time()
        }
        
        # Progress callback function
        def update_progress(progress, message):
            processing_status[project_id] = {
                'status': 'processing',
                'progress': progress,
                'message': message,
                'timestamp': time.time()
            }
        
        # Use the bulletproof processor
        frames_processed = SuperReliableVideoProcessor.process_video_bulletproof(
            input_path=input_path,
            output_path=output_path,
            art_style=art_style,
            intensity=intensity,
            crop_params=crop_params,
            trim_params=trim_params,
            resize_params=resize_params,
            progress_callback=update_progress
        )
        
        # Verify output file was created successfully
        if not output_path.exists() or output_path.stat().st_size < 1000:
            raise Exception("Output file not created or too small")
        
        # Create internal gallery copy with organized structure
        gallery_subdir = GALLERY_DIR / art_style
        gallery_subdir.mkdir(exist_ok=True)
        
        gallery_filename = f"{project_id}_{art_style}_{int(time.time())}.mp4"
        gallery_path = gallery_subdir / gallery_filename
        
        # Copy to gallery
        shutil.copy2(str(output_path), str(gallery_path))
        
        # Create preview video (first 10 seconds or full video if shorter)
        preview_filename = f"{project_id}_preview.mp4"
        preview_path = PREVIEW_DIR / preview_filename
        
        await create_preview_video(str(output_path), str(preview_path))
        
        # Generate thumbnail
        thumbnail_b64 = await generate_video_thumbnail(str(output_path))
        
        # Update database with completion
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "completed", 
                "output_path": str(output_path), 
                "gallery_path": str(gallery_path),
                "preview_path": str(preview_path),
                "thumbnail": thumbnail_b64,
                "progress": 100
            }}
        )
        
        # Update processing status
        processing_status[project_id] = {
            'status': 'completed',
            'progress': 100,
            'message': f'Masterpiece created! Processed {frames_processed} frames with {art_style} effect',
            'timestamp': time.time()
        }
        
        logging.info(f"Video processing completed for project {project_id}: {frames_processed} frames")
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Video processing failed for project {project_id}: {error_msg}")
        
        # Update status to failed
        processing_status[project_id] = {
            'status': 'failed',
            'progress': 0,
            'message': f'Processing failed: {error_msg}',
            'timestamp': time.time()
        }
        
        # Update database
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "failed", "error_message": error_msg}}
        )

async def create_preview_video(input_path, preview_path, max_duration=10):
    """Create a preview video (first 10 seconds or full if shorter)"""
    try:
        import subprocess
        
        # Get video duration first
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', str(input_path)
        ]
        
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            preview_duration = min(duration, max_duration)
        else:
            preview_duration = max_duration
        
        # Create preview using FFmpeg
        ffmpeg_cmd = [
            '/usr/bin/ffmpeg', '-y',
            '-i', str(input_path),
            '-t', str(preview_duration),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '28',  # Slightly lower quality for smaller size
            '-movflags', '+faststart',
            str(preview_path)
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            # Fallback: copy first part using OpenCV
            cap = cv2.VideoCapture(str(input_path))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(preview_path), fourcc, fps, (width, height))
                
                max_frames = int(fps * preview_duration)
                frame_count = 0
                
                while frame_count < max_frames and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    out.write(frame)
                    frame_count += 1
                
                cap.release()
                out.release()
        
        return Path(preview_path).exists()
        
    except Exception as e:
        logging.error(f"Preview creation error: {e}")
        return False

async def generate_video_thumbnail(input_path):
    """Generate a thumbnail from the middle frame of the video"""
    try:
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            return None
        
        # Get middle frame
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame = total_frames // 2
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Resize for thumbnail
            thumbnail = cv2.resize(frame, (320, 240))
            _, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 80])
            thumbnail_b64 = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{thumbnail_b64}"
        
        return None
        
    except Exception as e:
        logging.error(f"Thumbnail generation error: {e}")
        return None

@api_router.get("/status/{project_id}")
async def get_processing_status(project_id: str):
    """Get real-time processing status"""
    status = processing_status.get(project_id)
    if status:
        return ProcessingStatus(project_id=project_id, **status)
    
    # Check database for completed projects
    project_doc = await db.video_projects.find_one({"id": project_id})
    if project_doc:
        project = VideoProject(**project_doc)
        return ProcessingStatus(
            project_id=project_id,
            status=project.status,
            progress=project.progress,
            message=f"Project status: {project.status}"
        )
    
    raise HTTPException(status_code=404, detail="Project not found")

@api_router.get("/projects")
async def get_projects():
    """Get all video projects"""
    projects = await db.video_projects.find().sort("created_at", -1).to_list(100)
    return [VideoProject(**project) for project in projects]

@api_router.get("/download/{project_id}")
async def download_video(project_id: str):
    """Download processed video"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = VideoProject(**project_doc)
        
        if project.status != "completed":
            raise HTTPException(status_code=400, detail=f"Video not ready for download. Status: {project.status}")
        
        if not project.output_path:
            raise HTTPException(status_code=404, detail="Output path not found")
        
        output_path = Path(project.output_path)
        if not output_path.exists():
            # Try to find the file in outputs directory
            potential_files = list(OUTPUT_DIR.glob(f"{project_id}_*output.mp4"))
            if potential_files:
                output_path = potential_files[0]
                # Update the database with correct path
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"output_path": str(output_path)}}
                )
            else:
                raise HTTPException(status_code=404, detail="Output file not found on disk")
        
        # Ensure file is readable
        if not output_path.is_file():
            raise HTTPException(status_code=404, detail="Invalid output file")
        
        # Create a safe filename with timestamp
        timestamp = int(time.time())
        base_name = project.filename.split('.')[0] if '.' in project.filename else project.filename
        safe_base = "".join(c for c in base_name if c.isalnum() or c in "-_")
        art_style_clean = project.art_style.replace('_', '-') if project.art_style else 'processed'
        
        safe_filename = f"{safe_base}_{art_style_clean}_masterpiece_{timestamp}.mp4"
        
        # Get file size for proper headers
        file_size = output_path.stat().st_size
        
        return FileResponse(
            path=str(output_path),
            filename=safe_filename,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename={safe_filename}",
                "Content-Length": str(file_size),
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Download error for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

@api_router.get("/preview/{project_id}")
async def get_video_preview(project_id: str):
    """Get video preview frames"""
    try:
        # Get input file path
        input_path = None
        for file_path in UPLOAD_DIR.glob(f"{project_id}_*"):
            input_path = file_path
            break
        
        if not input_path:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Cannot open video")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Extract 5 preview frames
        frame_positions = [int(total_frames * i / 5) for i in range(5)]
        preview_frames = []
        
        for pos in frame_positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                # Resize for preview
                frame = cv2.resize(frame, (320, 240))
                _, buffer = cv2.imencode('.jpg', frame)
                frame_b64 = base64.b64encode(buffer).decode('utf-8')
                preview_frames.append(f"data:image/jpeg;base64,{frame_b64}")
        
        cap.release()
        
        return {"preview_frames": preview_frames}
        
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logging.error(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/analyze/{project_id}")
async def analyze_video_intelligence(project_id: str):
    """AI-powered video analysis with intelligent effect recommendations"""
    try:
        # Get input file path
        input_path = None
        for file_path in UPLOAD_DIR.glob(f"{project_id}_*"):
            input_path = file_path
            break
        
        if not input_path:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Perform intelligent analysis
        analysis = SmartVideoAnalyzer.analyze_video_content(input_path)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        return {
            "project_id": project_id,
            "intelligent_analysis": analysis["analysis"],
            "ai_recommendations": analysis["recommendations"],
            "message": "AI analysis completed - smart recommendations generated!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.post("/batch-compare/{project_id}")
async def create_effect_comparison(project_id: str):
    """Create a side-by-side comparison of different artistic effects"""
    try:
        # Get input file path
        input_path = None
        for file_path in UPLOAD_DIR.glob(f"{project_id}_*"):
            input_path = file_path
            break
        
        if not input_path:
            raise HTTPException(status_code=404, detail="Video file not found")
        
        output_filename = f"{project_id}_comparison_grid.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        # Create comparison grid
        success = BatchVideoProcessor.create_comparison_grid(
            [input_path], output_path, 
            effects=['original', 'pencil', 'cartoon', 'oil_painting']
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create comparison grid")
        
        # Update project in database
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"comparison_grid_path": str(output_path)}}
        )
        
        return {
            "project_id": project_id,
            "comparison_path": str(output_path),
            "message": "Comparison grid created successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Comparison creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison creation failed: {str(e)}")

@api_router.get("/download-comparison/{project_id}")
async def download_comparison_grid(project_id: str):
    """Download the comparison grid video"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        comparison_path = project_doc.get("comparison_grid_path")
        if not comparison_path:
            raise HTTPException(status_code=404, detail="Comparison grid not found")
        
        file_path = Path(comparison_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Comparison grid file not found")
        
        return FileResponse(
            path=str(file_path),
            filename=f"comparison_grid_{project_id}.mp4",
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=comparison_grid_{project_id}.mp4"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Comparison download error: {e}")
        raise HTTPException(status_code=500, detail="Comparison download failed")

@api_router.get("/preview-video/{project_id}")
async def get_video_preview_stream(project_id: str):
    """Stream the preview video for in-browser viewing"""
    try:
        project_doc = await db.video_projects.find_one({"id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = VideoProject(**project_doc)
        
        if project.status != "completed":
            raise HTTPException(status_code=400, detail=f"Video not ready. Status: {project.status}")
        
        preview_path = project.preview_path
        if not preview_path or not Path(preview_path).exists():
            # Try to create preview from output if it doesn't exist
            if project.output_path and Path(project.output_path).exists():
                preview_filename = f"{project_id}_preview.mp4"
                preview_path = PREVIEW_DIR / preview_filename
                
                success = await create_preview_video(project.output_path, str(preview_path))
                if success:
                    # Update database with preview path
                    await db.video_projects.update_one(
                        {"id": project_id},
                        {"$set": {"preview_path": str(preview_path)}}
                    )
                else:
                    raise HTTPException(status_code=404, detail="Preview creation failed")
            else:
                raise HTTPException(status_code=404, detail="Preview not available")
        
        return FileResponse(
            path=str(preview_path),
            filename=f"preview_{project_id}.mp4",
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"inline; filename=preview_{project_id}.mp4",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Preview streaming error: {e}")
        raise HTTPException(status_code=500, detail="Preview streaming failed")

@api_router.get("/gallery")
async def get_gallery():
    """Get all processed videos in the gallery with thumbnails"""
    try:
        # Get all completed projects with thumbnails
        projects = await db.video_projects.find(
            {"status": "completed"},
            sort=[("created_at", -1)]
        ).limit(50).to_list(length=None)
        
        gallery_items = []
        for project_doc in projects:
            project = VideoProject(**project_doc)
            
            # Ensure thumbnail exists
            if not project.thumbnail and project.output_path:
                thumbnail = await generate_video_thumbnail(project.output_path)
                if thumbnail:
                    await db.video_projects.update_one(
                        {"id": project.id},
                        {"$set": {"thumbnail": thumbnail}}
                    )
                    project.thumbnail = thumbnail
            
            gallery_items.append({
                "id": project.id,
                "filename": project.filename,
                "art_style": project.art_style,
                "duration": project.duration,
                "thumbnail": project.thumbnail,
                "created_at": project.created_at.isoformat(),
                "has_preview": bool(project.preview_path and Path(project.preview_path).exists()) if project.preview_path else False
            })
        
        return {
            "gallery": gallery_items,
            "total_count": len(gallery_items),
            "message": "Gallery loaded successfully"
        }
        
    except Exception as e:
        logging.error(f"Gallery error: {e}")
        raise HTTPException(status_code=500, detail="Gallery loading failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Comparison download error: {e}")
        raise HTTPException(status_code=500, detail="Comparison download failed")
        
    except HTTPException:
        # Re-raise HTTP exceptions with their original status codes
        raise
    except Exception as e:
        logging.error(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()