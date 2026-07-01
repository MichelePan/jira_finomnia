import streamlit as st

from auth import login_required, render_logout
from jira_client import JiraClient
from data_processing import (
 build_issues_dataframe,
 add_issue_urls,
 apply_filters,
 create_excel_export,
)
from ui_components import (
 render_kpis,
 render_status_panel,
 render_status_category_panel,
 render_epic_panel,
 render_assignee_panel,
 render_priority_panel,
 render_age_panel,
 render_detail_table,
)

# ======================
# STREAMLIT CONFIG
# ======================

st.set_page_config(
 page_title="Jira Project Dashboard",
 page_icon="📊",
 layout="wide",
)

# ======================
# LOGIN
# ======================

login_required()

# ======================
# PAGE HEADER
# ======================

st.title("📊 Jira Project Dashboard")
st.caption("Dashboard di monitoraggio avanzamento progetto basata su issue Jira")

# ======================
# CONFIG
# ======================

def get_secret(section: str, key: str, default=None):
 try:
 return st.secrets[section][key]
 except Exception:
 return default

jira_domain = get_secret("JIRA", "DOMAIN")
jira_email = get_secret("JIRA", "EMAIL")
jira_api_token = get_secret("JIRA", "API_TOKEN")
default_jql = get_secret(
 "JIRA",
 "DEFAULT_JQL",
 "project is not EMPTY ORDER BY updated DESC",
)

if not jira_domain or not jira_email or not jira_api_token:
 st.error(
 """
 Configurazione Jira mancante.

 Imposta i seguenti valori nei secrets di Streamlit:

 ```toml
 [JIRA]
 DOMAIN = "your-domain.atlassian.net"
 EMAIL = "your.email@reply.it"
 API_TOKEN = "your-api-token"
 DEFAULT_JQL = "project = KAN ORDER BY updated DESC"
