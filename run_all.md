# 실행 가이드

## 1) 가상환경 & 패키지 설치
python -m venv .venv
# Windows: .venv\Scripts\activate
# mac/Linux: source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

## 2) .env에 API 키 넣기
- Encoded 키를 MFDS_API_KEY_ENC에 그대로 붙여넣기

## 3) 데이터 수집 & 이미지 다운로드
python -m app.ingest_api   # 첫 실행은 시간이 조금 걸릴 수 있음

## 4) 특징 계산 & 인덱스 구축
python - <<'PY'
import asyncio
from app.indexer import compute_and_store_features, build_index
async def run():
    await compute_and_store_features()
    await build_index()
asyncio.run(run())
PY

## 5) 서버 실행
uvicorn app.main:app --reload --port 8000

## 6) 테스트
브라우저에서 http://127.0.0.1:8000/docs 접속 → /identify 엔드포인트 선택
- front_on, front_off 두 장 업로드(플래시 ON/OFF)
- 또는 front 한 장 업로드
- 실행 → Top-5 결과 확인
