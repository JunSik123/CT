from typing import List, Set

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.features import (
    feat_color_hist,
    feat_orb_embed,
    feat_shape,
    feat_texture,
    segment_pill,
)
from app.indexer import query_index
from app.models import AsyncSessionLocal, Drug, init_db
from app.ocr import lexicon_rank, ocr_basic
from app.preprocess import flash_only, flatten_placeholder
from app.ranker import fuse_scores
from app.schema import IdentifyResponse, IdentifyResult
from app.utils import read_bgr

app = FastAPI(title="PillID Server", version="1.0.0")


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/identify", response_model=IdentifyResponse)
async def identify(
    front_on: UploadFile | None = File(default=None),
    front_off: UploadFile | None = File(default=None),
    front: UploadFile | None = File(default=None),
    topk: int = Form(default=5),
):
    if front_on and front_off:
        img_on = read_bgr(front_on)
        img_off = read_bgr(front_off)
        if img_on is None or img_off is None:
            return JSONResponse(
                status_code=400, content={"detail": "이미지를 읽을 수 없습니다."}
            )
        albedo, _ = flash_only(img_on, img_off)
        processed = albedo
    elif front:
        img_single = read_bgr(front)
        if img_single is None:
            return JSONResponse(
                status_code=400, content={"detail": "이미지를 읽을 수 없습니다."}
            )
        gray = flatten_placeholder(img_single, None)
        processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    else:
        return JSONResponse(
            status_code=400,
            content={"detail": "front_on+front_off 또는 front 중 하나를 제공하세요."},
        )

    _, mask = segment_pill(processed)
    color = feat_color_hist(processed, mask)
    shape = feat_shape(processed, mask)
    texture = feat_texture(processed, mask)
    embed = feat_orb_embed(processed, mask)
    query_vector = np.concatenate([color, shape, texture, embed]).astype(np.float32)

    try:
        candidate_ids, distances = await query_index(query_vector, topk=100)
    except Exception as exc:  # pragma: no cover - runtime guard
        return JSONResponse(status_code=500, content={"detail": f"인덱스 조회 실패: {exc}"})

    ocr_text = ocr_basic(processed)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Drug).where(Drug.id.in_(candidate_ids)))
        drugs: List[Drug] = result.scalars().all()

    lexicon: Set[str] = set()
    for drug in drugs:
        if drug.print_front:
            lexicon.add(drug.print_front.strip().replace(" ", ""))
        if drug.print_back:
            lexicon.add(drug.print_back.strip().replace(" ", ""))

    ranked = lexicon_rank(ocr_text, list(lexicon), topn=50)
    lex_cost = {token: score for token, score in ranked}

    ann_map = {drug_id: dist for drug_id, dist in zip(candidate_ids, distances)}
    triples: List[tuple[Drug, float, float]] = []
    for drug in drugs:
        candidate_costs = []
        for token in (drug.print_front, drug.print_back):
            if not token:
                continue
            normalized = token.strip().replace(" ", "")
            candidate_costs.append(lex_cost.get(normalized, 5.0))
        ocr_cost = min(candidate_costs) if candidate_costs else 5.0
        triples.append((drug, ann_map.get(drug.id, 1e9), ocr_cost))

    ann_distances = [item[1] for item in triples]
    ocr_costs = [item[2] for item in triples]
    fused = fuse_scores(ann_distances, ocr_costs, w_ann=0.5, w_ocr=0.5)
    order = np.argsort(-fused)

    results: List[IdentifyResult] = []
    for idx in order[:topk]:
        drug, _, _ = triples[idx]
        results.append(
            IdentifyResult(
                item_seq=drug.item_seq,
                item_name=drug.item_name,
                entp_name=drug.entp_name,
                score=float(fused[idx]),
                image_url=drug.image_url,
            )
        )

    uncertain = True
    if len(results) >= 2 and results[0].score > 0.6 and (results[0].score - results[1].score) > 0.15:
        uncertain = False

    message = "추가 촬영(동전/뒷면)을 권장합니다." if uncertain else None
    return IdentifyResponse(results=results, uncertain=uncertain, message=message)
