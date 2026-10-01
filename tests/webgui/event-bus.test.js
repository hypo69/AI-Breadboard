// Тесты для CoreEventBus

import { eventBus } from '../../src/api/webgui/core/event-bus.js';

description('CoreEventBus базовые функции');

test('emit вызывает подписанный слушатель', () => {
  const mock = jest.fn();
  eventBus.on('testEvent', mock);
  const payload = { data: 123 };
  eventBus.emit('testEvent', payload);
  expect(mock).toHaveBeenCalledTimes(1);
  const eventArg = mock.mock.calls[0][0];
  expect(eventArg).toBeInstanceOf(CustomEvent);
  expect(eventArg.detail).toEqual(payload);
  eventBus.off('testEvent', mock);
});
