import { api } from './api';

export const downloadService = {
  // Create a new download
  createDownload: async (request) => {
    const response = await api.post('/api/downloads/', request);
    return response.data;
  },

  // Get all downloads with optional filters
  getAllDownloads: async (params = {}) => {
    const { skip = 0, limit = 50, status } = params;
    const queryParams = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString()
    });
    if (status) {
      queryParams.append('status', status);
    }
    const response = await api.get(`/api/downloads/?${queryParams}`);
    return response.data;
  },

  // Get active downloads only
  getActiveDownloads: async () => {
    const response = await api.get('/api/downloads/active');
    return response.data;
  },

  // Get a single download by ID
  getDownload: async (id) => {
    const response = await api.get(`/api/downloads/${id}`);
    return response.data;
  },

  // Get download statistics
  getStats: async () => {
    const response = await api.get('/api/downloads/stats');
    return response.data;
  },

  // Delete a download record
  deleteDownload: async (id) => {
    const response = await api.delete(`/api/downloads/${id}`);
    return response.data;
  },

  // Cancel an active download
  cancelDownload: async (id) => {
    const response = await api.post(`/api/downloads/${id}/cancel`);
    return response.data;
  },

  // Retry a failed download
  retryDownload: async (id) => {
    const response = await api.post(`/api/downloads/${id}/retry`);
    return response.data;
  },

  // Get video info without downloading
  getVideoInfo: async (url) => {
    const response = await api.post('/api/downloads/video-info', { url });
    return response.data;
  },

  // Get playlist info without downloading
  getPlaylistInfo: async (url) => {
    const response = await api.post('/api/downloads/playlist-info', { url });
    return response.data;
  },

  // Create batch downloads
  createBatchDownloads: async (requests) => {
    const response = await api.post('/api/downloads/batch', requests);
    return response.data;
  },

  // Check backend health
  checkHealth: async () => {
    const response = await api.get('/api/health');
    return response.data;
  }
};

export default downloadService;
