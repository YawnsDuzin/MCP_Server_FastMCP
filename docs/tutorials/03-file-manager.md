# Tutorial 03: 파일 관리 MCP 서버

> **난이도**: ★★★☆☆ (중급)
> **사전 지식**: Tutorial 01~02 완료
> **결과물**: 안전한 파일 읽기/쓰기/검색이 가능한 MCP 서버

## 이 튜토리얼에서 배우는 것

- `pathlib`으로 파일 시스템 작업하기
- **경로 탐색(Path Traversal) 공격** 방지
- 작업 디렉토리 제한 (샌드박스)
- 파일 CRUD 및 검색 기능 구현
- 환경변수로 작업 경로 설정

## 보안 경고

파일 시스템을 다루는 MCP 서버는 **보안이 매우 중요**합니다.

```
❌ 위험한 예:
   사용자: "../../../../etc/passwd 파일 읽어줘"
   → 시스템 파일에 접근하면 안 됩니다!

✅ 안전한 예:
   사용자: "notes/todo.txt 파일 읽어줘"
   → 지정된 작업 디렉토리 안에서만 동작
```

---

## Step 1: 작업 디렉토리 설정

```python
import os
from pathlib import Path
from fastmcp import FastMCP

# 작업 디렉토리: 이 디렉토리 안에서만 파일 작업 허용
WORKSPACE = Path(os.getenv("FILE_WORKSPACE", Path.home() / "mcp_workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("File Manager Server")
```

### `pathlib.Path`를 쓰는 이유

```python
# os.path (구식)
path = os.path.join("home", "user", "workspace")
exists = os.path.exists(path)

# pathlib (현대적) - 더 직관적!
path = Path("home") / "user" / "workspace"
exists = path.exists()
```

`pathlib`은 `/` 연산자로 경로를 조합할 수 있어 가독성이 좋습니다.

---

## Step 2: 경로 보안 함수

**가장 중요한 함수**입니다. 모든 파일 작업 전에 이 함수로 경로를 검증합니다:

```python
def _safe_path(relative_path: str) -> Path:
    """작업 디렉토리 내의 안전한 경로를 반환합니다."""
    # 1. 절대 경로로 변환 (심볼릭 링크도 해석)
    full_path = (WORKSPACE / relative_path).resolve()

    # 2. 작업 디렉토리 안에 있는지 확인
    if not str(full_path).startswith(str(WORKSPACE.resolve())):
        raise ValueError(f"접근 거부: 작업 디렉토리 밖입니다.")

    return full_path
```

### 왜 이것이 필요한가?

```python
# 공격 시도 예시
_safe_path("../../etc/passwd")

# 내부 동작:
# 1. WORKSPACE / "../../etc/passwd"
#    → /home/user/mcp_workspace/../../etc/passwd
# 2. .resolve()
#    → /etc/passwd
# 3. startswith 검사
#    → /etc/passwd는 /home/user/mcp_workspace로 시작하지 않음
#    → ValueError 발생!
```

---

## Step 3: 파일 목록 도구

```python
@mcp.tool
def list_files(directory: str = "", pattern: str = "*") -> str:
    """작업 디렉토리의 파일과 폴더를 나열합니다.

    Args:
        directory: 탐색할 하위 디렉토리
        pattern: 파일 필터 패턴 (예: "*.txt", "*.py")
    """
    try:
        target = _safe_path(directory)
    except ValueError as e:
        return str(e)

    if not target.is_dir():
        return f"디렉토리가 아닙니다: {directory}"

    items = sorted(target.glob(pattern))

    result = []
    for item in items:
        relative = item.relative_to(WORKSPACE)
        if item.is_dir():
            result.append(f"📂 {relative}/")
        else:
            size = item.stat().st_size
            result.append(f"📄 {relative} ({size} bytes)")

    return "\n".join(result) if result else "항목이 없습니다."
```

### glob 패턴 설명

| 패턴 | 의미 | 예시 매치 |
|------|------|----------|
| `*` | 모든 파일 | `a.txt`, `b.py` |
| `*.txt` | .txt 파일만 | `note.txt`, `todo.txt` |
| `*.py` | .py 파일만 | `server.py`, `app.py` |
| `**/*.py` | 하위 디렉토리 포함 | `src/app.py` |

---

## Step 4: 파일 읽기 도구

