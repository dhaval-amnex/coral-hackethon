from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evidence:
    type: str
    detail: str
    link: str = ""


@dataclass
class IncidentBrief:
    incident_id: str
    summary: str
    probable_root_cause: str
    confidence: str
    impacted_services: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "summary": self.summary,
            "probable_root_cause": self.probable_root_cause,
            "confidence": self.confidence,
            "impacted_services": self.impacted_services,
            "owners": self.owners,
            "evidence": [
                {"type": e.type, "detail": e.detail, "link": e.link}
                for e in self.evidence
            ],
            "recommended_actions": self.recommended_actions,
            "diagnostics": self.diagnostics,
        }

