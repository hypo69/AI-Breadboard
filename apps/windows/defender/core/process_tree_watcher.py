"""Модуль инспекции дерева процессов и детекции подозрительных цепочек выполнения."""
from __future__ import annotations
import re
from typing import List, Optional
import psutil
from logger import logger
from apps.windows.defender.core.models import SuspiciousProcessChain, ThreatSeverity

class ProcessTreeWatcher:
    """Анализатор дерева процессов и цепочек запуска."""
    SUSPICIOUS_PARENTS = {'winword.exe': 'Microsoft Word', 'excel.exe': 'Microsoft Excel', 'powerpnt.exe': 'Microsoft PowerPoint', 'outlook.exe': 'Microsoft Outlook', 'acrord32.exe': 'Adobe Acrobat Reader', 'acrobat.exe': 'Adobe Acrobat'}
    DANGEROUS_CHILDREN = {'powershell.exe', 'pwsh.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe', 'rundll32.exe', 'regsvr32.exe', 'certutil.exe', 'bitsadmin.exe', 'curl.exe', 'vssadmin.exe', 'schtasks.exe', 'wmic.exe'}
    SUSPICIOUS_CMD_PATTERNS = [(re.compile('-(enc|encodedcommand)\\s+[a-za-z0-9+/=]+', re.I), 'Использование закодированной Base64 команды PowerShell'), (re.compile('bypass\\s+-noprofile', re.I), 'Обход политики выполнения скриптов (ExecutionPolicy Bypass)'), (re.compile('downloadstring|downloaddata|downloadfile', re.I), 'Загрузка удаленного контента через WebClient/Net.Sockets'), (re.compile('\\biex\\b|invoke-expression', re.I), 'Динамическое выполнение кода в памяти (Invoke-Expression / Fileless)'), (re.compile('certutil.*-(decode|urlcache)', re.I), 'Использование Certutil для загрузки/декодирования полезной нагрузки'), (re.compile('bitsadmin.*/transfer', re.I), 'Скрытая загрузка файлов через службу BITS'), (re.compile('vssadmin.*delete\\s+shadows', re.I), 'Попытка удаления теневых копий VSS (типично для Ransomware)')]

    def scan_suspicious_chains(self) -> List[SuspiciousProcessChain]:
        """Сканирование текущих процессов на предмет аномальных связей родитель-потомок.

        Returns:
            List[SuspiciousProcessChain]: Список обнаруженных подозрительных цепочек.
        """
        results: List[SuspiciousProcessChain] = []
        try:
            procs_by_pid = {}
            for p in psutil.process_iter(['pid', 'name', 'ppid', 'cmdline']):
                try:
                    procs_by_pid[p.info['pid']] = p.info
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            for pid, info in procs_by_pid.items():
                pname = (info.get('name') or '').lower()
                ppid = info.get('ppid')
                cmdline_list = info.get('cmdline') or []
                cmdline_str = ' '.join(cmdline_list)
                if ppid and ppid in procs_by_pid:
                    parent_info = procs_by_pid[ppid]
                    parent_name = (parent_info.get('name') or '').lower()
                    if parent_name in self.SUSPICIOUS_PARENTS and pname in self.DANGEROUS_CHILDREN:
                        results.append(SuspiciousProcessChain(parent_process=parent_name, parent_pid=ppid, child_process=pname, child_pid=pid, command_line=cmdline_str, severity=ThreatSeverity.SEVERE, reason=f"Офисное приложение '{self.SUSPICIOUS_PARENTS[parent_name]}' запустило интерпретатор/утилиту '{pname}' (высокий риск эксплуатации макроса/эксплойта)."))
                for pattern, reason in self.SUSPICIOUS_CMD_PATTERNS:
                    if pattern.search(cmdline_str):
                        if not any((r.child_pid == pid for r in results)):
                            results.append(SuspiciousProcessChain(parent_process=f'PID:{ppid}', parent_pid=ppid, child_process=pname, child_pid=pid, command_line=cmdline_str, severity=ThreatSeverity.HIGH, reason=f'Обнаружен опасный шаблон выполнения: {reason}'))
        except Exception as e:
            logger.debug(f'Ошибка анализа дерева процессов: {e}')
        return results