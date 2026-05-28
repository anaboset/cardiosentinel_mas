import logging

logger = logging.getLogger(__name__)

# condition → medications to avoid
CONTRAINDICATION_DB = {
    "hyperkalemia": ["ace_inhibitor", "arb", "potassium_supplement"],
    "bilateral_renal_artery_stenosis": ["ace_inhibitor", "arb"],
    "asthma": ["beta_blocker", "nsaid"],
    "gout": ["thiazide"],
    "pregnancy": ["ace_inhibitor", "arb", "statin", "warfarin"],
    "liver_disease": ["statin"],
    "bradycardia": ["beta_blocker", "verapamil", "diltiazem"],
}


class ContraindicationChecker:
    """Flags medications contraindicated given patient conditions."""

    def run(self, conditions: list, proposed_medications: list) -> dict:
        logger.info(f"[ContraindicationChecker] Conditions: {conditions}, Meds: {proposed_medications}")
        conditions_clean = [c.lower().replace(" ", "_") for c in conditions]
        meds_clean = [m.lower().replace(" ", "_") for m in proposed_medications]
        flags = []

        for condition in conditions_clean:
            if condition in CONTRAINDICATION_DB:
                blocked = CONTRAINDICATION_DB[condition]
                for med in meds_clean:
                    if med in blocked:
                        flags.append(
                            f"CONTRAINDICATED: {med} is contraindicated in {condition}."
                        )

        return {
            "contraindications_found": len(flags) > 0,
            "flags": flags,
        }