```python
@mcp.tool
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """파일의 내용을 읽습니다."""
    try:
        path = _safe_path(file_path)
    except ValueError as e:
        return str(e)

    if not path.exists():
        return f"파일이 없습니다: {file_path}"

    # 바이너리 파일 체크
    binary_extensions = {".png", ".jpg", ".pdf", ".zip", ".exe"}
    if path.suffix.lower() in binary_extensions:
        return "바이너리 파일은 읽을 수 없습니다."

    try:
        content = path.read_text(encoding=encoding)
        lines = content.count("\n") + 1
        return f"📄 {file_path} ({lines}줄)\n{'=' * 40}\n{content}"
    except UnicodeDecodeError:
        return "인코딩 오류: 다른 인코딩을 시도해보세요."
```

---

## Step 5: 파일 쓰기 도구

```python
@mcp.tool
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """파일에 내용을 씁니다."""
    try:
        path = _safe_path(file_path)
    except ValueError as e:
        return str(e)

    if path.exists() and not overwrite:
        return "파일이 이미 존재합니다. overwrite=True로 덮어쓰세요."

    path.parent.mkdir(parents=True, exist_ok=True)  # 상위 폴더 자동 생성
    path.write_text(content, encoding="utf-8")

    return f"✅ 저장 완료: {file_path}"
```

### `overwrite` 파라미터의 중요성

기본값이 `False`이므로, Claude가 실수로 기존 파일을 덮어쓰는 것을 방지합니다.

---

## Step 6: 파일 검색 도구

```python
@mcp.tool
def search_files(keyword: str, file_pattern: str = "*.txt") -> str:
    """파일 내용에서 키워드를 검색합니다."""
    results = []

    for file_path in WORKSPACE.rglob(file_pattern):
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                if keyword.lower() in line.lower():
                    relative = file_path.relative_to(WORKSPACE)
                    results.append(f"📄 {relative}:{i}: {line.strip()}")
        except (UnicodeDecodeError, PermissionError):
            continue

    if not results:
        return f"'{keyword}'를 포함하는 파일을 찾지 못했습니다."

    return f"🔍 '{keyword}' 검색 결과 ({len(results)}건)\n" + "\n".join(results)
```

### `rglob` vs `glob`

```python
# glob: 현재 디렉토리만
target.glob("*.txt")      # notes.txt (하위 폴더 제외)

# rglob: 하위 디렉토리 포함 (recursive)
target.rglob("*.txt")     # notes.txt, sub/todo.txt, sub/deep/memo.txt
```

---

## Step 7: 실행 및 테스트

### 서버 실행

```bash
fastmcp run tutorials/03_file_manager/server.py
```

### Claude Code에 등록

```bash
claude mcp add file-manager -- fastmcp run /절대경로/tutorials/03_file_manager/server.py
```

### 테스트 대화 예시

```
"작업 디렉토리에 뭐가 있어?"
→ list_files() 호출

"meeting_notes.txt 파일 만들어줘. 내용은 오늘 회의 내용 정리."
→ write_file("meeting_notes.txt", "오늘 회의 내용 정리.") 호출

"meeting 키워드로 파일 검색해줘"
→ search_files("meeting") 호출

"notes라는 폴더 만들어줘"
→ create_directory("notes") 호출
```

---

## 보안 체크리스트

이 서버에 적용된 보안 조치:

- [x] 경로 탐색(Path Traversal) 방지: `_safe_path()` 함수
- [x] 작업 디렉토리 제한: `WORKSPACE` 외부 접근 차단
- [x] 덮어쓰기 방지: `overwrite=False` 기본값
- [x] 바이너리 파일 읽기 차단
- [x] 인코딩 에러 처리

## 핵심 정리

| 개념 | 코드 | 설명 |
|------|------|------|
| 경로 조합 | `Path("a") / "b"` | 안전한 경로 생성 |
| 경로 해석 | `.resolve()` | 심볼릭 링크/상대경로 해석 |
| 재귀 검색 | `.rglob("*.txt")` | 하위 폴더 포함 검색 |
| 파일 읽기 | `.read_text()` | 텍스트 파일 읽기 |
| 파일 쓰기 | `.write_text()` | 텍스트 파일 쓰기 |
| 폴더 생성 | `.mkdir(parents=True)` | 중간 경로도 자동 생성 |

## 도전 과제

1. 파일 복사/이동 도구를 추가해보세요
2. 파일 크기 제한 (예: 10MB 이상 읽기 제한) 기능을 추가해보세요
3. 최근 수정된 파일 Top 10을 보여주는 도구를 만들어보세요

## 다음 단계

➡️ [Tutorial 04: MSSQL 데이터베이스 서버](./04-database-server.md)
