"""
Tutorial 04: MSSQL 데이터베이스 MCP 서버 (IT-Log 실전)
=======================================================

MSSQL 데이터베이스에 연결하여 IT-Log 시스템의 데이터를
조회하는 실전 MCP 서버를 만듭니다.

학습 포인트:
- SQLAlchemy로 MSSQL 연결
- 안전한 SQL 쿼리 (SQL Injection 방지)
- 비동기 데이터베이스 작업
- 환경변수 기반 설정
- 실무 데이터 조회 패턴

실행 방법:
    1. .env 파일에 DB 접속 정보 설정
    2. pip install sqlalchemy pyodbc
    3. fastmcp run server.py

DB 없이 테스트:
    DB 연결 없이 실행하면 데모 데이터를 사용합니다.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from fastmcp import FastMCP

# 환경변수 로드
load_dotenv()

# 서버 생성
mcp = FastMCP("IT-Log Database Server")

# ============================================
# 데이터베이스 설정
# ============================================
DB_CONFIG = {
    "server": os.getenv("MSSQL_SERVER", "localhost"),
    "database": os.getenv("MSSQL_DATABASE", "ITLog"),
    "username": os.getenv("MSSQL_USERNAME", "sa"),
    "password": os.getenv("MSSQL_PASSWORD", ""),
    "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server"),
}

# SQLAlchemy 엔진 (실제 DB 사용 시)
engine = None

try:
    from sqlalchemy import create_engine, text

    if DB_CONFIG["password"]:  # 비밀번호가 설정되어 있으면 실제 DB 연결 시도
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

# ============================================
# 데모 데이터 (DB 없이 테스트용)
# ============================================
DEMO_SITES = [
    {"site_id": 1, "site_name": "서울 본사", "location": "서울시 강남구", "status": "운영중", "camera_count": 24},
    {"site_id": 2, "site_name": "부산 지사", "location": "부산시 해운대구", "status": "운영중", "camera_count": 16},
    {"site_id": 3, "site_name": "대전 데이터센터", "location": "대전시 유성구", "status": "운영중", "camera_count": 32},
    {"site_id": 4, "site_name": "인천 물류센터", "location": "인천시 남동구", "status": "점검중", "camera_count": 20},
    {"site_id": 5, "site_name": "제주 연구소", "location": "제주시 첨단로", "status": "운영중", "camera_count": 8},
]

DEMO_CAMERAS = [
    {"camera_id": "CAM-001", "site_id": 1, "name": "본사 로비", "type": "PTZ", "status": "정상", "ip": "192.168.1.101"},
    {"camera_id": "CAM-002", "site_id": 1, "name": "본사 주차장 A", "type": "고정형", "status": "정상", "ip": "192.168.1.102"},
    {"camera_id": "CAM-003", "site_id": 1, "name": "본사 주차장 B", "type": "고정형", "status": "점검중", "ip": "192.168.1.103"},
    {"camera_id": "CAM-004", "site_id": 2, "name": "부산 출입구", "type": "PTZ", "status": "정상", "ip": "192.168.2.101"},
    {"camera_id": "CAM-005", "site_id": 2, "name": "부산 서버실", "type": "고정형", "status": "정상", "ip": "192.168.2.102"},
    {"camera_id": "CAM-006", "site_id": 3, "name": "DC 출입구", "type": "PTZ", "status": "정상", "ip": "192.168.3.101"},
    {"camera_id": "CAM-007", "site_id": 3, "name": "DC 서버룸 A", "type": "고정형", "status": "정상", "ip": "192.168.3.102"},
    {"camera_id": "CAM-008", "site_id": 3, "name": "DC 서버룸 B", "type": "고정형", "status": "장애", "ip": "192.168.3.103"},
    {"camera_id": "CAM-009", "site_id": 4, "name": "물류 하역장", "type": "PTZ", "status": "정상", "ip": "192.168.4.101"},
    {"camera_id": "CAM-010", "site_id": 5, "name": "제주 정문", "type": "고정형", "status": "정상", "ip": "192.168.5.101"},
]

DEMO_EVENTS = [
    {"event_id": 1, "camera_id": "CAM-001", "event_type": "움직임 감지", "timestamp": "2026-02-20 09:15:00", "severity": "보통"},
    {"event_id": 2, "camera_id": "CAM-003", "event_type": "연결 끊김", "timestamp": "2026-02-20 08:30:00", "severity": "높음"},
    {"event_id": 3, "camera_id": "CAM-008", "event_type": "장애 발생", "timestamp": "2026-02-20 07:45:00", "severity": "긴급"},
    {"event_id": 4, "camera_id": "CAM-006", "event_type": "움직임 감지", "timestamp": "2026-02-20 10:00:00", "severity": "낮음"},
    {"event_id": 5, "camera_id": "CAM-009", "event_type": "움직임 감지", "timestamp": "2026-02-20 09:45:00", "severity": "보통"},
]


# ============================================
# 헬퍼 함수: DB 쿼리 실행
# ============================================
def _execute_query(query_text: str, params: dict | None = None) -> list[dict]:
    """SQLAlchemy를 사용하여 안전하게 쿼리를 실행합니다."""
    if engine is None:
        raise RuntimeError("데이터베이스 연결이 설정되지 않았습니다.")

    with engine.connect() as conn:
        result = conn.execute(text(query_text), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]


# ============================================
# Tool: 현장(Site) 목록 조회
# ============================================
@mcp.tool
def list_sites(status: str = "") -> str:
    """모든 현장(사이트) 목록을 조회합니다.

    Args:
        status: 상태 필터 (예: "운영중", "점검중"). 비우면 전체 조회.
    """
    if DB_MODE == "demo":
        sites = DEMO_SITES
        if status:
            sites = [s for s in sites if s["status"] == status]
    else:
        query = "SELECT site_id, site_name, location, status, camera_count FROM Sites"
        params = {}
        if status:
            query += " WHERE status = :status"
            params["status"] = status
        sites = _execute_query(query, params)

    if not sites:
        return f"조건에 맞는 현장이 없습니다." + (f" (필터: {status})" if status else "")

    result = [f"📋 현장 목록 {'(필터: ' + status + ')' if status else ''}", ""]
    result.append(f"{'ID':<4} {'현장명':<16} {'위치':<16} {'상태':<8} {'카메라'}")
    result.append("-" * 60)

    for site in sites:
        result.append(
            f"{site['site_id']:<4} {site['site_name']:<16} "
            f"{site['location']:<16} {site['status']:<8} {site['camera_count']}대"
        )

    result.append(f"\n총 {len(sites)}개 현장" + f" [{DB_MODE} 모드]")
    return "\n".join(result)


# ============================================
# Tool: 현장별 카메라 목록 조회
# ============================================
@mcp.tool
def list_cameras(site_id: int = 0, status: str = "") -> str:
    """카메라 목록을 조회합니다.

    Args:
        site_id: 현장 ID (0이면 전체 조회)
        status: 상태 필터 (예: "정상", "점검중", "장애")
    """
    if DB_MODE == "demo":
        cameras = DEMO_CAMERAS
        if site_id > 0:
            cameras = [c for c in cameras if c["site_id"] == site_id]
        if status:
            cameras = [c for c in cameras if c["status"] == status]
    else:
        query = "SELECT camera_id, site_id, name, type, status, ip FROM Cameras WHERE 1=1"
        params = {}
        if site_id > 0:
            query += " AND site_id = :site_id"
            params["site_id"] = site_id
        if status:
            query += " AND status = :status"
            params["status"] = status
        cameras = _execute_query(query, params)

    if not cameras:
        filter_info = []
        if site_id > 0:
            filter_info.append(f"현장 ID: {site_id}")
        if status:
            filter_info.append(f"상태: {status}")
        return f"조건에 맞는 카메라가 없습니다. ({', '.join(filter_info)})"

    # 현장명 찾기
    site_name = ""
    if site_id > 0:
        for site in DEMO_SITES:
            if site["site_id"] == site_id:
                site_name = site["site_name"]
                break

    header = "📷 카메라 목록"
    if site_name:
        header += f" - {site_name}"

    result = [header, ""]
    result.append(f"{'ID':<10} {'이름':<16} {'타입':<8} {'상태':<8} {'IP'}")
    result.append("-" * 65)

    for cam in cameras:
        result.append(
            f"{cam['camera_id']:<10} {cam['name']:<16} "
            f"{cam['type']:<8} {cam['status']:<8} {cam['ip']}"
        )

    result.append(f"\n총 {len(cameras)}대" + f" [{DB_MODE} 모드]")
    return "\n".join(result)


# ============================================
# Tool: 이벤트/알람 조회
# ============================================
@mcp.tool
def list_events(camera_id: str = "", severity: str = "", limit: int = 20) -> str:
    """이벤트(알람) 목록을 조회합니다.

    Args:
        camera_id: 카메라 ID 필터 (예: "CAM-001")
        severity: 심각도 필터 (낮음, 보통, 높음, 긴급)
        limit: 최대 조회 건수 (기본: 20)
    """
    if DB_MODE == "demo":
        events = DEMO_EVENTS
        if camera_id:
            events = [e for e in events if e["camera_id"] == camera_id]
        if severity:
            events = [e for e in events if e["severity"] == severity]
        events = events[:limit]
    else:
        query = "SELECT TOP(:limit) event_id, camera_id, event_type, timestamp, severity FROM Events WHERE 1=1"
        params = {"limit": limit}
        if camera_id:
            query += " AND camera_id = :camera_id"
            params["camera_id"] = camera_id
        if severity:
            query += " AND severity = :severity"
            params["severity"] = severity
        query += " ORDER BY timestamp DESC"
        events = _execute_query(query, params)

    if not events:
        return "조건에 맞는 이벤트가 없습니다."

    severity_icons = {
        "낮음": "🟢",
        "보통": "🟡",
        "높음": "🟠",
        "긴급": "🔴",
    }

    result = ["🚨 이벤트 목록", ""]
    result.append(f"{'심각도':<4} {'카메라':<10} {'유형':<12} {'시간'}")
    result.append("-" * 55)

    for event in events:
        icon = severity_icons.get(event["severity"], "⚪")
        result.append(
            f"{icon} {event['camera_id']:<10} "
            f"{event['event_type']:<12} {event['timestamp']}"
        )

    result.append(f"\n총 {len(events)}건" + f" [{DB_MODE} 모드]")
    return "\n".join(result)


# ============================================
# Tool: 현장 상태 요약 (대시보드)
# ============================================
@mcp.tool
def dashboard() -> str:
    """전체 시스템 현황을 대시보드 형태로 보여줍니다."""
    if DB_MODE == "demo":
        sites = DEMO_SITES
        cameras = DEMO_CAMERAS
        events = DEMO_EVENTS
    else:
        sites = _execute_query("SELECT * FROM Sites")
        cameras = _execute_query("SELECT * FROM Cameras")
        events = _execute_query("SELECT TOP(10) * FROM Events ORDER BY timestamp DESC")

    total_sites = len(sites)
    active_sites = sum(1 for s in sites if s.get("status") == "운영중")
    total_cameras = len(cameras)
    normal_cameras = sum(1 for c in cameras if c.get("status") == "정상")
    error_cameras = sum(1 for c in cameras if c.get("status") == "장애")
    urgent_events = sum(1 for e in events if e.get("severity") in ("높음", "긴급"))

    result = [
        "╔══════════════════════════════════════╗",
        "║        IT-Log 시스템 대시보드          ║",
        f"║  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}               ║",
        "╠══════════════════════════════════════╣",
        f"║  📍 현장: {active_sites}/{total_sites}개 운영중                 ║",
        f"║  📷 카메라: {normal_cameras}/{total_cameras}대 정상              ║",
        f"║  ⚠️  장애 카메라: {error_cameras}대                     ║",
        f"║  🚨 긴급 이벤트: {urgent_events}건                    ║",
        "╚══════════════════════════════════════╝",
        "",
        f"[{DB_MODE} 모드]",
    ]
    return "\n".join(result)


# ============================================
# Tool: 커스텀 쿼리 (읽기 전용)
# ============================================
@mcp.tool
def run_query(query: str) -> str:
    """읽기 전용 SQL 쿼리를 실행합니다. (SELECT만 허용)

    Args:
        query: 실행할 SQL SELECT 쿼리
    """
    # SELECT만 허용 (SQL Injection 방지)
    cleaned = query.strip().upper()
    if not cleaned.startswith("SELECT"):
        return "❌ 보안 정책: SELECT 쿼리만 실행할 수 있습니다."

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "EXEC", "EXECUTE"]
    for word in forbidden:
        if word in cleaned:
            return f"❌ 보안 정책: '{word}' 명령은 사용할 수 없습니다."

    if DB_MODE == "demo":
        return (
            "⚠️ 데모 모드에서는 커스텀 쿼리를 실행할 수 없습니다.\n"
            "실제 DB를 연결하려면 .env 파일에 MSSQL 접속 정보를 설정하세요.\n\n"
            "사용 가능한 도구:\n"
            "  - list_sites: 현장 목록 조회\n"
            "  - list_cameras: 카메라 목록 조회\n"
            "  - list_events: 이벤트 조회\n"
            "  - dashboard: 대시보드"
        )

    try:
        rows = _execute_query(query)
        if not rows:
            return "쿼리 결과가 없습니다."

        # 테이블 형태로 출력
        columns = list(rows[0].keys())
        result = [" | ".join(columns), "-" * (len(" | ".join(columns)))]
        for row in rows[:50]:  # 최대 50행
            result.append(" | ".join(str(row.get(col, "")) for col in columns))

        if len(rows) > 50:
            result.append(f"\n... 외 {len(rows) - 50}행 (총 {len(rows)}행)")

        return "\n".join(result)
    except Exception as e:
        return f"❌ 쿼리 실행 오류: {str(e)}"


# ============================================
# Resource: DB 연결 상태
# ============================================
@mcp.resource("db://status")
def db_status() -> str:
    """데이터베이스 연결 상태를 확인합니다."""
    return (
        f"데이터베이스 연결 상태\n"
        f"  모드: {DB_MODE}\n"
        f"  서버: {DB_CONFIG['server']}\n"
        f"  데이터베이스: {DB_CONFIG['database']}\n"
        f"  드라이버: {DB_CONFIG['driver']}\n"
        f"\n{'✅ 실제 DB에 연결됨' if DB_MODE == 'live' else '⚠️ 데모 모드 (DB 미연결)'}"
    )


# ============================================
# Resource: 테이블 스키마 정보
# ============================================
@mcp.resource("db://schema")
def db_schema() -> str:
    """데이터베이스 테이블 스키마 정보를 반환합니다."""
    return """
