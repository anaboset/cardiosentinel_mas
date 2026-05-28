import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from tools.rag_tool import GuidelineRetrieverTool
from tools.interaction_tool import DrugInteractionTool
from tools.contraindication_tool import ContraindicationChecker
from tools.risk_tool import RiskScoreCalculator


# ── GuidelineRetrieverTool ─────────────────────────────────────────────────────

class TestGuidelineRetrieverTool:
    def setup_method(self):
        self.tool = GuidelineRetrieverTool()

    def test_returns_recommendations_for_known_condition(self):
        result = self.tool.run(
            patient_summary={"conditions": ["hypertension"], "ldl": 100},
            clinical_question="first-line therapy",
        )
        assert result["status"] == "ok"
        assert len(result["recommendations"]) > 0
        assert len(result["sources"]) > 0

    def test_triggers_dyslipidemia_for_high_ldl(self):
        result = self.tool.run(
            patient_summary={"conditions": [], "ldl": 160},
            clinical_question="cholesterol management",
        )
        assert result["status"] == "ok"
        assert any("statin" in r.lower() or "ldl" in r.lower() for r in result["recommendations"])

    def test_returns_insufficient_evidence_for_unknown_condition(self):
        result = self.tool.run(
            patient_summary={"conditions": ["unknown_rare_disease"], "ldl": 90},
            clinical_question="treatment",
        )
        assert result["status"] == "insufficient_evidence"
        assert result["recommendations"] == []

    def test_multiple_conditions_merged(self):
        result = self.tool.run(
            patient_summary={"conditions": ["hypertension", "smoker"], "ldl": 100},
            clinical_question="treatment",
        )
        assert result["status"] == "ok"
        # Should include recommendations for both conditions
        combined = " ".join(result["recommendations"]).lower()
        assert "smoking" in combined or "cessation" in combined
        assert "thiazide" in combined or "ace" in combined

    def test_deduplicates_sources(self):
        result = self.tool.run(
            patient_summary={"conditions": ["hypertension", "hypertension"], "ldl": 100},
            clinical_question="treatment",
        )
        assert len(result["sources"]) == len(set(result["sources"]))


# ── DrugInteractionTool ────────────────────────────────────────────────────────

class TestDrugInteractionTool:
    def setup_method(self):
        self.tool = DrugInteractionTool()

    def test_detects_known_interaction(self):
        result = self.tool.run(["warfarin", "aspirin"])
        assert result["interactions_found"] is True
        assert len(result["warnings"]) == 1
        assert "bleeding" in result["warnings"][0].lower()

    def test_detects_reverse_pair(self):
        # Order shouldn't matter
        result = self.tool.run(["aspirin", "warfarin"])
        assert result["interactions_found"] is True

    def test_no_interaction_for_safe_combo(self):
        result = self.tool.run(["ace_inhibitor", "thiazide"])
        assert result["interactions_found"] is False
        assert result["warnings"] == []

    def test_single_drug_no_interaction(self):
        result = self.tool.run(["statin"])
        assert result["interactions_found"] is False

    def test_empty_list(self):
        result = self.tool.run([])
        assert result["interactions_found"] is False
        assert result["warnings"] == []

    def test_multiple_interactions_detected(self):
        result = self.tool.run(["warfarin", "aspirin", "statin", "fibrate"])
        assert result["interactions_found"] is True
        assert len(result["warnings"]) >= 2


# ── ContraindicationChecker ────────────────────────────────────────────────────

class TestContraindicationChecker:
    def setup_method(self):
        self.tool = ContraindicationChecker()

    def test_flags_asthma_with_beta_blocker(self):
        result = self.tool.run(
            conditions=["asthma"],
            proposed_medications=["beta_blocker"],
        )
        assert result["contraindications_found"] is True
        assert any("beta_blocker" in f.lower() for f in result["flags"])

    def test_flags_pregnancy_with_ace_inhibitor(self):
        result = self.tool.run(
            conditions=["pregnancy"],
            proposed_medications=["ace_inhibitor", "metformin"],
        )
        assert result["contraindications_found"] is True
        assert any("ace_inhibitor" in f for f in result["flags"])

    def test_no_flag_for_safe_combo(self):
        result = self.tool.run(
            conditions=["hypertension"],
            proposed_medications=["ace_inhibitor"],
        )
        assert result["contraindications_found"] is False
        assert result["flags"] == []

    def test_empty_inputs(self):
        result = self.tool.run(conditions=[], proposed_medications=[])
        assert result["contraindications_found"] is False

    def test_unknown_condition_no_flag(self):
        result = self.tool.run(
            conditions=["unknown_condition"],
            proposed_medications=["statin"],
        )
        assert result["contraindications_found"] is False


# ── RiskScoreCalculator ────────────────────────────────────────────────────────

class TestRiskScoreCalculator:
    def setup_method(self):
        self.tool = RiskScoreCalculator()

    def test_very_high_risk_patient(self):
        result = self.tool.run({
            "age": 70, "bp": "165/100", "ldl": 200,
            "conditions": ["smoker", "diabetes"],
        })
        assert result["classification"] == "Very High"
        assert result["score"] >= 60

    def test_low_risk_patient(self):
        result = self.tool.run({
            "age": 35, "bp": "118/75", "ldl": 100,
            "conditions": [],
        })
        assert result["classification"] == "Low"
        assert result["score"] < 20

    def test_score_capped_at_100(self):
        result = self.tool.run({
            "age": 80, "bp": "180/110", "ldl": 250,
            "conditions": ["smoker", "diabetes", "ckd"],
        })
        assert result["score"] <= 100

    def test_factors_list_populated(self):
        result = self.tool.run({
            "age": 65, "bp": "150/95", "ldl": 160,
            "conditions": ["smoker"],
        })
        assert len(result["factors"]) > 0

    def test_smoker_adds_to_score(self):
        base = self.tool.run({"age": 50, "bp": "120/80", "ldl": 100, "conditions": []})
        with_smoking = self.tool.run({"age": 50, "bp": "120/80", "ldl": 100, "conditions": ["smoker"]})
        assert with_smoking["score"] > base["score"]

    def test_classification_moderate(self):
        result = self.tool.run({
            "age": 50, "bp": "135/85", "ldl": 135,
            "conditions": [],
        })
        assert result["classification"] in ("Low", "Moderate")
