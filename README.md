# consult-cost-mgmt-opr
App to consult API of Cost Management Operator - Red Hat


# 📊 Red Hat Cost Management - OpenShift Dashboard

A modular web application built with **Python (Flask)** and **Vanilla JavaScript** to fetch, visualize, and export data from the Red Hat Cost Management REST API, focusing on OpenShift clusters.

...

## 🚀 Features

* **Modular Architecture:** The codebase is split into specific modules (`auth`, `report`, `optimization`) for better maintainability and scalability.
* **Security by Design:** Dynamic OAuth2 (Client Credentials) authentication via the web UI. No hardcoded credentials. Sessions are securely encrypted using Flask.
* **Smart Visualization:** Automatically parses massive JSON payloads. Custom visual formatting for nested Recommendation data (Limits & Requests) and Cost Values.
* **Dynamic Pagination:** Automatically handles API pagination to fetch all datasets (thousands of entries) seamlessly in the background.
* **Real-time Filtering:** Features an instant search bar to filter projects or clusters dynamically in the DOM.
* **Interactive Toggles:** Switch between analysis periods (`Long Term`, `Medium Term`, `Short Term`) and focuses (`Cost`, `Performance`) without triggering new API requests.
* **CSV Export:** Extracts and flattens nested data into a clean, UTF-8 formatted `.csv` file perfectly ready for Excel pivots and charting.

...

## 📂 Project Structure

```text
cost-management-app/
│
├── .env                         # Environment file for Flask security (DO NOT COMMIT)
├── app.py                       # Main Flask orchestrator, routing, and UI templates
├── auth.py                      # Handles OAuth2 flow and token caching with Red Hat SSO
├── openshift_report.py          # Handles fetching data from the cost reports endpoint
├── openshift_optimization.py    # Handles fetching data from the resource optimization endpoint
├── requirements.txt             # Python dependencies list
└── README.md                    # Project documentation
```

### **app.py:** 
The entry point. Manages user sessions, serves the HTML dashboard (using Bootstrap), handles UI logic, and routes API requests to the respective managers.

### **auth.py:** 
Manages the client_id and client_secret, requests a Bearer token from Red Hat SSO, and caches it until it expires to save HTTP requests.

### **openshift_report.py** & **openshift_optimization.py:**
The API wrappers. They inject the Bearer token into headers and run while loops to fetch all paginated data from Red Hat's endpoints.

....

## 🛠️ Prerequisites
Python 3.8+ installed.

An active Red Hat Hybrid Cloud Console account.

A Red Hat Service Account with a valid Client ID and Client Secret.

...

## 📦 Installation & Setup
1. Clone or download the repository to your local machine.

2. Open your terminal in the project directory and create a virtual environment:

command:
```bash
python -m venv venv
```
3. **Activate the virtual environment:**
* Linux/macOS: source venv/bin/activate
* Windows: venv\Scripts\activate

4. **Install the dependencies:**

command:
```bash
pip install -r requirements.txt
```
5. **Security Configuration (The Flask Secret Key):**
This application uses Flask Sessions to temporarily store your Red Hat credentials while you navigate the dashboard. To prevent malicious users from tampering with these session cookies, Flask requires a cryptographic signature called a Secret Key.

**How to generate a strong key:**
Run the following command in your terminal to let Python generate a highly secure, random hex string:

command:
```bash
python -c "import secrets; print(secrets.token_hex(24))"
```
Create a file named .env in the root directory and paste the generated string inside it like this:

command:
```text
FLASK_SECRET_KEY=paste_your_generated_hex_string_here
```
**⚠️ CRITICAL:** Never commit the .env file to version control (like GitHub or GitLab). Keep it strictly local.

...

## 💻 Running the App

**Start the Flask server:**

command:
```bash
python3 app.py
```
**Open your web browser and navigate to:**

command:
```text
URL: http://127.0.0.1:5000
```

At the login screen, enter your Red Hat Service Account Client ID and Client Secret.
Once authenticated, use the dashboard buttons to fetch Costs or Optimization data, filter the tables, and export the findings to CSV.
