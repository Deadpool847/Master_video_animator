import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoArtConverter = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [artStyle, setArtStyle] = useState('pencil');
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [showAdvancedEffects, setShowAdvancedEffects] = useState(false);
  const [intensity, setIntensity] = useState(0.5);
  const [previewFrames, setPreviewFrames] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [videoParams, setVideoParams] = useState({
    crop: { enabled: false, x: 0, y: 0, width: 100, height: 100 },
    trim: { enabled: false, start: 0, end: 100 },
    resize: { enabled: false, width: 1280, height: 720 }
  });

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);

  // Load projects on component mount
  useEffect(() => {
    fetchProjects();
  }, []);

  // Poll processing status
  useEffect(() => {
    let interval;
    if (currentProject && isProcessing) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/status/${currentProject.id}`);
          setProcessingStatus(response.data);
          
          if (response.data.status === 'completed' || response.data.status === 'failed') {
            setIsProcessing(false);
            fetchProjects(); // Refresh projects list
          }
        } catch (error) {
          console.error('Status polling error:', error);
        }
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentProject, isProcessing]);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Fetch projects error:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
      setCurrentProject(null);
      setPreviewFrames([]);
    } else {
      alert('Please select a valid video file');
    }
  };

  const uploadVideo = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        },
      });

      const projectId = response.data.project_id;
      setCurrentProject({ id: projectId, ...response.data.metadata });
      
      // Load preview frames
      await loadPreviewFrames(projectId);
      
      setSelectedFile(null);
      setUploadProgress(0);
      fetchProjects();
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setIsUploading(false);
    }
  };

  const loadPreviewFrames = async (projectId) => {
    try {
      const response = await axios.get(`${API}/preview/${projectId}`);
      setPreviewFrames(response.data.preview_frames);
      
      // Also load AI analysis
      loadAiAnalysis(projectId);
    } catch (error) {
      console.error('Preview error:', error);
    }
  };

  const loadAiAnalysis = async (projectId) => {
    try {
      const response = await axios.get(`${API}/analyze/${projectId}`);
      setAiAnalysis(response.data);
    } catch (error) {
      console.error('AI Analysis error:', error);
    }
  };

  const createComparisonGrid = async (projectId) => {
    try {
      setIsProcessing(true);
      const response = await axios.post(`${API}/batch-compare/${projectId}`);
      
      if (response.status === 200) {
        alert('Comparison grid created! Check your downloads.');
        // Download automatically
        window.open(`${API}/download-comparison/${projectId}`, '_blank');
      }
    } catch (error) {
      console.error('Comparison creation error:', error);
      alert('Failed to create comparison grid');
    } finally {
      setIsProcessing(false);
    }
  };

  const processVideo = async () => {
    if (!currentProject) return;

    setIsProcessing(true);
    setProcessingStatus({ status: 'starting', progress: 0, message: 'Starting...' });

    try {
      const processingRequest = {
        project_id: currentProject.id,
        art_style: artStyle,
        intensity: intensity,
        crop_params: videoParams.crop.enabled ? {
          x: Math.floor(videoParams.crop.x * currentProject.width / 100),
          y: Math.floor(videoParams.crop.y * currentProject.height / 100),
          width: Math.floor(videoParams.crop.width * currentProject.width / 100),
          height: Math.floor(videoParams.crop.height * currentProject.height / 100)
        } : null,
        trim_params: videoParams.trim.enabled ? {
          start_time: videoParams.trim.start * currentProject.duration / 100,
          end_time: videoParams.trim.end * currentProject.duration / 100
        } : null,
        resize_params: videoParams.resize.enabled ? {
          width: videoParams.resize.width,
          height: videoParams.resize.height
        } : null
      };

      await axios.post(`${API}/process`, processingRequest);
    } catch (error) {
      console.error('Processing error:', error);
      alert('Processing failed: ' + (error.response?.data?.detail || 'Unknown error'));
      setIsProcessing(false);
    }
  };

  const downloadVideo = async (projectId) => {
    try {
      const response = await axios.get(`${API}/download/${projectId}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `processed_video.mp4`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      alert('Download failed');
    }
  };

  const updateVideoParam = (category, param, value) => {
    setVideoParams(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [param]: value
      }
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-4">
            🎨 Video Art Masterpiece
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Transform any video into stunning pencil sketches or cartoon animations with our 
            revolutionary offline processing technology. No external dependencies, pure masterpiece creation!
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Upload & Controls Panel */}
          <div className="lg:col-span-2 space-y-8">
            {/* Upload Section */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                📁 Upload Video
              </h2>
              
              <div className="space-y-4">
                <div 
                  className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-cyan-400 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  
                  {selectedFile ? (
                    <div>
                      <div className="text-green-400 text-4xl mb-2">✅</div>
                      <p className="text-lg">{selectedFile.name}</p>
                      <p className="text-sm text-gray-400">
                        Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  ) : (
                    <div>
                      <div className="text-6xl mb-4">🎬</div>
                      <p className="text-lg mb-2">Click to select video file</p>
                      <p className="text-sm text-gray-400">
                        Supports MP4, AVI, MOV and other formats. Large files welcome!
                      </p>
                    </div>
                  )}
                </div>

                {selectedFile && (
                  <button
                    onClick={uploadVideo}
                    disabled={isUploading}
                    className="w-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-all transform hover:scale-105"
                  >
                    {isUploading ? `Uploading... ${uploadProgress}%` : 'Upload Video 🚀'}
                  </button>
                )}
              </div>
            </div>

            {/* Art Style Selection */}
            {currentProject && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  🎨 Artistic Style
                </h2>
                
                <div className="grid md:grid-cols-2 gap-4 mb-6">
                  <button
                    onClick={() => setArtStyle('pencil')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      artStyle === 'pencil'
                        ? 'border-cyan-400 bg-cyan-400/20'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-4xl mb-2">✏️</div>
                    <h3 className="font-bold">Pencil Sketch</h3>
                    <p className="text-sm text-gray-400">Hand-drawn artistic style</p>
                  </button>
                  
                  <button
                    onClick={() => setArtStyle('cartoon')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      artStyle === 'cartoon'
                        ? 'border-purple-400 bg-purple-400/20'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-4xl mb-2">🎭</div>
                    <h3 className="font-bold">Cartoon Animation</h3>
                    <p className="text-sm text-gray-400">Bold animated style</p>
                  </button>
                </div>
                
                {/* Advanced Effects Toggle */}
                <div className="mb-4">
                  <button
                    onClick={() => setShowAdvancedEffects(!showAdvancedEffects)}
                    className="text-cyan-400 hover:text-cyan-300 flex items-center gap-2"
                  >
                    <span>🎨 Advanced Masterpiece Effects</span>
                    <span>{showAdvancedEffects ? '🔽' : '▶️'}</span>
                  </button>
                </div>
                
                {/* Advanced Effects Grid */}
                {showAdvancedEffects && (
                  <div className="grid md:grid-cols-2 gap-3 mb-6 p-4 bg-gray-900/50 rounded-lg border border-cyan-400/30">
                    <button
                      onClick={() => setArtStyle('oil_painting')}
                      className={`p-3 rounded-lg border-2 transition-all text-sm ${
                        artStyle === 'oil_painting'
                          ? 'border-orange-400 bg-orange-400/20'
                          : 'border-gray-600 hover:border-gray-500'
                      }`}
                    >
                      <div className="text-2xl mb-1">🎨</div>
                      <h4 className="font-bold">Oil Painting</h4>
                      <p className="text-xs text-gray-400">Classic masterpiece</p>
                    </button>
                    
                    <button
                      onClick={() => setArtStyle('watercolor')}
                      className={`p-3 rounded-lg border-2 transition-all text-sm ${
                        artStyle === 'watercolor'
                          ? 'border-blue-400 bg-blue-400/20'
                          : 'border-gray-600 hover:border-gray-500'
                      }`}
                    >
                      <div className="text-2xl mb-1">🌊</div>
                      <h4 className="font-bold">Watercolor</h4>
                      <p className="text-xs text-gray-400">Flowing artistic style</p>
                    </button>
                    
                    <button
                      onClick={() => setArtStyle('anime')}
                      className={`p-3 rounded-lg border-2 transition-all text-sm ${
                        artStyle === 'anime'
                          ? 'border-pink-400 bg-pink-400/20'
                          : 'border-gray-600 hover:border-gray-500'
                      }`}
                    >
                      <div className="text-2xl mb-1">⚡</div>
                      <h4 className="font-bold">Anime Style</h4>
                      <p className="text-xs text-gray-400">Japanese animation</p>
                    </button>
                    
                    <button
                      onClick={() => setArtStyle('vintage_film')}
                      className={`p-3 rounded-lg border-2 transition-all text-sm ${
                        artStyle === 'vintage_film'
                          ? 'border-yellow-400 bg-yellow-400/20'
                          : 'border-gray-600 hover:border-gray-500'
                      }`}
                    >
                      <div className="text-2xl mb-1">📽️</div>
                      <h4 className="font-bold">Vintage Film</h4>
                      <p className="text-xs text-gray-400">Classic cinema look</p>
                    </button>
                  </div>
                )}

                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">
                    Effect Intensity: {(intensity * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={intensity}
                    onChange={(e) => setIntensity(parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              </div>
            )}

            {/* Video Editing Controls */}
            {currentProject && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  ✂️ Video Editing
                </h2>

                {/* Crop Controls */}
                <div className="mb-6">
                  <label className="flex items-center gap-2 mb-3">
                    <input
                      type="checkbox"
                      checked={videoParams.crop.enabled}
                      onChange={(e) => updateVideoParam('crop', 'enabled', e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="font-medium">Enable Crop</span>
                  </label>
                  
                  {videoParams.crop.enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm mb-1">X Position (%)</label>
                        <input
                          type="range"
                          min="0"
                          max="50"
                          value={videoParams.crop.x}
                          onChange={(e) => updateVideoParam('crop', 'x', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <span className="text-xs text-gray-400">{videoParams.crop.x}%</span>
                      </div>
                      <div>
                        <label className="block text-sm mb-1">Y Position (%)</label>
                        <input
                          type="range"
                          min="0"
                          max="50"
                          value={videoParams.crop.y}
                          onChange={(e) => updateVideoParam('crop', 'y', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <span className="text-xs text-gray-400">{videoParams.crop.y}%</span>
                      </div>
                      <div>
                        <label className="block text-sm mb-1">Width (%)</label>
                        <input
                          type="range"
                          min="10"
                          max="100"
                          value={videoParams.crop.width}
                          onChange={(e) => updateVideoParam('crop', 'width', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <span className="text-xs text-gray-400">{videoParams.crop.width}%</span>
                      </div>
                      <div>
                        <label className="block text-sm mb-1">Height (%)</label>
                        <input
                          type="range"
                          min="10"
                          max="100"
                          value={videoParams.crop.height}
                          onChange={(e) => updateVideoParam('crop', 'height', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <span className="text-xs text-gray-400">{videoParams.crop.height}%</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Trim Controls */}
                <div className="mb-6">
                  <label className="flex items-center gap-2 mb-3">
                    <input
                      type="checkbox"
                      checked={videoParams.trim.enabled}
                      onChange={(e) => updateVideoParam('trim', 'enabled', e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="font-medium">Enable Trim</span>
                  </label>
                  
                  {videoParams.trim.enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm mb-1">Start (%)</label>
                        <input
                          type="range"
                          min="0"
                          max="90"
                          value={videoParams.trim.start}
                          onChange={(e) => updateVideoParam('trim', 'start', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <span className="text-xs text-gray-400">
                          {(videoParams.trim.start * currentProject.duration / 100).toFixed(1)}s
                        </span>
                      </div>
                      <div>
                        <label className="block text-sm mb-1">End (%)</label>
                        <input
                          type="range"
                          min="10"
                          max="100"
                          value={videoParams.trim.end}
                          onChange={(e) => updateVideoParam('trim', 'end', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <span className="text-xs text-gray-400">
                          {(videoParams.trim.end * currentProject.duration / 100).toFixed(1)}s
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Resize Controls */}
                <div className="mb-6">
                  <label className="flex items-center gap-2 mb-3">
                    <input
                      type="checkbox"
                      checked={videoParams.resize.enabled}
                      onChange={(e) => updateVideoParam('resize', 'enabled', e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span className="font-medium">Enable Resize</span>
                  </label>
                  
                  {videoParams.resize.enabled && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm mb-1">Width</label>
                        <select
                          value={videoParams.resize.width}
                          onChange={(e) => updateVideoParam('resize', 'width', parseInt(e.target.value))}
                          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                        >
                          <option value="640">640p</option>
                          <option value="854">854p</option>
                          <option value="1280">1280p (HD)</option>
                          <option value="1920">1920p (FHD)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm mb-1">Height</label>
                        <select
                          value={videoParams.resize.height}
                          onChange={(e) => updateVideoParam('resize', 'height', parseInt(e.target.value))}
                          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                        >
                          <option value="480">480p</option>
                          <option value="720">720p (HD)</option>
                          <option value="1080">1080p (FHD)</option>
                          <option value="1440">1440p (2K)</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={processVideo}
                  disabled={isProcessing}
                  className="w-full bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-all transform hover:scale-105"
                >
                  {isProcessing ? 'Processing... 🎭' : 'Create Masterpiece! 🚀'}
                </button>
              </div>
            )}
          </div>

          {/* Preview & Status Panel */}
          <div className="space-y-8">
            {/* Video Preview */}
            {previewFrames.length > 0 && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h2 className="text-2xl font-bold mb-4">📹 Preview</h2>
                <div className="grid grid-cols-2 gap-2">
                  {previewFrames.slice(0, 4).map((frame, index) => (
                    <img
                      key={index}
                      src={frame}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-20 object-cover rounded border border-gray-600"
                    />
                  ))}
                </div>
                
                {currentProject && (
                  <div className="mt-4 text-sm text-gray-400">
                    <p>Duration: {currentProject.duration?.toFixed(1)}s</p>
                    <p>Dimensions: {currentProject.width} × {currentProject.height}</p>
                    <p>FPS: {currentProject.fps?.toFixed(1)}</p>
                  </div>
                )}
              </div>
            )}

            {/* Processing Status */}
            {processingStatus && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h2 className="text-2xl font-bold mb-4">⚡ Processing Status</h2>
                
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Status:</span>
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      processingStatus.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      processingStatus.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {processingStatus.status}
                    </span>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">Progress:</span>
                      <span>{processingStatus.progress?.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-cyan-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${processingStatus.progress || 0}%` }}
                      />
                    </div>
                  </div>
                  
                  {processingStatus.message && (
                    <p className="text-sm text-gray-400">{processingStatus.message}</p>
                  )}
                </div>
              </div>
            )}

            {/* Recent Projects */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h2 className="text-2xl font-bold mb-4">📚 Recent Projects</h2>
              
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {projects.map((project) => (
                  <div key={project.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-sm truncate">{project.filename}</p>
                      <p className="text-xs text-gray-400">
                        {project.art_style ? `${project.art_style} style` : 'No style'} • 
                        {project.duration?.toFixed(1)}s
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        project.status === 'completed' ? 'bg-green-400' :
                        project.status === 'processing' ? 'bg-blue-400' :
                        project.status === 'failed' ? 'bg-red-400' : 'bg-gray-400'
                      }`} />
                      
                      {project.status === 'completed' && (
                        <button
                          onClick={() => downloadVideo(project.id)}
                          className="text-cyan-400 hover:text-cyan-300 text-sm"
                        >
                          ⬇️
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                
                {projects.length === 0 && (
                  <p className="text-gray-400 text-center py-4">No projects yet</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return <VideoArtConverter />;
}

export default App;