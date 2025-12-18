import { useState } from 'react';
import downloadService from '../../services/downloadService';
import useDownloadStore from '../../store/slices/downloadStore';
import useSettingsStore from '../../store/slices/settingsStore';
import PlaylistPreview from './PlaylistPreview';
import './DownloadForm.css';

export default function DownloadForm() {
  const { addDownload } = useDownloadStore();
  const settings = useSettingsStore();

  const [url, setUrl] = useState('');
  const [batchUrls, setBatchUrls] = useState('');
  const [batchMode, setBatchMode] = useState(false);
  const [downloadType, setDownloadType] = useState(settings.defaultDownloadType);
  const [quality, setQuality] = useState(settings.defaultQuality);
  const [videoFormat, setVideoFormat] = useState(settings.defaultVideoFormat);
  const [audioFormat, setAudioFormat] = useState(settings.defaultAudioFormat);
  const [embedThumbnail, setEmbedThumbnail] = useState(settings.embedThumbnail);

  const [loading, setLoading] = useState(false);
  const [videoInfo, setVideoInfo] = useState(null);
  const [fetchingInfo, setFetchingInfo] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showPlaylistPreview, setShowPlaylistPreview] = useState(false);
  const [playlistInfo, setPlaylistInfo] = useState(null);

  const validateUrl = (urlString) => {
    // Support multiple platforms: YouTube, Twitter/X, Instagram, TikTok, etc.
    const urlPattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|x\.com|twitter\.com|instagram\.com|tiktok\.com|vimeo\.com|dailymotion\.com|twitch\.tv|facebook\.com|fb\.watch|reddit\.com|bilibili\.com|nicovideo\.jp)\/.+$/;
    return urlPattern.test(urlString);
  };

  const handleFetchInfo = async () => {
    if (!url) {
      setError('Please enter a URL');
      return;
    }

    if (!validateUrl(url)) {
      setError('Please enter a valid URL from a supported platform (YouTube, Twitter/X, Instagram, TikTok, etc.)');
      return;
    }

    setError(null);
    setFetchingInfo(true);
    setVideoInfo(null);

    try {
      const info = await downloadService.getVideoInfo(url);
      setVideoInfo(info);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch video information');
    } finally {
      setFetchingInfo(false);
    }
  };

  const handlePreviewPlaylist = async () => {
    const currentUrl = batchMode ? batchUrls.split('\n')[0]?.trim() : url;

    if (!currentUrl) {
      setError('Please enter a playlist URL');
      return;
    }

    if (!currentUrl.includes('list=')) {
      setError('This doesn\'t appear to be a playlist URL');
      return;
    }

    setError(null);
    setFetchingInfo(true);

    try {
      const info = await downloadService.getPlaylistInfo(currentUrl);
      setPlaylistInfo(info);
      setShowPlaylistPreview(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch playlist information');
    } finally {
      setFetchingInfo(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (batchMode) {
      // Handle batch download
      const urls = batchUrls.split('\n').filter(u => u.trim());

      if (urls.length === 0) {
        setError('Please enter at least one URL');
        return;
      }

      for (const u of urls) {
        if (!validateUrl(u.trim())) {
          setError(`Invalid URL: ${u}. Please provide a valid URL from a supported platform.`);
          return;
        }
      }

      setError(null);
      setSuccess(null);
      setLoading(true);

      try {
        const requests = urls.map(u => ({
          url: u.trim(),
          download_type: downloadType,
          quality,
          format: downloadType === 'audio' ? audioFormat : videoFormat,
          embed_thumbnail: downloadType === 'audio' ? embedThumbnail : false
        }));

        const downloads = await downloadService.createBatchDownloads(requests);
        downloads.forEach(download => addDownload(download));

        setSuccess(`${downloads.length} downloads started`);
        setBatchUrls('');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to create batch downloads');
      } finally {
        setLoading(false);
      }
    } else {
      // Handle single download
      if (!url) {
        setError('Please enter a URL');
        return;
      }

      if (!validateUrl(url)) {
        setError('Please enter a valid YouTube URL');
        return;
      }

      setError(null);
      setSuccess(null);
      setLoading(true);

      try {
        const request = {
          url,
          download_type: downloadType,
          quality,
          format: downloadType === 'audio' ? audioFormat : videoFormat,
          embed_thumbnail: downloadType === 'audio' ? embedThumbnail : false
        };

        const download = await downloadService.createDownload(request);
        addDownload(download);

        setSuccess(`Download started: ${download.title || 'Unknown'}`);
        setUrl('');
        setVideoInfo(null);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to create download');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="download-form-container">
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Create Download</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Batch Mode Toggle */}
          <div className="form-group">
            <label className="checkbox-group">
              <input
                type="checkbox"
                checked={batchMode}
                onChange={(e) => {
                  setBatchMode(e.target.checked);
                  setVideoInfo(null);
                  setError(null);
                }}
                disabled={loading}
              />
              <span>Batch Mode (multiple URLs)</span>
            </label>
          </div>

          {/* URL Input */}
          <div className="form-group">
            <label className="form-label">
              {batchMode ? 'YouTube URLs (one per line)' : 'YouTube URL'}
            </label>
            {batchMode ? (
              <textarea
                className="form-input"
                style={{ minHeight: '120px', fontFamily: 'inherit' }}
                placeholder="https://www.youtube.com/watch?v=...&#10;https://www.youtube.com/watch?v=...&#10;https://www.youtube.com/watch?v=..."
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
                disabled={loading}
              />
            ) : (
              <div className="url-input-group">
                <input
                  type="text"
                  className="form-input"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleFetchInfo}
                  disabled={fetchingInfo || loading || !url}
                >
                  {fetchingInfo ? (
                    <>
                      <span className="spinner"></span>
                      Fetching...
                    </>
                  ) : (
                    'Get Info'
                  )}
                </button>
              </div>
            )}
            <p className="form-help">
              {batchMode
                ? 'Enter multiple YouTube video or playlist URLs, one per line'
                : 'Enter a YouTube video or playlist URL to download'}
            </p>
          </div>

          {/* Preview Playlist Button */}
          {!batchMode && (
            <div className="form-group">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handlePreviewPlaylist}
                disabled={fetchingInfo || loading || !url}
                style={{ width: '100%' }}
              >
                {fetchingInfo ? (
                  <>
                    <span className="spinner"></span>
                    Loading Playlist...
                  </>
                ) : (
                  'Preview Playlist'
                )}
              </button>
            </div>
          )}

          {/* Video Info Preview */}
          {videoInfo && (
            <div className="video-info-preview">
              <div className="video-info-thumbnail">
                {videoInfo.thumbnail_url && (
                  <img src={videoInfo.thumbnail_url} alt={videoInfo.title} />
                )}
              </div>
              <div className="video-info-details">
                <h4>{videoInfo.title}</h4>
                <p className="video-info-meta">
                  {videoInfo.uploader && <span>By {videoInfo.uploader}</span>}
                  {videoInfo.duration && (
                    <span>{Math.floor(videoInfo.duration / 60)}:{String(videoInfo.duration % 60).padStart(2, '0')}</span>
                  )}
                </p>
              </div>
            </div>
          )}

          {/* Download Type */}
          <div className="form-group">
            <label className="form-label">Download Type</label>
            <div className="download-type-selector">
              <button
                type="button"
                className={`type-btn ${downloadType === 'video' ? 'active' : ''}`}
                onClick={() => setDownloadType('video')}
                disabled={loading}
              >
                <span className="type-icon">🎬</span>
                Video
              </button>
              <button
                type="button"
                className={`type-btn ${downloadType === 'audio' ? 'active' : ''}`}
                onClick={() => setDownloadType('audio')}
                disabled={loading}
              >
                <span className="type-icon">🎵</span>
                Audio
              </button>
            </div>
          </div>

          {/* Video Options */}
          {downloadType === 'video' && (
            <>
              <div className="form-group">
                <label className="form-label">Quality</label>
                <select
                  className="form-select"
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                  disabled={loading}
                >
                  <option value="best">Best Quality</option>
                  <option value="1080p">1080p</option>
                  <option value="720p">720p</option>
                  <option value="480p">480p</option>
                  <option value="360p">360p</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Format</label>
                <select
                  className="form-select"
                  value={videoFormat}
                  onChange={(e) => setVideoFormat(e.target.value)}
                  disabled={loading}
                >
                  <option value="mp4">MP4</option>
                  <option value="webm">WebM</option>
                  <option value="mkv">MKV</option>
                </select>
              </div>
            </>
          )}

          {/* Audio Options */}
          {downloadType === 'audio' && (
            <>
              <div className="form-group">
                <label className="form-label">Format</label>
                <select
                  className="form-select"
                  value={audioFormat}
                  onChange={(e) => setAudioFormat(e.target.value)}
                  disabled={loading}
                >
                  <option value="m4a">M4A</option>
                  <option value="mp3">MP3</option>
                  <option value="opus">Opus</option>
                  <option value="vorbis">Vorbis</option>
                </select>
              </div>

              <div className="form-group">
                <div className="checkbox-group">
                  <input
                    type="checkbox"
                    id="embedThumbnail"
                    checked={embedThumbnail}
                    onChange={(e) => setEmbedThumbnail(e.target.checked)}
                    disabled={loading}
                  />
                  <label htmlFor="embedThumbnail">Embed thumbnail</label>
                </div>
              </div>
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="alert alert-success">
              {success}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className="btn btn-primary btn-large"
            disabled={loading || (batchMode ? !batchUrls.trim() : !url)}
            style={{ width: '100%' }}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Starting Download...
              </>
            ) : (
              `Download ${downloadType === 'audio' ? 'Audio' : 'Video'}`
            )}
          </button>
        </form>
      </div>

      {/* Playlist Preview Modal */}
      {showPlaylistPreview && playlistInfo && (
        <PlaylistPreview
          playlistInfo={playlistInfo}
          downloadType={downloadType}
          quality={quality}
          format={downloadType === 'audio' ? audioFormat : videoFormat}
          embedThumbnail={embedThumbnail}
          onClose={() => {
            setShowPlaylistPreview(false);
            setPlaylistInfo(null);
          }}
        />
      )}
    </div>
  );
}
