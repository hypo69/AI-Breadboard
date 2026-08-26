# Пульт дистанционного управления

## Возможности

- Голосовое управление
- Speech-to-Text (STT)
- Text-to-Speech (TTS)
- Управление плеером в реальном времени

## Настройка

### 1. Браузерные разрешения

Разрешите использование микрофона в настройках браузера.

### 2. Язык распознавания

Выберите язык в настройках пульта (по умолчанию: Russian).

## Использование

### Голосовые команды

| Команда | Действие |
|---------|----------|
| "Включи Титаник" | Запустить воспроизведение |
| "Поставь на паузу" | Пауза |
| "Продолжай" | Возобновить |
| "Следующий файл" | Следующий трек |
| "Громкость на 80" | Установить громкость |

## Технологии

### Speech-to-Text

```javascript
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'ru-RU';
```

### Text-to-Speech

```javascript
const utterance = new SpeechSynthesisUtterance(text);
utterance.lang = 'ru-RU';
window.speechSynthesis.speak(utterance);
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:3000/api/control/ws?role=remote');
```

---

[← Telegram Mini App](tgmini.md) | [Troubleshooting →](../troubleshooting.md)