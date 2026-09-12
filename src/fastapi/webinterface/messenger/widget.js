/**
 * AI Breadboard Floating Messenger Widget
 * Zero-dependency embeddable script for any website or WordPress.
 */

(function () {
  const config = window.AB_MESSENGER_CONFIG || {
    apiUrl: window.location.origin,
    ssoToken: '',
    userId: '',
    userName: 'Guest',
  };

  const style = document.createElement('style');
  style.innerHTML = `
    .ab-widget-bubble {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #3b82f6, #1d4ed8);
      box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 999999;
      transition: transform 0.2s ease;
      color: #fff;
      font-size: 28px;
    }
    .ab-widget-bubble:hover {
      transform: scale(1.08);
    }
    .ab-widget-frame {
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 400px;
      height: 620px;
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 120px);
      border-radius: 20px;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.1);
      overflow: hidden;
      z-index: 999998;
      display: none;
      background: #0f172a;
    }
    .ab-widget-frame iframe {
      width: 100%;
      height: 100%;
      border: none;
    }
  `;
  document.head.appendChild(style);

  const bubble = document.createElement('div');
  bubble.className = 'ab-widget-bubble';
  bubble.innerHTML = '💬';

  const frameContainer = document.createElement('div');
  frameContainer.className = 'ab-widget-frame';

  let isOpen = false;
  let iframe = null;

  bubble.onclick = () => {
    isOpen = !isOpen;
    if (isOpen) {
      if (!iframe) {
        iframe = document.createElement('iframe');
        const tokenQuery = config.ssoToken ? `?token=${encodeURIComponent(config.ssoToken)}` : '';
        iframe.src = `${config.apiUrl}/webinterface/messenger/${tokenQuery}`;
        iframe.allow = 'camera; microphone; display-capture; autoplay';
        frameContainer.appendChild(iframe);
      }
      frameContainer.style.display = 'block';
      bubble.innerHTML = '✕';
    } else {
      frameContainer.style.display = 'none';
      bubble.innerHTML = '💬';
    }
  };

  document.body.appendChild(frameContainer);
  document.body.appendChild(bubble);
})();
