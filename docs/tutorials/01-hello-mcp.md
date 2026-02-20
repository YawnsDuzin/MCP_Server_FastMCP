# Tutorial 01: Hello MCP - 첫 번째 MCP 서버 만들기

> **난이도**: ★☆☆☆☆ (입문)
> **소요 시간**: 따라하면서 배우기
> **사전 지식**: Python 기초
> **결과물**: 기본 도구(Tool), 리소스(Resource), 프롬프트(Prompt)를 갖춘 MCP 서버

## 이 튜토리얼에서 배우는 것

- FastMCP 서버 인스턴스 생성
- `@mcp.tool` 데코레이터로 도구 만들기
- `@mcp.resource` 데코레이터로 리소스 만들기
- `@mcp.prompt` 데코레이터로 프롬프트 만들기
- 서버를 실행하고 Claude에서 사용하기

## 사전 준비

[환경 설정](../getting-started/environment-setup.md)이 완료되어 있어야 합니다.

```bash
# 가상환경 활성화 확인
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows

# FastMCP 설치 확인
python -c "import fastmcp; print('OK')"
```

---

## Step 1: 빈 서버 만들기

`tutorials/01_hello_mcp/server.py` 파일을 열어봅시다.

가장 기본적인 MCP 서버는 이렇게 생겼습니다:

```python
from fastmcp import FastMCP

# 서버 인스턴스 생성
mcp = FastMCP("Hello MCP Server")

# 서버 실행
if __name__ == "__main__":
    mcp.run()
```

**코드 설명:**

| 줄 | 코드 | 설명 |
|----|------|------|
| 1 | `from fastmcp import FastMCP` | FastMCP 프레임워크를 가져옵니다 |
| 4 | `mcp = FastMCP("Hello MCP Server")` | 서버 인스턴스를 생성합니다. 문자열은 서버 이름입니다 |
| 7 | `mcp.run()` | 서버를 시작합니다 |

이것만으로도 동작하는 MCP 서버입니다! 다만 아직 아무 도구도 없죠.

---

## Step 2: 첫 번째 Tool 만들기

**Tool**은 Claude가 실행할 수 있는 함수입니다. `@mcp.tool` 데코레이터를 붙이면 됩니다.

```python
@mcp.tool
def add(a: int, b: int) -> int:
    """두 숫자를 더합니다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자
    """
    return a + b
```

### 핵심 규칙 3가지

#### 규칙 1: 타입 힌트는 필수

```python
# ✅ 좋은 예 - 타입 힌트 있음
@mcp.tool
def add(a: int, b: int) -> int:
    return a + b

# ❌ 나쁜 예 - 타입 힌트 없음
@mcp.tool
def add(a, b):
    return a + b
```

타입 힌트가 있어야 FastMCP가 자동으로 입력 스키마를 생성할 수 있습니다. Claude는 이 스키마를 보고 어떤 값을 넣어야 하는지 파악합니다.

#### 규칙 2: docstring이 도구 설명이 됨

```python
@mcp.tool
def greet(name: str) -> str:
    """사용자에게 인사합니다."""  # ← Claude가 이 설명을 읽습니다!
    return f"안녕하세요, {name}님!"
```

Claude는 docstring을 읽고 "이 도구가 무엇을 하는지" 판단합니다. 명확하게 작성하세요.

#### 규칙 3: 기본값이 있는 파라미터는 선택사항

```python
@mcp.tool
def greet(name: str, language: str = "ko") -> str:
    """사용자에게 인사합니다.

    Args:
        name: 인사할 사람의 이름
        language: 인사 언어 (ko, en, ja)
    """
    ...
```

`language`에 기본값 `"ko"`가 있으므로, Claude는 이 파라미터를 생략할 수 있습니다.

---

## Step 3: 도구 추가하기

여러 개의 도구를 자유롭게 추가할 수 있습니다:

```python
@mcp.tool
def multiply(a: float, b: float) -> float:
    """두 숫자를 곱합니다."""
    return a * b

@mcp.tool
def reverse_string(text: str) -> str:
    """문자열을 뒤집습니다."""
    return text[::-1]
```

---

## Step 4: Resource 만들기

**Resource**는 Claude가 읽을 수 있는 정보입니다. URI 형식으로 접근합니다.

