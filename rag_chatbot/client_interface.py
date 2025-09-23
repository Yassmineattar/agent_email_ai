import streamlit as st
from datetime import datetime
import uuid
import time
from chatbot import RAGChatbot
from utils.feedback_system import AdvancedFeedbackSystem
from utils.performance_monitor import PerformanceMonitor

def setup_client_css():
    """Configure le CSS personnalisé pour le client"""
    st.markdown("""
    <style>
    .main-header { 
        font-size: 2.8rem; 
        color: #2563eb; 
        text-align: center; 
        margin-bottom: 1rem; 
        font-weight: 700; 
    }
    .assistant-response { 
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
        padding: 1.5rem; 
        border-radius: 12px; 
        border-left: 4px solid #3b82f6; 
        margin: 1rem 0; 
    }
    .user-message { 
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
        padding: 1.5rem; 
        border-radius: 12px; 
        border-left: 4px solid #1d4ed8; 
        margin: 1rem 0; 
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
    .feedback-buttons {
        margin-top: 1rem;
        display: flex;
        gap: 0.5rem;
    }
    .hidden {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialise l'état de session avec des valeurs par défaut"""
    session_defaults = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "feedback_given": {},
        "chat_start_time": datetime.now().isoformat(),
        "conversations": {
            "default": {
                "id": "default", 
                "title": "Conversation principale",
                "messages": [], 
                "created_at": datetime.now().isoformat()
            }
        }, 
        "current_conversation": "default",
        "processing_message": False,  # Nouveau: pour gérer l'état de traitement
        "pending_message": None,      # Nouveau: message en attente de traitement
    }
    
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialisation du PerformanceMonitor
    if "performance_monitor" not in st.session_state:
        st.session_state.performance_monitor = PerformanceMonitor()

def create_conversation_sidebar():
    """Crée la sidebar pour la gestion des conversations"""
    with st.sidebar:
        st.image("https://freesvg.org/img/1538298822.png", width=100)
        st.markdown("### Historique des Conversations")
        
        # Bouton nouvelle conversation
        if st.button("Nouvelle conversation", use_container_width=True, type="primary"):
            create_new_conversation()
        
        st.markdown("---")
        render_conversation_list()
        st.markdown("---")
        render_sidebar_stats()
        st.markdown("---")
        render_session_info()

def create_new_conversation():
    """Crée une nouvelle conversation"""
    new_id = f"conv_{len(st.session_state.conversations) + 1}"
    st.session_state.conversations[new_id] = {
        "id": new_id,
        "title": f"Conversation {len(st.session_state.conversations) + 1}",
        "messages": [],
        "created_at": datetime.now().isoformat()
    }
    st.session_state.current_conversation = new_id
    st.session_state.messages = []
    st.session_state.processing_message = False
    st.session_state.pending_message = None
    st.rerun()

def render_conversation_list():
    """Affiche la liste des conversations"""
    for conv_id, conv in st.session_state.conversations.items():
        is_active = conv_id == st.session_state.current_conversation
        status_indicator = "●" if is_active else "○"
        button_type = "primary" if is_active else "secondary"
        
        if st.button(f"{status_indicator} {conv['title']}", 
                    key=f"conv_{conv_id}", 
                    use_container_width=True, 
                    type=button_type):
            switch_conversation(conv_id)

def switch_conversation(conv_id):
    """Change de conversation"""
    st.session_state.current_conversation = conv_id
    st.session_state.messages = st.session_state.conversations[conv_id]["messages"]
    st.session_state.processing_message = False
    st.session_state.pending_message = None
    st.rerun()

def render_sidebar_stats():
    """Affiche les statistiques dans la sidebar"""
    st.markdown("#### Statistiques")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.messages))
    with col2:
        st.metric("Conversations", len(st.session_state.conversations))

def render_session_info():
    """Affiche les informations de session"""
    st.markdown("#### Informations")
    st.info(f"**Session:** {st.session_state.session_id[:8]}...")

