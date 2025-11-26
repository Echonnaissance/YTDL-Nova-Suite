import { api } from './api';

export const settingsService = {
  // Get user settings
  getSettings: async () => {
    const response = await api.get('/api/settings/');
    return response.data;
  },

  // Update user settings
  updateSettings: async (settings) => {
    const response = await api.patch('/api/settings/', settings);
    return response.data;
  }
};

export default settingsService;
