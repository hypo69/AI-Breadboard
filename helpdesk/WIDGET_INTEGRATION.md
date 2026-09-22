# AI-Breadboard Helpdesk — Widget Integration Guide

## 🚀 Quick Start (1 minute)

Add this code to the `<head>` of any website:

```html
<script>
  (function() {
    var helpdesk = document.createElement('script');
    helpdesk.type = 'text/javascript';
    helpdesk.async = true;
    helpdesk.src = 'https://helpdesk.yourdomain.com/widget.js';
    (document.head || document.body).appendChild(helpdesk);
  })();
</script>
```

Done! Chat appears in the bottom-right corner.

---

## 📦 How It Works

### Widget Structure

```
helpdesk/
├── public/
│   └── js/
│       ├── widget.js          ← Main script (embedded in sites)
│       ├── widget.css         ← Widget styles
│       └── widget.min.js      ← Minified version
└── index.html                 ← Standalone chat page
```

### Architecture

```
┌─────────────────────────────────────────┐
│  YOUR WEBSITE (any HTML/JS)             │
│                                         │
│  <script src="widget.js"></script>      │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  🤖 Helpdesk Button (corner)   │   │
│  └─────────────────────────────────┘   │
│         │                                │
│         ▼                                │
│  ┌─────────────────────────────────┐   │
│  │  📱 Helpdesk Widget (popup)     │   │
│  │  - Chat interface               │   │
│  │  - Ticket form                  │   │
│  │  - History                      │   │
│  └─────────────────────────────────┘   │
│         │                                │
│         ▼                                │
│  ┌─────────────────────────────────┐   │
│  │  API: /api/tickets.php          │   │
│  │  /api/messages.php              │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Option 1: Automatic Configuration

```html
<script>
  window.HelpdeskConfig = {
    url: 'https://helpdesk.yourdomain.com',
    theme: 'dark',           // 'light' or 'dark'
    position: 'right',       // 'left' or 'right'
    buttonColor: '#3498db',  // Button color
    welcomeMessage: 'Hello! How can we help?',
    autoOpen: false,         // Auto-open on load
    showBadge: true,         // Show badge
    onlineText: 'Online',    // Online status text
    offlineText: 'Offline'   // Offline status text
  };
</script>
<script src="https://helpdesk.yourdomain.com/widget.js"></script>
```

### Option 2: Programmatic Control

```html
<script>
  // Initialize
  window.Helpdesk = {
    init: function(config) {
      // Load widget
    },
    open: function() {
      // Open chat
    },
    close: function() {
      // Close chat
    },
    toggle: function() {
      // Toggle visibility
    },
    setOnline: function(status) {
      // Set status (online/offline)
    },
    showTicketForm: function() {
      // Show ticket form
    },
    setUser: function(user) {
      // Set user
      // { id: 1, email: 'user@example.com', name: 'John' }
    }
  };
</script>
```

---

## 🎨 Customization

### Styles

```css
/* Override styles */
.helpdesk-widget {
  --hd-primary: #2ecc71;
  --hd-secondary: #34495e;
  --hd-background: #ffffff;
  --hd-text: #2c3e50;
}

.helpdesk-button {
  background-color: var(--hd-primary);
}

.helpdesk-header {
  background-color: var(--hd-secondary);
  color: white;
}
```

### Themes

```javascript
// Built-in theme
window.HelpdeskConfig = {
  theme: 'dark'  // or 'light'
};

// Or custom theme
window.HelpdeskConfig = {
  theme: {
    primary: '#e74c3c',
    secondary: '#2c3e50',
    background: '#1a1a1a',
    text: '#ecf0f1'
  }
};
```

---

## 🔐 Security

### CORS

Ensure CORS is configured on helpdesk server:

```php
// In config.php or .htaccess
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
```

### XSS Protection

All data in widget is escaped:

```javascript
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
```

---

## 📱 Usage Examples

### 1. Static Site

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Site</title>
  <script>
    window.HelpdeskConfig = {
      url: 'https://helpdesk.example.com',
      welcomeMessage: 'Welcome!'
    };
  </script>
  <script src="https://helpdesk.example.com/widget.js"></script>
</head>
<body>
  <h1>My Site</h1>
  <p>Content...</p>
</body>
</html>
```

### 2. WordPress

Add to `footer.php`:

```php
<script>
  window.HelpdeskConfig = {
    url: 'https://helpdesk.yourdomain.com',
    position: 'left'
  };
</script>
<script src="https://helpdesk.yourdomain.com/widget.js"></script>
```

### 3. React/Vue/Angular

```javascript
// React
useEffect(() => {
  const script = document.createElement('script');
  script.src = 'https://helpdesk.yourdomain.com/widget.js';
  script.async = true;
  document.head.appendChild(script);
  
  return () => {
    document.head.removeChild(script);
  };
}, []);
```

### 4. With Programmatic Control

```html
<button onclick="Helpdesk.open()">Support</button>

<script>
  // Open chat on click
  Helpdesk.open();
  
  // Show ticket form
  Helpdesk.showTicketForm();
  
  // Set user
  Helpdesk.setUser({
    id: 123,
    email: 'user@example.com',
    name: 'John Doe'
  });
</script>
```

---

## 📊 Metrics

### Tracking

```javascript
// Events
window.Helpdesk.on('open', function() {
  console.log('Chat opened');
});

window.Helpdesk.on('close', function() {
  console.log('Chat closed');
});

window.Helpdesk.on('ticket_created', function(ticket) {
  console.log('Ticket created:', ticket);
});

// Send to Google Analytics
window.Helpdesk.on('open', function() {
  ga('send', 'event', 'Helpdesk', 'open');
});
```

---

## 🐛 Troubleshooting

### Chat not loading

1. Check browser console (F12)
2. Verify URL is correct
3. Check CORS on server

### Styles not applying

```javascript
window.HelpdeskConfig = {
  theme: 'dark',
  styles: {
    button: {
      backgroundColor: '#3498db',
      bottom: '20px',
      right: '20px'
    }
  }
};
```

### Mobile issues

```javascript
window.HelpdeskConfig = {
  mobile: {
    position: 'bottom',
    buttonSize: '60px',
    widgetWidth: '100%'
  }
};
```

---

## 📝 Integration Checklist

- [ ] Script added to `<head>`
- [ ] Correct helpdesk URL
- [ ] CORS verified
- [ ] Button working
- [ ] Ticket submission working
- [ ] Mobile version tested
- [ ] Theme checked (light/dark)
- [ ] Metrics added (optional)

---

## 🎉 Done!

Widget is fully autonomous and works on any site.

**Working code example:**

```html
<script>
  window.HelpdeskConfig = {
    url: 'https://helpdesk.yourdomain.com',
    theme: 'dark',
    position: 'right',
    welcomeMessage: 'Hello! We are here to help'
  };
  
  (function() {
    var hd = document.createElement('script');
    hd.type = 'text/javascript';
    hd.async = true;
    hd.src = 'https://helpdesk.yourdomain.com/widget.js';
    (document.head || document.body).appendChild(hd);
  })();
</script>
```

---

**Good luck! 🚀**
