"""
Tutorial 05: 메모/노트 MCP 서버 (SQLite + CRUD)
=================================================

SQLite 데이터베이스를 사용하여 메모를 관리하는
완전한 CRUD(Create, Read, Update, Delete) MCP 서버입니다.

학습 포인트:
- SQLite 데이터베이스 (표준 라이브러리 활용)
- 완전한 CRUD 작업 구현
- 태그 시스템 (다대다 관계)
- 검색 기능
- 데이터 초기화 및 마이그레이션

실행 방법:
    fastmcp run server.py
    또는
    python server.py

첫 실행 시 자동으로 데이터베이스와 테이블이 생성됩니다.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

# ============================================
# 설정
# ============================================
mcp = FastMCP("Memo App Server")

# 데이터베이스 파일 경로 (서버 파일과 같은 디렉토리에 생성)
DB_PATH = Path(__file__).parent / "memos.db"


# ============================================
# 데이터베이스 초기화
# ============================================
def _init_db():
    """데이터베이스와 테이블을 초기화합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 메모 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT '일반',
            is_pinned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 태그 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # 메모-태그 연결 테이블 (다대다 관계)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memo_tags (
            memo_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (memo_id, tag_id),
            FOREIGN KEY (memo_id) REFERENCES memos(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# 서버 시작 시 DB 초기화
_init_db()


# ============================================
# 헬퍼 함수
# ============================================
def _get_db():
    """데이터베이스 연결을 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _format_memo(memo: sqlite3.Row, include_content: bool = True) -> str:
    """메모를 보기 좋은 문자열로 변환합니다."""
    pin = "📌 " if memo["is_pinned"] else ""
    result = f"{pin}[#{memo['id']}] {memo['title']}"
    result += f"\n  📂 카테고리: {memo['category']}"
    result += f"\n  📅 생성: {memo['created_at']}"

    if memo["created_at"] != memo["updated_at"]:
        result += f" (수정: {memo['updated_at']})"

    # 태그 조회
    conn = _get_db()
    tags = conn.execute("""
        SELECT t.name FROM tags t
        JOIN memo_tags mt ON t.id = mt.tag_id
        WHERE mt.memo_id = ?
    """, (memo["id"],)).fetchall()
    conn.close()

    if tags:
        tag_names = ", ".join(f"#{t['name']}" for t in tags)
        result += f"\n  🏷️ 태그: {tag_names}"

    if include_content:
        result += f"\n  📝 내용:\n    {memo['content']}"

    return result


# ============================================
# Tool: 메모 생성 (Create)
# ============================================
@mcp.tool
def create_memo(
    title: str,
    content: str,
    category: str = "일반",
    tags: str = "",
    pinned: bool = False,
) -> str:
    """새 메모를 생성합니다.

    Args:
        title: 메모 제목
        content: 메모 내용
        category: 카테고리 (기본: "일반")
        tags: 쉼표로 구분된 태그 (예: "업무,중요,TODO")
        pinned: 상단 고정 여부
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO memos (title, content, category, is_pinned, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, category, int(pinned), now, now),
        )
        memo_id = cursor.lastrowid

        # 태그 처리
        if tags:
            for tag_name in tags.split(","):
                tag_name = tag_name.strip()
                if not tag_name:
                    continue
                # 태그 생성 (이미 있으면 무시)
                conn.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,)
                )
                tag = conn.execute(
                    "SELECT id FROM tags WHERE name = ?", (tag_name,)
                ).fetchone()
                conn.execute(
                    "INSERT OR IGNORE INTO memo_tags (memo_id, tag_id) VALUES (?, ?)",
                    (memo_id, tag["id"]),
                )

        conn.commit()
        return f"✅ 메모가 생성되었습니다! (ID: #{memo_id})\n  제목: {title}\n  카테고리: {category}"
    finally:
        conn.close()


