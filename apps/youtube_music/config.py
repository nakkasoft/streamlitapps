"""
유튜브 음악 다운로드 앱 설정
"""

# 서비스 포트
PORT = 8503

# 다운로드 경로 (서버 내 저장 위치)
DOWNLOAD_DIR = "/home/ubuntu/streamlitapp/downloads/music"

# 오디오 포맷 설정
AUDIO_FORMAT = "mp3"
AUDIO_QUALITY = "192"  # kbps

# 파일 자동 삭제 (일 단위)
FILE_RETENTION_DAYS = 3

# yt-dlp 옵션
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": AUDIO_FORMAT,
        "preferredquality": AUDIO_QUALITY,
    }],
    "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
}
