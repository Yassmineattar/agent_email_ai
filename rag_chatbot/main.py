import os
from dotenv import load_dotenv
import streamlit as st
from chatbot import RAGChatbot
import time
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional
import uuid
import hashlib

# Chargement de la configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class AdvancedFeedbackSystem:
    """Système de feedback avancé avec analytics"""
    
    def __init__(self, feedback_dir: str = "feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(exist_ok=True, parents=True)
        
    def save_feedback(self, session_id: str, message_id: str, question: str, 
                     response: str, feedback: str, sources: List[Dict], 
                     metrics: Dict, metadata: Optional[Dict] = None) -> bool:
        """Sauvegarde le feedback avec métadonnées complètes"""
        try:
            feedback_data = {
                "session_id": session_id,
                "message_id": message_id,
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "response": response,
                "feedback": feedback,
                "sources": sources,
                "metrics": metrics,
                "metadata": metadata or {},
                "response_length": len(response),
                "source_count": len(sources),
                "average_confidence": np.mean([s.get('confidence', 0) for s in sources]) if sources else 0
            }
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            feedback_file = self.feedback_dir / f"feedback_{date_str}.jsonl"
            
            with open(feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")
                
            return True
        except Exception as e:
            st.error(f"❌ Erreur sauvegarde feedback: {e}")
            return False

    def get_feedback_stats(self) -> Dict:
        """Retourne les statistiques de feedback"""
        feedback_files = list(self.feedback_dir.glob("*.jsonl"))
        stats = {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "avg_response_time": 0,
            "avg_confidence": 0,
            "daily_stats": {}
        }
        
        total_time = 0
        total_confidence = 0
        
        for file in feedback_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        stats["total"] += 1
                        
                        if data["feedback"] == "positive":
                            stats["positive"] += 1
                        else:
                            stats["negative"] += 1
                        
                        total_time += data["metrics"].get("total_time", 0)
                        total_confidence += data.get("average_confidence", 0)
                        
                        date = data["timestamp"][:10]
                        if date not in stats["daily_stats"]:
                            stats["daily_stats"][date] = {"positive": 0, "negative": 0}
                        
                        if data["feedback"] == "positive":
                            stats["daily_stats"][date]["positive"] += 1
                        else:
                            stats["daily_stats"][date]["negative"] += 1
                            
            except Exception as e:
                continue
        
        if stats["total"] > 0:
            stats["avg_response_time"] = total_time / stats["total"]
            stats["avg_confidence"] = total_confidence / stats["total"]
            stats["satisfaction_rate"] = (stats["positive"] / stats["total"]) * 100
        
        return stats

class PerformanceMonitor:
    """Monitor des performances en temps réel"""
    
    def __init__(self):
        self.metrics_history = []
        
    def add_metrics(self, metrics: Dict, cached: bool = False):
        """Ajoute des métriques à l'historique"""
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "cached": cached,
            **metrics
        })
        
    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance"""
        if not self.metrics_history:
            return {}
            
        df = pd.DataFrame(self.metrics_history)
        return {
            "avg_total_time": df["total_time"].mean(),
            "avg_retrieval_time": df["retrieval_time"].mean(),
            "avg_generation_time": df["generation_time"].mean(),
            "cache_hit_rate": (df["cached"].sum() / len(df)) * 100,
            "total_requests": len(df)
        }

class DataEntryForm:
    """Formulaire de saisie de données pour l'admin"""
    
    def __init__(self):
        self.data_file = Path("knowledge_base.jsonl")
        
    def save_entry(self, logiciel: str, probleme: str, solution: str, tags: List[str] = None):
        """Sauvegarde une nouvelle entrée dans la base de connaissances"""
        try:
            entry = {
                "uid": str(uuid.uuid4()),
                "logiciel": logiciel,
                "probleme": probleme,
                "solution": solution,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.data_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
            return True, "✅ Entrée sauvegardée avec succès!"
        except Exception as e:
            return False, f"❌ Erreur lors de la sauvegarde: {str(e)}"
    
    def get_all_entries(self):
        """Récupère toutes les entrées de la base de connaissances"""
        entries = []
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as f:
                for line in f:
                    entries.append(json.loads(line))
        return entries

class AuthSystem:
    """Système d'authentification pour l'admin"""
    
    def __init__(self):
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password: str) -> bool:
        """Vérifie le mot de passe"""
        return self.hash_password(password) == self.hash_password(self.admin_password)

