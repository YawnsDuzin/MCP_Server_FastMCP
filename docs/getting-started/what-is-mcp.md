# MCP란 무엇인가?

## 개요

**MCP (Model Context Protocol)** 는 AI 모델(LLM)이 외부 도구와 데이터에 접근할 수 있도록 해주는 **표준 프로토콜**입니다.

쉽게 말하면, Claude 같은 AI에게 **"손과 발"** 을 달아주는 기술입니다.

## 왜 MCP가 필요한가?

### MCP 없이 Claude를 사용할 때

```
사용자: "우리 서버에 있는 카메라 목록 보여줘"
Claude: "죄송합니다. 저는 외부 데이터베이스에 접근할 수 없습니다."
```

### MCP를 사용할 때

```
사용자: "우리 서버에 있는 카메라 목록 보여줘"
Claude: (MCP 서버의 list_cameras 도구를 호출)
        "현재 총 10대의 카메라가 등록되어 있습니다..."
```

## 핵심 개념

MCP는 **서버-클라이언트 구조**입니다:

```
┌─────────────────┐     MCP 프로토콜     ┌─────────────────┐
│   MCP 클라이언트  │ ◄──────────────────► │   MCP 서버       │
│   (Claude Code)  │                      │   (당신이 만듦)   │
└─────────────────┘                      └─────────────────┘
        │                                         │
        ▼                                         ▼
   사용자와 대화                              외부 시스템
                                          (DB, API, 파일 등)
```

### MCP 서버의 3가지 구성 요소

| 구성 요소 | 설명 | 비유 |
|----------|------|------|
| **Tool (도구)** | Claude가 **실행**할 수 있는 함수 | POST API 엔드포인트 |
| **Resource (리소스)** | Claude가 **읽을** 수 있는 데이터 | GET API 엔드포인트 |
| **Prompt (프롬프트)** | 재사용 가능한 **메시지 템플릿** | API 요청 템플릿 |

### Tool (도구) - 가장 많이 사용

```python
@mcp.tool
def search_camera(site_name: str) -> str:
    """현장의 카메라를 검색합니다."""
    # 데이터베이스 쿼리 실행
    return "검색 결과..."
```

Claude가 사용자 요청을 분석하여 적절한 Tool을 **자동으로** 호출합니다.

### Resource (리소스) - 컨텍스트 제공

```python
@mcp.resource("config://database")
def get_db_config() -> str:
    """데이터베이스 설정 정보를 제공합니다."""
    return "DB 서버: localhost, 포트: 1433"
```

Claude에게 참고할 수 있는 **배경 정보**를 제공합니다.

### Prompt (프롬프트) - 워크플로우 템플릿

```python
@mcp.prompt
def analyze_site(site_name: str) -> str:
    """현장 분석 프롬프트를 생성합니다."""
    return f"{site_name} 현장을 분석해주세요..."
```

반복되는 질문 패턴을 **템플릿**으로 만들어 재사용합니다.

## FastMCP란?

**FastMCP**는 Python으로 MCP 서버를 만드는 **프레임워크**입니다.

MCP 프로토콜을 직접 구현하려면 복잡하지만, FastMCP를 사용하면 **Python 함수에 데코레이터를 붙이는 것만으로** MCP 서버를 만들 수 있습니다.

### FastMCP의 장점

1. **간단함**: Python 함수 + 데코레이터 = MCP 서버
2. **자동화**: 타입 힌트에서 스키마 자동 생성
3. **문서화**: docstring이 자동으로 도구 설명이 됨
4. **검증**: 입력값 자동 검증 (Pydantic 기반)

### 최소 코드 예시

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool
def hello(name: str) -> str:
    """인사를 합니다."""
    return f"안녕하세요, {name}님!"

if __name__ == "__main__":
    mcp.run()
```

이 코드 **6줄**이면 MCP 서버가 완성됩니다.

## MCP의 동작 흐름

```
1. 사용자가 Claude에게 요청
   "서울 본사 카메라 목록 보여줘"

2. Claude가 요청을 분석
   → "list_cameras 도구를 site_id=1로 호출해야겠다"

3. Claude가 MCP 서버에 도구 호출 요청
   → list_cameras(site_id=1)

4. MCP 서버가 도구 실행
   → 데이터베이스 쿼리 실행
   → 결과 반환

5. Claude가 결과를 사용자에게 전달
   "서울 본사에는 다음 카메라가 있습니다: ..."
```

## 다음 단계

MCP가 무엇인지 이해했다면, 이제 직접 만들어볼 차례입니다!

➡️ [환경 설정하기](./environment-setup.md)로 이동하세요.
