import { useState, useEffect } from "react";
import useSettingsStore from "../store/slices/settingsStore";
import settingsService from "../services/settingsService";
import { useToast } from "../hooks/useToast";
import { useTheme } from "../hooks/useTheme";
import "./SettingsPage.css";

export default function SettingsPage() {
  const settings = useSettingsStore();
  const toast = useToast();
  const { theme, toggleTheme } = useTheme();
  const [downloadLocation, setDownloadLocation] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Load download location from backend
    const loadSettings = async () => {
      try {
        const data = await settingsService.getSettings();
        setDownloadLocation(data.download_location || "");
      } catch (err) {
        console.error("Failed to load settings:", err);
      }
    };
    loadSettings();
  }, []);

  const handleSaveDownloadLocation = async () => {
    setSaving(true);
    try {
      await settingsService.updateSettings({
        download_location: downloadLocation,
      });
      toast.success("Download location saved successfully!");
    } catch (err) {
      toast.error("Failed to save download location");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="page-subtitle">Configure your download preferences</p>
      </div>

      <div className="settings-container">
        {/* Appearance */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Appearance</h2>
          </div>

          <div className="form-group">
            <label className="form-label">Theme</label>
            <select
              className="form-select"
              value={theme}
              onChange={(e) => {
                if (e.target.value !== theme) {
                  toggleTheme();
                }
              }}
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
            <p className="form-help">Choose your preferred color theme</p>
          </div>

          <div className="form-group">
            <div className="checkbox-group">
              <input
                type="checkbox"
                id="notifications"
                checked={settings.notifications}
                onChange={(e) => settings.setNotifications(e.target.checked)}
              />
              <label htmlFor="notifications">Enable notifications</label>
            </div>
            <p className="form-help">
              Show notifications when downloads complete
            </p>
          </div>
        </div>

        {/* Download Location */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Download Location</h2>
          </div>

          <div className="form-group">
            <label className="form-label">Save downloads to</label>
            <div style={{ display: "flex", gap: "10px" }}>
              <input
                type="text"
                className="form-input"
                placeholder="Enter custom download path"
                value={downloadLocation}
                onChange={(e) => setDownloadLocation(e.target.value)}
                style={{ flex: 1 }}
              />
              <button
                className="btn btn-primary"
                onClick={handleSaveDownloadLocation}
                disabled={saving}
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
            <p className="form-help">
              Downloads will be organized in Audio and Video subfolders inside
              the Downloads folder of the app directory.
            </p>
          </div>
        </div>

        {/* Default Download Settings */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Default Download Settings</h2>
          </div>

          <div className="form-group">
            <label className="form-label">Default Download Type</label>
            <select
              className="form-select"
              value={settings.defaultDownloadType}
              onChange={(e) => settings.setDefaultDownloadType(e.target.value)}
            >
              <option value="video">Video</option>
              <option value="audio">Audio</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Default Video Quality</label>
            <select
              className="form-select"
              value={settings.defaultQuality}
              onChange={(e) => settings.setDefaultQuality(e.target.value)}
            >
              <option value="best">Best Quality</option>
              <option value="1080p">1080p</option>
              <option value="720p">720p</option>
              <option value="480p">480p</option>
              <option value="360p">360p</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Default Video Format</label>
            <select
              className="form-select"
              value={settings.defaultVideoFormat}
              onChange={(e) => settings.setDefaultVideoFormat(e.target.value)}
            >
              <option value="mp4">MP4</option>
              <option value="webm">WebM</option>
              <option value="mkv">MKV</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Default Audio Format</label>
            <select
              className="form-select"
              value={settings.defaultAudioFormat}
              onChange={(e) => settings.setDefaultAudioFormat(e.target.value)}
            >
              <option value="m4a">M4A</option>
              <option value="mp3">MP3</option>
              <option value="opus">Opus</option>
              <option value="vorbis">Vorbis</option>
            </select>
          </div>

          <div className="form-group">
            <div className="checkbox-group">
              <input
                type="checkbox"
                id="embedThumbnail"
                checked={settings.embedThumbnail}
                onChange={(e) => settings.setEmbedThumbnail(e.target.checked)}
              />
              <label htmlFor="embedThumbnail">
                Embed thumbnail in audio files
              </label>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="settings-actions">
          <button
            className="btn btn-danger"
            onClick={() => {
              if (confirm("Reset all settings to defaults?")) {
                settings.resetSettings();
              }
            }}
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
}
