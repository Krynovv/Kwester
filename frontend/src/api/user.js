import { api } from './client';

export const updateMe = (data) => api.patch('/users/me', data).then((r) => r.data);

export const uploadAvatar = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/users/me/avatar', formData).then((r) => r.data);
};