IT-Log 데이터베이스 스키마

[Sites 테이블] - 현장 정보
  - site_id (INT, PK): 현장 고유 ID
  - site_name (NVARCHAR): 현장 이름
  - location (NVARCHAR): 위치
  - status (NVARCHAR): 상태 (운영중, 점검중, 중지)
  - camera_count (INT): 카메라 수

[Cameras 테이블] - 카메라 정보
  - camera_id (VARCHAR, PK): 카메라 고유 ID (예: CAM-001)
  - site_id (INT, FK): 소속 현장 ID
  - name (NVARCHAR): 카메라 이름
  - type (NVARCHAR): 카메라 유형 (PTZ, 고정형)
  - status (NVARCHAR): 상태 (정상, 점검중, 장애)
  - ip (VARCHAR): IP 주소

[Events 테이블] - 이벤트/알람
  - event_id (INT, PK): 이벤트 고유 ID
  - camera_id (VARCHAR, FK): 카메라 ID
  - event_type (NVARCHAR): 이벤트 유형
  - timestamp (DATETIME): 발생 시각
  - severity (NVARCHAR): 심각도 (낮음, 보통, 높음, 긴급)
"""


# ============================================
# Prompt: 현장 상태 분석 요청
# ============================================
@mcp.prompt
def analyze_site(site_name: str) -> str:
    """특정 현장의 상태를 분석하는 프롬프트입니다."""
    return (
        f"'{site_name}' 현장의 현재 상태를 분석해주세요.\n\n"
        f"다음 단계로 진행해주세요:\n"
        f"1. list_sites로 현장 기본 정보 확인\n"
        f"2. list_cameras로 해당 현장 카메라 상태 확인\n"
        f"3. list_events로 최근 이벤트 확인\n"
        f"4. 종합 분석 및 조치 사항 보고"
    )


# ============================================
# 서버 실행
# ============================================
if __name__ == "__main__":
    mcp.run()
