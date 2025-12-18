import { Link } from "react-router-dom";
import "./HomePage.css";

export default function HomePage() {
  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-content">
          <h1 id="hero-title">
            Download Media from <span className="gradient-text">Anywhere</span>
          </h1>
          <p className="subtitle">
            YouTube, Twitter/X, Instagram, TikTok, and 1000+ sites. Fast, free,
            and easy to use.
          </p>
          <div className="hero-actions">
            <Link to="/download" className="btn btn-primary btn-large">
              <span aria-hidden="true">⬇️</span> Start Download
            </Link>
            <Link to="/history" className="btn btn-secondary btn-large">
              <span aria-hidden="true">📋</span> View History
            </Link>
          </div>
          <p className="hero-hint">
            <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to download instantly
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="features" aria-labelledby="features-title">
        <h2 id="features-title" className="sr-only">
          Features
        </h2>
        <article className="feature-card">
          <div className="feature-icon" aria-hidden="true">
            🎵
          </div>
          <h3>Audio Downloads</h3>
          <p>
            Extract audio in high quality MP3, M4A, or Opus formats with
            optional cover art
          </p>
        </article>
        <article className="feature-card">
          <div className="feature-icon" aria-hidden="true">
            🎬
          </div>
          <h3>Video Downloads</h3>
          <p>
            Download videos in MP4, WebM, MKV, MOV, AVI and more at up to 4K
            quality
          </p>
        </article>
        <article className="feature-card">
          <div className="feature-icon" aria-hidden="true">
            ⚡
          </div>
          <h3>Smart Features</h3>
          <p>
            Auto-fetch on paste, recent URLs, real-time progress, and keyboard
            shortcuts
          </p>
        </article>
        <article className="feature-card">
          <div className="feature-icon" aria-hidden="true">
            🌐
          </div>
          <h3>1000+ Sites</h3>
          <p>
            YouTube, Twitter/X, Instagram, TikTok, Vimeo, Reddit, and many more
          </p>
        </article>
      </section>

      {/* Supported Platforms */}
      <section className="platforms" aria-labelledby="platforms-title">
        <h2 id="platforms-title">Supported Platforms</h2>
        <div className="platform-badges">
          <span className="platform-badge">YouTube</span>
          <span className="platform-badge">Twitter/X</span>
          <span className="platform-badge">Instagram</span>
          <span className="platform-badge">TikTok</span>
          <span className="platform-badge">Vimeo</span>
          <span className="platform-badge">Reddit</span>
          <span className="platform-badge">Twitch</span>
          <span className="platform-badge">SoundCloud</span>
          <span className="platform-badge">+ 1000 more</span>
        </div>
      </section>
    </div>
  );
}
