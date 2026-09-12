// Network Terminal Tab JS Module
(function() {
  let netWs = null;
  let isNetInitialized = false;
  let capturedPackets = [];

  async function checkTSharkStatus() {
    const badge = document.getElementById('net-tshark-status');
    try {
      const res = await fetch('/api/v1/network/status');
      if (!res.ok) throw new Error('Status error');
      const data = await res.json();
      if (badge) {
        if (data.available) {
          badge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          badge.innerText = 'TShark: Доступен';
        } else {
          badge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-3 py-2';
          badge.innerText = 'TShark: Не найден';
        }
      }
    } catch (e) {
      if (badge) {
        badge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
        badge.innerText = 'TShark: Ошибка';
      }
    }
  }

  async function fetchInterfaces() {
    const select = document.getElementById('net-interface-select');
    if (!select) return;
    try {
      const res = await fetch('/api/v1/network/interfaces');
      if (!res.ok) {
        select.innerHTML = '<option value="">Интерфейсы недоступны</option>';
        return;
      }
      const interfaces = await res.json();
      if (!Array.isArray(interfaces) || interfaces.length === 0) {
        select.innerHTML = '<option value="">Интерфейсы не найдены</option>';
        return;
      }

      select.innerHTML = interfaces.map(iface => `
        <option value="${iface.name || iface.id}">${iface.name} (${iface.description || 'Ethernet'})</option>
      `).join('');
    } catch (e) {
      console.error('[NetworkTab] Failed to fetch interfaces:', e);
      select.innerHTML = '<option value="">Ошибка загрузки интерфейсов</option>';
    }
  }

  function renderPacketsTable() {
    const tbody = document.getElementById('net-packets-tbody');
    const filterInput = document.getElementById('net-table-filter');
    const filter = (filterInput?.value || '').toLowerCase().trim();
    if (!tbody) return;

    if (capturedPackets.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Нет захваченных пакетов. Запустите захват или загрузите PCAP.</td></tr>';
      return;
    }

    const filtered = capturedPackets.filter(p => {
      if (!filter) return true;
      return (
        String(p.number).includes(filter) ||
        (p.source || '').toLowerCase().includes(filter) ||
        (p.destination || '').toLowerCase().includes(filter) ||
        (p.protocol || '').toLowerCase().includes(filter) ||
        (p.info || '').toLowerCase().includes(filter)
      );
    });

    tbody.innerHTML = filtered.slice(-100).map(p => {
      const proto = (p.protocol || 'OTHER').toUpperCase();
      let protoClass = 'proto-other';
      if (proto.includes('TCP')) protoClass = 'proto-tcp';
      else if (proto.includes('UDP')) protoClass = 'proto-udp';
      else if (proto.includes('TLS') || proto.includes('SSL')) protoClass = 'proto-tls';
      else if (proto.includes('HTTP')) protoClass = 'proto-http';
      else if (proto.includes('DNS')) protoClass = 'proto-dns';

      return `
        <tr>
          <td class="text-muted">${p.number || '--'}</td>
          <td>${p.timestamp ? new Date(p.timestamp * 1000).toLocaleTimeString() : '--'}</td>
          <td style="color: #38bdf8;">${p.source || '--'}</td>
          <td style="color: #a855f7;">${p.destination || '--'}</td>
          <td><span class="proto-badge ${protoClass}">${proto}</span></td>
          <td style="text-align: right;">${p.length || 0} B</td>
          <td class="text-truncate" style="max-width: 300px;">${p.info || '--'}</td>
        </tr>
      `;
    }).join('');
  }

  function startLiveCapture() {
    const ifaceSelect = document.getElementById('net-interface-select');
    const filterInput = document.getElementById('net-capture-filter');
    const startBtn = document.getElementById('btn-start-live-capture');
    const stopBtn = document.getElementById('btn-stop-live-capture');

    const iface = ifaceSelect?.value;
    const filter = filterInput?.value || '';

    if (netWs) {
      try { netWs.close(); } catch {}
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/network/ws/live`;

    try {
      netWs = new WebSocket(wsUrl);

      netWs.onopen = () => {
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        netWs.send(JSON.stringify({
          interface: iface || '',
          bpf_filter: filter,
          max_packets: 1000
        }));
      };

      netWs.onmessage = (evt) => {
        try {
          const packet = JSON.parse(evt.data);
          if (packet.error) {
            alert('Live Capture Error: ' + packet.error);
            stopLiveCapture();
            return;
          }
          capturedPackets.push(packet);
          updateMetrics();
          renderPacketsTable();
        } catch (e) {
          console.error('[NetworkTab] Packet parse error:', e);
        }
      };

      netWs.onclose = () => {
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
      };
    } catch (e) {
      console.error('[NetworkTab] Live capture connection error:', e);
      alert('Ошибка подключения к Live Capture: ' + e.message);
    }
  }

  function stopLiveCapture() {
    if (netWs) {
      try { netWs.close(); } catch {}
      netWs = null;
    }
    const startBtn = document.getElementById('btn-start-live-capture');
    const stopBtn = document.getElementById('btn-stop-live-capture');
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
  }

  async function analyzePcapFile() {
    const fileInput = document.getElementById('net-pcap-file');
    const statusEl = document.getElementById('net-upload-status');
    const file = fileInput?.files?.[0];

    if (!file) {
      alert('Пожалуйста, выберите .pcap или .pcapng файл');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_packets', '500');

    if (statusEl) statusEl.innerText = 'Анализ пакетов...';

    try {
      const res = await fetch('/api/v1/network/analyze/pcap', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Ошибка анализа' }));
        throw new Error(err.detail || res.statusText);
      }

      const report = await res.json();
      if (statusEl) statusEl.innerText = `Анализ завершён: ${report.stats?.total_packets || 0} пакетов`;

      if (Array.isArray(report.sample_packets)) {
        capturedPackets = report.sample_packets;
      }

      // Update metrics
      const totalPacketsEl = document.getElementById('net-total-packets');
      const totalBytesEl = document.getElementById('net-total-bytes');
      const anomaliesEl = document.getElementById('net-anomalies-count');
      const aiStatusEl = document.getElementById('net-ai-status');

      if (totalPacketsEl) totalPacketsEl.innerText = report.stats?.total_packets || 0;
      if (totalBytesEl) totalBytesEl.innerText = `${((report.stats?.total_bytes || 0) / 1024).toFixed(1)} KB`;
      
      const anomaliesCount = (report.heuristics?.length || 0) + (report.ai_report?.anomalies?.length || 0);
      if (anomaliesEl) {
        anomaliesEl.innerText = `${anomaliesCount} аномалий`;
        anomaliesEl.style.color = anomaliesCount > 0 ? '#f87171' : '#4ade80';
      }

      if (aiStatusEl) {
        aiStatusEl.innerText = `AI Health: ${report.ai_report?.health_score || 100}/100`;
      }

      renderPacketsTable();
    } catch (e) {
      console.error('[NetworkTab] PCAP upload error:', e);
      if (statusEl) statusEl.innerText = 'Ошибка анализа: ' + e.message;
      alert('Ошибка при анализе PCAP: ' + e.message);
    }
  }

  function updateMetrics() {
    const totalPacketsEl = document.getElementById('net-total-packets');
    const totalBytesEl = document.getElementById('net-total-bytes');
    if (totalPacketsEl) totalPacketsEl.innerText = capturedPackets.length;
    
    const bytes = capturedPackets.reduce((acc, p) => acc + (p.length || 0), 0);
    if (totalBytesEl) totalBytesEl.innerText = `${(bytes / 1024).toFixed(1)} KB`;
  }

  function initNetworkTab() {
    console.log('[NetworkTab] Initializing Network Terminal tab...');
    checkTSharkStatus();
    fetchInterfaces();

    if (!isNetInitialized) {
      const startBtn = document.getElementById('btn-start-live-capture');
      const stopBtn = document.getElementById('btn-stop-live-capture');
      const analyzeBtn = document.getElementById('btn-analyze-pcap');
      const refreshIfacesBtn = document.getElementById('btn-refresh-net-interfaces');
      const clearBtn = document.getElementById('btn-clear-packets');
      const tableFilter = document.getElementById('net-table-filter');

      if (startBtn) startBtn.onclick = startLiveCapture;
      if (stopBtn) stopBtn.onclick = stopLiveCapture;
      if (analyzeBtn) analyzeBtn.onclick = analyzePcapFile;
      if (refreshIfacesBtn) refreshIfacesBtn.onclick = fetchInterfaces;
      if (clearBtn) clearBtn.onclick = () => {
        capturedPackets = [];
        updateMetrics();
        renderPacketsTable();
      };
      if (tableFilter) tableFilter.oninput = renderPacketsTable;

      isNetInitialized = true;
    }
  }

  window.initNetworkTab = initNetworkTab;
})();
