const API_URL = 'http://127.0.0.1:8000/api';
let currentUser = null;

// Initialize
window.onload = () => {
    const user = localStorage.getItem('user');
    if (!user) {
        window.location.href = 'index.html';
        return;
    }
    currentUser = JSON.parse(user);
    if (currentUser.role !== 'customer') {
        window.location.href = 'admin.html';
        return;
    }

    document.getElementById('welcomeHeader').innerText = `Welcome, ${currentUser.name}`;
    loadHistory();
}

function switchTab(tabId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById(tabId).classList.add('active');

    if (tabId === 'history-tab') {
        loadHistory();
    }
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

async function submitComplaint(e) {
    e.preventDefault();
    const text = document.getElementById('complaintText').value;

    document.getElementById('submitSpinner').classList.remove('hidden');
    document.getElementById('submitBtn').disabled = true;

    try {
        const res = await fetch(`${API_URL}/complaints`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                customer_name: currentUser.name,
                customer_email: currentUser.email,
                text: text
            })
        });

        const data = await res.json();
        if (res.ok) {
            document.getElementById('res-id').innerText = data.complaint_id;
            document.getElementById('res-sla').innerText = data.sla;
            
            document.getElementById('resultOverlay').classList.remove('hidden');
            document.getElementById('complaintForm').reset();
            loadHistory(); // Silently refresh history
        } else {
            alert(data.detail || "Submission failed");
        }
    } catch (err) {
        alert("Network error connecting to backend.");
    } finally {
        document.getElementById('submitSpinner').classList.add('hidden');
        document.getElementById('submitBtn').disabled = false;
    }
}

function closeResult() {
    document.getElementById('resultOverlay').classList.add('hidden');
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_URL}/user/complaints/${currentUser.email}`);
        if (!res.ok) return;
        const data = await res.json();
        
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = '';

        data.complaints.forEach(c => {
            const tr = document.createElement('tr');
            
            // Format date
            const dateStr = new Date(c.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
            
            // Clean Status and Department
            const statusClass = c.status.replace(" ", "_"); // E.g., "In Progress" -> "In_Progress"
            const displayDept = c.department === 'Spam' ? '-' : c.department.replace("_", " ");

            tr.innerHTML = `
                <td>${dateStr}</td>
                <td><strong>${c.complaint_id}</strong></td>
                <td>${displayDept}</td>
                <td>${c.sla}</td>
                <td><span class="status-badge ${statusClass}">${c.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load history", err);
    }
}
