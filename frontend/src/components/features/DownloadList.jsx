import { useEffect, useState } from 'react';
import downloadService from '../../services/downloadService';
import useDownloadStore from '../../store/slices/downloadStore';
import './DownloadList.css';

export default function DownloadList({ statusFilter = null }) {
  const { downloads, setDownloads, updateDownload, removeDownload } = useDownloadStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDownloads();
    // Refresh every 5 seconds
    const interval = setInterval(fetchDownloads, 5000);
    return () => clearInterval(interval);
  }, [statusFilter]);

  const fetchDownloads = async () => {
    try {
      const params = {};
      if (statusFilter) {
        params.status = statusFilter;
      }
      const data = await downloadService.getAllDownloads(params);
      setDownloads(data || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch downloads');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this download?')) {
      return;
    }

    try {
      await downloadService.deleteDownload(id);
      removeDownload(id);
    } catch (err) {
      alert('Failed to delete download');
    }
  };

  const handleCancel = async (id) => {
    try {
      await downloadService.cancelDownload(id);
      updateDownload(id, { status: 'cancelled' });
    } catch (err) {
      alert('Failed to cancel download');
    }
  };

  const handleRetry = async (id) => {
    try {
      const download = await downloadService.retryDownload(id);
      updateDownload(id, download);
    } catch (err) {
      alert('Failed to retry download');
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      pending: 'badge-pending',
      processing: 'badge-processing',
      completed: 'badge-completed',
      failed: 'badge-failed',
      cancelled: 'badge-cancelled'
    };

    return <span className={`badge ${statusClasses[status] || 'badge-pending'}`}>{status}</span>;
  };

  if (loading && downloads.length === 0) {
    return (
      <div className="download-list-loading">
        <span className="spinner" style={{ width: '2rem', height: '2rem' }}></span>
        <p>Loading downloads...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="download-list-error">
        <p>{error}</p>
        <button className="btn btn-primary" onClick={fetchDownloads}>
          Retry
        </button>
      </div>
    );
  }

  if (downloads.length === 0) {
    return (
      <div className="download-list-empty">
        <p>No downloads yet</p>
        <p className="text-secondary">Start by creating a new download</p>
      </div>
    );
  }

  return (
    <div className="download-list">
      {downloads.map((download) => (
        <div key={download.id} className="download-item">
          <div className="download-info">
            {download.thumbnail_url && (
              <div className="download-thumbnail">
                <img src={download.thumbnail_url} alt={download.title} />
              </div>
            )}
            <div className="download-details">
              <h3 className="download-title">{download.title || 'Unknown'}</h3>
              <div className="download-meta">
                <span className="download-type">{download.download_type}</span>
                <span className="download-format">{download.format}</span>
                {download.quality && <span className="download-quality">{download.quality}</span>}
              </div>
              {download.status === 'processing' && download.progress !== null && (
                <div className="download-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${download.progress}%` }}
                    ></div>
                  </div>
                  <span className="progress-text">{download.progress}%</span>
                </div>
              )}
              {download.error_message && (
                <p className="download-error">{download.error_message}</p>
              )}
            </div>
          </div>

          <div className="download-actions">
            {getStatusBadge(download.status)}

            {download.status === 'completed' && download.file_path && (
              <span className="download-file-path" title={download.file_path}>
                ✓ Downloaded
              </span>
            )}

            {(download.status === 'pending' || download.status === 'processing') && (
              <button
                className="btn btn-small btn-danger"
                onClick={() => handleCancel(download.id)}
              >
                Cancel
              </button>
            )}

            {download.status === 'failed' && (
              <button
                className="btn btn-small btn-secondary"
                onClick={() => handleRetry(download.id)}
              >
                Retry
              </button>
            )}

            <button
              className="btn btn-small btn-danger"
              onClick={() => handleDelete(download.id)}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