# ============================================
# Tool: 메모 목록 조회 (Read - List)
# ============================================
@mcp.tool
def list_memos(
    category: str = "",
    tag: str = "",
    pinned_only: bool = False,
    limit: int = 20,
) -> str:
    """메모 목록을 조회합니다.

    Args:
        category: 카테고리 필터
        tag: 태그 필터
        pinned_only: 고정된 메모만 표시
        limit: 최대 표시 개수
    """
    conn = _get_db()

    query = "SELECT DISTINCT m.* FROM memos m"
    params = []
    conditions = []

    if tag:
        query += " JOIN memo_tags mt ON m.id = mt.memo_id JOIN tags t ON mt.tag_id = t.id"
        conditions.append("t.name = ?")
        params.append(tag)

    if category:
        conditions.append("m.category = ?")
        params.append(category)

    if pinned_only:
        conditions.append("m.is_pinned = 1")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY m.is_pinned DESC, m.updated_at DESC LIMIT ?"
    params.append(limit)

    memos = conn.execute(query, params).fetchall()
    conn.close()

    if not memos:
        filters = []
        if category:
            filters.append(f"카테고리: {category}")
        if tag:
            filters.append(f"태그: {tag}")
        if pinned_only:
            filters.append("고정 메모만")
        return "메모가 없습니다." + (f" (필터: {', '.join(filters)})" if filters else "")

    result = ["📋 메모 목록", ""]
    for memo in memos:
        result.append(_format_memo(memo, include_content=False))
        result.append("")

    result.append(f"총 {len(memos)}개 메모")
    return "\n".join(result)


# ============================================
# Tool: 메모 상세 조회 (Read - Detail)
# ============================================
@mcp.tool
def get_memo(memo_id: int) -> str:
    """메모의 상세 내용을 조회합니다.

    Args:
        memo_id: 메모 ID
    """
    conn = _get_db()
    memo = conn.execute("SELECT * FROM memos WHERE id = ?", (memo_id,)).fetchone()
    conn.close()

    if not memo:
        return f"❌ 메모 #{memo_id}를 찾을 수 없습니다."

    return f"📝 메모 상세\n{'=' * 40}\n{_format_memo(memo)}"


# ============================================
# Tool: 메모 수정 (Update)
# ============================================
@mcp.tool
def update_memo(
    memo_id: int,
    title: str = "",
    content: str = "",
    category: str = "",
    tags: str = "",
    pinned: bool | None = None,
) -> str:
    """기존 메모를 수정합니다. 변경할 필드만 전달하세요.

    Args:
        memo_id: 수정할 메모 ID
        title: 새 제목 (빈 문자열이면 변경 안 함)
        content: 새 내용 (빈 문자열이면 변경 안 함)
        category: 새 카테고리 (빈 문자열이면 변경 안 함)
        tags: 새 태그 (쉼표 구분, 빈 문자열이면 변경 안 함)
        pinned: 고정 여부 (None이면 변경 안 함)
    """
    conn = _get_db()

    memo = conn.execute("SELECT * FROM memos WHERE id = ?", (memo_id,)).fetchone()
    if not memo:
        conn.close()
        return f"❌ 메모 #{memo_id}를 찾을 수 없습니다."

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = []
    params = []

    if title:
        updates.append("title = ?")
        params.append(title)
    if content:
        updates.append("content = ?")
        params.append(content)
    if category:
        updates.append("category = ?")
        params.append(category)
    if pinned is not None:
        updates.append("is_pinned = ?")
        params.append(int(pinned))

    if updates:
        updates.append("updated_at = ?")
        params.append(now)
        params.append(memo_id)
        conn.execute(
            f"UPDATE memos SET {', '.join(updates)} WHERE id = ?", params
        )

    # 태그 업데이트
    if tags:
        conn.execute("DELETE FROM memo_tags WHERE memo_id = ?", (memo_id,))
        for tag_name in tags.split(","):
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tag = conn.execute(
                "SELECT id FROM tags WHERE name = ?", (tag_name,)
            ).fetchone()
            conn.execute(
                "INSERT OR IGNORE INTO memo_tags (memo_id, tag_id) VALUES (?, ?)",
                (memo_id, tag["id"]),
            )

    conn.commit()
    conn.close()

    changes = []
    if title:
        changes.append(f"제목 → {title}")
    if content:
        changes.append("내용 수정")
    if category:
        changes.append(f"카테고리 → {category}")
    if tags:
        changes.append(f"태그 → {tags}")
    if pinned is not None:
        changes.append(f"고정 → {'예' if pinned else '아니오'}")

    return f"✅ 메모 #{memo_id} 수정 완료\n  변경 사항: {', '.join(changes)}"


# ============================================
# Tool: 메모 삭제 (Delete)
# ============================================
@mcp.tool
def delete_memo(memo_id: int) -> str:
    """메모를 삭제합니다.

    Args:
        memo_id: 삭제할 메모 ID
    """
    conn = _get_db()

    memo = conn.execute("SELECT title FROM memos WHERE id = ?", (memo_id,)).fetchone()
    if not memo:
        conn.close()
        return f"❌ 메모 #{memo_id}를 찾을 수 없습니다."

    title = memo["title"]
    conn.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
    conn.commit()
    conn.close()

    return f"🗑️ 메모 #{memo_id} '{title}'이(가) 삭제되었습니다."


