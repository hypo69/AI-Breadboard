/**
 * =============================================================================
 * Process Name: AI-Breadboard UI - Main Script
 * =============================================================================
 * Description:
 *   Клиентский веб-скрипт модуля main.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/src/api/webgui/network_tab/main.js?v=20261001_v1" type="module"></script>
 *
 * File: main.js
 * Project: ai-breadboard
 * Package: src/api/webgui/network_tab
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-01 13:13:56
 * =============================================================================
 */

// =============================================================================
// Process Name: Windows Network Terminal Tab Client Module
// =============================================================================
// Description:
//   Frontend controller for /apps/windows/network.
//   Manages internet speedtest, ping/latency benchmark, network adapters,
//   active connections, listening ports, live packet capture (DPI), PCAP upload,
//   and AI diagnostics.
// =============================================================================

(function() {
  let isNetInitialized = false;
  let netEventSource = null;
  let capturedPackets = [];
  let allConnections = [];
  let allAdapters = [];
  let allLanDevices = [];
  let activeConnFilter = 'all';
  let isSpeedtestRunning = false;
  let isLanScanRunning = false;

  // Format bytes to human readable format
  function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  // Check overall network status and TShark availability
  async function fetchNetworkStatus() {
    const engineBadge = document.getElementById('net-engine-status');
    const tsharkBadge = document.getElementById('net-tshark-status');
    const kpiAdapters = document.getElementById('net-kpi-adapters');
    const kpiAdaptersActive = document.getElementById('net-kpi-adapters-active');
    const kpiConns = document.getElementById('net-kpi-conns');
    const kpiListening = document.getElementById('net-kpi-listening');
    const kpiPackets = document.getElementById('net-kpi-packets');
    const kpiAnomalies = document.getElementById('net-kpi-anomalies');

    try {
      const res = await fetch('/api/network/status');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (engineBadge) {
        engineBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2 py-1';
        engineBadge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Windows Net: Active';
      }

      if (tsharkBadge) {
        if (data.tshark_available) {
          tsharkBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-2 py-1';
          tsharkBadge.innerText = 'TShark DPI: Доступен';
        } else {
          tsharkBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2 py-1';
          tsharkBadge.innerText = 'TShark DPI: Не найден';
        }
      }

      if (kpiAdapters) kpiAdapters.innerText = data.total_adapters ?? '--';
      if (kpiConns) kpiConns.innerText = data.active_connections_count ?? '--';
      if (kpiListening) kpiListening.innerText = `${data.listening_ports_count ?? 0} слушающих`;
      if (kpiPackets) kpiPackets.innerText = data.total_packets ?? capturedPackets.length;
      
      const anomaliesCount = (data.latest_heuristics?.length || 0) + (data.latest_ai_report?.anomalies?.length || 0);
      if (kpiAnomalies) {
        kpiAnomalies.innerText = `${anomaliesCount} аномалий`;
        kpiAnomalies.style.color = anomaliesCount > 0 ? '#f87171' : '#4ade80';
      }
    } catch (e) {
      console.warn('[NetworkTab] Status check error:', e);
      if (engineBadge) {
        engineBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-2 py-1';
        engineBadge.innerText = 'Windows Net: Ошибка';
      }
    }
  }

  // Load latest or cached speedtest
  async function fetchLatestSpeedtest() {
    try {
      const res = await fetch('/api/network/speedtest/latest');
      if (!res.ok) return;
      const data = await res.json();
      if (data && data.download) {
        renderSpeedtestResults(data);
      }
    } catch (e) {
      console.debug('[NetworkTab] No latest speedtest data:', e);
    }
  }

  // Run full internet speedtest
  async function runInternetSpeedtest() {
    if (isSpeedtestRunning) return;
    isSpeedtestRunning = true;

    const btn = document.getElementById('btn-run-speedtest');
    const statusText = document.getElementById('speedtest-status-text');
    const summaryText = document.getElementById('speed-summary-text');

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Тестирование...';
    }
    if (statusText) statusText.innerText = 'Измерение Ping, Download, Upload...';
    if (summaryText) summaryText.innerText = 'Выполняется опрос Cloudflare CDN и DNS серверов...';

    try {
      const res = await fetch('/api/network/speedtest/run', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderSpeedtestResults(data);
      if (statusText) statusText.innerText = `Завершено: ${new Date().toLocaleTimeString()}`;
    } catch (e) {
      console.error('[NetworkTab] Speedtest error:', e);
      window.showToast?.('Ошибка Speedtest: ' + e.message, 'danger') || alert('Ошибка Speedtest: ' + e.message);
      if (statusText) statusText.innerText = 'Ошибка выполнения теста';
    } finally {
      isSpeedtestRunning = false;
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Запустить тест скорости';
      }
    }
  }

  // Render speedtest report to UI
  function renderSpeedtestResults(data) {
    const valDown = document.getElementById('speed-val-download');
    const subDown = document.getElementById('speed-sub-download');
    const valUp = document.getElementById('speed-val-upload');
    const subUp = document.getElementById('speed-sub-upload');
    const valPing = document.getElementById('speed-val-ping');
    const subJitter = document.getElementById('speed-sub-jitter');
    const valGrade = document.getElementById('speed-val-grade');
    const subIsp = document.getElementById('speed-sub-isp');
    const badgeIp = document.getElementById('speed-badge-ip');
    const badgeLoc = document.getElementById('speed-badge-location');
    const summaryText = document.getElementById('speed-summary-text');
    const kpiSpeed = document.getElementById('net-kpi-speed');
    const kpiPing = document.getElementById('net-kpi-ping');
    const serversTbody = document.getElementById('speed-servers-tbody');

    const downMbps = data.download?.speed_mbps || 0;
    const downMBs = data.download?.speed_mb_s || 0;
    const upMbps = data.upload?.speed_mbps || 0;
    const upMBs = data.upload?.speed_mb_s || 0;
    const pingMs = data.ping_ms || 0;
    const jitterMs = data.jitter_ms || 0;
    const meta = data.meta || {};
    const quality = data.quality || {};

    if (valDown) valDown.innerText = `${downMbps} Mbps`;
    if (subDown) subDown.innerText = `${downMBs} MB/s (${data.download?.duration_s || 0}s)`;
    if (valUp) valUp.innerText = `${upMbps} Mbps`;
    if (subUp) subUp.innerText = `${upMBs} MB/s (${data.upload?.duration_s || 0}s)`;
    if (valPing) valPing.innerText = `${pingMs} ms`;
    if (subJitter) subJitter.innerText = `Jitter: ${jitterMs} ms`;
    
    if (valGrade) {
      valGrade.innerText = quality.rating || '--';
      valGrade.style.color = quality.color || '#fbbf24';
    }
    if (subIsp) subIsp.innerText = `Провайдер: ${meta.isp || 'Неизвестно'}`;
    if (badgeIp) badgeIp.innerText = `Внешний IP: ${meta.ip || '--'}`;
    if (badgeLoc) badgeLoc.innerText = `Локация: ${meta.city || ''} ${meta.country || ''} (${meta.colo || 'Edge'})`.trim();
    if (summaryText) summaryText.innerText = `${quality.grade || 'Оценка соединения'}. ${quality.summary || ''}`;

    // Top KPI cards
    if (kpiSpeed) kpiSpeed.innerText = `${downMbps} Mbps`;
    if (kpiPing) kpiPing.innerText = `Ping: ${pingMs} ms`;

    // DNS & Edge servers table
    if (serversTbody && Array.isArray(data.servers)) {
      serversTbody.innerHTML = data.servers.map(s => {
        const isOnline = s.avg_ms > 0;
        const statusBadge = isOnline 
          ? '<span class="proto-badge status-badge-up">Online</span>' 
          : '<span class="proto-badge status-badge-down">Offline</span>';
        
        return `
          <tr>
            <td class="fw-bold text-white"><i class="bi bi-hdd-network me-1 text-info"></i>${s.name}</td>
            <td class="text-secondary font-monospace">${s.host}</td>
            <td style="text-align: right;" class="text-info fw-bold font-monospace">${isOnline ? `${s.avg_ms} ms` : '--'}</td>
            <td style="text-align: right;" class="text-muted font-monospace">${isOnline ? `${s.min_ms} ms` : '--'}</td>
            <td style="text-align: right;" class="text-muted font-monospace">${isOnline ? `${s.max_ms} ms` : '--'}</td>
            <td style="text-align: right;" class="text-warning font-monospace">${isOnline ? `${s.jitter_ms} ms` : '--'}</td>
            <td>${statusBadge}</td>
          </tr>
        `;
      }).join('');
    }
  }

  // Fetch host network adapters
  async function fetchAdapters() {
    const tbody = document.getElementById('net-adapters-tbody');
    const ifaceSelect = document.getElementById('net-interface-select');
    const kpiActive = document.getElementById('net-kpi-adapters-active');

    try {
      const res = await fetch('/api/network/interfaces');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const adapters = await res.json();
      allAdapters = Array.isArray(adapters) ? adapters : [];

      let activeCount = 0;

      if (ifaceSelect) {
        ifaceSelect.innerHTML = allAdapters.map(a => `
          <option value="${a.name || a.id}">${a.name} (${a.description || 'Ethernet'}) - ${a.status}</option>
        `).join('');
      }

      if (tbody) {
        if (allAdapters.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Сетевые адаптеры не обнаружены.</td></tr>';
          return;
        }

        tbody.innerHTML = allAdapters.map(a => {
          if (a.is_up) activeCount++;
          const statusClass = a.is_up ? 'status-badge-up' : 'status-badge-down';
          const speedDisplay = a.speed_mbps ? `${a.speed_mbps} Mbps` : '--';
          const ipDisplay = a.ipv4 && a.ipv4.length > 0 ? a.ipv4.join(', ') : '--';

          return `
            <tr>
              <td class="fw-bold text-white"><i class="bi bi-hdd-network me-1 text-info"></i>${a.name}</td>
              <td class="text-secondary small text-truncate" style="max-width: 220px;" title="${a.description}">${a.description || '--'}</td>
              <td class="text-info">${ipDisplay}</td>
              <td class="text-muted small">${a.mac || '--'}</td>
              <td><span class="badge bg-dark border border-secondary text-light">${speedDisplay}</span></td>
              <td><span class="proto-badge ${statusClass}">${a.status || 'Unknown'}</span></td>
              <td style="text-align: right;" class="text-success">${formatBytes(a.bytes_sent)}</td>
              <td style="text-align: right;" class="text-primary">${formatBytes(a.bytes_recv)}</td>
            </tr>
          `;
        }).join('');
      }

      if (kpiActive) kpiActive.innerText = `${activeCount} активных`;
    } catch (e) {
      console.error('[NetworkTab] Failed to fetch adapters:', e);
      if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-center py-3 text-danger">Ошибка загрузки адаптеров: ${e.message}</td></tr>`;
    }
  }

  // Fetch active connections and listening ports
  async function fetchConnections() {
    const tbody = document.getElementById('net-conns-tbody');
    const badgeConn = document.getElementById('badge-conn-count');
    const kpiConns = document.getElementById('net-kpi-conns');
    const kpiListening = document.getElementById('net-kpi-listening');

    try {
      const res = await fetch('/api/network/connections?limit=250');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const conns = Array.isArray(data.connections) ? data.connections : [];
      const listening = Array.isArray(data.listening_ports) ? data.listening_ports : [];
      allConnections = [...listening, ...conns];

      if (badgeConn) badgeConn.innerText = allConnections.length;
      if (kpiConns) kpiConns.innerText = conns.length;
      if (kpiListening) kpiListening.innerText = `${listening.length} слушающих`;

      renderConnectionsTable();
    } catch (e) {
      console.error('[NetworkTab] Failed to fetch connections:', e);
      if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-danger">Ошибка загрузки соединений: ${e.message}</td></tr>`;
    }
  }

  // Render connections table with current filter and search
  function renderConnectionsTable() {
    const tbody = document.getElementById('net-conns-tbody');
    const searchInput = document.getElementById('net-conns-filter');
    const query = (searchInput?.value || '').toLowerCase().trim();

    if (!tbody) return;

    let filtered = allConnections.filter(c => {
      // Type filter
      if (activeConnFilter === 'LISTEN' && c.status !== 'LISTEN') return false;
      if (activeConnFilter === 'ESTABLISHED' && c.status !== 'ESTABLISHED') return false;
      if (activeConnFilter === 'UDP' && c.protocol !== 'UDP') return false;

      // Text query
      if (query) {
        const text = `${c.protocol} ${c.local_address} ${c.remote_address} ${c.status} ${c.pid} ${c.process_name}`.toLowerCase();
        return text.includes(query);
      }
      return true;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Соединения, удовлетворяющие критериям, не найдены.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.slice(0, 150).map((c, idx) => {
      const protoClass = c.protocol === 'TCP' ? 'proto-tcp' : (c.protocol === 'UDP' ? 'proto-udp' : 'proto-other');
      let statusClass = 'proto-other';
      if (c.status === 'LISTEN') statusClass = 'status-badge-listen';
      else if (c.status === 'ESTABLISHED') statusClass = 'status-badge-established';

      return `
        <tr class="net-conn-row" data-idx="${idx}" style="cursor: pointer;" title="Кликните для детального анализа">
          <td><span class="proto-badge ${protoClass}">${c.protocol || 'TCP'}</span></td>
          <td class="text-info font-monospace">${c.local_address || '-'}</td>
          <td class="text-secondary font-monospace">${c.remote_address || '-'}</td>
          <td><span class="proto-badge ${statusClass}">${c.status || '-'}</span></td>
          <td class="text-muted font-monospace">${c.pid || '-'}</td>
          <td class="fw-bold text-white"><i class="bi bi-app me-1 text-muted"></i>${c.process_name || 'Неизвестно'}</td>
        </tr>
      `;
    }).join('');

    // Modal inspection on row click
    tbody.querySelectorAll('.net-conn-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const item = filtered[idx];
        if (!item || !window.AITableModal) return;

        window.AITableModal.show({
          icon: '📡',
          title: `Сетевое соединение [${item.protocol || 'TCP'}]`,
          subtitle: `${item.process_name} (PID: ${item.pid || 'N/A'})`,
          tableType: 'network',
          badges: [
            { text: item.protocol || 'TCP', class: 'badge bg-primary' },
            { text: item.status || 'UNKNOWN', class: 'badge bg-info' },
            { text: `PID ${item.pid || '-'}`, class: 'badge bg-secondary' }
          ],
          metadata: [
            { label: 'Имя процесса', value: item.process_name || '-' },
            { label: 'PID', value: String(item.pid || '-') },
            { label: 'Протокол', value: item.protocol || '-' },
            { label: 'Локальный адрес', value: item.local_address || '-' },
            { label: 'Удаленный адрес', value: item.remote_address || '-' },
            { label: 'Состояние', value: item.status || '-' }
          ],
          rawTitle: 'Полные данные сокета',
          rawContent: JSON.stringify(item, null, 2),
          requestData: item
        });
      };
    });
  }

  // Render captured packets table
  function renderPacketsTable() {
    const tbody = document.getElementById('net-packets-tbody');
    const badge = document.getElementById('net-captured-badge');
    const filterInput = document.getElementById('net-table-filter');
    const filter = (filterInput?.value || '').toLowerCase().trim();

    if (!tbody) return;

    if (badge) badge.innerText = `${capturedPackets.length} пакетов`;

    if (capturedPackets.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Пакеты не захвачены. Выберите адаптер и нажмите "Старт захвата".</td></tr>';
      return;
    }

    const filtered = capturedPackets.filter(p => {
      if (!filter) return true;
      const str = `${p.number || p.packet_number || ''} ${p.source || ''} ${p.destination || ''} ${p.protocol || ''} ${p.info || ''}`.toLowerCase();
      return str.includes(filter);
    });

    const pagePackets = filtered.slice(-100);
    tbody.innerHTML = pagePackets.map((p, idx) => {
      const proto = (p.protocol || 'OTHER').toUpperCase();
      let protoClass = 'proto-other';
      if (proto.includes('TCP')) protoClass = 'proto-tcp';
      else if (proto.includes('UDP')) protoClass = 'proto-udp';
      else if (proto.includes('TLS') || proto.includes('SSL')) protoClass = 'proto-tls';
      else if (proto.includes('HTTP')) protoClass = 'proto-http';
      else if (proto.includes('DNS')) protoClass = 'proto-dns';

      return `
        <tr class="net-packet-row" data-idx="${idx}" style="cursor: pointer;" title="Кликните для AI анализа">
          <td class="text-muted">${p.number || p.packet_number || '--'}</td>
          <td>${p.timestamp ? (typeof p.timestamp === 'number' ? new Date(p.timestamp * 1000).toLocaleTimeString() : p.timestamp) : '--'}</td>
          <td style="color: #38bdf8;">${p.source || '--'}</td>
          <td style="color: #a855f7;">${p.destination || '--'}</td>
          <td><span class="proto-badge ${protoClass}">${proto}</span></td>
          <td style="text-align: right;">${p.length || 0} B</td>
          <td class="text-truncate" style="max-width: 320px;">${p.info || '--'}</td>
        </tr>
      `;
    }).join('');

    tbody.querySelectorAll('.net-packet-row').forEach(row => {
      row.onclick = () => {
        const idx = parseInt(row.getAttribute('data-idx'), 10);
        const p = pagePackets[idx];
        if (!p || !window.AITableModal) return;

        window.AITableModal.show({
          icon: '🌐',
          title: `Пакет #${p.number || p.packet_number || 'N/A'} [${p.protocol || 'TCP'}]`,
          subtitle: `${p.source || '0.0.0.0'} ➔ ${p.destination || '0.0.0.0'}`,
          tableType: 'network',
          badges: [
            { text: (p.protocol || 'TCP').toUpperCase(), class: 'badge bg-primary' },
            { text: `${p.length || 0} Bytes`, class: 'badge bg-secondary' }
          ],
          metadata: [
            { label: 'Номер пакета', value: String(p.number || p.packet_number || '-') },
            { label: 'Протокол', value: (p.protocol || 'TCP').toUpperCase() },
            { label: 'Источник (Source)', value: p.source || '-' },
            { label: 'Назначение (Destination)', value: p.destination || '-' },
            { label: 'Размер полезной нагрузки', value: `${p.length || 0} байт` },
            { label: 'Информация', value: p.info || 'Нет данных', fullWidth: true }
          ],
          rawTitle: 'Детализация фрейма (DPI)',
          rawContent: JSON.stringify(p, null, 2),
          requestData: p
        });
      };
    });
  }

  // Start live packet capture
  async function startLiveCapture() {
    const ifaceSelect = document.getElementById('net-interface-select');
    const filterInput = document.getElementById('net-capture-filter');
    const startBtn = document.getElementById('btn-start-live-capture');
    const stopBtn = document.getElementById('btn-stop-live-capture');

    const iface = ifaceSelect?.value || '1';
    const filter = filterInput?.value || '';

    try {
      const res = await fetch(`/api/network/start-capture?interface=${encodeURIComponent(iface)}&display_filter=${encodeURIComponent(filter)}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      if (startBtn) startBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = false;

      // Start SSE event source
      if (netEventSource) netEventSource.close();
      netEventSource = new EventSource('/api/network/packets/stream');
      netEventSource.onmessage = async () => {
        try {
          const packRes = await fetch('/api/network/packets?limit=50');
          if (packRes.ok) {
            const data = await packRes.json();
            if (Array.isArray(data.packets)) {
              capturedPackets = data.packets;
              renderPacketsTable();
            }
          }
        } catch (e) {
          console.warn('[NetworkTab] Packet poll error:', e);
        }
      };
    } catch (e) {
      console.error('[NetworkTab] Live capture error:', e);
      window.showToast?.('Ошибка запуска захвата: ' + e.message, 'danger') || alert('Ошибка запуска захвата: ' + e.message);
    }
  }

  // Stop live packet capture
  async function stopLiveCapture() {
    const startBtn = document.getElementById('btn-start-live-capture');
    const stopBtn = document.getElementById('btn-stop-live-capture');

    if (netEventSource) {
      netEventSource.close();
      netEventSource = null;
    }

    try {
      await fetch('/api/network/stop-capture', { method: 'POST' });
    } catch (e) {
      console.warn('[NetworkTab] Stop capture error:', e);
    }

    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
  }

  // Analyze uploaded PCAP file
  async function analyzePcapFile() {
    const fileInput = document.getElementById('net-pcap-file');
    const statusEl = document.getElementById('net-upload-status');
    const healthEl = document.getElementById('pcap-health-score');
    const anomaliesEl = document.getElementById('pcap-anomalies-count');
    const heuristicsEl = document.getElementById('pcap-heuristics-list');
    const recommendationsEl = document.getElementById('pcap-ai-recommendations');

    const file = fileInput?.files?.[0];
    if (!file) {
      window.showToast?.('Выберите файл .pcap для анализа', 'warning') || alert('Выберите файл .pcap для анализа');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_packets', '500');

    if (statusEl) statusEl.innerText = 'Загрузка и глубокий анализ пакетов...';

    try {
      const res = await fetch('/api/network/analyze/pcap', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const report = await res.json();

      if (statusEl) statusEl.innerText = `Анализ завершен (${report.stats?.total_packets || 0} пакетов)`;
      if (healthEl) healthEl.innerText = `${report.ai_report?.health_score ?? 100}/100`;

      const anomaliesCount = (report.heuristics?.length || 0) + (report.ai_report?.anomalies?.length || 0);
      if (anomaliesEl) {
        anomaliesEl.innerText = String(anomaliesCount);
        anomaliesEl.className = `net-value mt-1 ${anomaliesCount > 0 ? 'text-danger' : 'text-success'}`;
      }

      if (heuristicsEl) {
        if (Array.isArray(report.heuristics) && report.heuristics.length > 0) {
          heuristicsEl.innerHTML = report.heuristics.map(h => `<div class="text-warning mb-1"><i class="bi bi-exclamation-triangle-fill me-1"></i>${h}</div>`).join('');
        } else {
          heuristicsEl.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Эвристических угроз не выявлено.</span>';
        }
      }

      if (recommendationsEl) {
        if (Array.isArray(report.ai_report?.recommended_actions) && report.ai_report.recommended_actions.length > 0) {
          recommendationsEl.innerHTML = report.ai_report.recommended_actions.map(r => `<div class="text-info mb-1"><i class="bi bi-arrow-right-short me-1"></i>${r}</div>`).join('');
        } else {
          recommendationsEl.innerHTML = '<span class="text-muted">Рекомендаций нет, система функционирует штатно.</span>';
        }
      }

      if (Array.isArray(report.sample_packets) && report.sample_packets.length > 0) {
        capturedPackets = report.sample_packets;
        renderPacketsTable();
      }
    } catch (e) {
      console.error('[NetworkTab] PCAP upload error:', e);
      if (statusEl) statusEl.innerText = 'Ошибка: ' + e.message;
      window.showToast?.('Ошибка анализа PCAP: ' + e.message, 'danger') || alert('Ошибка анализа PCAP: ' + e.message);
    }
  }

  // Load available local subnets into dropdown
  async function fetchLanSubnets() {
    const select = document.getElementById('select-net-subnet');
    if (!select) return;
    try {
      const res = await fetch('/api/network/subnets');
      if (!res.ok) return;
      const data = await res.json();
      const currentVal = select.value;
      select.innerHTML = '<option value="">Все локальные подсети</option>';
      if (Array.isArray(data.subnets)) {
        data.subnets.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.cidr;
          opt.innerText = `${s.name}: ${s.cidr} (${s.ip})`;
          select.appendChild(opt);
        });
      }
      select.value = currentVal;
    } catch (e) {
      console.debug('[NetworkTab] fetchLanSubnets error:', e);
    }
  }

  // Fetch discovered LAN devices (cache or active scan)
  async function fetchLanDevices(scan = false) {
    if (isLanScanRunning && scan) return;
    const tbody = document.getElementById('table-net-devices-body');
    const badgeCount = document.getElementById('badge-devices-count');
    const statusBadge = document.getElementById('net-devices-status-badge');
    const scanBtn = document.getElementById('btn-scan-lan-devices');
    const subnetSelect = document.getElementById('select-net-subnet');
    const targetSubnet = subnetSelect ? subnetSelect.value : '';

    if (scan) {
      isLanScanRunning = true;
      if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Сканирование...';
      }
      if (statusBadge) {
        statusBadge.className = 'badge bg-warning text-dark';
        statusBadge.innerText = 'Активный опрос (SendARP)...';
      }
    }

    try {
      const url = `/api/network/devices?scan=${scan}${targetSubnet ? '&subnet=' + encodeURIComponent(targetSubnet) : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      allLanDevices = data.devices || [];
      if (badgeCount) badgeCount.innerText = allLanDevices.length;
      if (statusBadge) {
        statusBadge.className = 'badge bg-dark border border-secondary text-secondary small';
        statusBadge.innerText = scan ? `Сканировано: ${allLanDevices.length} устр.` : `Кеш: ${allLanDevices.length} устр.`;
      }
      renderLanDevicesTable();
    } catch (e) {
      console.error('[NetworkTab] fetchLanDevices error:', e);
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-3">Ошибка загрузки устройств: ${e.message}</td></tr>`;
      }
    } finally {
      if (scan) {
        isLanScanRunning = false;
        if (scanBtn) {
          scanBtn.disabled = false;
          scanBtn.innerHTML = '<i class="bi bi-radar me-1"></i> Сканировать сеть';
        }
      }
    }
  }

  // Render LAN devices table with search filtering
  function renderLanDevicesTable() {
    const tbody = document.getElementById('table-net-devices-body');
    const searchInput = document.getElementById('search-net-devices');
    if (!tbody) return;

    const query = (searchInput ? searchInput.value.trim().toLowerCase() : '');
    const filtered = allLanDevices.filter(d => {
      if (!query) return true;
      return (
        (d.ip && d.ip.toLowerCase().includes(query)) ||
        (d.mac && d.mac.toLowerCase().includes(query)) ||
        (d.hostname && d.hostname.toLowerCase().includes(query)) ||
        (d.vendor && d.vendor.toLowerCase().includes(query)) ||
        (d.state && d.state.toLowerCase().includes(query))
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4"><i class="bi bi-info-circle me-1"></i> Устройства не найдены. Нажмите «Сканировать сеть» для активного поиска.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(d => {
      let roleBadge = '';
      if (d.is_gateway) {
        roleBadge = '<span class="badge bg-warning text-dark ms-1"><i class="bi bi-router-fill me-1"></i>ШЛЮЗ</span>';
      } else if (d.is_local) {
        roleBadge = '<span class="badge bg-primary ms-1"><i class="bi bi-pc-display me-1"></i>Этот ПК</span>';
      }

      const vendor = d.vendor ? `<span class="fw-semibold text-light">${d.vendor}</span>` : '<span class="text-muted small">Неизвестно</span>';
      const hostname = d.hostname ? `<span class="text-info">${d.hostname}</span>` : '<span class="text-muted">-</span>';
      const mac = d.mac ? `<span class="text-monospace">${d.mac}</span>` : '<span class="text-muted">-</span>';
      
      const methods = (d.discovery_methods || []).map(m => {
        if (m === 'arp_sweep') return '<span class="badge proto-badge proto-tcp" title="Активный опрос ARP">ARP</span>';
        if (m === 'arp_cache') return '<span class="badge proto-badge proto-other" title="Кеш ядра">Cache</span>';
        if (m === 'ssdp') return '<span class="badge proto-badge proto-tls" title="UPnP/SSDP Multicast">SSDP</span>';
        if (m === 'local_interface') return '<span class="badge proto-badge proto-dns" title="Локальный интерфейс">Local</span>';
        return `<span class="badge proto-badge proto-other">${m}</span>`;
      }).join(' ');

      const latency = d.latency_ms !== null && d.latency_ms !== undefined
        ? `<span class="small text-success">${d.latency_ms} ms</span>`
        : '<span class="text-muted small">-</span>';

      return `
        <tr>
          <td><strong class="text-white">${d.ip}</strong>${roleBadge}</td>
          <td>${hostname}</td>
          <td>${mac}</td>
          <td>${vendor}</td>
          <td><span class="badge ${d.state === 'Online' || d.state === 'Reachable' ? 'status-badge-up' : 'status-badge-down'}">${d.state || 'Online'}</span></td>
          <td>${methods || '-'}</td>
          <td style="text-align: right;">${latency}</td>
        </tr>
      `;
    }).join('');
  }

  // Main init function for Network Terminal Tab
  function initNetworkTab() {
    console.log('[NetworkTab] Initializing Windows Network Terminal tab (/apps/windows/network)...');
    fetchNetworkStatus();
    fetchLatestSpeedtest();
    fetchAdapters();
    fetchConnections();
    fetchLanSubnets();
    fetchLanDevices(false);

    if (!isNetInitialized) {
      // Action buttons
      const refreshAllBtn = document.getElementById('btn-refresh-network-all');
      const runSpeedtestBtn = document.getElementById('btn-run-speedtest');
      const refreshAdaptersBtn = document.getElementById('btn-refresh-adapters');
      const refreshConnsBtn = document.getElementById('btn-refresh-conns');
      const startBtn = document.getElementById('btn-start-live-capture');
      const stopBtn = document.getElementById('btn-stop-live-capture');
      const analyzePcapBtn = document.getElementById('btn-analyze-pcap');
      const clearPacketsBtn = document.getElementById('btn-clear-packets');
      const connsFilterInput = document.getElementById('net-conns-filter');
      const tableFilterInput = document.getElementById('net-table-filter');
      const configBtn = document.getElementById('btn-network-config');

      // LAN Devices controls
      const scanLanBtn = document.getElementById('btn-scan-lan-devices');
      const refreshLanBtn = document.getElementById('btn-refresh-lan-devices');
      const searchLanInput = document.getElementById('search-net-devices');
      const subnetSelect = document.getElementById('select-net-subnet');

      if (refreshAllBtn) refreshAllBtn.onclick = () => {
        fetchNetworkStatus();
        fetchLatestSpeedtest();
        fetchAdapters();
        fetchConnections();
        fetchLanSubnets();
        fetchLanDevices(false);
      };
      if (runSpeedtestBtn) runSpeedtestBtn.onclick = runInternetSpeedtest;
      if (refreshAdaptersBtn) refreshAdaptersBtn.onclick = fetchAdapters;
      if (refreshConnsBtn) refreshConnsBtn.onclick = fetchConnections;
      if (startBtn) startBtn.onclick = startLiveCapture;
      if (stopBtn) stopBtn.onclick = stopLiveCapture;
      if (analyzePcapBtn) analyzePcapBtn.onclick = analyzePcapFile;
      if (clearPacketsBtn) clearPacketsBtn.onclick = () => {
        capturedPackets = [];
        renderPacketsTable();
      };

      if (scanLanBtn) scanLanBtn.onclick = () => fetchLanDevices(true);
      if (refreshLanBtn) refreshLanBtn.onclick = () => fetchLanDevices(false);
      if (searchLanInput) searchLanInput.oninput = renderLanDevicesTable;
      if (subnetSelect) subnetSelect.onchange = () => fetchLanDevices(false);

      if (connsFilterInput) connsFilterInput.oninput = renderConnectionsTable;
      if (tableFilterInput) tableFilterInput.oninput = renderPacketsTable;

      // Filter buttons for connections
      document.querySelectorAll('.btn-filter-conns').forEach(btn => {
        btn.onclick = () => {
          document.querySelectorAll('.btn-filter-conns').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          activeConnFilter = btn.getAttribute('data-filter') || 'all';
          renderConnectionsTable();
        };
      });

      if (configBtn) configBtn.onclick = () => {
        if (typeof window.openAppConfigModal === 'function') {
          window.openAppConfigModal('network_terminal', 'Network Analyzer Terminal');
        }
      };

      isNetInitialized = true;
    }
  }

  window.initNetworkTab = initNetworkTab;
})();
