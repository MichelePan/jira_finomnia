import requests
from requests.auth import HTTPBasicAuth

HEADERS_JSON = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

HEADERS_GET = {
    "Accept": "application/json",
}

class JiraClient:
    def __init__(self, domain: str, email: str, api_token: str):
        self.domain = domain
        self.email = email
        self.api_token = api_token
        self.base_url = f"https://{domain}/rest/api/3"
        self.auth = HTTPBasicAuth(email, api_token)

    def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"

        response = requests.get(
            url,
            params=params,
            headers=HEADERS_GET,
            auth=self.auth,
            timeout=60,
        )

        if not response.ok:
            raise RuntimeError(
                f"Errore Jira GET {path}: {response.status_code} - {response.text}"
            )

        return response.json()

    def _post(self, path: str, payload: dict):
        url = f"{self.base_url}{path}"

        response = requests.post(
            url,
            json=payload,
            headers=HEADERS_JSON,
            auth=self.auth,
            timeout=60,
        )

        if not response.ok:
            raise RuntimeError(
                f"Errore Jira POST {path}: {response.status_code} - {response.text}"
            )

        return response.json()

    def get_fields(self):
        return self._get("/field")

    def detect_epic_link_field(self):
        """
        Alcune istanze Jira usano ancora il campo custom 'Epic Link'.
        Nei progetti più recenti spesso basta usare il campo 'parent'.
        """
        try:
            fields = self.get_fields()
        except Exception:
            return None

        for field in fields:
            name = (field.get("name") or "").lower()
            if name == "epic link":
                return field.get("id")

        return None

    def detect_sprint_field(self):
        """
        Nei progetti Jira Software lo Sprint è spesso un custom field.
        Questo metodo prova a individuarlo.
        """
        try:
            fields = self.get_fields()
        except Exception:
            return None

        for field in fields:
            name = (field.get("name") or "").lower()
            if name == "sprint":
                return field.get("id")

        return None

    def search_issues_jql(self, jql: str, fields: list[str]):
        """
        Usa l'endpoint /search/jql con nextPageToken.
        """
        issues = []
        next_page_token = None

        while True:
            payload = {
                "jql": jql,
                "fields": fields,
            }

            if next_page_token:
                payload["nextPageToken"] = next_page_token

            data = self._post("/search/jql", payload)

            issues.extend(data.get("issues", []))

            next_page_token = data.get("nextPageToken")

            if not next_page_token:
                break

        return issues
