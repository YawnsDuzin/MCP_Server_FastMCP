"""
Tutorial 02: 날씨 정보 MCP 서버
================================

외부 API(OpenWeatherMap)를 연동하여 실시간 날씨 정보를
조회하는 MCP 서버를 만듭니다.

학습 포인트:
- 비동기(async) Tool 정의
- 외부 API 호출 (httpx)
- 환경변수로 API 키 관리
- 에러 처리 패턴

실행 방법:
    1. .env 파일에 OPENWEATHER_API_KEY 설정
    2. fastmcp run server.py

API 키 없이 테스트:
    OPENWEATHER_API_KEY 없이 실행하면 데모 데이터를 반환합니다.
"""

import os
from datetime import datetime

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

# ============================================
# 데모 데이터 (API 키가 없을 때 사용)
# ============================================
DEMO_WEATHER = {
    "서울": {"temp": 3.5, "humidity": 45, "description": "맑음", "wind": 2.1},
    "부산": {"temp": 7.2, "humidity": 55, "description": "구름 조금", "wind": 3.5},
    "제주": {"temp": 9.8, "humidity": 65, "description": "흐림", "wind": 5.2},
    "대전": {"temp": 2.1, "humidity": 40, "description": "맑음", "wind": 1.8},
    "인천": {"temp": 2.8, "humidity": 50, "description": "안개", "wind": 2.5},
}

DEMO_FORECAST = {
    "서울": [
        {"date": "내일", "temp_min": -2, "temp_max": 5, "description": "맑음"},
        {"date": "모레", "temp_min": 0, "temp_max": 7, "description": "구름 많음"},
        {"date": "글피", "temp_min": -1, "temp_max": 4, "description": "눈"},
    ]
}


# ============================================
# Tool 정의: 현재 날씨 조회
# ============================================
@mcp.tool
async def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회합니다.

    Args:
        city: 도시 이름 (예: 서울, 부산, Tokyo, New York)
    """
    # API 키가 없으면 데모 데이터 반환
    if not API_KEY:
        if city in DEMO_WEATHER:
            data = DEMO_WEATHER[city]
            return (
                f"📍 {city} 현재 날씨 (데모 데이터)\n"
                f"🌡️ 온도: {data['temp']}°C\n"
                f"💧 습도: {data['humidity']}%\n"
                f"🌤️ 상태: {data['description']}\n"
                f"💨 풍속: {data['wind']}m/s\n"
                f"\n⚠️ 데모 모드입니다. 실제 데이터를 보려면 "
                f"OPENWEATHER_API_KEY를 설정하세요."
            )
        return (
            f"'{city}'의 데모 데이터가 없습니다. "
            f"사용 가능: {', '.join(DEMO_WEATHER.keys())}\n"
            f"실제 도시 검색은 OPENWEATHER_API_KEY를 설정하세요."
        )

    # 실제 API 호출
    try:
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

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]
        city_name = data["name"]

        return (
            f"📍 {city_name} 현재 날씨\n"
            f"🌡️ 온도: {temp}°C (체감 {feels_like}°C)\n"
            f"💧 습도: {humidity}%\n"
            f"🌤️ 상태: {description}\n"
            f"💨 풍속: {wind_speed}m/s\n"
            f"🕐 조회 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"'{city}' 도시를 찾을 수 없습니다. 영어 도시명을 시도해보세요."
        return f"API 오류가 발생했습니다: {e.response.status_code}"
    except httpx.RequestError as e:
        return f"네트워크 오류가 발생했습니다: {str(e)}"


# ============================================
# Tool 정의: 여러 도시 날씨 비교
# ============================================
@mcp.tool
async def compare_weather(cities: list[str]) -> str:
    """여러 도시의 날씨를 비교합니다.

    Args:
        cities: 비교할 도시 목록 (예: ["서울", "부산", "제주"])
    """
    results = []
    for city in cities:
        weather = await get_weather(city)
        results.append(weather)
        results.append("---")

    return "\n".join(results)


# ============================================
# Tool 정의: 날씨 기반 옷차림 추천
# ============================================
@mcp.tool
def recommend_outfit(temperature: float, is_raining: bool = False) -> str:
    """온도와 날씨에 맞는 옷차림을 추천합니다.

    Args:
        temperature: 현재 기온 (섭씨)
        is_raining: 비가 오는지 여부
    """
    if temperature >= 28:
        outfit = "반팔, 반바지, 샌들"
        tip = "자외선 차단제를 꼭 바르세요!"
    elif temperature >= 23:
        outfit = "반팔, 얇은 긴바지"
        tip = "가벼운 겉옷을 챙기면 좋아요."
    elif temperature >= 17:
        outfit = "긴팔, 가디건 또는 얇은 자켓"
        tip = "일교차가 클 수 있으니 겉옷 필수!"
    elif temperature >= 12:
        outfit = "자켓, 니트, 긴바지"
        tip = "바람이 불면 쌀쌀할 수 있어요."
    elif temperature >= 5:
        outfit = "코트, 두꺼운 니트, 목도리"
        tip = "보온에 신경 쓰세요."
    elif temperature >= -5:
        outfit = "패딩, 기모 안감, 장갑, 목도리"
        tip = "동상에 주의하세요!"
    else:
        outfit = "롱패딩, 방한 장비 완전 무장"
        tip = "가급적 외출을 자제하세요."

    rain_tip = "\n🌂 우산을 꼭 챙기세요!" if is_raining else ""

    return (
        f"🌡️ 기온: {temperature}°C\n"
        f"👕 추천 옷차림: {outfit}\n"
        f"💡 팁: {tip}"
        f"{rain_tip}"
    )


# ============================================
# Resource 정의: 지원 도시 목록
# ============================================
@mcp.resource("weather://cities")
def get_supported_cities() -> str:
    """데모 모드에서 지원하는 도시 목록을 반환합니다."""
    cities = "\n".join(f"  - {city}" for city in DEMO_WEATHER.keys())
    return f"데모 모드 지원 도시:\n{cities}\n\nAPI 키 설정 시 전 세계 도시 검색 가능"


# ============================================
# Prompt 정의: 여행 준비 프롬프트
# ============================================
@mcp.prompt
def travel_preparation(destination: str, days: str = "3") -> str:
    """여행 준비를 위한 프롬프트를 생성합니다."""
    return (
        f"{destination}으로 {days}일 여행을 계획하고 있습니다.\n\n"
        f"다음을 알려주세요:\n"
        f"1. 현재 {destination}의 날씨\n"
        f"2. 추천 옷차림\n"
        f"3. 여행 시 주의사항\n"
        f"4. 추천 준비물 체크리스트"
    )


# ============================================
# 서버 실행
# ============================================
if __name__ == "__main__":
    mcp.run()
