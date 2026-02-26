import os
import requests
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from dotenv import load_dotenv

from auth import RedHatAuth
from openshift_report import OpenShiftReportManager
from openshift_optimization import OpenShiftOptimizationManager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_super_secret_key")

# ==========================================
# ROTAS DA APLICAÇÃO
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
                # Agora chamamos o arquivo .html direto da pasta templates
                return render_template('login.html', error="Authentication failed. Please check your credentials.")
                
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'client_id' not in session or 'client_secret' not in session:
        return redirect(url_for('login'))
    # O Flask procura automaticamente o arquivo 'dashboard.html' dentro da pasta 'templates'
    return render_template('dashboard.html')

@app.route('/api/openshift-costs', methods=['GET'])
def api_openshift_costs():
    if 'client_id' not in session: 
        return jsonify({"error": "Not authenticated"}), 401
    try:
        report_manager, _ = get_managers()
        return jsonify(report_manager.get_costs()), 200
    except Exception as e:
        return jsonify({"error": "Failed to load costs.", "details": str(e)}), 500

@app.route('/api/openshift-optimization', methods=['GET'])
def api_openshift_optimization():
    if 'client_id' not in session: 
        return jsonify({"error": "Not authenticated"}), 401
    try:
        _, optimization_manager = get_managers()
        return jsonify(optimization_manager.get_optimizations()), 200
    except Exception as e:
        return jsonify({"error": "Failed to load optimizations.", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

