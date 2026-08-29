const API_BASE = '/api';

// ─── Data Fetching ─────────────────────────────────────────────────────────────

async function fetchQueue() {
    try {
        const res = await fetch(`${API_BASE}/queue`);
        const data = await res.json();
        renderQueue(data);
    } catch (e) { console.error('Failed to fetch queue:', e); }
}

async function fetchAudit() {
    try {
        const filter = document.getElementById('audit-filter-type').value;
        const url = filter ? `${API_BASE}/audit?event_type=${filter}` : `${API_BASE}/audit`;
        const res = await fetch(url);
        const data = await res.json();
        renderAudit(data);
    } catch (e) { console.error('Failed to fetch audit:', e); }
}

let allCompletedPatients = [];
async function fetchCompleted() {
    try {
        const res = await fetch(`${API_BASE}/completed`);
        const data = await res.json();
        if (JSON.stringify(data) !== JSON.stringify(allCompletedPatients)) {
            allCompletedPatients = data;
            renderCompleted();
        }
    } catch (e) { console.error('Failed to fetch completed patients:', e); }
}

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();
        renderStats(data);
    } catch (e) { console.error('Failed to fetch stats:', e); }
}

// ─── Rendering ─────────────────────────────────────────────────────────────────

function renderStats(stats) {
    const q = stats.queue;
    const a = stats.audit;

    document.getElementById('stat-total').textContent = q.total_patients;
    document.getElementById('stat-l1').textContent = q.level_counts['LEVEL 1'] || 0;
    document.getElementById('stat-l2').textContent = q.level_counts['LEVEL 2'] || 0;
    document.getElementById('stat-l3').textContent = q.level_counts['LEVEL 3'] || 0;
    document.getElementById('stat-l4').textContent = q.level_counts['LEVEL 4'] || 0;
    document.getElementById('stat-l5').textContent = q.level_counts['LEVEL 5'] || 0;

    const avgWait = q.avg_wait_seconds;
    document.getElementById('stat-avg-wait').textContent =
        avgWait > 60 ? `${Math.floor(avgWait/60)}m` : `${Math.round(avgWait)}s`;

    document.getElementById('stat-ml-agree').textContent =
        a.ml_agreement_rate !== null ? `${Math.round(a.ml_agreement_rate * 100)}%` : '—';

    const surgeInd = document.getElementById('surge-indicator');
    const surgeStopBtn = document.getElementById('btn-surge-stop');
    if (q.surge_mode) {
        surgeInd.style.display = 'flex';
        surgeStopBtn.style.display = 'inline-block';
    } else {
        surgeInd.style.display = 'none';
        surgeStopBtn.style.display = 'none';
    }
}

