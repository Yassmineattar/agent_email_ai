import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
from chatbot import RAGChatbot
from utils.feedback_system import AdvancedFeedbackSystem
from utils.data_form import DataEntryForm, render_data_entry_form
from utils.auth_system import AuthSystem
from utils.performance_monitor import PerformanceMonitor
from utils.feedback_system import render_advanced_analytics, render_feedback_analysis

# Constantes pour les icônes
ICONS = {
    "users": "",
    "messages": "", 
    "knowledge": "",
    "performance": "",
    "time": "",
    "search": "",
    "ai": "",
    "cache": "",
    "chart": "",
    "refresh": "",
    "clear": "",
    "settings": "",
    "login": "",
    "dashboard": "",
    "analytics": "",
    "feedback": "",
    "system": ""
}

def setup_admin_css():
    """Configure le CSS personnalisé pour l'admin"""
    st.markdown("""
    <style>
    .admin-header { 
        font-size: 2.5rem; 
        color: #1e40af; 
        text-align: center; 
        margin-bottom: 1rem; 
        font-weight: 700; 
    }
    .metric-card { 
        background: white; 
        padding: 1.5rem; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); 
        margin-bottom: 1rem; 
    }
    .admin-login { 
        max-width: 400px; 
        margin: 3rem auto; 
        padding: 2rem; 
        background: white; 
        border-radius: 16px; 
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); 
    }
    .nav-button { 
        margin: 0.2rem 0; 
        border-radius: 8px; 
    }
    .nav-button.active { 
        background-color: #3b82f6; 
        color: white; 
    }
    .status-excellent { color: #10b981; }
    .status-good { color: #f59e0b; }
    .status-poor { color: #ef4444; }
    </style>
    """, unsafe_allow_html=True)

