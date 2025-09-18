"""Client for interacting with the MFDS pill identification dataset/API."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

import httpx

from .models import Pill


class MFDSClient:
    """Access pill data provided by the Korean MFDS API.

    The real API requires an API key and network connectivity. For the purposes of this
    capstone starter project we additionally support loading a bundled sample dataset
    stored under ``data/pills_sample.json``. This allows local development and testing
    without external dependencies while keeping the code structure identical to the
    production environment.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        dataset_path: Optional[Path] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.dataset_path = dataset_path or Path(__file__).resolve().parent.parent / "data" / "pills_sample.json"
        self._http_client = http_client
        self._cached_dataset: Optional[List[Pill]] = None

    # ------------------------------------------------------------------
    # Local dataset helpers
    # ------------------------------------------------------------------
    def _load_local_dataset(self) -> List[Pill]:
        if self._cached_dataset is None:
            with self.dataset_path.open("r", encoding="utf-8") as fh:
                raw_items = json.load(fh)
            self._cached_dataset = [Pill(**item) for item in raw_items]
        return list(self._cached_dataset)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def search_pills(
        self,
        *,
        color: Optional[str] = None,
        shape: Optional[str] = None,
        imprint: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Pill]:
        """Return pills matching the provided filters.

        When an API key is configured the method performs a live request to the MFDS
        API. Otherwise it falls back to filtering the bundled sample dataset.
        """

        if self.api_key:
            return self._search_remote(color=color, shape=shape, imprint=imprint, name=name, limit=limit)
        return self._search_local(color=color, shape=shape, imprint=imprint, name=name, limit=limit)

    def get_pill(self, pill_id: str) -> Optional[Pill]:
        """Return a single pill by its identifier."""

        if self.api_key:
            pills = self._search_remote(item_seq=pill_id, limit=1)
            return pills[0] if pills else None
        dataset = self._load_local_dataset()
        for pill in dataset:
            if pill.pill_id == pill_id:
                return pill
        return None

    # ------------------------------------------------------------------
    # Remote API implementation (network requests)
    # ------------------------------------------------------------------
    def _search_remote(
        self,
        *,
        color: Optional[str] = None,
        shape: Optional[str] = None,
        imprint: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 20,
        item_seq: Optional[str] = None,
    ) -> List[Pill]:
        """Query the MFDS REST API.

        The MFDS API expects parameters in Korean and uses a pagination scheme. For
        simplicity we map a subset of commonly used filters. Developers should extend
        the request schema to include all available query parameters when moving to
        production.
        """

        params = {
            "serviceKey": self.api_key,
            "perPage": str(limit),
        }
        if item_seq:
            params["ITEM_SEQ"] = item_seq
        if color:
            params["COLOR_CLASS1"] = color
        if shape:
            params["DRUG_SHAPE"] = shape
        if imprint:
            params["PRINT_FRONT"] = imprint
        if name:
            params["ITEM_NAME"] = name

        client = self._http_client or httpx.Client(timeout=10.0)
        close_client = self._http_client is None
        try:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()
        finally:
            if close_client:
                client.close()

        payload = response.json()
        records = payload.get("data", [])
        pills = [Pill(**self._normalize_remote_record(record)) for record in records]
        return pills[:limit]

    def _normalize_remote_record(self, record: dict) -> dict:
        """Normalize keys from the MFDS response payload into our schema."""

        return {
            "pill_id": str(record.get("ITEM_SEQ", "")),
            "name": record.get("ITEM_NAME", ""),
            "imprint": record.get("PRINT_FRONT") or record.get("PRINT_BACK"),
            "color": record.get("COLOR_CLASS1"),
            "shape": record.get("DRUG_SHAPE"),
            "manufacturer": record.get("ENTP_NAME"),
            "ingredients": record.get("MAIN_ITEM_INGR"),
            "image_url": record.get("ITEM_IMAGE"),
            "description": record.get("CHART"),
        }

    # ------------------------------------------------------------------
    # Local dataset implementation (no network needed)
    # ------------------------------------------------------------------
    def _search_local(
        self,
        *,
        color: Optional[str],
        shape: Optional[str],
        imprint: Optional[str],
        name: Optional[str],
        limit: int,
    ) -> List[Pill]:
        dataset = self._load_local_dataset()

        def predicate(pill: Pill) -> bool:
            return all(
                cond is None
                or (
                    getattr(pill, attr) is not None
                    and cond.lower() in getattr(pill, attr).lower()
                )
                for attr, cond in (
                    ("color", color),
                    ("shape", shape),
                    ("imprint", imprint),
                    ("name", name),
                )
            )

        filtered: Iterable[Pill] = filter(predicate, dataset)
        return list(filtered)[:limit]
