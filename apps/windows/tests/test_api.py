"""Tests for API layer."""
import unittest
from apps.windows.api import Kernel32API, PsapiAPI

class TestKernel32API(unittest.TestCase):
    """Test Kernel32 API."""

    def setUp(self):
        """Setup test fixtures."""
        self.api = Kernel32API()

    def test_api_initialization(self):
        """Test API initializes."""
        self.assertIsNotNone(self.api.kernel32)

    def test_enumerate_processes(self):
        """Test process enumeration."""
        processes = self.api.enumerate_processes()
        self.assertIsInstance(processes, list)
        self.assertGreater(len(processes), 0)

class TestPsapiAPI(unittest.TestCase):
    """Test PSAPI."""

    def setUp(self):
        """Setup test fixtures."""
        self.api = PsapiAPI()

    def test_api_initialization(self):
        """Test API initializes."""
        self.assertIsNotNone(self.api.psapi)

    def test_enumerate_processes(self):
        """Test process enumeration."""
        pids = self.api.enumerate_processes()
        self.assertIsInstance(pids, list)
        self.assertGreater(len(pids), 0)

if __name__ == '__main__':
    unittest.main()
