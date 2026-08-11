import { api } from './client';

export const fetchBossStatus = () => api.get('/boss/status').then((r) => r.data);

// 404 значит "нет активного боя" — это нормальное состояние, не ошибка.
export const fetchActiveFight = () =>
  api.get('/boss/fight').then((r) => r.data).catch((err) => {
    if (err.response?.status === 404) return null;
    throw err;
  });

export const fightBoss = (consumables = []) =>
  api.post('/boss/fight', { consumables }).then((r) => r.data);

export const takeTurn = (action) =>
  api.post('/boss/fight/turn', { action }).then((r) => r.data);
