# Техническое задание: Асинхронная многоскоростная архитектура сбора телеметрии и адаптивного управления интервалами (Multi-Rate Decoupled Telemetry Engine)

## 1. Назначение и базовые архитектурные принципы

Настоящее техническое задание определяет требования к архитектуре, алгоритмам и порядку реализации подсистемы сбора телеметрии **Multi-Rate Decoupled Telemetry Engine** в составе платформы **AI-Breadboard Windows Diagnostic & Administration Center**.

### Ключевые архитектурные принципы

* **Zero-Delay Startup (Мгновенный запуск)**: Служба телеметрии обязана выходить в рабочий режим за время не более **2 миллисекунд**. Инициализация тяжелых системных компонентов (WMI, COM, опрос физической памяти SPD) выносится из стартового блокирующего потока в отложенную асинхронную задачу.
* **Non-Blocking Core Loop (Гарантированная плавность главного тика)**: Главный цикл Real-Time сбора (Level 3) исполняется строго по таймеру и использует только высокоскоростные нативные C-FFI вызовы (`iphlpapi.dll`, `ReadDirectoryChangesW`, `psutil`). Категорически запрещаются вызовы WMI, COM или синхронные дисковые IOCTL внутри главного тика.
* **Multi-Rate Decoupling (Многоскоростное разделение контуров)**: Сбор параметров системы расщепляется на 4 изолированные асинхронные задачи (`asyncio.Task`), исполняемые параллельно с независимыми интервалами и приоритетами.
* **Executor Thread-Offloading (Защита GIL Event Loop)**: Все синхронные, потенциально зависающие или длительные операции сбора (WMI, SMART, опрос аккумулятора) исполняются в отдельном пуле потоков через `loop.run_in_executor(None, ...)`.

---

## 2. Четырехуровневая классификация параметров и регламент сбора

### 2.1 Уровень 3: Главный Real-Time контур (Main Tick & Event-Driven)
* **Приоритет**: Высший (Критический).
* **Регламент сбора**: **Строго 1.0 секунда** (для ресурсов и сокетов) / **0 миллисекунд / Event-Driven** (для файловых операций).
* **Механизм исполнения**: Нативный цикл `_main_realtime_tick_loop()` на C-FFI и Win32 API.
* **Состав собираемых метрик**:
  1. **Попроцессные метрики по PID**: Процент загрузки CPU, утилизация Private Bytes и Working Set, использование VRAM (D3DKMT), количество активных потоков, системных хэндлов и GUI-объектов (`GDI & USER Objects`).
  2. **Сетевая активность и сокеты по PID**: Маппинг PID на открытые TCP/UDP сокеты через `GetExtendedTcpTable` / `GetExtendedUdpTable` (`iphlpapi.dll`), локальные/удаленные IP-адреса, порты, статусы соединений (`ESTABLISHED`, `LISTEN`) и дифференциальный трафик.
  3. **Мониторинг выбранных директорий**: Асинхронный перехват событий создания (`CREATE`), изменения (`MODIFY`), удаления (`DELETE`) и переименования (`RENAME`) файлов в отслеживаемых каталогах через Win32 `ReadDirectoryChangesW` и провайдер ETW `Microsoft-Windows-Kernel-File`.

### 2.2 Уровень 0: Отложенный статический паспорт системы (Deferred Static Inventory)
* **Приоритет**: Высокий (Фоновый однократный).
* **Регламент сбора**: **Однократно при старте** (или по сигналу PnP / кнопке `force_refresh` в UI).
* **Порядок запуска**: Задача запускается асинхронно **СТРОГО ПОСЛЕ** того, как главный Real-Time цикл (Level 3) запущен и успешно выполнил свой первый тик (пауза 200 мс после старта).
* **Механизм исполнения**: Выполняется в фоновом пуле потоков `loop.run_in_executor(None, self._heavy_wmi_hardware_probe)`.
* **Состав собираемых метрик**:
  1. **Паспорт процессора**: Модель, микроархитектура, количество физических ядер и логических потоков, объемы L1/L2/L3 кэшей.
  2. **Модули оперативной памяти (RAM SPD)**: Производитель, партийные номера планок, физическая частота МГц, тип памяти (DDR4/DDR5), конфигурация каналов.
  3. **Спецификация GPU**: Полное название видеокарты, идентификаторы Vendor/Device ID, физический объем VRAM, ширина шины PCIe.
  4. **Паспорт накопителей и томов**: Модели SSD/HDD, серийные номера устройств, типы файловых систем (NTFS, ReFS), буквы разделов и метки томов.
  5. **Идентификация хоста**: Имя ПК, SID пользователя, Build и редакция ОС, дата установки Windows, часовой пояс, раскладки клавиатуры, параметры подключенных мониторов (EDID).

