/* Helpdesk Application JavaScript */

const API_BASE = '/helpdesk/api';

// State
let currentUser = null;
let currentToken = null;

// DOM Elements
const elements = {
    loginSection: document.getElementById('login-section'),
    registerSection: document.getElementById('register-section'),
    dashboardSection: document.getElementById('dashboard-section'),
    btnLogin: document.getElementById('btn-login'),
    btnRegister: document.getElementById('btn-register'),
    btnDashboard: document.getElementById('btn-dashboard'),
    btnLogout: document.getElementById('btn-logout'),
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    createTicketForm: document.getElementById('create-ticket-form'),
    ticketList: document.getElementById('ticket-list'),
    filterStatus: document.getElementById('filter-status'),
    filterPriority: document.getElementById('filter-priority'),
    statTotal: document.getElementById('stat-total'),
    statOpen: document.getElementById('stat-open'),
    statInProgress: document.getElementById('stat-in-progress'),
    statUrgent: document.getElementById('stat-urgent')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

function setupEventListeners() {
    // Navigation
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        elements.loginSection.style.display = 'none';
        elements.registerSection.style.display = 'block';
    });

    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        elements.registerSection.style.display = 'none';
        elements.loginSection.style.display = 'block';
    });

    // Forms
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.createTicketForm.addEventListener('submit', handleCreateTicket);
    
    // Filters
    elements.filterStatus.addEventListener('change', loadTickets);
    elements.filterPriority.addEventListener('change', loadTickets);
    
    // Buttons
    elements.btnLogin.addEventListener('click', () => {
        elements.loginSection.style.display = 'block';
        elements.registerSection.style.display = 'none';
    });

    elements.btnRegister.addEventListener('click', () => {
        elements.registerSection.style.display = 'block';
        elements.loginSection.style.display = 'none';
    });

    elements.btnDashboard.addEventListener('click', () => {
        elements.dashboardSection.style.display = 'block';
        elements.loginSection.style.display = 'none';
        elements.registerSection.style.display = 'none';
        loadTickets();
        loadStats();
    });

    elements.btnLogout.addEventListener('click', handleLogout);
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth.php`, {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            currentToken = localStorage.getItem('helpdesk_token');
            updateUI();
        }
    } catch (error) {
        console.log('Not authenticated');
    }
}

function updateUI() {
    if (currentUser) {
        elements.btnLogin.style.display = 'none';
        elements.btnRegister.style.display = 'none';
        elements.btnDashboard.style.display = 'inline-block';
        elements.btnLogout.style.display = 'inline-block';
        
        // Set user info
        document.querySelector('.navbar-brand h1').innerHTML = 
            `Helpdesk <span style="font-size: 0.8em; opacity: 0.7">(${currentUser.name})</span>`;
    } else {
        elements.btnLogin.style.display = 'inline-block';
        elements.btnRegister.style.display = 'inline-block';
        elements.btnDashboard.style.display = 'none';
        elements.btnLogout.style.display = 'none';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth.php`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'login',
                email,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentToken = data.token;
            localStorage.setItem('helpdesk_token', data.token);
            currentUser = data.user;
            updateUI();
            
            // Show dashboard
            elements.loginSection.style.display = 'none';
            elements.dashboardSection.style.display = 'block';
            loadTickets();
            loadStats();
            
            alert('Login successful!');
        } else {
            alert('Login failed: ' + data.message);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('An error occurred during login');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth.php`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'register',
                name,
                email,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentToken = data.token;
            localStorage.setItem('helpdesk_token', data.token);
            currentUser = data.user;
            updateUI();
            
            // Show dashboard
            elements.registerSection.style.display = 'none';
            elements.dashboardSection.style.display = 'block';
            loadTickets();
            loadStats();
            
            alert('Registration successful!');
        } else {
            alert('Registration failed: ' + data.message);
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred during registration');
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE}/auth.php`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        localStorage.removeItem('helpdesk_token');
        currentToken = null;
        currentUser = null;
        updateUI();
        
        elements.dashboardSection.style.display = 'none';
        elements.loginSection.style.display = 'block';
        
        alert('Logged out successfully');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

async function handleCreateTicket(e) {
    e.preventDefault();
    
    const subject = document.getElementById('ticket-subject').value;
    const category = document.getElementById('ticket-category').value;
    const priority = document.getElementById('ticket-priority').value;
    const message = document.getElementById('ticket-message').value;
    
    try {
        const response = await fetch(`${API_BASE}/tickets.php`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({
                subject,
                category,
                priority,
                message
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Ticket created successfully!');
            elements.createTicketForm.reset();
            loadTickets();
        } else {
            alert('Failed to create ticket: ' + data.message);
        }
    } catch (error) {
        console.error('Create ticket error:', error);
        alert('An error occurred while creating ticket');
    }
}

async function loadTickets() {
    const status = elements.filterStatus.value;
    const priority = elements.filterPriority.value;
    
    let url = `${API_BASE}/tickets.php?`;
    if (status !== 'all') url += `status=${status}&`;
    if (priority) url += `priority=${priority}&`;
    
    try {
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            renderTickets(data.tickets);
        }
    } catch (error) {
        console.error('Load tickets error:', error);
    }
}

function renderTickets(tickets) {
    elements.ticketList.innerHTML = tickets.map(ticket => `
        <div class="ticket-item" data-ticket-id="${ticket.id}">
            <div class="ticket-header">
                <span class="ticket-number">#${ticket.ticket_number}</span>
                <span class="ticket-status ${ticket.status}">${ticket.status}</span>
                <span class="ticket-priority ${ticket.priority}">${ticket.priority}</span>
            </div>
            <h4 class="ticket-subject">${escapeHtml(ticket.subject)}</h4>
            <div class="ticket-meta">
                <span class="ticket-user">${escapeHtml(ticket.user_name)}</span>
                <span class="ticket-date">${formatDate(ticket.created_at)}</span>
                <span class="ticket-messages">${ticket.messages_count || 0} messages</span>
            </div>
        </div>
    `).join('');
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats.php`);
        const data = await response.json();
        
        if (response.ok) {
            elements.statTotal.textContent = data.stats.total_tickets;
            elements.statOpen.textContent = data.stats.open_tickets;
            elements.statInProgress.textContent = data.stats.in_progress_tickets;
            elements.statUrgent.textContent = data.stats.urgent_tickets;
        }
    } catch (error) {
        console.error('Load stats error:', error);
    }
}

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
