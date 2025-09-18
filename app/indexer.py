from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
from sqlalchemy import select

from app.features import extract_all_features
from app.models import AsyncSessionLocal, Drug, init_db

INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = INDEX_DIR / "faiss.index"
MEANSTD_PATH = INDEX_DIR / "norm.npz"


def _buffer_to_vec(buffer: bytes | None) -> np.ndarray:
    if not buffer:
        return np.array([], dtype=np.float32)
    return np.frombuffer(buffer, dtype=np.float32)


def _stack_feature(drug: Drug) -> np.ndarray:
    color = _buffer_to_vec(drug.feat_color)
    shape = _buffer_to_vec(drug.feat_shape)
    texture = _buffer_to_vec(drug.feat_texture)
    embed = _buffer_to_vec(drug.feat_embed)
    return np.concatenate([color, shape, texture, embed]).astype(np.float32)


async def compute_and_store_features() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Drug))
        drugs = result.scalars().all()
        for drug in drugs:
            if not drug.image_path:
                continue
            features = extract_all_features(drug.image_path)
            if features is None:
                continue
            color, shape, texture, embed = features
            drug.feat_color = color.tobytes()
            drug.feat_shape = shape.tobytes()
            drug.feat_texture = texture.tobytes()
            drug.feat_embed = embed.tobytes()
            session.add(drug)
        await session.commit()


async def build_index() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Drug))
        drugs = result.scalars().all()

    vectors: List[np.ndarray] = []
    ids: List[int] = []
    for drug in drugs:
        if not (drug.feat_color and drug.feat_shape and drug.feat_texture and drug.feat_embed):
            continue
        vectors.append(_stack_feature(drug))
        ids.append(int(drug.id))

    if not vectors:
        raise RuntimeError("No features found. Run compute_and_store_features first.")

    matrix = np.vstack(vectors).astype(np.float32)
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0) + 1e-6
    normalized = (matrix - mean) / std

    dim = normalized.shape[1]
    index = faiss.IndexHNSWFlat(dim, 32)
    index.hnsw.efConstruction = 200
    index.add(normalized)
    faiss.write_index(index, str(INDEX_PATH))
    np.savez(MEANSTD_PATH, mean=mean, std=std, ids=np.array(ids, dtype=np.int64))
    print(f"Indexed {len(ids)} items → {INDEX_PATH}")


def _load_index() -> Tuple[faiss.Index, np.ndarray, np.ndarray, np.ndarray]:
    index = faiss.read_index(str(INDEX_PATH))
    stats = np.load(MEANSTD_PATH, allow_pickle=True)
    mean = stats["mean"]
    std = stats["std"]
    ids = stats["ids"]
    return index, mean, std, ids


async def query_index(vector: np.ndarray, topk: int = 100) -> Tuple[List[int], List[float]]:
    index, mean, std, ids = _load_index()
    normalized = ((vector - mean) / std).astype(np.float32)[None, :]
    distances, indices = index.search(normalized, topk)
    id_list = [int(ids[i]) for i in indices[0]]
    return id_list, distances[0].tolist()