### 2.3 Уровень 2: Адаптивная динамическая телеметрия (Adaptive Sensors)
* **Приоритет**: Средний (Адаптивный).
* **Регламент сбора**: **Плавающий интервал от 500 мс до 30.0 секунд**.
* **Алгоритм управления (Adaptive Delta-Triggered Polling)**:
  * Вводятся зоны нечувствительности (**Deadband**) для предотвращения реакций на фоновый шум:
    * Температура: `±1.0 °C`
    * Загрузка CPU: `±3.0 %`
    * Частота CPU/GPU: `±50 МГц`
    * Мощность: `±2.0 Вт`
    * Обороты кулеров: `±100 RPM`
  * **Реакция на всплеск (Trigger-Up)**: Если хотя бы один параметр превышает порог Deadband за время замера, интервал опроса **мгновенно сбрасывается до 500 мс**.
  * **Задержка остывания (Cooldown)**: Высокая частота сбора (500 мс) удерживается минимум 10 тиков после прекращения роста параметров для детальной фиксации профиля остывания.
  * **Замедление при штиле (Exponential Back-Off)**: При отсутствии изменений интервал опроса плавно увеличивается в 1.5 раза с каждым тиком вплоть до верхнего лимита **30 секунд**.

### 2.4 Уровень 1: Низкочастотный фоновый опрос (Low-Frequency Heavy)
* **Приоритет**: Низкий (Фоновый периодический).
* **Регламент сбора**: **От 15 минут до 12 часов**.
* **Механизм исполнения**: Фоновый вызов через `run_in_executor` с задержкой старта на 5 секунд после запуска приложения.
* **Состав собираемых метрик**:
  1. **S.M.A.R.T. здоровье SSD/NVMe**: TBW, Wear Level %, Power-On Hours, счетчики ошибок — **1 раз в 12 часов**.
  2. **Износ аккумулятора**: Design Capacity, Full Charge Capacity, количество циклов — **1 раз в 15–30 минут**.
  3. **Аудит безопасности и патчей**: Состояние UAC, брандмауэра, баз Defender, список KB — **1 раз в 1–4 часа**.
  4. **Реестр служб SCM и задач Планировщика**: **1 раз в 30 минут**.

---

## 3. Архитектура асинхронного планировщика (`TelemetryEngine`)

Управление процессом сбора осуществляется центральным классом `TelemetryEngine`:

