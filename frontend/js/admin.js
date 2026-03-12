const API_URL = 'http://127.0.0.1:8000/api';
let currentUser = null;

window.onload = () => {
    const user = localStorage.getItem('user');
    if (!user) {
        window.location.href = 'index.html';
        return;
    }
    currentUser = JSON.parse(user);
    if (currentUser.role !== 'admin') {
        window.location.href = 'customer.html';
        return;
    }

    loadDashboard();
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

async function loadDashboard() {
    try {
        const res = await fetch(`${API_URL}/admin/dashboard`);
        if (!res.ok) throw new Error("Failed to load");
        const data = await res.json();
        
        document.getElementById('kpi-total').innerText = data.total_tickets;
        document.getElementById('kpi-active').innerText = data.active_tickets;
        document.getElementById('kpi-resolved').innerText = data.resolved_tickets;

        const grid = document.getElementById('departmentGrid');
        grid.innerHTML = '';

        Object.keys(data.department_stats).forEach(dept => {
            const stats = data.department_stats[dept];
            const deptName = dept.replace("_", " ");
            
            const card = document.createElement('div');
            card.className = 'dept-card glass-card';
            card.innerHTML = `
                <div class="dept-title">${deptName}</div>
                <div class="stat-row">
                    <span>Active Tickets:</span>
                    <span class="val active">${stats.active}</span>
                </div>
                <div class="stat-row">
                    <span>Resolved:</span>
                    <span class="val resolved">${stats.resolved}</span>
                </div>
                <div class="stat-row" style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.5);">
                    <span>Total Historical:</span>
                    <span>${stats.total}</span>
                </div>
            `;
            grid.appendChild(card);
        });

        loadPendingTickets();

    } catch (err) {
        console.error(err);
        alert("Error loading dashboard metrics. Ensure backend is running.");
    }
}

async function loadPendingTickets() {
    try {
        const res = await fetch(`${API_URL}/admin/pending`);
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('pendingTableBody');
        tbody.innerHTML = '';

        if (data.tickets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 2rem; color: rgba(255,255,255,0.5);">No pending tickets. AI is highly confident!</td></tr>`;
            return;
        }

        data.tickets.forEach(ticket => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 1rem; vertical-align: top;"><strong>${ticket.complaint_id}</strong></td>
                <td style="padding: 1rem; color: rgba(255,255,255,0.8);">${ticket.text}</td>
                <td style="padding: 1rem; vertical-align: top;">
                    <select id="assign-${ticket.complaint_id}" style="width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.3); color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 6px;">
                        <option value="Finance Department">Finance Department</option>
                        <option value="Customer Accounts">Customer Accounts</option>
                        <option value="Product Management">Product Management</option>
                        <option value="Customer Service">Customer Service</option>
                        <option value="Logistics & Delivery">Logistics & Delivery</option>
                        <option value="Spam" style="color: #ff6b6b; font-weight: bold;">🚫 Dismiss as Spam</option>
                    </select>
                </td>
                <td style="padding: 1rem; vertical-align: top;">
                    <button class="primary-btn" style="padding: 0.5rem 1rem; font-size: 0.9rem;" onclick="assignTicket('${ticket.complaint_id}')">Assign</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load pending tickets", err);
    }
}

async function assignTicket(complaintId) {
    const selector = document.getElementById(`assign-${complaintId}`);
    const selectedDept = selector.value;
    
    try {
        const res = await fetch(`${API_URL}/admin/assign`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                complaint_id: complaintId,
                target_department: selectedDept
            })
        });
        
        if (res.ok) {
            // Full refresh to update both pending list AND department stats
            loadDashboard();
        } else {
            const errData = await res.json();
            alert("Error: " + errData.detail);
        }
    } catch (err) {
        alert("Network error.");
    }
}
