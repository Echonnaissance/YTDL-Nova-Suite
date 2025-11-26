import { useState } from 'react';
import downloadService from '../../services/downloadService';
import useDownloadStore from '../../store/slices/downloadStore';
import './PlaylistPreview.css';

export default function PlaylistPreview({ playlistInfo, downloadType, quality, format, embedThumbnail, onClose }) {
  const { addDownload } = useDownloadStore();
  const [selectedVideos, setSelectedVideos] = useState(
    playlistInfo?.videos?.map((_, index) => index) || []
  );
  const [downloading, setDownloading] = useState(false);

  const toggleVideo = (index) => {
    setSelectedVideos(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const toggleAll = () => {
    if (selectedVideos.length === playlistInfo.videos.length) {
      setSelectedVideos([]);
    } else {
      setSelectedVideos(playlistInfo.videos.map((_, index) => index));
    }
  };

  const handleDownload = async () => {
    if (selectedVideos.length === 0) {
      alert('Please select at least one video');
      return;
    }

    setDownloading(true);

    try {
      const requests = selectedVideos.map(index => ({
        url: playlistInfo.videos[index].url,
        download_type: downloadType,
        quality,
        format,
        embed_thumbnail: downloadType === 'audio' ? embedThumbnail : false
      }));

      const downloads = await downloadService.createBatchDownloads(requests);
      downloads.forEach(download => addDownload(download));

      alert(`${downloads.length} downloads started!`);
      onClose();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start downloads');
    } finally {
      setDownloading(false);
    }
  };

  if (!playlistInfo) return null;

  return (
    <div className="playlist-preview-overlay" onClick={onClose}>
      <div className="playlist-preview-modal" onClick={(e) => e.stopPropagation()}>
        <div className="playlist-preview-header">
          <h2>Playlist Preview</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="playlist-info">
          <h3>{playlistInfo.title}</h3>
          <p>{playlistInfo.video_count} videos</p>
        </div>

        <div className="playlist-controls">
          <button
            className="btn btn-secondary"
            onClick={toggleAll}
            disabled={downloading}
          >
            {selectedVideos.length === playlistInfo.videos.length ? 'Deselect All' : 'Select All'}
          </button>
          <span className="selected-count">
            {selectedVideos.length} selected
          </span>
        </div>

        <div className="playlist-videos">
          {playlistInfo.videos.map((video, index) => (
            <div
              key={video.id}
              className={`playlist-video ${selectedVideos.includes(index) ? 'selected' : ''}`}
              onClick={() => toggleVideo(index)}
            >
              <input
                type="checkbox"
                checked={selectedVideos.includes(index)}
                onChange={() => toggleVideo(index)}
                onClick={(e) => e.stopPropagation()}
              />
              {video.thumbnail_url && (
                <img src={video.thumbnail_url} alt={video.title} className="video-thumbnail" />
              )}
              <div className="video-info">
                <h4>{video.title}</h4>
                {video.duration && (
                  <span className="video-duration">
                    {Math.floor(video.duration / 60)}:{String(video.duration % 60).padStart(2, '0')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="playlist-preview-footer">
          <button
            className="btn btn-primary"
            onClick={handleDownload}
            disabled={downloading || selectedVideos.length === 0}
            style={{ width: '100%' }}
          >
            {downloading ? (
              <>
                <span className="spinner"></span>
                Starting Downloads...
              </>
            ) : (
              `Download ${selectedVideos.length} Selected as ${downloadType === 'audio' ? 'Audio' : 'Video'}`
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
