# FastMCP API 레퍼런스

> FastMCP 공식 문서: [gofastmcp.com](https://gofastmcp.com)

## 설치

```bash
# pip
pip install fastmcp

# uv (권장)
uv pip install fastmcp
```

**요구 사항:** Python 3.10 이상

---

## FastMCP 서버 인스턴스

### 기본 생성

```python
from fastmcp import FastMCP

mcp = FastMCP("서버 이름")
```

### 서버 실행

```python
# 방법 1: 스크립트 내에서 실행
if __name__ == "__main__":
    mcp.run()

# 방법 2: CLI로 실행 (권장)
# $ fastmcp run server.py
```

---

## Tool (도구) API

### 기본 도구

```python
@mcp.tool
def my_tool(param: str) -> str:
    """도구 설명 (Claude가 읽습니다)."""
    return "결과"
```

### 비동기 도구

```python
@mcp.tool
async def async_tool(url: str) -> str:
    """비동기 도구 (API 호출 등에 적합)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.text
```

### 파라미터 타입

| Python 타입 | MCP 스키마 | 예시 |
|-------------|-----------|------|
| `str` | string | `name: str` |
| `int` | integer | `count: int` |
| `float` | number | `price: float` |
| `bool` | boolean | `active: bool` |
| `list[str]` | array of strings | `tags: list[str]` |
| `dict[str, str]` | object | `meta: dict[str, str]` |
| `Optional[str]` | string (nullable) | `note: str \| None = None` |

### 기본값이 있는 파라미터

```python
@mcp.tool
def search(
    keyword: str,                    # 필수
    limit: int = 10,                 # 선택 (기본값: 10)
    case_sensitive: bool = False,    # 선택 (기본값: False)
) -> str:
    """검색을 수행합니다."""
    ...
```

### 복잡한 입력 (Pydantic 모델)

```python
from pydantic import BaseModel

class SearchFilter(BaseModel):
    keyword: str
    category: str = "all"
    min_date: str | None = None

@mcp.tool
def advanced_search(filter: SearchFilter) -> str:
    """고급 검색을 수행합니다."""
    ...
```

---

## Resource (리소스) API

### 정적 리소스

```python
@mcp.resource("myapp://config")
def get_config() -> str:
    """앱 설정을 반환합니다."""
    return "설정 데이터"
```

### 동적 리소스 (URI 파라미터)

```python
@mcp.resource("myapp://users/{user_id}")
def get_user(user_id: str) -> str:
    """사용자 정보를 반환합니다."""
    return f"사용자 {user_id}의 정보"
```

### URI 규칙

```
protocol://path/to/resource
──────── ─────────────────
  스킴        경로

예시:
  weather://forecast/seoul
  db://tables/users
  file://documents/report.txt
```

---

## Prompt (프롬프트) API

### 기본 프롬프트

```python
@mcp.prompt
def summarize(text: str) -> str:
    """텍스트 요약 프롬프트를 생성합니다."""
    return f"다음 텍스트를 3줄로 요약해주세요:\n\n{text}"
```

### 파라미터가 있는 프롬프트

```python
@mcp.prompt
def code_review(code: str, language: str = "python") -> str:
    """코드 리뷰 프롬프트를 생성합니다."""
    return f"""다음 {language} 코드를 리뷰해주세요.

```{language}
{code}
```

다음 관점에서 분석해주세요:
1. 코드 품질
2. 보안 취약점
3. 개선 제안"""
```

---

## 서버 실행 방법

### CLI 실행

```bash
# 기본 실행
fastmcp run server.py

# python -m으로 실행
python -m fastmcp run server.py
```

### 스크립트 내에서 실행

```python
if __name__ == "__main__":
    mcp.run()
```

그 후 `python server.py`로 실행합니다.

---

## 자주 사용하는 패턴

### 데모/라이브 모드 전환

```python
import os

API_KEY = os.getenv("API_KEY", "")

@mcp.tool
def fetch_data() -> str:
    if not API_KEY:
        return "데모 데이터"
    # 실제 API 호출
    ...
```

### 에러 처리

```python
@mcp.tool
def safe_operation(param: str) -> str:
    try:
        result = risky_operation(param)
        return f"✅ 성공: {result}"
    except ValueError as e:
        return f"❌ 입력 오류: {str(e)}"
    except Exception as e:
        return f"❌ 예상치 못한 오류: {str(e)}"
```

### 데이터베이스 연결

```python
import sqlite3

def _get_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool
def query_data(keyword: str) -> str:
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM items WHERE name LIKE ?",
        (f"%{keyword}%",)
    ).fetchall()
    conn.close()
    return "\n".join(str(dict(row)) for row in rows)
```

---

## 참고 링크

- [FastMCP 공식 문서](https://gofastmcp.com)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP 공식 사양](https://spec.modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