function renderQueue(queue) {
    const container = document.getElementById('queue-container');
    const hContainer = document.getElementById('horizontal-queue-container');
    const hWrapper = document.getElementById('hq-wrapper');
    
    container.innerHTML = '';
    hContainer.innerHTML = '';

    if (queue.length === 0) {
        container.innerHTML = '<p class="empty-state">No patients in queue. Click "Add Patient" or "Load Seed Patients" to begin.</p>';
        if (hWrapper) hWrapper.style.display = 'none';
        return;
    }
    
    if (hWrapper) hWrapper.style.display = 'flex';

    queue.forEach(item => {
        const p = item.patient;
        const tr = item.triage_result;

        // Badges
        let badges = '';
        if (item.reassessment_required) badges += '<span class="badge-reassess pulse">⚠ REASSESSMENT DUE</span> ';
        if (item.escalation_required) badges += '<span class="badge-escalate pulse">🔴 ESCALATION REQUIRED</span> ';
        if (tr.escalation) badges += '<span class="badge-escalate">⬆ SAFETY ESCALATION</span> ';

        const waitTime = Math.floor(Date.now()/1000 - item.added_at);
        const waitDisplay = waitTime > 60 ? `${Math.floor(waitTime/60)}m ${waitTime%60}s` : `${waitTime}s`;

        const cardClass = tr.priority.replace(' ', '-').toLowerCase();

        // Age group badge
        const ageGroupBadge = `<span class="badge-age-${tr.age_group.toLowerCase()}">${tr.age_group}</span>`;

        // Source badge
        let sourceBadge = '';
        if (tr.source === 'ML_ESCALATED') sourceBadge = '<span class="badge-ml-escalated">ML ⬆</span>';
        else if (tr.source === 'HYBRID_AGREE') sourceBadge = '<span class="badge-ml-agree">ML ✓</span>';
        else if (tr.source === 'RULES_FLOOR') sourceBadge = '<span class="badge-rules-floor">Rules Floor</span>';
        else if (tr.source === 'CLINICIAN_OVERRIDE') sourceBadge = '<span class="badge-override">Clinician</span>';
        else sourceBadge = '<span class="badge-rules-only">Rules Only</span>';

        // Confidence bar
        const confPct = Math.round(tr.confidence * 100);
        const confColor = confPct >= 80 ? '#28a745' : confPct >= 50 ? '#ffc107' : '#dc3545';

        // ML confidence bar
        let mlBar = '';
        if (tr.ml_confidence !== null && tr.ml_confidence !== undefined) {
            const mlPct = Math.round(tr.ml_confidence * 100);
            mlBar = `
                <div class="confidence-row">
                    <span class="conf-label">ML: ${tr.ml_priority || 'N/A'} (${mlPct}%)</span>
                    <div class="conf-bar"><div class="conf-fill" style="width:${mlPct}%;background:#6f42c1;"></div></div>
                </div>`;
        }

        // Disagreement
        let disagreementHtml = '';
        if (tr.disagreement) {
            disagreementHtml = `<div class="disagreement">⚡ ${tr.disagreement}</div>`;
        }

        // Reasons
        const reasonsHtml = tr.reasons.map(r => `<li>${r}</li>`).join('');

        // Feature importances
        let importancesHtml = '';
        if (tr.feature_importances) {
            const entries = Object.entries(tr.feature_importances).slice(0, 5);
            if (entries.length > 0) {
                importancesHtml = `
                    <details class="importances">
                        <summary>ML Feature Importances</summary>
                        <ul>${entries.map(([k, v]) => `<li>${k}: ${(v*100).toFixed(1)}%</li>`).join('')}</ul>
                    </details>`;
            }
        }

        // Vitals display
        const v = p.vitals;
        const vitalsHtml = [
            v.heart_rate !== null ? `HR:${v.heart_rate}` : null,
            v.spo2 !== null ? `SpO2:${v.spo2}%` : null,
            v.temperature !== null ? `T:${v.temperature}°C` : null,
            v.respiratory_rate !== null ? `RR:${v.respiratory_rate}` : null,
            v.gcs !== null ? `GCS:${v.gcs}` : null,
            v.pain_scale !== null ? `Pain:${v.pain_scale}/10` : null,
            v.blood_pressure !== null ? `BP:${v.blood_pressure}` : null,
        ].filter(Boolean).join(' | ');

        // Reassessment count
        let reassessInfo = '';
        if (item.reassessment_count > 0) {
            reassessInfo = `<span class="reassess-count">Re-assessed ${item.reassessment_count}×</span>`;
        }

        const card = document.createElement('div');
        card.className = `patient-card ${cardClass}`;
        card.innerHTML = `
            <div class="card-header">
                <h3>${p.name} <span class="patient-id">(${p.id})</span></h3>
                <div class="card-badges">
                    ${ageGroupBadge}
                    <span class="priority-badge ${cardClass}">${tr.priority}</span>
                    ${sourceBadge}
                </div>
            </div>
            <div class="card-meta">
                Age: ${p.age} | ${p.gender} | ${p.arrival_mode || 'walk-in'} ${reassessInfo}
            </div>
            <p><strong>Complaint:</strong> ${p.chief_complaint}</p>
            <p class="vitals-line"><strong>Vitals:</strong> ${vitalsHtml || 'No vitals recorded'}</p>
            <div class="confidence-row">
                <span class="conf-label">Rules: ${tr.rules_priority} (${confPct}% conf)</span>
                <div class="conf-bar"><div class="conf-fill" style="width:${confPct}%;background:${confColor};"></div></div>
            </div>
            ${mlBar}
            ${disagreementHtml}
            <p><strong>Wait:</strong> ${waitDisplay} ${badges}</p>
            <details><summary>Triage Reasons</summary><ul>${reasonsHtml}</ul></details>
            ${importancesHtml}
            <div class="card-actions">
                <button class="btn-primary btn-sm" onclick="openOverrideModal('${p.id}', '${tr.priority}')">Override</button>
                <button class="btn-warning btn-sm" onclick="openVitalsModal('${p.id}')">Update Vitals</button>
                <button class="btn-danger btn-sm" onclick="dischargePatient('${p.id}')">Discharge</button>
            </div>
        `;
        container.appendChild(card);
        
        // --- Horizontal Queue Item ---
        const hCard = document.createElement('div');
        hCard.className = `horizontal-queue-item level-${tr.priority.split(' ')[1]}`;
        const genderFull = p.gender === 'M' ? 'Male' : (p.gender === 'F' ? 'Female' : 'Other');
        hCard.innerHTML = `
            <div class="hq-name">${p.name}</div>
            <div class="hq-gender">${genderFull}</div>
            <div class="hq-age">${p.age}</div>
            <div class="hq-id">${p.id}</div>
            <div class="hq-tooltip-data" style="display: none;">
                <strong>Complaint:</strong> ${p.chief_complaint}<br>
                <strong>Vitals:</strong> ${vitalsHtml || 'No vitals'}<br>
                <strong>Priority:</strong> ${tr.priority}<br>
                <strong>Wait:</strong> ${waitDisplay}
            </div>
        `;
        if (hContainer) hContainer.appendChild(hCard);
    });
}

