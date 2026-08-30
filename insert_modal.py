import re

with open('frontend/index.html', 'r') as f:
    html = f.read()

modal_html = """
    <!-- UPDATE PATIENT MODAL -->
    <div id="update-patient-modal" class="modal">
        <div class="modal-content">
            <span class="close-btn" data-modal="update-patient-modal">&times;</span>
            <h2>Update Patient Details</h2>
            <form id="update-patient-form">
                <input type="hidden" id="up-patient-id">
                <div class="form-group">
                    <label>Chief Complaint</label>
                    <input type="text" id="up-complaint">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Arrival Mode</label>
                        <select id="up-arrival">
                            <option value="">-- No Change --</option>
                            <option value="walk-in">Walk-in</option>
                            <option value="ambulance">Ambulance</option>
                            <option value="helicopter">Helicopter</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>History Available</label>
                        <select id="up-history">
                            <option value="">-- No Change --</option>
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Medical History (comma-separated)</label>
                    <input type="text" id="up-med-history">
                </div>
                <div class="form-group">
                    <label>Observed Signs (comma-separated)</label>
                    <input type="text" id="up-signs">
                </div>
                <button type="submit" class="btn-primary" style="width:100%;margin-top:15px;">Update Patient</button>
            </form>
        </div>
    </div>
"""

new_html = html.replace('<script src="app.js"></script>', modal_html + '\n    <script src="app.js"></script>')

with open('frontend/index.html', 'w') as f:
    f.write(new_html)

