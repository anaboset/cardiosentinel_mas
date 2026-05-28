import logging

logger = logging.getLogger(__name__)


class RiskScoreCalculator:
    """
    Simplified cardiovascular risk scoring (Framingham-inspired, mock logic).
    Score 0–100 → Low / Moderate / High / Very High.
    """

    def run(self, patient: dict) -> dict:
        logger.info("[RiskScoreCalculator] Calculating risk score.")
        score = 0
        factors = []

        age = patient.get("age", 0)
        if age >= 65:
            score += 25
            factors.append(f"Age {age} (≥65 years)")
        elif age >= 55:
            score += 15
            factors.append(f"Age {age} (55–64 years)")

        bp = patient.get("bp", "120/80")
        systolic = int(bp.split("/")[0])
        if systolic >= 160:
            score += 25
            factors.append(f"Severe hypertension (SBP {systolic})")
        elif systolic >= 140:
            score += 15
            factors.append(f"Stage 2 hypertension (SBP {systolic})")
        elif systolic >= 130:
            score += 8
            factors.append(f"Stage 1 hypertension (SBP {systolic})")

        ldl = patient.get("ldl", 0)
        if ldl >= 190:
            score += 20
            factors.append(f"Very high LDL ({ldl} mg/dL)")
        elif ldl >= 160:
            score += 12
            factors.append(f"High LDL ({ldl} mg/dL)")
        elif ldl >= 130:
            score += 6
            factors.append(f"Borderline LDL ({ldl} mg/dL)")

        conditions = [c.lower() for c in patient.get("conditions", [])]
        if "smoker" in conditions:
            score += 20
            factors.append("Active smoker")
        if "diabetes" in conditions:
            score += 15
            factors.append("Diabetes mellitus")
        if "ckd" in conditions:
            score += 10
            factors.append("Chronic kidney disease")

        score = min(score, 100)

        if score < 20:
            classification = "Low"
        elif score < 40:
            classification = "Moderate"
        elif score < 60:
            classification = "High"
        else:
            classification = "Very High"

        return {
            "score": score,
            "classification": classification,
            "factors": factors,
        }
