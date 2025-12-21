import { useEffect, useState, useRef } from "react";
import downloadService from "../services/downloadService";
import "./DownloadedPage.css";

export default function DownloadedPage() {
  const [downloads, setDownloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [autoplay, setAutoplay] = useState(true);
  const videoRef = useRef(null);

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
      if (!selected && data && data.length > 0) setSelected(data[0]);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to load downloads");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Auto-play selected when changed
    if (selected && autoplay && videoRef.current) {
      // small delay to ensure src is set
      const t = setTimeout(() => {
        try {
          videoRef.current.play().catch(() => {});
        } catch (e) {}
      }, 150);
      return () => clearTimeout(t);
    }
  }, [selected, autoplay]);

  const findIndex = (item) => downloads.findIndex((d) => d.id === item.id);

  const handleNext = () => {
    if (!selected) return;
    const idx = findIndex(selected);
    if (idx === -1) return;
    const next = downloads[idx + 1] || downloads[0];
    setSelected(next);
  };

  const handlePrev = () => {
    if (!selected) return;
    const idx = findIndex(selected);
    if (idx === -1) return;
    const prev = downloads[idx - 1] || downloads[downloads.length - 1];
    setSelected(prev);
  };

  const handleToggleAutoplay = () => setAutoplay((v) => !v);

  const handleDelete = async (item) => {
    if (!confirm(`Delete "${item.title || item.file_name}"?`)) return;
    try {
      await downloadService.deleteDownload(item.id);
      // remove locally
      const remaining = downloads.filter((d) => d.id !== item.id);
      setDownloads(remaining);
      if (selected && selected.id === item.id) {
        setSelected(remaining[0] || null);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to delete download");
    }
  };

  const handleReveal = (item) => {
    if (item.file_path) {
      navigator.clipboard?.writeText(item.file_path).then(
        () => {
          alert("File path copied to clipboard");
        },
        () => {
          alert(item.file_path);
        }
      );
    } else {
      alert("File path not available");
    }
  };

  if (loading) return <p>Loading downloaded media…</p>;
  if (error) return <p>{error}</p>;

  return (
    <div className="downloaded-page">
      <h2>Downloaded Media</h2>
      {downloads.length === 0 && <p>No completed downloads yet.</p>}

      <div className="downloaded-container">
        <div className="player-column">
          {selected ? (
            <div className="player-card">
              <div className="player-controls">
                <button className="btn" onClick={handlePrev} title="Previous">
                  ◀◀
                </button>
                <button className="btn" onClick={handleNext} title="Next">
                  ▶▶
                </button>
                <label className="autoplay-toggle">
                  <input
                    type="checkbox"
                    checked={autoplay}
                    onChange={handleToggleAutoplay}
                  />{" "}
                  Autoplay
                </label>
                <div style={{ flex: 1 }} />
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(selected)}
                >
                  Delete
                </button>
                <button className="btn" onClick={() => handleReveal(selected)}>
                  Reveal
                </button>
              </div>
              <h3 className="player-title">
                {selected.title || selected.file_name}
              </h3>
              <video
                ref={videoRef}
                controls
                preload="metadata"
                src={selected.media_url || `/api/downloads/${selected.id}/file`}
                className="main-player"
              />
              {selected.file_size && (
                <div className="file-meta">
                  {Math.round(selected.file_size / 1024 / 1024)} MB
                </div>
              )}
              {selected.file_path && (
                <div className="file-path">{selected.file_path}</div>
              )}
            </div>
          ) : (
            <p>Select a video on the right to play</p>
          )}
        </div>

        <aside className="list-column" aria-label="Downloaded videos">
          {downloads.map((d) => (
            <div
              key={d.id}
              className={`list-item ${
                selected && selected.id === d.id ? "active" : ""
              }`}
              onClick={() => setSelected(d)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && setSelected(d)}
            >
              <img src={d.thumbnail_url} alt={d.title} className="list-thumb" />
              <div className="list-meta">
                <div className="list-title">{d.title || d.file_name}</div>
                <div className="list-sub">
                  {d.duration ? `${Math.round(d.duration)}s` : ""}
                </div>
              </div>
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
