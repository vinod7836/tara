import streamlit as st
import main as app
import auth as auth

# # Initialize session state
if "logged_in" not in st.session_state:
     st.session_state.logged_in = False


st.set_page_config(
    page_title="TARA 2.0",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded"
    )

# Inject custom CSS
st.markdown("""
    <style>
        ._profileContainer_gzau3_53 {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
# st.markdown(
#         """
#         <style>
#             /* Dark Background */
#             .stApp {
#                 background-color: #1E1E1E;  /* Dark Gray */
#                 color: #FFFFFF;  /* White Text 1E1E1E */
#             }
#             .stButton p {
#               color: #FFFFFF;
#             }
#             /* Heading Colors */
#             h1, h2, h3 {
#                 color: #FFDD44;  /* Gold */
            
#             }

#             /* Sidebar Background */
#             .st-emotion-cache-no9uk0 {
#                 background-color: #333333;  /* Dark Sidebar */
#             }


#     /* Change multiselect label color to white */
#             .stMultiSelect label {
#                 color: white !important;
#             }
#             .stAppHeader {
#                 background-color:rgb(14, 17, 23)
#             }
#             .st-el,.st-em,.st-b7,.st-bu,.st-d4 {
#                 background-color: rgb(38, 39, 48);
#             }

#         </style>
#         """,
#         unsafe_allow_html=True
#     )


##col1, col2 = st.columns([10, 1])

# with col2:
#     # 3-dot button
#     with st.expander("⋮", expanded=False):
#         st.markdown("###")
#         selected = st.radio("Menu", ["Rerun", "Settings", "Print", "Record a screencast", "About"],label_visibility="hidden")



if st.session_state.logged_in: 
    app.core_app()
    #st.text(st.session_state.logged_in)
else:
    auth.render_login()
    #st.text(st.session_state.logged_in)

