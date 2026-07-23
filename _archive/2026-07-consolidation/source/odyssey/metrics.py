"""
Success metrics and measurement models for strategic initiatives.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SuccessMetric(BaseModel):
    """Defines how success will be measured."""
    metric_name: str = Field(..., description="Name of the success metric")
    target_value: Optional[str] = Field(None, description="Target value or range")
    measurement_method: Optional[str] = Field(None, description="How this will be measured")
    timeline: Optional[str] = Field(None, description="When this should be achieved")
    is_primary: bool = Field(False, description="Whether this is a primary success indicator")
    baseline_value: Optional[str] = Field(None, description="Current baseline value")
    measurement_frequency: str = Field("monthly", description="How often to measure this metric")
    
    def is_on_track(self, current_value: str) -> bool:
        """Simple check if metric is progressing toward target."""
        # This is a placeholder - actual logic would depend on metric type
        return current_value != self.baseline_value


class MetricsDashboard(BaseModel):
    """Collection of metrics organized for tracking and reporting."""
    primary_metrics: List[SuccessMetric] = Field(default_factory=list)
    secondary_metrics: List[SuccessMetric] = Field(default_factory=list)
    leading_indicators: List[SuccessMetric] = Field(default_factory=list)
    lagging_indicators: List[SuccessMetric] = Field(default_factory=list)

    last_updated: datetime = Field(default_factory=datetime.utcnow)
    measurement_cadence: Dict[str, str] = Field(default_factory=dict)
    
    def get_all_metrics(self) -> List[SuccessMetric]:
        """Return all metrics combined."""
        return (self.primary_metrics + self.secondary_metrics + 
                self.leading_indicators + self.lagging_indicators)
    
    def get_metrics_by_frequency(self, frequency: str) -> List[SuccessMetric]:
        """Return metrics filtered by measurement frequency."""
        return [m for m in self.get_all_metrics() if m.measurement_frequency == frequency]
    
    def update_metric(self, metric_name: str, new_value: str) -> bool:
        """Update a metric's current value and return success status."""
        for metric in self.get_all_metrics():
            if metric.metric_name == metric_name:
                metric.baseline_value = new_value
                self.last_updated = datetime.utcnow()
                return True
        return False
