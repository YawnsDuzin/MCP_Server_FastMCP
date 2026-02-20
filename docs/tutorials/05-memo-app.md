# Tutorial 05: 메모/노트 MCP 서버 (SQLite + CRUD)

> **난이도**: ★★★★☆ (중상급)
> **사전 지식**: Tutorial 01~04 완료
> **결과물**: SQLite 기반 완전한 CRUD 메모 앱 MCP 서버

## 이 튜토리얼에서 배우는 것

- SQLite 데이터베이스 설계 및 활용
- 완전한 CRUD (Create, Read, Update, Delete)
- 태그 시스템 (다대다 관계)
- 검색 기능 구현
- 통계 및 카테고리 관리

## 왜 SQLite인가?

| 특징 | MSSQL (Tutorial 04) | SQLite (이 튜토리얼) |
|------|---------------------|---------------------|
| 설치 | ODBC 드라이버 필요 | 없음 (Python 내장) |
| 서버 | 별도 DB 서버 필요 | 파일 하나로 동작 |
| 용도 | 대규모 운영 환경 | 개인/소규모 앱 |
| 학습 | 환경 설정이 복잡 | 즉시 시작 가능 |

SQLite는 Python에 내장되어 있어 **추가 설치 없이** 바로 사용할 수 있습니다.

---

## Step 1: 데이터베이스 설계

### 테이블 구조

```
[memos] ──── N:M ──── [tags]
  │                      │
  └──── [memo_tags] ─────┘
         (연결 테이블)

memos:                     tags:
├── id (PK)               ├── id (PK)
├── title                 └── name (UNIQUE)
├── content
├── category              memo_tags:
├── is_pinned             ├── memo_id (FK)
├── created_at            └── tag_id (FK)
└── updated_at
```

### 다대다 관계란?

- 하나의 메모에 여러 태그를 붙일 수 있음
- 하나의 태그가 여러 메모에 사용될 수 있음

```
메모 "회의록"  ←→  #업무, #중요
메모 "장보기"  ←→  #개인, #TODO
메모 "프로젝트" ←→  #업무, #TODO
                        ↑
                  두 메모에서 공유
```

---

## Step 2: 데이터베이스 초기화

```python
import sqlite3
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("Memo App Server")
DB_PATH = Path(__file__).parent / "memos.db"

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

    # 메모-태그 연결 테이블
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

# 서버 시작 시 자동 초기화
_init_db()
```

### `CREATE TABLE IF NOT EXISTS`

테이블이 없으면 생성하고, 있으면 건너뜁니다. 서버를 여러 번 재시작해도 안전합니다.

### `ON DELETE CASCADE`

메모를 삭제하면 연결된 `memo_tags` 레코드도 자동 삭제됩니다.

---

## Step 3: CRUD - Create (생성)

```python
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
            "INSERT INTO memos (title, content, category, is_pinned, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, category, int(pinned), now, now),
        )
        memo_id = cursor.lastrowid

        # 태그 처리
        if tags:
            for tag_name in tags.split(","):
                tag_name = tag_name.strip()
                if not tag_name:
                    continue
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                tag = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
                conn.execute("INSERT OR IGNORE INTO memo_tags (memo_id, tag_id) VALUES (?, ?)",
                           (memo_id, tag["id"]))

        conn.commit()
        return f"✅ 메모 생성 (ID: #{memo_id})"
    finally:
        conn.close()
```

### `INSERT OR IGNORE`

태그가 이미 존재하면 에러 대신 무시합니다:

```sql
INSERT OR IGNORE INTO tags (name) VALUES ('업무')
-- '업무' 태그가 이미 있으면 → 아무 일도 안 함
-- '업무' 태그가 없으면 → 새로 생성
```

---

## Step 4: CRUD - Read (조회)

### 목록 조회

```python
@mcp.tool
def list_memos(category: str = "", tag: str = "", pinned_only: bool = False) -> str:
    """메모 목록을 조회합니다."""
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

    query += " ORDER BY m.is_pinned DESC, m.updated_at DESC"
    ...
```

### 상세 조회

```python
@mcp.tool
def get_memo(memo_id: int) -> str:
    """메모의 상세 내용을 조회합니다."""
    conn = _get_db()
    memo = conn.execute("SELECT * FROM memos WHERE id = ?", (memo_id,)).fetchone()
    conn.close()

    if not memo:
        return f"❌ 메모 #{memo_id}를 찾을 수 없습니다."

    return _format_memo(memo)
```

---

## Step 5: CRUD - Update (수정)

```python
@mcp.tool
def update_memo(
    memo_id: int,
    title: str = "",
    content: str = "",
    category: str = "",
) -> str:
    """기존 메모를 수정합니다. 변경할 필드만 전달하세요."""
    # 변경할 필드만 UPDATE 쿼리에 포함
    updates = []
    params = []

    if title:
        updates.append("title = ?")
        params.append(title)
    if content:
        updates.append("content = ?")
        params.append(content)
    # ...

    if updates:
        updates.append("updated_at = ?")
        params.append(now)
        params.append(memo_id)
        conn.execute(f"UPDATE memos SET {', '.join(updates)} WHERE id = ?", params)
```

