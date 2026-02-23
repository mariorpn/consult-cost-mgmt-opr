import requests

class OpenShiftOptimizationManager:
    def __init__(self, auth_object):

        self.auth = auth_object
        self.base_url = "https://console.redhat.com/api/cost-management/v1/"

    def get_optimizations(self):

        token = self.auth.get_token()
        endpoint = f"{self.base_url}recommendations/openshift"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        response = requests.get(endpoint, headers=headers, timeout=15)
        response.raise_for_status()
        
        return response.json()
