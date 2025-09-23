# utils/performance_monitor.py
from datetime import datetime
import pandas as pd
from typing import Dict, List
import streamlit as st
import json
from pathlib import Path
from threading import Lock

_METRICS_FILE = Path("metrics_store.jsonl")  # JSON lines file, append-only
_LOCK = Lock()

class PerformanceMonitor:
    """Monitor des performances en temps réel, avec persistence locale (jsonl)."""
    def __init__(self, persist_file: Path = _METRICS_FILE):
        self.persist_file = Path(persist_file)
        self.metrics_history: List[Dict] = []
        # charger l'historique persistant au démarrage
        self._load_from_disk()

    def _load_from_disk(self):
        if not self.persist_file.exists():
            return
        try:
            with self.persist_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            self.metrics_history = [json.loads(l) for l in lines if l.strip()]
        except Exception:
            # en cas d'erreur on laisse history vide mais on ne crash pas
            self.metrics_history = []

    def _append_to_disk(self, entry: Dict):
        # thread/process-safe append (simple)
        try:
            with _LOCK:
                with self.persist_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            # ne pas planter l'app si l'écriture échoue
            pass

    def add_metrics(self, metrics: Dict, cached: bool = False):
        """Ajoute des métriques à l'historique et persiste sur disque."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "cached": bool(cached),
            **metrics
        }
        self.metrics_history.append(entry)
        # garder 1000 dernières en mémoire
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        # write to disk for cross-process visibility
        self._append_to_disk(entry)

    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance"""
        if not self.metrics_history:
            return {}
        df = pd.DataFrame(self.metrics_history)
        total_requests = len(df)
        cached_requests = int(df["cached"].sum()) if "cached" in df.columns else 0
        cache_hit_rate = (cached_requests / total_requests * 100) if total_requests > 0 else 0
        # protéger contre colonnes manquantes
        def mean_safe(col):
            return float(df[col].mean()) if col in df.columns and len(df[col].dropna()) > 0 else 0.0

        return {
            "avg_total_time": mean_safe("total_time"),
            "avg_retrieval_time": mean_safe("retrieval_time"),
            "avg_generation_time": mean_safe("generation_time"),
            "cache_hit_rate": cache_hit_rate,
            "total_requests": total_requests,
            "cached_requests": cached_requests,
            "uncached_requests": total_requests - cached_requests
        }

    def get_recent_metrics(self, limit: int = 50) -> List[Dict]:
        """Retourne les métriques les plus récentes"""
        return self.metrics_history[-limit:] if self.metrics_history else []

    def clear_history(self):
        """Vide l'historique des performances (mémoire + fichier)"""
        self.metrics_history = []
        try:
            with _LOCK:
                if self.persist_file.exists():
                    self.persist_file.unlink()
        except Exception:
            pass

    def get_cache_analytics(self) -> Dict:
        """Retourne des analytics détaillés sur le cache"""
        if not self.metrics_history:
            return {}
        df = pd.DataFrame(self.metrics_history)
        hourly_stats = []
        for i in range(24):
            hour_data = df[df['timestamp'].apply(lambda x: datetime.fromisoformat(x).hour == i)]
            if not hour_data.empty:
                hourly_stats.append({
                    'hour': i,
                    'cache_hit_rate': (hour_data['cached'].sum() / len(hour_data)) * 100,
                    'avg_response_time': hour_data['total_time'].mean() if 'total_time' in hour_data.columns else 0
                })
        return {
            'hourly_stats': hourly_stats,
            'peak_usage_hour': max(hourly_stats, key=lambda x: x['cache_hit_rate']) if hourly_stats else None,
            'efficiency_score': (df['cached'].sum() / len(df)) * (1 / df['total_time'].mean()) if len(df) > 0 and 'total_time' in df.columns else 0
        }
