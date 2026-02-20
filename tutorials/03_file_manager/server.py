"""
Tutorial 03: 파일 관리 MCP 서버
================================

로컬 파일 시스템을 안전하게 관리하는 MCP 서버를 만듭니다.
지정된 작업 디렉토리 안에서만 파일 읽기/쓰기/검색이 가능합니다.

학습 포인트:
- 파일 시스템 작업 (pathlib 활용)
- 보안: 경로 탐색(Path Traversal) 방지
- Context를 활용한 로깅
- 다양한 반환 타입 (문자열, 딕셔너리)

실행 방법:
    fastmcp run server.py

환경변수:
    FILE_WORKSPACE: 작업 디렉토리 경로 (기본: ~/mcp_workspace)
"""

import os
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

# ============================================
# 설정
# ============================================
# 작업 디렉토리 설정 - 이 디렉토리 안에서만 파일 작업 허용
WORKSPACE = Path(os.getenv("FILE_WORKSPACE", Path.home() / "mcp_workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("File Manager Server")


# ============================================
# 보안: 경로 검증 헬퍼 함수
# ============================================
def _safe_path(relative_path: str) -> Path:
    """작업 디렉토리 내의 안전한 경로를 반환합니다.

    경로 탐색(Path Traversal) 공격을 방지하기 위해
    resolve() 후 작업 디렉토리 안에 있는지 확인합니다.
    """
    # 절대 경로로 변환
    full_path = (WORKSPACE / relative_path).resolve()

    # 작업 디렉토리 안에 있는지 확인
    if not str(full_path).startswith(str(WORKSPACE.resolve())):
        raise ValueError(
            f"접근 거부: '{relative_path}'는 작업 디렉토리 밖에 있습니다.\n"
            f"작업 디렉토리: {WORKSPACE}"
        )

    return full_path


# ============================================
# Tool: 파일 목록 보기
# ============================================
@mcp.tool
def list_files(directory: str = "", pattern: str = "*") -> str:
    """작업 디렉토리의 파일과 폴더를 나열합니다.

    Args:
        directory: 탐색할 하위 디렉토리 (기본: 작업 디렉토리 루트)
        pattern: 파일 필터 패턴 (예: "*.txt", "*.py")
    """
    try:
        target = _safe_path(directory)
    except ValueError as e:
        return str(e)

    if not target.exists():
        return f"디렉토리가 존재하지 않습니다: {directory or '(루트)'}"

    if not target.is_dir():
        return f"'{directory}'는 디렉토리가 아닙니다."

    items = sorted(target.glob(pattern))
    if not items:
        return f"'{directory or '(루트)'}' 디렉토리에 '{pattern}' 패턴과 일치하는 항목이 없습니다."

    result = [f"📁 {directory or '작업 디렉토리'} 내용 (패턴: {pattern}):", ""]

    for item in items:
        relative = item.relative_to(WORKSPACE)
        if item.is_dir():
            result.append(f"  📂 {relative}/")
        else:
            size = item.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            result.append(f"  📄 {relative} ({size_str})")

    result.append(f"\n총 {len(items)}개 항목")
    return "\n".join(result)


# ============================================
# Tool: 파일 읽기
# ============================================
@mcp.tool
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """파일의 내용을 읽습니다.

    Args:
        file_path: 읽을 파일 경로 (작업 디렉토리 기준 상대 경로)
        encoding: 파일 인코딩 (기본: utf-8)
    """
    try:
        path = _safe_path(file_path)
    except ValueError as e:
        return str(e)

    if not path.exists():
        return f"파일이 존재하지 않습니다: {file_path}"

    if not path.is_file():
        return f"'{file_path}'는 파일이 아닙니다."

    # 바이너리 파일 체크
    binary_extensions = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe"}
    if path.suffix.lower() in binary_extensions:
        return f"'{file_path}'는 바이너리 파일이므로 텍스트로 읽을 수 없습니다."

    try:
        content = path.read_text(encoding=encoding)
        lines = content.count("\n") + 1
        return (
            f"📄 {file_path} ({lines}줄)\n"
            f"{'=' * 40}\n"
            f"{content}"
        )
    except UnicodeDecodeError:
        return f"인코딩 오류: '{encoding}'으로 읽을 수 없습니다. 다른 인코딩을 시도해보세요."


# ============================================
# Tool: 파일 쓰기
# ============================================
@mcp.tool
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """파일에 내용을 씁니다.

    Args:
        file_path: 저장할 파일 경로 (작업 디렉토리 기준 상대 경로)
        content: 파일에 쓸 내용
        overwrite: 기존 파일 덮어쓰기 여부 (기본: False)
    """
    try:
        path = _safe_path(file_path)
    except ValueError as e:
        return str(e)

    if path.exists() and not overwrite:
        return (
            f"파일이 이미 존재합니다: {file_path}\n"
            f"덮어쓰려면 overwrite=True를 설정하세요."
        )

    # 상위 디렉토리 자동 생성
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content, encoding="utf-8")

    return (
        f"✅ 파일이 저장되었습니다: {file_path}\n"
        f"📊 크기: {len(content)} bytes, {content.count(chr(10)) + 1}줄"
    )


# ============================================
# Tool: 파일 검색
# ============================================
@mcp.tool
def search_files(keyword: str, file_pattern: str = "*.txt", directory: str = "") -> str:
    """파일 내용에서 키워드를 검색합니다.

    Args:
        keyword: 검색할 키워드
        file_pattern: 검색할 파일 패턴 (기본: "*.txt")
        directory: 검색할 디렉토리 (기본: 전체 작업 디렉토리)
    """
    try:
        search_dir = _safe_path(directory)
    except ValueError as e:
        return str(e)

    if not search_dir.exists():
        return f"디렉토리가 존재하지 않습니다: {directory or '(루트)'}"

    results = []
    files_searched = 0

    for file_path in search_dir.rglob(file_pattern):
        if not file_path.is_file():
            continue

        files_searched += 1
        try:
            content = file_path.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                if keyword.lower() in line.lower():
                    relative = file_path.relative_to(WORKSPACE)
                    results.append(f"  📄 {relative}:{i}: {line.strip()}")
        except (UnicodeDecodeError, PermissionError):
            continue

    if not results:
        return (
            f"'{keyword}'를 포함하는 파일을 찾지 못했습니다.\n"
            f"검색 범위: {directory or '전체'}, 패턴: {file_pattern}\n"
            f"검색한 파일 수: {files_searched}"
        )

    header = (
        f"🔍 '{keyword}' 검색 결과 ({len(results)}건)\n"
        f"검색 범위: {directory or '전체'}, 패턴: {file_pattern}\n"
        f"{'=' * 40}"
    )
    return header + "\n" + "\n".join(results)


# ============================================
# Tool: 파일/폴더 정보
# ============================================
@mcp.tool
def get_file_info(file_path: str) -> str:
    """파일 또는 폴더의 상세 정보를 반환합니다.

    Args:
        file_path: 정보를 확인할 파일/폴더 경로
    """
    try:
        path = _safe_path(file_path)
    except ValueError as e:
        return str(e)

    if not path.exists():
        return f"경로가 존재하지 않습니다: {file_path}"

    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")

    if path.is_file():
        size = stat.st_size
        return (
            f"📄 파일 정보: {file_path}\n"
            f"  유형: 파일\n"
            f"  확장자: {path.suffix or '없음'}\n"
            f"  크기: {size:,} bytes\n"
            f"  수정일: {modified}\n"
            f"  생성일: {created}"
        )
    else:
        items = list(path.iterdir())
        dirs = sum(1 for i in items if i.is_dir())
        files = sum(1 for i in items if i.is_file())
        return (
            f"📂 폴더 정보: {file_path}\n"
            f"  유형: 디렉토리\n"
            f"  하위 폴더: {dirs}개\n"
            f"  파일: {files}개\n"
            f"  수정일: {modified}\n"
            f"  생성일: {created}"
        )


# ============================================
# Tool: 디렉토리 생성
# ============================================
@mcp.tool
def create_directory(dir_path: str) -> str:
    """새 디렉토리를 생성합니다.

    Args:
        dir_path: 생성할 디렉토리 경로 (작업 디렉토리 기준 상대 경로)
    """
    try:
        path = _safe_path(dir_path)
    except ValueError as e:
        return str(e)

    if path.exists():
        return f"이미 존재합니다: {dir_path}"

    path.mkdir(parents=True, exist_ok=True)
    return f"✅ 디렉토리가 생성되었습니다: {dir_path}"


# ============================================
# Resource: 작업 디렉토리 정보
# ============================================
@mcp.resource("files://workspace")
def workspace_info() -> str:
    """현재 작업 디렉토리의 정보를 반환합니다."""
    items = list(WORKSPACE.iterdir())
    dirs = sum(1 for i in items if i.is_dir())
    files = sum(1 for i in items if i.is_file())

    return (
        f"작업 디렉토리: {WORKSPACE}\n"
        f"하위 폴더: {dirs}개\n"
        f"파일: {files}개\n"
        f"총 항목: {len(items)}개"
    )


# ============================================
# Prompt: 프로젝트 구조 분석
# ============================================
@mcp.prompt
def analyze_project(project_name: str) -> str:
    """프로젝트 구조 분석을 요청하는 프롬프트입니다."""
    return (
        f"'{project_name}' 프로젝트의 파일 구조를 분석해주세요.\n\n"
        f"다음 순서로 진행해주세요:\n"
        f"1. list_files로 전체 파일 목록 확인\n"
        f"2. 주요 파일의 내용을 read_file로 읽기\n"
        f"3. 프로젝트 구조와 목적을 설명\n"
        f"4. 개선 제안"
    )


# ============================================
# 서버 실행
# ============================================
if __name__ == "__main__":
    mcp.run()
