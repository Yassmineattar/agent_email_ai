import streamlit as st
from utils.auth_system import AuthSystem
from client_interface import client_app
from admin_interface import admin_app

def main():
    """Point d'entrée principal - Redirection vers l'app appropriée"""
    query_params = st.query_params
    
    if "admin" in query_params:
        admin_app()
    else:
        client_app()

if __name__ == "__main__":
    main()