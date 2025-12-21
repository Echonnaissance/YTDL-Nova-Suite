/**
 * API Client
 * Centralized axios instance for making API calls to the backend
 */
import axios from 'axios'

// Create axios instance with default config
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth tokens, etc.
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors globally
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Retry/backoff for 429 Too Many Requests
    try {
      const config = error.config;
      if (config) {
        // Defaults
        const DEFAULT_MAX_RETRIES = 3;
        config.__retryCount = config.__retryCount || 0;

        const status = error.response ? error.response.status : null;
        if (status === 429 && config.__retryCount < DEFAULT_MAX_RETRIES) {
          config.__retryCount += 1;

          // Honor Retry-After header if present
          let delayMs = 1000 * Math.pow(2, config.__retryCount - 1); // 1s,2s,4s
          const raHeader = error.response.headers
            ? error.response.headers['retry-after'] || error.response.headers['Retry-After']
            : null;
          if (raHeader) {
            const ra = parseInt(raHeader, 10);
            if (!isNaN(ra) && ra > 0) {
              delayMs = ra * 1000;
            }
          }

          // Add small jitter
          delayMs = delayMs + Math.floor(Math.random() * 300);

          await new Promise((res) => setTimeout(res, delayMs));
          return api(config);
        }
      }
    } catch (e) {
      // fall through to default handler
      console.error('Retry handler error:', e);
    }

    // Fallback: existing global logging
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.message);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api