```python
@mcp.resource("hello://info")
def get_server_info() -> str:
    """이 서버의 기본 정보를 반환합니다."""
    return """
    서버 이름: Hello MCP Server
    버전: 1.0.0
    설명: FastMCP 학습을 위한 첫 번째 서버입니다.
    """
```

### 동적 Resource (URI 파라미터)

URI에 `{변수명}`을 넣으면 동적 리소스를 만들 수 있습니다:

```python
@mcp.resource("hello://help/{topic}")
def get_help(topic: str) -> str:
    """주제별 도움말을 반환합니다."""
    help_topics = {
        "tools": "Tool은 Claude가 실행할 수 있는 함수입니다.",
        "resources": "Resource는 Claude가 읽을 수 있는 데이터입니다.",
    }
    return help_topics.get(topic, f"'{topic}'에 대한 도움말이 없습니다.")
```

- `hello://help/tools` → "Tool은 Claude가 실행할 수 있는 함수입니다."
- `hello://help/resources` → "Resource는 Claude가 읽을 수 있는 데이터입니다."

---

## Step 5: Prompt 만들기

**Prompt**는 재사용 가능한 메시지 템플릿입니다:

```python
@mcp.prompt
def explain_code(code: str, language: str = "python") -> str:
    """코드를 설명해달라는 프롬프트를 생성합니다."""
    return f"""다음 {language} 코드를 초보자도 이해할 수 있게 설명해주세요.

```{language}
{code}
```"""
```

프롬프트는 자주 사용하는 질문 패턴을 템플릿으로 만들어 놓은 것입니다.

---

## Step 6: 서버 실행하기

### 방법 1: fastmcp 명령어 (권장)

```bash
cd tutorials/01_hello_mcp
fastmcp run server.py
```

### 방법 2: Python 직접 실행

```bash
python tutorials/01_hello_mcp/server.py
```

### 서버가 실행되면?

서버가 시작되면 MCP 프로토콜을 통해 클라이언트(Claude)의 연결을 기다립니다. 터미널에는 별다른 출력이 없을 수 있지만, 정상입니다.

---

## Step 7: Claude Code에서 사용하기

### 서버 등록

```bash
# Claude Code에 MCP 서버 추가
claude mcp add hello-mcp -- fastmcp run /절대경로/tutorials/01_hello_mcp/server.py
```

### Claude에서 테스트

Claude Code를 시작하고 다음과 같이 요청해보세요:

```
"3과 5를 더해줘"
→ Claude가 add(3, 5) 도구를 호출 → 결과: 8

"내 이름은 홍길동이야. 인사해줘"
→ Claude가 greet("홍길동") 도구를 호출 → 결과: 안녕하세요, 홍길동님!

"hello world를 뒤집어줘"
→ Claude가 reverse_string("hello world") 도구를 호출 → 결과: dlrow olleh
```

---

## 전체 코드

완성된 코드는 `tutorials/01_hello_mcp/server.py`에 있습니다.

핵심 구조를 다시 정리하면:

```python
from fastmcp import FastMCP

mcp = FastMCP("Hello MCP Server")

# 1. Tool: Claude가 실행하는 함수
@mcp.tool
def add(a: int, b: int) -> int:
    """두 숫자를 더합니다."""
    return a + b

# 2. Resource: Claude가 읽는 데이터
@mcp.resource("hello://info")
def get_info() -> str:
    """서버 정보"""
    return "Hello MCP Server v1.0"

# 3. Prompt: 재사용 메시지 템플릿
@mcp.prompt
def explain_code(code: str) -> str:
    """코드 설명 프롬프트"""
    return f"이 코드를 설명해줘: {code}"

if __name__ == "__main__":
    mcp.run()
```

## 핵심 정리

| 개념 | 데코레이터 | 역할 | 비유 |
|------|-----------|------|------|
| Tool | `@mcp.tool` | 함수 실행 | POST API |
| Resource | `@mcp.resource("uri")` | 데이터 읽기 | GET API |
| Prompt | `@mcp.prompt` | 메시지 템플릿 | API 문서 예시 |

## 도전 과제

1. 나만의 Tool을 하나 추가해보세요 (예: 나이 계산기, BMI 계산기)
2. Resource를 하나 더 만들어보세요 (예: 좋아하는 책 목록)
3. 한국어/영어 번역 프롬프트를 만들어보세요

## 다음 단계

기본기를 익혔으니, 외부 API를 연동하는 서버를 만들어봅시다!

➡️ [Tutorial 02: 날씨 정보 서버](./02-weather-server.md)
