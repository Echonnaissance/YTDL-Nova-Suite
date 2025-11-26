import { create } from 'zustand';

const useDownloadStore = create((set, get) => ({
  // State
  downloads: [],
  activeDownloads: [],
  loading: false,
  error: null,

  // Actions
  setDownloads: (downloads) => set({ downloads }),

  setActiveDownloads: (activeDownloads) => set({ activeDownloads }),

  addDownload: (download) => set((state) => ({
    downloads: [download, ...state.downloads]
  })),

  updateDownload: (id, updates) => set((state) => ({
    downloads: state.downloads.map((d) =>
      d.id === id ? { ...d, ...updates } : d
    ),
    activeDownloads: state.activeDownloads.map((d) =>
      d.id === id ? { ...d, ...updates } : d
    )
  })),

  removeDownload: (id) => set((state) => ({
    downloads: state.downloads.filter((d) => d.id !== id),
    activeDownloads: state.activeDownloads.filter((d) => d.id !== id)
  })),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  // Get download by ID
  getDownloadById: (id) => {
    const state = get();
    return state.downloads.find((d) => d.id === id);
  }
}));

export default useDownloadStore;
