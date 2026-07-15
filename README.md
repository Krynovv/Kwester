# Kwester
это геймефицированный трекер задач и привычек в стиле RPG. Выполняешь квесты - получаешь опыт и игровую валюту, прокачиваешь характеристики. За полученные награды можешь купить игровые предметы и пойти одалеть босса. 

### Заходи и играй
[![Kwester](https://img.shields.io/badge/Enter_the_Realm-Kwester-black?style=for-the-badge)](https://Kwester.quest)

## Идея
+ Характеристики персонажа: Сила, Ловкость, Интелект, Фокус, Здоровье
+ Экономика: заработанные награды с квестов можно потратить на придуманное для себя действие в реальной жизни, а выповшая валюта за убийства боссов используется для специальных игровых предметов.

## Стек
### Backend:
+ FastAPI
+ SQLAlchemy + PostgreSQL
+ Alembic
+ Pydantic v2 + pydantic-settings
+ PyJWT+pwdlib
+ pytest + pytest-asyncio
### Frontend
+ React + Vite
+ React Router
+ Tailwind CSS
+ Zustand
+ axios

## Roadmap
- [x] Backend
- [x] Frontend
- [x] Основные механники 
- [ ] Чат-механика битвы с боссом, продуманная боевка
- [ ] Панель Достижений
- [ ] Улучшение системы квестов