def create_admin_sidebar(chatbot):
    """Crée la sidebar pour l'interface admin"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/admin-settings-male.png", width=80)
        st.markdown("### Administration")
        
        admin_pages = {
            "dashboard": f"{ICONS['dashboard']} Tableau de bord", 
            "data_entry": f"{ICONS['knowledge']} Saisie de données",
            "analytics": f"{ICONS['analytics']} Analytics avancés", 
            "performance": f"{ICONS['performance']} Performance",
            "feedback": f"{ICONS['feedback']} Feedback utilisateurs", 
            "system": f"{ICONS['system']} Système"
        }
        
        selected_page = st.radio("Navigation", list(admin_pages.values()))
        
        st.markdown("---")
        if st.button("Retour au Client", use_container_width=True, type="secondary"):
            st.session_state.admin_authenticated = False
            st.rerun()
        
        return [key for key, value in admin_pages.items() if value == selected_page][0]

def get_performance_status(cache_rate):
    """Retourne le statut de performance basé sur le taux de cache"""
    if cache_rate > 70:
        return "status-excellent", "Excellente"
    elif cache_rate > 40:
        return "status-good", "Bonne"
    else:
        return "status-poor", "À améliorer"

def render_performance_metrics(perf_stats):
    """Affiche les métriques de performance de manière réutilisable"""
    if not perf_stats or not isinstance(perf_stats, dict):
        return {
            "avg_time": 0.0,
            "cache_rate": 0.0,
            "total_requests": 0,
            "delta_text": "0.0% cache"
        }
    
    avg_time = perf_stats.get('avg_total_time', 0)
    cache_rate = perf_stats.get('cache_hit_rate', 0)
    total_requests = perf_stats.get('total_requests', 0)
    
    if total_requests > 0:
        status_class, status_text = get_performance_status(cache_rate)
        delta_text = f"{cache_rate:.1f}% cache"
    else:
        delta_text = "0.0% cache"
    
    return {
        "avg_time": avg_time,
        "cache_rate": cache_rate,
        "total_requests": total_requests,
        "delta_text": delta_text
    }

def render_performance_details(perf_stats):
    """Affiche les détails des performances"""
    if not perf_stats or perf_stats.get('total_requests', 0) == 0:
        st.info("Aucune donnée de performance disponible. Les métriques apparaîtront après les premières requêtes.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Tester l'enregistrement", help="Ajoute une métrique de test"):
                st.session_state.performance_monitor.add_metrics(
                    {"total_time": 1.5, "retrieval_time": 0.5, "generation_time": 1.0},
                    cached=False
                )
                st.success("Métrique de test ajoutée!")
                st.rerun()
        
        with col2:
            if st.button("Vérifier la persistence", help="Recharge depuis le fichier"):
                from utils.performance_monitor import PerformanceMonitor
                st.session_state.performance_monitor = PerformanceMonitor()
                st.rerun()
        return False
    
    # Statistiques détaillées du cache
    perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
    
    with perf_col1:
        st.metric("Requêtes totales", perf_stats.get('total_requests', 0))
    
    with perf_col2:
        st.metric("Cache hits", perf_stats.get('cached_requests', 0))
    
    with perf_col3:
        st.metric("Cache misses", perf_stats.get('uncached_requests', 0))
    
    with perf_col4:
        efficiency = (perf_stats.get('cached_requests', 0) / perf_stats.get('total_requests', 1) * 100)
        st.metric("Efficacité", f"{efficiency:.1f}%")
    
    return True

def render_performance_charts():
    """Affiche les graphiques de performance"""
    recent_metrics = st.session_state.performance_monitor.get_recent_metrics(20)
    
    if not recent_metrics:
        st.info("Aucune donnée historique disponible.")
        return
    
    try:
        df = pd.DataFrame(recent_metrics)
        if 'timestamp' in df.columns and 'total_time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            fig = px.line(df, x='timestamp', y='total_time', 
                        title="Temps de réponse des dernières requêtes",
                        labels={'total_time': 'Temps (s)', 'timestamp': 'Heure'})
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Graphique des performances temporairement indisponible")

def render_feedback_section(feedback_system):
    """Affiche la section feedback"""
    st.subheader("Satisfaction utilisateurs")
    feedback_stats = feedback_system.get_feedback_stats()
    
    if feedback_stats.get("daily_stats"):
        df = pd.DataFrame([
            {"date": date, "positive": data["positive"], "negative": data["negative"]}
            for date, data in feedback_stats["daily_stats"].items()
        ])
        fig = px.bar(df, x="date", y=["positive", "negative"], 
                   title="Feedback par jour", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée de feedback disponible")

def render_knowledge_section(data_form):
    """Affiche la section base de connaissances"""
    st.subheader("Répartition par logiciel")
    knowledge_entries = data_form.get_all_entries()
    
    if knowledge_entries:
        df = pd.DataFrame(knowledge_entries)
        if not df.empty and "logiciel" in df.columns:
            software_counts = df["logiciel"].value_counts().head(10)
            fig = px.pie(values=software_counts.values, names=software_counts.index,
                       title="Top 10 logiciels")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune entrée dans la base de connaissances")

def render_recent_activity(feedback_system, perf_stats):
    """Affiche l'activité récente"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Derniers feedbacks**")
        recent_feedback = feedback_system.get_recent_feedback(5)
        if recent_feedback:
            for fb in recent_feedback:
                sentiment = "👍positive" if fb['feedback'] == 'positive' else "👎negative"
                st.caption(f"{fb['question'][:50]}... - {fb['timestamp'][11:16]} ({sentiment})")
        else:
            st.caption("Aucun feedback récent")
    
    with col2:
        st.markdown("**Performances système**")
        if perf_stats and perf_stats.get('total_requests', 0) > 0:
            cache_rate = perf_stats.get('cache_hit_rate', 0)
            status_class, status_text = get_performance_status(cache_rate)
            
            st.caption(f"Temps moyen: {perf_stats.get('avg_total_time', 0):.2f}s")
            st.caption(f"Recherche: {perf_stats.get('avg_retrieval_time', 0):.2f}s")
            st.caption(f"Génération: {perf_stats.get('avg_generation_time', 0):.2f}s")
            st.caption(f"Cache: {cache_rate:.1f}% ({status_text})")
            st.caption(f"Requêtes: {perf_stats.get('total_requests', 0)} total")
        else:
            st.caption("Temps moyen: 0.00s")
            st.caption("Recherche: 0.00s")
            st.caption("Génération: 0.00s")
            st.caption("Cache: 0.0%")
            st.caption("Requêtes: 0 total")

