const API_BASE = '/api';
const BASE_URL = `${window.location.protocol}//${window.location.host}`;

// ── Populate curl snippets in the API Reference panel ──
(function buildCurlSnippets() {
    const auth = `curl -X POST ${BASE_URL}/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "YOUR_HOSPITAL_CODE",
    "password": "YOUR_PASSWORD"
  }'`;

    const submit = `curl -X POST ${BASE_URL}/api/fhir/historical \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer <YOUR_TOKEN>" \\
  -d '{
    "resourceType": "Bundle",
    "type": "collection",
    "entry": [
      {
        "resource": {
          "resourceType": "Patient",
          "id": "patient-001",
          "name": [{"given": ["John"], "family": "Doe"}],
          "gender": "male",
          "birthDate": "1990-05-15"
        }
      },
      {
        "resource": {
          "resourceType": "Observation",
          "code": {
            "coding": [{
              "system": "http://loinc.org",
              "code": "8867-4"
            }]
          },
          "valueQuantity": {"value": 88}
        }
      }
    ]
  }'`;

    const fetch_ = `curl -X POST ${BASE_URL}/api/fhir/fetch-and-submit \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer <YOUR_TOKEN>" \\
  -d '{
    "fhir_url": "https://your-fhir-server.com/Bundle/patient-001"
  }'`;

    document.getElementById('curl-auth').textContent   = auth;
    document.getElementById('curl-submit').textContent = submit;
    document.getElementById('curl-fetch').textContent  = fetch_;
})();

// ── Copy button handler ──
function copyCode(btn) {
    const pre = btn.closest('.code-block').querySelector('pre');
    navigator.clipboard.writeText(pre.textContent).then(() => {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
        }, 2000);
    });
}


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

document.getElementById('fhir-fetch-btn').addEventListener('click', async () => {
    const url = document.getElementById('fhir-url-input').value.trim();
    if (!url) {
        showMessage('Please enter a FHIR Server URL', true);
        return;
    }

    const btn = document.getElementById('fhir-fetch-btn');
    btn.textContent = 'Fetching...';
    btn.disabled = true;

    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/fhir/fetch-and-submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ fhir_url: url })
        });
        const data = await res.json();

        if (res.ok) {
            showMessage('FHIR data fetched from URL and saved successfully!');
            document.getElementById('fhir-url-input').value = '';
        } else {
            showMessage(data.detail || 'Failed to fetch FHIR data', true);
        }
    } catch (err) {
        showMessage('Network error', true);
    } finally {
        btn.textContent = 'Fetch & Submit';
        btn.disabled = false;
    }
});

checkAuth();
