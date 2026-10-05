"""
Janseva AI — Priority Scoring Engine
Transparent, rule-based priority calculation using real data signals.
"""
import structlog
from typing import Optional, List
from app.models.schemas import PriorityLevel, SeverityLevel

logger = structlog.get_logger()

# Priority score weights (configurable)
WEIGHTS = {
    "safety_risk": 25,
    "severity": 20,
    "affected_population": 15,
    "critical_infrastructure": 10,
    "duration": 10,
    "vulnerable_location": 10,
    "sla_pressure": 5,
    "complaint_volume": 5,
}

# Score thresholds for priority levels
THRESHOLDS = {
    "critical": 80,
    "high": 60,
    "medium": 35,
    "low": 0,
}


class PriorityEngine:
    """
    Calculates transparent priority scores from real data signals.
    Never uses arbitrary LLM-assigned priority — all factors are weighted and traceable.
    """

    def calculate(
        self,
        safety_risk: bool = False,
        severity: Optional[SeverityLevel] = None,
        estimated_affected_population: Optional[int] = None,
        critical_infrastructure: bool = False,
        duration_days: Optional[float] = None,
        near_vulnerable_location: bool = False,
        sla_remaining_percent: Optional[float] = None,
        complaint_count: int = 1,
        historical_recurrence: int = 0,
    ) -> dict:
        """
        Calculate priority score from real signals.

        Returns:
            {
                "priority_score": float (0-100),
                "priority_level": PriorityLevel,
                "reason_codes": list of human-readable reasons
            }
        """
        score = 0.0
        reasons: List[str] = []

        # ── Safety Risk ──────────────────────────────────────────────────
        if safety_risk:
            score += WEIGHTS["safety_risk"]
            reasons.append("Immediate safety risk identified")

        # ── Severity ─────────────────────────────────────────────────────
        severity_scores = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.MAJOR: 0.75,
            SeverityLevel.MODERATE: 0.4,
            SeverityLevel.MINOR: 0.15,
        }
        if severity:
            sev_score = severity_scores.get(severity, 0.4)
            score += WEIGHTS["severity"] * sev_score
            if sev_score >= 0.75:
                reasons.append(f"Severity: {severity.value}")

        # ── Affected Population ──────────────────────────────────────────
        if estimated_affected_population:
            if estimated_affected_population >= 1000:
                pop_factor = 1.0
            elif estimated_affected_population >= 500:
                pop_factor = 0.8
            elif estimated_affected_population >= 100:
                pop_factor = 0.5
            elif estimated_affected_population >= 20:
                pop_factor = 0.3
            else:
                pop_factor = 0.1
            score += WEIGHTS["affected_population"] * pop_factor
            if pop_factor >= 0.5:
                reasons.append(f"~{estimated_affected_population} residents affected")

        # ── Critical Infrastructure ──────────────────────────────────────
        if critical_infrastructure:
            score += WEIGHTS["critical_infrastructure"]
            reasons.append("Critical infrastructure affected")

        # ── Duration ─────────────────────────────────────────────────────
        if duration_days is not None:
            if duration_days >= 7:
                dur_factor = 1.0
            elif duration_days >= 3:
                dur_factor = 0.7
            elif duration_days >= 1:
                dur_factor = 0.4
            else:
                dur_factor = 0.15
            score += WEIGHTS["duration"] * dur_factor
            if dur_factor >= 0.7:
                reasons.append(f"Issue persisting for {duration_days:.0f}+ days")

        # ── Vulnerable Location ──────────────────────────────────────────
        if near_vulnerable_location:
            score += WEIGHTS["vulnerable_location"]
            reasons.append("Near school, hospital, or vulnerable area")

        # ── SLA Pressure ─────────────────────────────────────────────────
        if sla_remaining_percent is not None:
            if sla_remaining_percent <= 10:
                sla_factor = 1.0
                reasons.append("SLA deadline imminent")
            elif sla_remaining_percent <= 30:
                sla_factor = 0.7
            elif sla_remaining_percent <= 50:
                sla_factor = 0.4
            else:
                sla_factor = 0.1
            score += WEIGHTS["sla_pressure"] * sla_factor

        # ── Complaint Volume ─────────────────────────────────────────────
        if complaint_count > 1:
            if complaint_count >= 10:
                vol_factor = 1.0
            elif complaint_count >= 5:
                vol_factor = 0.7
            elif complaint_count >= 3:
                vol_factor = 0.4
            else:
                vol_factor = 0.2
            score += WEIGHTS["complaint_volume"] * vol_factor
            if complaint_count >= 3:
                reasons.append(f"{complaint_count} complaints about this issue")

        # ── Historical Recurrence Bonus ──────────────────────────────────
        if historical_recurrence >= 3:
            score += 5
            reasons.append(f"Recurring issue ({historical_recurrence} prior occurrences)")

        # Clamp to 0-100
        score = max(0, min(100, score))

        # Determine priority level
        if score >= THRESHOLDS["critical"]:
            level = PriorityLevel.CRITICAL
        elif score >= THRESHOLDS["high"]:
            level = PriorityLevel.HIGH
        elif score >= THRESHOLDS["medium"]:
            level = PriorityLevel.MEDIUM
        else:
            level = PriorityLevel.LOW

        if not reasons:
            reasons.append("Standard priority based on available signals")

        result = {
            "priority_score": round(score, 2),
            "priority_level": level,
            "reason_codes": reasons,
        }

        logger.info(
            "priority_calculated",
            score=result["priority_score"],
            level=result["priority_level"].value,
            reasons=reasons,
        )

        return result


