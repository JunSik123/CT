# 물리-인지 융합 의약품 식별 시스템

이 저장소는 식약처 낱알식별 API(getMdcinGrnIdntfcInfoList02)와 멀티모달 특징 추출, FAISS 인덱싱, 혼동 인지형 OCR 후처리를 결합한 엔드투엔드 데모 서버를 제공합니다. 제공된 실행 순서를 따르면 데이터 수집 → 이미지 다운로드 → 특징 계산 → ANN 인덱스 구축 → FastAPI 식별 서버 구동까지 한 번에 완료할 수 있습니다.

## 프로젝트 구조

```
pillid/
├─ .env
├─ requirements.txt
├─ data/
│  ├─ images/
│  └─ index/
├─ db/
│  └─ pillid.sqlite
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ models.py
│  ├─ schema.py
│  ├─ ingest_api.py
│  ├─ features.py
│  ├─ ocr.py
│  ├─ indexer.py
│  ├─ preprocess.py
│  ├─ ranker.py
│  └─ utils.py
└─ run_all.md
```

## 주요 모듈

- **`app/ingest_api.py`**: 식약처 API에서 의약품 메타데이터를 수집하고 이미지 파일을 다운로드합니다.
- **`app/features.py`**: 색상, 형상, 질감, ORB 임베딩을 포함한 멀티모달 특징을 계산합니다.
- **`app/indexer.py`**: 추출된 특징을 데이터베이스에 저장하고 FAISS HNSW 인덱스를 생성합니다.
- **`app/ocr.py`**: Tesseract 기반 OCR과 혼동 행렬을 이용한 가중 편집거리 디코더를 제공합니다.
- **`app/preprocess.py`**: Flash-Only 조명 분리와 간이 평탄화를 수행합니다.
- **`app/main.py`**: FastAPI 서버. `/identify` 엔드포인트에서 플래시 온/오프 이미지 또는 단일 이미지를 받아 후보 약품을 반환합니다.

## 실행 순서

자세한 커맨드는 `run_all.md`를 참고하세요.

1. 가상환경 생성 후 `pip install -r requirements.txt` 설치
2. `.env` 파일에 제공된 API 키 입력 (기본값 포함)
3. `python -m app.ingest_api` 로 메타데이터 및 이미지 수집
4. `compute_and_store_features` → `build_index` 실행으로 특징 및 인덱스 구축
5. `uvicorn app.main:app --reload --port 8000` 명령으로 서버 실행
6. `http://127.0.0.1:8000/docs` 접속 후 `/identify` 호출로 식별 결과 확인

## 환경 변수

`.env` 파일에는 다음 값이 포함되어 있습니다.

- `MFDS_API_KEY_ENC`: 식약처 API 호출에 사용하는 URL 인코딩된 인증키
- `MFDS_API_KEY_DEC`: 참고용 디코딩 키
- `TESSERACT_PATH`: Windows 환경에서 Tesseract 실행 파일 경로 (선택)

## 주의 사항

- 실제 서비스 키가 포함되어 있으므로 배포 시 보안에 유의하세요.
- 초기 데이터 수집은 몇 분 정도 소요될 수 있습니다. 네트워크 오류가 발생하면 재실행하면 됩니다.
- 인덱스 파일(`data/index/`)과 이미지(`data/images/`)는 저장소에 커밋되지 않으며, 필요시 다시 생성할 수 있습니다.
- `faiss-cpu`와의 호환을 위해 NumPy는 1.x 계열(현재 `1.26.4`)로 고정되어 있습니다. 다른 버전을 사용하면 설치 충돌이 발생할 수 있습니다.
- Windows 환경에서 Python 3.12 사용 시 TLS 1.3 핸드셰이크 문제로 SSL 오류가 발생할 수 있어 `app/ingest_api.py`는 자동으로 TLS 1.2로 다운그레이드하도록 구성되어 있습니다. 여전히 네트워크 장벽이 있는 경우 재시도하거나 방화벽 설정을 확인해주세요.
