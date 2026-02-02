import streamlit as st
import logging

import modules.database as db
# from views.home import show_home
# from views.login import show_login
# from views.register import show_register
# from views.headline import show_headline
# from views.settings import show_settings
# from views.admin import show_admin

def main():
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting app...")
    
    # Initialize database
    db.init_db()

    # TODO Add login auth check

    # Initialize session state
    # if "page" not in st.session_state:
    #     st.session_state.page = "home"
    
    # Route to appropriate view
    # if st.session_state.page == "home":
    #     show_home()
    # elif st.session_state.page == "login":
    #     show_login()
    # elif st.session_state.page == "register":
    #     show_register()
    # elif st.session_state.page == "headline":
    #     show_headline()
    # elif st.session_state.page == "settings":
    #     show_settings()
    # elif st.session_state.page == "admin":
    #     show_admin()

if __name__ == "__main__":
    main()