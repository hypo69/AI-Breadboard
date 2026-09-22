<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Helpdesk - Support Ticket System</title>
    <link rel="stylesheet" href="public/css/style.css">
</head>
<body>
    <div id="app">
        <!-- Navigation -->
        <nav class="navbar">
            <div class="container">
                <div class="navbar-brand">
                    <h1>Helpdesk</h1>
                </div>
                <div class="navbar-menu">
                    <button id="btn-login" class="btn btn-primary">Login</button>
                    <button id="btn-register" class="btn btn-secondary">Register</button>
                    <button id="btn-dashboard" class="btn btn-success" style="display: none;">Dashboard</button>
                    <button id="btn-logout" class="btn btn-danger" style="display: none;">Logout</button>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Login Form -->
            <div id="login-section" class="section">
                <div class="container">
                    <div class="card">
                        <h2>Login to Helpdesk</h2>
                        <form id="login-form">
                            <div class="form-group">
                                <label for="email">Email</label>
                                <input type="email" id="email" name="email" required>
                            </div>
                            <div class="form-group">
                                <label for="password">Password</label>
                                <input type="password" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Login</button>
                            <p class="form-footer">
                                Don't have an account? <a href="#" id="show-register">Register</a>
                            </p>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Register Form -->
            <div id="register-section" class="section" style="display: none;">
                <div class="container">
                    <div class="card">
                        <h2>Create Account</h2>
                        <form id="register-form">
                            <div class="form-group">
                                <label for="reg-name">Name</label>
                                <input type="text" id="reg-name" name="name" required>
                            </div>
                            <div class="form-group">
                                <label for="reg-email">Email</label>
                                <input type="email" id="reg-email" name="email" required>
                            </div>
                            <div class="form-group">
                                <label for="reg-password">Password</label>
                                <input type="password" id="reg-password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Register</button>
                            <p class="form-footer">
                                Already have an account? <a href="#" id="show-login">Login</a>
                            </p>
                        </form>
                    </div>
                </div>
            </div>

            <!-- Dashboard (Hidden by default) -->
            <div id="dashboard-section" class="section" style="display: none;">
                <div class="container">
                    <div class="dashboard-header">
                        <h2>Support Dashboard</h2>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <span class="stat-value" id="stat-total">0</span>
                                <span class="stat-label">Total Tickets</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-value" id="stat-open">0</span>
                                <span class="stat-label">Open</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-value" id="stat-in-progress">0</span>
                                <span class="stat-label">In Progress</span>
                            </div>
                            <div class="stat-card">
                                <span class="stat-value" id="stat-urgent">0</span>
                                <span class="stat-label">Urgent</span>
                            </div>
                        </div>
                    </div>

                    <!-- Create Ticket -->
                    <div class="card">
                        <h3>Create New Ticket</h3>
                        <form id="create-ticket-form">
                            <div class="form-group">
                                <label for="ticket-subject">Subject</label>
                                <input type="text" id="ticket-subject" name="subject" required maxlength="500">
                            </div>
                            <div class="form-group">
                                <label for="ticket-category">Category</label>
                                <select id="ticket-category" name="category">
                                    <option value="general">General</option>
                                    <option value="technical">Technical Support</option>
                                    <option value="billing">Billing</option>
                                    <option value="bug">Bug Report</option>
                                    <option value="ai_query">AI Query</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="ticket-priority">Priority</label>
                                <select id="ticket-priority" name="priority">
                                    <option value="low">Low</option>
                                    <option value="normal" selected>Normal</option>
                                    <option value="high">High</option>
                                    <option value="urgent">Urgent</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="ticket-message">Message</label>
                                <textarea id="ticket-message" name="message" rows="5" required></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">Create Ticket</button>
                        </form>
                    </div>

                    <!-- Ticket List -->
                    <div class="card">
                        <div class="card-header">
                            <h3>Your Tickets</h3>
                            <div class="filters">
                                <select id="filter-status">
                                    <option value="all">All Status</option>
                                    <option value="open">Open</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="resolved">Resolved</option>
                                    <option value="closed">Closed</option>
                                </select>
                                <select id="filter-priority">
                                    <option value="">All Priority</option>
                                    <option value="urgent">Urgent</option>
                                    <option value="high">High</option>
                                    <option value="normal">Normal</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                        </div>
                        <div id="ticket-list">
                            <!-- Tickets will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="footer">
            <div class="container">
                <p>&copy; 2026 Helpdesk. All rights reserved.</p>
            </div>
        </footer>
    </div>

    <script src="public/js/app.js"></script>
</body>
</html>
