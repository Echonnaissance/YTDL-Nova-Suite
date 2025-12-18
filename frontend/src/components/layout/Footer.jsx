import { Link } from "react-router-dom";
import "./Footer.css";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer" role="contentinfo">
      <div className="footer-container">
        <div className="footer-main">
          <div className="footer-brand">
            <span className="footer-logo" aria-hidden="true">
              ⬇️
            </span>
            <span>Universal Media Downloader</span>
          </div>
          <p className="footer-description">
            Download videos and audio from YouTube, Twitter/X, Instagram,
            TikTok, and 1000+ sites.
          </p>
        </div>

        <div className="footer-links">
          <div className="footer-section">
            <h4>Quick Links</h4>
            <ul>
              <li>
                <Link to="/download">Download</Link>
              </li>
              <li>
                <Link to="/history">History</Link>
              </li>
              <li>
                <Link to="/settings">Settings</Link>
              </li>
            </ul>
          </div>
          <div className="footer-section">
            <h4>Resources</h4>
            <ul>
              <li>
                <Link to="/api-docs">API Docs</Link>
              </li>
              <li>
                <a
                  href="https://github.com/yt-dlp/yt-dlp"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  yt-dlp
                </a>
              </li>
              <li>
                <a
                  href="https://ffmpeg.org"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  FFmpeg
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© {currentYear} Echonnaissance. For educational purposes.</p>
        <p className="footer-version">v1.1.2</p>
      </div>
    </footer>
  );
}
