"""
Скрипт для проверки внутренних и внешних ссылок в документации.

Использует регулярные выражения для извлечения ссылок из Markdown,
валидирует внутренние ссылки путём проверки существования файлов,
пропускает якоря (#раздел) и внешние ссылки (http/https).
"""

import re
import sys
from pathlib import Path
from typing import List, Set, Tuple


class LinkChecker:
    """
    Проверяет ссылки в документации.
    
    Собирает все файлы в структуре docs/ru/, извлекает ссылки из Markdown,
    валидирует внутренние ссылки и генерирует отчёт об ошибках.
    """
    
    def __init__(self, docs_root: Path):
        """
        Инициализирует LinkChecker.
        
        Args:
            docs_root: Путь к корневой директории документации (docs/ru/)
        """
        self.docs_root = docs_root
        self.errors: List[str] = []
        self.all_files: Set[str] = set()
    
    def collect_all_files(self) -> None:
        """
        Собирает все доступные файлы документации в структуре docs/ru/.
        
        Ищет все .md файлы рекурсивно и сохраняет их относительные пути.
        """
        for md_file in self.docs_root.rglob('*.md'):
            # Нормализуем путь: используем прямые слэши для кроссплатформности
            rel_path = md_file.relative_to(self.docs_root)
            normalized_path = str(rel_path).replace('\\', '/')
            self.all_files.add(normalized_path)
            self.all_files.add(normalized_path.lower())  # Также добавляем нижний регистр
    
    def extract_links(self, content: str) -> List[str]:
        """
        Извлекает ссылки из Markdown контента.
        
        Ищет ссылки в формате [text](url) и возвращает список URL.
        
        Args:
            content: Содержимое Markdown файла
            
        Returns:
            Список извлечённых ссылок (URL)
        """
        # Регулярное выражение для поиска ссылок в формате [text](url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, content)
        return [url for _, url in matches]
    
    def resolve_relative_path(self, link: str, source_file: str) -> str:
        """
        Разрешает относительный путь с учётом расположения исходного файла.
        
        Args:
            link: Ссылка для разрешения
            source_file: Путь исходного файла (относительный от docs/ru/)
            
        Returns:
            Абсолютный путь от корня docs/ru/
        """
        # Нормализуем пути
        link = link.replace('\\', '/')
        source_file = source_file.replace('\\', '/')
        
        # Если ссылка уже абсолютная (не начинается с ./ или ../)
        if not link.startswith('.') and not link.startswith('../'):
            # Проверяем в той же директории, что и исходный файл
            source_dir = '/'.join(source_file.split('/')[:-1])
            if source_dir:
                candidate = f"{source_dir}/{link}"
                if candidate in self.all_files or candidate.lower() in self.all_files:
                    return candidate
            return link
        
        # Обработка относительных путей (./ и ../)
        source_dir = '/'.join(source_file.split('/')[:-1])
        
        # Обработка ./file.md -> file.md в той же папке
        if link.startswith('./'):
            link = link[2:]
            if source_dir:
                return f"{source_dir}/{link}"
            else:
                return link
        
        # Обработка ../file.md и ../../file.md
        if link.startswith('../'):
            parts = source_dir.split('/')
            link_parts = link.split('/')
            
            # Считаем количество уровней вверх
            up_count = 0
            for part in link_parts:
                if part == '..':
                    up_count += 1
                else:
                    break
            
            # Убираем лишние уровни из пути исходного файла
            parts = parts[:-up_count] if up_count > 0 else parts
            
            # Добавляем оставшуюся часть ссылки
            remaining = '/'.join(link_parts[up_count:])
            
            if parts and remaining:
                return '/'.join(parts + [remaining])
            elif remaining:
                return remaining
        
        return link
    
    def validate_internal_link(self, link: str, source_file: str) -> bool:
        """
        Проверяет внутреннюю ссылку на корректность.
        
        - Внешние ссылки (http/https) пропускаются
        - Якоря (#раздел) пропускаются
        - Внутренние ссылки проверяются на существование файла
        
        Args:
            link: Ссылка для проверки
            source_file: Путь исходного файла (для отчётов об ошибках)
            
        Returns:
            True если ссылка валидна или пропускается, False если ошибка
        """
        # Пропускаем внешние ссылки
        if link.startswith('http://') or link.startswith('https://') or link.startswith('file://'):
            return True
        
        # Пропускаем якоря
        if link.startswith('#'):
            return True
        
        # Удаляем якоры из конца ссылки (file.md#section -> file.md)
        target = link.split('#')[0]
        
        # Пустая ссылка после удаления якоря
        if not target:
            return True
        
        # Пропускаем ссылки на якоря в специальных символах (например **params)
        if target.startswith('*'):
            return True
        
        # Разрешаем относительный путь
        resolved_target = self.resolve_relative_path(target, source_file)
        
        # Проверяем существование файла внутри docs/ru/ (с учётом регистра)
        if resolved_target in self.all_files or resolved_target.lower() in self.all_files:
            return True
        
        # Проверяем файлы относительно корневой директории проекта (если ссылка выходит за пределы docs/ru/)
        # Вычисляем путь к исходному файлу относительно docs_root
        src_path = self.docs_root / source_file
        # Разрешаем путь относительно директории файла
        candidate_file = (src_path.parent / target).resolve()
        if candidate_file.exists():
            return True

        self.errors.append(
            f"❌ Неверная ссылка в {source_file}: '{link}' "
            f"(целевой файл не найден: {resolved_target})"
        )
        return False
    
    def check_file(self, md_file: Path) -> None:
        """
        Проверяет ссылки в одном Markdown файле.
        
        Args:
            md_file: Путь к файлу для проверки
        """
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(
                f"❌ Ошибка чтения файла {md_file}: {e}"
            )
            return
        
        links = self.extract_links(content)
        rel_path = md_file.relative_to(self.docs_root)
        
        for link in links:
            self.validate_internal_link(link, str(rel_path))
    
    def check_all(self) -> Tuple[bool, List[str]]:
        """
        Проверяет все Markdown файлы в документации.
        
        Returns:
            Кортеж (успех, список сообщений об ошибках)
            - успех: True если нет ошибок, False если найдены ошибки
            - список сообщений: отчёт о неверных ссылках
        """
        print("🔗 Проверка ссылок в документации...")
        
        # Собираем все доступные файлы
        self.collect_all_files()
        
        if not self.all_files:
            print("⚠️  Документация не найдена в структуре.")
            return True, []
        
        # Проверяем каждый Markdown файл
        for md_file in sorted(self.docs_root.rglob('*.md')):
            self.check_file(md_file)
        
        # Определяем успех
        success = len(self.errors) == 0
        
        return success, self.errors


def main() -> int:
    """
    Главная функция скрипта.
    
    Определяет путь к документации, запускает проверку ссылок
    и выводит результаты.
    
    Returns:
        0 если всё успешно, 1 если обнаружены ошибки
    """
    # Определяем корневую директорию проекта
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    # Путь к документации
    docs_root = project_root / 'docs' / 'ru'
    
    if not docs_root.exists():
        print(f"❌ Директория документации не найдена: {docs_root}")
        return 1
    
    # Создаём и запускаем проверку ссылок
    checker = LinkChecker(docs_root)
    success, messages = checker.check_all()
    
    # Выводим результаты
    print()
    if messages:
        print("📋 Результаты проверки ссылок:")
        for msg in messages:
            print(msg)
        print()
        print(f"❌ Найдено {len(messages)} ошибок")
    else:
        print("✓ Все ссылки корректны!")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
