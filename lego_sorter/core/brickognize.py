"""
Brickognize API-Client für LegoLAS.
Dokumentation: https://api.brickognize.com/docs

Sendet ein JPEG-Bild und gibt eine Liste von Erkennungsergebnissen zurück.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False
    logger.warning("requests nicht installiert – Brickognize nicht verfügbar.")


@dataclass
class BrickResult:
    """Einzelnes Erkennungsergebnis der Brickognize-API."""
    part_num: str
    name: str
    score: float
    img_url: str = ""
    external_sites: dict = field(default_factory=dict)


class BrickognizeClient:
    """
    Wrapper um die Brickognize REST-API.

    Parameter
    ---------
    config : module
        Konfigurationsmodul mit BRICKOGNIZE_URL, API_TIMEOUT,
        DEFAULT_CONF_THRESHOLD.
    """

    def __init__(self, config):
        self.cfg = config

    def predict(self, image_bytes: bytes,
                filename: str = "scan.jpg") -> List[BrickResult]:
        """
        Sendet ``image_bytes`` (JPEG) an die Brickognize-API.

        Rückgabe
        --------
        Sortierte Liste von ``BrickResult`` (bestes Ergebnis zuerst).
        Leere Liste bei Fehler oder wenn API nicht erreichbar.
        """
        if not _REQUESTS_AVAILABLE:
            logger.error("requests-Bibliothek fehlt.")
            return []

        try:
            resp = requests.post(
                self.cfg.BRICKOGNIZE_URL,
                files={"query_image": (filename, image_bytes, "image/jpeg")},
                timeout=self.cfg.API_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            logger.error("Brickognize-API-Fehler: %s", exc)
            return []
        except ValueError as exc:
            logger.error("Ungültige API-Antwort: %s", exc)
            return []

        items = data.get("items", [])
        results: List[BrickResult] = []
        for item in items:
            results.append(BrickResult(
                part_num=str(item.get("id", "")),
                name=item.get("name", "Unbekannt"),
                score=float(item.get("score", 0.0)),
                img_url=item.get("img_url", ""),
                external_sites=item.get("external_sites", {}),
            ))
        # Sortierung nach Score absteigend
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def best_match(self, image_bytes: bytes,
                   threshold: float = None) -> Optional[BrickResult]:
        """
        Gibt das beste Erkennungsergebnis zurück, das mindestens
        ``threshold`` Konfidenz hat. ``None`` wenn keines gefunden.
        """
        if threshold is None:
            threshold = self.cfg.DEFAULT_CONF_THRESHOLD
        results = self.predict(image_bytes)
        if results and results[0].score >= threshold:
            return results[0]
        return None
