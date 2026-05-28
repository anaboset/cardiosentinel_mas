import logging

logger = logging.getLogger(__name__)

# (drug_a, drug_b) → warning message
INTERACTION_DB = {
    ("warfarin", "aspirin"): "Increased bleeding risk — avoid combination or monitor closely.",
    ("ace_inhibitor", "potassium_supplement"): "Risk of hyperkalemia — monitor serum potassium.",
    ("statin", "fibrate"): "Risk of myopathy/rhabdomyolysis — use with caution.",
    ("beta_blocker", "verapamil"): "Severe bradycardia and AV block risk — avoid combination.",
    ("thiazide", "lithium"): "Thiazides reduce lithium clearance — risk of lithium toxicity.",
    ("ssri", "tramadol"): "Serotonin syndrome risk — avoid combination.",
}


class DrugInteractionTool:
    """Checks for known drug-drug interactions."""

    def run(self, medications: list) -> dict:
        logger.info(f"[DrugInteractionTool] Checking: {medications}")
        meds = [m.lower().replace(" ", "_") for m in medications]
        warnings = []

        for i, drug_a in enumerate(meds):
            for drug_b in meds[i + 1 :]:
                pair = (drug_a, drug_b)
                pair_rev = (drug_b, drug_a)
                if pair in INTERACTION_DB:
                    warnings.append(f"{drug_a} + {drug_b}: {INTERACTION_DB[pair]}")
                elif pair_rev in INTERACTION_DB:
                    warnings.append(f"{drug_b} + {drug_a}: {INTERACTION_DB[pair_rev]}")

        return {
            "interactions_found": len(warnings) > 0,
            "warnings": warnings,
        }
