# -*- coding: utf-8 -*-
# Updated: 2026-10-03 23:58:45
"""report.py – генерация отчёта о программах и их артефактах.

Функция `generate_report` собирает:
* список установленных программ (из реестра);
* список найденных артефактов (сканирование пользовательских профилей);
* сопоставляет артефакты с программами;
* формирует структуру `ProgramArtifactReport`.

Отчёт возвращается в виде словаря, готового к сериализации в JSON.
"""

import json
from typing import List, Dict

from .scanner import scan_user_profiles
from .registry_extractor import get_installed_programs
from .artifact_mapper import map_artifacts


def generate_report() -> Dict:
    """Генерирует полный отчёт о программном обеспечении и артефактах.

    Returns:
        dict: Схема отчёта.
    """
    programs: List[Dict] = get_installed_programs()
    artifacts: List[Dict] = scan_user_profiles()
    mapped, unknown = map_artifacts(programs, artifacts)

    report = {
        "generated_at": __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        "installed_programs": programs,
        "detected_artifacts": artifacts,
        "mapped_artifacts": [
            {"program_name": entry["program"].get("name"), "artifact_path": entry["artifact"]["path"]}
            for entry in mapped
        ],
        "unknown_artifacts": unknown,
    }
    return report

# Helper для печати JSON (может использоваться в CLI)
def dump_report(pretty: bool = True) -> str:
    rpt = generate_report()
    if pretty:
        return json.dumps(rpt, indent=2, ensure_ascii=False)
    return json.dumps(rpt, ensure_ascii=False)
