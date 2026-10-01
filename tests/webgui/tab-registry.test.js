// Тесты для TabRegistry

import { TabRegistry } from '../../src/api/webgui/core/tab-registry.js';

description('TabRegistry основные функции');

test('getAll возвращает массив со всеми определениями вкладок', () => {
  const all = TabRegistry.getAll();
  expect(Array.isArray(all)).toBe(true);
  expect(all.length).toBeGreaterThan(0);
});

test('getById возвращает правильную вкладку', () => {
  const tab = TabRegistry.getById('about_system');
  expect(tab).toBeDefined();
  expect(tab.id).toBe('about_system');
});

test('getFiltered фильтрует по роли и статусу приложений', () => {
  const filtered = TabRegistry.getFiltered(null, 'admin');
  expect(Array.isArray(filtered)).toBe(true);
  // По умолчанию все вкладки, имеющие роль admin, должны быть включены
  const hasAdmin = filtered.every(t => t.roles?.includes('admin'));
  expect(hasAdmin).toBe(true);
});
