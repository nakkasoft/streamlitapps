"""
유튜브 음악 다운로드 모듈
yt-dlp를 사용하여 유튜브 영상에서 오디오를 추출합니다.
다중 URL 및 진행률 콜백을 지원합니다.
"""

import os
import yt_dlp
from .config import DOWNLOAD_DIR, YDL_OPTIONS


def ensure_download_dir():
    """다운로드 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_video_info(url: str) -> dict | None:
    """다운로드 전에 영상 정보를 가져옵니다.

    Args:
        url: 유튜브 영상 URL

    Returns:
        영상 정보 딕셔너리 또는 None
    """
    try:
        opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
                "url": url,
            }
    except Exception as e:
        return {"title": f"[오류] {url}", "duration": 0, "thumbnail": None, "uploader": None, "url": url, "error": str(e)}


def download_single(url: str, progress_hook=None) -> dict:
    """단일 URL에서 오디오를 다운로드합니다.

    Args:
        url: 유튜브 영상 URL
        progress_hook: 진행률 콜백 함수 (yt-dlp progress_hooks 형식)

    Returns:
        결과 딕셔너리 {"success": bool, "title": str, "filename": str, "error": str}
    """
    ensure_download_dir()

    options = YDL_OPTIONS.copy()
    if progress_hook:
        options["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown")
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".mp3"

            return {
                "success": True,
                "title": title,
                "filename": filename,
                "error": None,
            }
    except Exception as e:
        return {
            "success": False,
            "title": None,
            "filename": None,
            "error": str(e),
        }


def download_multiple(urls: list[str], progress_callback=None) -> list[dict]:
    """여러 URL을 순차적으로 다운로드합니다.

    Args:
        urls: 유튜브 URL 리스트
        progress_callback: 전체 진행률 콜백 (current_index, total, current_result)

    Returns:
        각 URL의 다운로드 결과 리스트
    """
    results = []
    total = len(urls)

    for idx, url in enumerate(urls):
        url = url.strip()
        if not url:
            continue

        result = download_single(url)
        result["url"] = url
        result["index"] = idx + 1
        results.append(result)

        if progress_callback:
            progress_callback(idx + 1, total, result)

    return results


def list_downloaded_files() -> list[dict]:
    """다운로드된 파일 목록을 반환합니다."""
    ensure_download_dir()

    files = []
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".mp3"):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            stat = os.stat(filepath)
            size_mb = stat.st_size / (1024 * 1024)
            from datetime import datetime
            mtime = datetime.fromtimestamp(stat.st_mtime)
            files.append({
                "파일명": filename,
                "크기": f"{size_mb:.1f} MB",
                "다운로드일시": mtime.strftime("%Y-%m-%d %H:%M"),
                "경로": filepath,
            })

    return sorted(files, key=lambda x: x["다운로드일시"], reverse=True)
