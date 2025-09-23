import json
from pathlib import Path
from datetime import datetime
import uuid
from typing import List, Optional, Tuple, Dict 
import streamlit as st
import pandas as pd
import plotly.express as px

class DataEntryForm:
    """Formulaire de saisie de données pour l'admin"""
    
    def __init__(self, data_file: str = "knowledge_base.jsonl"):
        self.data_file = Path(data_file)
        
    def save_entry(self, logiciel: str, probleme: str, solution: str, 
                  tags: List[str] = None, category: str = "") -> Tuple[bool, str]:
        """Sauvegarde une nouvelle entrée dans la base de connaissances"""
        try:
            entry = {
                "uid": str(uuid.uuid4()),
                "logiciel": logiciel.strip(),
                "probleme": probleme.strip(),
                "solution": solution.strip(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.data_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
            return True, "Entrée sauvegardée avec succès!"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {str(e)}"
    
    def get_all_entries(self) -> List[Dict]:
        """Récupère toutes les entrées de la base de connaissances"""
        entries = []
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    for line in f:
                        entries.append(json.loads(line))
            except:
                pass
        return entries
    
    def get_entries_by_software(self, software: str) -> List[Dict]:
        """Récupère les entrées pour un logiciel spécifique"""
        all_entries = self.get_all_entries()
        return [entry for entry in all_entries if entry.get('logiciel', '').lower() == software.lower()]
    
    def get_unique_software(self) -> List[str]:
        """Retourne la liste des logiciels uniques"""
        entries = self.get_all_entries()
        return sorted(list(set(entry.get('logiciel', '') for entry in entries if entry.get('logiciel'))))

def render_data_entry_form(data_form):
    """Affiche le formulaire de saisie de données"""
    st.markdown('<h1 style="font-size: 2.5rem; color: #1e40af; text-align: center;">Saisie de Données</h1>', unsafe_allow_html=True)
    
    # Statistiques rapides
    entries = data_form.get_all_entries()
    unique_software = data_form.get_unique_software()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total entrées", len(entries))
    col2.metric("Logiciels uniques", len(unique_software))
    col3.metric("Tags moyens", f"{sum(len(entry.get('tags', [])) for entry in entries) / max(len(entries), 1):.1f}")
    
    # Formulaire de saisie
    with st.form("data_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            logiciel = st.text_input("Logiciel*", placeholder="Nom du logiciel (ex: SAP, DocuBase, Agirh, Mariproject, etc.)",
                                     help="Indiquez le nom du logiciel concerné par le problème")
            probleme = st.text_area("Problème*", placeholder="Description détaillée du problème", height=120,
                                  help="Décrivez le problème de manière précise et complète")
        
        with col2:
            solution = st.text_area("Solution*", placeholder="Solution détaillée au problème", height=120,
                                  help="Fournissez une solution étape par étape si possible")
        
        submitted = st.form_submit_button("Sauvegarder l'entrée", type="primary")
        
        if submitted:
            if not logiciel or not probleme or not solution:
                st.error("Veuillez remplir tous les champs obligatoires (*)")
            else:
                success, message = data_form.save_entry(logiciel, probleme, solution)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    # Affichage des entrées existantes
    st.markdown("### Entrées Existantes")
    
    if entries:
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            selected_software = st.selectbox("Filtrer par logiciel", [""] + unique_software)
        with col2:
            search_term = st.text_input("Rechercher dans le contenu")
        
        filtered_entries = entries
        if selected_software:
            filtered_entries = [e for e in filtered_entries if e.get('logiciel') == selected_software]
        if search_term:
            search_lower = search_term.lower()
            filtered_entries = [e for e in filtered_entries 
                              if search_lower in e.get('probleme', '').lower() 
                              or search_lower in e.get('solution', '').lower()]
        
        for entry in reversed(filtered_entries[-20:]):  # Afficher les 20 dernières
            with st.expander(f"{entry['logiciel']} - {entry['probleme'][:60]}..."):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Problème:** {entry['probleme']}")
                    st.write(f"**Solution:** {entry['solution']}")
                with col2:
                    st.caption(f"**Créé le:** {entry['created_at'][:10]}")
    else:
        st.info(" Aucune entrée dans la base de connaissances. Commencez par en ajouter une ci-dessus.")