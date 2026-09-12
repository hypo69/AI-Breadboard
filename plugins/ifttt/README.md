# IFTTT Smart Home Plugin (`plugins/ifttt`)

The **IFTTT Smart Home Plugin** connects AI Breadboard to the **IFTTT (If This Then That) Webhooks Maker Service**, enabling bidirectional smart home automation, appliance dispatching, and security alerts.

---

## 🌟 Capabilities

- **Device & Routine Dispatching:** Trigger custom IFTTT Webhook applets to control smart lighting (Philips Hue, Yeelight, Tuya), climate (Nest, Sensibo, Tado), robot vacuums (Roomba, Roborock), and smart power plugs.
- **AI Tool Integration:** Exposes `trigger_ifttt_event` function calling tool for AI agents and chat models.
- **Admin Panel UI:** Test connections and trigger events directly from the AI Breadboard Admin UI (`/admin`).
- **Flexible Parameters:** Supports standard parameters (`value1`, `value2`, `value3`) and complex JSON payloads (`json_payload`).

---

## ⚙️ Configuration

### 1. Environment Variable (`.env`)
Obtain your Maker Webhooks key from [IFTTT Webhooks Documentation](https://ifttt.com/maker_webhooks):
```env
IFTTT_WEBHOOK_KEY=your_secret_ifttt_maker_key
```

### 2. Plugin Configuration (`plugins/ifttt/config.json`)
```json
{
    "webhook_key": "${IFTTT_WEBHOOK_KEY}",
    "timeout_seconds": 10,
    "default_events": {
        "movie_mode": "movie_mode",
        "lights_on": "living_room_lights_on",
        "lights_off": "living_room_lights_off",
        "ac_cool": "ac_cool"
    }
}
```

---

## 🚀 Usage

### Programmatic Python API
```python
from plugins.ifttt import send_ifttt_event, IFTTTClient

# Using convenience helper
result = await send_ifttt_event(
    event_name="living_room_lights_on",
    value1="warm_white",
    value2="80%",
)
print(result)

# Using client
client = IFTTTClient()
res = await client.trigger_event("movie_mode")
```

### Admin Actions
- `test_connection`: Pings IFTTT Maker Webhooks to verify API key validity.
- `trigger_event`: Dispatches an arbitrary event with `event_name` and parameters.

---

## 📁 File Structure

- `__init__.py`: Plugin factory `plugin()` and exports.
- `plugin.py`: `IFTTTPlugin` inheriting from `BasePlugin`.
- `client.py`: Async `IFTTTClient` connector.
- `config.json`: Default configuration and predefined events.
- `README.md`: English documentation and guide.
