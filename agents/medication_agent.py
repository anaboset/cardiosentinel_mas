import logging
from tools.interaction_tool import DrugInteractionTool
from tools.contraindication_tool import ContraindicationChecker
from schemas.outputs import MedicationSafetyOutput

logger = logging.getLogger(__name__)

# Medications inferred from common hypertension/dyslipidemia guidelines
CONDITION_TO_MEDS = {
    "hypertension": ["ace_inhibitor", "thiazide", "arb", "beta_blocker"],
    "dyslipidemia": ["statin"],
    "smoker": ["varenicline"],
    "diabetes": ["metformin"],
    "smoking": ["varenicline"],
}


class MedicationAgent:
    """Checks drug interactions and contraindications for inferred medications."""

    def __init__(self):
        self.interaction_tool = DrugInteractionTool()
        self.contraindication_tool = ContraindicationChecker()

    def _infer_medications(self, patient: dict) -> list:
        """Infer medications from patient conditions."""
        meds = []
        for condition in patient.get("conditions", []):
            key = condition.lower()
            meds.extend(CONDITION_TO_MEDS.get(key, []))
        
        # Add explicitly listed medications
        if patient.get("medications"):
            meds.extend([m.lower().replace(" ", "_") for m in patient.get("medications", [])])
        
        return list(set(meds))

    def run(self, patient: dict) -> MedicationSafetyOutput:
        """Run the medication agent and return safety output."""
        logger.info("[MedicationAgent] Running safety checks...")
        try:
            meds = self._infer_medications(patient)
            logger.info(f"[MedicationAgent] Inferred medications: {meds}")

            interaction_result = self.interaction_tool.run(meds)
            contraindication_result = self.contraindication_tool.run(
                conditions=patient.get("conditions", []),
                proposed_medications=meds,
            )

            safe = (
                not interaction_result["interactions_found"]
                and not contraindication_result["contraindications_found"]
            )

            return MedicationSafetyOutput(
                interactions=interaction_result["warnings"],
                contraindications=contraindication_result["flags"],
                safe_to_proceed=safe,
            )

        except Exception as e:
            logger.error(f"[MedicationAgent] Tool failed: {e}")
            return MedicationSafetyOutput(
                interactions=[],
                contraindications=[],
                safe_to_proceed=False,
            )
