"""Tests for core modules."""
import unittest
from apps.windows.core.data_model import ProcessInfo, ThreadInfo, SystemState
from apps.windows.core.correlation_engine import CorrelationEngine

class TestDataModels(unittest.TestCase):
    """Test data models."""

    def test_process_info_creation(self):
        """Test ProcessInfo creation."""
        proc = ProcessInfo(pid=1234, name="test.exe", ppid=0)
        self.assertEqual(proc.pid, 1234)
        self.assertEqual(proc.name, "test.exe")
        self.assertEqual(proc.ppid, 0)

    def test_thread_info_creation(self):
        """Test ThreadInfo creation."""
        thread = ThreadInfo(tid=5678, pid=1234, base_priority=8)
        self.assertEqual(thread.tid, 5678)
        self.assertEqual(thread.pid, 1234)

    def test_system_state_creation(self):
        """Test SystemState creation."""
        state = SystemState(processes=[])
        self.assertIsNotNone(state.timestamp)
        self.assertEqual(len(state.processes), 0)


class TestCorrelationEngine(unittest.TestCase):
    """Test correlation engine."""

    def setUp(self):
        """Setup test fixtures."""
        self.engine = CorrelationEngine()

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        self.assertIsNotNone(self.engine)

if __name__ == '__main__':
    unittest.main()