function renderAudit(logs) {
    const container = document.getElementById('audit-container');
    container.innerHTML = '';

    if (logs.length === 0) {
        container.innerHTML = '<p class="empty-state">No events recorded.</p>';
        return;
    }

    // Show latest 50
    logs.slice(0, 50).forEach(log => {
        const div = document.createElement('div');
        div.className = `audit-log audit-${log.event_type.toLowerCase()}`;
        const d = new Date(log.timestamp * 1000);
        const time = d.toLocaleTimeString();

        let detailHtml = '';
        const det = log.details;
        switch(log.event_type) {
            case 'TRIAGE':
                detailHtml = `Priority: <strong>${det.priority}</strong> | Source: ${det.source} | Confidence: ${Math.round(det.confidence*100)}%`;
                break;
            case 'RETRIAGE':
                detailHtml = `${det.old_priority} → <strong>${det.new_priority}</strong> | Trigger: ${det.trigger}`;
                break;
            case 'OVERRIDE':
                detailHtml = `${det.original_priority} → <strong>${det.new_priority}</strong><br/>Reason: <em>${det.reason}</em>`;
                break;
            case 'DISAGREEMENT':
                detailHtml = `Rules: ${det.rules_priority} vs ML: ${det.ml_priority} → Final: <strong>${det.final_priority}</strong> (${det.resolution})`;
                break;
            case 'DETERIORATION':
                detailHtml = `Vitals worsened`;
                break;
            case 'SURGE':
                detailHtml = `Action: ${det.action} | Patients: ${det.patient_count}`;
                break;
            case 'DISCHARGE':
                detailHtml = `Patient discharged`;
                break;
            default:
                detailHtml = JSON.stringify(det);
        }

        div.innerHTML = `
            <div class="audit-header">
                <span class="audit-type badge-${log.event_type.toLowerCase()}">${log.event_type}</span>
                <span class="audit-time">${time}</span>
            </div>
            <div class="audit-patient">${log.patient_id}</div>
            <div class="audit-detail">${detailHtml}</div>
        `;
        container.appendChild(div);
    });
}

// ─── Button Handlers ───────────────────────────────────────────────────────────

document.getElementById('btn-surge-seed').addEventListener('click', async () => {
    await fetch(`${API_BASE}/surge`, { method: 'POST' });
    refreshAll();
});

document.getElementById('btn-surge-3x').addEventListener('click', async () => {
    const btn = document.getElementById('btn-surge-3x');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    await fetch(`${API_BASE}/surge/start`, { method: 'POST' });
    btn.disabled = false;
    btn.textContent = 'Simulate Surge (3×)';
    refreshAll();
});

document.getElementById('btn-surge-stop').addEventListener('click', async () => {
    await fetch(`${API_BASE}/surge/stop`, { method: 'POST' });
    refreshAll();
});

document.getElementById('btn-deteriorate').addEventListener('click', async () => {
    const btn = document.getElementById('btn-deteriorate');
    btn.disabled = true;
    const res = await fetch(`${API_BASE}/simulate/deteriorate`, { method: 'POST' });
    const data = await res.json();
    btn.disabled = false;
    if (data.patients_affected > 0) {
        alert(`${data.patients_affected} patient(s) deteriorated and re-triaged.`);
    } else {
        alert('No patients to deteriorate (queue may be empty).');
    }
    refreshAll();
});

document.getElementById('btn-clear').addEventListener('click', async () => {
    await fetch(`${API_BASE}/clear`, { method: 'POST' });
    refreshAll();
});

// ─── Add Patient Modal ─────────────────────────────────────────────────────────

document.getElementById('btn-add-patient').addEventListener('click', () => {
    document.getElementById('add-patient-modal').style.display = 'block';
});

// Toggle Logic
const requiredFormFields = ['ap-name', 'ap-age', 'ap-gender', 'ap-complaint'];
document.querySelectorAll('input[name="ap_mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'form') {
            document.getElementById('ap-form-view').style.display = 'block';
            document.getElementById('ap-json-view').style.display = 'none';
            requiredFormFields.forEach(id => document.getElementById(id).setAttribute('required', 'true'));
        } else {
            document.getElementById('ap-form-view').style.display = 'none';
            document.getElementById('ap-json-view').style.display = 'block';
            requiredFormFields.forEach(id => document.getElementById(id).removeAttribute('required'));
        }
    });
});

// Copy Sample JSON Logic
document.getElementById('btn-copy-sample').addEventListener('click', () => {
    const sample = document.getElementById('ap-json-input').placeholder;
    navigator.clipboard.writeText(sample).then(() => {
        const btn = document.getElementById('btn-copy-sample');
        const origText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = origText, 2000);
    });
});