```python
import asyncio
import time
from logger import logger

class TelemetryEngine:
    def __init__(self):
        self.is_running = False
        self.static_inventory_loaded = False
        self.static_catalog = {}

    async def start(self):
        """Единая точка входа запуска службы телеметрии."""
        self.is_running = True
        logger.info("[TelemetryEngine] Запуск асинхронного ядра телеметрии...")

        # 1. ЗАПУСКАЕМ ГЛАВНЫЙ REAL-TIME ЦИКЛ (LEVEL 3)
        # Начинает работу мгновенно (< 2 мс) без тяжелых блокировок
        main_tick_task = asyncio.create_task(
            self._main_realtime_tick_loop(), 
            name="MainRealtimeTickTask"
        )

        # 2. ОТЛОЖЕННЫЙ ЗАПУСК СТАТИЧЕСКОГО ИНВЕНТАРЯ (LEVEL 0)
        # Запускается асинхронно СТРОГО ПОСЛЕ старта главного цикла
        asyncio.create_task(
            self._deferred_static_inventory_task(), 
            name="DeferredStaticInventoryTask"
        )

        # 3. ФОНОВЫЕ АСИНХРОННЫЕ ТАСКИ (LEVELS 1 & 2)
        asyncio.create_task(
            self._adaptive_sensors_loop(), 
            name="AdaptiveSensorsTask"
        )
        asyncio.create_task(
            self._low_frequency_background_loop(), 
            name="LowFrequencyTask"
        )

        await main_tick_task

    async def _main_realtime_tick_loop(self):
        """Главный высокоприоритетный тик: PID, сокеты, файловый I/O.
        
        СТРОГОЕ ПРАВИЛО: Никаких WMI, COM, heavy IOCTL или синхронных блокировок!
        """
        logger.info("[MainTick] 🚀 Главный Real-Time контур успешно запущен!")
        tick_count = 0

        while self.is_running:
            t0 = time.perf_counter()
            tick_count += 1

            try:
                # Нативные C-FFI вызовы (iphlpapi.dll, ReadDirectoryChangesW, psutil)
                await self._collect_pid_metrics_fast()
                await self._collect_network_sockets_fast()
                
            except Exception as e:
                logger.error(f"[MainTick] Ошибка в главном тике #{tick_count}: {e}", exc_info=True)

            dt = time.perf_counter() - t0
            sleep_time = max(0.05, 1.0 - dt)
            await asyncio.sleep(sleep_time)

    async def _deferred_static_inventory_task(self):
        """Собирается 1 раз при старте, но СТРОГО ПОСЛЕ запуска основного процесса."""
        await asyncio.sleep(0.2) # Пауза для выполнения первого главного тика
        
        logger.info("[Level-0] 🔍 Начало фонового сбора статического паспорта системы...")
        t0 = time.perf_counter()

        # Тяжелый опрос WMI выносится в ThreadPoolExecutor для защиты Event Loop
        loop = asyncio.get_running_loop()
        self.static_catalog = await loop.run_in_executor(None, self._heavy_wmi_hardware_probe)

        self.static_inventory_loaded = True
        dt = time.perf_counter() - t0
        logger.info(f"[Level-0] ✅ Паспорт системы сформирован за {dt:.2f}s и сохранен в памяти.")

    def _heavy_wmi_hardware_probe(self) -> dict:
        """Синхронный тяжелый опрос WMI, SPD памяти, серийников дисков."""
        return {
            "cpu_model": "AMD Ryzen 9 5900X",
            "ram_spd": ["DDR4 3600MHz Kingston", "DDR4 3600MHz Kingston"],
            "disks_passport": ["Samsung NVMe 980 PRO 1TB"],
            "os_build": "Windows 11 Pro 22H2"
        }

    async def _adaptive_sensors_loop(self):
        """Адаптивные сенсоры: 500 мс при всплеске <-> 30 сек при штиле."""
        await asyncio.sleep(0.5)
        current_interval = 2.0

        while self.is_running:
            try:
                has_spike = await self._poll_sensors_and_check_spikes()
                if has_spike:
                    current_interval = 0.5  # Реактивный сброс
                else:
                    current_interval = min(30.0, current_interval * 1.5) # Экспоненциальное замедление
            except Exception as e:
                logger.error(f"[AdaptiveSensors] Ошибка: {e}")

            await asyncio.sleep(current_interval)

    async def _low_frequency_background_loop(self):
        """Низкочастотные фоновые задачи: SMART (12ч), Аккумулятор (15мин)."""
        await asyncio.sleep(5.0)

        while self.is_running:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._poll_smart_and_battery)
            except Exception as e:
                logger.error(f"[LowFreq] Ошибка: {e}")

            await asyncio.sleep(900) # 15 минут

    async def _collect_pid_metrics_fast(self):
        await asyncio.sleep(0.001)

    async def _collect_network_sockets_fast(self):
        await asyncio.sleep(0.001)

    async def _poll_sensors_and_check_spikes(self) -> bool:
        return False

    def _poll_smart_and_battery(self):
        pass
```

---

## 4. Оптимизация записи в БД SQLite и дедупликация

1. **Дедупликация записью в БД (Deadband Filtering)**:
   * Новая строка в таблицу `sensor_polls` базы данных `telemetry.db` записывается **только при выходе параметра за границы Deadband** относительно последней записанной строки.
   * Для предотвращения пробелов во временных рядах при длительном штиле принудительно записывается контрольный кадр (**Heartbeat**) 1 раз в 60 секунд.
2. **Пакетный сброс (Batch WAL Writer)**:
   * Все метрики Level 3 и Level 2 заносятся в кольцевой буфер RAM и сбрасываются единой транзакцией (`BEGIN IMMEDIATE ... COMMIT`) раз в 5 секунд.

---

## 5. Критерии приемки и метрики эффективности (KPI)

1. **Время старта службы**: Менее **2 миллисекунд** до начала сбора первых снимков PID в Level 3.
2. **Отсутствие задержек в главном тике**: Стандартное отклонение интервала главного тика (1.0 с) не должно превышать ±5 мс.
3. **Нагрузка на CPU в режиме штиля**: Менее **0.2%** от общего ресурса процессора.
4. **Сокращение объема базы данных**: Сокращение дисковых записей в WAL-журнал `telemetry.db` не менее чем в **8–10 раз** по сравнению с непрерывным односекундным опросом.
