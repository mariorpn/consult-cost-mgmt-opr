import requests

class OpenShiftReportManager:
    def __init__(self, auth_object):
        self.auth = auth_object
        self.base_url = "https://console.redhat.com/api/cost-management/v1/"

    def get_costs(self):
        token = self.auth.get_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        
        all_data = []
        # Parâmetro limit=100 para trazer mais dados por página
        endpoint = f"{self.base_url}reports/openshift/costs/?limit=100"
        
        while endpoint:
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            json_data = response.json()
            
            if "data" in json_data:
                all_data.extend(json_data["data"])
            
            # Busca a próxima página
            next_link = json_data.get("links", {}).get("next")
            if next_link:
                if next_link.startswith("http"):
                    endpoint = next_link
                else:
                    endpoint = f"https://console.redhat.com{next_link}"
            else:
                endpoint = None
                
        return {"data": all_data}

