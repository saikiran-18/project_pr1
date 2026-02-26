// Tab Switching Logic
function switchTab(tabId) {
    // Update nav links
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Update views
    document.querySelectorAll('.view-section').forEach(section => {
        section.classList.add('hidden');
        section.classList.remove('active');
    });

    document.getElementById(tabId).classList.remove('hidden');
    document.getElementById(tabId).classList.add('active');

    // Load data if switching to dashboard
    if (tabId === 'dashboard-tab') {
        loadAnalytics();
    }
}

// Form Submission Logic
const API_BASE = "http://localhost:8000/api";

document.getElementById('complaintForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('submitSpinner');
    const btnText = submitBtn.querySelector('span');

    // UI Loading State
    submitBtn.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = 'Processing...';

    const payload = {
        customer_name: document.getElementById('name').value,
        customer_email: document.getElementById('email').value,
        text: document.getElementById('complaintText').value
    };

    try {
        const response = await fetch(`${API_BASE}/complaints`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        showResult(data);
        document.getElementById('complaintForm').reset();

    } catch (error) {
        console.error("Error submitting complaint:", error);
        alert("There was an error submitting your complaint. Ensure the local FastAPI server is running.");
    } finally {
        // Reset UI
        submitBtn.disabled = false;
        spinner.classList.add('hidden');
        btnText.textContent = 'Submit Complaint';
    }
});

// Result Modal Logic
function showResult(data) {
    document.getElementById('res-id').textContent = data.complaint_id;
    document.getElementById('res-dept').textContent = data.department;
    document.getElementById('res-category').textContent = data.category;
    document.getElementById('res-priority').textContent = data.priority;
    document.getElementById('res-sla').textContent = data.sla;

    // Manage dynamic styling based on priority
    const priorityBadge = document.getElementById('res-priority');
    if (data.priority === 'Critical') priorityBadge.style.color = '#dc2626';
    if (data.priority === 'Low') priorityBadge.style.color = '#10b981';

    document.getElementById('resultOverlay').classList.remove('hidden');
}

function closeResult() {
    document.getElementById('resultOverlay').classList.add('hidden');
}

// Analytics Dashboard Logic
async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics`);
        if (!response.ok) return;

        const data = await response.json();

        // Update Total
        document.getElementById('kpi-total').textContent = data.total;

        // Render simple bar charts
        renderChart('categoryChart', data.categories, data.total);
        renderChart('sentimentChart', data.sentiments, data.total);
        renderChart('priorityChart', data.priorities, data.total);

    } catch (error) {
        console.error("Failed to load analytics:", error);
    }
}

function renderChart(containerId, dataObj, total) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Clear prev

    if (total === 0) {
        container.innerHTML = '<p style="color:var(--text-muted)">No data available yet.</p>';
        return;
    }

    // Sort by count descending
    const sortedEntries = Object.entries(dataObj).sort((a, b) => b[1] - a[1]);

    sortedEntries.forEach(([label, count]) => {
        const percentage = Math.round((count / total) * 100);

        const row = document.createElement('div');
        row.className = 'chart-row';
        row.innerHTML = `
            <div class="chart-label">${label}</div>
            <div class="chart-bar-track">
                <div class="chart-bar-fill" style="width: 0%"></div>
            </div>
            <div class="chart-value">${count}</div>
        `;
        container.appendChild(row);

        // Animate width after insertion
        setTimeout(() => {
            row.querySelector('.chart-bar-fill').style.width = `${percentage}%`;
        }, 50);
    });
}
