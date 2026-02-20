# MCP_Server_FastMCP

FastMCP를 사용한 MCP 서버 직접 만들기 - 튜토리얼 모음

## MCP(Model Context Protocol)란?

MCP는 AI 모델(Claude)이 외부 도구와 데이터에 접근할 수 있게 해주는 표준 프로토콜입니다.
이 프로젝트는 [FastMCP](https://github.com/jlowin/fastmcp) 프레임워크를 사용하여
**5개의 단계별 튜토리얼**로 MCP 서버를 만드는 방법을 배웁니다.

## 튜토리얼 목록

| # | 제목 | 설명 | 난이도 |
|---|------|------|--------|
| 01 | [Hello MCP](docs/tutorials/01-hello-mcp.md) | 첫 번째 MCP 서버, Tool/Resource/Prompt 기초 | ★☆☆☆☆ |
| 02 | [날씨 정보 서버](docs/tutorials/02-weather-server.md) | 외부 API 연동, async, 에러 처리 | ★★☆☆☆ |
| 03 | [파일 관리 서버](docs/tutorials/03-file-manager.md) | 파일 시스템 CRUD, 보안 (Path Traversal 방지) | ★★★☆☆ |
| 04 | [MSSQL DB 서버](docs/tutorials/04-database-server.md) | SQLAlchemy + MSSQL, SQL Injection 방지, 실전 패턴 | ★★★★☆ |
| 05 | [메모/노트 앱](docs/tutorials/05-memo-app.md) | SQLite CRUD, 태그 시스템, 검색/통계 | ★★★★☆ |

## 빠른 시작

### 1. 환경 설정

```bash
# Python 3.10+ 필요
python --version

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 2. 첫 번째 서버 실행

```bash
fastmcp run tutorials/01_hello_mcp/server.py
```

### 3. Claude Code에 연결

```bash
claude mcp add hello-mcp -- fastmcp run $(pwd)/tutorials/01_hello_mcp/server.py
```

### 4. 사용해보기

Claude Code에서:
```
"3과 5를 더해줘"          → add(3, 5) 도구 호출
"안녕 내 이름은 민수야"   → greet("민수") 도구 호출
```

## 프로젝트 구조

```
MCP_Server_FastMCP/
├── tutorials/                    # 튜토리얼 소스 코드
│   ├── 01_hello_mcp/server.py   # 기본 MCP 서버
│   ├── 02_weather_server/server.py  # 날씨 API 연동
│   ├── 03_file_manager/server.py    # 파일 관리
│   ├── 04_database_server/server.py # MSSQL 연동
│   └── 05_memo_app/server.py        # 메모 CRUD 앱
├── docs/                         # 상세 문서
│   ├── getting-started/          # 시작 가이드
│   ├── tutorials/                # 튜토리얼 문서
│   └── reference/                # API 레퍼런스
├── requirements.txt              # Python 의존성
├── pyproject.toml               # 프로젝트 설정
└── .env.example                 # 환경변수 템플릿
```

## 문서

상세 문서는 [docs/index.md](docs/index.md)를 참고하세요.

- [MCP란 무엇인가?](docs/getting-started/what-is-mcp.md) - MCP 개념 이해
- [환경 설정](docs/getting-started/environment-setup.md) - 개발 환경 구성
- [FastMCP API](docs/reference/fastmcp-api.md) - API 레퍼런스
- [Claude 연동](docs/reference/claude-integration.md) - Claude Code/Desktop 연결

## 요구 사항

- Python 3.10 이상
- [FastMCP](https://pypi.org/project/fastmcp/) 2.0+
- Claude Code 또는 Claude Desktop (MCP 클라이언트)

### 튜토리얼별 추가 요구 사항

| 튜토리얼 | 추가 패키지 | 외부 서비스 |
|---------|------------|-----------|
| 02 날씨 | httpx | OpenWeatherMap API (선택) |
| 04 MSSQL | sqlalchemy, pyodbc | MSSQL Server (선택) |
| 05 메모 | - (sqlite3 내장) | - |

> Tutorial 02, 04는 API 키/DB 없이도 **데모 모드**로 동작합니다.

## 라이선스

MIT License
