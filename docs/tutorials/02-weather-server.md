# Tutorial 02: 날씨 정보 MCP 서버

> **난이도**: ★★☆☆☆ (초급)
> **사전 지식**: Tutorial 01 완료, Python async 기초
> **결과물**: 실시간 날씨 조회 + 옷차림 추천 MCP 서버

## 이 튜토리얼에서 배우는 것

- 비동기(async) 도구 정의
- 외부 API (OpenWeatherMap) 연동
- 환경변수(`.env`)로 API 키 관리
- API 키 없이도 동작하는 데모 모드 패턴
- 에러 처리 (네트워크 오류, API 오류)

## 사전 준비

```bash
# 필수 패키지 설치 확인
pip install fastmcp httpx python-dotenv
```

**OpenWeatherMap API 키 (선택사항)**:
- [openweathermap.org](https://openweathermap.org/api)에서 무료 가입
- API 키 없이도 **데모 모드**로 학습 가능

---

## Step 1: 프로젝트 설정

### 환경변수 파일 (.env) 생성

```bash
cd tutorials/02_weather_server
```

프로젝트 루트의 `.env` 파일에 추가:

```env
OPENWEATHER_API_KEY=your_api_key_here
```

> API 키가 없으면 이 줄을 비워두세요. 서버가 자동으로 데모 모드로 실행됩니다.

---

## Step 2: 기본 서버 구조

```python
import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# 환경변수 로드
load_dotenv()

# 서버 생성
mcp = FastMCP("Weather Server")

# API 설정
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"
```

### `load_dotenv()` 는 무엇인가?

`.env` 파일의 내용을 환경변수로 로드합니다:

```
.env 파일                     Python 코드
OPENWEATHER_API_KEY=abc123 → os.getenv("OPENWEATHER_API_KEY") → "abc123"
```

---

## Step 3: 데모 데이터 준비

API 키가 없을 때도 테스트할 수 있도록 데모 데이터를 준비합니다:

```python
DEMO_WEATHER = {
    "서울": {"temp": 3.5, "humidity": 45, "description": "맑음", "wind": 2.1},
    "부산": {"temp": 7.2, "humidity": 55, "description": "구름 조금", "wind": 3.5},
    "제주": {"temp": 9.8, "humidity": 65, "description": "흐림", "wind": 5.2},
}
```

이 패턴은 실무에서도 유용합니다:
- 개발 환경에서 외부 의존성 없이 테스트
- API 장애 시 폴백 데이터 제공

---

## Step 4: 비동기 도구 만들기 (async)

외부 API를 호출하는 도구는 `async`로 만드는 것이 좋습니다:

```python
@mcp.tool
async def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회합니다.

    Args:
        city: 도시 이름 (예: 서울, 부산, Tokyo)
    """
    # API 키가 없으면 데모 데이터 반환
    if not API_KEY:
        if city in DEMO_WEATHER:
            data = DEMO_WEATHER[city]
            return f"📍 {city}: {data['temp']}°C, {data['description']}"
        return f"'{city}'의 데모 데이터가 없습니다."

    # 실제 API 호출
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/weather",
            params={
                "q": city,
                "appid": API_KEY,
                "units": "metric",
                "lang": "kr",
            },
        )
        response.raise_for_status()
        data = response.json()

    return f"📍 {data['name']}: {data['main']['temp']}°C"
```

### 왜 `async`인가?

```
동기 (sync)                    비동기 (async)
─────────────                  ─────────────
API 요청 보냄                   API 요청 보냄
(기다림...)                     (다른 작업 가능)
(기다림...)                     (다른 요청 처리)
응답 받음                       응답 받음
```

네트워크 요청처럼 기다리는 시간이 긴 작업은 `async`가 효율적입니다.

### httpx 사용법

```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.example.com/data",
        params={"key": "value"},  # URL 쿼리 파라미터
    )
    response.raise_for_status()   # 에러 시 예외 발생
    data = response.json()        # JSON 파싱
```

---

## Step 5: 에러 처리 추가

실제 서비스에서는 다양한 에러가 발생할 수 있습니다:

```python
try:
    async with httpx.AsyncClient() as client:
        response = await client.get(...)
        response.raise_for_status()
        data = response.json()
except httpx.HTTPStatusError as e:
    # API 에러 (404: 도시 없음, 401: 키 오류 등)
    if e.response.status_code == 404:
        return f"'{city}' 도시를 찾을 수 없습니다."
    return f"API 오류: {e.response.status_code}"
except httpx.RequestError as e:
    # 네트워크 에러 (연결 실패, 타임아웃 등)
    return f"네트워크 오류: {str(e)}"
```

---

## Step 6: 추가 도구 만들기

### 옷차림 추천 도구

```python
@mcp.tool
def recommend_outfit(temperature: float, is_raining: bool = False) -> str:
    """온도와 날씨에 맞는 옷차림을 추천합니다."""
    if temperature >= 23:
        outfit = "반팔, 얇은 긴바지"
    elif temperature >= 12:
        outfit = "자켓, 니트, 긴바지"
    elif temperature >= 5:
        outfit = "코트, 두꺼운 니트, 목도리"
    else:
        outfit = "패딩, 기모 안감, 장갑"

    rain_tip = "\n🌂 우산을 꼭 챙기세요!" if is_raining else ""
    return f"🌡️ {temperature}°C\n👕 추천: {outfit}{rain_tip}"
```

### 여러 도시 비교 도구

```python
@mcp.tool
async def compare_weather(cities: list[str]) -> str:
    """여러 도시의 날씨를 비교합니다."""
    results = []
    for city in cities:
        weather = await get_weather(city)
        results.append(weather)
    return "\n---\n".join(results)
```

`list[str]` 타입 힌트를 사용하면 Claude가 자동으로 리스트를 전달합니다.

---

## Step 7: 실행 및 테스트

### 서버 실행

```bash
fastmcp run tutorials/02_weather_server/server.py
```

### Claude Code에 등록

```bash
claude mcp add weather-server -- fastmcp run /절대경로/tutorials/02_weather_server/server.py
```

### 테스트 대화 예시

```
"서울 날씨 어때?"
→ get_weather("서울") 호출

"서울이랑 부산 날씨 비교해줘"
→ compare_weather(["서울", "부산"]) 호출

"지금 기온이 3도인데 뭐 입고 나가야 해?"
→ recommend_outfit(3.0) 호출

"제주도 3일 여행 준비물 알려줘"
→ travel_preparation("제주", "3") 프롬프트 + get_weather("제주") + recommend_outfit() 조합
```

---

## 전체 코드

완성된 코드: `tutorials/02_weather_server/server.py`

## 핵심 정리

| 개념 | 사용법 | 포인트 |
|------|--------|--------|
| async 도구 | `async def tool():` | 네트워크 요청에 사용 |
| 환경변수 | `load_dotenv()` + `os.getenv()` | API 키 보안 관리 |
| 에러 처리 | `try/except` | 안정적인 서비스 |
| 데모 모드 | `if not API_KEY:` | 개발/테스트 편의 |
| 리스트 파라미터 | `list[str]` | Claude가 자동 파싱 |

## 도전 과제

1. 미세먼지 정보를 추가해보세요 (OpenWeatherMap Air Pollution API)
2. 날씨 아이콘을 이모지로 변환하는 함수를 만들어보세요
3. 특정 시간대의 날씨를 예보하는 도구를 추가해보세요

## 다음 단계

➡️ [Tutorial 03: 파일 관리 서버](./03-file-manager.md)
