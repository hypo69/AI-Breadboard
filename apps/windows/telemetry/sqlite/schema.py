# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry Sqlite - Schema
# =============================================================================
# Description:
#   Схема таблиц, индексов и миграций SQLite базы данных системной телеметрии.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.sqlite.schema import init_database_schema
#
#     init_database_schema(connection)
#
# File: schema.py
# Project: ai-breadboard
# Package: apps.windows.telemetry.sqlite
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 04:25:00
# =============================================================================

from __future__ import annotations

"""Схема таблиц, индексов и процедур миграции базы данных телеметрии SQLite."""

import sqlite3
from typing import Set

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def init_database_schema(conn: sqlite3.Connection) -> None:
    """Инициализирует таблицы, индексы и выполняет миграции для базы данных телеметрии.

    Args:
        conn: Активное подключение к базе данных SQLite.
    """
    cursor = conn.cursor()

    # 1. Системные снимки (основная таблица метрик)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            hostname TEXT,
            username TEXT,
            uptime_seconds REAL,
            os_name TEXT,
            os_build TEXT,
            os_install_date TEXT,
            system_language TEXT,
            os_install_language TEXT,
            user_locale TEXT,
            system_locale TEXT,
            timezone TEXT,
            codepage TEXT,
            input_languages_json TEXT,
            disks_json TEXT,
            physical_disks_json TEXT,
            monitors_json TEXT,
            updates_json TEXT,
            office_json TEXT,
            onedrive_json TEXT,
            battery_json TEXT,
            ram_sticks_json TEXT,
            listening_ports_json TEXT,
            alerts_json TEXT,
            cpu_total_percent REAL,
            cpu_frequency_mhz REAL,
            memory_total_gb REAL,
            memory_used_gb REAL,
            memory_percent REAL,
            swap_percent REAL,
            gpu_load_percent REAL,
            gpu_temp_c REAL,
            disk_read_bytes_sec REAL,
            disk_write_bytes_sec REAL,
            disk_read_count_sec REAL,
            disk_write_count_sec REAL,
            network_sent_bytes_sec REAL,
            network_recv_bytes_sec REAL,
            hardware_audit TEXT,
            raw_json TEXT
        );
    ''')

    # 2. Сенсоры (аппаратные датчики)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            hardware_name TEXT,
            hardware_type TEXT,
            sensor_category TEXT,
            sensor_name TEXT,
            unit TEXT,
            value REAL,
            provider TEXT,
            provider_priority INTEGER DEFAULT 30,
            raw_json TEXT,
            UNIQUE(sensor_id, timestamp)
        );
    ''')

    # 3. Снимки процессов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            pid INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT,
            cpu_percent REAL,
            memory_mb REAL,
            memory_percent REAL,
            num_threads INTEGER,
            num_handles INTEGER DEFAULT 0,
            username TEXT,
            read_bytes_sec REAL,
            write_bytes_sec REAL,
            integrity_level TEXT,
            elevation INTEGER DEFAULT 0,
            ppid INTEGER,
            parent_name TEXT,
            executable TEXT,
            cmdline TEXT,
            sid TEXT,
            session_id INTEGER,
            creation_time TEXT,
            process_guid TEXT,
            ancestor_chain TEXT,
            launch_reason TEXT,
            FOREIGN KEY (snapshot_id) REFERENCES system_snapshots(id) ON DELETE CASCADE
        );
    ''')

    # 4. Происхождение и жизненный цикл процессов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_provenance_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            event_type TEXT NOT NULL,
            pid INTEGER NOT NULL,
            ppid INTEGER,
            process_guid TEXT NOT NULL,
            parent_guid TEXT,
            name TEXT NOT NULL,
            executable_path TEXT,
            command_line TEXT,
            user TEXT,
            sid TEXT,
            session_id INTEGER,
            integrity_level TEXT,
            elevation INTEGER,
            parent_name TEXT,
            parent_cmdline TEXT,
            ancestor_chain TEXT,
            launch_reason TEXT,
            source TEXT DEFAULT 'system',
            details_json TEXT,
            raw_json TEXT
        );
    ''')

    # 5. Почасовые агрегаты сенсоров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_aggregates_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            avg_value REAL,
            min_value REAL,
            max_value REAL,
            count INTEGER,
            raw_json TEXT
        );
    ''')

    # 6. Двухминутные агрегаты процессов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_rollups_2min (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            period_start_epoch REAL,
            period_end_epoch REAL,
            name TEXT NOT NULL,
            pid INTEGER,
            username TEXT,
            sample_count INTEGER NOT NULL,
            avg_cpu_percent REAL NOT NULL,
            max_cpu_percent REAL NOT NULL,
            min_cpu_percent REAL,
            avg_memory_mb REAL NOT NULL,
            max_memory_mb REAL NOT NULL,
            min_memory_mb REAL,
            avg_num_threads REAL,
            outliers_count INTEGER DEFAULT 0
        );
    ''')

    # 7. Суточные агрегаты процессов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_rollups_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            name TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            avg_cpu_percent REAL NOT NULL,
            max_cpu_percent REAL NOT NULL,
            avg_memory_mb REAL NOT NULL,
            max_memory_mb REAL NOT NULL,
            outliers_count INTEGER DEFAULT 0,
            last_seen TEXT
        );
    ''')

    # 8. Бакеты сжатия временных рядов телеметрии
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_rollups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            period_start_epoch REAL NOT NULL,
            period_end_epoch REAL NOT NULL,
            duration_seconds REAL NOT NULL,
            sample_count INTEGER NOT NULL,
            tier TEXT NOT NULL,
            cpu_avg REAL,
            cpu_min REAL,
            cpu_max REAL,
            cpu_p95 REAL,
            ram_avg_gb REAL,
            ram_min_gb REAL,
            ram_max_gb REAL,
            ram_percent_avg REAL,
            ram_percent_max REAL,
            disk_read_avg_mbs REAL,
            disk_read_max_mbs REAL,
            disk_read_total_mb REAL,
            disk_write_avg_mbs REAL,
            disk_write_max_mbs REAL,
            disk_write_total_mb REAL,
            network_rx_avg_mbs REAL,
            network_rx_max_mbs REAL,
            network_rx_total_mb REAL,
            network_tx_avg_mbs REAL,
            network_tx_max_mbs REAL,
            network_tx_total_mb REAL,
            raw_json TEXT
        );
    ''')

    # 9. Аудит оборудования
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hardware_audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            devices_count INTEGER DEFAULT 0,
            problem_devices_count INTEGER DEFAULT 0,
            outdated_drivers_count INTEGER DEFAULT 0,
            changes_count INTEGER DEFAULT 0,
            raw_json TEXT
        );
    ''')

    # 10. История перезагрузок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reboot_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boot_id TEXT UNIQUE NOT NULL,
            boot_time TEXT NOT NULL,
            previous_boot_time TEXT,
            uptime_seconds REAL,
            uptime_human TEXT,
            shutdown_type TEXT NOT NULL,
            likely_class TEXT,
            conclusion TEXT,
            initiating_process TEXT,
            initiating_user TEXT,
            shutdown_action TEXT,
            reason_text TEXT,
            reason_code INTEGER,
            bugcheck_code TEXT,
            bugcheck_params_json TEXT,
            power_button_timestamp TEXT,
            windows_update_kb TEXT,
            service_installed TEXT,
            evidence_json TEXT,
            events_chain_json TEXT,
            raw_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 11. Инциденты аномалий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            trigger_type TEXT NOT NULL,
            severity TEXT DEFAULT 'warning',
            title TEXT NOT NULL,
            description TEXT,
            trigger_metrics_json TEXT,
            suspect_processes_json TEXT,
            related_events_json TEXT,
            metrics_summary_json TEXT,
            raw_window_json TEXT
        );
    ''')

    # 12. События телеметрии
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            event_details TEXT,
            raw_json TEXT
        );
    ''')

    # 13. Опросы приложений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            app TEXT NOT NULL,
            poll_type TEXT,
            metric_name TEXT,
            value REAL,
            unit TEXT,
            status TEXT,
            details TEXT,
            raw_json TEXT
        );
    ''')

    # 14. События приложений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            app TEXT NOT NULL,
            event_type TEXT NOT NULL,
            status TEXT,
            message TEXT,
            details TEXT,
            raw_json TEXT
        );
    ''')

    # 15. Изменения параметров приложений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_param_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            app TEXT NOT NULL,
            param_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            status TEXT,
            user TEXT,
            details TEXT,
            raw_json TEXT
        );
    ''')

    # 16. Пользовательские записи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            source_file TEXT,
            payload_json TEXT
        );
    ''')

    # 17. События устройств (PnP / Device Events)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            event_type TEXT NOT NULL,
            device_instance_id TEXT,
            friendly_name TEXT,
            device_class TEXT,
            category TEXT,
            has_problem INTEGER DEFAULT 0,
            problem_code INTEGER DEFAULT 0,
            status_code INTEGER DEFAULT 0,
            manufacturer TEXT,
            flapping_count INTEGER DEFAULT 0,
            uptime_seconds REAL DEFAULT 0.0,
            raw_json TEXT
        );
    ''')

    # 18. Инвентарь устройств
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_instance_id TEXT UNIQUE NOT NULL,
            friendly_name TEXT,
            device_class TEXT,
            install_date TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 19. Системные события W64/ETW
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS w64_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            event_type TEXT,
            path TEXT,
            pid INTEGER,
            name TEXT,
            provider TEXT,
            raw_json TEXT
        );
    ''')

    # 20. Аномальные процессы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_outliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            pid INTEGER,
            name TEXT,
            status TEXT,
            cpu_percent REAL,
            memory_mb REAL,
            memory_percent REAL,
            num_threads INTEGER,
            username TEXT,
            details TEXT
        );
    ''')

    # 21. Расширенный системный аудит
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_extended_audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            hostname TEXT,
            defender_cfa_enabled INTEGER DEFAULT 0,
            defender_asr_count INTEGER DEFAULT 0,
            defender_exclusions_count INTEGER DEFAULT 0,
            defender_threats_count INTEGER DEFAULT 0,
            startup_entries_count INTEGER DEFAULT 0,
            vss_snapshots_count INTEGER DEFAULT 0,
            users_total_count INTEGER DEFAULT 0,
            users_admin_count INTEGER DEFAULT 0,
            raw_json TEXT
        );
    ''')

    # 22. Почасовые агрегаты сенсоров (telemetry_hourly)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_hourly (
            sensor_id TEXT NOT NULL,
            bucket_start INTEGER NOT NULL,
            bucket_end INTEGER NOT NULL,
            sample_count INTEGER NOT NULL,
            value_min REAL,
            value_max REAL,
            value_avg REAL,
            value_sum REAL,
            value_sum_sq REAL,
            value_stddev REAL,
            value_first REAL,
            value_last REAL,
            PRIMARY KEY (sensor_id, bucket_start)
        );
    ''')

    # 23. Суточные агрегаты сенсоров (telemetry_daily)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_daily (
            sensor_id TEXT NOT NULL,
            bucket_start INTEGER NOT NULL,
            bucket_end INTEGER NOT NULL,
            sample_count INTEGER NOT NULL,
            value_min REAL,
            value_max REAL,
            value_avg REAL,
            value_sum REAL,
            value_sum_sq REAL,
            value_stddev REAL,
            value_first REAL,
            value_last REAL,
            PRIMARY KEY (sensor_id, bucket_start)
        );
    ''')

    # 24. Недельные агрегаты сенсоров (telemetry_weekly)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_weekly (
            sensor_id TEXT NOT NULL,
            bucket_start INTEGER NOT NULL,
            bucket_end INTEGER NOT NULL,
            sample_count INTEGER NOT NULL,
            value_min REAL,
            value_max REAL,
            value_avg REAL,
            value_sum REAL,
            value_sum_sq REAL,
            value_stddev REAL,
            value_first REAL,
            value_last REAL,
            PRIMARY KEY (sensor_id, bucket_start)
        );
    ''')

    # 25. Месячные агрегаты сенсоров (telemetry_monthly)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_monthly (
            sensor_id TEXT NOT NULL,
            bucket_start INTEGER NOT NULL,
            bucket_end INTEGER NOT NULL,
            sample_count INTEGER NOT NULL,
            value_min REAL,
            value_max REAL,
            value_avg REAL,
            value_sum REAL,
            value_sum_sq REAL,
            value_stddev REAL,
            value_first REAL,
            value_last REAL,
            PRIMARY KEY (sensor_id, bucket_start)
        );
    ''')

    # 26. Годовые агрегаты сенсоров (telemetry_yearly)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_yearly (
            sensor_id TEXT NOT NULL,
            bucket_start INTEGER NOT NULL,
            bucket_end INTEGER NOT NULL,
            sample_count INTEGER NOT NULL,
            value_min REAL,
            value_max REAL,
            value_avg REAL,
            value_sum REAL,
            value_sum_sq REAL,
            value_stddev REAL,
            value_first REAL,
            value_last REAL,
            PRIMARY KEY (sensor_id, bucket_start)
        );
    ''')

    # 27. Фиксация аномальных всплесков сенсоров (telemetry_spikes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_spikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            value REAL NOT NULL,
            spike_type TEXT DEFAULT 'high',
            baseline_avg REAL,
            baseline_stddev REAL,
            details TEXT,
            raw_json TEXT
        );
    ''')

    # 28. События прямого ввода-вывода (disk_io_events / ETW / Process I/O)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disk_io_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            pid INTEGER NOT NULL,
            process_name TEXT NOT NULL,
            disk_id INTEGER NOT NULL,
            operation TEXT NOT NULL,
            bytes_count INTEGER NOT NULL,
            duration_ms REAL,
            offset INTEGER,
            file_path TEXT
        );
    ''')

    # 29. Снимки здоровья и износа накопителей (disk_health_snapshots / NVMe SMART / TBW)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disk_health_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            disk_id INTEGER NOT NULL,
            serial_number TEXT,
            model TEXT,
            bus_type TEXT,
            temperature_c REAL,
            wear_percent REAL,
            available_spare REAL,
            tbw_written_tb REAL,
            tbw_read_tb REAL,
            power_on_hours INTEGER,
            power_cycles INTEGER,
            unsafe_shutdowns INTEGER,
            media_errors INTEGER,
            error_log_entries INTEGER,
            health_status TEXT DEFAULT 'Healthy',
            raw_smart_json TEXT
        );
    ''')

    # 30. Паспорт и конфигурация физических накопителей (disk_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disk_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disk_id INTEGER NOT NULL,
            device_path TEXT NOT NULL,
            serial_number TEXT UNIQUE,
            vendor TEXT,
            product TEXT,
            revision TEXT,
            bus_type TEXT,
            media_type TEXT,
            size_bytes INTEGER,
            size_gb REAL,
            sector_size INTEGER,
            removable INTEGER DEFAULT 0,
            partition_style TEXT,
            gpt_guid TEXT,
            partitions_json TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 31. Паспорт логических томов (volume_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volume_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volume_guid TEXT UNIQUE NOT NULL,
            drive_letter TEXT,
            mount_point TEXT,
            label TEXT,
            filesystem TEXT,
            filesystem_flags INTEGER,
            cluster_size_bytes INTEGER,
            sector_size_bytes INTEGER,
            total_bytes INTEGER,
            total_gb REAL,
            disk_id INTEGER,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 32. Сэмплы производительности дисков (disk_performance_samples)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disk_performance_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            disk_name TEXT NOT NULL,
            read_bytes_sec REAL,
            write_bytes_sec REAL,
            read_iops REAL,
            write_iops REAL,
            read_time_ms REAL,
            write_time_ms REAL,
            percent_disk_time REAL,
            queue_length REAL
        );
    ''')

    # 33. Паспорт процессоров (cpu_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cpu_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processor_id INTEGER NOT NULL,
            name TEXT UNIQUE NOT NULL,
            vendor TEXT,
            architecture TEXT,
            physical_cores INTEGER,
            logical_cores INTEGER,
            base_frequency_mhz REAL,
            max_frequency_mhz REAL,
            l2_cache_kb INTEGER,
            l3_cache_kb INTEGER,
            socket TEXT,
            features_json TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 34. Паспорт планок памяти (ram_module_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ram_module_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            bank_label TEXT NOT NULL,
            device_locator TEXT,
            serial_number TEXT UNIQUE,
            part_number TEXT,
            manufacturer TEXT,
            capacity_bytes INTEGER,
            capacity_gb REAL,
            speed_mhz INTEGER,
            memory_type TEXT,
            form_factor TEXT,
            configured_voltage REAL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 35. Паспорт графических ускорителей (gpu_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gpu_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gpu_id INTEGER NOT NULL,
            pci_device_id TEXT UNIQUE,
            name TEXT NOT NULL,
            vendor TEXT,
            driver_version TEXT,
            driver_date TEXT,
            vram_bytes INTEGER,
            vram_gb REAL,
            pci_bus_id TEXT,
            bios_version TEXT,
            cuda_cores INTEGER,
            directml_supported INTEGER DEFAULT 1,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 36. Паспорт сетевых интерфейсов (network_adapter_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_adapter_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adapter_id INTEGER NOT NULL,
            adapter_guid TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            interface_name TEXT,
            mac_address TEXT,
            adapter_type TEXT,
            is_physical INTEGER DEFAULT 1,
            is_wireless INTEGER DEFAULT 0,
            max_speed_mbps INTEGER,
            driver_name TEXT,
            driver_version TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
    ''')

    # 37. Сэмплы телеметрии процессора (cpu_telemetry_samples)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cpu_telemetry_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            processor_id INTEGER DEFAULT 0,
            total_percent REAL,
            user_percent REAL,
            kernel_percent REAL,
            frequency_mhz REAL,
            temperature_c REAL,
            package_power_w REAL,
            core_utilization_json TEXT,
            core_temperatures_json TEXT
        );
    ''')

    # 38. Сэмплы телеметрии оперативной памяти (ram_telemetry_samples)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ram_telemetry_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            total_bytes INTEGER,
            total_gb REAL,
            used_bytes INTEGER,
            used_gb REAL,
            available_bytes INTEGER,
            available_gb REAL,
            percent_used REAL,
            swap_total_gb REAL,
            swap_used_gb REAL,
            swap_percent REAL,
            pool_paged_mb REAL,
            pool_nonpaged_mb REAL
        );
    ''')

    # 39. Сэмплы телеметрии GPU (gpu_telemetry_samples)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gpu_telemetry_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            gpu_id INTEGER DEFAULT 0,
            name TEXT NOT NULL,
            load_percent REAL,
            memory_used_mb REAL,
            memory_total_mb REAL,
            memory_percent REAL,
            temperature_gpu_c REAL,
            temperature_memory_c REAL,
            fan_speed_pct REAL,
            power_draw_w REAL,
            clock_graphics_mhz REAL,
            clock_memory_mhz REAL
        );
    ''')

    # 40. Сэмплы сетевых интерфейсов (network_adapter_samples)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_adapter_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            adapter_name TEXT NOT NULL,
            bytes_recv_sec REAL,
            bytes_sent_sec REAL,
            packets_recv_sec REAL,
            packets_sent_sec REAL,
            errors_in_sec REAL,
            errors_out_sec REAL,
            link_speed_mbps INTEGER,
            is_connected INTEGER DEFAULT 1
        );
    ''')

    # Индексы для ускорения выборок
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON system_snapshots(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_sensor_time ON sensor_polls(sensor_id, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_category ON sensor_polls(sensor_category, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_snapshot_id ON process_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_name_pid ON process_snapshots(name, pid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregates_sensor_time ON sensor_aggregates_hourly(sensor_id, period_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rollups_daily_date ON process_rollups_daily(date, name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hardware_audits_archive_id ON hardware_audits(archive_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reboot_history_boot_time ON reboot_history(boot_time);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_trigger ON incidents(trigger_type);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_prov_guid ON process_provenance_events(process_guid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_prov_created_at ON process_provenance_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_prov_name_pid ON process_provenance_events(name, pid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_events_created_at ON device_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_inventory_dev_id ON device_inventory(device_instance_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_w64_events_created_at ON w64_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_process_outliers_created_at ON process_outliers(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_extended_audits_created_at ON system_extended_audits(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_hourly_time ON telemetry_hourly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_daily_time ON telemetry_daily(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_weekly_time ON telemetry_weekly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_monthly_time ON telemetry_monthly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_yearly_time ON telemetry_yearly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_spikes_time ON telemetry_spikes(created_at, sensor_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disk_io_pid_time ON disk_io_events(pid, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disk_io_disk_time ON disk_io_events(disk_id, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disk_health_disk_time ON disk_health_snapshots(disk_id, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disk_health_serial_time ON disk_health_snapshots(serial_number, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disk_inv_serial ON disk_inventory(serial_number);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_volume_inv_guid ON volume_inventory(volume_guid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disk_perf_name_time ON disk_performance_samples(disk_name, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cpu_inv_name ON cpu_inventory(name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ram_mod_serial ON ram_module_inventory(serial_number);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gpu_inv_pci ON gpu_inventory(pci_device_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_net_inv_guid ON network_adapter_inventory(adapter_guid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cpu_samples_time ON cpu_telemetry_samples(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ram_samples_time ON ram_telemetry_samples(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gpu_samples_time ON gpu_telemetry_samples(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_net_samples_time ON network_adapter_samples(created_at);')

    _run_migrations(cursor)
    conn.commit()


def _run_migrations(cursor: sqlite3.Cursor) -> None:
    """Выполняет безопасные миграции добавления новых колонок в существующие таблицы."""
    # Миграция: telemetry_events
    try:
        cursor.execute("PRAGMA table_info(telemetry_events)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'severity' not in columns:
            cursor.execute("ALTER TABLE telemetry_events ADD COLUMN severity TEXT DEFAULT 'info'")
        if 'event_details' not in columns:
            cursor.execute("ALTER TABLE telemetry_events ADD COLUMN event_details TEXT")
        if 'raw_json' not in columns:
            cursor.execute("ALTER TABLE telemetry_events ADD COLUMN raw_json TEXT")
    except Exception as exc:
        logger.warning(f'Миграция telemetry_events: {exc}')

    # Миграция: system_snapshots
    try:
        cursor.execute("PRAGMA table_info(system_snapshots)")
        snap_cols = {row[1] for row in cursor.fetchall()}
        expected_snap_cols = {
            'hostname': 'TEXT',
            'username': 'TEXT',
            'uptime_seconds': 'REAL',
            'os_name': 'TEXT',
            'os_build': 'TEXT',
            'os_install_date': 'TEXT',
            'system_language': 'TEXT',
            'os_install_language': 'TEXT',
            'user_locale': 'TEXT',
            'system_locale': 'TEXT',
            'timezone': 'TEXT',
            'codepage': 'TEXT',
            'input_languages_json': 'TEXT',
            'disks_json': 'TEXT',
            'physical_disks_json': 'TEXT',
            'monitors_json': 'TEXT',
            'updates_json': 'TEXT',
            'office_json': 'TEXT',
            'onedrive_json': 'TEXT',
            'battery_json': 'TEXT',
            'ram_sticks_json': 'TEXT',
            'listening_ports_json': 'TEXT',
            'alerts_json': 'TEXT',
            'cpu_total_percent': 'REAL',
            'cpu_frequency_mhz': 'REAL',
            'memory_total_gb': 'REAL',
            'memory_used_gb': 'REAL',
            'memory_percent': 'REAL',
            'swap_percent': 'REAL',
            'gpu_load_percent': 'REAL',
            'gpu_temp_c': 'REAL',
            'disk_read_bytes_sec': 'REAL',
            'disk_write_bytes_sec': 'REAL',
            'disk_read_count_sec': 'REAL',
            'disk_write_count_sec': 'REAL',
            'network_sent_bytes_sec': 'REAL',
            'network_recv_bytes_sec': 'REAL',
            'hardware_audit': 'TEXT',
            'raw_json': 'TEXT',
        }
        for col_name, col_type in expected_snap_cols.items():
            if col_name not in snap_cols:
                cursor.execute(f"ALTER TABLE system_snapshots ADD COLUMN {col_name} {col_type}")
    except Exception as exc:
        logger.warning(f'Миграция system_snapshots: {exc}')

    # Миграция: process_snapshots
    try:
        cursor.execute("PRAGMA table_info(process_snapshots)")
        proc_cols = {row[1] for row in cursor.fetchall()}
        new_proc_columns = {
            'num_handles': 'INTEGER DEFAULT 0',
            'read_bytes_sec': 'REAL',
            'write_bytes_sec': 'REAL',
            'integrity_level': 'TEXT',
            'elevation': 'INTEGER DEFAULT 0',
            'ppid': 'INTEGER',
            'parent_name': 'TEXT',
            'executable': 'TEXT',
            'cmdline': 'TEXT',
            'sid': 'TEXT',
            'session_id': 'INTEGER',
            'creation_time': 'TEXT',
            'process_guid': 'TEXT',
            'ancestor_chain': 'TEXT',
            'launch_reason': 'TEXT',
        }
        for col_name, col_def in new_proc_columns.items():
            if col_name not in proc_cols:
                cursor.execute(f"ALTER TABLE process_snapshots ADD COLUMN {col_name} {col_def}")
    except Exception as exc:
        logger.warning(f'Миграция process_snapshots: {exc}')