### 부분 업데이트 패턴

빈 문자열이면 변경하지 않으므로, 변경하고 싶은 필드만 전달하면 됩니다:

```
"메모 3번 제목을 '회의록 수정본'으로 바꿔줘"
→ update_memo(memo_id=3, title="회의록 수정본")
  (content, category 등은 변경되지 않음)
```

---

## Step 6: CRUD - Delete (삭제)

```python
@mcp.tool
def delete_memo(memo_id: int) -> str:
    """메모를 삭제합니다."""
    conn = _get_db()
    memo = conn.execute("SELECT title FROM memos WHERE id = ?", (memo_id,)).fetchone()

    if not memo:
        conn.close()
        return f"❌ 메모 #{memo_id}를 찾을 수 없습니다."

    conn.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
    conn.commit()
    conn.close()

    return f"🗑️ 메모 #{memo_id} '{memo['title']}' 삭제 완료"
```

---

## Step 7: 검색 및 통계

### 키워드 검색

```python
@mcp.tool
def search_memos(keyword: str) -> str:
    """메모 제목과 내용에서 키워드를 검색합니다."""
    conn = _get_db()
    memos = conn.execute(
        "SELECT * FROM memos WHERE title LIKE ? OR content LIKE ?",
        (f"%{keyword}%", f"%{keyword}%"),
    ).fetchall()
    ...
```

### 통계

```python
@mcp.tool
def memo_stats() -> str:
    """메모 통계를 보여줍니다."""
    # 총 메모 수, 고정 메모, 카테고리 수, 태그 수 등
    ...
```

---

## Step 8: 실행 및 테스트

### 서버 실행

```bash
fastmcp run tutorials/05_memo_app/server.py
```

### Claude Code에 등록

```bash
claude mcp add memo-app -- fastmcp run /절대경로/tutorials/05_memo_app/server.py
```

### 테스트 대화 시나리오

```
1. "오늘 회의 내용을 메모해줘. 제목은 '팀 회의', 태그는 업무,회의"
   → create_memo("팀 회의", "...", tags="업무,회의")

2. "메모 목록 보여줘"
   → list_memos()

3. "업무 카테고리 메모만 보여줘"
   → list_memos(category="업무")

4. "1번 메모 자세히 보여줘"
   → get_memo(1)

5. "1번 메모 제목을 '주간 팀 회의'로 바꿔줘"
   → update_memo(1, title="주간 팀 회의")

6. "'회의' 키워드로 검색해줘"
   → search_memos("회의")

7. "메모 통계 보여줘"
   → memo_stats()

8. "2번 메모 삭제해줘"
   → delete_memo(2)
```

---

## CRUD 요약

```
Create  →  create_memo()    →  INSERT INTO memos ...
Read    →  list_memos()     →  SELECT * FROM memos ...
         get_memo()         →  SELECT * FROM memos WHERE id = ?
Update  →  update_memo()    →  UPDATE memos SET ... WHERE id = ?
Delete  →  delete_memo()    →  DELETE FROM memos WHERE id = ?
```

## 핵심 정리

| 개념 | 코드 | 설명 |
|------|------|------|
| SQLite 연결 | `sqlite3.connect(path)` | 파일 기반 DB |
| Row Factory | `conn.row_factory = sqlite3.Row` | 딕셔너리처럼 접근 |
| 자동 증가 | `AUTOINCREMENT` | ID 자동 생성 |
| 다대다 관계 | `memo_tags` 테이블 | 연결 테이블 패턴 |
| 부분 업데이트 | 동적 UPDATE | 변경할 필드만 반영 |
| 검색 | `LIKE '%keyword%'` | 부분 일치 검색 |

## 도전 과제

1. 메모 내보내기 기능 (JSON, Markdown)을 추가해보세요
2. 메모 즐겨찾기/보관함 기능을 만들어보세요
3. 작성일 기준 달력 보기 도구를 만들어보세요
4. 여러 메모를 병합하는 도구를 만들어보세요

## 튜토리얼 완료!

5개의 튜토리얼을 모두 완료했습니다. 이제 당신은:

- MCP 서버의 기본 구조를 이해합니다
- Tool, Resource, Prompt를 자유롭게 정의할 수 있습니다
- 외부 API, 파일 시스템, 데이터베이스를 연동할 수 있습니다
- 보안 사항 (Path Traversal, SQL Injection)을 알고 있습니다
- 완전한 CRUD 서버를 만들 수 있습니다

➡️ [FastMCP API 레퍼런스](../reference/fastmcp-api.md)에서 더 많은 기능을 확인하세요.
➡️ [Claude 연동 가이드](../reference/claude-integration.md)에서 연동 방법을 자세히 알아보세요.