document.getElementById('add-patient-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const mode = document.querySelector('input[name="ap_mode"]:checked').value;

    if (mode === 'form') {
        const body = {
            name: document.getElementById('ap-name').value,
            age: parseInt(document.getElementById('ap-age').value),
            gender: document.getElementById('ap-gender').value,
            chief_complaint: document.getElementById('ap-complaint').value,
            arrival_mode: document.getElementById('ap-arrival').value,
            history_available: document.getElementById('ap-history').value === 'true',
        };

        const hr = document.getElementById('ap-hr').value;
        const bp = document.getElementById('ap-bp').value;
        const spo2 = document.getElementById('ap-spo2').value;
        const temp = document.getElementById('ap-temp').value;
        const rr = document.getElementById('ap-rr').value;
        const gcs = document.getElementById('ap-gcs').value;
        const pain = document.getElementById('ap-pain').value;

        if (hr) body.heart_rate = parseInt(hr);
        if (bp) body.blood_pressure = bp;
        if (spo2) body.spo2 = parseInt(spo2);
        if (temp) body.temperature = parseFloat(temp);
        if (rr) body.respiratory_rate = parseInt(rr);
        if (gcs) body.gcs = parseInt(gcs);
        if (pain) body.pain_scale = parseInt(pain);

        const medHist = document.getElementById('ap-med-history').value;
        body.medical_history = medHist ? medHist.split(',').map(s => s.trim()).filter(Boolean) : [];

        const signs = document.getElementById('ap-signs').value;
        body.observed_signs = signs ? signs.split(',').map(s => s.trim()).filter(Boolean) : [];

        body.symptoms = [];

        try {
            await fetch(`${API_BASE}/patient`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            document.getElementById('add-patient-modal').style.display = 'none';
            document.getElementById('add-patient-form').reset();
            document.getElementById('ap-json-input').value = '';
            refreshAll();
        } catch (err) {
            alert('Error adding patient: ' + err.message);
        }

    } else {
        // JSON Mode
        const rawInput = document.getElementById('ap-json-input').value.trim();
        if (!rawInput) {
            alert('Please paste or type JSON data.');
            return;
        }

        // Strip JS-style comments: // and /* */
        const strippedInput = rawInput.replace(/\/\/.*|\/\*[\s\S]*?\*\//g, '');
        let parsedData;
        try {
            parsedData = JSON.parse(strippedInput);
        } catch (err) {
            alert(`Malformed JSON:\n${err.message}`);
            return;
        }

        const patients = Array.isArray(parsedData) ? parsedData : [parsedData];
        if (patients.length === 0) {
            alert('No patients found in JSON.');
            return;
        }

        // Validate required fields
        for (let i = 0; i < patients.length; i++) {
            const p = patients[i];
            const requiredFields = ['name', 'age', 'gender', 'chief_complaint'];
            for (const field of requiredFields) {
                if (p[field] === undefined || p[field] === null || p[field] === '') {
                    alert(`Validation Error in patient #${i + 1}:\nMissing required parameter '${field}'`);
                    return;
                }
            }
        }

        try {
            const apBtn = document.getElementById('ap-submit-btn');
            const originalText = apBtn.textContent;
            apBtn.textContent = 'Submitting...';
            apBtn.disabled = true;

            // Submit all patients concurrently
            await Promise.all(patients.map(p => 
                fetch(`${API_BASE}/patient`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(p)
                }).then(res => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.json();
                })
            ));

            document.getElementById('add-patient-modal').style.display = 'none';
            document.getElementById('add-patient-form').reset();
            document.getElementById('ap-json-input').value = '';
            refreshAll();
            
            apBtn.textContent = originalText;
            apBtn.disabled = false;
        } catch (err) {
            alert('Error adding patients: ' + err.message);
            const apBtn = document.getElementById('ap-submit-btn');
            apBtn.textContent = 'Submit Patient';
            apBtn.disabled = false;
        }
    }
});

// ─── Override Modal ────────────────────────────────────────────────────────────

let currentOverrideId = null;

window.openOverrideModal = function(id, prio) {
    currentOverrideId = id;
    document.getElementById('override-patient-id').textContent = id;
    document.getElementById('override-current-prio').textContent = prio;
    document.getElementById('new-priority').value = prio;
    document.getElementById('override-reason').value = '';
    document.getElementById('override-modal').style.display = 'block';
};

