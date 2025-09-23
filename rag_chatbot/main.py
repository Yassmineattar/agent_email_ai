import streamlit as st
from client_interface import client_app
from admin_interface import admin_app

def main():
    """Point d'entrée principal"""
    query_params = st.query_params if hasattr(st, 'query_params') else st.experimental_get_query_params()
    
    # Vérifier le paramètre admin
    show_admin = "admin" in query_params
    
    if show_admin:
        admin_app()
    else:
        client_app()

if __name__ == "__main__":
    main()