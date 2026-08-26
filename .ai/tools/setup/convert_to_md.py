import json
from pathlib import Path
from header import __root__

REPORTS_DIR = __root__ / 'tmp' / 'reports'

# Загружаем JSON (замените на реальные данные из предыдущего шага)
# Для примера я использую структуру, полученную в прошлый раз
json_data = """
{
  "title": "Острые козырьки (Peaky Blinders)",
  "plot": "События разворачиваются в послевоенном Бирмингеме 1920-х годов...",
  "seasons": [
    {
      "season_number": 1,
      "season_plot_summary": "Бирмингем, 1919 год. Вернувшись с полей сражений Первой мировой войны, Томас Шелби возглавляет преступную группировку «Острые козырьки»...",
      "episodes": [
        {"episode_number": 1, "title": "Эпизод 1", "detailed_description": "Томми захватывает оружие...", "final_verdict": "Начало кровавого пути."}
      ]
    }
  ]
}
"""
data = json.loads(json_data)

md_content = f"# {data['title']}\n\n"
md_content += f"## Сюжет\n{data['plot']}\n\n"

for season in data.get('seasons', []):
    md_content += f"## Сезон {season['season_number']}\n"
    md_content += f"{season['season_plot_summary']}\n\n"
    md_content += "### Эпизоды\n"
    for ep in season.get('episodes', []):
        md_content += f"#### {ep['episode_number']}. {ep['title']}\n"
        md_content += f"{ep['detailed_description']}\n\n"
        md_content += f"**Вердикт:** {ep['final_verdict']}\n\n"

output_path = REPORTS_DIR / "Peaky_Blinders_Card.md"
output_path.write_text(md_content, encoding='utf-8')
print(f"✅ Отчёт сохранён: {output_path}")