document.getElementById('btn-submit-override').onclick = async () => {
    const newPrio = document.getElementById('new-priority').value;
    const reason = document.getElementById('override-reason').value;
    if (!reason) return alert('Please provide a reason for the override.');

    await fetch(`${API_BASE}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            patient_id: currentOverrideId,
            new_priority: newPrio,
            reason: reason
        })
    });

    document.getElementById('override-modal').style.display = 'none';
    refreshAll();
};

// ─── Vitals Modal ──────────────────────────────────────────────────────────────

let currentVitalsId = null;

window.openVitalsModal = function(id) {
    currentVitalsId = id;
    document.getElementById('vitals-patient-id').textContent = id;
    document.getElementById('vitals-hr').value = '';
    document.getElementById('vitals-spo2').value = '';
    document.getElementById('vitals-temp').value = '';
    document.getElementById('vitals-rr').value = '';
    document.getElementById('vitals-gcs').value = '';
    document.getElementById('vitals-modal').style.display = 'block';
};

document.getElementById('btn-submit-vitals').onclick = async () => {
    const body = { patient_id: currentVitalsId };
    const hr = document.getElementById('vitals-hr').value;
    const spo2 = document.getElementById('vitals-spo2').value;
    const temp = document.getElementById('vitals-temp').value;
    const rr = document.getElementById('vitals-rr').value;
    const gcs = document.getElementById('vitals-gcs').value;

    if (hr) body.heart_rate = parseInt(hr);
    if (spo2) body.spo2 = parseInt(spo2);
    if (temp) body.temperature = parseFloat(temp);
    if (rr) body.respiratory_rate = parseInt(rr);
    if (gcs) body.gcs = parseInt(gcs);

    await fetch(`${API_BASE}/queue/vitals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    document.getElementById('vitals-modal').style.display = 'none';
    refreshAll();
};

// ─── Discharge ─────────────────────────────────────────────────────────────────

window.dischargePatient = async function(id) {
    if (!confirm(`Discharge patient ${id}?`)) return;
    await fetch(`${API_BASE}/queue/${id}/discharge`, { method: 'POST' });
    refreshAll();
};

// ─── Modal Close Handlers ──────────────────────────────────────────────────────

document.querySelectorAll('.close-btn').forEach(btn => {
    btn.onclick = () => {
        const modalId = btn.getAttribute('data-modal');
        if (modalId) document.getElementById(modalId).style.display = 'none';
    };
});

// Close modals on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};

// Audit filter change
document.getElementById('audit-filter-type').addEventListener('change', fetchAudit);

// ─── Refresh All ───────────────────────────────────────────────────────────────

function refreshAll() {
    fetchQueue();
    fetchAudit();
    fetchStats();
    fetchCompleted();
}

// Polling
setInterval(refreshAll, 3000);

// Init
refreshAll();

// ─── Shared Horizontal Queue Tooltip ───────────────────────────────────────────
const hQueueContainer = document.getElementById('horizontal-queue-container');
const sharedTooltip = document.getElementById('shared-hq-tooltip');

if (hQueueContainer && sharedTooltip) {
    hQueueContainer.addEventListener('mouseover', (e) => {
        const card = e.target.closest('.horizontal-queue-item');
        if (card) {
            const dataDiv = card.querySelector('.hq-tooltip-data');
            if (dataDiv) {
                sharedTooltip.innerHTML = dataDiv.innerHTML;
                const rect = card.getBoundingClientRect();
                sharedTooltip.style.left = `${rect.left + rect.width / 2}px`;
                // Position above the card, centering via transform
                sharedTooltip.style.top = `${rect.top + window.scrollY - 10}px`;
                sharedTooltip.style.transform = 'translate(-50%, -100%)';
                sharedTooltip.classList.add('visible');
            }
        }
    });

    hQueueContainer.addEventListener('mouseout', (e) => {
        const card = e.target.closest('.horizontal-queue-item');
        if (card) {
            sharedTooltip.classList.remove('visible');
        }
    });
}

function renderCompleted() {
    const container = document.getElementById('completed-container');
    if (!container) return;
    container.innerHTML = '';
    
    const query = (document.getElementById('completed-search').value || '').toLowerCase();
    
    const filtered = allCompletedPatients.filter(item => {
        const p = item.patient;
        return p.name.toLowerCase().includes(query) || 
               p.id.toLowerCase().includes(query) || 
               p.chief_complaint.toLowerCase().includes(query);
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state">No completed patients found.</div>';
        return;
    }

    filtered.forEach(item => {
        const p = item.patient;
        const tr = item.triage_result;
        
        const card = document.createElement('div');
        card.className = `patient-card level-${tr.priority.split(' ')[1]}`;
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px;">
                <div>
                    <div style="font-weight: bold; font-size: 15px;">${p.name}</div>
                    <div style="color: #666; font-size: 12px;">${p.id}</div>
                </div>
                <div style="font-weight: bold; font-size: 11px; padding: 2px 6px; border-radius: 4px;" class="priority-badge level-${tr.priority.split(' ')[1]}">${tr.priority}</div>
            </div>
            <div style="margin-top: 10px; display: flex; gap: 5px; align-items: center; justify-content: space-between;">
                <div>
                    <button class="btn-primary btn-sm" onclick="openReviewModal('${p.id}')">Review</button>
                    <button class="btn-secondary btn-sm" onclick="downloadHandoff('${p.id}')">Download</button>
                </div>
                <div class="dropdown">
                    <button class="dropdown-btn" onclick="const content = this.nextElementSibling; const isVisible = content.style.display === 'block'; document.querySelectorAll('.dropdown-content').forEach(el => el.style.display = 'none'); content.style.display = isVisible ? 'none' : 'block'; event.stopPropagation();">&#8942;</button>
                    <div class="dropdown-content" style="text-align: left;">
                        <a href="#" onclick="archivePatient('${p.id}'); return false;" style="color: #dc3545;">Archive</a>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

const searchEl = document.getElementById('completed-search');
if(searchEl) searchEl.addEventListener('input', renderCompleted);

window.archivePatient = async function(patientId) {
    if (!confirm('Archive this completed patient?\n\nThis will remove the patient from the Completed Patients list.')) return;
    try {
        await fetch(`${API_BASE}/completed/${patientId}/archive`, { method: 'POST' });
        refreshAll();
    } catch(e) {
        alert('Failed to archive patient.');
    }
};

window.openReviewModal = async function(patientId) {
    const item = allCompletedPatients.find(x => x.patient.id === patientId);
    if (!item) return;
    const p = item.patient;
    const tr = item.triage_result;
    
    let auditLogs = [];
    try {
        const res = await fetch(`${API_BASE}/audit`);
        const logs = await res.json();
        auditLogs = logs.filter(l => l.patient_id === patientId);
    } catch(e) {}

    let auditHtml = auditLogs.length === 0 ? '<p>No events recorded.</p>' : 
        '<ul style="padding-left: 20px;">' + auditLogs.map(log => {
            const timeStr = new Date(log.timestamp * 1000).toLocaleTimeString();
            let detailStr = '';
            if (log.event_type === 'DETERIORATION') detailStr = 'Vitals worsened';
            else if (log.event_type === 'TRIAGE') detailStr = 'Initial triage performed';
            else if (log.event_type === 'RETRIAGE') detailStr = `Re-triaged (${log.details.trigger})`;
            else if (log.event_type === 'OVERRIDE') detailStr = `Clinician override: ${log.details.reason}`;
            else if (log.event_type === 'DISAGREEMENT') detailStr = 'Disagreement resolved';
            else if (log.event_type === 'DISCHARGE') detailStr = 'Discharged from queue';
            else detailStr = JSON.stringify(log.details);
            return `<li style="margin-bottom: 5px;"><strong>${timeStr}</strong> <span style="color:#666;">[${log.event_type}]</span> - ${detailStr}</li>`;
        }).join('') + '</ul>';

    const arrivalTime = new Date(item.added_at * 1000).toLocaleTimeString();
    const completedTime = new Date(item.completed_at * 1000).toLocaleTimeString();
    const waitTimeMins = Math.round((item.completed_at - item.added_at) / 60);

    const initV = item.initial_vitals || {};
    const currV = p.vitals;

    let vitalChangesHtml = '';
    let latestVitalsHtml = '';
    let hasChanges = false;
    
    const metrics = [
        { label: 'HR', init: initV.heart_rate, curr: currV.heart_rate, unit: '' },
        { label: 'SpO2', init: initV.spo2, curr: currV.spo2, unit: '%' },
        { label: 'Temp', init: initV.temperature, curr: currV.temperature, unit: '°C' },
        { label: 'RR', init: initV.respiratory_rate, curr: currV.respiratory_rate, unit: '' },
        { label: 'GCS', init: initV.gcs, curr: currV.gcs, unit: '' },
        { label: 'Pain', init: initV.pain_scale, curr: currV.pain_scale, unit: '' }
    ];
    
    metrics.forEach(m => {
        if (m.init !== m.curr && m.curr !== undefined && m.curr !== null) {
            hasChanges = true;
            vitalChangesHtml += `<p style="margin:2px 0;"><strong>${m.label}:</strong> ${m.init||'-'}${m.unit} &rarr; ${m.curr}${m.unit}</p>`;
        }
    });

    if (hasChanges) {
        latestVitalsHtml = `
            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">LATEST VITALS</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 14px;">
                <p style="margin:0;"><strong>HR:</strong> ${currV.heart_rate || '-'}</p>
                <p style="margin:0;"><strong>BP:</strong> ${currV.blood_pressure || (currV.systolic_bp ? currV.systolic_bp + '/' + (currV.diastolic_bp||'') : '-')}</p>
                <p style="margin:0;"><strong>RR:</strong> ${currV.respiratory_rate || '-'}</p>
                <p style="margin:0;"><strong>Temp:</strong> ${currV.temperature || '-'}°C</p>
                <p style="margin:0;"><strong>SpO2:</strong> ${currV.spo2 || '-'}%</p>
                <p style="margin:0;"><strong>GCS:</strong> ${currV.gcs || '-'}</p>
                <p style="margin:0;"><strong>Pain:</strong> ${currV.pain_scale || '-'}</p>
            </div>
            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">VITAL CHANGES</h3>
            ${vitalChangesHtml}
        `;
    }

    const modalBody = document.getElementById('review-modal-body');
    if (modalBody) {
        modalBody.innerHTML = `
            <h2 style="margin-top: 0;">PATIENT TRIAGE RECORD</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">PATIENT INFORMATION</h3>
                    <p style="margin: 2px 0;"><strong>Name:</strong> ${p.name}</p>
                    <p style="margin: 2px 0;"><strong>ID:</strong> ${p.id}</p>
                    <p style="margin: 2px 0;"><strong>Age:</strong> ${p.age}</p>
                    <p style="margin: 2px 0;"><strong>Gender:</strong> ${p.gender}</p>
                    <p style="margin: 2px 0;"><strong>Arrival Mode:</strong> ${p.arrival_mode || 'Walk-in'}</p>
                </div>
                <div>
                    <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">WAITING INFORMATION</h3>
                    <p style="margin: 2px 0;"><strong>Arrival Time:</strong> ${arrivalTime}</p>
                    <p style="margin: 2px 0;"><strong>Initial Triage Time:</strong> ${arrivalTime}</p>
                    <p style="margin: 2px 0;"><strong>Completion Time:</strong> ${completedTime}</p>
                    <p style="margin: 2px 0;"><strong>Total Waiting Time:</strong> ${waitTimeMins} mins</p>
                </div>
            </div>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">CHIEF COMPLAINT</h3>
            <p style="margin: 2px 0;">${p.chief_complaint}</p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">MEDICAL HISTORY</h3>
            <p style="margin: 2px 0;">${p.medical_history.length ? p.medical_history.join(', ') : 'None reported'}</p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">OBSERVED SIGNS</h3>
            <p style="margin: 2px 0;">${p.observed_signs.length ? p.observed_signs.join(', ') : 'None'}</p>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">INITIAL VITALS</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 14px;">
                <p style="margin:0;"><strong>HR:</strong> ${initV.heart_rate || '-'}</p>
                <p style="margin:0;"><strong>BP:</strong> ${initV.blood_pressure || (initV.systolic_bp ? initV.systolic_bp + '/' + (initV.diastolic_bp||'') : '-')}</p>
                <p style="margin:0;"><strong>RR:</strong> ${initV.respiratory_rate || '-'}</p>
                <p style="margin:0;"><strong>Temp:</strong> ${initV.temperature || '-'}°C</p>
                <p style="margin:0;"><strong>SpO2:</strong> ${initV.spo2 || '-'}%</p>
                <p style="margin:0;"><strong>GCS:</strong> ${initV.gcs || '-'}</p>
                <p style="margin:0;"><strong>Pain:</strong> ${initV.pain_scale || '-'}</p>
            </div>

            ${latestVitalsHtml}

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">TRIAGE ASSESSMENT</h3>
            <p style="margin: 2px 0;"><strong>Final Priority:</strong> ${tr.priority}</p>
            <p style="margin: 2px 0;"><strong>Decision Source:</strong> ${tr.source}</p>
            <p style="margin: 2px 0;"><strong>Rules Assessment:</strong> ${tr.rules_priority} (${Math.round(tr.confidence*100)}%)</p>
            <p style="margin: 2px 0;"><strong>ML Recommendation:</strong> ${tr.ml_priority || 'N/A'} (${tr.ml_confidence ? Math.round(tr.ml_confidence*100)+'%' : 'N/A'})</p>
            
            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">TRIAGE FACTORS</h3>
            <ul style="margin: 2px 0; padding-left: 20px;">${tr.reasons.map(r => `<li>${r}</li>`).join('')}</ul>

            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 15px;">AUDIT HISTORY</h3>
            ${auditHtml}
        `;
        document.getElementById('review-modal').style.display = 'block';
    }
};

window.downloadHandoff = async function(patientId) {
    const item = allCompletedPatients.find(x => x.patient.id === patientId);
    if (!item) return;
    
    const p = item.patient;
    const tr = item.triage_result;
    
    const arrivalTime = new Date(item.added_at * 1000).toLocaleTimeString();
    const completedTime = new Date(item.completed_at * 1000).toLocaleTimeString();
    const waitTimeMins = Math.round((item.completed_at - item.added_at) / 60);
    
    let auditLogs = [];
    try {
        const res = await fetch(`${API_BASE}/audit`);
        const logs = await res.json();
        auditLogs = logs.filter(l => l.patient_id === patientId);
    } catch(e) {}
    
    let auditHtml = auditLogs.length === 0 ? '<p>No events recorded.</p>' : 
        '<ul>' + auditLogs.map(log => {
            const timeStr = new Date(log.timestamp * 1000).toLocaleTimeString();
            let detailStr = '';
            if (log.event_type === 'DETERIORATION') detailStr = 'Vitals worsened';
            else if (log.event_type === 'TRIAGE') detailStr = 'Initial triage performed';
            else if (log.event_type === 'RETRIAGE') detailStr = `Re-triaged (${log.details.trigger})`;
            else if (log.event_type === 'OVERRIDE') detailStr = `Clinician override: ${log.details.reason}`;
            else if (log.event_type === 'DISAGREEMENT') detailStr = 'Disagreement resolved';
            else if (log.event_type === 'DISCHARGE') detailStr = 'Discharged from queue';
            else detailStr = JSON.stringify(log.details);
            return `<li><strong>${timeStr}</strong> [${log.event_type}] - ${detailStr}</li>`;
        }).join('') + '</ul>';

    const initV = item.initial_vitals || {};
    const currV = p.vitals;
    
    let vitalChangesHtml = '';
    let latestVitalsHtml = '';
    let hasChanges = false;
    
    const metrics = [
        { label: 'HR', init: initV.heart_rate, curr: currV.heart_rate, unit: '' },
        { label: 'SpO2', init: initV.spo2, curr: currV.spo2, unit: '%' },
        { label: 'Temp', init: initV.temperature, curr: currV.temperature, unit: '°C' },
        { label: 'RR', init: initV.respiratory_rate, curr: currV.respiratory_rate, unit: '' },
        { label: 'GCS', init: initV.gcs, curr: currV.gcs, unit: '' },
        { label: 'Pain', init: initV.pain_scale, curr: currV.pain_scale, unit: '' }
    ];
    
    metrics.forEach(m => {
        if (m.init !== m.curr && m.curr !== undefined && m.curr !== null) {
            hasChanges = true;
            vitalChangesHtml += `<p><strong>${m.label}:</strong> ${m.init||'-'}${m.unit} &rarr; ${m.curr}${m.unit}</p>`;
        }
    });
    
    if (hasChanges) {
        latestVitalsHtml = `
            <h2>LATEST / CURRENT VITALS</h2>
            <p>HR: ${currV.heart_rate || '-'}</p>
            <p>BP: ${currV.blood_pressure || (currV.systolic_bp ? currV.systolic_bp + '/' + (currV.diastolic_bp||'') : '-')}</p>
            <p>RR: ${currV.respiratory_rate || '-'}</p>
            <p>Temperature: ${currV.temperature || '-'}°C</p>
            <p>SpO2: ${currV.spo2 || '-'}%</p>
            <p>GCS: ${currV.gcs || '-'}</p>
            <p>Pain: ${currV.pain_scale || '-'}</p>
        `;
        vitalChangesHtml = `<h2>VITAL CHANGES</h2>` + vitalChangesHtml;
    }

    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <title>PatientTriage_Handoff_${p.name.replace(/\s+/g, '_')}_${p.id}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { font-size: 24px; margin-bottom: 5px; }
        h2 { font-size: 18px; color: #555; border-bottom: 1px solid #000; padding-bottom: 5px; margin-top: 30px; }
        p { margin: 5px 0; }
        ul { margin: 5px 0; padding-left: 20px; }
        .footer { margin-top: 50px; font-size: 12px; color: #777; border-top: 1px solid #ccc; padding-top: 10px; text-align: center; }
        @media print {
            body { font-size: 12pt; }
            button { display: none; }
        }
    </style>
</head>
<body>
    <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; margin-bottom: 20px; cursor: pointer;">🖨️ Print / Save as PDF</button>

    <h1>PATIENTTRIAGE.AI</h1>
    <p><strong>TRIAGE / HANDOFF SUMMARY</strong></p>
    
    <h2>PATIENT INFORMATION</h2>
    <p><strong>Patient:</strong> ${p.name}</p>
    <p><strong>Patient ID:</strong> ${p.id}</p>
    <p><strong>Age:</strong> ${p.age}</p>
    <p><strong>Gender:</strong> ${p.gender}</p>
    <p><strong>Arrival Mode:</strong> ${p.arrival_mode || 'Walk-in'}</p>

    <h2>CHIEF COMPLAINT</h2>
    <p>${p.chief_complaint}</p>

    <h2>FINAL TRIAGE</h2>
    <p><strong>Final Priority:</strong> ${tr.priority}</p>
    <p><strong>Rules Assessment:</strong> ${tr.rules_priority}</p>
    <p><strong>ML Recommendation:</strong> ${tr.ml_priority || 'N/A'}</p>
    <p><strong>Decision Source:</strong> ${tr.source}</p>

    <h2>INITIAL VITALS</h2>
    <p>HR: ${initV.heart_rate || '-'}</p>
    <p>BP: ${initV.blood_pressure || (initV.systolic_bp ? initV.systolic_bp + '/' + (initV.diastolic_bp||'') : '-')}</p>
    <p>RR: ${initV.respiratory_rate || '-'}</p>
    <p>Temperature: ${initV.temperature || '-'}°C</p>
    <p>SpO2: ${initV.spo2 || '-'}%</p>
    <p>GCS: ${initV.gcs || '-'}</p>
    <p>Pain: ${initV.pain_scale || '-'}</p>

    ${latestVitalsHtml}
    ${vitalChangesHtml}

    <h2>TRIAGE FACTORS</h2>
    <ul>${tr.reasons.map(r => `<li>${r}</li>`).join('')}</ul>

    <h2>QUEUE HISTORY</h2>
    <p><strong>Arrival:</strong> ${arrivalTime}</p>
    <p><strong>Initial Triage:</strong> ${arrivalTime}</p>
    <p><strong>Completed:</strong> ${completedTime}</p>
    <p><strong>Total Wait:</strong> ${waitTimeMins} mins</p>

    <h2>IMPORTANT EVENTS</h2>
    ${auditHtml}

    <div class="footer">
        PatientTriage.ai<br>
        AI-assisted triage / queue management<br>
        For clinical review
    </div>
</body>
</html>
    `;

    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `PatientTriage_Handoff_\${p.name.replace(/\\s+/g, '_')}_\${p.id}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

document.addEventListener('click', () => { 
    document.querySelectorAll('.dropdown-content').forEach(el => el.style.display = 'none'); 
});
