# -*- coding: utf-8 -*-
import unittest
from apps.dashboard.dashboard import Dashboard

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.dashboard = Dashboard()

    def test_initialization(self):
        self.assertGreater(len(self.dashboard.modules), 0)

    def test_get_system_overview(self):
        overview = self.dashboard.get_system_overview()
        self.assertIn('timestamp', overview)
        self.assertIn('modules_loaded', overview)
        self.assertGreater(overview['modules_loaded'], 0)

    def test_list_modules(self):
        modules = self.dashboard.list_modules()
        self.assertIsInstance(modules, dict)
        self.assertIn('processes', modules)
        self.assertIn('performance', modules)

    def test_get_module(self):
        mod = self.dashboard.get_module('processes')
        self.assertIsNotNone(mod)

if __name__ == '__main__':
    unittest.main()