def init_session_state():
    """Initialise l'état de session"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = {}
    if "performance_monitor" not in st.session_state:
        st.session_state.performance_monitor = PerformanceMonitor()
    if "chat_start_time" not in st.session_state:
        st.session_state.chat_start_time = datetime.now().isoformat()
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = "default"
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

def setup_custom_css():
    """Configure le CSS personnalisé"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        color: #2563eb;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .assistant-response {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .user-message {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #1d4ed8;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #93c5fd;
    }
    .feedback-buttons {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        align-items: center;
    }
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e40af;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .cache-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    .source-badge {
        background: #f59e0b;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-size: 0.7rem;
        margin-right: 0.5rem;
    }
    .conversation-item {
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 8px;
        cursor: pointer;
    }
    .conversation-item:hover {
        background-color: #f1f5f9;
    }
    .conversation-item.active {
        background-color: #dbeafe;
        font-weight: 600;
    }
    .admin-login {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def create_client_sidebar(chatbot, feedback_system):
    """Crée la sidebar pour l'interface client"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/chatbot.png", width=80)
        st.markdown("### 💬 Historique des Conversations")
        
        # Bouton nouvelle conversation
        if st.button("➕ Nouvelle conversation", use_container_width=True):
            new_id = f"conv_{len(st.session_state.conversations) + 1}"
            st.session_state.conversations[new_id] = {
                "id": new_id,
                "title": f"Conversation {len(st.session_state.conversations) + 1}",
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
            st.session_state.current_conversation = new_id
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        
        # Liste des conversations
        for conv_id, conv in st.session_state.conversations.items():
            is_active = conv_id == st.session_state.current_conversation
            emoji = "🔵" if is_active else "⚪"
            
            if st.button(f"{emoji} {conv['title']}", key=f"conv_{conv_id}", 
                        use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.current_conversation = conv_id
                st.session_state.messages = conv["messages"]
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### ⚙️ Paramètres")
        
        if chatbot:
            k_results = st.slider("Nombre de résultats", 1, 10, 3)
            cache_enabled = st.toggle("Cache", value=True)
            
            chatbot.config["cache_enabled"] = cache_enabled
            
        # Informations session
        st.markdown("---")
        st.markdown("#### ℹ️ Informations")
        st.info(f"""
        **Session:** {st.session_state.session_id[:8]}...
        **Conversation:** {st.session_state.current_conversation}
        **Messages:** {len(st.session_state.messages) // 2}
        """)

def create_admin_sidebar():
    """Crée la sidebar pour l'interface admin"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/admin-settings-male.png", width=80)
        st.markdown("### ⚙️ Administration")
        
        admin_pages = {
            "dashboard": "📊 Tableau de bord",
            "data_entry": "📝 Saisie de données",
            "analytics": "📈 Analytics",
            "system": "⚙️ Système"
        }
        
        selected_page = st.radio("Navigation", list(admin_pages.values()))
        
        # Ajouter le bouton "Vider le cache" dans la sidebar admin
        st.markdown("---")
        st.markdown("#### 🗑️ Actions Système")
        if st.button("🗑️ Vider le Cache", use_container_width=True):
            try:
                chatbot.cache.clear()
                st.success("Cache vidé avec succès!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors du vidage du cache: {e}")
        
        st.markdown("---")
        if st.button("🚪 Retour à l'interface Client", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()
        
        return [key for key, value in admin_pages.items() if value == selected_page][0]

def render_client_interface(chatbot, feedback_system):
    """Affiche l'interface client"""
    st.markdown('<h1 class="main-header">🤖 Assistant Technique</h1>', unsafe_allow_html=True)
    
    # Container de chat principal
    chat_container = st.container()
    
    # Affichage de l'historique des messages
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(f'<div class="assistant-response">{message["content"]}</div>', unsafe_allow_html=True)
                    
                    # Feedback system
                    message_id = f"msg_{i}"
                    if message_id not in st.session_state.feedback_given:
                        st.markdown("**Cette réponse était-elle utile?**")
                        cols = st.columns([1, 1, 6])
                        
                        with cols[0]:
                            if st.button("👍", key=f"like_{i}"):
                                feedback_system.save_feedback(
                                    st.session_state.session_id,
                                    message_id,
                                    st.session_state.messages[i-1]["content"] if i > 0 else "Unknown",
                                    message["content"],
                                    "positive",
                                    message.get("sources", []),
                                    message.get("metrics", {}),
                                    {"response_index": i}
                                )
                                st.session_state.feedback_given[message_id] = "positive"
                                st.rerun()
                        
                        with cols[1]:
                            if st.button("👎", key=f"dislike_{i}"):
                                feedback_system.save_feedback(
                                    st.session_state.session_id,
                                    message_id,
                                    st.session_state.messages[i-1]["content"] if i > 0 else "Unknown",
                                    message["content"],
                                    "negative",
                                    message.get("sources", []),
                                    message.get("metrics", {}),
                                    {"response_index": i}
                                )
                                st.session_state.feedback_given[message_id] = "negative"
                                st.rerun()
                    else:
                        feedback = st.session_state.feedback_given[message_id]
                        if feedback == "positive":
                            st.success("✅ Merci pour votre feedback positif!")
                        else:
                            st.warning("📝 Nous prenons note de votre retour pour nous améliorer.")
    # Input utilisateur
    if prompt := st.chat_input("💬 Posez votre question technique..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Sauvegarder dans la conversation actuelle
        if st.session_state.current_conversation in st.session_state.conversations:
            st.session_state.conversations[st.session_state.current_conversation]["messages"] = st.session_state.messages
        
        # Générer la réponse
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🔍 Analyse en cours..."):
                    try:
                        result = chatbot.ask(prompt, 3) if chatbot else {
                            "response": "⚠️ Chatbot non configuré",
                            "sources": [],
                            "metrics": {},
                            "cached": False
                        }
                        
                        if chatbot:
                            st.session_state.performance_monitor.add_metrics(
                                result["metrics"], result.get("cached", False)
                            )
                        
                        st.markdown(f'<div class="assistant-response">{result["response"]}</div>', unsafe_allow_html=True)
                        
                        # Sauvegarder le message
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["response"],
                            "sources": result.get("sources", []),
                            "metrics": result.get("metrics", {}),
                            "cached": result.get("cached", False)
                        })
                        
                        # Mettre à jour la conversation
                        if st.session_state.current_conversation in st.session_state.conversations:
                            st.session_state.conversations[st.session_state.current_conversation]["messages"] = st.session_state.messages
                        
                    except Exception as e:
                        error_msg = f"❌ Erreur: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

def render_admin_dashboard(feedback_system, data_form):
    """Affiche le tableau de bord admin"""
    st.markdown('<h1 class="main-header">📊 Tableau de Bord Admin</h1>', unsafe_allow_html=True)
    
    # Statistiques
    feedback_stats = feedback_system.get_feedback_stats()
    perf_stats = st.session_state.performance_monitor.get_performance_stats()
    knowledge_entries = data_form.get_all_entries()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Feedback", feedback_stats.get("total", 0))
    with col2:
        st.metric("Taux Satisfaction", f"{feedback_stats.get('satisfaction_rate', 0):.1f}%")
    with col3:
        st.metric("Entrées Base", len(knowledge_entries))
    with col4:
        st.metric("Requêtes Total", perf_stats.get("total_requests", 0))
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        if feedback_stats.get("daily_stats"):
            df = pd.DataFrame([
                {"date": date, "positive": data["positive"], "negative": data["negative"]}
                for date, data in feedback_stats["daily_stats"].items()
            ])
            fig = px.bar(df, x="date", y=["positive", "negative"], 
                       title="Feedback par Jour", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if knowledge_entries:
            df = pd.DataFrame(knowledge_entries)
            if not df.empty and "logiciel" in df.columns:
                software_counts = df["logiciel"].value_counts()
                fig = px.pie(values=software_counts.values, names=software_counts.index,
                           title="Répartition par Logiciel")
                st.plotly_chart(fig, use_container_width=True)

def render_data_entry_form(data_form):
    """Affiche le formulaire de saisie de données"""
    st.markdown('<h1 class="main-header">📝 Saisie de Données</h1>', unsafe_allow_html=True)
    
    with st.form("data_entry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            logiciel = st.text_input("Logiciel*", placeholder="Nom du logiciel")
            probleme = st.text_area("Problème*", placeholder="Description du problème", height=150)
        
        with col2:
            tags = st.text_input("Tags", placeholder="tag1, tag2, tag3")
            solution = st.text_area("Solution*", placeholder="Solution au problème", height=150)
        
        submitted = st.form_submit_button("💾 Sauvegarder")
        
        if submitted:
            if not logiciel or not probleme or not solution:
                st.error("Veuillez remplir tous les champs obligatoires (*)")
            else:
                tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
                success, message = data_form.save_entry(logiciel, probleme, solution, tag_list)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Afficher les entrées existantes
    st.markdown("### 📋 Entrées Existantes")
    entries = data_form.get_all_entries()
    
    if entries:
        for entry in entries[-10:]:
            with st.expander(f"{entry['logiciel']} - {entry['probleme'][:50]}..."):
                st.write(f"**Problème:** {entry['probleme']}")
                st.write(f"**Solution:** {entry['solution']}")
                st.write(f"**Tags:** {', '.join(entry['tags'])}")
                st.write(f"**Créé le:** {entry['created_at'][:10]}")
    else:
        st.info("Aucune entrée dans la base de connaissances.")

def render_admin_analytics(feedback_system):
    """Affiche les analytics avancés"""
    st.markdown('<h1 class="main-header">📈 Analytics Avancés</h1>', unsafe_allow_html=True)
    
    feedback_stats = feedback_system.get_feedback_stats()
    perf_stats = st.session_state.performance_monitor.get_performance_stats()
    
    # Métriques détaillées
    st.subheader("📊 Métriques de Performance")
    
    if perf_stats:
        col1, col2, col3 = st.columns(3)
        col1.metric("⏱️ Temps moyen", f"{perf_stats['avg_total_time']:.2f}s")
        col2.metric("🔍 Temps recherche", f"{perf_stats['avg_retrieval_time']:.2f}s")
        col3.metric("🤖 Temps génération", f"{perf_stats['avg_generation_time']:.2f}s")
        
        col1, col2 = st.columns(2)
        col1.metric("📈 Taux cache", f"{perf_stats['cache_hit_rate']:.1f}%")
        col2.metric("🔢 Total requêtes", perf_stats['total_requests'])
    
    # Analytics temporels
    st.subheader("📅 Trends Temporels")
    
    if feedback_stats.get("daily_stats"):
        df = pd.DataFrame([
            {"date": date, "total": data["positive"] + data["negative"], 
             "positive": data["positive"], "negative": data["negative"]}
            for date, data in feedback_stats["daily_stats"].items()
        ])
        
        fig = make_subplots(rows=2, cols=1, subplot_titles=("Volume de requêtes", "Taux de satisfaction"))
        
        fig.add_trace(go.Bar(x=df["date"], y=df["total"], name="Total requêtes"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["positive"]/df["total"]*100, 
                               name="Taux satisfaction", mode="lines+markers"), row=2, col=1)
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def render_system_settings():
    """Affiche les paramètres système"""
    st.markdown('<h1 class="main-header">⚙️ Paramètres Système</h1>', unsafe_allow_html=True)
    
    st.subheader("Configuration du Système")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("API Key OpenRouter", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
        st.number_input("Nombre max de résultats", min_value=1, max_value=10, value=3)
    
    with col2:
        st.slider("Seuil de confiance", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        st.toggle("Activer le cache", value=True)
    
    if st.button("💾 Sauvegarder la configuration", type="primary"):
        st.success("Configuration sauvegardée avec succès!")

def render_admin_login(auth_system):
    """Affiche le formulaire de connexion admin"""
    st.markdown("""
    <div class="admin-login">
        <h2 style="text-align: center; margin-bottom: 2rem;">🔐 Connexion Admin</h2>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Mot de passe administrateur", type="password")
    
    if st.button("Se connecter", use_container_width=True):
        if auth_system.check_password(password):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    
    st.markdown("</div>", unsafe_allow_html=True)

def client_app():
    """Application client principale"""
    st.set_page_config(
        page_title="Assistant Technique - Client",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    setup_custom_css()
    init_session_state()
    
    @st.cache_resource
    def init_components():
        try:
            chatbot = RAGChatbot()
            return chatbot, AdvancedFeedbackSystem()
        except Exception as e:
            st.error(f"⚠️ Erreur d'initialisation: {str(e)}")
            return None, AdvancedFeedbackSystem()
    
    chatbot, feedback_system = init_components()
    create_client_sidebar(chatbot, feedback_system)
    render_client_interface(chatbot, feedback_system)
    
    # Bouton admin caché (accessible seulement avec URL spécifique)
    if st.session_state.get('show_admin_button', False):
        if st.sidebar.button("👨‍💼 Accès Admin", type="secondary"):
            st.session_state.is_admin = True
            st.rerun()

def admin_app():
    """Application admin séparée"""
    st.set_page_config(
        page_title="Assistant Technique - Admin",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    setup_custom_css()
    init_session_state()
    
    auth_system = AuthSystem()
    feedback_system = AdvancedFeedbackSystem()
    data_form = DataEntryForm()
    
    # Vérifier l'authentification
    if not st.session_state.admin_authenticated:
        render_admin_login(auth_system)
        return
    
    # Interface admin authentifiée
    admin_page = create_admin_sidebar()
    
    if admin_page == "dashboard":
        render_admin_dashboard(feedback_system, data_form)
    elif admin_page == "data_entry":
        render_data_entry_form(data_form)
    elif admin_page == "analytics":
        render_admin_analytics(feedback_system)
    elif admin_page == "system":
        render_system_settings()

def main():
    """Point d'entrée principal - Redirection vers l'app appropriée"""
    # Vérifier le query parameter pour déterminer quelle app afficher
    query_params = st.query_params
    
    if "admin" in query_params:
        admin_app()
    else:
        client_app()

if __name__ == "__main__":
    main()