def render_message_history():
    """Affiche l'historique des messages"""
    # Afficher tous les messages sauf le dernier s'il est en cours de traitement
    messages_to_display = st.session_state.messages.copy()
    
    # Si un message est en cours de traitement, on ne l'affiche pas encore
    if st.session_state.processing_message and st.session_state.pending_message:
        # On affiche tout sauf le dernier message utilisateur qui est en cours de traitement
        if messages_to_display and messages_to_display[-1]["role"] == "user":
            messages_to_display = messages_to_display[:-1]
    
    for i, message in enumerate(messages_to_display):
        if message["role"] == "user":
            render_user_message(message["content"])
        elif message["role"] == "assistant":
            render_assistant_message(message, i)

def render_user_message(content):
    """Affiche un message utilisateur"""
    with st.chat_message("user"):
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)

def render_assistant_message(message, index):
    """Affiche un message assistant avec système de feedback"""
    with st.chat_message("assistant"):
        st.markdown(f'<div class="assistant-response">{message["content"]}</div>', unsafe_allow_html=True)
        render_feedback_system(message, index)

def render_feedback_system(message, index):
    """Affiche le système de feedback pour un message"""
    message_id = f"msg_{index}"
    
    if message_id not in st.session_state.feedback_given:
        render_feedback_buttons(message_id, message, index)
    else:
        display_feedback_status(message_id)

def render_feedback_buttons(message_id, message, index):
    """Affiche les boutons de feedback"""
    st.markdown("**Cette réponse était-elle utile?**")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("👍 Positif", key=f"like_{index}", use_container_width=True):
            save_feedback(message_id, message, index, "positive")
    
    with col2:
        if st.button("👎 Négatif", key=f"dislike_{index}", use_container_width=True):
            save_feedback(message_id, message, index, "negative")

def save_feedback(message_id, message, index, feedback_type):
    """Sauvegarde le feedback utilisateur"""
    from utils.feedback_system import AdvancedFeedbackSystem
    feedback_system = AdvancedFeedbackSystem()
    
    previous_message = st.session_state.messages[index-1]["content"] if index > 0 else "Unknown"
    
    feedback_system.save_feedback(
        st.session_state.session_id, message_id,
        previous_message,
        message["content"], feedback_type, message.get("sources", []),
        message.get("metrics", {}), {"response_index": index}
    )
    
    st.session_state.feedback_given[message_id] = feedback_type
    st.rerun()

def display_feedback_status(message_id):
    """Affiche le statut du feedback donné"""
    feedback = st.session_state.feedback_given[message_id]
    if feedback == "positive":
        st.success("✓ Merci pour votre retour positif")
    else:
        st.warning("✓ Nous prenons note de votre retour")

def handle_user_input(chatbot, feedback_system):
    """Gère la saisie utilisateur et génère la réponse"""
    # Si un message est en cours de traitement, on affiche l'état actuel
    if st.session_state.processing_message:
        display_processing_state(chatbot, feedback_system)
        return
    
    # Nouvelle saisie utilisateur
    if prompt := st.chat_input("Posez votre question technique..."):
        # Marquer qu'un message est en cours de traitement
        st.session_state.processing_message = True
        st.session_state.pending_message = prompt
        
        # Ajouter immédiatement le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Forcer le rerun pour afficher le message utilisateur immédiatement
        st.rerun()

def display_processing_state(chatbot, feedback_system):
    """Affiche l'état de traitement en cours"""
    if st.session_state.pending_message:
        # Afficher le message utilisateur qui est en cours de traitement
        with st.chat_message("user"):
            st.markdown(f'<div class="user-message">{st.session_state.pending_message}</div>', unsafe_allow_html=True)
        
        # Générer et afficher la réponse de l'assistant
        generate_assistant_response(st.session_state.pending_message, chatbot, feedback_system)

