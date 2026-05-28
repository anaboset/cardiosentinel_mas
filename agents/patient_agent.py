import json
import logging
from groq import Groq
from schemas.outputs import GuidelineOutput, RiskOutput, PatientOutput
from config import MODEL_NAME
import os

logger = logging.getLogger(__name__)


class PatientAgent:
    """Converts clinical findings into plain-language patient communication."""

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def run(
        self,
        patient: dict,
        guidelines: GuidelineOutput,
        risk: RiskOutput,
    ) -> PatientOutput:
        """Run the patient agent and return patient-friendly output."""
        logger.info("[PatientAgent] Generating patient communication...")
        try:
            prompt = self._build_prompt(patient, guidelines, risk)
            response_text = self._call_claude(prompt)
            return self._parse_response(response_text)
        except Exception as e:
            logger.error(f"[PatientAgent] Failed: {e}")
            return PatientOutput(
                summary="Unable to generate patient summary.",
                lifestyle_advice=[],
            )

    def _build_prompt(self, patient: dict, guidelines: GuidelineOutput, risk: RiskOutput) -> str:
        """Build the prompt for Claude."""
        recs = "\n".join(f"- {r}" for r in guidelines.recommendations[:4])
        return f"""You are a patient educator. A patient has the following profile:
- Age: {patient.get('age')}
- Blood pressure: {patient.get('bp')}
- LDL cholesterol: {patient.get('ldl')} mg/dL
- Conditions: {', '.join(patient.get('conditions', []))}
- Cardiovascular risk: {risk.classification} ({risk.score}/100)

Clinical guidelines recommend:
{recs}

Write a SHORT, friendly explanation (2–3 sentences) the patient can understand, 
then list 3–4 specific lifestyle tips.

Respond ONLY with valid JSON, no markdown:
{{"summary": "...", "lifestyle_advice": ["...", "...", "..."]}}"""

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with proper SDK."""
        message = self.client.messages.create(
            model=MODEL_NAME,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def _parse_response(self, text: str) -> PatientOutput:
        """Parse JSON response from Claude."""
        try:
            parsed = json.loads(text.strip())
            return PatientOutput(
                summary=parsed.get("summary", ""),
                lifestyle_advice=parsed.get("lifestyle_advice", []),
            )
        except json.JSONDecodeError:
            logger.warning("[PatientAgent] Could not parse JSON response.")
            return PatientOutput(summary=text, lifestyle_advice=[])
