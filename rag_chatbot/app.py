import streamlit as st
from chatbot import RAGChatbot

def main():
    """Interface Streamlit pour le chatbot RAG"""
    # Initialisation du chatbot
    chatbot = RAGChatbot()
    
    # Configuration de la page
    st.set_page_config(
        page_title="Chatbot RAG Technique",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Chatbot d'Assistance Technique")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        chatbot.config["cache_enabled"] = st.toggle("Activer le cache", value=True)
        k_results = st.slider("Nombre de résultats", 1, 10, 3)
        
        if st.button("🗑️ Vider le cache"):
            chatbot.cache.clear()
            st.success("Cache vidé!")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("cached", False):
                st.caption("⚡ Depuis le cache")
    
    # User input
    if prompt := st.chat_input("Posez votre question technique..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Recherche en cours..."):
                result = chatbot.ask(prompt, k_results)
                
                st.markdown(result["response"])
                if result.get("cached", False):
                    st.caption("⚡ Réponse depuis le cache")
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "cached": result.get("cached", False)
                })

if __name__ == "__main__":
    main()