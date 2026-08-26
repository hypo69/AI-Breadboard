# Telegram Mini App

## Настройка

### 1. Создание бота

1. Откройте @BotFather в Telegram
2. Создайте нового бота: `/newbot`
3. Получите токен бота

### 2. Настройка .env

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 3. Настройка config.json

```json
{
  "tg_mini_app": {
    "url": "https://your-domain.com/tgmini",
    "name": "ai-assistant",
    "description": "AI Assistant with media player"
  }
}
```

## Использование

### 1. Запуск Mini App

1. Откройте Telegram
2. Найдите вашего бота
3. Нажмите меню → Запустить Mini App

### 2. Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск Mini App |
| `/help` | Справка |
| `/status` | Статус плеера |

## Разработка

### Структура

```
webinterface/tgmini/
├── index.html
├── main.js
└── style.css
```

### Подключение SDK

```html
<script src="https://telegram.org/js/telegram-web-app.js"></script>
```

### Использование SDK

```javascript
const tg = window.Telegram.WebApp;

tg.expand(); // Раскрыть на весь экран
tg.HapticFeedback.impactOccurred('light'); // Тактильная отдача
```

---

[← Gemini](gemini.md) | [Remote Control →](rc.md)