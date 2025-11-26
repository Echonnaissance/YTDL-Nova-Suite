import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useSettingsStore = create(
  persist(
    (set) => ({
      // State
      theme: 'dark',
      defaultDownloadType: 'video',
      defaultQuality: 'best',
      defaultVideoFormat: 'mp4',
      defaultAudioFormat: 'm4a',
      embedThumbnail: true,
      notifications: true,

      // Actions
      setTheme: (theme) => set({ theme }),

      setDefaultDownloadType: (type) => set({ defaultDownloadType: type }),

      setDefaultQuality: (quality) => set({ defaultQuality: quality }),

      setDefaultVideoFormat: (format) => set({ defaultVideoFormat: format }),

      setDefaultAudioFormat: (format) => set({ defaultAudioFormat: format }),

      setEmbedThumbnail: (embed) => set({ embedThumbnail: embed }),

      setNotifications: (enabled) => set({ notifications: enabled }),

      resetSettings: () => set({
        theme: 'dark',
        defaultDownloadType: 'video',
        defaultQuality: 'best',
        defaultVideoFormat: 'mp4',
        defaultAudioFormat: 'm4a',
        embedThumbnail: true,
        notifications: true
      })
    }),
    {
      name: 'youtube-downloader-settings'
    }
  )
);

export default useSettingsStore;
