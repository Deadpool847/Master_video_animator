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
  const [gallery, setGallery] = useState([]);
  const [showPreview, setShowPreview] = useState(null);
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
    loadGallery();
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
      // Show loading state
      const downloadButton = document.querySelector(`[data-download="${projectId}"]`);
      if (downloadButton) {
        downloadButton.textContent = 'Downloading...';
        downloadButton.disabled = true;
      }

      const response = await axios.get(`${API}/download/${projectId}`, {
        responseType: 'blob',
        timeout: 60000, // 1 minute timeout
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.lengthComputable) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            if (downloadButton) {
              downloadButton.textContent = `Downloading... ${percentCompleted}%`;
            }
          }
        }
      });
      
      // Create blob URL
      const blob = new Blob([response.data], { type: 'video/mp4' });
      const url = window.URL.createObjectURL(blob);
      
      // Extract filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'video_masterpiece.mp4';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      // Create download link
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      link.style.display = 'none';
      document.body.appendChild(link);
      
      // Trigger download
      link.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
      
      // Reset button
      if (downloadButton) {
        downloadButton.textContent = '⬇️';
        downloadButton.disabled = false;
      }
      
      // Show success message
      alert('🎉 Masterpiece downloaded successfully!');
      
    } catch (error) {
      console.error('Download error:', error);
      
      // Reset button
      const downloadButton = document.querySelector(`[data-download="${projectId}"]`);
      if (downloadButton) {
        downloadButton.textContent = '⬇️';
        downloadButton.disabled = false;
      }
      
      // Show detailed error message
      if (error.response?.status === 404) {
        alert('❌ Video file not found. It may have been deleted or moved.');
      } else if (error.code === 'ECONNABORTED') {
        alert('❌ Download timeout. Please try again or check your connection.');
      } else {
        alert(`❌ Download failed: ${error.response?.data?.detail || error.message || 'Unknown error'}`);
      }
    }
  };

  const loadGallery = async () => {
    try {
      const response = await axios.get(`${API}/gallery`);
      setGallery(response.data.gallery || []);
    } catch (error) {
      console.error('Gallery loading error:', error);
    }
  };

  const openPreview = (projectId) => {
    setShowPreview(projectId);
  };

  const closePreview = () => {
    setShowPreview(null);
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
                <h2 className="text-2xl font-bold mb-4">📹 Preview & Intelligence</h2>
                <div className="grid grid-cols-2 gap-2 mb-4">
                  {previewFrames.slice(0, 4).map((frame, index) => (
                    <img
                      key={index}
                      src={frame}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-20 object-cover rounded border border-gray-600"
                    />
                  ))}
                </div>
                
                {/* AI Recommendations */}
                {aiAnalysis && aiAnalysis.ai_recommendations && (
                  <div className="mb-4 p-3 bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-lg border border-blue-400/30">
                    <h3 className="text-sm font-bold text-blue-300 mb-2">🤖 AI Recommendations</h3>
                    {aiAnalysis.ai_recommendations.slice(0, 2).map((rec, index) => (
                      <div key={index} className="text-xs mb-2">
                        <button
                          onClick={() => setArtStyle(rec.effect)}
                          className="text-cyan-300 hover:text-cyan-200 font-medium"
                        >
                          {rec.effect.replace('_', ' ').toUpperCase()}
                        </button>
                        <p className="text-gray-400">{rec.reason}</p>
                        <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                          <div 
                            className="bg-cyan-400 h-1 rounded-full" 
                            style={{ width: `${rec.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Comparison Grid Button */}
                {currentProject && (
                  <button
                    onClick={() => createComparisonGrid(currentProject.id)}
                    disabled={isProcessing}
                    className="w-full mb-4 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg transition-all text-sm"
                  >
                    {isProcessing ? 'Creating...' : '🎯 Create Effect Comparison Grid'}
                  </button>
                )}
                
                {currentProject && (
                  <div className="text-sm text-gray-400">
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

            {/* Masterpiece Gallery */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h2 className="text-2xl font-bold mb-4">🎬 Masterpiece Gallery</h2>
              
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {projects.filter(p => p.status === 'completed').map((project) => (
                  <div key={project.id} className="p-4 bg-gradient-to-r from-gray-800/70 to-gray-700/70 rounded-xl border border-gray-600 hover:border-cyan-400/50 transition-all">
                    {/* Thumbnail and Info */}
                    <div className="flex items-center gap-3 mb-3">
                      {project.thumbnail && (
                        <img 
                          src={project.thumbnail} 
                          alt="Thumbnail"
                          className="w-16 h-12 object-cover rounded border border-gray-500"
                        />
                      )}
                      <div className="flex-1">
                        <p className="font-medium text-sm text-white truncate">{project.filename}</p>
                        <p className="text-xs text-gray-300">
                          <span className="inline-block px-2 py-1 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full border border-cyan-400/30 mr-2">
                            {project.art_style?.replace('_', ' ').toUpperCase() || 'PROCESSED'}
                          </span>
                          {project.duration?.toFixed(1)}s • {new Date(project.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openPreview(project.id)}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white text-xs font-bold py-2 px-3 rounded-lg transition-all flex items-center justify-center gap-1"
                      >
                        <span>👁️</span> Preview
                      </button>
                      
                      <button
                        onClick={() => downloadVideo(project.id)}
                        data-download={project.id}
                        className="bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white text-xs font-bold py-2 px-4 rounded-lg transition-all"
                      >
                        ⬇️
                      </button>
                    </div>
                  </div>
                ))}
                
                {projects.filter(p => p.status === 'completed').length === 0 && (
                  <div className="text-center py-8">
                    <div className="text-6xl mb-4">🎨</div>
                    <p className="text-gray-400">No masterpieces yet</p>
                    <p className="text-gray-500 text-sm">Upload a video to create your first artistic masterpiece!</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Processing Queue */}
            {projects.filter(p => p.status !== 'completed').length > 0 && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h2 className="text-xl font-bold mb-4">⚡ Processing Queue</h2>
                
                <div className="space-y-2">
                  {projects.filter(p => p.status !== 'completed').map((project) => (
                    <div key={project.id} className="flex items-center justify-between p-2 bg-gray-700/30 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium text-xs truncate">{project.filename}</p>
                        <p className="text-xs text-gray-400">
                          {project.art_style || 'No style'} • {project.status}
                        </p>
                      </div>
                      
                      <span className={`w-2 h-2 rounded-full ${
                        project.status === 'processing' ? 'bg-blue-400 animate-pulse' :
                        project.status === 'failed' ? 'bg-red-400' : 'bg-gray-400'
                      }`} />
                    </div>
                  ))}
                </div>
              </div>
            )}
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