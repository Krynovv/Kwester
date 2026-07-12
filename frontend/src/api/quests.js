import { api } from './client';

export const fetchQuests = () => api.get('/quest').then((r) => r.data);

export const createQuest = (data) => api.post('/quest', data).then((r) => r.data);

export const completeQuest = (questId) =>
  api.post(`/quest/${questId}/complete`).then((r) => r.data);

export const deleteQuest = (questId) => api.delete(`/quest/${questId}`);