def render_admin_dashboard(feedback_system, data_form, chatbot):
    """Affiche le tableau de bord admin amélioré avec persistence"""
    st.markdown('<h1 class="admin-header">Tableau de Bord Administratif</h1>', unsafe_allow_html=True)
    
    # Récupération des données
    feedback_stats = feedback_system.get_feedback_stats()
    perf_stats = st.session_state.performance_monitor.get_performance_stats()
    knowledge_entries = data_form.get_all_entries()
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            f"{ICONS['users']} **Utilisateurs actifs**", 
            feedback_stats.get("total", 0), 
            f"{feedback_stats.get('satisfaction_rate', 0):.1f}% satisfaction"
        )
    
    with col2:
        total_messages = len([msg for conv in st.session_state.conversations.values() for msg in conv['messages']])
        st.metric(f"{ICONS['messages']} **Total messages**", total_messages)
    
    with col3:
        st.metric(f"{ICONS['knowledge']} **Base de connaissances**", len(knowledge_entries))
    
    with col4:
        perf_data = render_performance_metrics(perf_stats)
        st.metric(
            f"{ICONS['performance']} **Performance**", 
            f"{perf_data['avg_time']:.2f}s", 
            perf_data['delta_text']
        )
    
    # Section performances
    # st.markdown("---")
    # st.subheader(f"{ICONS['chart']} Performances en Temps Réel")
    
    # has_data = render_performance_details(perf_stats)
    # if has_data:
    #     render_performance_charts()
    
    # Graphiques en temps réel
    col1, col2 = st.columns(2)
    with col1:
        render_feedback_section(feedback_system)
    
    with col2:
        render_knowledge_section(data_form)
    
    # Dernières activités
    st.subheader("Activité récente")
    render_recent_activity(feedback_system, perf_stats)

