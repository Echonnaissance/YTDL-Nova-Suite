import { useState, useEffect, useRef } from "react";
import downloadService from "../../services/downloadService";
import useDownloadStore from "../../store/slices/downloadStore";
import useSettingsStore from "../../store/slices/settingsStore";
import PlaylistPreview from "./PlaylistPreview";
import "./DownloadForm.css";

export default function DownloadForm() {
  const { addDownload } = useDownloadStore();
  const settings = useSettingsStore();

  const [url, setUrl] = useState("");
  const [batchUrls, setBatchUrls] = useState("");
  const [batchMode, setBatchMode] = useState(false);
  const [downloadType, setDownloadType] = useState(
    settings.defaultDownloadType || "video"
  );
  const [quality, setQuality] = useState(settings.defaultQuality || "best");
  const [videoFormat, setVideoFormat] = useState(
    settings.defaultVideoFormat || "mp4"
  );
  const [audioFormat, setAudioFormat] = useState(
    settings.defaultAudioFormat || "m4a"
  );
  const [embedThumbnail, setEmbedThumbnail] = useState(
    typeof settings.embedThumbnail === "boolean"
      ? settings.embedThumbnail
      : true
  );

  const [loading, setLoading] = useState(false);
  const [videoInfo, setVideoInfo] = useState(null);
  const [fetchingInfo, setFetchingInfo] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showPlaylistPreview, setShowPlaylistPreview] = useState(false);
  const [playlistInfo, setPlaylistInfo] = useState(null);

  // Progress tracking state
  const [activeDownload, setActiveDownload] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadSpeed, setDownloadSpeed] = useState(null);
  const [downloadEta, setDownloadEta] = useState(null);
  const pollIntervalRef = useRef(null);

  // Recent URLs (session storage)
  const [recentUrls, setRecentUrls] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem("recentUrls") || "[]");
    } catch {
      return [];
    }
  });
  const [showRecent, setShowRecent] = useState(false);
  const urlInputRef = useRef(null);

  // Poll for download progress
  useEffect(() => {
    if (activeDownload && activeDownload.id) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const updated = await downloadService.getDownload(activeDownload.id);
          setDownloadProgress(updated.progress || 0);
          setDownloadSpeed(updated.speed);
          setDownloadEta(updated.eta);

          // Check if download is complete or failed
          if (updated.status === "completed") {
            clearInterval(pollIntervalRef.current);
            setActiveDownload(null);
            setLoading(false);
            setDownloadProgress(100);
            setSuccess(`Download completed: ${updated.title || "Unknown"}`);
            setTimeout(() => {
              setDownloadProgress(0);
              setDownloadSpeed(null);
              setDownloadEta(null);
            }, 2000);
          } else if (updated.status === "failed") {
            clearInterval(pollIntervalRef.current);
            setActiveDownload(null);
            setLoading(false);
            setDownloadProgress(0);
            setError(
              `Download failed: ${updated.error_message || "Unknown error"}`
            );
          }
        } catch (err) {
          console.error("Failed to poll download status:", err);
        }
      }, 1000); // Poll every second
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [activeDownload]);

  const validateUrl = (urlString) => {
    // Accept any http/https URL - yt-dlp supports 1000+ sites
    return /^https?:\/\/.+/.test(urlString);
  };

  // Add URL to recent list
  const addToRecent = (newUrl) => {
    if (!newUrl || !validateUrl(newUrl)) return;
    const updated = [newUrl, ...recentUrls.filter((u) => u !== newUrl)].slice(
      0,
      5
    );
    setRecentUrls(updated);
    sessionStorage.setItem("recentUrls", JSON.stringify(updated));
  };

  // Handle paste - auto-fetch info
  const handlePaste = async (e) => {
    const pastedText = e.clipboardData?.getData("text")?.trim();
    if (pastedText && validateUrl(pastedText)) {
      // Let the paste happen, then fetch info
      setTimeout(async () => {
        if (!fetchingInfo && !loading) {
          setError(null);
          setFetchingInfo(true);
          setVideoInfo(null);
          try {
            const info = await downloadService.getVideoInfo(pastedText);
            setVideoInfo(info);
          } catch (err) {
            // Silently fail - user can manually fetch if needed
            console.log("Auto-fetch failed:", err);
          } finally {
            setFetchingInfo(false);
          }
        }
      }, 100);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e) => {
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!loading && (batchMode ? batchUrls.trim() : url)) {
        handleSubmit(e);
      }
    }
  };

  // Clear URL input
  const handleClear = () => {
    setUrl("");
    setVideoInfo(null);
    setError(null);
    urlInputRef.current?.focus();
  };

  const handleFetchInfo = async () => {
    if (!url) {
      setError("Please enter a URL");
      return;
    }

    if (!validateUrl(url)) {
      setError(
        "Please enter a valid URL (must start with http:// or https://)"
      );
      return;
    }

    setError(null);
    setFetchingInfo(true);
    setVideoInfo(null);

    try {
      const info = await downloadService.getVideoInfo(url);
      setVideoInfo(info);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to fetch video information"
      );
    } finally {
      setFetchingInfo(false);
    }
  };

  const handlePreviewPlaylist = async () => {
    const currentUrl = batchMode ? batchUrls.split("\n")[0]?.trim() : url;

    if (!currentUrl) {
      setError("Please enter a playlist URL");
      return;
    }

    if (!currentUrl.includes("list=")) {
      setError("This doesn't appear to be a playlist URL");
      return;
    }

    setError(null);
    setFetchingInfo(true);

    try {
      const info = await downloadService.getPlaylistInfo(currentUrl);
      setPlaylistInfo(info);
      setShowPlaylistPreview(true);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to fetch playlist information"
      );
    } finally {
      setFetchingInfo(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (batchMode) {
      // Handle batch download
      const urls = batchUrls.split("\n").filter((u) => u.trim());

      if (urls.length === 0) {
        setError("Please enter at least one URL");
        return;
      }

      for (const u of urls) {
        if (!validateUrl(u.trim())) {
          setError(
            `Invalid URL: ${u}. Please provide a valid URL from a supported platform.`
          );
          return;
        }
      }

      setError(null);
      setSuccess(null);
      setLoading(true);

      try {
        const requests = urls.map((u) => ({
          url: u.trim(),
          download_type: downloadType,
          quality,
          format: downloadType === "audio" ? audioFormat : videoFormat,
          embed_thumbnail: downloadType === "audio" ? embedThumbnail : false,
        }));

        const downloads = await downloadService.createBatchDownloads(requests);
        downloads.forEach((download) => addDownload(download));

        setSuccess(`${downloads.length} downloads started`);
        setBatchUrls("");
      } catch (err) {
        setError(
          err.response?.data?.detail || "Failed to create batch downloads"
        );
      } finally {
        setLoading(false);
      }
    } else {
      // Handle single download
      if (!url) {
        setError("Please enter a URL");
        return;
      }

      if (!validateUrl(url)) {
        setError("Please enter a valid URL from a supported platform");
        return;
      }

      setError(null);
      setSuccess(null);
      setLoading(true);
      setDownloadProgress(0);
      setDownloadSpeed(null);
      setDownloadEta(null);

      try {
        // Always send all required fields with safe defaults
        const request = {
          url: url || "",
          download_type: downloadType || "video",
          quality: quality || "best",
          format:
            (downloadType === "audio" ? audioFormat : videoFormat) ||
            (downloadType === "audio" ? "m4a" : "mp4"),
          embed_thumbnail:
            downloadType === "audio"
              ? typeof embedThumbnail === "boolean"
                ? embedThumbnail
                : true
              : false,
        };

        const download = await downloadService.createDownload(request);
        addDownload(download);

        // Add to recent URLs
        addToRecent(url);

        // Start tracking this download's progress
        setActiveDownload(download);
        setSuccess(`Download started: ${download.title || "Unknown"}`);
        setUrl("");
        setVideoInfo(null);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to create download");
        setLoading(false);
      }
      // Don't set loading to false here - let the progress polling handle it
    }
  };

  return (
    <div className="download-form-container">
      <form onSubmit={handleSubmit} className="download-form">
        {/* URL Input Row */}
        <div className="url-row">
          {batchMode ? (
            <textarea
              className="form-input url-input"
              placeholder="Paste URLs here, one per line... (Ctrl+Enter to download)"
              value={batchUrls}
              onChange={(e) => setBatchUrls(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={3}
            />
          ) : (
            <div className="url-input-wrapper">
              <input
                ref={urlInputRef}
                type="text"
                className="form-input url-input"
                placeholder="Paste any video URL here... (Ctrl+Enter to download)"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setShowRecent(false);
                }}
                onPaste={handlePaste}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowRecent(recentUrls.length > 0 && !url)}
                onBlur={() => setTimeout(() => setShowRecent(false), 150)}
                disabled={loading}
              />
              {url && !loading && (
                <button
                  type="button"
                  className="btn-clear"
                  onClick={handleClear}
                  title="Clear"
                >
                  ✕
                </button>
              )}
              {showRecent && recentUrls.length > 0 && (
                <div className="recent-urls-dropdown">
                  <div className="recent-urls-header">Recent URLs</div>
                  {recentUrls.map((recentUrl, i) => (
                    <button
                      key={i}
                      type="button"
                      className="recent-url-item"
                      onMouseDown={() => {
                        setUrl(recentUrl);
                        setShowRecent(false);
                      }}
                    >
                      {recentUrl.length > 50
                        ? recentUrl.substring(0, 50) + "..."
                        : recentUrl}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {!batchMode && (
            <button
              type="button"
              className="btn btn-secondary btn-icon"
              onClick={handleFetchInfo}
              disabled={fetchingInfo || loading || !url}
              title="Get video info"
            >
              {fetchingInfo ? <span className="spinner-small"></span> : "ℹ️"}
            </button>
          )}
        </div>

        {/* Options Row - Compact inline */}
        <div className="options-row">
          <div className="option-group type-toggle">
            <button
              type="button"
              className={`toggle-btn ${
                downloadType === "video" ? "active" : ""
              }`}
              onClick={() => setDownloadType("video")}
              disabled={loading}
            >
              🎬 Video
            </button>
            <button
              type="button"
              className={`toggle-btn ${
                downloadType === "audio" ? "active" : ""
              }`}
              onClick={() => setDownloadType("audio")}
              disabled={loading}
            >
              🎵 Audio
            </button>
          </div>

          <div className="option-group">
            <label className="option-label">Quality</label>
            <select
              className="form-select compact"
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
              disabled={loading}
            >
              <option value="best">Best</option>
              <option value="1080p">1080p</option>
              <option value="720p">720p</option>
              <option value="480p">480p</option>
            </select>
          </div>

          <div className="option-group">
            <label className="option-label">Format</label>
            <select
              className="form-select compact"
              value={downloadType === "audio" ? audioFormat : videoFormat}
              onChange={(e) =>
                downloadType === "audio"
                  ? setAudioFormat(e.target.value)
                  : setVideoFormat(e.target.value)
              }
              disabled={loading}
            >
              {downloadType === "video" ? (
                <>
                  <option value="mp4">MP4</option>
                  <option value="webm">WebM</option>
                  <option value="mkv">MKV</option>
                  <option value="mov">MOV</option>
                  <option value="avi">AVI</option>
                  <option value="wmv">WMV</option>
                  <option value="ogv">OGG</option>
                </>
              ) : (
                <>
                  <option value="m4a">M4A</option>
                  <option value="mp3">MP3</option>
                  <option value="opus">Opus</option>
                </>
              )}
            </select>
          </div>

          {downloadType === "audio" && (
            <label
              className="option-group checkbox-inline"
              title="Embed album art into audio file"
            >
              <input
                type="checkbox"
                checked={embedThumbnail}
                onChange={(e) => setEmbedThumbnail(e.target.checked)}
                disabled={loading}
              />
              <span>🖼️ Art</span>
            </label>
          )}

          <label
            className="option-group checkbox-inline batch-toggle"
            title="Download multiple URLs at once"
          >
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
            <span>📋 Batch</span>
          </label>
        </div>

        {/* Video Preview - Compact */}
        {videoInfo && (
          <div className="preview-row">
            {videoInfo.thumbnail_url && (
              <img
                src={videoInfo.thumbnail_url}
                alt=""
                className="preview-thumb"
              />
            )}
            <div className="preview-info">
              <span className="preview-title">{videoInfo.title}</span>
              <span className="preview-meta">
                {videoInfo.uploader && `${videoInfo.uploader}`}
                {videoInfo.duration && (
                  <>
                    {" "}
                    • {Math.floor(videoInfo.duration / 60)}:
                    {String(Math.floor(videoInfo.duration % 60)).padStart(
                      2,
                      "0"
                    )}
                  </>
                )}
              </span>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {(activeDownload || downloadProgress > 0) && (
          <div className="progress-row">
            <div className="progress-bar-wrapper">
              <div
                className="progress-bar-fill"
                style={{ width: `${downloadProgress}%` }}
              />
            </div>
            <div className="progress-stats">
              <span>{downloadProgress.toFixed(0)}%</span>
              {downloadSpeed && <span>{downloadSpeed}</span>}
              {downloadEta && <span>ETA: {downloadEta}</span>}
            </div>
          </div>
        )}

        {/* Messages */}
        {error && (
          <div className="message error">
            {typeof error === "string" ? error : error.detail || "Error"}
          </div>
        )}
        {success && <div className="message success">{success}</div>}

        {/* Download Button */}
        <button
          type="submit"
          className="btn btn-primary btn-download"
          disabled={loading || (batchMode ? !batchUrls.trim() : !url)}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              {activeDownload ? "Downloading..." : "Starting..."}
            </>
          ) : (
            `⬇️ Download ${downloadType === "audio" ? "Audio" : "Video"}`
          )}
        </button>
      </form>

      {/* Playlist Preview Modal */}
      {showPlaylistPreview && playlistInfo && (
        <PlaylistPreview
          playlistInfo={playlistInfo}
          downloadType={downloadType}
          quality={quality}
          format={downloadType === "audio" ? audioFormat : videoFormat}
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
