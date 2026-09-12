/**
 * Google Drive Sync API Client
 * Клиент для работы с REST API синхронизации
 */

class SyncApiClient {
  constructor(baseUrl = '/api/admin/sync') {
    this.baseUrl = baseUrl;
    this.timeout = 10000;
  }

  /**
   * Выполнить GET запрос
   */
  async get(endpoint) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`[SyncApiClient] GET ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Выполнить POST запрос
   */
  async post(endpoint, data = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`[SyncApiClient] POST ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Получить статус синхронизации
   */
  async getStatus() {
    return this.get('/status');
  }

  /**
   * Получить статистику
   */
  async getStats() {
    return this.get('/stats');
  }

  /**
   * Получить информацию о Google Drive
   */
  async getDriveInfo() {
    return this.get('/drive-info');
  }

  /**
   * Получить конфигурацию
   */
  async getConfig() {
    return this.get('/config');
  }

  /**
   * Запустить планировщик
   */
  async startScheduler(interval = 6) {
    return this.post('/start', { sync_interval_hours: interval });
  }

  /**
   * Остановить планировщик
   */
  async stopScheduler() {
    return this.post('/stop');
  }

  /**
   * Синхронизировать
   */
  async syncNow(syncType = 'all') {
    return this.post('/sync-now', { sync_type: syncType });
  }

  /**
   * Проверить подключение
   */
  async testConnection() {
    return this.post('/test-connection');
  }

  /**
   * Обновить конфигурацию
   */
  async updateConfig(config) {
    return this.post('/config', config);
  }
}
