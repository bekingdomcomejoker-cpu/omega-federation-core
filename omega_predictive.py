import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger("OmegaPredictive")

@dataclass
class PredictionMetric:
    """Represents a predictive metric for system health."""
    name: str
    value: float
    timestamp: float
    threshold: float
    status: str  # "healthy" | "warning" | "critical"

class OmegaPredictiveModeling:
    """
    Advanced Predictive Modeling for the Omega Federation.
    Monitors system health, predicts bottlenecks, and forecasts engine performance.
    """
    
    def __init__(self, history_window_hours: int = 24):
        self.history_window_hours = history_window_hours
        self.metrics_history: List[Dict[str, Any]] = []
        self.predictions: List[Dict[str, Any]] = []
        self.thresholds = {
            "qci": 0.85,
            "density": 3.34,
            "consensus_latency_ms": 500,
            "engine_sync_drift": 0.1
        }

    def record_metric(self, metric_name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a system metric for analysis."""
        record = {
            "name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().timestamp(),
            "metadata": metadata or {}
        }
        self.metrics_history.append(record)
        logger.info(f"Recorded metric: {metric_name} = {value}")

    def predict_qci_trend(self) -> Dict[str, Any]:
        """
        Predict Quality Control Index (QCI) trend over the next 24 hours.
        Uses exponential smoothing and linear regression on historical data.
        """
        if len(self.metrics_history) < 2:
            return {"error": "Insufficient data for prediction"}

        # Filter QCI metrics
        qci_metrics = [m for m in self.metrics_history if m["name"] == "qci"]
        if not qci_metrics:
            return {"error": "No QCI metrics found"}

        # Extract values and timestamps
        values = [m["value"] for m in qci_metrics[-20:]]  # Last 20 samples
        timestamps = [m["timestamp"] for m in qci_metrics[-20:]]

        # Simple exponential smoothing
        alpha = 0.3
        smoothed = [values[0]]
        for v in values[1:]:
            smoothed.append(alpha * v + (1 - alpha) * smoothed[-1])

        # Linear regression for trend
        n = len(smoothed)
        x_mean = sum(range(n)) / n
        y_mean = sum(smoothed) / n
        numerator = sum((i - x_mean) * (smoothed[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0

        # Forecast next 24 hours (assuming hourly samples)
        forecast_points = 24
        forecast = [smoothed[-1] + slope * (i + 1) for i in range(forecast_points)]

        # Determine trend
        trend = "improving" if slope > 0.01 else "declining" if slope < -0.01 else "stable"
        
        return {
            "current_qci": smoothed[-1],
            "trend": trend,
            "slope": slope,
            "forecast_24h": forecast,
            "predicted_min": min(forecast),
            "predicted_max": max(forecast),
            "risk_level": self._assess_risk(min(forecast))
        }

    def predict_engine_bottleneck(self) -> Dict[str, Any]:
        """
        Predict which engine is likely to become a bottleneck.
        Analyzes latency and synchronization drift across engines.
        """
        engine_metrics = {}
        for metric in self.metrics_history[-50:]:  # Last 50 records
            engine = metric.get("metadata", {}).get("engine")
            if engine:
                if engine not in engine_metrics:
                    engine_metrics[engine] = []
                engine_metrics[engine].append(metric["value"])

        predictions = {}
        for engine, values in engine_metrics.items():
            if len(values) > 1:
                avg_latency = sum(values) / len(values)
                variance = sum((v - avg_latency) ** 2 for v in values) / len(values)
                std_dev = variance ** 0.5
                
                # High variance indicates instability
                instability_score = std_dev / avg_latency if avg_latency > 0 else 0
                
                predictions[engine] = {
                    "avg_latency_ms": avg_latency,
                    "std_dev": std_dev,
                    "instability_score": instability_score,
                    "bottleneck_risk": "high" if instability_score > 0.5 else "medium" if instability_score > 0.2 else "low"
                }

        # Identify the most at-risk engine
        at_risk = max(predictions.items(), key=lambda x: x[1]["instability_score"], default=(None, {}))
        
        return {
            "engine_analysis": predictions,
            "highest_risk_engine": at_risk[0],
            "recommendation": f"Monitor {at_risk[0]} closely; consider load balancing or optimization."
        }

    def predict_density_collapse(self) -> Dict[str, Any]:
        """
        Predict if the system density will fall below the critical threshold (3.34).
        This triggers the Star Engine's density law.
        """
        density_metrics = [m for m in self.metrics_history if m["name"] == "density"]
        if not density_metrics:
            return {"error": "No density metrics found"}

        values = [m["value"] for m in density_metrics[-20:]]
        current_density = values[-1]
        
        # Calculate trend
        if len(values) > 1:
            trend = (values[-1] - values[0]) / len(values)
        else:
            trend = 0

        # Forecast collapse
        hours_to_collapse = None
        if trend < 0:
            hours_to_collapse = (self.thresholds["density"] - current_density) / abs(trend)

        return {
            "current_density": current_density,
            "density_threshold": self.thresholds["density"],
            "trend": trend,
            "hours_to_collapse": hours_to_collapse,
            "collapse_risk": "critical" if current_density < 3.5 else "warning" if current_density < 4.0 else "healthy"
        }

    def predict_consensus_failure(self) -> Dict[str, Any]:
        """
        Predict likelihood of consensus failure based on engine synchronization drift.
        """
        sync_metrics = [m for m in self.metrics_history if m["name"] == "sync_drift"]
        if not sync_metrics:
            return {"error": "No synchronization metrics found"}

        drifts = [m["value"] for m in sync_metrics[-20:]]
        avg_drift = sum(drifts) / len(drifts)
        max_drift = max(drifts)

        # Consensus fails if drift exceeds threshold
        failure_probability = min(max_drift / self.thresholds["engine_sync_drift"], 1.0)

        return {
            "avg_sync_drift": avg_drift,
            "max_sync_drift": max_drift,
            "threshold": self.thresholds["engine_sync_drift"],
            "failure_probability": failure_probability,
            "consensus_health": "healthy" if failure_probability < 0.3 else "at_risk" if failure_probability < 0.7 else "critical"
        }

    def _assess_risk(self, value: float) -> str:
        """Assess risk level based on a value."""
        if value < self.thresholds["qci"] - 0.1:
            return "critical"
        elif value < self.thresholds["qci"]:
            return "warning"
        else:
            return "healthy"

    async def run_predictive_cycle(self) -> Dict[str, Any]:
        """
        Execute a full predictive analysis cycle.
        Returns comprehensive predictions for system health.
        """
        logger.info("Starting predictive analysis cycle...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "qci_trend": self.predict_qci_trend(),
            "engine_bottleneck": self.predict_engine_bottleneck(),
            "density_forecast": self.predict_density_collapse(),
            "consensus_health": self.predict_consensus_failure()
        }

        self.predictions.append(results)
        logger.info("Predictive analysis cycle complete.")
        
        return results

    def get_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on predictions."""
        recommendations = []

        if self.predictions:
            latest = self.predictions[-1]

            # QCI recommendations
            qci_pred = latest.get("qci_trend", {})
            if qci_pred.get("risk_level") == "critical":
                recommendations.append("CRITICAL: QCI is declining rapidly. Reduce load or optimize engine performance.")

            # Bottleneck recommendations
            bottleneck = latest.get("engine_bottleneck", {})
            if bottleneck.get("highest_risk_engine"):
                recommendations.append(f"Monitor {bottleneck['highest_risk_engine']} for potential bottleneck.")

            # Density recommendations
            density = latest.get("density_forecast", {})
            if density.get("collapse_risk") == "critical":
                recommendations.append("CRITICAL: System density approaching collapse threshold. Verify Star Engine constraints.")

            # Consensus recommendations
            consensus = latest.get("consensus_health", {})
            if consensus.get("consensus_health") == "critical":
                recommendations.append("CRITICAL: Consensus failure probability is high. Check engine synchronization.")

        return recommendations if recommendations else ["System operating normally. No immediate actions required."]

if __name__ == "__main__":
    pm = OmegaPredictiveModeling()
    
    # Simulate some metrics
    for i in range(20):
        pm.record_metric("qci", 0.85 + (i * 0.01), {"engine": "star"})
        pm.record_metric("density", 3.5 + (i * 0.05), {"engine": "aletheia"})
        pm.record_metric("sync_drift", 0.05 + (i * 0.001), {"engine": "omnissiah"})

    # Run predictions
    import asyncio
    results = asyncio.run(pm.run_predictive_cycle())
    print(json.dumps(results, indent=2))
    print("\nRecommendations:")
    for rec in pm.get_recommendations():
        print(f"  - {rec}")