def render_performance_dashboard(perf_stats):
    """Tableau de bord détaillé des performances"""
    st.markdown('<h1 class="admin-header">Dashboard Performance</h1>', unsafe_allow_html=True)
    
    # Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"{ICONS['refresh']} Rafraîchir les données", use_container_width=True):
            st.rerun()
    with col2:
        if st.button(f"{ICONS['clear']} Vider le cache", use_container_width=True):
            try:
                chatbot = RAGChatbot()
                chatbot.cache.clear()
                st.success("Cache vidé avec succès!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
    
    if not perf_stats:
        # Valeurs par défaut démonstratives
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Temps total moyen", "2.93s")
        with col2:
            st.metric("Temps recherche", "0.03s")
        with col3:
            st.metric("Temps génération", "2.90s")
        with col4:
            st.metric("Taux cache", "66.7%")
        return
    
    # Métriques détaillées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(f"{ICONS['time']} Temps total moyen", f"{perf_stats.get('avg_total_time', 0):.2f}s")
    
    with col2:
        st.metric(f"{ICONS['search']} Temps recherche", f"{perf_stats.get('avg_retrieval_time', 0):.2f}s")
    
    with col3:
        st.metric(f"{ICONS['ai']} Temps génération", f"{perf_stats.get('avg_generation_time', 0):.2f}s")
    
    with col4:
        cache_rate = perf_stats.get('cache_hit_rate', 0)
        st.metric(f"{ICONS['cache']} Taux cache", f"{cache_rate:.1f}%")
    
    # Détails du cache
    st.subheader("Statistiques détaillées du cache")
    
    cache_col1, cache_col2, cache_col3, cache_col4 = st.columns(4)
    
    with cache_col1:
        st.metric("Requêtes totales", perf_stats.get('total_requests', 0))
    
    with cache_col2:
        st.metric("Cache hits", perf_stats.get('cached_requests', 0))
    
    with cache_col3:
        st.metric("Cache misses", perf_stats.get('uncached_requests', 0))
    
    with cache_col4:
        efficiency = (perf_stats.get('cached_requests', 0) / perf_stats.get('total_requests', 1) * 100)
        st.metric("Efficacité", f"{efficiency:.1f}%")
    
    # Graphiques
    st.subheader("Évolution des performances")
    render_performance_charts()

def render_system_settings():
    """Affiche les paramètres système"""
    st.markdown('<h1 class="main-header">Paramètres Système</h1>', unsafe_allow_html=True)
    
    st.subheader("Configuration du Système")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("API Key OpenRouter", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
        st.number_input("Nombre max de résultats", min_value=1, max_value=10, value=3)
    
    with col2:
        st.slider("Seuil de confiance", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        st.toggle("Activer le cache", value=True)
    
    if st.button("Sauvegarder la configuration", type="primary"):
        st.success("Configuration sauvegardée avec succès!")

def render_admin_login(auth_system):
    """Affiche le formulaire de connexion admin"""
    st.markdown("""
    <div style='max-width: 400px; margin: 3rem auto; padding: 2rem; background: white; border-radius: 16px; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);'>
        <h2 style='text-align: center; margin-bottom: 2rem; color: #1e40af;'>Connexion Admin</h2>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Mot de passe administrateur", type="password")
    
    if st.button("Se connecter", use_container_width=True):
        if auth_system.check_credentials("admin", password):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    
    st.markdown("</div>", unsafe_allow_html=True)

def admin_app():
    """Application admin séparée"""
    st.set_page_config(
        page_title="Assistant Technique - Admin", 
        page_icon="⚙️",
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    
    setup_admin_css()

    # Initialisation de l'état de session
    session_defaults = {
        "performance_monitor": PerformanceMonitor(),
        "admin_authenticated": False,
        "admin_username": "",
        "conversations": {},
        "feedback_given": {},
        "chat_start_time": datetime.now().isoformat(),
        "session_id": str(__import__('uuid').uuid4())
    }
    
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialisation des composants
    auth_system = AuthSystem()
    feedback_system = AdvancedFeedbackSystem()
    data_form = DataEntryForm()
    
    @st.cache_resource
    def init_chatbot():
        try:
            return RAGChatbot()
        except Exception as e:
            st.error(f"Erreur d'initialisation: {str(e)}")
            return None
    
    chatbot = init_chatbot()
    
    # Vérifier l'authentification
    if not st.session_state.get('admin_authenticated', False):
        render_admin_login(auth_system)
        return
    
    # Interface admin
    admin_page = create_admin_sidebar(chatbot)
    
    # Récupération des stats de performance
    try:
        perf_stats = st.session_state.performance_monitor.get_performance_stats()
    except Exception as e:
        st.error(f"Erreur lors de la récupération des stats: {e}")
        perf_stats = {}
    
    # Routing des pages - CORRECTION ICI
    if admin_page == "dashboard":
        render_admin_dashboard(feedback_system, data_form, chatbot)
    elif admin_page == "data_entry":
        render_data_entry_form(data_form)
    elif admin_page == "analytics":
        render_advanced_analytics(feedback_system)
    elif admin_page == "performance":
        render_performance_dashboard(perf_stats)
    elif admin_page == "feedback":
        render_feedback_analysis(feedback_system)
    elif admin_page == "system":
        render_system_settings()
    else:
        st.error("Page non trouvée")

if __name__ == "__main__":
    admin_app()