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

class VideoProcessor:
    @staticmethod
    def apply_pencil_sketch(frame, intensity=0.5):
        """Apply pencil sketch effect to a frame"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Create inverted grayscale
        inv_gray = 255 - gray
        
        # Apply Gaussian blur
        blur_intensity = int(21 + (intensity * 20))  # Range: 21-41
        blurred = cv2.GaussianBlur(inv_gray, (blur_intensity, blur_intensity), 0)
        
        # Create pencil sketch
        sketch = cv2.divide(gray, 255 - blurred, scale=256)
        
        # Apply adaptive thresholding for more pencil-like appearance
        threshold = cv2.adaptiveThreshold(sketch, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 10)
        
        # Convert back to BGR for consistency
        sketch_bgr = cv2.cvtColor(threshold, cv2.COLOR_GRAY2BGR)
        
        # Blend with original if intensity is not full
        if intensity < 1.0:
            sketch_bgr = cv2.addWeighted(frame, (1 - intensity), sketch_bgr, intensity, 0)
        
        return sketch_bgr
    
    @staticmethod
    def apply_cartoon_effect(frame, intensity=0.5):
        """Apply cartoon effect to a frame"""
        # Reduce noise
        bilateral = cv2.bilateralFilter(frame, 9, 200, 200)
        
        # Create edge mask
        gray = cv2.cvtColor(bilateral, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 10)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Color quantization
        k = int(8 + intensity * 4)  # Number of colors (8-12)
        data = bilateral.reshape((-1, 3))
        data = np.float32(data)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        centers = np.uint8(centers)
        quantized_data = centers[labels.flatten()]
        quantized = quantized_data.reshape(bilateral.shape)
        
        # Combine quantized image with edges
        cartoon = cv2.bitwise_and(quantized, edges)
        
        # Blend with original if intensity is not full
        if intensity < 1.0:
            cartoon = cv2.addWeighted(frame, (1 - intensity), cartoon, intensity, 0)
        
        return cartoon
    
    @staticmethod
    async def process_video_chunk(input_path, output_path, start_frame, end_frame, art_style, intensity, crop_params, resize_params, project_id):
        """Process a chunk of video frames"""
        try:
            cap = cv2.VideoCapture(str(input_path))
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Set up video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # Determine output dimensions
            if resize_params:
                width, height = resize_params['width'], resize_params['height']
            else:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if crop_params:
                width = crop_params['width']
                height = crop_params['height']
            
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            # Jump to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_count = start_frame
            processed_frames = 0
            
            while frame_count < end_frame and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Apply crop if specified
                if crop_params:
                    x, y, w, h = crop_params['x'], crop_params['y'], crop_params['width'], crop_params['height']
                    frame = frame[y:y+h, x:x+w]
                
                # Apply resize if specified
                if resize_params:
                    frame = cv2.resize(frame, (resize_params['width'], resize_params['height']))
                
                # Apply artistic effect
                if art_style == 'pencil':
                    frame = VideoProcessor.apply_pencil_sketch(frame, intensity)
                elif art_style == 'cartoon':
                    frame = VideoProcessor.apply_cartoon_effect(frame, intensity)
                
                out.write(frame)
                processed_frames += 1
                frame_count += 1
                
                # Update progress every 10 frames
                if processed_frames % 10 == 0:
                    progress = (frame_count - start_frame) / (end_frame - start_frame) * 100
                    processing_status[project_id] = {
                        'status': 'processing',
                        'progress': progress,
                        'message': f'Processing frames {frame_count}/{end_frame}'
                    }
            
            cap.release()
            out.release()
            
            return True
            
        except Exception as e:
            logging.error(f"Error processing chunk: {e}")
            processing_status[project_id] = {
                'status': 'failed',
                'progress': 0,
                'message': f'Error: {str(e)}'
            }
            return False

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Video Art Converter API - Ready to create masterpieces!"}

@api_router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file with chunked processing support"""
    try:
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
        
        # Initialize processing status
        processing_status[request.project_id] = {
            'status': 'starting',
            'progress': 0,
            'message': 'Initializing processing...'
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
    """Background task for video processing"""
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
        
        # Process video in chunks for large files
        chunk_size = min(1000, (end_frame - start_frame) // 4)  # Adaptive chunk size
        if chunk_size < 100:
            chunk_size = end_frame - start_frame
        
        temp_outputs = []
        
        # Process chunks
        for i in range(start_frame, end_frame, chunk_size):
            chunk_end = min(i + chunk_size, end_frame)
            chunk_output = TEMP_DIR / f"{project_id}_chunk_{i}.mp4"
            
            success = await VideoProcessor.process_video_chunk(
                input_path, chunk_output, i, chunk_end, art_style, intensity, crop_params, resize_params, project_id
            )
            
            if success:
                temp_outputs.append(chunk_output)
            else:
                raise Exception("Chunk processing failed")
        
        # Combine chunks if multiple
        if len(temp_outputs) > 1:
            processing_status[project_id] = {
                'status': 'processing',
                'progress': 90,
                'message': 'Combining video chunks...'
            }
            
            # Create file list for FFmpeg concat
            concat_file = TEMP_DIR / f"{project_id}_concat.txt"
            with open(concat_file, 'w') as f:
                for temp_output in temp_outputs:
                    f.write(f"file '{temp_output}'\n")
            
            # Use FFmpeg to concatenate
            cmd = f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_path}"
            os.system(cmd)
            
            # Cleanup temp files
            for temp_output in temp_outputs:
                temp_output.unlink(missing_ok=True)
            concat_file.unlink(missing_ok=True)
        else:
            # Single chunk, just move it
            shutil.move(str(temp_outputs[0]), str(output_path))
        
        # Update project status
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "completed", "output_path": str(output_path), "progress": 100}}
        )
        
        processing_status[project_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Processing completed successfully!'
        }
        
    except Exception as e:
        logging.error(f"Background processing error: {e}")
        processing_status[project_id] = {
            'status': 'failed',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }
        
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "failed"}}
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
    project_doc = await db.video_projects.find_one({"id": project_id})
    if not project_doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = VideoProject(**project_doc)
    
    if project.status != "completed" or not project.output_path:
        raise HTTPException(status_code=400, detail="Video not ready for download")
    
    output_path = Path(project.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=output_path,
        filename=f"{project.filename.split('.')[0]}_{project.art_style}.mp4",
        media_type="video/mp4"
    )

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