const API_URL = 'http://127.0.0.1:8000/api';

function switchAuthTab(tab) {
    document.getElementById('tab-login').classList.remove('active');
    document.getElementById('tab-register').classList.remove('active');
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'none';
    
    document.getElementById(`tab-${tab}`).classList.add('active');
    document.getElementById(`${tab}Form`).style.display = 'block';
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('user', JSON.stringify(data));
            if (data.role === 'admin') {
                window.location.href = 'admin.html';
            } else {
                window.location.href = 'customer.html';
            }
        } else {
            errorEl.innerText = data.detail;
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.innerText = 'Network error connecting to backend.';
        errorEl.style.display = 'block';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const role = 'customer'; // Default role to prevent self-registering as an Admin
    const errorEl = document.getElementById('regError');

    try {
        const res = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, email, password, role})
        });
        const data = await res.json();
        
        if (res.ok) {
            alert('Registration successful! Please login.');
            switchAuthTab('login');
        } else {
            errorEl.innerText = data.detail;
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.innerText = 'Network error connecting to backend.';
        errorEl.style.display = 'block';
    }
}

// Redirect if already logged in
window.onload = () => {
    const user = localStorage.getItem('user');
    if (user) {
        const parsed = JSON.parse(user);
        if (parsed.role === 'admin') window.location.href = 'admin.html';
        else window.location.href = 'customer.html';
    }
}
