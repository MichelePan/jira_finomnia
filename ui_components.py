import pandas as pd
import plotly.express as px
import streamlit as st

def render_kpis(df: pd.DataFrame):
    if df.empty:
        st.info("Nessun dato disponibile per i filtri selezionati.")
        return

    total_tasks = len(df)
    done_tasks = int(df["Done"].sum())
    open_tasks = total_tasks - done_tasks

    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((done_tasks / total_tasks) * 100, 1)

    unassigned_tasks = int(
        (df["Assignee"].fillna("").str.strip() == "").sum()
    )

    stale_days = st.session_state.get("stale_days", 7)

    stale_tasks = int(
        (
            (df["Done"] == False)
            & (df["DaysSinceUpdate"].fillna(0) >= stale_days)
        ).sum()
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Task totali", total_tasks)
    c2.metric("Task aperti", open_tasks)
    c3.metric("Task completati", done_tasks)
    c4.metric("Avanzamento", f"{completion_rate}%")
    c5.metric("Task fermi", stale_tasks)

    c6, c7, c8, c9, c10 = st.columns(5)

    c6.metric(
        "Non assegnati",
        unassigned_tasks,
    )

    c7.metric(
        "Epic",
        df["EpicKey"].replace("", pd.NA).dropna().nunique(),
    )

    c8.metric(
        "Assignee",
        df["Assignee"].replace("", pd.NA).dropna().nunique(),
    )

    c9.metric(
        "Issue Type",
        df["IssueType"].replace("", pd.NA).dropna().nunique(),
    )

    c10.metric(
        "Priorità",
        df["Priority"].replace("", pd.NA).dropna().nunique(),
    )

def render_status_panel(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Task per stato")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    status_df = (
        df.groupby(["Stato", "StatusCategory"], dropna=False)
        .size()
        .reset_index(name="Task")
        .sort_values("Task", ascending=False)
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            status_df,
            x="Stato",
            y="Task",
            color="StatusCategory",
            text="Task",
            title="Distribuzione task per stato",
        )

        fig.update_layout(
            xaxis_title="Stato",
            yaxis_title="Numero task",
            legend_title="Categoria",
        )

        fig.update_traces(textposition="outside")

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"status_panel_chart_{key_suffix}",
        )

    with col2:
        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True,
            key=f"status_panel_table_{key_suffix}",
        )

def render_status_category_panel(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Categorie stato Jira")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    category_df = (
        df.groupby("StatusCategory", dropna=False)
        .size()
        .reset_index(name="Task")
        .sort_values("Task", ascending=False)
    )

    fig = px.pie(
        category_df,
        names="StatusCategory",
        values="Task",
        hole=0.45,
        title="Distribuzione per categoria Jira",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"status_category_chart_{key_suffix}",
    )

    st.dataframe(
        category_df,
        use_container_width=True,
        hide_index=True,
        key=f"status_category_table_{key_suffix}",
    )

def render_epic_panel(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Avanzamento per Epic")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    epic_df = df.copy()

    epic_df["Epic"] = epic_df["EpicName"]

    epic_df.loc[
        epic_df["Epic"].fillna("").str.strip() == "",
        "Epic",
    ] = epic_df["EpicKey"]

    epic_df.loc[
        epic_df["Epic"].fillna("").str.strip() == "",
        "Epic",
    ] = "Senza Epic"

    grouped = (
        epic_df.groupby("Epic", dropna=False)
        .agg(
            Task=("Issue", "count"),
            Completati=("Done", "sum"),
        )
        .reset_index()
    )

    grouped["Aperti"] = grouped["Task"] - grouped["Completati"]

    grouped["Avanzamento %"] = (
        grouped["Completati"] / grouped["Task"] * 100
    ).round(1)

    grouped = grouped.sort_values("Task", ascending=False)

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            grouped.head(20),
            x="Epic",
            y=["Aperti", "Completati"],
            title="Task aperti/completati per Epic",
            barmode="stack",
        )

        fig.update_layout(
            xaxis_title="Epic",
            yaxis_title="Numero task",
            legend_title="",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"epic_panel_chart_{key_suffix}",
        )

    with col2:
        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True,
            key=f"epic_panel_table_{key_suffix}",
        )

