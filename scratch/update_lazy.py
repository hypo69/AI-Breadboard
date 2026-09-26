from pathlib import Path

path = Path("src/api/webgui/admin/lazy-init-patch.js")
text = path.read_text(encoding="utf-8")

lines = text.splitlines(keepends=True)
new_lines = []
for line in lines:
    if "'observability'" in line and "system_inspector_tab" in line:
        continue
    line = line.replace("20260926_v1", "20260926_v2")
    new_lines.append(line)

path.write_text("".join(new_lines), encoding="utf-8")
print("Updated lazy-init-patch.js successfully")
