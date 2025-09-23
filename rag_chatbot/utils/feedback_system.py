import json
from pathlib import Path
from datetime import datetime
import numpy as np
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import streamlit as st

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
            st.error(f"Erreur sauvegarde feedback: {e}")
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

    def get_recent_feedback(self, limit: int = 10) -> List[Dict]:
        """Retourne les feedbacks les plus récents"""
        feedback_files = sorted(self.feedback_dir.glob("*.jsonl"), reverse=True)
        recent_feedback = []
        
        for file in feedback_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(recent_feedback) >= limit:
                            return recent_feedback
                        recent_feedback.append(json.loads(line))
            except:
                continue
        
        return recent_feedback

def render_advanced_analytics(feedback_system):
    """Affiche les analytics avancés"""
    st.markdown('<h1 style="font-size: 2.5rem; color: #1e40af; text-align: center;">Analytics Avancés</h1>', unsafe_allow_html=True)
    
    feedback_stats = feedback_system.get_feedback_stats()
    
    if not feedback_stats.get("total", 0):
        st.info("Aucune donnée de feedback disponible")
        return
    
    # Métriques détaillées
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Feedback", feedback_stats["total"])
    col2.metric("Positifs", feedback_stats["positive"])
    col3.metric("Négatifs", feedback_stats["negative"])
    col4.metric("Satisfaction", f"{feedback_stats.get('satisfaction_rate', 0):.1f}%")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        if feedback_stats.get("daily_stats"):
            df = pd.DataFrame([
                {"date": date, "positive": data["positive"], "negative": data["negative"]}
                for date, data in feedback_stats["daily_stats"].items()
            ])
            fig = px.line(df, x="date", y=["positive", "negative"], 
                         title="Évolution des feedbacks", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(values=[feedback_stats["positive"], feedback_stats["negative"]], 
                    names=["Positifs", "Négatifs"], title="Répartition des feedbacks")
        st.plotly_chart(fig, use_container_width=True)

def render_feedback_analysis(feedback_system):
    """Affiche l'analyse détaillée des feedbacks"""
    st.markdown('<h1 style="font-size: 2.5rem; color: #1e40af; text-align: center;">Analyse des Feedbacks</h1>', unsafe_allow_html=True)
    
    recent_feedback = feedback_system.get_recent_feedback(20)
    
    if not recent_feedback:
        st.info("Aucun feedback disponible")
        return
    
    st.subheader("Derniers feedbacks")
    
    for feedback in recent_feedback:
        with st.expander(f"{feedback['timestamp'][:16]} - {feedback['question'][:50]}..."):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Question:** {feedback['question']}")
                st.write(f"**Réponse:** {feedback['response'][:100]}...")
                st.write(f"**Feedback:** {'👍 Positif' if feedback['feedback'] == 'positive' else '👎 Négatif'}")
                
                # Afficher la meilleure source (confiance max)
                if feedback.get('sources'):
                    best_source = max(feedback['sources'], key=lambda x: x.get('confidence', 0))
                    st.write(f"**Meilleure source:** {best_source.get('logiciel', 'N/A')} ({best_source.get('confidence', 0):.1f}%)")
            
            with col2:
                st.write(f"**Session:** {feedback['session_id'][:8]}...")
                
                # Afficher les métriques de confiance
                avg_confidence = feedback.get('average_confidence', 0)
                max_confidence = max([s.get('confidence', 0) for s in feedback.get('sources', [])]) if feedback.get('sources') else 0
                min_confidence = min([s.get('confidence', 0) for s in feedback.get('sources', [])]) if feedback.get('sources') else 0
                
                st.write(f"**Confiance moyenne:** {avg_confidence:.1f}%")
                st.write(f"**Confiance maximale:** {max_confidence:.1f}%")
                st.write(f"**Longueur réponse:** {feedback['response_length']} caractères")
                st.write(f"**Nombre de sources:** {feedback.get('source_count', 0)}")
                
                # Indicateur de qualité
                if max_confidence >= 80:
                    st.success("Haute qualité (confiance > 80%)")
                elif max_confidence >= 50:
                    st.info("Qualité moyenne (confiance 50-80%)")
                else:
                    st.warning("Faible qualité (confiance < 50%)")