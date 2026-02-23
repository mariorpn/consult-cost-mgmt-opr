import os
import requests
from flask import Flask, jsonify, render_template_string, request, redirect, url_for, session
from dotenv import load_dotenv

from auth import RedHatAuth
from openshift_report import OpenShiftReportManager
from openshift_optimization import OpenShiftOptimizationManager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_super_secret_key")

# ==========================================
# HTML TEMPLATES
# ==========================================

TEMPLATE_LOGIN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login - Red Hat Cost Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .login-card { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 450px; }
        .brand { color: #cc0000; font-weight: bold; font-size: 24px; text-align: center; margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="brand">Red Hat<br>Cost Management</div>
        {% if error %}
        <div class="alert alert-danger" role="alert">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <div class="mb-3">
                <label class="form-label fw-bold">Client ID</label>
                <input type="text" name="client_id" class="form-control" required>
            </div>
            <div class="mb-4">
                <label class="form-label fw-bold">Client Secret</label>
                <input type="password" name="client_secret" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-danger w-100 fw-bold py-2">Login</button>
        </form>
    </div>
</body>
</html>
"""

TEMPLATE_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Red Hat Dashboard - OpenShift</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding-top: 20px; }
        .navbar-brand { font-weight: bold; color: #cc0000 !important; }
        .table-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px; overflow-x: auto; }
        .code-block { background-color: #f4f4f4; border: 1px solid #e9ecef; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5; }
        .cost-val { color: #198754; font-weight: bold; font-size: 14px;}
    </style>
</head>
<body>
    <div class="container-fluid px-4">
        <nav class="navbar navbar-light bg-light mb-4 rounded px-3 shadow-sm d-flex justify-content-between">
            <span class="navbar-brand mb-0 h1">Red Hat Cost Management</span>
            <a href="/logout" class="btn btn-outline-danger btn-sm fw-bold">Logout</a>
        </nav>

        <div class="row mb-3">
            <div class="col-md-6">
                <button class="btn btn-primary w-100" onclick="loadData('/api/openshift-costs', 'costResult')">
                    📊 Load Cost Report
                </button>
            </div>
            <div class="col-md-6">
                <button class="btn btn-success w-100" onclick="loadData('/api/openshift-optimization', 'optimizationResult')">
                    ⚡ Load Resource Optimization
                </button>
            </div>
        </div>

        <div id="optimizationControls" class="row mb-3 p-3 bg-white rounded shadow-sm border mx-0" style="display: none;">
            <h5 class="mb-3 text-success">⚙️ Optimization Parameters</h5>
            <div class="col-md-6">
                <label class="form-label fw-bold">Analysis Period</label>
                <select id="selectTerm" class="form-select border-success" onchange="reapplyOptimizationFilters()">
                    <option value="long_term" selected>Last 15 days (Long Term)</option>
                    <option value="medium_term">Last 7 days (Medium Term)</option>
                    <option value="short_term">Last 24 hours (Short Term)</option>
                </select>
            </div>
            <div class="col-md-6">
                <label class="form-label fw-bold">Recommendation Focus</label>
                <select id="selectEngine" class="form-select border-success" onchange="reapplyOptimizationFilters()">
                    <option value="cost" selected>Cost</option>
                    <option value="performance">Performance</option>
                </select>
            </div>
        </div>

        <div class="row mb-3" id="filterArea" style="display: none;">
            <div class="col-md-9 mb-2 mb-md-0">
                <input type="text" id="inputFilter" class="form-control border-secondary" placeholder="🔍 Type to filter projects, clusters, or values..." onkeyup="filterTable()">
            </div>
            <div class="col-md-3">
                <button class="btn btn-dark w-100" onclick="exportCSV()">
                    📥 Export to CSV
                </button>
            </div>
        </div>

        <div class="row">
            <div class="col-12" id="costResult" style="display: none;">
                <div class="table-container">
                    <h4 class="mb-3 text-primary">Cost Report</h4>
                    <div class="content"></div>
                </div>
            </div>
            <div class="col-12" id="optimizationResult" style="display: none;">
                <div class="table-container">
                    <h4 class="mb-3 text-success">Resource Optimization</h4>
                    <div class="content"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentReportType = '';
        let globalLoadedData = [];

        async function loadData(endpoint, divId) {
            document.getElementById('costResult').style.display = 'none';
            document.getElementById('optimizationResult').style.display = 'none';
            document.getElementById('inputFilter').value = '';
            document.getElementById('filterArea').style.display = 'none';
            
            currentReportType = endpoint.includes('costs') ? 'openshift_costs' : 'openshift_optimization';
            document.getElementById('optimizationControls').style.display = (currentReportType === 'openshift_optimization') ? 'flex' : 'none';

            const container = document.getElementById(divId);
            const content = container.querySelector('.content');
            container.style.display = 'block';
            content.innerHTML = '<div class="spinner-border text-secondary" role="status"></div> Fetching all pages from Red Hat. This might take a few seconds...';

            try {
                const response = await fetch(endpoint);
                const json = await response.json();

                if (!response.ok) {
                    if (response.status === 401) window.location.href = '/login';
                    content.innerHTML = `<div class="alert alert-danger">Error: ${json.error || 'Failed'}</div>`;
                    return;
                }

                globalLoadedData = json.data; 

                if (globalLoadedData && Array.isArray(globalLoadedData) && globalLoadedData.length > 0) {
                    content.innerHTML = generateTable(globalLoadedData, divId);
                    document.getElementById('filterArea').style.display = 'flex';
                } else {
                    content.innerHTML = `<div class="alert alert-warning">No data found.</div>`;
                }
            } catch (error) {
                content.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
            }
        }

        function reapplyOptimizationFilters() {
            if (globalLoadedData.length > 0) {
                const content = document.querySelector('#optimizationResult .content');
                content.innerHTML = generateTable(globalLoadedData, 'optimizationResult');
                filterTable(); 
            }
        }

        function formatCostValues(rawVal) {
            try {
                let vals = Array.isArray(rawVal) ? rawVal : [rawVal];
                if (vals.length === 0) return { html: '', flat: '' };

                let html = `<pre class="code-block">`;
                let flatLines = [];

                vals.forEach(v => {
                    let label = v.project || v.cluster || v.node || v.date || '';
                    let costTotal = v.cost?.total || v.cost?.raw?.total || {};
                    let val = costTotal.value !== undefined ? costTotal.value : 0;
                    let unit = costTotal.units || 'USD';

                    if (!isNaN(val)) val = Number(val).toFixed(4);

                    if (label) {
                        html += `[${label}]\\n  cost: <span class="cost-val">${val} ${unit}</span>\\n`;
                        flatLines.push(`[${label}] ${val} ${unit}`);
                    } else {
                        html += `cost: <span class="cost-val">${val} ${unit}</span>\\n`;
                        flatLines.push(`${val} ${unit}`);
                    }
                });
                
                html += `</pre>`;
                return { html: html, flat: flatLines.join(" | ") };
            } catch (e) {
                return { html: `<pre class="code-block" style="font-size: 11px;">${JSON.stringify(rawVal, null, 2)}</pre>`, flat: JSON.stringify(rawVal) };
            }
        }

        function formatRecommendation(rawVal) {
            let flatData = { 
                lim_cpu: '-', lim_cpu_var: '-', lim_mem: '-', lim_mem_var: '-', 
                req_cpu: '-', req_cpu_var: '-', req_mem: '-', req_mem_var: '-' 
            };

            try {
                let rec = Array.isArray(rawVal) ? rawVal[0] : rawVal;
                if (!rec || !rec.recommendation_terms) {
                    return { html: `<pre class="code-block" style="font-size: 11px;">No structured data</pre>`, flat: flatData };
                }

                let selectTerm = document.getElementById('selectTerm') ? document.getElementById('selectTerm').value : 'long_term';
                let selectEngine = document.getElementById('selectEngine') ? document.getElementById('selectEngine').value : 'cost';

                let recTerms = rec.recommendation_terms || {};
                let termData = recTerms[selectTerm] || {};
                let engines = termData.recommendation_engines || {};
                let engine = engines[selectEngine] || {};
                let config = engine.config || {};
                let variation = engine.variation || {};

                if (Object.keys(config).length === 0) {
                    return { html: `<pre class="code-block" style="font-size: 11px; color:#666;">No recommendation available for [${selectEngine}] in [${selectTerm}].</pre>`, flat: flatData };
                }

                const formatLine = (objConfig, objVar, type, flagFlat) => {
                    let valStr = '-';
                    let varStr = '-';

                    if (objConfig && objConfig[type] !== undefined && objConfig[type] !== null) {
                        let item = objConfig[type];
                        let val = item.amount !== undefined ? item.amount : item;
                        let fmt = item.format || "";
                        
                        if (typeof val === 'object' || val === '') {
                            valStr = '-';
                        } else {
                            if (fmt === "bytes") {
                                val = (Number(val) / 1048576).toFixed(2);
                                fmt = "Mi";
                            } else if (!isNaN(val)) { val = Number(val).toFixed(3); }
                            
                            valStr = `${val}${fmt}`;
                        }
                    }
                    
                    if (objVar && objVar[type] !== undefined && objVar[type] !== null) {
                        let vItem = objVar[type];
                        let vVal = vItem.amount !== undefined ? vItem.amount : vItem;
                        let vFmt = vItem.format || "%";
                        
                        if (typeof vVal === 'object' || vVal === '') {
                            varStr = '-';
                        } else {
                            vFmt = vFmt.replace(/percente?/gi, '%');
                            if (!isNaN(vVal)) vVal = Number(vVal).toFixed(0);
                            varStr = `${vVal}${vFmt}`;
                        }
                    }

                    if(flagFlat === 'limit_cpu') { flatData.lim_cpu = valStr; flatData.lim_cpu_var = varStr; }
                    if(flagFlat === 'limit_mem') { flatData.lim_mem = valStr; flatData.lim_mem_var = varStr; }
                    if(flagFlat === 'req_cpu') { flatData.req_cpu = valStr; flatData.req_cpu_var = varStr; }
                    if(flagFlat === 'req_mem') { flatData.req_mem = valStr; flatData.req_mem_var = varStr; }

                    return `  ${type}: ${valStr.padEnd(12)} # ${varStr}\\n`;
                };

                let html = `<pre class="code-block">`;
                
                if (config.limits) {
                    html += `limits:\\n`;
                    html += formatLine(config.limits, variation.limits, 'cpu', 'limit_cpu');
                    html += formatLine(config.limits, variation.limits, 'memory', 'limit_mem');
                }
                if (config.requests) {
                    html += `requests:\\n`;
                    html += formatLine(config.requests, variation.requests, 'cpu', 'req_cpu');
                    html += formatLine(config.requests, variation.requests, 'memory', 'req_mem');
                }
                html += `</pre>`;
                
                return { html: html, flat: flatData };
            } catch (e) {
                return { html: `<pre class="code-block" style="font-size: 11px;">Format error</pre>`, flat: flatData };
            }
        }

        function generateTable(objectList, tableId) {
            let keys = Object.keys(objectList[0]);
            let html = `<table id="table-${tableId}" class="table table-striped table-bordered table-hover table-sm text-start align-middle">`;
            html += '<thead class="table-dark"><tr>';
            keys.forEach(key => { html += `<th>${key.toUpperCase()}</th>`; });
            html += '</tr></thead><tbody>';

            objectList.forEach(obj => {
                html += '<tr>';
                keys.forEach(key => {
                    let val = obj[key];
                    let k = key.toLowerCase();
                    
                    if (k.includes('recommendation')) {
                        let result = formatRecommendation(val);
                        html += `<td 
                            data-is-rec="true"
                            data-lc="${result.flat.lim_cpu}" data-lcv="${result.flat.lim_cpu_var}"
                            data-lm="${result.flat.lim_mem}" data-lmv="${result.flat.lim_mem_var}"
                            data-rc="${result.flat.req_cpu}" data-rcv="${result.flat.req_cpu_var}"
                            data-rm="${result.flat.req_mem}" data-rmv="${result.flat.req_mem_var}"
                        >${result.html}</td>`;
                        
                    } else if (k === 'values' && currentReportType === 'openshift_costs') {
                        let resultCost = formatCostValues(val);
                        html += `<td data-is-cost-value="true" data-flat-cost="${resultCost.flat}">${resultCost.html}</td>`;
                        
                    } else {
                        if (typeof val === 'object' && val !== null) {
                            val = `<pre class="code-block" style="font-size: 11px; padding: 5px;">${JSON.stringify(val, null, 2)}</pre>`;
                        }
                        html += `<td>${val}</td>`;
                    }
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            return html;
        }

        function filterTable() {
            let input = document.getElementById("inputFilter");
            let filter = input.value.toLowerCase();
            let activeTable = document.querySelector("table[id^='table-']:not([style*='display: none'])");
            if (!activeTable) return;
            let trs = activeTable.getElementsByTagName("tr");
            for (let i = 1; i < trs.length; i++) {
                let tds = trs[i].getElementsByTagName("td");
                let textContent = "";
                for (let j = 0; j < tds.length; j++) { textContent += tds[j].textContent || tds[j].innerText; }
                if (textContent.toLowerCase().indexOf(filter) > -1) {
                    trs[i].style.display = "";
                } else { trs[i].style.display = "none"; }
            }
        }

        function exportCSV() {
            let activeTable = document.querySelector(".table-container table");
            if (!activeTable) return;
            
            let csv = [];
            let rows = activeTable.querySelectorAll("tr");
            let headers = [];
            let ths = rows[0].querySelectorAll("th");
            let recommendationIndex = -1;

            for (let j = 0; j < ths.length; j++) {
                if (ths[j].innerText.toUpperCase().includes('RECOMMENDATION')) {
                    recommendationIndex = j;
                    headers.push('"limits.cpu"','"limits.cpu (%)"','"limits.memory"','"limits.memory (%)"','"requests.cpu"','"requests.cpu (%)"','"requests.memory"','"requests.memory (%)"');
                } else {
                    headers.push('"' + ths[j].innerText.replace(/"/g, '""') + '"');
                }
            }
            csv.push(headers.join(","));

            for (let i = 1; i < rows.length; i++) {
                if (rows[i].style.display === "none") continue; 
                
                let rowData = [];
                let cols = rows[i].querySelectorAll("td");
                
                for (let j = 0; j < cols.length; j++) {
                    if (j === recommendationIndex && cols[j].getAttribute("data-is-rec") === "true") {
                        rowData.push('"' + (cols[j].getAttribute("data-lc") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-lcv") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-lm") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-lmv") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-rc") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-rcv") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-rm") || '') + '"');
                        rowData.push('"' + (cols[j].getAttribute("data-rmv") || '') + '"');
                        
                    } else if (cols[j].getAttribute("data-is-cost-value") === "true") {
                        rowData.push('"' + (cols[j].getAttribute("data-flat-cost") || '').replace(/"/g, '""') + '"');
                        
                    } else {
                        rowData.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
                    }
                }
                csv.push(rowData.join(","));
            }

            let universalBOM = "\\uFEFF";
            let csvString = csv.join("\\n");
            let blob = new Blob([universalBOM + csvString], { type: 'text/csv;charset=utf-8;' });
            let link = document.createElement("a");
            
            let filterName = "";
            if (currentReportType === 'openshift_optimization') {
                let sTerm = document.getElementById('selectTerm').value;
                let sEng = document.getElementById('selectEngine').value;
                filterName = `_${sTerm}_${sEng}`;
            }

            let today = new Date().toISOString().split('T')[0];
            link.download = `${currentReportType}${filterName}_${today}.csv`;
            
            link.href = URL.createObjectURL(blob);
            link.style.display = "none";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    </script>
</body>
</html>
"""

# ==========================================
# APP ROUTES
# ==========================================

def get_managers():
    client_id = session.get('client_id')
    client_secret = session.get('client_secret')
    auth_manager = RedHatAuth(client_id, client_secret)
    report_manager = OpenShiftReportManager(auth_manager)
    optimization_manager = OpenShiftOptimizationManager(auth_manager)
    return report_manager, optimization_manager

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client_id = request.form.get('client_id', '').strip()
        client_secret = request.form.get('client_secret', '').strip()
        if client_id and client_secret:
            try:
                temp_auth = RedHatAuth(client_id, client_secret)
                temp_auth.get_token()
                session['client_id'] = client_id
                session['client_secret'] = client_secret
                return redirect(url_for('index'))
            except Exception as e:
                return render_template_string(TEMPLATE_LOGIN, error="Authentication failed. Please check your credentials.")
    return render_template_string(TEMPLATE_LOGIN, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'client_id' not in session or 'client_secret' not in session:
        return redirect(url_for('login'))
    return render_template_string(TEMPLATE_DASHBOARD)

@app.route('/api/openshift-costs', methods=['GET'])
def api_openshift_costs():
    if 'client_id' not in session: return jsonify({"error": "Not authenticated"}), 401
    try:
        report_manager, _ = get_managers()
        return jsonify(report_manager.get_costs()), 200
    except Exception as e:
        return jsonify({"error": "Failed to load costs.", "details": str(e)}), 500

@app.route('/api/openshift-optimization', methods=['GET'])
def api_openshift_optimization():
    if 'client_id' not in session: return jsonify({"error": "Not authenticated"}), 401
    try:
        _, optimization_manager = get_managers()
        return jsonify(optimization_manager.get_optimizations()), 200
    except Exception as e:
        return jsonify({"error": "Failed to load optimizations.", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)


