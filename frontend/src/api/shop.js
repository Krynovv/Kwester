import { api } from './client';

export const fetchShopItems = () => api.get('/shop').then((r) => r.data);

export const purchaseShopItem = (itemKey) =>
  api.post(`/shop/${itemKey}/purchase`).then((r) => r.data);
