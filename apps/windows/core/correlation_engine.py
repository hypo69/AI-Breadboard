# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard Apps Windows Core - Correlation Engine
# =============================================================================
# Description:
#   Correlation Engine for analyzing relationships between system components
#
# Usage Examples:
#   Python API:
#     from apps.windows.core.correlation_engine import Correlation
#
#     service = Correlation()
#
# File: correlation_engine.py
# Project: ai-breadboard
# Package: apps.windows.core
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-06 03:07:00
# =============================================================================

"""Движок корреляции для анализа взаимосвязей между системными компонентами."""

from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from logger import logger
from .data_model import ProcessInfo, ServiceInfo, DriverInfo, SystemState

@dataclass
class Correlation:
    """Представляет взаимосвязь между компонентами системы."""
    source_type: str
    source_id: Any
    source_name: str
    target_type: str
    target_id: Any
    target_name: str
    relationship_type: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {'source': f'{self.source_type}:{self.source_name}', 'target': f'{self.target_type}:{self.target_name}', 'relationship': self.relationship_type, 'strength': self.strength}

class CorrelationEngine:
    """
    Анализирует корреляции между процессами, службами, драйверами и файлами.
    """

    def __init__(self):
        self.correlations: List[Correlation] = []
        self.logger = logger

    def analyze_system_state(self, state: SystemState) -> List[Correlation]:
        """Analyze correlations in system state"""
        correlations = []
        correlations.extend(self._correlate_services_to_processes(state))
        correlations.extend(self._correlate_processes_to_modules(state))
        correlations.extend(self._correlate_processes_to_files(state))
        correlations.extend(self._correlate_services_to_drivers(state))
        correlations.extend(self._correlate_process_trees(state))
        self.correlations = correlations
        return correlations

    def _correlate_services_to_processes(self, state: SystemState) -> List[Correlation]:
        """Find which processes are running which services"""
        correlations = []
        for service in state.services:
            if service.pid:
                proc = state.get_process_by_pid(service.pid)
                if proc:
                    correlations.append(Correlation(source_type='service', source_id=service.name, source_name=service.display_name, target_type='process', target_id=proc.pid, target_name=proc.name, relationship_type='runs_as', strength=1.0, metadata={'service_state': service.current_state.value, 'process_state': proc.state.value}))
        return correlations

    def _correlate_processes_to_modules(self, state: SystemState) -> List[Correlation]:
        """Find which processes load which modules"""
        correlations = []
        for proc in state.processes:
            for module in proc.modules:
                correlations.append(Correlation(source_type='process', source_id=proc.pid, source_name=proc.name, target_type='module', target_id=module.path, target_name=module.name, relationship_type='loads', strength=1.0, metadata={'path': module.path, 'version': module.version, 'signed': module.is_signed}))
        return correlations

    def _correlate_processes_to_files(self, state: SystemState) -> List[Correlation]:
        """Find file handles per process"""
        correlations = []
        for proc in state.processes:
            file_handles = [h for h in proc.handles if h.object_type == 'File']
            for handle in file_handles:
                correlations.append(Correlation(source_type='process', source_id=proc.pid, source_name=proc.name, target_type='file', target_id=handle.handle_value, target_name=handle.object_name, relationship_type='has_open_handle', strength=1.0, metadata={'handle': hex(handle.handle_value), 'access': hex(handle.access_mask)}))
        return correlations

    def _correlate_services_to_drivers(self, state: SystemState) -> List[Correlation]:
        """Link services to their drivers"""
        correlations = []
        for service in state.services:
            if service.executable:
                driver = self._find_driver_for_service(service, state)
                if driver:
                    correlations.append(Correlation(source_type='service', source_id=service.name, source_name=service.display_name, target_type='driver', target_id=driver.name, target_name=driver.display_name, relationship_type='uses', strength=0.8, metadata={'service_path': service.executable, 'driver_path': driver.path}))
        return correlations

    def _correlate_process_trees(self, state: SystemState) -> List[Correlation]:
        """Correlate parent and child processes"""
        correlations = []
        pid_to_process = {p.pid: p for p in state.processes}
        for proc in state.processes:
            if proc.ppid and proc.ppid in pid_to_process:
                parent = pid_to_process[proc.ppid]
                correlations.append(Correlation(source_type='process', source_id=parent.pid, source_name=parent.name, target_type='process', target_id=proc.pid, target_name=proc.name, relationship_type='spawned', strength=1.0, metadata={'parent_pid': parent.pid, 'child_pid': proc.pid}))
        return correlations

    @staticmethod
    def _find_driver_for_service(service: ServiceInfo, state: SystemState) -> Optional[DriverInfo]:
        """Find driver associated with service"""
        for driver in state.drivers:
            if driver.service_name.lower() == service.name.lower():
                return driver
        '# TODO: вернуть корректное значение'
        logger.error('Функция _find_driver_for_service вернула пустой результат')
        return None

    def get_process_chain(self, pid: int, state: SystemState) -> List[ProcessInfo]:
        """Get chain of parent processes for a PID"""
        chain = []
        pid_to_process = {p.pid: p for p in state.processes}
        current_pid = pid
        while current_pid:
            if current_pid not in pid_to_process:
                break
            proc = pid_to_process[current_pid]
            chain.append(proc)
            current_pid = proc.ppid
        return chain

    def get_child_processes(self, pid: int, state: SystemState) -> List[ProcessInfo]:
        """Get all child processes recursively"""
        children = []
        for proc in state.processes:
            if proc.ppid == pid:
                children.append(proc)
                children.extend(self.get_child_processes(proc.pid, state))
        return children

    def get_services_for_process(self, pid: int) -> List[ServiceInfo]:
        """Get services running in a specific process"""
        services = []
        for corr in self.correlations:
            if corr.relationship_type == 'runs_as' and corr.target_type == 'process' and (corr.target_id == pid):
                services.append(corr.source_id)
        return services

    def find_anomalous_correlations(self, state: SystemState) -> List[Dict[str, Any]]:
        """Find unusual correlations that may indicate issues"""
        anomalies = []
        process_instances: Dict[str, Set[int]] = {}
        for proc in state.processes:
            if proc.name not in process_instances:
                process_instances[proc.name] = set()
            process_instances[proc.name].add(proc.ppid)
        for name, parents in process_instances.items():
            if len(parents) > 1 and name not in ['svchost.exe', 'conhost.exe']:
                anomalies.append({'type': 'multiple_parents', 'process': name, 'parent_count': len(parents), 'severity': 'medium'})
        for proc in state.processes:
            if proc.executable:
                if any((x in proc.executable.lower() for x in ['temp', 'appdata', 'downloads'])):
                    anomalies.append({'type': 'suspicious_location', 'process': proc.name, 'path': proc.executable, 'severity': 'high'})
        return anomalies

    def export_graph(self) -> Dict[str, Any]:
        """Export correlation graph for visualization"""
        nodes = []
        edges = []
        for corr in self.correlations:
            source_node = f'{corr.source_type}:{corr.source_id}'
            target_node = f'{corr.target_type}:{corr.target_id}'
            nodes.append({'id': source_node, 'label': corr.source_name, 'type': corr.source_type})
            nodes.append({'id': target_node, 'label': corr.target_name, 'type': corr.target_type})
            edges.append({'source': source_node, 'target': target_node, 'label': corr.relationship_type, 'strength': corr.strength})
        return {'nodes': nodes, 'edges': edges, 'correlation_count': len(self.correlations)}