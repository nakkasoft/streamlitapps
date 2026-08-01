"""
유튜브 음악 다운로드 앱 설정
"""

import os

# 서비스 포트
PORT = 8503

# 다운로드 경로 (서버 내 저장 위치)
DOWNLOAD_DIR = "/home/ubuntu/streamlitapp/downloads/music"

# 오디오 포맷 설정
AUDIO_FORMAT = "mp3"
AUDIO_QUALITY = "192"  # kbps

# 파일 자동 삭제 (일 단위)
FILE_RETENTION_DAYS = 3

# 유튜브 쿠키 파일 (Netscape 형식, cookies.txt)
# 서버(클라우드) IP에서 요청하면 유튜브가 "봇 확인" 페이지를 띄우며 차단하는
# 경우가 있습니다. 실제 로그인 브라우저의 쿠키를 넘겨주면 우회할 수 있습니다.
# - 이 파일은 계정 로그인 정보를 담고 있으므로 절대 git에 커밋하지 마세요.
# - 파일이 없으면 쿠키 없이 시도합니다(공개 영상은 대부분 문제없이 동작).
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")


def _base_options() -> dict:
    """쿠키 파일 유무에 따라 공통 yt-dlp 옵션을 구성합니다."""
    options = {
        "quiet": True,
        "no_warnings": True,
    }
    if os.path.exists(COOKIES_FILE):
        options["cookiefile"] = COOKIES_FILE
    return options


# yt-dlp 다운로드용 옵션
YDL_OPTIONS = {
    **_base_options(),
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": AUDIO_FORMAT,
        "preferredquality": AUDIO_QUALITY,
    }],
    "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
}

# yt-dlp 영상 정보 조회(다운로드 없이)용 옵션
YDL_INFO_OPTIONS = _base_options()
