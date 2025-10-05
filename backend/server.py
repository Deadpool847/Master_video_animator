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

for dir_path in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
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
    art_style: Optional[str] = None  # pencil, cartoon
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    output_path: Optional[str] = None
    processing_params: Dict[str, Any] = Field(default_factory=dict)

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
        """Fallback method to combine chunks using OpenCV when FFmpeg fails"""
        try:
            if not temp_outputs:
                raise Exception("No chunks to combine")
            
            # Get properties from first chunk
            first_cap = cv2.VideoCapture(str(temp_outputs[0]))
            fps = first_cap.get(cv2.CAP_PROP_FPS)
            width = int(first_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(first_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            first_cap.release()
            
            # Create output writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            if not out.isOpened():
                # Try with different codec
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(str(output_path).replace('.mp4', '.avi'), fourcc, fps, (width, height))
            
            # Combine all chunks
            for chunk_path in temp_outputs:
                cap = cv2.VideoCapture(str(chunk_path))
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    out.write(frame)
                cap.release()
            
            out.release()
            cv2.destroyAllWindows()
            
            logging.info("Successfully combined chunks using OpenCV fallback")
            
        except Exception as e:
            logging.error(f"OpenCV chunk combination failed: {e}")
            # Last resort: just copy the largest chunk
            if temp_outputs:
                largest_chunk = max(temp_outputs, key=lambda p: p.stat().st_size)
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
            
            # Use H.264 codec for better compatibility and compression
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            
            # Remove existing output file to avoid FFmpeg prompts
            if output_path.exists():
                output_path.unlink()
            
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            if not out.isOpened():
                # Fallback to mp4v codec
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
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
        except:
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
        
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video format")
        
        # Check file size (max 2GB for safety)
        content = await file.read()
        if len(content) > 2 * 1024 * 1024 * 1024:  # 2GB
            raise HTTPException(status_code=413, detail="File too large (max 2GB)")
        
        if len(content) < 1000:  # Minimum viable video size
            raise HTTPException(status_code=400, detail="File too small or corrupted")
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        project_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{project_id}_{file.filename}"
        
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
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
        
    except Exception as e:
        logging.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/process")
async def process_video(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Start video processing with artistic effects"""
    try:
        # Get project from database
        project_doc = await db.video_projects.find_one({"id": request.project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = VideoProject(**project_doc)
        
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
        
    except Exception as e:
        logging.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_background(project_id: str, art_style: str, intensity: float, crop_params: Optional[Dict], trim_params: Optional[Dict], resize_params: Optional[Dict]):
    """Background task for video processing with bulletproof error handling"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
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
        
        # Open video for processing
        cap = cv2.VideoCapture(str(input_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Apply trim parameters
        start_frame = 0
        end_frame = total_frames
        
        if trim_params:
            start_frame = int(trim_params.get('start_time', 0) * fps)
            end_frame = int(trim_params.get('end_time', total_frames / fps) * fps)
        
        cap.release()
        
        # Optimized chunking strategy
        total_frames_to_process = end_frame - start_frame
        
        # Use smaller chunks for better progress tracking and memory management
        chunk_size = min(300, max(50, total_frames_to_process // 8))  # Smaller, adaptive chunks
        
        temp_outputs = []
        
        # Process chunks with better error handling
        chunk_number = 0
        for i in range(start_frame, end_frame, chunk_size):
            chunk_end = min(i + chunk_size, end_frame)
            chunk_output = TEMP_DIR / f"{project_id}_chunk_{chunk_number:03d}.mp4"
            
            processing_status[project_id] = {
                'status': 'processing',
                'progress': (i - start_frame) / total_frames_to_process * 90,
                'message': f'Processing chunk {chunk_number + 1} - {art_style} effect'
            }
            
            success = await VideoProcessor.process_video_chunk(
                input_path, chunk_output, i, chunk_end, art_style, intensity, crop_params, resize_params, project_id
            )
            
            if success and chunk_output.exists():
                temp_outputs.append(chunk_output)
                chunk_number += 1
            else:
                # Clean up any partial files
                for temp_file in temp_outputs:
                    temp_file.unlink(missing_ok=True)
                raise Exception(f"Chunk processing failed at frame {i}")
        
        # Combine chunks with optimized FFmpeg command
        processing_status[project_id] = {
            'status': 'processing',
            'progress': 95,
            'message': 'Finalizing video...'
        }
        
        # Remove existing output file
        if output_path.exists():
            output_path.unlink()
        
        if len(temp_outputs) > 1:
            # Create file list for FFmpeg concat
            concat_file = TEMP_DIR / f"{project_id}_concat.txt"
            with open(concat_file, 'w') as f:
                for temp_output in temp_outputs:
                    f.write(f"file '{temp_output.resolve()}'\n")
            
            # Use optimized FFmpeg command with full path and robust error handling
            ffmpeg_path = '/usr/bin/ffmpeg'
            cmd = [
                ffmpeg_path, '-y',  # Overwrite output files without asking
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c:v', 'libx264',  # Use H.264 codec
                '-preset', 'fast',   # Faster encoding
                '-crf', '23',        # Good quality/size balance
                '-movflags', '+faststart',  # Optimize for web streaming
                str(output_path)
            ]
            
            import subprocess
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
                
                if result.returncode != 0:
                    logging.error(f"FFmpeg concatenation failed: {result.stderr}")
                    # Fallback 1: Try simpler FFmpeg command
                    simple_cmd = [ffmpeg_path, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'copy', str(output_path)]
                    simple_result = subprocess.run(simple_cmd, capture_output=True, text=True, timeout=180)
                    
                    if simple_result.returncode != 0:
                        logging.error(f"Simple FFmpeg also failed: {simple_result.stderr}")
                        # Fallback 2: Use OpenCV to combine chunks
                        await VideoProcessor.combine_chunks_opencv(temp_outputs, output_path)
                
            except subprocess.TimeoutExpired:
                logging.error("FFmpeg timeout - using fallback method")
                await VideoProcessor.combine_chunks_opencv(temp_outputs, output_path)
            except Exception as e:
                logging.error(f"FFmpeg subprocess error: {e}")
                await VideoProcessor.combine_chunks_opencv(temp_outputs, output_path)
            
            # Cleanup temp files
            for temp_output in temp_outputs:
                temp_output.unlink(missing_ok=True)
            concat_file.unlink(missing_ok=True)
        else:
            # Single chunk, just copy it
            if temp_outputs:
                shutil.copy2(str(temp_outputs[0]), str(output_path))
                temp_outputs[0].unlink(missing_ok=True)
        
        # Update project status
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "completed", "output_path": str(output_path), "progress": 100}}
        )
        
            # Verify output file was created successfully
            if not output_path.exists() or output_path.stat().st_size < 1000:
                raise Exception("Output file not created or too small")
            
            processing_status[project_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Processing completed successfully!',
                'timestamp': time.time()
            }
            
            return  # Success - exit retry loop
            
        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            logging.error(f"Background processing error (attempt {retry_count}/{max_retries}): {error_msg}")
            
            if retry_count < max_retries:
                # Wait before retry with exponential backoff
                wait_time = 2 ** retry_count
                processing_status[project_id] = {
                    'status': 'retrying',
                    'progress': 0,
                    'message': f'Error occurred, retrying in {wait_time}s... (attempt {retry_count}/{max_retries})',
                    'timestamp': time.time()
                }
                await asyncio.sleep(wait_time)
            else:
                # Final failure after all retries
                processing_status[project_id] = {
                    'status': 'failed',
                    'progress': 0,
                    'message': f'Processing failed after {max_retries} attempts: {error_msg}',
                    'timestamp': time.time()
                }
                
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"status": "failed", "error_message": error_msg}}
                )

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
        
        # Create a safe filename
        safe_filename = f"{project.filename.split('.')[0]}_{project.art_style or 'processed'}.mp4"
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ".-_")
        
        return FileResponse(
            path=str(output_path),
            filename=safe_filename,
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
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
        
    except Exception as e:
        logging.error(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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