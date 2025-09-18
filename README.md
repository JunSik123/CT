# 의약품 낱알 식별 캡스톤 예시

이 저장소는 식품의약품안전처(MFDS) 낱알식별 정보와 GPT 기반 후처리를 활용한 의약품 낱알식별 백엔드의 예시 구현입니다. 실제 서비스에서 필요한 핵심 모듈 구조를 단순화하여 포함하고 있으며, 외부 API 연동이 어려운 환경에서도 개발 및 테스트가 가능하도록 샘플 데이터셋과 휴리스틱 GPT 대체 모듈을 제공합니다.

## 구성 요소

- **FastAPI 애플리케이션 (`app/main.py`)**: 식별 요청, 데이터 검색, 의약품 상세 조회 API 제공
- **MFDS 클라이언트 (`app/mfds_client.py`)**: 식약처 API 또는 로컬 샘플 데이터셋에서 의약품 메타데이터 조회
- **GPT 클라이언트 (`app/gpt_client.py`)**: GPT API 호출을 모사하는 휴리스틱 재정렬 로직
- **식별 서비스 (`app/pipeline.py`)**: 후보 생성 → GPT 재정렬 → 결과 설명 생성
- **데이터 (`data/pills_sample.json`)**: 오프라인 테스트용 3개 의약품 샘플 레코드
- **테스트 (`tests/test_pipeline.py`)**: API 엔드포인트 동작 검증 예시

## 로컬 실행 방법

1. (선택) 실제 MFDS API(`https://apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService02/getMdcinGrnIdntfcInfoList02`)를 사용하려면 `.env` 파일에 아래 값을 설정하세요.
   ```env
   PILL_ID_MFDS_API_KEY=발급받은_API_KEY
   ```
   예: 데이터포털에서 발급받은 일반 인증키 `9lAsn5GBHw/tSBCo3XE4uPq7T4nZu0NiM8UPaayX3E+PK64xU59HLAcFW8nczk2RENnFIzW5DLcHOdtxIcehtw==`
   를 그대로 사용할 수 있습니다.
2. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```
3. 개발 서버를 실행합니다.
   ```bash
   uvicorn app.main:app --reload
   ```
4. 브라우저에서 `http://127.0.0.1:8000/docs`에 접속하면 자동 생성된 Swagger UI를 확인할 수 있습니다.

## 주요 엔드포인트

| 메소드 | 경로 | 설명 |
| ------ | ---- | ---- |
| `GET`  | `/health` | 헬스 체크 |
| `POST` | `/identify` | 이미지 특징을 기반으로 의약품 식별 |
| `POST` | `/pills/search` | 색상/형태/각인 등으로 의약품 검색 |
| `GET`  | `/pills/{pill_id}` | 특정 의약품 상세 정보 및 주의 문구 조회 |

## 테스트

Pytest를 이용해 기본 시나리오를 검증할 수 있습니다.
```bash
pytest
```

네트워크 차단으로 외부 패키지를 설치하지 못하는 환경에서는 FastAPI 모듈이 없어 테스트가 실패할 수 있습니다. 이 경우 패키지 설치가 가능한 환경에서 실행하거나, 사전에 필요한 휠 파일을 준비해 오프라인 설치를 진행하세요.
