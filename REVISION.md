# REVISION

## 변경 이력

- **환경 변수**: DB 접속 정보(host, port, user, password)를 `.env`로 분리 (`python-dotenv`)
- **FastAPI 앱**: DB 관리 REST API 추가 (포트 8013)
  - `POST /api/v1/rdb/database/create` — DB·사용자 생성
  - `POST /api/v1/rdb/table/create` — 테이블 생성 및 권한 부여
  - `GET /health` — DB 연결 상태 확인
- **Docker**: FastAPI 앱 배포용 Dockerfile 추가
