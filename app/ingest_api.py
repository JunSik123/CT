import asyncio
import math
import os
import ssl
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import aiohttp
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AsyncSessionLocal, Drug, init_db

load_dotenv()
API_KEY_ENC = os.getenv("MFDS_API_KEY_ENC")
IMG_DIR = Path("data/images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = (
    "https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService02/"
    "getMdcinGrnIdntfcInfoList02"
)


def _tls12_connector() -> aiohttp.TCPConnector:
    try:
        context = ssl.create_default_context()
        if hasattr(ssl, "TLSVersion"):
            try:
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            except ValueError:
                pass
            try:
                context.maximum_version = ssl.TLSVersion.TLSv1_2
            except ValueError:
                pass
        else:
            context.options |= getattr(ssl, "OP_NO_TLSv1_3", 0)
            context.options |= getattr(ssl, "OP_NO_TLSv1_1", 0)
            context.options |= getattr(ssl, "OP_NO_TLSv1", 0)
        return aiohttp.TCPConnector(ssl=context)
    except Exception:
        return aiohttp.TCPConnector(ssl=False)


def _clean(value: Any, default: Any = "") -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return value


def _parse_items(payload: Dict[str, Any]) -> Tuple[int, Iterable[Dict[str, Any]]]:
    response = payload.get("response", {})
    body = response.get("body", {})
    total = body.get("totalCount", 0) or 0
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", []) or []
    return int(total), items


async def _fetch_page(
    client: aiohttp.ClientSession, page: int, rows: int = 100
) -> Dict[str, Any]:
    params = {
        "serviceKey": API_KEY_ENC,
        "pageNo": page,
        "numOfRows": rows,
        "type": "json",
    }
    async with client.get(BASE_URL, params=params, timeout=30) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


def _drug_from_item(item: Dict[str, Any]) -> Drug:
    return Drug(
        item_seq=str(_clean(item.get("ITEM_SEQ"), "")),
        item_name=_clean(item.get("ITEM_NAME"), ""),
        entp_name=_clean(item.get("ENTP_NAME"), ""),
        drug_shape=_clean(item.get("DRUG_SHAPE")),
        color1=_clean(item.get("COLOR_CLASS1")),
        color2=_clean(item.get("COLOR_CLASS2")),
        line_front=_clean(item.get("LINE_FRONT")),
        line_back=_clean(item.get("LINE_BACK")),
        print_front=_clean(item.get("PRINT_FRONT")),
        print_back=_clean(item.get("PRINT_BACK")),
        image_url=_clean(item.get("ITEM_IMAGE")),
    )


async def ingest_all() -> None:
    if not API_KEY_ENC:
        raise RuntimeError("MFDS_API_KEY_ENC is not set in environment")

    await init_db()

    async with aiohttp.ClientSession(connector=_tls12_connector()) as client:
        first_page = await _fetch_page(client, 1)
        total, items = _parse_items(first_page)
        rows = 100
        total_pages = max(1, math.ceil(total / rows)) if total else 1

        async with AsyncSessionLocal() as session:
            for item in items:
                await _upsert_drug(session, item)
            await session.commit()

        for page in range(2, total_pages + 1):
            data = await _fetch_page(client, page)
            _, page_items = _parse_items(data)
            async with AsyncSessionLocal() as session:
                for item in page_items:
                    await _upsert_drug(session, item)
                await session.commit()


async def _upsert_drug(session: AsyncSession, item: Dict[str, Any]) -> None:
    drug = _drug_from_item(item)
    if not drug.item_seq:
        return
    existing = await session.execute(
        select(Drug).where(Drug.item_seq == drug.item_seq)
    )
    existing_drug = existing.scalars().first()
    if existing_drug:
        for attr in (
            "item_name",
            "entp_name",
            "drug_shape",
            "color1",
            "color2",
            "line_front",
            "line_back",
            "print_front",
            "print_back",
            "image_url",
        ):
            setattr(existing_drug, attr, getattr(drug, attr))
        session.add(existing_drug)
    else:
        session.add(drug)


async def download_images() -> None:
    await init_db()

    async with aiohttp.ClientSession(connector=_tls12_connector()) as client:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Drug).where(Drug.image_url.is_not(None))
            )
            drugs = result.scalars().all()
            for drug in drugs:
                if not drug.image_url or drug.image_path:
                    continue
                try:
                    async with client.get(drug.image_url, timeout=30) as resp:
                        if resp.status != 200:
                            continue
                        content = await resp.read()
                except Exception:
                    continue

                file_path = IMG_DIR / f"{drug.item_seq}.jpg"
                file_path.write_bytes(content)
                drug.image_path = str(file_path)
                session.add(drug)
                await session.commit()


if __name__ == "__main__":
    asyncio.run(ingest_all())
    asyncio.run(download_images())
