import streamlit as st

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
    render_alerts_panel,
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
        ```
        """
    )
    st.stop()

# ======================
# SIDEBAR
# ======================

st.sidebar.header("Configurazione")

jql = st.sidebar.text_area(
    "JQL perimetro progetto",
    value=default_jql,
    height=120,
    help="Esempio: project = KAN AND issuetype != Epic ORDER BY updated DESC",
)

exclude_done_from_alerts = st.sidebar.checkbox(
    "Considera solo task aperti negli alert",
    value=True,
)

stale_days = st.sidebar.slider(
    "Task fermo se non aggiornato da almeno N giorni",
    min_value=1,
    max_value=60,
    value=7,
)

st.session_state["stale_days"] = stale_days

refresh = st.sidebar.button("Aggiorna dati")

# ======================
# CACHE
# ======================

@st.cache_data(ttl=24 * 60 * 60)
def cached_detect_epic_link_field(domain, email, token):
    client = JiraClient(domain, email, token)
    return client.detect_epic_link_field()

@st.cache_data(ttl=24 * 60 * 60)
def cached_detect_sprint_field(domain, email, token):
    client = JiraClient(domain, email, token)
    return client.detect_sprint_field()

@st.cache_data(ttl=30 * 60)
def cached_search_issues(
    domain,
    email,
    token,
    jql_query,
    epic_link_field_id,
    sprint_field_id,
):
    client = JiraClient(domain, email, token)

    fields = [
        "summary",
        "issuetype",
        "status",
        "assignee",
        "reporter",
        "priority",
        "parent",
        "created",
        "updated",
        "duedate",
        "resolutiondate",
    ]

    if epic_link_field_id:
        fields.append(epic_link_field_id)

    if sprint_field_id:
        fields.append(sprint_field_id)

    return client.search_issues_jql(jql_query, fields)

if refresh:
    st.cache_data.clear()
    st.rerun()

# ======================
# LOAD DATA
# ======================

try:
    with st.spinner("Rilevamento campi Jira..."):
        epic_link_field_id = cached_detect_epic_link_field(
            jira_domain,
            jira_email,
            jira_api_token,
        )

        sprint_field_id = cached_detect_sprint_field(
            jira_domain,
            jira_email,
            jira_api_token,
        )

    with st.spinner("Caricamento issue Jira..."):
        issues = cached_search_issues(
            jira_domain,
            jira_email,
            jira_api_token,
            jql,
            epic_link_field_id,
            sprint_field_id,
        )

except Exception as exc:
    st.error("Errore durante il caricamento dati da Jira.")
    st.exception(exc)
    st.stop()

# ======================
# DEBUG SIDEBAR
# ======================

st.sidebar.divider()
st.sidebar.subheader("Debug")

st.sidebar.write("JQL effettivo:")
st.sidebar.code(jql)

st.sidebar.write("Issue recuperate da Jira:")
st.sidebar.write(len(issues))

if issues:
    st.sidebar.write("Prime issue:")
    st.sidebar.write([issue.get("key") for issue in issues[:10]])

# ======================
# EMPTY STATE
# ======================

if not issues:
    st.info("Nessuna issue trovata per il JQL indicato.")
    st.stop()

df = build_issues_dataframe(
    issues,
    epic_link_field_id=epic_link_field_id,
    sprint_field_id=sprint_field_id,
)

df = add_issue_urls(df, jira_domain)

if df.empty:
    st.info("Nessun dato disponibile.")
    st.stop()

# ======================
# FILTRI
# ======================

st.sidebar.header("Filtri dashboard")

only_open = st.sidebar.checkbox(
    "Mostra solo task aperti",
    value=False,
    key="filter_only_open",
)

status_options = sorted(df["Stato"].dropna().unique())

selected_statuses = st.sidebar.multiselect(
    "Stato",
    options=status_options,
    default=[],
    key="filter_statuses",
)

issue_type_options = sorted(df["IssueType"].dropna().unique())

selected_issue_types = st.sidebar.multiselect(
    "Issue Type",
    options=issue_type_options,
    default=[],
    key="filter_issue_types",
)

priority_options = sorted(
    df["Priority"]
    .fillna("")
    .replace("", "Nessuna priorità")
    .unique()
)

selected_priorities_ui = st.sidebar.multiselect(
    "Priorità",
    options=priority_options,
    default=[],
    key="filter_priorities",
)

selected_priorities = [
    "" if priority == "Nessuna priorità" else priority
    for priority in selected_priorities_ui
]

assignee_options = sorted(
    df["Assignee"]
    .fillna("")
    .replace("", "Non assegnato")
    .unique()
)

selected_assignees_ui = st.sidebar.multiselect(
    "Assegnatario",
    options=assignee_options,
    default=[],
    key="filter_assignees",
)

selected_assignees = [
    "" if assignee == "Non assegnato" else assignee
    for assignee in selected_assignees_ui
]

epic_df = df.copy()
epic_df["EpicFilter"] = epic_df["EpicName"]

epic_df.loc[
    epic_df["EpicFilter"].fillna("").str.strip() == "",
    "EpicFilter",
] = epic_df["EpicKey"]

epic_df.loc[
    epic_df["EpicFilter"].fillna("").str.strip() == "",
    "EpicFilter",
] = "Senza Epic"

epic_options = sorted(epic_df["EpicFilter"].dropna().unique())

selected_epics_ui = st.sidebar.multiselect(
    "Epic",
    options=epic_options,
    default=[],
    key="filter_epics",
)

selected_epics = [
    "" if epic == "Senza Epic" else epic
    for epic in selected_epics_ui
]

sprint_options = sorted(
    df["Sprint"]
    .fillna("")
    .replace("", "Nessuno Sprint")
    .unique()
)

selected_sprints_ui = st.sidebar.multiselect(
    "Sprint",
    options=sprint_options,
    default=[],
    key="filter_sprints",
)

selected_sprints = [
    "" if sprint == "Nessuno Sprint" else sprint
    for sprint in selected_sprints_ui
]

df_view = apply_filters(
    df,
    statuses=selected_statuses,
    issue_types=selected_issue_types,
    assignees=selected_assignees,
    priorities=selected_priorities,
    epics=selected_epics,
    sprints=selected_sprints,
    only_open=only_open,
)

# ======================
# DASHBOARD
# ======================

st.divider()

render_kpis(df_view)

st.divider()

tab_overview, tab_flow, tab_epic, tab_people, tab_alerts, tab_details = st.tabs(
    [
        "Overview",
        "Stati e priorità",
        "Epic",
        "Persone",
        "Alert",
        "Dettaglio",
    ]
)

with tab_overview:
    render_status_panel(df_view, key_suffix="overview")

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        render_status_category_panel(df_view, key_suffix="overview")

    with col2:
        render_age_panel(df_view, key_suffix="overview")

with tab_flow:
    render_status_panel(df_view, key_suffix="flow")

    st.divider()

    render_priority_panel(df_view, key_suffix="flow")

with tab_epic:
    render_epic_panel(df_view, key_suffix="epic")

with tab_people:
    render_assignee_panel(df_view, key_suffix="people")

with tab_alerts:
    alert_df = df_view.copy()

    if exclude_done_from_alerts:
        alert_df = alert_df[alert_df["Done"] == False]

    render_alerts_panel(
        alert_df,
        stale_days,
        key_suffix="alerts",
    )

with tab_details:
    render_detail_table(df_view, key_suffix="details")

    excel_file = create_excel_export(df_view)

    st.download_button(
        label="📥 Scarica Excel",
        data=excel_file,
        file_name="jira_project_dashboard.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_excel_details",
    )
