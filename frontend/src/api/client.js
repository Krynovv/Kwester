import axios from 'axios'
import { useAuthStore } from '../store/authStore'

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function forceLogout() {
  useAuthStore.getState().logout({ silent: true });
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

// Гарантирует, что параллельные 401 не устроят гонку из нескольких /auth/refresh.
let refreshPromise = null;

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const { config, response } = err;
    const isAuthEndpoint = config?.url?.startsWith('/auth/');

    if (response?.status !== 401 || isAuthEndpoint || config._retry) {
      if (response?.status === 401 && !isAuthEndpoint) forceLogout();
      return Promise.reject(err);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      forceLogout();
      return Promise.reject(err);
    }

    config._retry = true;
    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
          .then((res) => res.data)
          .finally(() => { refreshPromise = null; });
      }
      const data = await refreshPromise;
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      config.headers.Authorization = `Bearer ${data.access_token}`;
      return api(config);
    } catch (refreshErr) {
      forceLogout();
      return Promise.reject(refreshErr);
    }
  }
);