def render_assignee_panel(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Task per assegnatario")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    assignee_df = df.copy()

    assignee_df["Assignee"] = (
        assignee_df["Assignee"]
        .fillna("")
        .replace("", "Non assegnato")
    )

    grouped = (
        assignee_df.groupby("Assignee", dropna=False)
        .agg(
            Task=("Issue", "count"),
            Completati=("Done", "sum"),
        )
        .reset_index()
    )

    grouped["Aperti"] = grouped["Task"] - grouped["Completati"]

    grouped["Avanzamento %"] = (
        grouped["Completati"] / grouped["Task"] * 100
    ).round(1)

    grouped = grouped.sort_values("Task", ascending=False)

    fig = px.bar(
        grouped.head(25),
        x="Assignee",
        y=["Aperti", "Completati"],
        title="Task per assegnatario",
        barmode="stack",
    )

    fig.update_layout(
        xaxis_title="Assegnatario",
        yaxis_title="Numero task",
        legend_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"assignee_panel_chart_{key_suffix}",
    )

    st.dataframe(
        grouped,
        use_container_width=True,
        hide_index=True,
        key=f"assignee_panel_table_{key_suffix}",
    )

def render_priority_panel(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Task per priorità")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    priority_df = df.copy()

    priority_df["Priority"] = (
        priority_df["Priority"]
        .fillna("")
        .replace("", "Nessuna priorità")
    )

    grouped = (
        priority_df.groupby("Priority", dropna=False)
        .size()
        .reset_index(name="Task")
        .sort_values("Task", ascending=False)
    )

    fig = px.bar(
        grouped,
        x="Priority",
        y="Task",
        text="Task",
        title="Distribuzione task per priorità",
    )

    fig.update_layout(
        xaxis_title="Priorità",
        yaxis_title="Numero task",
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"priority_panel_chart_{key_suffix}",
    )

    st.dataframe(
        grouped,
        use_container_width=True,
        hide_index=True,
        key=f"priority_panel_table_{key_suffix}",
    )

def render_age_panel(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Task aperti da più tempo")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    open_df = df[df["Done"] == False].copy()

    if open_df.empty:
        st.success("Non ci sono task aperti nel perimetro selezionato.")
        return

    open_df = open_df.sort_values("DaysOpen", ascending=False)

    columns = [
        "Issue",
        "Summary",
        "Stato",
        "Assignee",
        "Priority",
        "EpicName",
        "Created",
        "Updated",
        "DaysOpen",
        "DaysSinceUpdate",
        "Url",
    ]

    existing_columns = [
        column
        for column in columns
        if column in open_df.columns
    ]

    st.dataframe(
        open_df[existing_columns].head(30),
        use_container_width=True,
        hide_index=True,
        key=f"age_panel_table_{key_suffix}",
        column_config={
            "Url": st.column_config.LinkColumn("Jira"),
        },
    )

def render_alerts_panel(
    df: pd.DataFrame,
    stale_days: int,
    key_suffix: str = "default",
):
    st.subheader("Alert operativi")

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    open_df = df[df["Done"] == False].copy()

    unassigned_df = open_df[
        open_df["Assignee"].fillna("").str.strip() == ""
    ]

    stale_df = open_df[
        open_df["DaysSinceUpdate"].fillna(0) >= stale_days
    ].sort_values("DaysSinceUpdate", ascending=False)

    no_epic_df = open_df[
        (open_df["EpicKey"].fillna("").str.strip() == "")
        & (open_df["EpicName"].fillna("").str.strip() == "")
    ]

    overdue_df = open_df[
        open_df["DueDate"].notna()
        & (open_df["DueDate"].dt.date < pd.Timestamp.today().date())
    ].sort_values("DueDate", ascending=True)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            f"Fermi da almeno {stale_days} giorni",
            "Non assegnati",
            "Senza Epic",
            "Scaduti",
        ]
    )

    columns = [
        "Issue",
        "Summary",
        "Stato",
        "Assignee",
        "Priority",
        "EpicName",
        "Created",
        "Updated",
        "DueDate",
        "DaysOpen",
        "DaysSinceUpdate",
        "Url",
    ]

    with tab1:
        render_alert_table(
            stale_df,
            columns,
            key=f"{key_suffix}_stale",
        )

    with tab2:
        render_alert_table(
            unassigned_df,
            columns,
            key=f"{key_suffix}_unassigned",
        )

    with tab3:
        render_alert_table(
            no_epic_df,
            columns,
            key=f"{key_suffix}_no_epic",
        )

    with tab4:
        render_alert_table(
            overdue_df,
            columns,
            key=f"{key_suffix}_overdue",
        )

def render_alert_table(df: pd.DataFrame, columns: list[str], key: str):
    if df.empty:
        st.success("Nessuna anomalia rilevata.")
        return

    existing_columns = [
        column
        for column in columns
        if column in df.columns
    ]

    st.dataframe(
        df[existing_columns],
        use_container_width=True,
        hide_index=True,
        key=f"alert_table_{key}",
        column_config={
            "Url": st.column_config.LinkColumn("Jira"),
        },
    )

def render_detail_table(df: pd.DataFrame, key_suffix: str = "default"):
    st.subheader("Dettaglio issue")

    if df.empty:
        st.info("Nessuna issue disponibile.")
        return

    detail_df = df.copy()

    columns = [
        "Issue",
        "Summary",
        "IssueType",
        "Stato",
        "StatusCategory",
        "Assignee",
        "Reporter",
        "Priority",
        "EpicKey",
        "EpicName",
        "Sprint",
        "Created",
        "Updated",
        "DueDate",
        "ResolutionDate",
        "DaysOpen",
        "DaysSinceUpdate",
        "Url",
    ]

    existing_columns = [
        column
        for column in columns
        if column in detail_df.columns
    ]

    st.dataframe(
        detail_df[existing_columns],
        use_container_width=True,
        hide_index=True,
        key=f"detail_table_{key_suffix}",
        column_config={
            "Url": st.column_config.LinkColumn("Jira"),
        },
    )
