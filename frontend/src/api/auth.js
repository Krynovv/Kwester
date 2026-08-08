import { api } from './client';

export const registerUser = (data) => api.post('/auth/register', data);

export const loginUser = async (username, password) => {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const res = await api.post('/auth/token', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return res.data;
};

export const fetchMe = () => api.get('/users/me').then((r) => r.data);

export const refreshTokens = (refreshToken) =>
  api.post('/auth/refresh', { refresh_token: refreshToken }).then((r) => r.data);

export const logoutRequest = (refreshToken) =>
  api.post('/auth/logout', { refresh_token: refreshToken });
