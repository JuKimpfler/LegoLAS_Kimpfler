"""
Rebrickable API Client für LegoLAS.

Ruft die Teileliste eines LEGO-Sets von der Rebrickable-API ab.
"""

from typing import List, Tuple

import requests

_BASE_URL = "https://rebrickable.com/api/v3/lego/sets/{set_num}/parts/"
_PLACEHOLDER_KEY = "DEIN_REBRICKABLE_API_KEY_HIER"


def fetch_set_parts(set_id: str, api_key: str) -> List[Tuple[str, str, str, int]]:
    """
    Lädt alle Nicht-Ersatzteile eines LEGO-Sets von Rebrickable.

    Parameters
    ----------
    set_id : str
        LEGO-Set-Nummer (z. B. ``"75192"`` oder ``"75192-1"``).
    api_key : str
        Gültiger Rebrickable API Key.

    Returns
    -------
    List[Tuple[part_num, name, color_name, quantity]]
        Unsortierte Liste der benötigten Teile.

    Raises
    ------
    ValueError
        Falls ``api_key`` fehlt, das Set nicht gefunden wurde oder leer ist.
    requests.HTTPError
        Bei sonstigen HTTP-Fehlern.
    """
    if not api_key or api_key.strip() == _PLACEHOLDER_KEY:
        raise ValueError(
            "Kein gültiger Rebrickable API Key konfiguriert. "
            "Bitte den Key in den Einstellungen eintragen."
        )

    normalized = set_id.strip()
    if not normalized.endswith("-1"):
        normalized = normalized + "-1"

    url = _BASE_URL.format(set_num=normalized)
    headers = {"Authorization": f"key {api_key}"}
    params: dict = {"page_size": 1000}

    parts: List[Tuple[str, str, str, int]] = []

    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 404:
            raise ValueError(
                f"Set '{normalized}' wurde auf Rebrickable nicht gefunden. "
                "Bitte Set-ID prüfen (z. B. '75192-1')."
            )
        resp.raise_for_status()

        data = resp.json()
        for item in data.get("results", []):
            if item.get("is_spare"):
                continue
            part_num = str(item["part"]["part_num"])
            name = item["part"].get("name", "")
            color_name = item["color"].get("name", "")
            quantity = int(item.get("quantity", 1))
            parts.append((part_num, name, color_name, quantity))

        url = data.get("next")
        params = {}

    if not parts:
        raise ValueError(
            f"Set '{normalized}' wurde gefunden, enthält aber keine Teileliste."
        )

    return parts
