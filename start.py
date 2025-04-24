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

if st.session_state["logged_in"]:   
    app.core_app()
else:
    #app.core_app()
    auth.render_login()

