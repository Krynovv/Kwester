import { api } from './client';

export const fetchBossStatus = () => api.get('/boss/status').then((r) => r.data);

export const fightBoss = (consumables = []) =>
  api.post('/boss/fight', { consumables }).then((r) => r.data);
