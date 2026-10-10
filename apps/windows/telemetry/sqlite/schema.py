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
# Updated: 2026-10-10 05:49:00
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

    # 41. Архивные снимки автозапуска Windows (startup_audit_archives)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS startup_audit_archives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            total_entries INTEGER DEFAULT 0,
            active_entries INTEGER DEFAULT 0,
            disabled_entries INTEGER DEFAULT 0,
            broken_entries INTEGER DEFAULT 0,
            health_score INTEGER DEFAULT 100,
            changes_count INTEGER DEFAULT 0,
            raw_json TEXT
        );
    ''')

    # 42. Отличия и изменения в автозапуске между снимками (startup_changes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS startup_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            change_type TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            previous_value TEXT,
            current_value TEXT
        );
    ''')

    # 43. Снимки каналов журналов событий (event_log_channel_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_log_channel_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            channel_name TEXT NOT NULL,
            display_name TEXT,
            description TEXT,
            record_count INTEGER DEFAULT 0,
            size_bytes INTEGER DEFAULT 0,
            channel_type TEXT DEFAULT 'Admin',
            is_enabled INTEGER DEFAULT 1,
            created_at REAL NOT NULL
        );
    ''')

    # 44. Кеш записей журналов событий (event_log_entries_cache)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_log_entries_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            channel TEXT NOT NULL,
            event_id INTEGER DEFAULT 0,
            level TEXT DEFAULT 'Information',
            provider_name TEXT,
            time_created TEXT,
            message TEXT,
            raw_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 45. Скомпилированные профили Log Intelligence (event_log_intelligence_profiles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_log_intelligence_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            channel TEXT NOT NULL,
            total_analyzed INTEGER DEFAULT 0,
            unique_patterns_count INTEGER DEFAULT 0,
            critical_incidents_json TEXT,
            top_clusters_json TEXT,
            bursts_json TEXT,
            decision_gate_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 46. Профили брандмауэра (firewall_profile_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firewall_profile_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            domain_enabled INTEGER NOT NULL,
            private_enabled INTEGER NOT NULL,
            public_enabled INTEGER NOT NULL,
            domain_default_inbound TEXT,
            private_default_inbound TEXT,
            public_default_inbound TEXT,
            stealth_mode_enabled INTEGER DEFAULT 1,
            created_at REAL NOT NULL
        );
    ''')

    # 47. Правила брандмауэра (firewall_rule_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firewall_rule_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            display_name TEXT,
            direction TEXT NOT NULL,
            action TEXT NOT NULL,
            enabled INTEGER NOT NULL,
            protocol TEXT,
            local_port TEXT,
            remote_port TEXT,
            program_path TEXT,
            profile_mask INTEGER,
            created_at REAL NOT NULL
        );
    ''')

    # 48. Снимки состояния служб Windows (services_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            service_name TEXT NOT NULL,
            display_name TEXT,
            state TEXT NOT NULL,
            state_code INTEGER,
            start_type TEXT,
            pid INTEGER,
            binary_path TEXT,
            account TEXT,
            is_orphaned INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        );
    ''')

    # 49. События изменений служб (service_change_events)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_change_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            service_name TEXT NOT NULL,
            display_name TEXT,
            action TEXT NOT NULL,
            old_state TEXT,
            new_state TEXT,
            performed_by TEXT DEFAULT 'SYSTEM',
            details_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 50. Снимки троттлинга и электропитания CPU (cpu_throttling_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cpu_throttling_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            prochot_active BOOLEAN NOT NULL DEFAULT 0,
            pl1_limit_watts REAL,
            pl2_limit_watts REAL,
            current_power_watts REAL,
            max_core_temp_c REAL,
            package_temp_c REAL,
            dpc_latency_us INTEGER DEFAULT 0,
            isr_latency_us INTEGER DEFAULT 0,
            throttling_reasons_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 51. Снимки температурных зон (thermal_zone_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thermal_zone_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            zone_name TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            critical_limit_c REAL,
            throttling_limit_c REAL,
            sensor_provider TEXT NOT NULL,
            created_at REAL NOT NULL
        );
    ''')

    # 52. Снимки поведенческой форензики (forensics_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forensics_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            foreground_window_title TEXT,
            foreground_process_name TEXT,
            foreground_pid INTEGER,
            user_idle_seconds INTEGER DEFAULT 0,
            camera_active_apps_json TEXT,
            microphone_active_apps_json TEXT,
            userassist_top_apps_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 53. Сводные снимки утечек ресурсов (process_leak_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_leak_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL UNIQUE,
            timestamp DATETIME NOT NULL,
            total_processes INTEGER NOT NULL,
            suspicious_count INTEGER NOT NULL,
            created_at REAL NOT NULL
        );
    ''')

    # 54. Детализация процессов с утечками (process_leak_items)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_leak_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            pid INTEGER NOT NULL,
            name TEXT NOT NULL,
            handles_count INTEGER NOT NULL,
            gdi_objects INTEGER NOT NULL,
            user_objects INTEGER NOT NULL,
            page_faults INTEGER NOT NULL,
            working_set_mb REAL NOT NULL,
            leak_risk_score TEXT NOT NULL,
            leak_risk_reasons_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 55. Снимки защитника Defender (defender_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS defender_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            real_time_protection_enabled INTEGER NOT NULL,
            cloud_protection_enabled INTEGER NOT NULL,
            behavior_monitoring_enabled INTEGER NOT NULL,
            tamper_protection_enabled INTEGER NOT NULL,
            pua_protection_enabled INTEGER NOT NULL,
            antivirus_enabled INTEGER NOT NULL,
            antispyware_enabled INTEGER NOT NULL,
            engine_version TEXT,
            av_signature_version TEXT,
            last_quick_scan_datetime DATETIME,
            last_full_scan_datetime DATETIME,
            security_score INTEGER DEFAULT 100,
            cfa_state INTEGER DEFAULT 0,
            raw_status_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 56. Исключения защитника (defender_exclusions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS defender_exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            exclusion_type TEXT NOT NULL,
            exclusion_value TEXT NOT NULL,
            risk_level TEXT DEFAULT 'SAFE',
            created_at REAL NOT NULL
        );
    ''')

    # 57. Правила ASR (defender_asr_rules)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS defender_asr_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            rule_guid TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            rule_action TEXT NOT NULL,
            created_at REAL NOT NULL
        );
    ''')

    # 58. Обнаруженные угрозы (defender_threats)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS defender_threats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            threat_id TEXT,
            threat_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            category TEXT,
            resources_json TEXT,
            detection_time DATETIME,
            created_at REAL NOT NULL
        );
    ''')

    # 59. Снимки сетевых сокетов процессов (process_network_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_network_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            pid INTEGER NOT NULL,
            process_name TEXT NOT NULL,
            local_address TEXT,
            remote_address TEXT,
            protocol TEXT,
            status TEXT,
            service_type TEXT,
            sent_kb REAL DEFAULT 0.0,
            recv_kb REAL DEFAULT 0.0,
            read_speed_kbs REAL DEFAULT 0.0,
            write_speed_kbs REAL DEFAULT 0.0,
            created_at REAL NOT NULL
        );
    ''')

    # 60. Инвентарь установленного ПО (software_inventory)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS software_inventory (
            app_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            version TEXT,
            publisher TEXT,
            install_date TEXT,
            install_location TEXT,
            architecture TEXT,
            is_system_component INTEGER DEFAULT 0,
            first_seen DATETIME NOT NULL,
            last_scanned_at DATETIME NOT NULL
        );
    ''')

    # 61. Категоризированные места хранения ПО (software_storage_locations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS software_storage_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT NOT NULL,
            category TEXT NOT NULL,
            path TEXT NOT NULL,
            size_bytes INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            last_updated DATETIME NOT NULL,
            FOREIGN KEY (app_id) REFERENCES software_inventory(app_id) ON DELETE CASCADE
        );
    ''')

    # 62. Файлы конфигурации ПО (software_config_files)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS software_config_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            format TEXT,
            size_bytes INTEGER DEFAULT 0,
            snippet TEXT,
            FOREIGN KEY (app_id) REFERENCES software_inventory(app_id) ON DELETE CASCADE
        );
    ''')

    # 63. Сетевые снимки ПО (software_network_snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS software_network_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            app_id TEXT NOT NULL,
            pid INTEGER NOT NULL,
            local_address TEXT,
            remote_address TEXT,
            protocol TEXT,
            domain_name TEXT,
            sent_kb REAL DEFAULT 0.0,
            recv_kb REAL DEFAULT 0.0,
            FOREIGN KEY (app_id) REFERENCES software_inventory(app_id) ON DELETE CASCADE
        );
    ''')

    # 64. Анализ ПО с помощью ИИ (software_ai_research)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS software_ai_research (
            app_id TEXT PRIMARY KEY,
            summary TEXT,
            config_purpose_explanation TEXT,
            data_storage_explanation TEXT,
            network_activity_explanation TEXT,
            confirmed_facts_json TEXT,
            inferred_facts_json TEXT,
            confidence_level REAL DEFAULT 0.0,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (app_id) REFERENCES software_inventory(app_id) ON DELETE CASCADE
        );
    ''')

    # 65. Нормализованные события безопасности Windows (security_events)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_record_id INTEGER DEFAULT 0,
            event_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            computer TEXT,
            channel TEXT DEFAULT 'Security',
            level TEXT DEFAULT 'Information',
            subject_user TEXT,
            subject_domain TEXT,
            subject_sid TEXT,
            target_user TEXT,
            target_domain TEXT,
            target_sid TEXT,
            process_id INTEGER DEFAULT 0,
            process_name TEXT,
            parent_process_id INTEGER DEFAULT 0,
            parent_process_name TEXT,
            command_line TEXT,
            logon_id TEXT,
            logon_type INTEGER,
            elevated_token INTEGER,
            source_ip TEXT,
            source_port INTEGER,
            object_name TEXT,
            status_code TEXT,
            message TEXT,
            event_data_json TEXT,
            ingested_at TEXT NOT NULL
        );
    ''')

    # 66. Сырые события безопасности Windows (security_events_raw)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_record_id INTEGER DEFAULT 0,
            event_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            channel TEXT DEFAULT 'Security',
            raw_xml TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );
    ''')

    # 67. Закладки инкрементального сбора событий (security_collector_bookmarks)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_collector_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL UNIQUE,
            last_record_id INTEGER DEFAULT 0,
            bookmark_xml TEXT,
            last_timestamp TEXT,
            updated_at REAL NOT NULL
        );
    ''')

    # 68. События питания и жизненного цикла Windows (power_events)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS power_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            provider TEXT,
            channel TEXT DEFAULT 'System',
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            event_type TEXT NOT NULL,
            shutdown_type TEXT,
            user TEXT,
            domain TEXT,
            process TEXT,
            process_id INTEGER,
            reason TEXT,
            reason_code TEXT,
            comment TEXT,
            unexpected INTEGER DEFAULT 0,
            bugcheck_code TEXT,
            bugcheck_params_json TEXT,
            boot_id TEXT,
            details_json TEXT,
            raw_xml TEXT,
            UNIQUE(event_id, timestamp, provider) ON CONFLICT REPLACE
        );
    ''')

    # 69. Реконструированные сессии питания ОС (power_sessions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS power_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            boot_time TEXT NOT NULL,
            boot_timestamp REAL,
            shutdown_time TEXT,
            shutdown_timestamp REAL,
            uptime_seconds REAL,
            uptime_human TEXT,
            shutdown_type TEXT DEFAULT 'Active',
            initiator TEXT,
            process TEXT,
            reason TEXT,
            reason_code TEXT,
            comment TEXT,
            clean_shutdown INTEGER DEFAULT 1,
            unexpected_shutdown INTEGER DEFAULT 0,
            bugcheck TEXT,
            boot_event_id INTEGER DEFAULT 12,
            shutdown_event_id INTEGER,
            initiator_chain_json TEXT,
            events_json TEXT,
            created_at REAL NOT NULL
        );
    ''')

    # 69.1. Разрывы и паузы телеметрии при сне (telemetry_gaps)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_utc TEXT NOT NULL,
            end_utc TEXT NOT NULL,
            gap_type TEXT NOT NULL,
            duration_seconds REAL NOT NULL,
            confidence TEXT NOT NULL,
            evidence_json TEXT,
            created_at REAL NOT NULL
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_gaps_start ON telemetry_gaps(start_utc);')

    # 70. Паспорт программы (process_definition)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_definition (
            definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            executable_path TEXT NOT NULL UNIQUE,
            sha256 TEXT,
            company_name TEXT,
            file_description TEXT,
            icon_base64 TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
    ''')

    # 71. Единичный инстанс процесса (process_instance - Process Intelligence & PID Recycling Resolution)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_instance (
            instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            definition_id INTEGER NOT NULL,
            pid INTEGER NOT NULL,
            parent_instance_id INTEGER,
            name TEXT NOT NULL,
            executable_path TEXT NOT NULL,
            command_line TEXT,
            start_time TEXT NOT NULL,
            exit_time TEXT,
            exit_code INTEGER,
            session_id INTEGER DEFAULT 1,
            user_name TEXT,
            integrity_level TEXT,
            status TEXT NOT NULL DEFAULT 'RUNNING',
            UNIQUE (pid, start_time),
            FOREIGN KEY (parent_instance_id) REFERENCES process_instance(instance_id),
            FOREIGN KEY (definition_id) REFERENCES process_definition(definition_id)
        );
    ''')

    # 72. Срезы телеметрии во времени (process_sample)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_sample (
            sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            created_at REAL NOT NULL,
            cpu_percent REAL DEFAULT 0.0,
            cpu_user_time REAL DEFAULT 0.0,
            cpu_kernel_time REAL DEFAULT 0.0,
            thread_count INTEGER DEFAULT 1,
            working_set_mb REAL DEFAULT 0.0,
            private_bytes_mb REAL DEFAULT 0.0,
            page_faults_sec REAL DEFAULT 0.0,
            gpu_load_percent REAL DEFAULT 0.0,
            gpu_vram_mb REAL DEFAULT 0.0,
            disk_read_bytes_sec REAL DEFAULT 0.0,
            disk_write_bytes_sec REAL DEFAULT 0.0,
            disk_iops REAL DEFAULT 0.0,
            handle_count INTEGER DEFAULT 0,
            gdi_objects INTEGER DEFAULT 0,
            user_objects INTEGER DEFAULT 0,
            sockets_count INTEGER DEFAULT 0,
            sockets_json TEXT,
            FOREIGN KEY (instance_id) REFERENCES process_instance(instance_id) ON DELETE CASCADE
        );
    ''')

    # 73. Лента файловых операций процесса (process_file_events)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_file_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER NOT NULL DEFAULT 0,
            process_name TEXT NOT NULL DEFAULT '',
            action_type TEXT NOT NULL DEFAULT '', -- 'CREATE', 'MODIFY', 'DELETE', 'RENAME'
            target_directory TEXT NOT NULL DEFAULT '',
            file_path TEXT NOT NULL,
            bytes_affected INTEGER DEFAULT 0,
            instance_id INTEGER,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            created_at REAL DEFAULT 0.0,
            FOREIGN KEY (instance_id) REFERENCES process_instance(instance_id) ON DELETE CASCADE
        );
    ''')

    # 74. Единая таблица снимков ресурсов и активности процессов по PID (Per-PID Telemetry Engine)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_pid_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid INTEGER NOT NULL,
            process_name TEXT NOT NULL,
            executable_path TEXT,
            
            -- Процессор (CPU)
            cpu_percent REAL NOT NULL DEFAULT 0.0,
            user_time_ms INTEGER NOT NULL DEFAULT 0,
            kernel_time_ms INTEGER NOT NULL DEFAULT 0,
            thread_count INTEGER NOT NULL DEFAULT 1,
            
            -- Память (RAM)
            working_set_bytes INTEGER NOT NULL DEFAULT 0,
            private_bytes INTEGER NOT NULL DEFAULT 0,
            page_faults_count INTEGER DEFAULT 0,
            
            -- Графика (GPU)
            gpu_vram_bytes INTEGER DEFAULT 0,
            gpu_utilization REAL DEFAULT 0.0,
            
            -- Дисковый I/O
            read_bytes_total INTEGER DEFAULT 0,
            write_bytes_total INTEGER DEFAULT 0,
            read_ops_total INTEGER DEFAULT 0,
            write_ops_total INTEGER DEFAULT 0,
            
            -- Сетевой трафик
            net_bytes_sent_total INTEGER DEFAULT 0,
            net_bytes_recv_total INTEGER DEFAULT 0,
            
            -- Системные дескрипторы и GUI-ресурсы
            handle_count INTEGER DEFAULT 0,
            gdi_objects INTEGER DEFAULT 0,
            user_objects INTEGER DEFAULT 0,
            
            timestamp TEXT NOT NULL DEFAULT (datetime('now'))
        );
    ''')

    # Индексы для ускорения выборок
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_def_path ON process_definition(executable_path);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_inst_pid_start ON process_instance(pid, start_time);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_inst_status ON process_instance(status);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_inst_parent ON process_instance(parent_instance_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_inst_name ON process_instance(name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_sample_inst_time ON process_sample(instance_id, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_sample_time ON process_sample(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_fe_inst_time ON process_file_events(instance_id, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON system_snapshots(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_startup_archives_created_at ON startup_audit_archives(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_startup_archives_archive_id ON startup_audit_archives(archive_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_startup_changes_created_at ON startup_changes(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_startup_changes_archive_id ON startup_changes(archive_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_created_host ON system_snapshots(created_at, hostname);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_sensor_time ON sensor_polls(sensor_id, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_polls_category ON sensor_polls(sensor_category, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_snapshot_id ON process_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_processes_name_pid ON process_snapshots(name, pid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_snap_snapshot_cpu ON process_snapshots(snapshot_id, cpu_percent DESC);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregates_sensor_time ON sensor_aggregates_hourly(sensor_id, period_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rollups_daily_date ON process_rollups_daily(date, name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rollups_tier_start_end ON telemetry_rollups(tier, period_start_epoch, period_end_epoch);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hardware_audits_archive_id ON hardware_audits(archive_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reboot_history_boot_time ON reboot_history(boot_time);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_trigger ON incidents(trigger_type);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_sev_time ON incidents(severity, created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_prov_guid ON process_provenance_events(process_guid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_prov_created_at ON process_provenance_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_prov_name_pid ON process_provenance_events(name, pid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_events_created_at ON device_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_inventory_dev_id ON device_inventory(device_instance_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_w64_events_created_at ON w64_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_process_outliers_created_at ON process_outliers(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_extended_audits_created_at ON system_extended_audits(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_hourly_time ON telemetry_hourly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_hourly_sensor ON telemetry_hourly(sensor_id, bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_daily_time ON telemetry_daily(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_daily_sensor ON telemetry_daily(sensor_id, bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_weekly_time ON telemetry_weekly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_weekly_sensor ON telemetry_weekly(sensor_id, bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_monthly_time ON telemetry_monthly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_monthly_sensor ON telemetry_monthly(sensor_id, bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_yearly_time ON telemetry_yearly(bucket_start);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_yearly_sensor ON telemetry_yearly(sensor_id, bucket_start);')
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

    # Индексы для новых подсистем
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evt_chan_snap_id ON event_log_channel_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evt_chan_name ON event_log_channel_snapshots(channel_name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evt_entries_snap_id ON event_log_entries_cache(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evt_entries_chan_lvl ON event_log_entries_cache(channel, level);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evt_intel_chan ON event_log_intelligence_profiles(channel);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fw_prof_snapshot ON firewall_profile_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fw_rule_snapshot ON firewall_rule_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fw_rule_name ON firewall_rule_snapshots(rule_name);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_services_snap_id ON services_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_services_name ON services_snapshots(service_name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_services_state ON services_snapshots(state);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_svc_changes_ts ON service_change_events(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_svc_changes_name ON service_change_events(service_name);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_throttling_snapshot_id ON cpu_throttling_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_throttling_timestamp ON cpu_throttling_snapshots(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_thermal_zone_snapshot ON thermal_zone_snapshots(snapshot_id);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_forensics_snapshot_id ON forensics_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_forensics_timestamp ON forensics_snapshots(timestamp);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_leak_snapshot_id ON process_leak_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_leak_timestamp ON process_leak_snapshots(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_leak_item_snapshot ON process_leak_items(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_leak_item_pid ON process_leak_items(pid);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_defender_snapshot_id ON defender_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_defender_timestamp ON defender_snapshots(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_defender_exclusions_snap ON defender_exclusions(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_defender_asr_snap ON defender_asr_rules(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_defender_threats_snap ON defender_threats(snapshot_id);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_net_snapshot_id ON process_network_snapshots(snapshot_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_net_pid ON process_network_snapshots(pid);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sw_storage_app ON software_storage_locations(app_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sw_config_app ON software_config_files(app_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sw_net_app_ts ON software_network_snapshots(timestamp, app_id);')

    # Индексы для подсистемы безопасности Security Event Log
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_event_id ON security_events(event_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_created_at ON security_events(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_user ON security_events(subject_user);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_target_user ON security_events(target_user);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_process ON security_events(process_name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_pid ON security_events(process_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_record_id ON security_events(event_record_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sec_raw_record_id ON security_events_raw(event_record_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sec_raw_created_at ON security_events_raw(created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sec_bm_channel ON security_collector_bookmarks(channel);')

    # Индексы для подсистемы событий питания и сессий
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_events_eid ON power_events(event_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_events_ts ON power_events(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_events_type ON power_events(event_type);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_events_user ON power_events(user);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_events_proc ON power_events(process);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_sessions_boot_time ON power_sessions(boot_time);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_sessions_shutdown_type ON power_sessions(shutdown_type);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_sessions_clean ON power_sessions(clean_shutdown, unexpected_shutdown);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_power_sessions_initiator ON power_sessions(initiator);')

    _run_migrations(cursor)

    # Индексы для Per-PID Telemetry Engine и отслеживания файлов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_pid_time ON process_pid_snapshots(pid, timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_proc_name_time ON process_pid_snapshots(process_name, timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_events_pid ON process_file_events(pid);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_events_dir ON process_file_events(target_directory, timestamp);')

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

    # Миграция: process_file_events
    try:
        cursor.execute("PRAGMA table_info(process_file_events)")
        fe_cols = {row[1] for row in cursor.fetchall()}
        if fe_cols:
            # Безопасное переименование устаревших имен колонок при их наличии
            legacy_renames = [
                ('id', 'event_id'),
                ('action', 'action_type'),
                ('target_folder', 'target_directory'),
                ('bytes_count', 'bytes_affected'),
            ]
            for old_col, new_col in legacy_renames:
                if old_col in fe_cols and new_col not in fe_cols:
                    cursor.execute(f"ALTER TABLE process_file_events RENAME COLUMN {old_col} TO {new_col}")
                    fe_cols.remove(old_col)
                    fe_cols.add(new_col)

            target_fe_columns = {
                'pid': "INTEGER NOT NULL DEFAULT 0",
                'process_name': "TEXT NOT NULL DEFAULT ''",
                'action_type': "TEXT NOT NULL DEFAULT ''",
                'target_directory': "TEXT NOT NULL DEFAULT ''",
                'file_path': "TEXT NOT NULL DEFAULT ''",
                'bytes_affected': "INTEGER DEFAULT 0",
                'instance_id': "INTEGER",
                'timestamp': "TEXT NOT NULL DEFAULT (datetime('now'))",
                'created_at': "REAL DEFAULT 0.0",
            }
            for col_name, col_def in target_fe_columns.items():
                if col_name not in fe_cols:
                    cursor.execute(f"ALTER TABLE process_file_events ADD COLUMN {col_name} {col_def}")
    except Exception as exc:
        logger.warning(f'Миграция process_file_events: {exc}')


