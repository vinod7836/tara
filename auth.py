import streamlit as st

USERNAME = "admin"
PASSWORD = "WqFJz6p$@O"
def render_login():
    st.markdown("<h2 style='text-align: center;'>🔐Login</h2>", unsafe_allow_html=True)

    # Centered login form layout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            # st.markdown("""
            #     <style>
            #         .login-box {
            #             background-color: #f9f9f9;
            #             padding: 2rem;
            #             border-radius: 10px;
            #             box-shadow: 0 0 10px rgba(0,0,0,0.1);
            #         }
            #     </style>
            #     <div class="login-box">
            # """, unsafe_allow_html=True)

            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
            #st.text(st.session_state.logged_in)
            login_btn = st.button("Login", use_container_width=True)
            if login_btn:
                if username == USERNAME and password == PASSWORD:
                    st.session_state.logged_in = True
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

            st.markdown("</div>", unsafe_allow_html=True)
def logout_button_clicked():
    st.session_state.logged_in = False
    st.session_state.do_logout = True
    st.session_state.clear()