def parse_duration_to_days(duration_str: Optional[str]) -> Optional[float]:
    """Parse a human-readable duration string to days."""
    if not duration_str:
        return None

    duration_str = duration_str.lower().strip()

    try:
        if "week" in duration_str:
            num = float("".join(c for c in duration_str.split("week")[0] if c.isdigit() or c == ".") or "1")
            return num * 7
        elif "day" in duration_str:
            num = float("".join(c for c in duration_str.split("day")[0] if c.isdigit() or c == ".") or "1")
            return num
        elif "hour" in duration_str:
            num = float("".join(c for c in duration_str.split("hour")[0] if c.isdigit() or c == ".") or "1")
            return num / 24
        elif "month" in duration_str:
            num = float("".join(c for c in duration_str.split("month")[0] if c.isdigit() or c == ".") or "1")
            return num * 30
        elif "year" in duration_str:
            num = float("".join(c for c in duration_str.split("year")[0] if c.isdigit() or c == ".") or "1")
            return num * 365
    except (ValueError, IndexError):
        pass

    return None


# Singleton
_priority_engine: Optional[PriorityEngine] = None


def get_priority_engine() -> PriorityEngine:
    global _priority_engine
    if _priority_engine is None:
        _priority_engine = PriorityEngine()
    return _priority_engine


def compute_priority_score(
    safety_risk: bool = False,
    severity: Optional[SeverityLevel] = None,
    severity_score: Optional[float] = None,
    urgency_score: Optional[float] = None,
    impact_score: Optional[float] = None,
    hazard_risk_score: Optional[float] = None,
    vulnerability_score: Optional[float] = None,
    confidence_score: Optional[float] = None,
    duplicate_count: int = 1,
    **kwargs,
) -> dict:
    """Convenience helper function for priority scoring."""
    engine = get_priority_engine()
    sev = severity
    if sev is None and severity_score is not None:
        if severity_score >= 80:
            sev = SeverityLevel.CRITICAL
        elif severity_score >= 60:
            sev = SeverityLevel.MAJOR
        elif severity_score >= 35:
            sev = SeverityLevel.MODERATE
        else:
            sev = SeverityLevel.MINOR

    is_safety_risk = safety_risk or (hazard_risk_score is not None and hazard_risk_score > 70)
    is_critical_infra = (hazard_risk_score is not None and hazard_risk_score >= 80)
    
    affected_pop = None
    if impact_score is not None:
        affected_pop = int(impact_score * 20)

    duration_days = None
    if urgency_score is not None and urgency_score >= 80:
        duration_days = 7.0

    return engine.calculate(
        safety_risk=is_safety_risk,
        severity=sev,
        critical_infrastructure=is_critical_infra,
        estimated_affected_population=affected_pop,
        duration_days=duration_days,
        complaint_count=duplicate_count,
        near_vulnerable_location=(vulnerability_score is not None and vulnerability_score > 50),
    )

