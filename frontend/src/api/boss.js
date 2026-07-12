import { api } from './client';

export const fetchBossStatus = () => api.get('/boss/status').then((r) => r.data);

export const fightBoss = () => api.post('/boss/fight').then((r) => r.data);
