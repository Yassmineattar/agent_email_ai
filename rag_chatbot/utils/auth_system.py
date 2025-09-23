import os
import hashlib
import streamlit as st
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv()

class AuthSystem:
    """Système d'authentification pour l'admin"""
    
    def __init__(self):
        self.admin_password = os.getenv("ADMIN_PASSWORD")
        self.admin_username = os.getenv("ADMIN_USERNAME")
        
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe avec salt"""
        salt = os.getenv("PASSWORD_SALT", "default_salt")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def check_credentials(self, username: str, password: str) -> bool:
        """Vérifie les credentials"""
        return (username == self.admin_username and 
                self.hash_password(password) == self.hash_password(self.admin_password))
    
    def set_admin_credentials(self, username: str, password: str):
        """Définit de nouveaux credentials admin"""
        # Cette méthode pourrait être utilisée pour changer les credentials
        # À utiliser avec précaution en production
        self.admin_username = username
        self.admin_password = password

def render_admin_login(auth_system):
    """Affiche le formulaire de connexion admin"""
    st.markdown("""
    <div style="max-width: 400px; margin: 3rem auto; padding: 2rem; 
                background: white; border-radius: 16px; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);">
        <h2 style="text-align: center; margin-bottom: 2rem; color: #1e40af;">🔐 Connexion Administrateur</h2>
    """, unsafe_allow_html=True)
    
    with st.form("admin_login"):
        username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre identifiant")
        password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
        
        submitted = st.form_submit_button("🚀 Se connecter", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("Veuillez remplir tous les champs")
            elif auth_system.check_credentials(username, password):
                st.session_state.admin_authenticated = True
                st.session_state.admin_username = username
                st.success("Connexion réussie!")
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    
    st.markdown("</div>", unsafe_allow_html=True)