from __future__ import annotations
import sys
from pathlib import Path
_project_root = str(Path(__file__).resolve().parents[3])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
try:
    from apps.windows.telemetry.storage import TelemetryStorage
except ImportError as e:
    print(f'Error: Could not import TelemetryStorage: {e}', file=sys.stderr)
    sys.exit(1)

def main() -> None:
    """Main execution entry point for temperature sensors inspection."""
    try:
        storage = TelemetryStorage.get_instance()
    except Exception as ex:
        print(f'Error accessing telemetry storage: {ex}', file=sys.stderr)
        sys.exit(1)
    query = "\n        SELECT s1.hardware_name, s1.sensor_name, s1.unit, s1.value, s1.timestamp\n        FROM sensor_polls s1\n        INNER JOIN (\n            SELECT sensor_id, MAX(id) as max_id\n            FROM sensor_polls\n            WHERE sensor_category = 'Temperatures'\n            GROUP BY sensor_id\n        ) s2 ON s1.id = s2.max_id\n        ORDER BY s1.hardware_name, s1.sensor_name;\n    "
    with storage._lock, storage._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
    print(f'=== TELEMETRY TEMPERATURE SENSORS ({storage.db_path}) ===')
    if not rows:
        print('No temperature sensor records found in database (ensure hybrid/full telemetry mode has run).')
        return
    print(f"{'Hardware':<25} {'Sensor Name':<25} {'Value':<10} {'Unit':<8} {'Timestamp'}")
    print('-' * 80)
    for r in rows:
        hw = r.get('hardware_name', 'System') or 'System'
        sname = r.get('sensor_name', 'Unknown') or 'Unknown'
        val = r.get('value', 0.0)
        unit = r.get('unit', '°C') or '°C'
        ts = r.get('timestamp', '-')
        print(f'{hw:<25} {sname:<25} {val:<10.1f} {unit:<8} {ts}')
if __name__ == '__main__':
    main()