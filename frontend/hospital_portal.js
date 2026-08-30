const API_BASE = '/api';

function showMessage(msg, isError = false) {
    const banner = document.getElementById('message-banner');
    banner.textContent = msg;
    banner.className = isError ? 'msg-error' : 'msg-success';
    banner.classList.remove('hidden');
    setTimeout(() => {
        banner.classList.add('hidden');
    }, 5000);
}

function switchAuthTab(tab) {
    if (tab === 'login') {
        document.getElementById('tab-login').classList.add('active');
        document.getElementById('tab-register').classList.remove('active');
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    } else {
        document.getElementById('tab-register').classList.add('active');
        document.getElementById('tab-login').classList.remove('active');
        document.getElementById('register-form').classList.remove('hidden');
        document.getElementById('login-form').classList.add('hidden');
    }
}

function checkAuth() {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const hospName = localStorage.getItem('hospital_name');

    if (token && role === 'HOSPITAL_ADMIN') {
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('dashboard-section').classList.remove('hidden');
        document.getElementById('nav-user').classList.remove('hidden');
        document.getElementById('hospital-name-display').textContent = hospName;
    } else {
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('dashboard-section').classList.add('hidden');
        document.getElementById('nav-user').classList.add('hidden');
    }
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = document.getElementById('login-code').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: code, password: password })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('role', data.role);
            localStorage.setItem('hospital_code', data.hospital_code);
            localStorage.setItem('hospital_name', data.hospital_name);
            checkAuth();
            showMessage('Login successful');
        } else {
            showMessage(data.detail || 'Login failed', true);
        }
    } catch (err) {
        showMessage('Network error', true);
    }
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const code = document.getElementById('reg-code').value;
    const password = document.getElementById('reg-password').value;

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, hospital_code: code, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            showMessage('Registration successful! Please login.');
            switchAuthTab('login');
            document.getElementById('login-code').value = code;
        } else {
            showMessage(data.detail || 'Registration failed', true);
        }
    } catch (err) {
        showMessage('Network error', true);
    }
});

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('hospital_code');
    localStorage.removeItem('hospital_name');
    checkAuth();
}

document.getElementById('fhir-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payloadStr = document.getElementById('fhir-payload').value;
    
    let payload;
    try {
        payload = JSON.parse(payloadStr);
    } catch (err) {
        showMessage('Invalid JSON format', true);
        return;
    }

    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/fhir/historical`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (res.ok) {
            showMessage('Historical FHIR data saved successfully!');
            document.getElementById('fhir-payload').value = '';
        } else {
            showMessage(data.detail || 'Failed to submit data', true);
        }
    } catch (err) {
        showMessage('Network error', true);
    }
});

checkAuth();
