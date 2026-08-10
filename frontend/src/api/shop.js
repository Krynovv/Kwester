import { api } from './client';

export const fetchShopItems = () => api.get('/shop').then((r) => r.data);

export const purchaseShopItem = (itemKey) =>
  api.post(`/shop/${itemKey}/purchase`).then((r) => r.data);

export const applyShopItem = (itemKey) =>
  api.post(`/shop/${itemKey}/use`).then((r) => r.data);