# ============================================
# Tool: 메모 검색
# ============================================
@mcp.tool
def search_memos(keyword: str) -> str:
    """메모 제목과 내용에서 키워드를 검색합니다.

    Args:
        keyword: 검색 키워드
    """
    conn = _get_db()
    memos = conn.execute(
        "SELECT * FROM memos WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
        (f"%{keyword}%", f"%{keyword}%"),
    ).fetchall()
    conn.close()

    if not memos:
        return f"🔍 '{keyword}'에 대한 검색 결과가 없습니다."

    result = [f"🔍 '{keyword}' 검색 결과 ({len(memos)}건)", ""]
    for memo in memos:
        result.append(_format_memo(memo, include_content=False))
        result.append("")

    return "\n".join(result)


# ============================================
# Tool: 카테고리 목록
# ============================================
@mcp.tool
def list_categories() -> str:
    """사용 중인 모든 카테고리와 메모 수를 보여줍니다."""
    conn = _get_db()
    categories = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM memos
        GROUP BY category
        ORDER BY count DESC
    """).fetchall()
    conn.close()

    if not categories:
        return "카테고리가 없습니다. 메모를 먼저 생성하세요."

    result = ["📂 카테고리 목록", ""]
    for cat in categories:
        result.append(f"  {cat['category']}: {cat['count']}개")

    return "\n".join(result)


# ============================================
# Tool: 태그 목록
# ============================================
@mcp.tool
def list_tags() -> str:
    """사용 중인 모든 태그를 보여줍니다."""
    conn = _get_db()
    tags = conn.execute("""
        SELECT t.name, COUNT(mt.memo_id) as count
        FROM tags t
        LEFT JOIN memo_tags mt ON t.id = mt.tag_id
        GROUP BY t.name
        ORDER BY count DESC
    """).fetchall()
    conn.close()

    if not tags:
        return "태그가 없습니다. 메모 생성 시 태그를 추가해보세요."

    result = ["🏷️ 태그 목록", ""]
    for tag in tags:
        result.append(f"  #{tag['name']}: {tag['count']}개 메모")

    return "\n".join(result)


# ============================================
# Tool: 통계
# ============================================
@mcp.tool
def memo_stats() -> str:
    """메모 통계를 보여줍니다."""
    conn = _get_db()

    total = conn.execute("SELECT COUNT(*) as c FROM memos").fetchone()["c"]
    pinned = conn.execute("SELECT COUNT(*) as c FROM memos WHERE is_pinned = 1").fetchone()["c"]
    categories = conn.execute("SELECT COUNT(DISTINCT category) as c FROM memos").fetchone()["c"]
    tags = conn.execute("SELECT COUNT(*) as c FROM tags").fetchone()["c"]
    latest = conn.execute("SELECT updated_at FROM memos ORDER BY updated_at DESC LIMIT 1").fetchone()

    conn.close()

    result = [
        "📊 메모 통계",
        f"  총 메모 수: {total}개",
        f"  고정 메모: {pinned}개",
        f"  카테고리 수: {categories}개",
        f"  태그 수: {tags}개",
    ]
    if latest:
        result.append(f"  마지막 수정: {latest['updated_at']}")

    return "\n".join(result)


# ============================================
# Resource: 최근 메모
# ============================================
@mcp.resource("memo://recent")
def recent_memos() -> str:
    """최근 5개 메모를 반환합니다."""
    conn = _get_db()
    memos = conn.execute(
        "SELECT * FROM memos ORDER BY updated_at DESC LIMIT 5"
    ).fetchall()
    conn.close()

    if not memos:
        return "메모가 없습니다."

    result = ["최근 메모 (최대 5개)", ""]
    for memo in memos:
        result.append(_format_memo(memo, include_content=False))
        result.append("")
    return "\n".join(result)


# ============================================
# Prompt: 주간 정리 프롬프트
# ============================================
@mcp.prompt
def weekly_review() -> str:
    """이번 주 메모를 정리하는 프롬프트입니다."""
    return (
        "이번 주 작성한 메모를 정리해주세요.\n\n"
        "1. list_memos로 전체 목록을 확인\n"
        "2. 카테고리별로 분류하여 요약\n"
        "3. 미완료 TODO가 있다면 정리\n"
        "4. 중요도에 따라 다음 주 액션 아이템 제안"
    )


# ============================================
# 서버 실행
# ============================================
if __name__ == "__main__":
    mcp.run()
