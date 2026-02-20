# Claude 연동 가이드

## 개요

만든 MCP 서버를 Claude와 연결하는 방법을 설명합니다.

---

## Claude Code (CLI)에서 연결

### 방법 1: `claude mcp add` 명령어 (권장)

```bash
# 기본 형식
claude mcp add <서버이름> -- <실행명령어>

# 예시: Hello MCP 서버 추가
claude mcp add hello-mcp -- fastmcp run /home/user/MCP_Server_FastMCP/tutorials/01_hello_mcp/server.py

# 예시: 날씨 서버 추가
claude mcp add weather -- fastmcp run /home/user/MCP_Server_FastMCP/tutorials/02_weather_server/server.py

# 예시: 파일 관리 서버 추가
claude mcp add file-manager -- fastmcp run /home/user/MCP_Server_FastMCP/tutorials/03_file_manager/server.py

# 예시: DB 서버 추가
claude mcp add itlog-db -- fastmcp run /home/user/MCP_Server_FastMCP/tutorials/04_database_server/server.py

# 예시: 메모앱 추가
claude mcp add memo-app -- fastmcp run /home/user/MCP_Server_FastMCP/tutorials/05_memo_app/server.py
```

### 방법 2: 설정 파일 직접 수정

**프로젝트별 설정** (`.claude/claude_code_config.json`):

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/tutorials/01_hello_mcp/server.py"]
    },
    "weather": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/tutorials/02_weather_server/server.py"]
    },
    "file-manager": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/tutorials/03_file_manager/server.py"]
    },
    "itlog-db": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/tutorials/04_database_server/server.py"]
    },
    "memo-app": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/tutorials/05_memo_app/server.py"]
    }
  }
}
```

**전역 설정** (`~/.claude/claude_code_config.json`):
모든 프로젝트에서 사용할 MCP 서버는 전역 설정에 추가합니다.

### MCP 서버 관리 명령어

```bash
# 등록된 MCP 서버 목록 확인
claude mcp list

# MCP 서버 제거
claude mcp remove <서버이름>
```

---

## Claude Desktop에서 연결

### 설정 파일 위치

| OS | 경로 |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

### 설정 예시

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/tutorials/01_hello_mcp/server.py"]
    }
  }
}
```

### Python 경로 문제 해결

가상환경의 Python을 직접 지정해야 할 수 있습니다:

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "/home/user/MCP_Server_FastMCP/venv/bin/python",
      "args": ["-m", "fastmcp", "run", "/절대/경로/tutorials/01_hello_mcp/server.py"]
    }
  }
}
```

Windows의 경우:

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "C:\\Users\\user\\MCP_Server_FastMCP\\venv\\Scripts\\python.exe",
      "args": ["-m", "fastmcp", "run", "C:\\절대\\경로\\tutorials\\01_hello_mcp\\server.py"]
    }
  }
}
```

---

## 연결 확인 방법

### Claude Code에서 확인

Claude Code를 시작한 후 다음과 같이 테스트:

```
"사용 가능한 MCP 도구 목록을 보여줘"
```

Claude가 등록된 MCP 서버의 도구 목록을 보여줍니다.

### 디버깅

서버가 연결되지 않을 때:

1. **서버를 독립 실행하여 오류 확인**
   ```bash
   fastmcp run /절대/경로/server.py
   ```
   에러 메시지가 출력되면 해당 문제를 수정합니다.

2. **경로 확인**
   - 반드시 **절대 경로**를 사용하세요.
   - 상대 경로는 동작하지 않을 수 있습니다.

3. **fastmcp 경로 확인**
   ```bash
   which fastmcp      # macOS/Linux
   where fastmcp      # Windows
   ```
   PATH에 없으면 전체 경로를 `command`에 지정하세요.

4. **Python 패키지 확인**
   ```bash
   pip list | grep fastmcp
   ```

---

## 여러 서버 동시 사용

MCP 서버는 여러 개를 동시에 연결할 수 있습니다:

```
Claude
  ├── hello-mcp (기본 도구)
  ├── weather (날씨 조회)
  ├── file-manager (파일 관리)
  ├── itlog-db (DB 조회)
  └── memo-app (메모 관리)
```

Claude는 사용자 요청에 따라 적절한 서버의 도구를 자동으로 선택합니다:

```
"서울 날씨 어때?" → weather 서버의 get_weather 도구
"메모 목록 보여줘" → memo-app 서버의 list_memos 도구
"현장 카메라 조회해줘" → itlog-db 서버의 list_cameras 도구
```

---

## 환경변수 전달

MCP 서버에 환경변수를 전달해야 하는 경우:

### 설정 파일에서 env 지정

```json
{
  "mcpServers": {
    "weather": {
      "command": "fastmcp",
      "args": ["run", "/절대/경로/server.py"],
      "env": {
        "OPENWEATHER_API_KEY": "your_key_here"
      }
    }
  }
}
```

### .env 파일 사용

서버 코드에서 `python-dotenv`를 사용하면 `.env` 파일을 자동으로 읽습니다:

```python
from dotenv import load_dotenv
load_dotenv()  # 서버 파일과 같은 디렉토리 또는 상위 디렉토리의 .env 로드
```

---

## 참고 링크

- [Claude Code 공식 문서](https://docs.anthropic.com/en/docs/claude-code)
- [MCP 서버 설정 가이드](https://modelcontextprotocol.io/quickstart)
