// Trading Terminal Tab JS Module
(function() {
  let tradingWs = null;
  let isTradingInitialized = false;

  async function fetchTradingState() {
    try {
      const res = await fetch('/api/v1/trading/status');
      if (!res.ok) return;
      const data = await res.json();
      updateTradingUI(data);
    } catch (e) {
      console.error('[TradingTab] Failed to fetch state:', e);
    }
  }

  async function fetchOrderbook() {
    try {
      const res = await fetch('/api/v1/trading/orderbook?depth=6');
      if (!res.ok) return;
      const data = await res.json();
      renderOrderbook(data);
    } catch (e) {
      console.error('[TradingTab] Failed to fetch orderbook:', e);
    }
  }

  async function fetchOrdersList() {
    try {
      const res = await fetch('/api/v1/trading/orders');
      if (!res.ok) return;
      const orders = await res.json();
      renderOrders(orders);
    } catch (e) {
      console.error('[TradingTab] Failed to fetch orders:', e);
    }
  }

  function updateTradingUI(state) {
    if (!state) return;
    const symEl = document.getElementById('trading-symbol');
    const priceEl = document.getElementById('trading-current-price');
    const equityEl = document.getElementById('trading-total-equity');
    const balanceEl = document.getElementById('trading-cash-balance');
    const pnlEl = document.getElementById('trading-pnl-val');
    const posEl = document.getElementById('trading-pos-size');

    if (symEl) symEl.innerText = state.symbol || 'BTC/USDT';
    if (priceEl) priceEl.innerText = `$${Number(state.current_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (equityEl) equityEl.innerText = `$${Number(state.total_equity || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (balanceEl) balanceEl.innerText = `Доступно: $${Number(state.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    if (pnlEl) {
      const pnl = Number(state.unrealized_pnl || 0);
      const sign = pnl >= 0 ? '+' : '';
      pnlEl.innerText = `${sign}$${pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      pnlEl.style.color = pnl >= 0 ? '#4ade80' : '#f87171';
    }

    if (posEl) {
      posEl.innerText = `Размер позиции: ${state.position_size || 0} ${state.symbol?.split('/')[0] || 'BTC'}`;
    }
  }

  function renderOrderbook(ob) {
    if (!ob) return;
    const asksTbody = document.getElementById('trading-asks-tbody');
    const bidsTbody = document.getElementById('trading-bids-tbody');
    const midEl = document.getElementById('trading-orderbook-midprice');
    const spreadEl = document.getElementById('trading-spread-info');

    if (midEl && ob.mid_price) {
      midEl.innerText = `$${Number(ob.mid_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (spreadEl && ob.spread !== undefined) {
      spreadEl.innerText = `Спред: $${Number(ob.spread).toFixed(2)}`;
    }

    if (asksTbody && Array.isArray(ob.asks)) {
      // Show asks reversed (highest on top)
      const reversedAsks = [...ob.asks].reverse();
      asksTbody.innerHTML = reversedAsks.map(a => `
        <tr class="trading-ask-row">
          <td>$${Number(a.price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
          <td style="text-align: right;">${Number(a.amount).toFixed(4)}</td>
          <td style="text-align: right;">$${Number(a.total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        </tr>
      `).join('');
    }

    if (bidsTbody && Array.isArray(ob.bids)) {
      bidsTbody.innerHTML = ob.bids.map(b => `
        <tr class="trading-bid-row">
          <td>$${Number(b.price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
          <td style="text-align: right;">${Number(b.amount).toFixed(4)}</td>
          <td style="text-align: right;">$${Number(b.total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        </tr>
      `).join('');
    }
  }

  function renderOrders(orders) {
    const tbody = document.getElementById('trading-orders-tbody');
    const countEl = document.getElementById('trading-orders-count');
    if (!tbody) return;

    if (!Array.isArray(orders) || orders.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">История сделок пуста</td></tr>';
      if (countEl) countEl.innerText = '0 ордеров';
      return;
    }

    if (countEl) countEl.innerText = `${orders.length} ордеров`;

    tbody.innerHTML = orders.map(o => {
      const isBuy = (o.side || '').toUpperCase() === 'BUY';
      const sideBadge = isBuy
        ? '<span class="badge bg-success">BUY</span>'
        : '<span class="badge bg-danger">SELL</span>';
      return `
        <tr>
          <td>${new Date(o.timestamp * 1000).toLocaleTimeString()}</td>
          <td class="text-muted">${o.order_id}</td>
          <td>${sideBadge}</td>
          <td>${o.order_type}</td>
          <td style="text-align: right;">${Number(o.amount).toFixed(4)}</td>
          <td style="text-align: right;">$${Number(o.price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
          <td style="text-align: right;"><span class="badge bg-secondary">${o.status}</span></td>
        </tr>
      `;
    }).join('');
  }

  async function placeOrder(side) {
    const amountInput = document.getElementById('trading-order-amount');
    const priceInput = document.getElementById('trading-order-price');
    const typeSelect = document.getElementById('trading-order-type');
    const amount = parseFloat(amountInput?.value || '0');
    const orderType = typeSelect?.value || 'MARKET';
    const price = priceInput?.value ? parseFloat(priceInput.value) : null;

    if (!amount || amount <= 0) {
      alert('Укажите корректный объём ордера');
      return;
    }

    try {
      const payload = {
        symbol: 'BTC/USDT',
        side: side,
        amount: amount,
        order_type: orderType,
        price: price
      };

      const res = await fetch('/api/v1/trading/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Ошибка выполнения' }));
        alert('Ошибка выставления ордера: ' + (err.detail || res.statusText));
        return;
      }

      await fetchTradingState();
      await fetchOrdersList();
      await fetchOrderbook();
    } catch (e) {
      console.error('[TradingTab] Order error:', e);
      alert('Ошибка соединения при отправке ордера: ' + e.message);
    }
  }

  async function triggerKillSwitch() {
    if (!confirm('⚠️ ВНИМАНИЕ: Вы действительно хотите немедленно закрыть все позиции по рыночной цене (Kill-Switch)?')) {
      return;
    }

    try {
      const res = await fetch('/api/v1/trading/kill-switch', { method: 'POST' });
      if (!res.ok) throw new Error('Ошибка вызова Kill-Switch');
      const data = await res.json();
      alert(`Ликвидация завершена: ${data.message || 'Позиции закрыты'}`);
      await fetchTradingState();
      await fetchOrdersList();
    } catch (e) {
      alert('Ошибка при вызове Kill-Switch: ' + e.message);
    }
  }

  function isTradingTabActive() {
    const el = document.getElementById('tab-trading');
    if (!el) return false;
    return el.classList.contains('active') || el.classList.contains('show') || (el.offsetWidth > 0 && el.offsetHeight > 0);
  }

  function connectTradingWebSocket() {
    if (tradingWs) {
      try { tradingWs.close(); } catch {}
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/v1/trading/ws/stream`;

    try {
      tradingWs = new WebSocket(wsUrl);
      const statusBadge = document.getElementById('trading-stream-status');

      tradingWs.onopen = () => {
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-success-subtle text-success border border-success px-3 py-2';
          statusBadge.innerText = '● Стрим активен';
        }
      };

      tradingWs.onmessage = (evt) => {
        try {
          const state = JSON.parse(evt.data);
          updateTradingUI(state);
          if (isTradingTabActive()) {
            fetchOrderbook();
            fetchOrdersList();
          }
        } catch (e) {
          console.error('[TradingTab] WS message parse error:', e);
        }
      };

      tradingWs.onclose = () => {
        if (statusBadge) {
          statusBadge.className = 'badge rounded-pill bg-danger-subtle text-danger border border-danger px-3 py-2';
          statusBadge.innerText = '● Отключено';
        }
      };
    } catch (e) {
      console.error('[TradingTab] WS connection error:', e);
    }
  }

  function initTradingTab(force = false) {
    if (!isTradingInitialized) {
      const buyBtn = document.getElementById('btn-order-buy');
      const sellBtn = document.getElementById('btn-order-sell');
      const refreshBtn = document.getElementById('btn-refresh-trading');
      const killBtn = document.getElementById('btn-trigger-kill-switch');

      const configBtn = document.getElementById('btn-trading-config');

      if (buyBtn) buyBtn.onclick = () => placeOrder('BUY');
      if (sellBtn) sellBtn.onclick = () => placeOrder('SELL');
      if (refreshBtn) refreshBtn.onclick = () => {
        fetchTradingState();
        fetchOrderbook();
        fetchOrdersList();
      };
      if (killBtn) killBtn.onclick = triggerKillSwitch;
      if (configBtn) configBtn.onclick = () => {
        if (typeof window.openAppConfigModal === 'function') {
          window.openAppConfigModal('trading_terminal', 'Exchange Trading Terminal');
        }
      };

      isTradingInitialized = true;
    }

    if (!force && !isTradingTabActive()) {
      console.log('[TradingTab] Tab is not active; skipping background network polling and WebSocket connection.');
      return;
    }

    console.log('[TradingTab] Initializing active Trading Terminal network polling & WebSocket...');
    fetchTradingState();
    fetchOrderbook();
    fetchOrdersList();
    connectTradingWebSocket();
  }

  window.initTradingTab = initTradingTab;
})();
