# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Telemetry - Security Normalizer
# =============================================================================
# Description:
#   Нормализатор событий журнала безопасности Windows Security Event Log.
#   Извлекает и структурирует атрибуты пользователей, процессов, сессий и политик.
#
# Usage Examples:
#   Python API:
#     from apps.windows.telemetry.security_normalizer import SecurityEventNormalizer
#
#     normalizer = SecurityEventNormalizer()
#     item, raw = normalizer.normalize_event(event_dict)
#
# File: security_normalizer.py
# Project: ai-breadboard
# Package: apps.windows.telemetry
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 02:15:00
# =============================================================================

from __future__ import annotations
"""Нормализатор событий журнала безопасности Windows Security Event Log."""

import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import SecurityEventItem, SecurityEventRaw


def _parse_int(val: Any, default: int = 0) -> int:
    """Безопасный парсинг целого числа из строки, включая шестнадцатеричные значения (0x...)."""
    if val is None:
        return default
    if isinstance(val, int):
        return val
    s = str(val).strip()
    if not s or s == '-':
        return default
    try:
        if s.startswith(('0x', '0X')):
            return int(s, 16)
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return default


class SecurityEventNormalizer:
    """Нормализатор сырых XML и словарей событий Windows Security в типизированные модели."""

    EVENT_DESCRIPTIONS = {
        4624: 'Успешный вход пользователя в систему',
        4625: 'Неудачная попытка входа в систему',
        4634: 'Завершение сеанса пользователя (Logoff)',
        4647: 'Пользователь инициировал выход из системы',
        4672: 'Назначение специальных привилегий администратора',
        4688: 'Создание нового процесса',
        4689: 'Завершение процесса',
        4697: 'Установка новой системной службы',
        4698: 'Создание запланированной задачи (Task Scheduler)',
        4702: 'Изменение параметров запланированной задачи',
        4719: 'Изменение системной политики аудита безопасности',
        4720: 'Создание учетной записи пользователя',
        4722: 'Включение учетной записи пользователя',
        4723: 'Попытка изменения пароля пользователя',
        4724: 'Сброс пароля учетной записи пользователя',
        4725: 'Отключение учетной записи пользователя',
        4726: 'Удаление учетной записи пользователя',
        4732: 'Добавление пользователя в локальную группу безопасности',
        4738: 'Изменение параметров учетной записи пользователя',
        4740: 'Блокировка учетной записи пользователя',
        4768: 'Запрос билета Kerberos TGT (Authentication Ticket)',
        4769: 'Запрос сервисного билета Kerberos (Service Ticket)',
        4771: 'Сбой предварительной проверки подлинности Kerberos',
        4776: 'Проверка учетных данных контроллером (NTLM/MSV1_0)',
        1102: 'ВНИМАНИЕ: Журнал аудита безопасности был очищен',
    }

    def normalize_event(
        self,
        event_dict: Dict[str, Any],
        extract_raw: bool = True,
    ) -> Tuple[SecurityEventItem, Optional[SecurityEventRaw]]:
        """Нормализовать срез события безопасности в типизированную структуру.

        Args:
            event_dict: Словарь события от WevtAPI.
            extract_raw: Формировать ли параллельно объект сырого XML.

        Returns:
            Tuple[SecurityEventItem, Optional[SecurityEventRaw]]:
                Кортеж нормализованного события и опционального сырого объекта.
        """
        event_id = _parse_int(event_dict.get('event_id', 0))
        record_id = _parse_int(event_dict.get('record_id', 0))
        timestamp = str(event_dict.get('timestamp', '') or '')
        computer = str(event_dict.get('computer', '') or '')
        channel = str(event_dict.get('channel', 'Security') or 'Security')
        level = str(event_dict.get('level', 'Information') or 'Information')
        raw_xml = str(event_dict.get('raw_data', '') or '')

        # Получаем данные EventData
        ed = event_dict.get('event_data', {})
        if not ed and raw_xml:
            ed = self._parse_event_data_xml(raw_xml)

        now_iso = datetime.now(timezone.utc).isoformat()
        now_epoch = time.time()

        # Извлечение общих субъектов
        subject_user = ed.get('SubjectUserName') or ed.get('UserName') or ''
        subject_domain = ed.get('SubjectDomainName') or ed.get('UserDomain') or ''
        subject_sid = ed.get('SubjectUserSid') or ed.get('UserSid') or ''

        target_user = ed.get('TargetUserName') or ed.get('MemberName') or ''
        target_domain = ed.get('TargetDomainName') or ''
        target_sid = ed.get('TargetUserSid') or ed.get('MemberSid') or ''

        # Извлечение процессов
        process_id = 0
        process_name = ''
        parent_process_id = 0
        parent_process_name = ''
        command_line = ''

        if event_id == 4688:
            process_id = _parse_int(ed.get('NewProcessId') or ed.get('ProcessId', 0))
            process_name = str(ed.get('NewProcessName') or '')
            parent_process_id = _parse_int(ed.get('ProcessId') or ed.get('ParentProcessId', 0))
            parent_process_name = str(ed.get('ParentProcessName') or '')
            command_line = str(ed.get('CommandLine') or '')
        elif event_id == 4689:
            process_id = _parse_int(ed.get('ProcessId', 0))
            process_name = str(ed.get('ProcessName') or '')
        else:
            process_id = _parse_int(ed.get('ProcessId', 0))
            process_name = str(ed.get('ProcessName') or '')

        # Logon сессия и сеть
        logon_id = str(ed.get('TargetLogonId') or ed.get('SubjectLogonId') or '')
        logon_type_val = ed.get('LogonType')
        logon_type = _parse_int(logon_type_val, -1) if logon_type_val is not None else None
        if logon_type == -1:
            logon_type = None

        elevated_token_val = ed.get('ElevatedToken') or ed.get('TokenElevationType')
        elevated_token = _parse_int(elevated_token_val, -1) if elevated_token_val is not None else None
        if elevated_token == -1:
            elevated_token = None

        source_ip = str(ed.get('IpAddress') or ed.get('WorkstationName') or '')
        if source_ip == '-':
            source_ip = ''
        source_port_val = ed.get('IpPort')
        source_port = _parse_int(source_port_val, -1) if source_port_val is not None else None
        if source_port == -1:
            source_port = None

        # Объект и статусы
        object_name = (
            ed.get('ObjectName')
            or ed.get('ServiceName')
            or ed.get('TaskName')
            or ed.get('TargetName')
            or ''
        )
        status_code = str(ed.get('Status') or ed.get('SubStatus') or ed.get('ExitStatus') or '')

        # Формирование русскоязычного сообщения
        message = self._build_human_message(
            event_id=event_id,
            subject_user=subject_user,
            target_user=target_user,
            process_name=process_name,
            process_id=process_id,
            parent_process_name=parent_process_name,
            parent_process_id=parent_process_id,
            command_line=command_line,
            logon_type=logon_type,
            source_ip=source_ip,
            object_name=object_name,
            status_code=status_code,
            default_msg=event_dict.get('message', ''),
        )

        item = SecurityEventItem(
            event_record_id=record_id,
            event_id=event_id,
            timestamp=timestamp,
            created_at=now_epoch,
            computer=computer,
            channel=channel,
            level=level,
            subject_user=subject_user,
            subject_domain=subject_domain,
            subject_sid=subject_sid,
            target_user=target_user,
            target_domain=target_domain,
            target_sid=target_sid,
            process_id=process_id,
            process_name=process_name,
            parent_process_id=parent_process_id,
            parent_process_name=parent_process_name,
            command_line=command_line,
            logon_id=logon_id,
            logon_type=logon_type,
            elevated_token=elevated_token,
            source_ip=source_ip,
            source_port=source_port,
            object_name=object_name,
            status_code=status_code,
            message=message,
            event_data=ed,
            ingested_at=now_iso,
        )

        raw_item = None
        if extract_raw and raw_xml:
            raw_item = SecurityEventRaw(
                event_record_id=record_id,
                event_id=event_id,
                timestamp=timestamp,
                created_at=now_epoch,
                channel=channel,
                raw_xml=raw_xml,
                ingested_at=now_iso,
            )

        return item, raw_item

    def _build_human_message(
        self,
        event_id: int,
        subject_user: str,
        target_user: str,
        process_name: str,
        process_id: int,
        parent_process_name: str,
        parent_process_id: int,
        command_line: str,
        logon_type: Optional[int],
        source_ip: str,
        object_name: str,
        status_code: str,
        default_msg: str = '',
    ) -> str:
        """Сформировать понятное русскоязычное описание события."""
        p_short = process_name.replace('\\', '/').split('/')[-1] if process_name else ''
        parent_short = parent_process_name.replace('\\', '/').split('/')[-1] if parent_process_name else ''

        if event_id == 4688:
            user_part = f"пользователем {subject_user}" if subject_user and subject_user != '-' else ""
            parent_part = f", родитель: {parent_short} (PID {parent_process_id})" if parent_short else ""
            cmd_part = f" [{command_line[:120]}...]" if len(command_line) > 120 else (f" [{command_line}]" if command_line else "")
            return f"Создание процесса: {p_short} (PID {process_id}) {user_part}{parent_part}{cmd_part}".strip()

        if event_id == 4689:
            status_part = f", код завершения {status_code}" if status_code else ""
            return f"Завершение процесса: {p_short} (PID {process_id}){status_part}"

        if event_id == 4624:
            user = target_user or subject_user or 'Неизвестно'
            type_str = f", тип входа {logon_type}" if logon_type is not None else ""
            ip_str = f", IP: {source_ip}" if source_ip else ""
            return f"Успешный вход пользователя: {user}{type_str}{ip_str}"

        if event_id == 4625:
            user = target_user or subject_user or 'Неизвестно'
            status_str = f", статус ошибки {status_code}" if status_code else ""
            ip_str = f", IP: {source_ip}" if source_ip else ""
            return f"Неудачная попытка входа: {user}{status_str}{ip_str}"

        if event_id in (4634, 4647):
            user = target_user or subject_user or 'Пользователь'
            return f"Выход пользователя из системы: {user}"

        if event_id == 4672:
            return f"Назначение привилегий администратора пользователю {subject_user}"

        if event_id == 4697:
            return f"Установка новой службы Windows: {object_name} ({p_short})"

        if event_id == 4698:
            return f"Создание запланированной задачи: {object_name} пользователем {subject_user}"

        if event_id == 4702:
            return f"Обновление запланированной задачи: {object_name}"

        if event_id == 4719:
            return f"Изменение системной политики аудита безопасности администратором {subject_user}"

        if event_id == 4720:
            return f"Создание учетной записи пользователя: {target_user} (инициатор: {subject_user})"

        if event_id == 4722:
            return f"Включение учетной записи: {target_user}"

        if event_id in (4723, 4724):
            return f"Сброс/изменение пароля пользователя: {target_user}"

        if event_id == 4725:
            return f"Отключение учетной записи пользователя: {target_user}"

        if event_id == 4726:
            return f"Удаление учетной записи пользователя: {target_user}"

        if event_id == 4732:
            return f"Добавление пользователя {target_user} в группу безопасности {object_name}"

        if event_id == 4740:
            return f"Блокировка учетной записи пользователя: {target_user}"

        if event_id == 4768:
            return f"Запрос Kerberos TGT для {target_user or subject_user}"

        if event_id == 4771:
            return f"Сбой пре-аутентификации Kerberos для {target_user} (Код: {status_code})"

        if event_id == 4776:
            return f"Проверка учетных данных NTLM для {target_user}"

        if event_id == 1102:
            return f"ВНИМАНИЕ: Журнал аудита безопасности был очищен пользователем {subject_user}!"

        if default_msg:
            return default_msg

        desc = self.EVENT_DESCRIPTIONS.get(event_id, f'Событие безопасности {event_id}')
        return f"{desc} (субъект: {subject_user or target_user or '-'})"

    def _parse_event_data_xml(self, raw_xml: str) -> Dict[str, str]:
        """Извлечь структурированные пары ключ-значение из EventData XML."""
        res: Dict[str, str] = {}
        try:
            root = ET.fromstring(raw_xml)
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]
                if tag in ('Data', 'string', 'Value') and elem.text:
                    name_attr = elem.attrib.get('Name')
                    if name_attr:
                        res[name_attr] = elem.text.strip()
        except Exception:
            pass
        return res


__all__ = ['SecurityEventNormalizer', '_parse_int']
