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

# Chargement de la configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class AdvancedFeedbackSystem:
    """Système de feedback avancé avec analytics"""
    
    def __init__(self, feedback_dir: str = "feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(exist_ok=True)
        
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
            
            # Organisation par date et type
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
                        
                        # Stats par date
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
    </style>
    """, unsafe_allow_html=True)

def create_sidebar(chatbot, feedback_system):
    """Crée la sidebar avec toutes les configurations"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/chatbot.png", width=80)
        st.markdown("### ⚙️ Configuration Avancée")
        
        # Vérifier si chatbot est initialisé
        if chatbot is None:
            st.warning("⚠️ OpenRouter non configuré")
            st.info("Veuillez ajouter OPENROUTER_API_KEY dans les paramètres Streamlit")
            
            # Afficher les statistiques de feedback même en mode démo
            st.markdown("#### 📈 Analytics Feedback")
            feedback_stats = feedback_system.get_feedback_stats()
            
            if feedback_stats["total"] > 0:
                cols = st.columns(2)
                cols[0].metric("👍 Positifs", feedback_stats["positive"])
                cols[1].metric("👎 Négatifs", feedback_stats["negative"])
            
            return  # Quitter early si chatbot n'est pas initialisé
        
        # Paramètres de recherche (seulement si chatbot est initialisé)
        st.markdown("#### 🔍 Paramètres de Recherche")
        k_results = st.slider(
            "Nombre de résultats", 1, 10, 3,
            help="Nombre maximum de sources utilisées pour générer la réponse"
        )
        
        min_confidence = st.slider(
            "Seuil de confiance minimum", 0.0, 1.0, 0.3, 0.1,
            help="Filtre les sources dont la confiance est trop faible"
        )
        
        # Paramètres de performance
        st.markdown("#### ⚡ Performance")
        col1, col2 = st.columns(2)
        with col1:
            cache_enabled = st.toggle(
                "Cache", value=True, help="Active le cache pour des réponses plus rapides"
            )
        with col2:
            streaming_enabled = st.toggle(
                "Streaming", value=False, help="Affiche la réponse au fur et à mesure"
            )
        
        chatbot.config["cache_enabled"] = cache_enabled
        chatbot.config["streaming_enabled"] = streaming_enabled
        
        # Statistiques de performance
        st.markdown("#### 📊 Performance Live")
        perf_stats = st.session_state.performance_monitor.get_performance_stats()
        
        if perf_stats:
            cols = st.columns(2)
            cols[0].metric("⏱️ Temps moyen", f"{perf_stats['avg_total_time']:.2f}s")
            cols[1].metric("📈 Taux cache", f"{perf_stats['cache_hit_rate']:.1f}%")
            
            st.progress(perf_stats['cache_hit_rate'] / 100, "Utilisation du cache")
        
        # Analytics de feedback
        st.markdown("#### 📈 Analytics Feedback")
        feedback_stats = feedback_system.get_feedback_stats()
        
        if feedback_stats["total"] > 0:
            cols = st.columns(2)
            cols[0].metric("👍 Positifs", feedback_stats["positive"])
            cols[1].metric("👎 Négatifs", feedback_stats["negative"])
            
            st.metric("😊 Satisfaction", f"{feedback_stats.get('satisfaction_rate', 0):.1f}%")
            
            # Graphique des feedbacks
            if feedback_stats["daily_stats"]:
                df = pd.DataFrame([
                    {"date": date, "positive": data["positive"], "negative": data["negative"]}
                    for date, data in feedback_stats["daily_stats"].items()
                ])
                fig = px.bar(df, x="date", y=["positive", "negative"], 
                           title="Feedback par Jour", barmode="group")
                st.plotly_chart(fig, use_container_width=True)
        
        # Actions système
        st.markdown("#### 🛠️ Actions Système")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Vider Cache", use_container_width=True):
                chatbot.cache.clear()
                st.success("Cache vidé avec succès!")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("🔄 Nouvelle Session", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key not in ['session_id', 'performance_monitor']:
                        del st.session_state[key]
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.chat_start_time = datetime.now().isoformat()
                st.rerun()
        
        # Export des données
        st.markdown("#### 💾 Export des Données")
        if st.button("📤 Exporter Conversation", use_container_width=True):
            export_data = {
                "session_id": st.session_state.session_id,
                "start_time": st.session_state.chat_start_time,
                "messages": st.session_state.messages,
                "performance_stats": perf_stats,
                "feedback_stats": feedback_stats
            }
            
            st.download_button(
                label="⬇️ Télécharger JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"conversation_{st.session_state.session_id[:8]}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Informations système
        st.markdown("---")
        st.markdown("#### ℹ️ Informations Système")
        
        st.info(f"""
        **Session:** {st.session_state.session_id[:8]}...
        **Début:** {st.session_state.chat_start_time[11:19]}
        **Messages:** {len(st.session_state.messages) // 2}
        """)
        
        # Footer
        st.markdown("---")
        st.caption("""
        **🤖 Assistant Technique RAG** v2.0  
        *Powered by OpenRouter + FAISS + Streamlit*
        """)

def main():
    """Application Streamlit professionnelle complète"""
    
    # Configuration de la page
    st.set_page_config(
        page_title="Enterprise RAG Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo',
            'Report a bug': 'https://github.com/your-repo/issues',
            'About': "# Assistant Technique Enterprise\nSystème RAG professionnel avec analytics avancés"
        }
    )
    
    # Initialisation
    setup_custom_css()
    init_session_state()
    
    # Header principal
    st.markdown('<h1 class="main-header">🤖 Enterprise RAG Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Assistant technique intelligent avec analyse de performances avancée</p>', unsafe_allow_html=True)
    
    # Initialisation des composants
    @st.cache_resource
    def init_components():
        return RAGChatbot(), AdvancedFeedbackSystem()
    
    chatbot, feedback_system = init_components()
    
    # Sidebar
    create_sidebar(chatbot, feedback_system)
    
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
                    # Réponse
                    st.markdown(f'<div class="assistant-response">{message["content"]}</div>', unsafe_allow_html=True)
                    
                    # Badges
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if message.get("cached", False):
                            st.markdown('<span class="cache-badge">⚡ CACHÉ</span>', unsafe_allow_html=True)
                    
                    # Feedback system
                    message_id = f"msg_{i}"
                    if message_id not in st.session_state.feedback_given:
                        st.markdown("**Cette réponse était-elle utile?**")
                        feedback_cols = st.columns([1, 1, 4])
                        
                        with feedback_cols[0]:
                            if st.button("👍", key=f"like_{i}", use_container_width=True):
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
                        
                        with feedback_cols[1]:
                            if st.button("👎", key=f"dislike_{i}", use_container_width=True):
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
                    
                    # Détails techniques
                    with st.expander("📊 Détails Techniques", expanded=False):
                        if message.get("metrics"):
                            metrics = message["metrics"]
                            cols = st.columns(4)
                            cols[0].metric("⏱️ Total", f"{metrics['total_time']:.2f}s")
                            cols[1].metric("🔍 Recherche", f"{metrics['retrieval_time']:.2f}s")
                            cols[2].metric("🤖 Génération", f"{metrics['generation_time']:.2f}s")
                            cols[3].metric("📊 Résultats", metrics['results_count'])
                        
                        if message.get("sources"):
                            st.markdown("**📚 Sources Utilisées:**")
                            for j, source in enumerate(message["sources"], 1):
                                st.markdown(f"""
                                **Source #{j} - {source['logiciel']}**  
                                **Confiance:** {source['confidence']:.1f}%  
                                **UID:** {source['uid']}
                                """)
                                if source.get('probleme'):
                                    st.caption(f"*Problème:* {source['probleme']}")
                                if source.get('solution'):
                                    st.caption(f"*Solution:* {source['solution']}")
    
    # Input utilisateur
    if prompt := st.chat_input("💬 Posez votre question technique..."):
        # Ajouter le message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Afficher le message utilisateur
        with chat_container:
            with st.chat_message("user"):
                st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)
        
        # Générer la réponse
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🔍 Analyse en cours..."):
                    try:
                        result = chatbot.ask(prompt, 3)  # k_results from sidebar would be better
                        
                        # Track performance
                        st.session_state.performance_monitor.add_metrics(
                            result["metrics"], result.get("cached", False)
                        )
                        
                        # Afficher la réponse
                        st.markdown(f'<div class="assistant-response">{result["response"]}</div>', unsafe_allow_html=True)
                        
                        # Système de feedback
                        message_id = f"msg_{len(st.session_state.messages)}"
                        st.markdown("**Cette réponse était-elle utile?**")
                        
                        feedback_cols = st.columns([1, 1, 4])
                        with feedback_cols[0]:
                            if st.button("👍", key="like_new", use_container_width=True):
                                feedback_system.save_feedback(
                                    st.session_state.session_id,
                                    message_id,
                                    prompt,
                                    result["response"],
                                    "positive",
                                    result.get("sources", []),
                                    result.get("metrics", {}),
                                    {"response_index": len(st.session_state.messages)}
                                )
                                st.session_state.feedback_given[message_id] = "positive"
                                st.rerun()
                        
                        with feedback_cols[1]:
                            if st.button("👎", key="dislike_new", use_container_width=True):
                                feedback_system.save_feedback(
                                    st.session_state.session_id,
                                    message_id,
                                    prompt,
                                    result["response"],
                                    "negative",
                                    result.get("sources", []),
                                    result.get("metrics", {}),
                                    {"response_index": len(st.session_state.messages)}
                                )
                                st.session_state.feedback_given[message_id] = "negative"
                                st.rerun()
                        
                        # Sauvegarder le message
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["response"],
                            "sources": result["sources"],
                            "metrics": result["metrics"],
                            "cached": result.get("cached", False)
                        })
                        
                    except Exception as e:
                        error_msg = f"❌ Erreur: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_msg
                        })

if __name__ == "__main__":
    main()