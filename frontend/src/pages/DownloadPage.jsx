import DownloadForm from '../components/features/DownloadForm';
import './DownloadPage.css';

export default function DownloadPage() {
  return (
    <div className="download-page">
      <div className="page-header">
        <h1>New Download</h1>
        <p className="page-subtitle">Download videos and audio from YouTube, Twitter/X, Instagram, TikTok, and more</p>
      </div>
      <DownloadForm />
    </div>
  );
}
