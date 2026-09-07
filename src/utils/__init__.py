"""
Модуль утилит для AI-Breadboard.

Содержит различные вспомогательные инструменты и функции для работы с:
- CSV файлами
- Датой и временем
- Файловой системой
- FTP
- Изображениями
- JSON
- PDF
- SMTP
- URL
- Видео
- Excel файлами
"""

# Импортируем основные компоненты для удобства
from . import (
    csv,
    date_time,
    file,
    ftp,
    get_free_port,
    header,
    image,
    jjson,
    printer,
    smtp,
    url,
    versioning,
    video,
    xls,
    archive,
    docx,
    pdf_extractor,
)

try:
    from . import pdf
except ImportError:
    pdf = None

__all__ = [
    'archive',
    'csv',
    'date_time',
    'docx',
    'file',
    'ftp',
    'get_free_port',
    'header',
    'image',
    'jjson',
    'pdf',
    'pdf_extractor',
    'printer',
    'smtp',
    'url',
    'versioning',
    'video',
    'xls',
]
