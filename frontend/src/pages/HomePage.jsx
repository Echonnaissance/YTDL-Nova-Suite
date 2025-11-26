import { Link } from 'react-router-dom';
import './HomePage.css';

export default function HomePage() {
  return (
    <div className="home-page">
      <div className="hero">
        <h1>YouTube Downloader</h1>
        <p className="subtitle">Download YouTube videos and audio in high quality</p>
        <div className="hero-actions">
          <Link to="/download" className="btn btn-primary btn-large">
            Start Download
          </Link>
          <Link to="/history" className="btn btn-secondary btn-large">
            View History
          </Link>
        </div>
      </div>

      <div className="features">
        <div className="feature-card">
          <div className="feature-icon">🎵</div>
          <h3>Audio Downloads</h3>
          <p>Extract audio in high quality MP3, M4A, or other formats</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🎬</div>
          <h3>Video Downloads</h3>
          <p>Download videos in various qualities and formats</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">⚡</div>
          <h3>Fast Processing</h3>
          <p>Efficient downloads with real-time progress tracking</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Download Queue</h3>
          <p>Manage multiple downloads with up to 3 concurrent processes</p>
        </div>
      </div>
    </div>
  );
}
