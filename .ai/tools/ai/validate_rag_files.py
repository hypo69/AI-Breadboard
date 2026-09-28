import os
from pathlib import Path
EXCLUDED_DIRS = {'.git', '.pytest_cache', '.vs', '__pycache__', 'venv', 'htmlcov', 'site', 'node_modules', '.venv'}
EXCLUDED_FILES = {'.env', '.gitignore', '.gitattributes', 'all_duplicates_with_ids.csv', 'all_media_data.csv', 'deletion_candidates_all.csv', 'deletion_candidates.csv', 'duplicates_report_candidates.csv', 'duplicates_report.csv', 'inferred_titles_report.csv', 'physical_check_results.csv', 'potential_duplicates.csv'}

def get_files_to_index(project_root: Path=None):
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    aux_dir = project_root / '.ai' / 'instructions' / 'knowledge'
    files_to_index = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if file in EXCLUDED_FILES:
                continue
            file_path = Path(root) / file
            if file_path.suffix in ['.py', '.md']:
                files_to_index.append(file_path)
    if aux_dir.exists():
        for file_path in aux_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.py', '.md']:
                if file_path not in files_to_index:
                    files_to_index.append(file_path)
    return files_to_index
if __name__ == '__main__':
    files = get_files_to_index()
    print(f'Всего файлов к индексации: {len(files)}')
    for f in files:
        print(f)