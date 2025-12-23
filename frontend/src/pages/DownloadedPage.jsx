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
  const skipAutoNextRef = useRef(false);
  const upNextIntervalRef = useRef(null);
  const [showUpNext, setShowUpNext] = useState(false);
  const [upNextCountdown, setUpNextCountdown] = useState(0);
  const [showReplay, setShowReplay] = useState(false);
  const [descOpen, setDescOpen] = useState(false);
  const [upNextEnabled, setUpNextEnabled] = useState(() => {
    try {
      const v = localStorage.getItem("umd.upNextEnabled");
      return v === null ? true : v === "1";
    } catch (e) {
      return true;
    }
  });
  const [moreOptionsOpen, setMoreOptionsOpen] = useState(false);
  const [theater, setTheater] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showCustom, setShowCustom] = useState(() => {
    try {
      const v = localStorage.getItem("umd.showCustom");
      return v === null ? true : v === "1";
    } catch (e) {
      return true;
    }
  });
  const [volume, setVolume] = useState(1);
  const thumbCacheRef = useRef(new Map());
  const [localFiles, setLocalFiles] = useState([]);
  const [persistentFiles, setPersistentFiles] = useState(null);
  const [persistentPath, setPersistentPath] = useState(null);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  const [largePlayer, setLargePlayer] = useState(false);
  const [showList, setShowList] = useState(true);
  const [navigationMode, setNavigationMode] = useState(() => {
    try {
      return localStorage.getItem("umd.navMode") || "list";
    } catch (e) {
      return "list";
    }
  });
  const [userLoadedList, setUserLoadedList] = useState(false);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onPlay = () => setIsPlaying(true);
    const onLoadedMeta = () => {
      try {
        const vid = videoRef.current;
        if (!vid) return;
        const w = vid.videoWidth;
        const h = vid.videoHeight;
        const videoEl =
          playerCardRef.current?.querySelector?.(".video-element");
        if (videoEl && w && h) {
          // CSS expects aspect like "16/9"
          videoEl.style.setProperty("--video-aspect", `${w}/${h}`);
        }
      } catch (e) {}
    };
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
    v.addEventListener("loadedmetadata", onLoadedMeta);
    // keep replay overlay hidden once playing
    const onPlaying = () => setShowReplay(false);
    v.addEventListener("playing", onPlaying);
    // initialize volume from saved preference or current element volume
    try {
      const savedVol = localStorage.getItem("umd.volume");
      const initVol = savedVol !== null ? Number(savedVol) : v.volume ?? 1;
      setVolume(initVol);
      v.volume = initVol;
    } catch (err) {}
    setIsPlaying(!v.paused);
    // If metadata already available, set aspect immediately
    try {
      if (v.readyState >= 1) onLoadedMeta();
    } catch (e) {}
    return () => {
      v.removeEventListener("play", onPlay);
      v.removeEventListener("pause", onPause);
      v.removeEventListener("volumechange", onVolume);
      v.removeEventListener("playing", onPlaying);
      v.removeEventListener("loadedmetadata", onLoadedMeta);
    };
  }, [selected]);

  // Persist upNextEnabled setting
  useEffect(() => {
    try {
      localStorage.setItem("umd.upNextEnabled", upNextEnabled ? "1" : "0");
    } catch (e) {}
  }, [upNextEnabled]);

  // Persist showCustom setting
  useEffect(() => {
    try {
      localStorage.setItem("umd.showCustom", showCustom ? "1" : "0");
    } catch (e) {}
  }, [showCustom]);

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

  // Keep the list column height in sync with the visible video area.
  // This sets a CSS variable on the container so the CSS can cap the
  // sidebar height to the player's visible height and allow independent scrolling.
  useEffect(() => {
    if (!containerRef.current) return;

    const setPlayerVisibleHeight = () => {
      try {
        const playerEl = playerCardRef.current;
        if (!playerEl) return;
        // Measure only the video element (preserves aspect ratio) so
        // controls and title wrapping do not affect the computed visible
        // player height used to size the sidebar.
        const videoWrap =
          playerEl.querySelector?.(".video-element") ||
          playerEl.querySelector?.(".video-wrapper") ||
          playerEl;
        if (!videoWrap) return;
        const rect = videoWrap.getBoundingClientRect();
        const containerRect = containerRef.current.getBoundingClientRect();
        const topOffset = Math.max(0, Math.round(rect.top - containerRect.top));
        // Use the element's height (px) so CSS can use it directly
        containerRef.current.style.setProperty(
          "--player-visible-height",
          `${Math.max(0, Math.round(rect.height))}px`
        );
        containerRef.current.style.setProperty(
          "--player-visible-top-offset",
          `${topOffset}px`
        );
      } catch (err) {}
    };

    // Initial set
    setPlayerVisibleHeight();

    // ResizeObserver to catch dynamic changes to the video wrapper
    let ro;
    try {
      const playerEl = playerCardRef.current;
      const videoWrap =
        playerEl?.querySelector?.(".video-element") ||
        playerEl?.querySelector?.(".video-wrapper") ||
        null;
      if (videoWrap && window.ResizeObserver) {
        ro = new ResizeObserver(() => setPlayerVisibleHeight());
        ro.observe(videoWrap);
      }
    } catch (e) {}

    // window resize fallback
    window.addEventListener("resize", setPlayerVisibleHeight);

    return () => {
      window.removeEventListener("resize", setPlayerVisibleHeight);
      try {
        if (ro) ro.disconnect();
      } catch (e) {}
    };
  }, [selected, theater, largePlayer]);

  useEffect(() => {
    fetchDownloads();
    // Try to load server-configured persistent folder and its files
    (async () => {
      try {
        const resp = await api.get("/persistent-media");
        if (resp && resp.data && resp.data.path) {
          setPersistentPath(resp.data.path);
          const filesResp = await api.get("/persistent-media/files");
          if (
            filesResp &&
            filesResp.data &&
            Array.isArray(filesResp.data.items)
          ) {
            setPersistentFiles(filesResp.data.items || []);
            if (!selected && filesResp.data.items.length > 0)
              setSelected(filesResp.data.items[0]);
          }
        }
      } catch (e) {
        // ignore - backend may not support persistent-media route in older setups
      }
    })();
  }, []);

  const combinedList = [...localFiles, ...downloads];

  // Sidebar list selection:
  // - If a persistent folder is configured, show those files.
  // - Otherwise, only show the sidebar list if the user explicitly loaded
  //   a folder or files during this session (`userLoadedList`). By default
  //   the sidebar stays empty while the grid shows project downloads.
  const listItems = (() => {
    if (persistentFiles && persistentFiles.length > 0) return persistentFiles;
    if (userLoadedList)
      return localFiles && localFiles.length > 0 ? localFiles : [];
    return [];
  })();

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
      // Do NOT populate localFiles from DB results — grid must reflect
      // folder contents only (persistent folder or user-loaded files).
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
          __file: f,
          thumbnail_url: null,
          duration: null,
          file_path: null,
          __local_file: true,
        };
      });

    setLocalFiles((prev) => [...newItems, ...prev]);
    // mark that the user explicitly loaded files (folder/file)
    setUserLoadedList(true);
    // If nothing is selected, pick the first newly-loaded file so it appears
    // in both the grid and (when userLoadedList) the sidebar immediately.
    try {
      if (!selected && newItems.length > 0) setSelected(newItems[0]);
    } catch (e) {}
  };

  // Revoke object URLs when localFiles are removed or component unmounts
  useEffect(() => {
    return () => {
      try {
        localFiles.forEach((l) => {
          if (l && l.media_url && l.__file) {
            try {
              URL.revokeObjectURL(l.media_url);
            } catch (e) {}
          }
        });
      } catch (e) {}
    };
  }, [localFiles]);

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

  // Drag-and-drop support to load local files (works for both list and grid)
  useEffect(() => {
    const el = containerRef.current || document.body;
    if (!el) return;

    const onDragOver = (ev) => {
      try {
        ev.preventDefault();
        el.classList && el.classList.add("dragover");
      } catch (e) {}
    };
    const onDragLeave = (ev) => {
      try {
        el.classList && el.classList.remove("dragover");
      } catch (e) {}
    };
    const onDrop = (ev) => {
      try {
        ev.preventDefault();
        el.classList && el.classList.remove("dragover");
        const dt = ev.dataTransfer;
        if (!dt) return;
        const files = dt.files;
        if (!files || files.length === 0) return;
        addLocalFiles(files);
      } catch (e) {}
    };

    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    window.addEventListener("drop", onDrop);

    return () => {
      window.removeEventListener("dragover", onDragOver);
      window.removeEventListener("dragleave", onDragLeave);
      window.removeEventListener("drop", onDrop);
    };
  }, [containerRef.current]);

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
    let ctx;
    try {
      ctx =
        canvas.getContext("2d", { willReadFrequently: true }) ||
        canvas.getContext("2d");
    } catch (e) {
      ctx = canvas.getContext("2d");
    }

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

  const findIndex = (item, arr = combinedList) =>
    arr.findIndex((d) => d && item && d.id === item.id);

  const _chooseSourceArray = () => {
    // navigationMode: 'list' => use the sidebar listItems
    // navigationMode: 'grid' => use localFiles (visible grid)
    if (navigationMode === "grid") {
      // Grid should only reflect files coming directly from folders:
      // prefer server-configured persistent folder, otherwise user-loaded local files.
      // Do NOT fall back to DB downloads here.
      if (persistentFiles && persistentFiles.length > 0) return persistentFiles;
      if (localFiles && localFiles.length > 0) return localFiles;
      return [];
    }
    // default: list
    return listItems && listItems.length > 0 ? listItems : combinedList;
  };

  const getNextItem = () => {
    const src = _chooseSourceArray() || [];
    if (!selected || !src || src.length === 0) return null;
    const idx = findIndex(selected, src);
    if (idx === -1) return null;
    // if only one item, return null
    if (src.length === 1) return null;
    return src[(idx + 1) % src.length];
  };

  const handleNext = () => {
    if (!selected) return;
    const src = _chooseSourceArray();
    const idx = findIndex(selected, src);
    if (idx === -1) {
      // fallback to combinedList
      const fidx = findIndex(selected, combinedList);
      if (fidx === -1) return;
      const next = combinedList[(fidx + 1) % Math.max(1, combinedList.length)];
      setSelected(next);
      return;
    }
    const next = src[(idx + 1) % Math.max(1, src.length)];
    setSelected(next);
  };

  const handlePrev = () => {
    if (!selected) return;
    const src = _chooseSourceArray();
    const idx = findIndex(selected, src);
    if (idx === -1) {
      const fidx = findIndex(selected, combinedList);
      if (fidx === -1) return;
      const prev =
        combinedList[(fidx - 1 + combinedList.length) % combinedList.length];
      setSelected(prev);
      return;
    }
    const prev = src[(idx - 1 + src.length) % src.length];
    setSelected(prev);
  };

  // Up Next / Replay overlay: show when nearing the end, countdown and auto-advance
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const UP_NEXT_THRESHOLD = 8; // seconds before end to show up-next

    const clearUpNextTimer = () => {
      try {
        if (upNextIntervalRef.current) {
          clearInterval(upNextIntervalRef.current);
          upNextIntervalRef.current = null;
        }
      } catch (e) {}
    };

    const onTimeUpdate = () => {
      try {
        if (skipAutoNextRef.current) return;
        if (!upNextEnabled) return;
        if (!v.duration || !isFinite(v.duration)) return;
        const remaining = v.duration - v.currentTime;
        const next = getNextItem();
        if (remaining <= UP_NEXT_THRESHOLD && next) {
          if (!showUpNext) {
            setShowUpNext(true);
            setUpNextCountdown(Math.max(1, Math.ceil(remaining)));
            // start countdown
            clearUpNextTimer();
            upNextIntervalRef.current = setInterval(() => {
              setUpNextCountdown((c) => {
                if (c <= 1) {
                  clearUpNextTimer();
                  setShowUpNext(false);
                  handleNext();
                  return 0;
                }
                return c - 1;
              });
            }, 1000);
          }
        } else {
          if (showUpNext) {
            setShowUpNext(false);
            clearUpNextTimer();
          }
        }
      } catch (e) {}
    };

    const onEnded = () => {
      try {
        clearUpNextTimer();
        setShowUpNext(false);
        setShowReplay(true);
      } catch (e) {}
    };

    v.addEventListener("timeupdate", onTimeUpdate);
    v.addEventListener("ended", onEnded);

    return () => {
      v.removeEventListener("timeupdate", onTimeUpdate);
      v.removeEventListener("ended", onEnded);
      clearUpNextTimer();
    };
  }, [
    selected,
    navigationMode,
    localFiles,
    persistentFiles,
    downloads,
    showUpNext,
  ]);

  // Global Spacebar handler: toggle play/pause and prevent page scrolling
  useEffect(() => {
    const onKeyDown = (e) => {
      try {
        // Accept both ' ' and 'Space' depending on browser
        if (e.code !== "Space" && e.key !== " ") return;
        const active = document.activeElement;
        const tag = active && active.tagName && active.tagName.toLowerCase();
        const isEditable =
          tag === "input" || tag === "textarea" || active?.isContentEditable;
        if (isEditable) return; // don't hijack typing
        e.preventDefault();
        e.stopPropagation();
        togglePlay();
      } catch (err) {}
    };

    window.addEventListener("keydown", onKeyDown, { capture: true });
    return () =>
      window.removeEventListener("keydown", onKeyDown, { capture: true });
  }, [selected, isPlaying]);

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
              webkitdirectory="true"
              directory="true"
              multiple
              style={{ display: "none" }}
              onChange={handleFolderInput}
            />
            {localFiles.length > 0 && (
              <button
                className="btn btn-small"
                onClick={() => {
                  // revoke object URLs and clear local list
                  try {
                    localFiles.forEach((l) => {
                      if (l && l.media_url) URL.revokeObjectURL(l.media_url);
                    });
                  } catch (e) {}
                  setLocalFiles([]);
                  setUserLoadedList(false);
                }}
                title="Clear local files"
              >
                Clear Local Files
              </button>
            )}
            {/* Persistent folder controls (server-side persistent folder) */}
            <button
              className="btn btn-small"
              onClick={async () => {
                const p = window.prompt(
                  "Set persistent folder (absolute path, server must allow it):",
                  persistentPath || ""
                );
                if (!p) return;
                try {
                  await api.post("/persistent-media", { path: p });
                  setPersistentPath(p);
                  const filesResp = await api.get("/persistent-media/files");
                  setPersistentFiles(filesResp.data.items || []);
                  if (filesResp.data.items && filesResp.data.items.length > 0)
                    setSelected(filesResp.data.items[0]);
                } catch (err) {
                  alert(
                    "Failed to set persistent folder: " +
                      (err?.response?.data?.detail || err.message)
                  );
                }
              }}
            >
              Set Persistent Folder
            </button>
            {persistentPath && (
              <button
                className="btn btn-small"
                onClick={async () => {
                  try {
                    await api.delete("/persistent-media");
                    setPersistentPath(null);
                    setPersistentFiles(null);
                  } catch (err) {
                    alert("Failed to clear persistent folder");
                  }
                }}
                title="Clear persistent folder"
              >
                Clear Persistent Folder
              </button>
            )}
          </div>
          {selected ? (
            <div
              ref={playerCardRef}
              className={`player-card ${theater ? "theater" : ""} ${
                largePlayer ? "large" : ""
              } ${showCustom ? "show-custom" : ""}`}
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
                      <div className="video-element">
                        <video
                          ref={videoRef}
                          preload="metadata"
                          src={src}
                          className="main-player"
                          crossOrigin="anonymous"
                          onClick={togglePlay}
                          onPointerDown={handlePointerDown}
                          autoPlay={autoplay}
                          playsInline
                          controls
                        />
                      </div>

                      {/* Up Next / Replay overlay */}
                      {(showUpNext || showReplay) && (
                        <div
                          className={`upnext-overlay ${
                            showUpNext ? "show" : ""
                          } ${showReplay ? "replay" : ""}`}
                        >
                          <div className="upnext-card">
                            {showUpNext &&
                              (() => {
                                const next = getNextItem();
                                if (!next) return null;
                                return (
                                  <div className="upnext-content">
                                    <img
                                      src={next.thumbnail_url || ""}
                                      alt={next.title || next.file_name}
                                      className="upnext-thumb"
                                      onError={(e) =>
                                        (e.currentTarget.style.display = "none")
                                      }
                                    />
                                    <div className="upnext-meta">
                                      <div className="upnext-label">
                                        Up next
                                      </div>
                                      <div className="upnext-title">
                                        {next.title || next.file_name}
                                      </div>
                                      <div className="upnext-countdown">
                                        Playing in {upNextCountdown}s
                                      </div>
                                      <div className="upnext-actions">
                                        <button
                                          className="btn"
                                          onClick={() => {
                                            // play next immediately
                                            setShowUpNext(false);
                                            skipAutoNextRef.current = false;
                                            handleNext();
                                          }}
                                        >
                                          Play Now
                                        </button>
                                        <button
                                          className="btn"
                                          onClick={() => {
                                            // cancel auto-next for this session
                                            setShowUpNext(false);
                                            skipAutoNextRef.current = true;
                                          }}
                                        >
                                          Cancel
                                        </button>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })()}

                            {showReplay && (
                              <div className="upnext-content">
                                <div className="upnext-meta">
                                  <div className="upnext-label">
                                    Playback ended
                                  </div>
                                  <div className="upnext-title">
                                    {selected.title || selected.file_name}
                                  </div>
                                  <div className="upnext-actions">
                                    <button
                                      className="btn"
                                      onClick={() => {
                                        try {
                                          const v = videoRef.current;
                                          if (v) {
                                            v.currentTime = 0;
                                            v.play().catch(() => {});
                                          }
                                        } catch (e) {}
                                        setShowReplay(false);
                                      }}
                                    >
                                      Replay
                                    </button>
                                    <button
                                      className="btn"
                                      onClick={() => {
                                        setShowReplay(false);
                                        handleNext();
                                      }}
                                    >
                                      Next
                                    </button>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="player-header">
                        <h3 className="player-title">
                          {selected.title || selected.file_name}
                        </h3>
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
                    </div>
                  </>
                );
              })()}

              <div className="player-details-section">
                <div className="more-options-row">
                  <button
                    className="btn btn-small more-btn"
                    onClick={() => setMoreOptionsOpen((s) => !s)}
                    aria-expanded={moreOptionsOpen}
                    title="More options"
                  >
                    More ▾
                  </button>
                  {moreOptionsOpen && (
                    <div className="more-options-menu">
                      <label className="more-option">
                        <input
                          type="checkbox"
                          checked={upNextEnabled}
                          onChange={(e) => setUpNextEnabled(e.target.checked)}
                        />
                        Enable Up Next overlay
                      </label>
                      <label className="more-option">
                        <input
                          type="checkbox"
                          checked={showCustom}
                          onChange={(e) => setShowCustom(e.target.checked)}
                        />
                        Show custom controls
                      </label>
                    </div>
                  )}
                </div>

                <button
                  className="btn btn-small desc-toggle-bottom"
                  onClick={() => setDescOpen((s) => !s)}
                  aria-expanded={descOpen}
                >
                  {descOpen ? "Hide details ▴" : "Show details ▾"}
                </button>

                {descOpen && (
                  <div className="player-desc-btm">
                    {selected.file_size && (
                      <div className="desc-row">
                        {Math.round(selected.file_size / 1024 / 1024)} MB
                      </div>
                    )}
                    {selected.duration && (
                      <div className="desc-row">
                        {(() => {
                          const totalSec = Math.round(selected.duration);
                          const h = Math.floor(totalSec / 3600);
                          const m = Math.floor((totalSec % 3600) / 60);
                          const s = totalSec % 60;
                          return h > 0
                            ? `${h}:${String(m).padStart(2, "0")}:${String(
                                s
                              ).padStart(2, "0")}`
                            : `${m}:${String(s).padStart(2, "0")}`;
                        })()}
                      </div>
                    )}
                    {selected.file_path && (
                      <div className="desc-row file-path-small">
                        {selected.file_path}
                      </div>
                    )}
                  </div>
                )}
              </div>
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
          <div className="list-header">
            <div className="list-header-title">Downloaded videos</div>
            <div className="list-header-actions">
              <button
                className="btn btn-small"
                onClick={() => setShowList((s) => !s)}
                aria-pressed={showList}
              >
                {showList ? "Hide List" : "Show List"}
              </button>
              <select
                className="nav-mode-select"
                value={navigationMode}
                onChange={(e) => {
                  const v = e.target.value;
                  setNavigationMode(v);
                  try {
                    localStorage.setItem("umd.navMode", v);
                  } catch (err) {}
                }}
                title="Navigation mode: choose list (sidebar) or grid (local files)"
                aria-label="Navigation mode"
              >
                <option value="list">List</option>
                <option value="grid">Grid</option>
              </select>
            </div>
          </div>

          {showList &&
            listItems.map((d) => (
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
      {localFiles.length > 0 && (
        <section className="local-grid" aria-label="Local folder preview">
          <h4 className="local-grid-heading">Local Folder Preview</h4>
          <div className="local-grid-items">
            {localFiles.map((d) => (
              <div
                key={d.id}
                className={`local-grid-item ${
                  selected && selected.id === d.id ? "active" : ""
                }`}
                onClick={() => setSelected(d)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && setSelected(d)}
              >
                <video
                  src={d.media_url}
                  muted
                  playsInline
                  preload="metadata"
                  className="local-preview-video"
                  onMouseEnter={(e) => {
                    try {
                      e.currentTarget.play().catch(() => {});
                    } catch (err) {}
                  }}
                  onMouseLeave={(e) => {
                    try {
                      e.currentTarget.pause();
                      e.currentTarget.currentTime = 0;
                    } catch (err) {}
                  }}
                />
                <div className="grid-title">{d.title || d.file_name}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
