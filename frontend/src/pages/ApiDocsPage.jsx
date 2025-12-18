import "./ApiDocsPage.css";

export default function ApiDocsPage() {
  const baseUrl = "http://localhost:8000/api";

  return (
    <div className="api-docs-page">
      <header className="api-header">
        <h1>📚 API Documentation</h1>
        <p className="api-intro">
          REST API for downloading media from YouTube, Twitter/X, Instagram,
          TikTok, and 1000+ sites.
        </p>
        <div className="api-links">
          <a
            href="http://localhost:8000/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            🔗 Interactive Swagger UI
          </a>
          <a
            href="http://localhost:8000/api/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            📖 ReDoc
          </a>
        </div>
      </header>

      <section className="api-section">
        <h2>Base URL</h2>
        <code className="code-block">{baseUrl}</code>
      </section>

      {/* Downloads Endpoints */}
      <section className="api-section">
        <h2>📥 Downloads</h2>

        {/* POST /downloads */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method post">POST</span>
            <code>/downloads</code>
          </div>
          <p className="endpoint-desc">Create a new download</p>
          <details>
            <summary>Request Body</summary>
            <pre className="code-block">{`{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "download_type": "audio",    // "audio" | "video" | "playlist"
  "quality": "best",           // "best" | "1080p" | "720p" | etc.
  "format": "m4a",             // Audio: m4a, mp3, opus, flac, wav
                               // Video: mp4, webm, mkv
  "embed_thumbnail": true
}`}</pre>
          </details>
          <details>
            <summary>Response (201 Created)</summary>
            <pre className="code-block">{`{
  "id": 1,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "thumbnail_url": "https://i.ytimg.com/vi/...",
  "duration": 212.0,
  "download_type": "audio",
  "format": "m4a",
  "quality": "best",
  "status": "pending",
  "progress": 0.0,
  "created_at": "2024-12-18T10:30:00Z"
}`}</pre>
          </details>
        </div>

        {/* GET /downloads */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method get">GET</span>
            <code>/downloads</code>
          </div>
          <p className="endpoint-desc">
            Get all downloads with optional filtering
          </p>
          <details>
            <summary>Query Parameters</summary>
            <ul className="params-list">
              <li>
                <code>skip</code> - Number of records to skip (default: 0)
              </li>
              <li>
                <code>limit</code> - Max records to return (default: 100, max:
                1000)
              </li>
              <li>
                <code>status</code> - Filter by status: pending, downloading,
                completed, failed, cancelled
              </li>
            </ul>
          </details>
        </div>

        {/* GET /downloads/active */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method get">GET</span>
            <code>/downloads/active</code>
          </div>
          <p className="endpoint-desc">
            Get all currently active downloads (downloading, processing, or
            queued)
          </p>
        </div>

        {/* GET /downloads/stats */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method get">GET</span>
            <code>/downloads/stats</code>
          </div>
          <p className="endpoint-desc">
            Get download statistics (counts by status)
          </p>
        </div>

        {/* GET /downloads/:id */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method get">GET</span>
            <code>/downloads/{"{id}"}</code>
          </div>
          <p className="endpoint-desc">Get a specific download by ID</p>
        </div>

        {/* DELETE /downloads/:id */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method delete">DELETE</span>
            <code>/downloads/{"{id}"}</code>
          </div>
          <p className="endpoint-desc">Delete a download record</p>
        </div>

        {/* POST /downloads/:id/cancel */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method post">POST</span>
            <code>/downloads/{"{id}"}/cancel</code>
          </div>
          <p className="endpoint-desc">Cancel an active download</p>
        </div>

        {/* POST /downloads/:id/retry */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method post">POST</span>
            <code>/downloads/{"{id}"}/retry</code>
          </div>
          <p className="endpoint-desc">Retry a failed download</p>
        </div>

        {/* POST /downloads/video-info */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method post">POST</span>
            <code>/downloads/video-info</code>
          </div>
          <p className="endpoint-desc">
            Get video metadata without downloading
          </p>
          <details>
            <summary>Request Body</summary>
            <pre className="code-block">{`{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}`}</pre>
          </details>
        </div>

        {/* POST /downloads/playlist-info */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method post">POST</span>
            <code>/downloads/playlist-info</code>
          </div>
          <p className="endpoint-desc">
            Get playlist metadata without downloading
          </p>
        </div>
      </section>

      {/* Settings Endpoints */}
      <section className="api-section">
        <h2>⚙️ Settings</h2>

        {/* GET /settings */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method get">GET</span>
            <code>/settings</code>
          </div>
          <p className="endpoint-desc">Get user settings</p>
          <details>
            <summary>Response</summary>
            <pre className="code-block">{`{
  "id": 1,
  "download_location": "C:/Downloads",
  "default_video_format": "mp4",
  "default_audio_format": "m4a",
  "default_quality": "best",
  "embed_thumbnail": true,
  "concurrent_downloads": 3
}`}</pre>
          </details>
        </div>

        {/* PATCH /settings */}
        <div className="endpoint">
          <div className="endpoint-header">
            <span className="method patch">PATCH</span>
            <code>/settings</code>
          </div>
          <p className="endpoint-desc">Update user settings (partial update)</p>
        </div>
      </section>

      {/* Supported Formats */}
      <section className="api-section">
        <h2>📋 Supported Formats</h2>
        <div className="formats-grid">
          <div className="format-card">
            <h3>🎵 Audio Formats</h3>
            <div className="format-badges">
              <span className="badge">m4a</span>
              <span className="badge">mp3</span>
              <span className="badge">opus</span>
              <span className="badge">vorbis</span>
              <span className="badge">flac</span>
              <span className="badge">wav</span>
              <span className="badge">aac</span>
            </div>
          </div>
          <div className="format-card">
            <h3>🎬 Video Formats</h3>
            <div className="format-badges">
              <span className="badge">mp4</span>
              <span className="badge">webm</span>
              <span className="badge">mkv</span>
              <span className="badge">flv</span>
              <span className="badge">avi</span>
            </div>
          </div>
          <div className="format-card">
            <h3>📺 Quality Options</h3>
            <div className="format-badges">
              <span className="badge">best</span>
              <span className="badge">2160p</span>
              <span className="badge">1440p</span>
              <span className="badge">1080p</span>
              <span className="badge">720p</span>
              <span className="badge">480p</span>
              <span className="badge">360p</span>
            </div>
          </div>
        </div>
      </section>

      {/* Status Codes */}
      <section className="api-section">
        <h2>🚦 Download Status Values</h2>
        <ul className="status-list">
          <li>
            <code className="status pending">pending</code> - Queued, waiting to
            start
          </li>
          <li>
            <code className="status downloading">downloading</code> - Currently
            downloading
          </li>
          <li>
            <code className="status processing">processing</code> -
            Post-processing (converting, embedding)
          </li>
          <li>
            <code className="status completed">completed</code> - Successfully
            completed
          </li>
          <li>
            <code className="status failed">failed</code> - Download failed
          </li>
          <li>
            <code className="status cancelled">cancelled</code> - Cancelled by
            user
          </li>
        </ul>
      </section>

      {/* Error Codes */}
      <section className="api-section">
        <h2>❌ Error Codes</h2>
        <ul className="error-list">
          <li>
            <code>400</code> - Bad Request (invalid URL or parameters)
          </li>
          <li>
            <code>404</code> - Download not found
          </li>
          <li>
            <code>422</code> - Validation error (check request body)
          </li>
          <li>
            <code>429</code> - Rate limit exceeded
          </li>
          <li>
            <code>500</code> - Server error (yt-dlp failure, etc.)
          </li>
        </ul>
      </section>

      {/* Rate Limiting */}
      <section className="api-section">
        <h2>⏱️ Rate Limiting</h2>
        <p>
          Download and info endpoints are rate limited to prevent abuse. If you
          exceed the limit, you'll receive a <code>429</code> response.
        </p>
      </section>
    </div>
  );
}
