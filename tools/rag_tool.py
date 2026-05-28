import logging

logger = logging.getLogger(__name__)

# Mock guideline database — in production this calls your RAG API
MOCK_GUIDELINES = {
    "hypertension": {
        "recommendations": [
            "First-line therapy: ACE inhibitors or ARBs for hypertensive patients with diabetes or CKD.",
            "Thiazide diuretics are recommended as first-line for uncomplicated hypertension.",
            "Target BP < 130/80 mmHg for high-risk patients (ACC/AHA 2023).",
            "Beta-blockers preferred if concurrent ischemic heart disease.",
        ],
        "sources": [
            "ACC/AHA 2023 Hypertension Guidelines",
            "JNC 8 Evidence-Based Guideline",
            "ESC/ESH 2023 Arterial Hypertension Guidelines",
        ],
        "confidence": "high",
    },
    "dyslipidemia": {
        "recommendations": [
            "High-intensity statin therapy for LDL > 190 mg/dL or ASCVD risk > 20%.",
            "Lifestyle modification (diet + exercise) as adjunct to pharmacotherapy.",
            "LDL target < 70 mg/dL for very high cardiovascular risk patients.",
        ],
        "sources": [
            "ACC/AHA 2022 Cholesterol Guidelines",
            "ESC/EAS 2023 Dyslipidaemia Guidelines",
        ],
        "confidence": "high",
    },
    "smoker": {
        "recommendations": [
            "Smoking cessation counseling is mandatory for all smokers.",
            "NRT (nicotine replacement therapy) or varenicline as pharmacotherapy.",
            "Smoking doubles cardiovascular risk — cessation is highest-yield intervention.",
        ],
        "sources": [
            "USPSTF Tobacco Cessation Guidelines 2021",
            "ACC/AHA 2023 Primary Prevention Guidelines",
        ],
        "confidence": "high",
    },
}


class GuidelineRetrieverTool:
    """Calls the RAG Guideline Engine and returns evidence chunks + citations."""

    def run(self, patient_summary: dict, clinical_question: str) -> dict:
        logger.info(f"[RAGTool] Query: {clinical_question}")
        conditions = patient_summary.get("conditions", [])

        recommendations, sources = [], []

        for condition in conditions:
            key = condition.lower()
            if key in MOCK_GUIDELINES:
                entry = MOCK_GUIDELINES[key]
                recommendations.extend(entry["recommendations"])
                sources.extend(entry["sources"])

        # LDL-triggered dyslipidemia check
        ldl = patient_summary.get("ldl", 0)
        if ldl and ldl > 130 and "dyslipidemia" not in conditions:
            entry = MOCK_GUIDELINES["dyslipidemia"]
            recommendations.extend(entry["recommendations"])
            sources.extend(entry["sources"])

        if not recommendations:
            logger.warning("[RAGTool] No guidelines found for given conditions.")
            return {"status": "insufficient_evidence", "recommendations": [], "sources": []}

        return {
            "status": "ok",
            "recommendations": list(dict.fromkeys(recommendations)),  # deduplicate
            "sources": list(dict.fromkeys(sources)),
            "confidence": "high",
        }
