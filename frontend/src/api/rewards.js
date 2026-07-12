import { api } from './client';

export const fetchRewards = () => api.get('/rewards').then((r) => r.data);

export const createReward = (data) => api.post('/rewards', data).then((r) => r.data);

export const purchaseReward = (rewardId) =>
  api.post(`/rewards/${rewardId}/purchase`).then((r) => r.data);

export const deleteReward = (rewardId) => api.delete(`/rewards/${rewardId}`);
