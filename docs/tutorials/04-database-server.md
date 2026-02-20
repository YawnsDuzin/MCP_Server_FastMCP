# Tutorial 04: MSSQL 데이터베이스 MCP 서버 (IT-Log 실전)

> **난이도**: ★★★★☆ (중상급)
> **사전 지식**: Tutorial 01~03 완료, SQL 기초
> **결과물**: MSSQL DB를 조회하는 실전 MCP 서버

## 이 튜토리얼에서 배우는 것

- SQLAlchemy로 MSSQL 데이터베이스 연결
- SQL Injection 방지 (파라미터 바인딩)
- 읽기 전용 쿼리 제한 (보안)
- 실무 데이터 모델 (현장-카메라-이벤트)
- 대시보드 형태의 요약 도구

## 이 서버의 핵심 가치

```
Before MCP:
  → SSMS 열기 → DB 접속 → SQL 작성 → 실행 → 결과 확인

After MCP:
  → Claude에게 "서울 본사 카메라 목록 보여줘" 한마디
  → 끝!
```

"도구를 만드는 도구를 만드는" 메타적 쾌감이 있는 튜토리얼입니다.

---

## Step 1: 데이터 모델 이해

IT-Log 시스템의 데이터 구조:

```
[Sites] ─── 1:N ──── [Cameras] ─── 1:N ──── [Events]
 현장                  카메라                   이벤트

 site_id (PK)          camera_id (PK)          event_id (PK)
 site_name             site_id (FK)            camera_id (FK)
 location              name                    event_type
 status                type                    timestamp
 camera_count          status                  severity
                       ip
```

---

## Step 2: 추가 패키지 설치

```bash
pip install sqlalchemy pyodbc
```

### ODBC 드라이버 설치

MSSQL에 연결하려면 ODBC 드라이버가 필요합니다:

**Windows:**
- [Microsoft ODBC Driver for SQL Server](https://learn.microsoft.com/ko-kr/sql/connect/odbc/download-odbc-driver-for-sql-server) 다운로드 및 설치

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"
sudo apt update
sudo apt install msodbcsql17
```

---

## Step 3: 환경변수 설정

`.env` 파일:

```env
MSSQL_SERVER=localhost
MSSQL_DATABASE=ITLog
MSSQL_USERNAME=sa
MSSQL_PASSWORD=your_password_here
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
```

> **DB 없이 테스트**: `.env`에서 `MSSQL_PASSWORD`를 비워두면 **데모 모드**로 실행됩니다.

---

## Step 4: 데이터베이스 연결

```python
import os
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("IT-Log Database Server")

DB_CONFIG = {
    "server": os.getenv("MSSQL_SERVER", "localhost"),
    "database": os.getenv("MSSQL_DATABASE", "ITLog"),
    "username": os.getenv("MSSQL_USERNAME", "sa"),
    "password": os.getenv("MSSQL_PASSWORD", ""),
    "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server"),
}

# DB 연결 시도
engine = None
try:
    from sqlalchemy import create_engine, text

    if DB_CONFIG["password"]:
        connection_string = (
            f"mssql+pyodbc://{DB_CONFIG['username']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['server']}/{DB_CONFIG['database']}"
            f"?driver={DB_CONFIG['driver'].replace(' ', '+')}"
        )
        engine = create_engine(connection_string)
        DB_MODE = "live"
    else:
        DB_MODE = "demo"
except ImportError:
    DB_MODE = "demo"
```

### SQLAlchemy 연결 문자열 구조

```
mssql+pyodbc://사용자:비밀번호@서버/데이터베이스?driver=드라이버
              ─────── ──────── ──── ──────────── ──────────────
```

### Demo vs Live 모드

```
DB_MODE = "demo"  → 하드코딩된 데모 데이터 사용
DB_MODE = "live"  → 실제 MSSQL 데이터베이스 쿼리
```

---

## Step 5: 안전한 쿼리 실행 함수

```python
def _execute_query(query_text: str, params: dict | None = None) -> list[dict]:
    """SQLAlchemy를 사용하여 안전하게 쿼리를 실행합니다."""
    with engine.connect() as conn:
        result = conn.execute(text(query_text), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]
```

### SQL Injection 방지

```python
# ❌ 위험한 방법 - 절대 이렇게 하지 마세요!
query = f"SELECT * FROM Sites WHERE site_name = '{user_input}'"
# user_input = "'; DROP TABLE Sites; --" 이면 테이블 삭제됨!

# ✅ 안전한 방법 - 파라미터 바인딩
query = "SELECT * FROM Sites WHERE site_name = :name"
params = {"name": user_input}
_execute_query(query, params)
```

`text()` + 파라미터 바인딩을 사용하면 SQL Injection을 원천 차단합니다.

---

## Step 6: 핵심 도구 구현

### 현장 목록 조회

```python
@mcp.tool
def list_sites(status: str = "") -> str:
    """모든 현장 목록을 조회합니다."""
    if DB_MODE == "demo":
        sites = DEMO_SITES
        if status:
            sites = [s for s in sites if s["status"] == status]
    else:
        query = "SELECT * FROM Sites"
        params = {}
        if status:
            query += " WHERE status = :status"
            params["status"] = status
        sites = _execute_query(query, params)

    # 결과를 보기 좋게 포맷팅
    result = ["📋 현장 목록", ""]
    for site in sites:
        result.append(f"  [{site['site_id']}] {site['site_name']} - {site['status']}")

    return "\n".join(result)
