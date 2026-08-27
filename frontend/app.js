const API_BASE = '/api';

async function fetchQueue() {
    const res = await fetch(`${API_BASE}/queue`);
    const data = await res.json();
    renderQueue(data);
}

async function fetchAudit() {
    const res = await fetch(`${API_BASE}/audit`);
    const data = await res.json();
    renderAudit(data);
}

function renderQueue(queue) {
    const container = document.getElementById('queue-container');
    container.innerHTML = '';
    
    if (queue.length === 0) {
        container.innerHTML = '<p>No patients in queue.</p>';
        return;
    }

    queue.forEach(item => {
        const p = item.patient;
        const tr = item.triage_result;
        
        let badges = '';
        if (item.reassessment_required) badges += '<span class="badge-reassess">REASSESSMENT REQUIRED</span> ';
        if (item.escalation_required) badges += '<span class="badge-escalate">ESCALATION REQUIRED</span> ';
        if (tr.escalation) badges += '<span class="badge-escalate">SAFETY ESCALATION</span> ';
        
        const waitTime = Math.floor(Date.now()/1000 - item.added_at);
        
        const cardClass = tr.priority.replace(' ', '-').toLowerCase();

        const card = document.createElement('div');
        card.className = `patient-card ${cardClass}`;
        
        const reasonsHtml = tr.reasons.map(r => `<li>${r}</li>`).join('');

        card.innerHTML = `
            <h3>${p.name} (ID: ${p.id}, Age: ${p.age}) <span>${tr.priority}</span></h3>
            <p><strong>Complaint:</strong> ${p.chief_complaint}</p>
            <p><strong>Confidence:</strong> ${(tr.confidence * 100).toFixed(0)}% (${tr.uncertainty} uncertainty)</p>
            <p><strong>Wait Time:</strong> ${waitTime}s ${badges}</p>
            <div><strong>Reasons:</strong><ul>${reasonsHtml}</ul></div>
            <div style="margin-top:10px;">
                <button class="btn-primary" onclick="openOverrideModal('${p.id}', '${tr.priority}')">Clinician Override</button>
                <button class="btn-warning" onclick="openVitalsModal('${p.id}')">Update Vitals</button>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderAudit(logs) {
    const container = document.getElementById('audit-container');
    container.innerHTML = '';
    
    if (logs.length === 0) {
        container.innerHTML = '<p>No overrides recorded.</p>';
        return;
    }
    
    logs.forEach(log => {
        const div = document.createElement('div');
        div.className = 'audit-log';
        const d = new Date(log.timestamp * 1000);
        div.innerHTML = `
            <strong>${d.toLocaleTimeString()} - Patient: ${log.patient_id}</strong><br/>
            Changed: ${log.original_priority} &rarr; ${log.new_priority}<br/>
            Reason: <em>${log.reason}</em>
        `;
        container.appendChild(div);
    });
}

// Surge Event
document.getElementById('btn-surge').addEventListener('click', async () => {
    await fetch(`${API_BASE}/surge`, { method: 'POST' });
    fetchQueue();
});

// Clear Event
document.getElementById('btn-clear').addEventListener('click', async () => {
    await fetch(`${API_BASE}/clear`, { method: 'POST' });
    fetchQueue();
    fetchAudit();
});

// Modal Logic for Override
const modalOverride = document.getElementById('override-modal');
const overridePatientId = document.getElementById('override-patient-id');
const overrideCurrentPrio = document.getElementById('override-current-prio');
let currentOverrideId = null;

window.openOverrideModal = function(id, prio) {
    currentOverrideId = id;
    overridePatientId.textContent = id;
    overrideCurrentPrio.textContent = prio;
    document.getElementById('new-priority').value = prio;
    document.getElementById('override-reason').value = '';
    modalOverride.style.display = 'block';
};

document.querySelector('.close-btn').onclick = () => modalOverride.style.display = 'none';

document.getElementById('btn-submit-override').onclick = async () => {
    const newPrio = document.getElementById('new-priority').value;
    const reason = document.getElementById('override-reason').value;
    
    if(!reason) return alert('Please provide a reason');
    
    await fetch(`${API_BASE}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            patient_id: currentOverrideId,
            new_priority: newPrio,
            reason: reason
        })
    });
    
    modalOverride.style.display = 'none';
    fetchQueue();
    fetchAudit();
};

// Modal Logic for Vitals Update
const modalVitals = document.getElementById('vitals-modal');
const vitalsPatientId = document.getElementById('vitals-patient-id');
let currentVitalsId = null;

window.openVitalsModal = function(id) {
    currentVitalsId = id;
    vitalsPatientId.textContent = id;
    document.getElementById('vitals-hr').value = '';
    document.getElementById('vitals-spo2').value = '';
    modalVitals.style.display = 'block';
};

document.querySelector('.close-btn-vitals').onclick = () => modalVitals.style.display = 'none';

document.getElementById('btn-submit-vitals').onclick = async () => {
    const hr = document.getElementById('vitals-hr').value;
    const spo2 = document.getElementById('vitals-spo2').value;
    
    const body = { patient_id: currentVitalsId };
    if(hr) body.heart_rate = parseInt(hr);
    if(spo2) body.spo2 = parseInt(spo2);

    await fetch(`${API_BASE}/queue/vitals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    
    modalVitals.style.display = 'none';
    fetchQueue();
};

// Polling for demo purposes
setInterval(() => {
    fetchQueue();
}, 2000);

// Init
fetchQueue();
fetchAudit();
