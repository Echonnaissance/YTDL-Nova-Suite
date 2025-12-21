import { useEffect, useState, useRef } from "react";
import downloadService from "../services/downloadService";
import { api } from "../services/api";
import "./DownloadedPage.css";

export default function DownloadedPage() {
  const [downloads, setDownloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [autoplay, setAutoplay] = useState(true);
  const videoRef = useRef(null);
  const playerCardRef = useRef(null);
  const shadowCanvasRef = useRef(null);
  const [adaptiveShadow, setAdaptiveShadow] = useState(false);
  const lastToggleRef = useRef(0);
  const controlsRestoreTimerRef = useRef(null);
  const containerRef = useRef(null);
  const listRef = useRef(null);
  const [theater, setTheater] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const thumbCacheRef = useRef(new Map());
  const [localFiles, setLocalFiles] = useState([]);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  const [largePlayer, setLargePlayer] = useState(false);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onPlay = () => setIsPlaying(true);
    const onPause = () => {
      setIsPlaying(false);
      try {
        // If the user manually pauses, disable autoplay to avoid immediate resume
        setAutoplay(false);
        localStorage.setItem("umd.autoplay", "0");
      } catch (err) {}
    };
    const onVolume = () => {
      setVolume(v.volume);
      try {
        localStorage.setItem("umd.volume", String(v.volume));
      } catch (err) {}
    };
    v.addEventListener("play", onPlay);
    v.addEventListener("pause", onPause);
    v.addEventListener("volumechange", onVolume);
    // initialize volume from saved preference or current element volume
    try {
      const savedVol = localStorage.getItem("umd.volume");
      const initVol = savedVol !== null ? Number(savedVol) : v.volume ?? 1;
      setVolume(initVol);
      v.volume = initVol;
    } catch (err) {}
    setIsPlaying(!v.paused);
    return () => {
      v.removeEventListener("play", onPlay);
      v.removeEventListener("pause", onPause);
      v.removeEventListener("volumechange", onVolume);
    };
  }, [selected]);

  const togglePlay = async (e) => {
    // Prevent native browser click toggling so only our handler runs
    try {
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.stopPropagation) e.stopPropagation();
      if (e && e.nativeEvent && e.nativeEvent.stopImmediatePropagation)
        e.nativeEvent.stopImmediatePropagation();
    } catch (err) {}

    const v = videoRef.current;
    if (!v) return;
    // prevent rapid double-toggle (native controls + handler)
    const now = Date.now();
    if (now - (lastToggleRef.current || 0) < 400) return;
    lastToggleRef.current = now;
    try {
      if (v.paused) await v.play();
      else v.pause();
    } catch (err) {}
  };

  // When user clicks the video we want to ensure the native controls
  // do not also toggle playback (causing an immediate resume). To do
  // that we temporarily hide native controls on pointerdown and
  // restore them shortly after the click handler runs.
  const handlePointerDown = (e) => {
    try {
      if (e.button !== 0) return; // only left click
      const v = videoRef.current;
      if (!v) return;
      // if pointerdown happened on the native controls (some browsers),
      // let it behave normally. Only suppress when target is the video element.
      if (e.target !== v) return;
      // clear any previous timer
      if (controlsRestoreTimerRef.current) {
        clearTimeout(controlsRestoreTimerRef.current);
        controlsRestoreTimerRef.current = null;
      }
      // hide native controls briefly
      v.controls = false;
      // restore controls after a short delay
      controlsRestoreTimerRef.current = setTimeout(() => {
        try {
          v.controls = true;
        } catch (err) {}
        controlsRestoreTimerRef.current = null;
      }, 400);
    } catch (err) {}
  };

  const onVolumeChange = (e) => {
    const v = videoRef.current;
    const val = Number(e.target.value);
    setVolume(val);
    try {
      localStorage.setItem("umd.volume", String(val));
    } catch (err) {}
    if (v) v.volume = val;
  };

  // load persisted settings on mount (default autoplay ON)
  useEffect(() => {
    try {
      const savedVol = localStorage.getItem("umd.volume");
      if (savedVol !== null) {
        const n = Number(savedVol);
        setVolume(n);
        if (videoRef.current) videoRef.current.volume = n;
      }
      const savedAuto = localStorage.getItem("umd.autoplay");
      if (savedAuto !== null) setAutoplay(savedAuto === "1");
      else {
        // enable autoplay by default and persist that choice
        setAutoplay(true);
        try {
          localStorage.setItem("umd.autoplay", "1");
        } catch (e) {}
      }
      const savedTheater = localStorage.getItem("umd.theater");
      if (savedTheater !== null) setTheater(savedTheater === "1");
    } catch (err) {}
  }, []);

  useEffect(() => {
    fetchDownloads();
  }, []);

  const combinedList = [...localFiles, ...downloads];

  useEffect(() => {
    const prevTitle = document.title;
    document.title = "Video Player";
    return () => {
      document.title = prevTitle;
    };
  }, []);

  // Player sizing is handled in CSS via aspect-ratio so the video fills
  // the available width while maintaining 16:9. This keeps layout simpler.

  // No editable resizer: list column keeps fixed width and stays on right

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

  // Visibility-based thumbnail loader: observe thumbnail placeholders and
  // start loading the real image when the element enters a generous rootMargin.
  useEffect(() => {
    if (!listRef.current) return;
    const root = null; // viewport
    const obsOptions = { root, rootMargin: "400px", threshold: 0.01 };

    const encodePath = (p) => {
      if (!p) return p;
      if (p.startsWith("http")) return p;
      const leading = p.startsWith("/") ? "/" : "";
      const parts = p.replace(/^\//, "").split("/");
      return leading + parts.map(encodeURIComponent).join("/");
    };

    const backendOrigin =
      api && api.defaults && api.defaults.baseURL
        ? api.defaults.baseURL.replace(/\/$/, "")
        : import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

    const observer = new IntersectionObserver((entries, o) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const imgEl = entry.target;
        const src = imgEl.dataset.thumbSrc;
        if (!src) {
          o.unobserve(imgEl);
          return;
        }

        if (!thumbCacheRef.current.has(src)) {
          const img = new Image();
          img.src = src;
          thumbCacheRef.current.set(src, img);
        }

        try {
          imgEl.src = src;
        } catch (e) {}

        o.unobserve(imgEl);
      });
    }, obsOptions);

    // Observe all current placeholder images
    const imgs = Array.from(
      listRef.current.querySelectorAll(".list-thumb[data-thumb-src]")
    );
    imgs.forEach((i) => observer.observe(i));

    return () => {
      observer.disconnect();
    };
  }, [downloads]);

  const isAbsolute = (p) => {
    if (!p) return false;
    return (
      p.startsWith("http") ||
      p.startsWith("blob:") ||
      p.startsWith("data:") ||
      p.startsWith("file:")
    );
  };

  const addLocalFiles = (fileList) => {
    const arr = Array.from(fileList || []);
    if (arr.length === 0) return;
    const now = Date.now();
    const newItems = arr
      .filter((f) => f && f.type && f.type.startsWith("video/"))
      .map((f, idx) => {
        const id = `local-${now}-${idx}`;
        const blob = URL.createObjectURL(f);
        return {
          id,
          title: f.webkitRelativePath || f.name,
          file_name: f.name,
          file_size: f.size,
          media_url: blob,
          thumbnail_url: null,
          duration: null,
          file_path: null,
          __local_file: true,
        };
      });

    setLocalFiles((prev) => [...newItems, ...prev]);
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    addLocalFiles(files);
    // reset input so selecting same files again triggers change
    e.target.value = null;
  };

  const handleFolderInput = (e) => {
    const files = e.target.files;
    addLocalFiles(files);
    e.target.value = null;
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

  // load adaptiveShadow pref from localStorage on mount
  useEffect(() => {
    try {
      const v = localStorage.getItem("umd.adaptiveShadow");
      if (v !== null) setAdaptiveShadow(v === "1");
    } catch (e) {}
  }, []);

  // Adaptive shadow sampler (throttled, safe for cross-origin)
  useEffect(() => {
    if (!adaptiveShadow) return;
    const video = videoRef.current;
    const el = playerCardRef.current;
    if (!video || !el) return;

    let raf = 0;
    let last = 0;
    const canvas = shadowCanvasRef.current || document.createElement("canvas");
    canvas.width = 32;
    canvas.height = 18; // small 16:9 sample
    shadowCanvasRef.current = canvas;
    const ctx = canvas.getContext("2d");

    const sample = () => {
      try {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        let r = 0,
          g = 0,
          b = 0,
          count = 0;
        // sample every 4th pixel for speed
        for (let i = 0; i < data.length; i += 16) {
          r += data[i];
          g += data[i + 1];
          b += data[i + 2];
          count++;
        }
        if (count === 0) return;
        r = Math.round(r / count);
        g = Math.round(g / count);
        b = Math.round(b / count);

        const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
        const alpha = Math.min(0.6, 0.28 + (0.5 - luminance) * 0.5);
        const spread = luminance > 0.6 ? "0 8px 28px" : "0 12px 48px";
        const shadow = `${spread} rgba(${r}, ${g}, ${b}, ${alpha.toFixed(2)})`;
        el.style.setProperty("--video-shadow", shadow);
      } catch (err) {
        // likely CORS or other issue; stop sampling silently
      }
    };

    const loop = (t) => {
      if (t - last > 160) {
        sample();
        last = t;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [adaptiveShadow, selected]);

  const findIndex = (item) => combinedList.findIndex((d) => d.id === item.id);

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

  const handleToggleAutoplay = () =>
    setAutoplay((v) => {
      const nv = !v;
      try {
        localStorage.setItem("umd.autoplay", nv ? "1" : "0");
      } catch (err) {}
      return nv;
    });

  const handleToggleTheater = (e) => {
    if (e && e.stopPropagation) e.stopPropagation();
    const el = playerCardRef.current;
    if (!el) return setTheater((t) => !t);
    // FLIP: measure start, toggle state to apply final layout, then animate transform
    const start = el.getBoundingClientRect();
    setTheater((t) => !t);
    requestAnimationFrame(() => {
      const end = el.getBoundingClientRect();
      // guard
      if (end.width === 0 || end.height === 0) return;
      const dx = start.left - end.left;
      const dy = start.top - end.top;
      const sx = start.width / end.width;
      const sy = start.height / end.height;
      // apply inverse transform immediately without transition
      el.style.transition = "none";
      el.style.transformOrigin = "center top";
      el.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`;
      // force reflow
      // eslint-disable-next-line @typescript-eslint/no-unused-expressions
      el.offsetWidth;
      // animate to identity
      el.style.transition =
        "transform 420ms cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 420ms ease, opacity 300ms ease";
      el.style.transform = "";
      const cleanup = () => {
        el.style.transition = "";
        el.style.transform = "";
        el.removeEventListener("transitionend", cleanup);
      };
      el.addEventListener("transitionend", cleanup);
    });
  };

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
      {combinedList.length === 0 && <p>No completed downloads yet.</p>}

      <div className="downloaded-container" ref={containerRef}>
        <div className="player-column">
          <div className="local-open-toolbar">
            <button
              className="btn btn-small"
              onClick={() =>
                fileInputRef.current && fileInputRef.current.click()
              }
            >
              Open File(s)
            </button>
            <button
              className="btn btn-small"
              onClick={async () => {
                // Prefer File System Access API for true folder selection when available
                if (window.showDirectoryPicker) {
                  try {
                    const dirHandle = await window.showDirectoryPicker();
                    const collected = [];

                    const recurse = async (handle, prefix = "") => {
                      for await (const [name, entry] of handle.entries()) {
                        if (entry.kind === "file") {
                          const f = await entry.getFile();
                          try {
                            Object.defineProperty(f, "webkitRelativePath", {
                              value: prefix + name,
                              writable: false,
                              configurable: true,
                            });
                          } catch (e) {}
                          collected.push(f);
                        } else if (entry.kind === "directory") {
                          await recurse(entry, prefix + name + "/");
                        }
                      }
                    };

                    await recurse(dirHandle, "");
                    addLocalFiles(collected);
                  } catch (err) {
                    // fallback to hidden input if API unavailable or user cancels
                    folderInputRef.current && folderInputRef.current.click();
                  }
                } else {
                  folderInputRef.current && folderInputRef.current.click();
                }
              }}
            >
              Open Folder
            </button>
            {typeof window !== "undefined" &&
              (window.location.hostname === "localhost" ||
                window.location.hostname === "127.0.0.1") && (
                <button
                  className="btn btn-small"
                  onClick={() => {
                    setAdaptiveShadow((v) => {
                      const nv = !v;
                      try {
                        localStorage.setItem(
                          "umd.adaptiveShadow",
                          nv ? "1" : "0"
                        );
                      } catch (e) {}
                      return nv;
                    });
                  }}
                  title="Toggle adaptive shadow (dev)"
                >
                  {adaptiveShadow
                    ? "Adaptive Shadow: On"
                    : "Adaptive Shadow: Off"}
                </button>
              )}
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              multiple
              style={{ display: "none" }}
              onChange={handleFileInput}
            />
            <input
              ref={folderInputRef}
              type="file"
              // webkitdirectory enables folder selection in Chromium-based browsers
              webkitdirectory
              directory
              multiple
              style={{ display: "none" }}
              onChange={handleFolderInput}
            />
          </div>
          {selected ? (
            <div
              ref={playerCardRef}
              className={`player-card ${theater ? "theater" : ""} ${
                largePlayer ? "large" : ""
              }`}
            >
              {/* prefer media_url (served at /media) and convert to absolute URL so cross-origin range requests work consistently */}
              {(() => {
                const backendOrigin =
                  api && api.defaults && api.defaults.baseURL
                    ? api.defaults.baseURL.replace(/\/$/, "")
                    : import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

                // helper: encode each path segment so characters like '#' are percent-encoded
                const encodePath = (p) => {
                  if (!p) return p;
                  if (p.startsWith("http")) return p;
                  const leading = p.startsWith("/") ? "/" : "";
                  const parts = p.replace(/^\//, "").split("/");
                  return leading + parts.map(encodeURIComponent).join("/");
                };

                const src = selected.media_url
                  ? isAbsolute(selected.media_url)
                    ? selected.media_url
                    : `${backendOrigin}${encodePath(selected.media_url)}`
                  : `${backendOrigin}/api/downloads/${selected.id}/file`;
                return (
                  <>
                    <div className="video-wrapper">
                      <video
                        ref={videoRef}
                        controls
                        preload="metadata"
                        src={src}
                        className="main-player"
                        crossOrigin="anonymous"
                        onClick={togglePlay}
                        onPointerDown={handlePointerDown}
                        autoPlay={autoplay}
                        playsInline
                      />
                    </div>

                    <div
                      className="player-controls"
                      role="group"
                      aria-label="player controls"
                    >
                      <div className="controls-bar">
                        <button
                          className="btn control prev"
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePrev();
                          }}
                          aria-label="Previous"
                        >
                          ◀◀
                        </button>
                        <button
                          className="btn control play"
                          onClick={(e) => {
                            e.stopPropagation();
                            togglePlay();
                          }}
                          aria-label={isPlaying ? "Pause" : "Play"}
                        >
                          {isPlaying ? "❚❚" : "▶"}
                        </button>

                        <button
                          className="btn control next"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleNext();
                          }}
                          aria-label="Next"
                        >
                          ▶▶
                        </button>
                        <div className="volume-control">
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={volume}
                            onChange={onVolumeChange}
                            aria-label="Volume"
                          />
                        </div>
                        <button
                          className={`btn control autoplay-btn ${
                            autoplay ? "active" : ""
                          }`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleAutoplay();
                          }}
                          title="Toggle Autoplay"
                          aria-pressed={autoplay}
                        >
                          {autoplay ? "Autoplay On" : "Autoplay Off"}
                        </button>
                      </div>

                      <div className="controls-right" role="group">
                        <button
                          className="btn control theater-toggle"
                          onClick={handleToggleTheater}
                          title="Toggle theater mode"
                        >
                          {theater ? "Exit" : "Theater"}
                        </button>
                      </div>
                    </div>
                  </>
                );
              })()}

              <h3 className="player-title">
                {selected.title || selected.file_name}
              </h3>
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

        <aside
          className="list-column"
          aria-label="Downloaded videos"
          ref={listRef}
        >
          {combinedList.map((d) => (
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
              {(() => {
                const backendOrigin =
                  api && api.defaults && api.defaults.baseURL
                    ? api.defaults.baseURL.replace(/\/$/, "")
                    : import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
                const placeholder =
                  "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";

                const encodePath = (p) => {
                  if (!p) return p;
                  if (p.startsWith("http")) return p;
                  const leading = p.startsWith("/") ? "/" : "";
                  const parts = p.replace(/^\//, "").split("/");
                  return leading + parts.map(encodeURIComponent).join("/");
                };

                // Append a cache-busting query param so clients always fetch the
                // latest thumbnail instead of relying on cached 304 responses.
                const thumbSrc = d.thumbnail_url
                  ? isAbsolute(d.thumbnail_url)
                    ? d.thumbnail_url +
                      (d.updated_at
                        ? (d.thumbnail_url.includes("?") ? "&" : "?") +
                          `v=${encodeURIComponent(d.updated_at)}`
                        : "")
                    : `${backendOrigin}${encodePath(d.thumbnail_url)}${
                        d.updated_at
                          ? (d.thumbnail_url.includes("?") ? "&" : "?") +
                            `v=${encodeURIComponent(d.updated_at)}`
                          : ""
                      }`
                  : placeholder;
                return (
                  <img
                    src={thumbSrc}
                    loading="lazy"
                    alt={d.title || d.file_name}
                    className="list-thumb"
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = placeholder;
                    }}
                  />
                );
              })()}
              <div className="list-meta">
                <div className="list-title">{d.title || d.file_name}</div>
                <div className="list-sub">
                  {d.duration
                    ? (() => {
                        const totalSec = Math.round(d.duration);
                        const h = Math.floor(totalSec / 3600);
                        const m = Math.floor((totalSec % 3600) / 60);
                        const s = totalSec % 60;
                        return h > 0
                          ? `${h}:${String(m).padStart(2, "0")}:${String(
                              s
                            ).padStart(2, "0")}`
                          : `${m}:${String(s).padStart(2, "0")}`;
                      })()
                    : ""}
                </div>
                {/* Diagnostic: show raw thumbnail URL so you can copy/paste to test */}
                <div className="thumb-url">
                  {d.thumbnail_url || "(no thumbnail)"}
                </div>
              </div>
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
