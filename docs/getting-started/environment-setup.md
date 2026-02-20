# 개발 환경 설정

## 필수 요구사항

| 항목 | 최소 버전 | 확인 명령어 |
|------|----------|------------|
| Python | 3.10 이상 | `python --version` |
| pip | 최신 | `pip --version` |
| Claude Code (CLI) | 최신 | `claude --version` |

## 1단계: Python 설치 확인

터미널을 열고 Python 버전을 확인합니다:

```bash
python --version
# 또는
python3 --version
```

**Python 3.10 이상**이 필요합니다. 설치되어 있지 않다면:

- **Windows**: [python.org](https://www.python.org/downloads/)에서 다운로드
- **macOS**: `brew install python3`
- **Linux**: `sudo apt install python3 python3-pip python3-venv`

## 2단계: 프로젝트 디렉토리 설정

```bash
# 프로젝트 클론 (이미 클론했다면 생략)
git clone <repository-url> MCP_Server_FastMCP
cd MCP_Server_FastMCP
```

## 3단계: 가상환경 생성 및 활성화

가상환경을 사용하면 프로젝트별로 패키지를 독립적으로 관리할 수 있습니다.

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (OS별로 다름)
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat

# macOS / Linux:
source venv/bin/activate
```

활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다:

```
(venv) $ _
```

## 4단계: 패키지 설치

### 기본 설치 (Tutorial 01~03)

```bash
pip install -r requirements.txt
```

설치되는 패키지:
- `fastmcp` - MCP 서버 프레임워크
- `python-dotenv` - 환경변수 관리
- `httpx` - 비동기 HTTP 클라이언트

### 전체 설치 (Tutorial 04~05 포함)

```bash
pip install -r requirements.txt sqlalchemy pyodbc aiosqlite
```

> **참고**: Tutorial 04 (MSSQL)를 사용하려면 ODBC 드라이버가 별도로 필요합니다.
> [Microsoft ODBC Driver for SQL Server](https://learn.microsoft.com/ko-kr/sql/connect/odbc/download-odbc-driver-for-sql-server) 참고

### uv를 사용하는 경우 (선택사항)

[uv](https://docs.astral.sh/uv/)는 빠른 Python 패키지 관리자입니다:

```bash
# uv 설치
pip install uv

# uv로 패키지 설치
uv pip install -r requirements.txt
```

## 5단계: 환경변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env
```

`.env` 파일을 열어 필요한 값을 설정합니다:

```env
# Tutorial 02: 날씨 서버 (선택사항 - 없으면 데모 모드)
OPENWEATHER_API_KEY=your_api_key_here

# Tutorial 04: MSSQL (선택사항 - 없으면 데모 모드)
MSSQL_SERVER=localhost
MSSQL_DATABASE=ITLog
MSSQL_USERNAME=sa
MSSQL_PASSWORD=your_password_here
```

> **중요**: `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.
> API 키나 비밀번호가 GitHub에 올라가지 않도록 주의하세요.

## 6단계: 설치 확인

모든 설치가 완료되었는지 확인합니다:

```bash
# FastMCP 버전 확인
python -c "import fastmcp; print(fastmcp.__version__)"

# 첫 번째 튜토리얼 서버 실행 테스트
cd tutorials/01_hello_mcp
fastmcp run server.py
```

서버가 정상적으로 시작되면 설치 완료입니다!

(`Ctrl+C`로 서버를 종료합니다)

## 7단계: Claude Code에서 MCP 서버 연결하기

### 방법 1: Claude Code CLI에서 직접 추가

```bash
# Claude Code에서 MCP 서버 추가
claude mcp add hello-mcp -- fastmcp run /absolute/path/to/tutorials/01_hello_mcp/server.py
```

### 방법 2: 설정 파일 직접 수정

Claude Code 설정 파일에 MCP 서버를 추가합니다.

**설정 파일 위치:**
- **프로젝트별**: `.claude/claude_code_config.json` (프로젝트 루트)
- **전역**: `~/.claude/claude_code_config.json`

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "fastmcp",
      "args": ["run", "/absolute/path/to/tutorials/01_hello_mcp/server.py"]
    }
  }
}
```

### 방법 3: Claude Desktop App에서 연결 (선택사항)

Claude Desktop을 사용하는 경우:

**설정 파일 위치:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "fastmcp",
      "args": ["run", "/absolute/path/to/tutorials/01_hello_mcp/server.py"]
    }
  }
}
```

> **팁**: `fastmcp`가 PATH에 없다면, `which fastmcp` (macOS/Linux) 또는 `where fastmcp` (Windows)로 전체 경로를 확인하여 사용하세요.

## 문제 해결

### `fastmcp` 명령어를 찾을 수 없는 경우

```bash
# fastmcp 전체 경로 확인
which fastmcp  # macOS/Linux
where fastmcp  # Windows

# 또는 python -m으로 실행
python -m fastmcp run server.py
```

### Python 버전이 3.10 미만인 경우

```bash
# pyenv로 최신 Python 설치 (macOS/Linux)
brew install pyenv
pyenv install 3.12
pyenv local 3.12
```

### 가상환경에서 패키지를 찾지 못하는 경우

```bash
# 가상환경이 활성화되어 있는지 확인
which python  # venv 안의 Python이어야 함

# 패키지 재설치
pip install --force-reinstall -r requirements.txt
```

## 다음 단계

환경 설정이 완료되었습니다!

➡️ [프로젝트 구조 이해하기](./project-structure.md)로 이동하세요.
