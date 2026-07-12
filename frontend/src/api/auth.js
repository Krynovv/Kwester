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
