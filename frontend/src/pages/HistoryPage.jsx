import { useState } from 'react';
import DownloadList from '../components/features/DownloadList';
import './HistoryPage.css';

export default function HistoryPage() {
  const [statusFilter, setStatusFilter] = useState(null);

  return (
    <div className="history-page">
      <div className="page-header">
        <h1>Download History</h1>
        <p className="page-subtitle">View and manage all your downloads</p>
      </div>

      <div className="history-filters">
        <button
          className={`filter-btn ${statusFilter === null ? 'active' : ''}`}
          onClick={() => setStatusFilter(null)}
        >
          All
        </button>
        <button
          className={`filter-btn ${statusFilter === 'completed' ? 'active' : ''}`}
          onClick={() => setStatusFilter('completed')}
        >
          Completed
        </button>
        <button
          className={`filter-btn ${statusFilter === 'processing' ? 'active' : ''}`}
          onClick={() => setStatusFilter('processing')}
        >
          Processing
        </button>
        <button
          className={`filter-btn ${statusFilter === 'failed' ? 'active' : ''}`}
          onClick={() => setStatusFilter('failed')}
        >
          Failed
        </button>
      </div>

      <DownloadList statusFilter={statusFilter} />
    </div>
  );
}
