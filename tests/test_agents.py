import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
from agents.guideline_agent import GuidelineAgent
from agents.medication_agent import MedicationAgent
from agents.risk_agent import RiskAgent
from agents.patient_agent import PatientAgent
from schemas.outputs import GuidelineOutput, RiskOutput


PATIENT = {
    "age": 65,
    "bp": "150/95",
    "ldl": 160,
    "conditions": ["hypertension", "smoker"],
}


# ── GuidelineAgent ─────────────────────────────────────────────────────────────

class TestGuidelineAgent:
    def setup_method(self):
        self.agent = GuidelineAgent()

    def test_returns_guideline_output_on_success(self):
        result = self.agent.run(PATIENT, "first-line therapy")
        assert isinstance(result, GuidelineOutput)
        assert len(result.recommendations) > 0
        assert len(result.evidence_sources) > 0
        assert result.confidence in ("low", "moderate", "high")

    def test_returns_insufficient_evidence_for_unknown(self):
        patient = {"conditions": ["unknown_disease"], "ldl": 90}
        result = self.agent.run(patient, "treatment")
        assert result.recommendations == ["insufficient_evidence"]
        assert result.confidence == "none"

    def test_abstains_on_tool_exception(self):
        with patch.object(self.agent.tool, "run", side_effect=Exception("RAG down")):
            result = self.agent.run(PATIENT, "treatment")
        assert result.recommendations == ["insufficient_evidence"]
        assert result.confidence == "none"


# ── MedicationAgent ────────────────────────────────────────────────────────────

class TestMedicationAgent:
    def setup_method(self):
        self.agent = MedicationAgent()

    def test_returns_medication_safety_output(self):
        from schemas.outputs import MedicationSafetyOutput
        result = self.agent.run(PATIENT)
        assert isinstance(result, MedicationSafetyOutput)
        assert isinstance(result.safe_to_proceed, bool)
        assert isinstance(result.interactions, list)
        assert isinstance(result.contraindications, list)

    def test_safe_for_standard_hypertension_patient(self):
        result = self.agent.run(PATIENT)
        # Standard hypertension meds should not interact with each other by default
        assert result.safe_to_proceed is True

    def test_flags_dangerous_combination(self):
        # Asthma + beta_blocker is contraindicated
        patient = {**PATIENT, "conditions": ["asthma", "hypertension"]}
        result = self.agent.run(patient)
        assert result.safe_to_proceed is False
        assert len(result.contraindications) > 0

    def test_abstains_on_tool_exception(self):
        with patch.object(self.agent.interaction_tool, "run", side_effect=Exception("DB error")):
            result = self.agent.run(PATIENT)
        assert result.safe_to_proceed is False

    def test_infers_medications_from_conditions(self):
        meds = self.agent._infer_medications({"conditions": ["hypertension", "smoker"]})
        assert isinstance(meds, list)
        assert len(meds) > 0

    def test_empty_conditions_gives_empty_meds(self):
        meds = self.agent._infer_medications({"conditions": []})
        assert meds == []


# ── RiskAgent ──────────────────────────────────────────────────────────────────

class TestRiskAgent:
    def setup_method(self):
        self.agent = RiskAgent()

    def test_returns_risk_output(self):
        result = self.agent.run(PATIENT)
        assert isinstance(result, RiskOutput)
        assert result.score >= 0
        assert result.classification in ("Low", "Moderate", "High", "Very High")

    def test_very_high_risk_for_example_patient(self):
        result = self.agent.run(PATIENT)
        assert result.classification == "Very High"

    def test_low_risk_young_healthy_patient(self):
        patient = {"age": 30, "bp": "115/75", "ldl": 95, "conditions": []}
        result = self.agent.run(patient)
        assert result.classification == "Low"

    def test_abstains_on_tool_exception(self):
        with patch.object(self.agent.tool, "run", side_effect=Exception("tool error")):
            result = self.agent.run(PATIENT)
        assert result.classification == "Unknown"
        assert result.score == 0.0

    def test_factors_match_patient_profile(self):
        result = self.agent.run(PATIENT)
        factors_text = " ".join(result.factors).lower()
        assert "smoker" in factors_text or "smoking" in factors_text
        assert "65" in factors_text or "age" in factors_text


# ── PatientAgent ───────────────────────────────────────────────────────────────

class TestPatientAgent:
    def setup_method(self):
        self.agent = PatientAgent()
        self.guidelines = GuidelineOutput(
            recommendations=["Take ACE inhibitor daily.", "Quit smoking."],
            evidence_sources=["ACC/AHA 2023"],
            confidence="high",
        )
        self.risk = RiskOutput(score=72, classification="Very High", factors=["Age 65", "Smoker"])

    def test_returns_patient_output_on_success(self):
        mock_response = '{"summary": "You have high blood pressure.", "lifestyle_advice": ["Exercise daily.", "Quit smoking."]}'
        with patch.object(self.agent, "_call_claude", return_value=mock_response):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        assert result.summary == "You have high blood pressure."
        assert "Exercise daily." in result.lifestyle_advice

    def test_abstains_gracefully_on_api_failure(self):
        with patch.object(self.agent, "_call_claude", side_effect=Exception("401 Unauthorized")):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        assert result.summary == "Unable to generate patient summary."
        assert result.lifestyle_advice == []

    def test_handles_malformed_json_response(self):
        with patch.object(self.agent, "_call_claude", return_value="not valid json"):
            result = self.agent.run(PATIENT, self.guidelines, self.risk)
        # Should not raise — falls back to raw text
        assert isinstance(result.summary, str)

    def test_prompt_includes_patient_data(self):
        prompt = self.agent._build_prompt(PATIENT, self.guidelines, self.risk)
        assert "65" in prompt
        assert "150/95" in prompt
        assert "160" in prompt
        assert "Very High" in prompt
