/**
 * activityTracker.js — Client-side Telemetry & User Activity Tracker
 *
 * Tracks tab views, dwell durations, and UI button/action clicks strictly
 * for authenticated registered users and flushes batches to /api/telemetry/events.
 */

'use strict';

let currentTabId = 'tab-chat';
let tabEnterTimestamp = Date.now();
let eventQueue = [];
let flushTimer = null;
let isInitialized = false;

/**
 * Check if the current user session is an authenticated registered user.
 * @returns {boolean}
 */
export function isUserAuthenticated() {
  if (window.currentUser && window.currentUser.authenticated) {
    return true;
  }
  // Check auth_token cookie or session storage flag
  return document.cookie.includes('auth_token=');
}

/**
 * Push an event to the internal batch queue if user is authenticated.
 * @param {Object} event
 */
export function trackEvent(event) {
  if (!isUserAuthenticated()) {
    return;
  }

  const payload = {
    action: event.action || event.event_type || 'action',
    event_type: event.event_type || 'action',
    tab_name: event.tab_name || currentTabId,
    target_element: event.target_element || '',
    duration_ms: event.duration_ms || 0,
    details: event.details || null,
    timestamp: new Date().toISOString()
  };

  eventQueue.push(payload);

  if (eventQueue.length >= 20) {
    flushEvents();
  }
}

/**
 * Record a tab switch / tab view event with dwell time calculation.
 * @param {string} newTabId
 */
export function trackTabSwitch(newTabId) {
  if (!newTabId) return;
  const now = Date.now();
  const cleanNewTab = newTabId.startsWith('#') ? newTabId.slice(1) : newTabId;

  if (currentTabId && currentTabId !== cleanNewTab) {
    const duration = now - tabEnterTimestamp;
    trackEvent({
      action: `Left tab ${currentTabId}`,
      event_type: 'tab_view',
      tab_name: currentTabId,
      target_element: `tab:${currentTabId}`,
      duration_ms: duration,
      details: {
        transition_to: cleanNewTab,
        duration_sec: Math.round(duration / 1000)
      }
    });
  }

  currentTabId = cleanNewTab;
  tabEnterTimestamp = now;

  trackEvent({
    action: `Entered tab ${cleanNewTab}`,
    event_type: 'tab_view',
    tab_name: cleanNewTab,
    target_element: `tab:${cleanNewTab}`,
    duration_ms: 0,
    details: {
      timestamp: new Date().toISOString()
    }
  });
}

/**
 * Send queued events to the backend telemetry ingestion endpoint.
 */
export async function flushEvents() {
  if (!isUserAuthenticated() || eventQueue.length === 0) {
    return;
  }

  const batch = [...eventQueue];
  eventQueue = [];

  const body = JSON.stringify({
    events: batch,
    session_id: window.currentUser?.email || 'authenticated_session'
  });

  try {
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: 'application/json' });
      const success = navigator.sendBeacon('/api/telemetry/events', blob);
      if (success) return;
    }

    await fetch('/api/telemetry/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body,
      keepalive: true
    });
  } catch (err) {
    console.debug('Telemetry flush failed, restoring queue:', err);
    // Put events back in queue up to maximum limit
    if (eventQueue.length < 50) {
      eventQueue = [...batch, ...eventQueue];
    }
  }
}

/**
 * Inspect click target and capture non-sensitive interactive element info.
 * @param {MouseEvent} event
 */
function handleGlobalClick(event) {
  if (!isUserAuthenticated()) return;

  const target = event.target;
  if (!target) return;

  // Find closest interactive element
  const interactiveEl = target.closest(
    'button, a, input[type="button"], input[type="submit"], [role="button"], .nav-link, .dropdown-item, .btn, .badge[role="button"], [data-action], [data-tab]'
  );

  if (!interactiveEl) return;

  // Skip sensitive elements (passwords, auth inputs, tokens)
  const isSensitive =
    interactiveEl.type === 'password' ||
    interactiveEl.name === 'password' ||
    interactiveEl.id?.includes('password') ||
    interactiveEl.id?.includes('token') ||
    interactiveEl.classList?.contains('sensitive');

  if (isSensitive) return;

  // Extract meaningful descriptive label
  let label = (
    interactiveEl.getAttribute('data-action') ||
    interactiveEl.getAttribute('data-tab') ||
    interactiveEl.getAttribute('aria-label') ||
    interactiveEl.getAttribute('title') ||
    interactiveEl.innerText?.trim().slice(0, 60) ||
    interactiveEl.id ||
    interactiveEl.name ||
    interactiveEl.tagName.toLowerCase()
  );

  // Clean label whitespace
  label = label.replace(/\s+/g, ' ').trim();
  if (!label) return;

  const targetDescriptor = `${interactiveEl.tagName.toLowerCase()}${interactiveEl.id ? '#' + interactiveEl.id : ''}${interactiveEl.className ? '.' + interactiveEl.className.split(' ').filter(c => !c.startsWith('show') && !c.startsWith('active')).slice(0, 2).join('.') : ''}`;

  trackEvent({
    action: `Click: ${label}`,
    event_type: 'click',
    tab_name: currentTabId,
    target_element: targetDescriptor,
    details: {
      label,
      tag: interactiveEl.tagName.toLowerCase(),
      id: interactiveEl.id || null,
      data_action: interactiveEl.getAttribute('data-action') || null,
      data_tab: interactiveEl.getAttribute('data-tab') || null
    }
  });
}

/**
 * Initialize Activity Tracker listeners and flush loop.
 */
export function initActivityTracker() {
  if (isInitialized) return;
  isInitialized = true;

  // Listen for click interactions
  document.addEventListener('click', handleGlobalClick, { capture: true, passive: true });

  // Periodic flush every 5 seconds
  flushTimer = setInterval(flushEvents, 5000);

  // Flush on visibility change / window unload
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      flushEvents();
    }
  });
  window.addEventListener('pagehide', () => {
    flushEvents();
  });

  console.log('✓ Activity Tracker initialized (registered users only)');
}

// Global exposure for legacy scripts
window.activityTracker = {
  trackTabSwitch,
  trackEvent,
  flushEvents,
  initActivityTracker
};
