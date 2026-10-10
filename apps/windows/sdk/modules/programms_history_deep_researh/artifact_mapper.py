# -*- coding: utf-8 -*-
# Updated: 2026-10-03 23:57:30
"""artifact_mapper.py – сопоставление найденных артефактов с программами.

Для простоты реализовано эвристическое сопоставление: в пути к артефакту ищется
название программы (без учёта регистра). Если совпадение найдено – артефакт
приписывается этой программе. При отсутствии совпадений артефакт попадает в
список `unknown_artifacts`.

В более продвинутой реализации можно воспользоваться LLM (Gemini) или RAG‑
индексом, но в рамках базового механизма достаточно локальной логики.
"""

from typing import List, Dict, Tuple

def map_artifacts(programs: List[Dict], artifacts: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Сопоставляет артефакты с известными программами.

    Args:
        programs: Список программ (словарей) из `registry_extractor.get_installed_programs`.
        artifacts: Список артефактов, полученных `scanner.scan_user_profiles`.

    Returns:
        tuple: (mapped, unknown)
            * mapped – список словарей `{"program": <program dict>, "artifact": <artifact dict>}`;
            * unknown – артефакты, которым не удалось сопоставить программу.
    """
    mapped: List[Dict] = []
    unknown: List[Dict] = []
    # Подготовим список названий программ в нижнем регистре.
    prog_names = [(p.get("name", "").lower(), p) for p in programs]
    for art in artifacts:
        path_lower = art.get("path", "").lower()
        matched = False
        for pname, prog in prog_names:
            if pname and pname in path_lower:
                mapped.append({"program": prog, "artifact": art})
                matched = True
                break
        if not matched:
            unknown.append(art)
    return mapped, unknown