```

### 카메라 목록 조회

```python
@mcp.tool
def list_cameras(site_id: int = 0, status: str = "") -> str:
    """카메라 목록을 조회합니다."""
    # Demo/Live 모드 분기 + 필터링 로직
    ...
```

### 대시보드

```python
@mcp.tool
def dashboard() -> str:
    """전체 시스템 현황을 보여줍니다."""
    # 현장 수, 카메라 수, 장애 수, 긴급 이벤트 등
    # 한눈에 파악할 수 있는 요약 정보
    ...
```

---

## Step 7: 커스텀 쿼리 (읽기 전용)

```python
@mcp.tool
def run_query(query: str) -> str:
    """읽기 전용 SQL 쿼리를 실행합니다. (SELECT만 허용)"""
    cleaned = query.strip().upper()

    # SELECT만 허용
    if not cleaned.startswith("SELECT"):
        return "❌ SELECT 쿼리만 실행할 수 있습니다."

    # 위험한 키워드 차단
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]
    for word in forbidden:
        if word in cleaned:
            return f"❌ '{word}' 명령은 사용할 수 없습니다."

    rows = _execute_query(query)
    # 결과 포맷팅...
```

### 보안 계층

```
사용자 요청
    ↓
Claude가 run_query 호출
    ↓
[보안 체크 1] SELECT만 허용
    ↓
[보안 체크 2] 위험 키워드 차단
    ↓
[보안 체크 3] 파라미터 바인딩 (SQLAlchemy)
    ↓
DB 쿼리 실행
```

---

## Step 8: 실행 및 테스트

### 서버 실행

```bash
fastmcp run tutorials/04_database_server/server.py
```

### Claude Code에 등록

```bash
claude mcp add itlog-db -- fastmcp run /절대경로/tutorials/04_database_server/server.py
```

### 테스트 대화 예시 (데모 모드)

```
"현장 목록 보여줘"
→ list_sites() 호출

"서울 본사 카메라 목록 조회해줘"
→ list_cameras(site_id=1) 호출

"장애 상태인 카메라 있어?"
→ list_cameras(status="장애") 호출

"전체 시스템 현황 보여줘"
→ dashboard() 호출

"긴급 이벤트 확인해줘"
→ list_events(severity="긴급") 호출
```

---

## 실제 DB 연결 시 추가 작업

데모 모드로 충분히 학습한 후, 실제 MSSQL을 연결하려면:

### 1. 테이블 생성 SQL

```sql
CREATE TABLE Sites (
    site_id INT PRIMARY KEY IDENTITY(1,1),
    site_name NVARCHAR(100) NOT NULL,
    location NVARCHAR(200),
    status NVARCHAR(50) DEFAULT '운영중',
    camera_count INT DEFAULT 0
);

CREATE TABLE Cameras (
    camera_id VARCHAR(20) PRIMARY KEY,
    site_id INT FOREIGN KEY REFERENCES Sites(site_id),
    name NVARCHAR(100) NOT NULL,
    type NVARCHAR(50),
    status NVARCHAR(50) DEFAULT '정상',
    ip VARCHAR(15)
);

CREATE TABLE Events (
    event_id INT PRIMARY KEY IDENTITY(1,1),
    camera_id VARCHAR(20) FOREIGN KEY REFERENCES Cameras(camera_id),
    event_type NVARCHAR(100),
    timestamp DATETIME DEFAULT GETDATE(),
    severity NVARCHAR(20) DEFAULT '보통'
);
```

### 2. .env 업데이트

```env
MSSQL_SERVER=실제서버주소
MSSQL_DATABASE=ITLog
MSSQL_USERNAME=sa
MSSQL_PASSWORD=실제비밀번호
```

---

## 핵심 정리

| 개념 | 코드 | 설명 |
|------|------|------|
| DB 연결 | `create_engine(conn_string)` | SQLAlchemy 엔진 |
| 안전 쿼리 | `text(query), params` | SQL Injection 방지 |
| 읽기 전용 | `SELECT` 검사 | 데이터 보호 |
| 데모 모드 | `if DB_MODE == "demo":` | 로컬 개발 지원 |
| 대시보드 | `dashboard()` | 한눈에 현황 파악 |

## 도전 과제

1. 카메라 장애 통계를 시간대별로 집계하는 도구를 추가해보세요
2. 현장 간 카메라 수 비교 차트(텍스트 기반)를 만들어보세요
3. 이벤트 발생 시 자동 알림 메시지를 구성하는 프롬프트를 만들어보세요

## 다음 단계

➡️ [Tutorial 05: 메모/노트 앱](./05-memo-app.md)
