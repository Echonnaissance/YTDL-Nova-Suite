import { useEffect, useState } from "react";
import downloadService from "../services/downloadService";
import "./DownloadedPage.css";

export default function DownloadedPage() {
  const [downloads, setDownloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDownloads();
  }, []);

  const fetchDownloads = async () => {
    try {
      const data = await downloadService.getAllDownloads({
        status: "completed",
        limit: 200,
      });
      setDownloads(data || []);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to load downloads");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>Loading downloaded media…</p>;
  if (error) return <p>{error}</p>;

  return (
    <div className="downloaded-page">
      <h2>Downloaded Media</h2>
      {downloads.length === 0 && <p>No completed downloads yet.</p>}
      <div className="downloaded-list">
        {downloads.map((d) => (
          <div className="downloaded-item" key={d.id}>
            <h3 className="downloaded-title">
              {d.title || d.file_name || "Untitled"}
            </h3>
            {d.thumbnail_url && (
              <img
                src={d.thumbnail_url}
                alt={d.title}
                className="downloaded-thumb"
              />
            )}
            <div className="player-wrap">
              {d.media_url ? (
                <video
                  controls
                  preload="metadata"
                  src={d.media_url}
                  className="downloaded-video"
                />
              ) : d.file_path ? (
                <video
                  controls
                  preload="metadata"
                  src={`/api/downloads/${d.id}/file`}
                  className="downloaded-video"
                />
              ) : (
                <p>File not available</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
