# Вкладка инспектора активности процессов (Process Intelligence & Activity Deep Dive)

## 📋 Описание модуля
Модуль веб-интерфейса инспектора активности процессов (`processes_load_inspector_tab`), доступный по адресу `http://127.0.0.1:8001/tc#tab-processes-load-inspector`.

Построен на архитектурном принципе **Process Intelligence** с гарантированным разрешением проблемы **PID Recycling** (переиспользование PID операционной системой Windows) за счет уникальной пары `(pid, start_time)` и уникального ключа `instance_id`.

---

## 7 Функциональных виджетов интерфейса

1. **Панель выбора и профиля инстанса (Instance Header & Selector Bar)**:
   - Быстрый поиск и выбор процессов с переключателем «Активные процессы» / «История завершенных».
   - Карточка профиля: имя, PID, `instance_id`, статус (`RUNNING`, `EXITED`, `SUSPENDED`), время запуска (`start_time`), время работы (`Uptime`), пользователь, уровень целостности UAC (`IntegrityLevel`), полная командная строка.

2. **Метрики ресурсоемкости в реальном времени (Real-Time Metrics Charts)**:
   - 4 синхронизированных интерактивных графика (интервалы: 1 мин, 5 мин, 1 час, 24 часа):
     - **ЦП (CPU Utilization)**: общая нагрузка %, User Mode %, счетчик потоков.
     - **Память (RAM Profile)**: Working Set (МБ), Private Bytes (МБ), Page Faults/сек.
     - **Графический процессор (GPU & VRAM)**: нагрузка GPU % и использование видеопамяти VRAM.
     - **Дисковый I/O**: скорость чтения/записи (КБ/с) и количество операций ввода-вывода (IOPS).

3. **Иерархическое дерево происхождения (Process Lineage & Hierarchy Graph)**:
   - Интерактивный граф предков и потомков на основе `parent_instance_id`. Клик по любому узлу мгновенно переключает весь интерфейс на анализ выбранного процесса.

4. **Таблица сетевых сокетов и соединений (Network Sockets Panel)**:
   - Список открытых сокетов инстанса: протокол (TCP/UDP), локальный адрес $\rightarrow$ удаленный сервер, статус соединения, GeoIP/DNS.

5. **Лента файловых операций (File Events Feed)**:
   - Журнал дисковых операций процесса: время, действие (`CREATE`, `MODIFY`, `DELETE`, `RENAME`), путь к файлу, затронутый объем данных.

6. **Панель дескрипторов ОС и системных ресурсов (Handles & GUI Objects)**:
   - Количество открытых дескрипторов (Handles), объектов GDI (кисти, шрифты, битмапы) и USER (окна, меню), детектор риска утечек ресурсов.

7. **Панель безопасного администрирования (SafeOps Action Panel)**:
   - Завершение процесса (`Kill Process` с подтверждением диалоговым окном).
   - Приостановка и возобновление потоков (`Suspend / Resume`).
   - Снятие дампа памяти (`Create Memory Dump`).
   - Изменение класса приоритета CPU (`Set Priority Class`: Idle, Below Normal, Normal, Above Normal, High, Realtime).

---

## 🛠️ Спецификация REST API Контрактов

- `GET /api/v1/telemetry/instances/active` — список всех активных инстансов процессов.
- `GET /api/v1/telemetry/instances/history` — история завершенных инстансов.
- `GET /api/v1/telemetry/instances/{instance_id}` — паспорт и текущий статус инстанса.
- `GET /api/v1/telemetry/instances/{instance_id}/samples` — временной ряд метрик (CPU, RAM, GPU, IO).
- `GET /api/v1/telemetry/instances/{instance_id}/lineage` — дерево предков и потомков инстанса.
- `GET /api/v1/telemetry/instances/{instance_id}/file-activity` — файловые события инстанса.
- `GET /api/v1/telemetry/instances/{instance_id}/sockets` — открытые сокеты и сетевые соединения.
- `POST /api/v1/telemetry/instances/{instance_id}/action` — выполнение безопасных действий SafeOps.
