# 💬 Плагин WhatsApp (WhatsApp Messenger Plugin)

Модульный плагин для интеграции платформы AI Breadboard с мессенджером WhatsApp.
Позволяет отправлять текстовые сообщения, оповещения, превью входящей почты и отчеты в чаты WhatsApp.

---

## 📋 Поддерживаемые провайдеры

Плагин поддерживает несколько режимов и провайдеров интеграции:

1. **Meta WhatsApp Cloud API (Graph API)** — официальный облачный REST API от Meta:
   - `WHATSAPP_TOKEN` / `access_token`: Bearer токен доступа Meta Graph API.
   - `WHATSAPP_PHONE_NUMBER_ID` / `phone_number_id`: Идентификатор телефонного номера в Meta Business Manager.
2. **Green API** — популярный шлюз для отправки сообщений в WhatsApp:
   - `GREEN_API_INSTANCE_ID` / `instance_id`
   - `GREEN_API_TOKEN` / `api_token`
3. **Generic Webhook** — отправка POST-запросов на любой пользовательский вебхук/шлюз.

---

## ⚙️ Конфигурация

Параметры могут быть заданы через:
- Файл `plugins/user-plugins/whatsapp/config.json`
- Файл секретов `secrets.json` в директории плагина
- Переменные окружения: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_RECIPIENT_DEFAULT`

### Пример `config.json`
```json
{
  "provider": "cloud_api",
  "phone_number_id": "",
  "api_version": "v18.0",
  "default_recipient": "",
  "timeout": 15
}
```

---

## 🛠️ Действия плагина (Actions)

- `send_message(to, message)`: Отправка текстового сообщения на указанный номер (в международном формате, например `+79991234567` или `79991234567`).
- `send_email_alert(to, email_data)`: Форматирование и отправка оповещения о новом входящем письме.
- `test_connection()`: Проверка доступности и валидности учетных данных API.
