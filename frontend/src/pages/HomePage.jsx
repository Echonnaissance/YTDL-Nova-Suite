import { Link } from "react-router-dom";
import "./HomePage.css";

export default function HomePage() {
  return (
    <div className="home-page">
      {/* Hero Section - Full Width */}
      <section className="hero" aria-labelledby="hero-title">
        <h1 id="hero-title">
          Download Media from <span className="gradient-text">Anywhere</span>
        </h1>
        <p className="subtitle">
          YouTube, Twitter/X, Instagram, TikTok, and 1000+ sites.
        </p>
        <div className="hero-actions">
          <Link to="/download" className="btn btn-primary btn-large">
            ⬇️ Start Download
          </Link>
          <Link to="/history" className="btn btn-secondary btn-large">
            📋 History
          </Link>
        </div>
      </section>

      {/* Two Column Layout - Symmetrical */}
      <div className="home-columns">
        {/* Left Column - Features */}
        <section className="features-section" aria-labelledby="features-title">
          <h2 id="features-title" className="section-title">
            Features
          </h2>
          <div className="features-grid">
            <div className="feature-card">
              <span className="feature-icon">🎵</span>
              <h3>Audio</h3>
              <p>MP3, M4A, Opus</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🎬</span>
              <h3>Video</h3>
              <p>MP4, WebM, MKV</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">⚡</span>
              <h3>Smart</h3>
              <p>Auto-fetch URLs</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🖼️</span>
              <h3>Cover Art</h3>
              <p>Embed thumbnails</p>
            </div>
          </div>
        </section>

        {/* Right Column - Platforms & Tips */}
        <div className="info-column">
          <section className="platforms" aria-labelledby="platforms-title">
            <h2 id="platforms-title" className="section-title">
              Supported Sites
            </h2>
            <div className="platform-badges">
              <span className="platform-badge">YouTube</span>
              <span className="platform-badge">Twitter/X</span>
              <span className="platform-badge">Instagram</span>
              <span className="platform-badge">TikTok</span>
              <span className="platform-badge">Vimeo</span>
              <span className="platform-badge">Reddit</span>
              <span className="platform-badge">Twitch</span>
              <span className="platform-badge">+1000 more</span>
            </div>
          </section>

          <section className="tips" aria-labelledby="tips-title">
            <h2 id="tips-title" className="section-title">
              Quick Tips
            </h2>
            <ul className="tips-list">
              <li>
                <kbd>Ctrl</kbd>+<kbd>V</kbd> to auto-paste URL
              </li>
              <li>
                <kbd>Ctrl</kbd>+<kbd>Enter</kbd> to download
              </li>
              <li>Paste multiple URLs for batch</li>
              <li>Up to 4K quality supported</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