def generate_assistant_response(prompt, chatbot, feedback_system):
    """Génère et affiche la réponse de l'assistant"""
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            try:
                result = get_chatbot_response(prompt, chatbot)
                display_assistant_response(result, prompt, feedback_system)
                
            except Exception as e:
                display_error_message(str(e))
            finally:
                # Réinitialiser l'état de traitement
                st.session_state.processing_message = False
                st.session_state.pending_message = None

def get_chatbot_response(prompt, chatbot):
    """Obtient la réponse du chatbot"""
    if chatbot:
        return chatbot.ask(prompt, 3)
    else:
        return {
            "response": "Chatbot non configuré",
            "sources": [],
            "metrics": {},
            "cached": False
        }

def display_assistant_response(result, prompt, feedback_system):
    """Affiche la réponse de l'assistant"""
    response_text = result["response"]
    st.markdown(f'<div class="assistant-response">{response_text}</div>', unsafe_allow_html=True)
    
    # Sauvegarder le message (il est déjà dans l'historique depuis le premier rerun)
    # On s'assure juste qu'il n'y a pas de doublon
    if not st.session_state.messages or st.session_state.messages[-1]["role"] != "assistant":
        save_assistant_message(result, response_text)
    
    # Afficher le système de feedback pour la nouvelle réponse
    render_new_response_feedback(prompt, response_text, result, feedback_system)

def save_assistant_message(result, response_text):
    """Sauvegarde le message de l'assistant"""
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": result.get("sources", []),
        "metrics": result.get("metrics", {}),
        "cached": result.get("cached", False)
    })

def render_new_response_feedback(prompt, response_text, result, feedback_system):
    """Affiche le feedback pour la nouvelle réponse"""
    message_id = f"msg_{len(st.session_state.messages) - 1}"  # -1 car le message est déjà ajouté
    
    st.markdown("**Cette réponse était-elle utile?**")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("👍 Positif", key="like_new", use_container_width=True):
            save_new_feedback(message_id, prompt, response_text, result, "positive", feedback_system)
    
    with col2:
        if st.button("👎 Négatif", key="dislike_new", use_container_width=True):
            save_new_feedback(message_id, prompt, response_text, result, "negative", feedback_system)

def save_new_feedback(message_id, prompt, response_text, result, feedback_type, feedback_system):
    """Sauvegarde le feedback pour la nouvelle réponse"""
    feedback_system.save_feedback(
        st.session_state.session_id, message_id, prompt, response_text,
        feedback_type, result.get("sources", []), result.get("metrics", {}),
        {"response_index": len(st.session_state.messages) - 1}
    )
    st.session_state.feedback_given[message_id] = feedback_type
    st.rerun()

def display_error_message(error_msg):
    """Affiche un message d'erreur"""
    st.error(f"Erreur: {error_msg}")
    # Ajouter le message d'erreur à l'historique
    st.session_state.messages.append({"role": "assistant", "content": f"Erreur: {error_msg}"})
    # Réinitialiser l'état de traitement
    st.session_state.processing_message = False
    st.session_state.pending_message = None

@st.cache_resource
def initialize_components():
    """Initialise les composants principaux"""
    try:
        chatbot = RAGChatbot()
        feedback_system = AdvancedFeedbackSystem()
        return chatbot, feedback_system
    except Exception as e:
        st.error(f"Erreur d'initialisation: {str(e)}")
        return None, AdvancedFeedbackSystem()

def render_client_interface(chatbot, feedback_system):
    """Affiche l'interface client principale"""
    st.markdown('<h1 class="main-header">Assistant Technique</h1>', unsafe_allow_html=True)
    
    # Afficher l'historique des messages (sans le message en cours de traitement)
    render_message_history()
    
    # Gérer la saisie utilisateur
    handle_user_input(chatbot, feedback_system)

def client_app():
    """Application client principale"""
    st.set_page_config(
        page_title="Assistant Technique - Client",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    setup_client_css()
    initialize_session_state()
    
    chatbot, feedback_system = initialize_components()
    create_conversation_sidebar()
    render_client_interface(chatbot, feedback_system)

if __name__ == "__main__":
    client_app()