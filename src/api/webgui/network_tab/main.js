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
  let activeConnFilter = 'all';
  let isSpeedtestRunning = false;

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
          tsharkBadge.innerText = i18n.t('auto_tshark_dpi__360aa8');
        } else {
          tsharkBadge.className = 'badge rounded-pill bg-warning-subtle text-warning border border-warning px-2 py-1';
          tsharkBadge.innerText = i18n.t('auto_tshark_dpi__7a38fb');
        }
      }

      if (kpiAdapters) kpiAdapters.innerText = data.total_adapters ?? '--';
      if (kpiConns) kpiConns.innerText = data.active_connections_count ?? '--i18n.t('auto__if_kpilistening_kpilistening_innertext_data_listening_ports_count_0_if_kpipackets_kpipackets_innertext_data_total_packets_capturedpackets_length_const_anomaliescount_data_latest_heuristics_length_0_data_latest_ai_report_anomalies_length_0_if_kpianomalies_kpianomalies_innertext_anomaliescount_kpianomalies_style_color_anomaliescount_0__2717e0')#f87171' : '#4ade80';
      }
    } catch (e) {
      console.warn('[NetworkTab] Status check error:', e);
      if (engineBadge) {
        engineBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-2 py-1';
        engineBadge.innerText = i18n.t('auto_windows_net__f32419');
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
    if (statusText) statusText.innerText = i18n.t('auto__ping_download_upload__0f04c3');
    if (summaryText) summaryText.innerText = i18n.t('auto__cloudflare_dns__a23ee1');

    try {
      const res = await fetch('/api/network/speedtest/run', { method: 'POSTi18n.t('auto__if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_renderspeedtestresults_data_if_statustext_statustext_innertext_new_date_tolocaletimestring_catch_e_console_error__56dacc')[NetworkTab] Speedtest error:', e);
      window.showToast?.(i18n.t('auto___138be8') + e.message, 'danger') || alert(i18n.t('auto___138be8') + e.message);
      if (statusText) statusText.innerText = i18n.t('auto___d482f2');
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
      valGrade.style.color = quality.color || '#fbbf24i18n.t('auto__if_subisp_subisp_innertext_meta_isp__cd72e0')Неизвестноi18n.t('auto__if_badgeip_badgeip_innertext_ip_meta_ip__cc1436')--i18n.t('auto__if_badgeloc_badgeloc_innertext_meta_city__4883f8')'} ${meta.country || ''} (${meta.colo || 'Edge'})`.trim();
    if (summaryText) summaryText.innerText = `${quality.grade || i18n.t('auto___398c7d')}. ${quality.summary || ''}`;

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
        }).join('i18n.t('auto__if_kpiactive_kpiactive_innertext_activecount_catch_e_console_error__854064')[NetworkTab] Failed to fetch adapters:', e);
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
      const res = await fetch('/api/network/connections?limit=250i18n.t('auto__if_res_ok_throw_new_error_http_res_status_const_data_await_res_json_const_conns_array_isarray_data_connections_data_connections_const_listening_array_isarray_data_listening_ports_data_listening_ports_allconnections_listening_conns_if_badgeconn_badgeconn_innertext_allconnections_length_if_kpiconns_kpiconns_innertext_conns_length_if_kpilistening_kpilistening_innertext_listening_length_renderconnectionstable_catch_e_console_error__e73855')[NetworkTab] Failed to fetch connections:', e);
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
        <tr class="net-conn-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto___59fdea')>
          <td><span class="proto-badge ${protoClass}">${c.protocol || 'TCP'}</span></td>
          <td class="text-info font-monospace">${c.local_address || '-'}</td>
          <td class="text-secondary font-monospace">${c.remote_address || '-'}</td>
          <td><span class="proto-badge ${statusClass}">${c.status || '-'}</span></td>
          <td class="text-muted font-monospace">${c.pid || '-'}</td>
          <td class="fw-bold text-white"><i class="bi bi-app me-1 text-muted"></i>${c.process_name || i18n.t('auto___43b44f')}</td>
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
          icon: '📡i18n.t('auto__title_item_protocol__3a2e36')TCP'}]`,
          subtitle: `${item.process_name} (PID: ${item.pid || 'N/A'})`,
          tableType: 'network',
          badges: [
            { text: item.protocol || 'TCP', class: 'badge bg-primary' },
            { text: item.status || 'UNKNOWN', class: 'badge bg-info' },
            { text: `PID ${item.pid || '-'}`, class: 'badge bg-secondary' }
          ],
          metadata: [
            { label: i18n.t('auto___2988c5'), value: item.process_name || '-' },
            { label: 'PID', value: String(item.pid || '-') },
            { label: i18n.t('auto___382265'), value: item.protocol || '-' },
            { label: i18n.t('auto___e7a4ba'), value: item.local_address || '-' },
            { label: i18n.t('auto___34aa72'), value: item.remote_address || '-' },
            { label: i18n.t('auto___1aa3a3'), value: item.status || '-' }
          ],
          rawTitle: i18n.t('auto___a9d76e'),
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
    const filter = (filterInput?.value || 'i18n.t('auto__tolowercase_trim_if_tbody_return_if_badge_badge_innertext_capturedpackets_length_if_capturedpackets_length_0_tbody_innerhtml__bd9ab6')<tr><td colspan="7" class="text-center py-4 text-mutedi18n.t('auto___16e745')Старт захвата".</td></tr>';
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
        <tr class="net-packet-row" data-idx="${idx}" style="cursor: pointer;" title=i18n.t('auto__ai__f95071')>
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
          icon: '🌐i18n.t('auto__title_p_number_p_packet_number__96e9d6')N/A'} [${p.protocol || 'TCP'}]`,
          subtitle: `${p.source || '0.0.0.0'} ➔ ${p.destination || '0.0.0.0'}`,
          tableType: 'network',
          badges: [
            { text: (p.protocol || 'TCP').toUpperCase(), class: 'badge bg-primary' },
            { text: `${p.length || 0} Bytes`, class: 'badge bg-secondary' }
          ],
          metadata: [
            { label: i18n.t('auto___246ebf'), value: String(p.number || p.packet_number || '-') },
            { label: i18n.t('auto___382265'), value: (p.protocol || 'TCP').toUpperCase() },
            { label: i18n.t('auto___8290a3'), value: p.source || '-' },
            { label: i18n.t('auto___332fdc'), value: p.destination || '-' },
            { label: i18n.t('auto___98713e'), value: `${p.length || 0} байт` },
            { label: i18n.t('auto___778b60'), value: p.info || i18n.t('auto___d0dd94'), fullWidth: true }
          ],
          rawTitle: i18n.t('auto___18c6aa'),
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
      window.showToast?.(i18n.t('auto___13847c') + e.message, 'danger') || alert(i18n.t('auto___13847c') + e.message);
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
      window.showToast?.(i18n.t('auto__pcap_pcapng__699cdf'), 'warning') || alert(i18n.t('auto__pcap_pcapng__699cdf'));
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_packets', '500');

    if (statusEl) statusEl.innerText = i18n.t('auto___ebfe25');

    try {
      const res = await fetch('/api/network/analyze/pcap', {
        method: 'POSTi18n.t('auto__body_formdata_if_res_ok_throw_new_error_http_res_status_const_report_await_res_json_if_statusel_statusel_innertext_report_stats_total_packets_0_if_healthel_healthel_innertext_report_ai_report_health_score_100_100_const_anomaliescount_report_heuristics_length_0_report_ai_report_anomalies_length_0_if_anomaliesel_anomaliesel_innertext_string_anomaliescount_anomaliesel_classname_net_value_mt_1_anomaliescount_0__326abf')text-danger' : 'text-success'}`;
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
      if (statusEl) statusEl.innerText = i18n.t('auto___bf2214') + e.message;
      window.showToast?.(i18n.t('auto__pcap__cac8b8') + e.message, 'danger') || alert(i18n.t('auto__pcap__cac8b8') + e.message);
    }
  }

  // Main init function for Network Terminal Tab
  function initNetworkTab() {
    console.log('[NetworkTab] Initializing Windows Network Terminal tab (/apps/windows/network)...');
    fetchNetworkStatus();
    fetchLatestSpeedtest();
    fetchAdapters();
    fetchConnections();

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

      if (refreshAllBtn) refreshAllBtn.onclick = () => {
        fetchNetworkStatus();
        fetchLatestSpeedtest();
        fetchAdapters();
        fetchConnections();
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
