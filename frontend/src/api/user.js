import { api } from './client';

export const uploadAvatar = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/users/me/avatar', formData).then((r) => r.data);
};
