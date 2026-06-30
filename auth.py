import hmac
import streamlit as st

def get_auth_secret(key: str, default=None):
    try:
        return st.secrets["AUTH"][key]
    except Exception:
        return default

def check_credentials(username: str, password: str) -> bool:
    expected_username = get_auth_secret("USERNAME")
    expected_password = get_auth_secret("PASSWORD")

    if not expected_username or not expected_password:
        return False

    username_ok = hmac.compare_digest(
        str(username).strip(),
        str(expected_username).strip(),
    )

    password_ok = hmac.compare_digest(
        str(password),
        str(expected_password),
    )

    return username_ok and password_ok

def login_required():
    if st.session_state.get("authenticated") is True:
        return

    st.markdown(
        """
        <style>
        .login-container {
            max-width: 420px;
            margin: 80px auto 0 auto;
            padding: 2rem;
            border-radius: 16px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        .login-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .login-subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="login-title">Jira Project Dashboard</div>
        <div class="login-subtitle">Accedi per continuare</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi", use_container_width=True)

    if submitted:
        if check_credentials(username, password):
            st.session_state["authenticated"] = True
            st.session_state["authenticated_user"] = username.strip()
            st.rerun()
        else:
            st.error("Username o password non corretti.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

def render_logout():
    authenticated_user = st.session_state.get("authenticated_user", "")

    if authenticated_user:
        st.sidebar.caption(f"Accesso effettuato come: **{authenticated_user}**")

    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state["authenticated"] = False
        st.session_state["authenticated_user"] = ""
        st.rerun()
