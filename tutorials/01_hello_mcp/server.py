"""
Tutorial 01: Hello MCP - 첫 번째 MCP 서버 만들기
=================================================

이 튜토리얼에서는 가장 간단한 MCP 서버를 만들어봅니다.
- 기본적인 Tool 정의
- Resource 정의
- Prompt 정의
- 서버 실행

실행 방법:
    fastmcp run server.py
    또는
    python server.py
"""

from fastmcp import FastMCP

# ============================================
# 1단계: FastMCP 서버 인스턴스 생성
# ============================================
# FastMCP()에 전달하는 문자열은 서버의 이름입니다.
# Claude가 이 서버를 식별할 때 사용합니다.
mcp = FastMCP("Hello MCP Server")


# ============================================
# 2단계: Tool 정의하기
# ============================================
# Tool은 Claude가 "실행"할 수 있는 함수입니다.
# @mcp.tool 데코레이터를 붙이면 자동으로 MCP 도구로 등록됩니다.
# 함수의 docstring이 도구 설명이 되고,
# 타입 힌트가 파라미터 스키마가 됩니다.


@mcp.tool
def add(a: int, b: int) -> int:
    """두 숫자를 더합니다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자
    """
    return a + b


@mcp.tool
def multiply(a: float, b: float) -> float:
    """두 숫자를 곱합니다.

    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자
    """
    return a * b


@mcp.tool
def greet(name: str, language: str = "ko") -> str:
    """사용자에게 인사합니다.

    Args:
        name: 인사할 사람의 이름
        language: 인사 언어 (ko: 한국어, en: 영어, ja: 일본어)
    """
    greetings = {
        "ko": f"안녕하세요, {name}님! 반갑습니다!",
        "en": f"Hello, {name}! Nice to meet you!",
        "ja": f"こんにちは、{name}さん！はじめまして！",
    }
    return greetings.get(language, greetings["ko"])


@mcp.tool
def reverse_string(text: str) -> str:
    """문자열을 뒤집습니다.

    Args:
        text: 뒤집을 문자열
    """
    return text[::-1]


# ============================================
# 3단계: Resource 정의하기
# ============================================
# Resource는 Claude가 "읽을" 수 있는 데이터입니다.
# URI 형식으로 접근합니다.


@mcp.resource("hello://info")
def get_server_info() -> str:
    """이 서버의 기본 정보를 반환합니다."""
    return """
    서버 이름: Hello MCP Server
    버전: 1.0.0
    설명: FastMCP 학습을 위한 첫 번째 서버입니다.
    제공 도구: add, multiply, greet, reverse_string
    """


@mcp.resource("hello://help/{topic}")
def get_help(topic: str) -> str:
    """주제별 도움말을 반환합니다."""
    help_topics = {
        "tools": "도구(Tool)는 Claude가 실행할 수 있는 함수입니다. "
        "@mcp.tool 데코레이터로 정의합니다.",
        "resources": "리소스(Resource)는 Claude가 읽을 수 있는 데이터입니다. "
        "URI로 접근하며 @mcp.resource 데코레이터로 정의합니다.",
        "prompts": "프롬프트(Prompt)는 재사용 가능한 메시지 템플릿입니다. "
        "@mcp.prompt 데코레이터로 정의합니다.",
    }
    return help_topics.get(topic, f"'{topic}'에 대한 도움말이 없습니다. "
                           f"사용 가능한 주제: {', '.join(help_topics.keys())}")


# ============================================
# 4단계: Prompt 정의하기
# ============================================
# Prompt는 재사용 가능한 메시지 템플릿입니다.
# Claude에게 특정 방식으로 응답하도록 안내합니다.


@mcp.prompt
def explain_code(code: str, language: str = "python") -> str:
    """코드를 설명해달라는 프롬프트를 생성합니다."""
    return f"""다음 {language} 코드를 초보자도 이해할 수 있게 설명해주세요.
각 줄이 무엇을 하는지 한국어로 상세히 설명해주세요.

```{language}
{code}
```"""


@mcp.prompt
def debug_error(error_message: str) -> str:
    """에러 디버깅을 위한 프롬프트를 생성합니다."""
    return f"""다음 에러 메시지를 분석하고 해결 방법을 알려주세요.

에러 메시지:
{error_message}

다음 형식으로 답변해주세요:
1. 에러 원인
2. 해결 방법
3. 예방 방법"""


# ============================================
# 5단계: 서버 실행
# ============================================
if __name__ == "__main__":
    mcp.run()
