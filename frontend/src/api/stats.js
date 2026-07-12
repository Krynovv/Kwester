import { api } from './client';

export const fetchStats = () => api.get('/stats').then((r) => r.data);
