// Telegram Mini App SDK — доступен, только когда приложение открыто через
// web_app-кнопку бота (обычная ссылка, открытая в браузере Telegram, SDK не
// подключает). Вне Telegram window.Telegram нет вовсе — все вызовы ниже
// опциональны, чтобы обычная разработка в браузере не ломалась.
const CYBER_BG = '#0a0a0f'

export function initTelegramWebApp() {
  const tg = window.Telegram?.WebApp
  if (!tg) return

  tg.ready()
  tg.expand()

  // Сам системный хедер (название "Kvvester", крестик, троеточие) Telegram
  // не даёт стилизовать вообще — можно перекрасить только его фон и фон
  // подложки под вьюпортом. Красим в cyber-bg, чтобы не было светлого шва
  // над тёмной темой приложения. setHeaderColor с произвольным hex
  // поддерживают не все версии клиента — старые бросают исключение,
  // поэтому оборачиваем в try/catch, а не в isVersionAtLeast (сама SDK
  // хранит список умений неполно и по-разному в разных сборках клиента).
  try {
    tg.setHeaderColor(CYBER_BG)
  } catch {
    // старый клиент Telegram — просто оставляем дефолтный хедер
  }
  try {
    tg.setBackgroundColor(CYBER_BG)
  } catch {
    // аналогично
  }

  try {
    tg.disableVerticalSwipes()
  } catch {
    // смахивание вниз для закрытия — не критично, если недоступно
  }
}
