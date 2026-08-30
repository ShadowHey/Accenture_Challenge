// On page load: check if already logged in
const existingToken = localStorage.getItem('auth_token');
if (existingToken) {
    // Validate token
    fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${existingToken}` } })
        .then(res => {
            if (res.ok) window.location.href = '/index.html';
            else localStorage.clear();
        })
        .catch(() => localStorage.clear());
}

// Form submit handler
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error-message');
    errorDiv.style.display = 'none';
    
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!res.ok) {
            const err = await res.json();
            errorDiv.textContent = err.detail || 'Invalid credentials';
            errorDiv.style.display = 'block';
            return;
        }
        
        const data = await res.json();
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('user_role', data.role);
        localStorage.setItem('hospital_code', data.hospital_code);
        localStorage.setItem('hospital_name', data.hospital_name);
        localStorage.setItem('username', data.username);
        window.location.href = '/index.html';
    } catch (err) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.style.display = 'block';
    }
});
