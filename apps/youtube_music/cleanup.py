"""
오래된 다운로드 파일 자동 삭제 스크립트
FILE_RETENTION_DAYS일이 지난 MP3 파일을 삭제합니다.

사용법:
    python -m apps.youtube_music.cleanup

crontab에 등록하여 매일 자동 실행:
    0 3 * * * cd /home/ubuntu/streamlitapp && venv/bin/python -m apps.youtube_music.cleanup
"""

import os
import time
from datetime import datetime

# 직접 실행 시 상위 경로 문제 해결
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.youtube_music.config import DOWNLOAD_DIR, FILE_RETENTION_DAYS


def cleanup_old_files():
    """보관 기간이 지난 파일을 삭제합니다."""
    if not os.path.exists(DOWNLOAD_DIR):
        print(f"[INFO] 다운로드 디렉토리 없음: {DOWNLOAD_DIR}")
        return

    now = time.time()
    retention_seconds = FILE_RETENTION_DAYS * 24 * 60 * 60
    deleted = []
    kept = []

    for filename in os.listdir(DOWNLOAD_DIR):
        if not filename.endswith(".mp3"):
            continue

        filepath = os.path.join(DOWNLOAD_DIR, filename)
        file_mtime = os.path.getmtime(filepath)
        age_seconds = now - file_mtime

        if age_seconds > retention_seconds:
            try:
                os.remove(filepath)
                deleted.append(filename)
            except OSError as e:
                print(f"[ERROR] 삭제 실패: {filename} - {e}")
        else:
            kept.append(filename)

    # 결과 출력
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 파일 정리 완료")
    print(f"  삭제: {len(deleted)}개")
    print(f"  유지: {len(kept)}개")

    if deleted:
        for f in deleted:
            print(f"    - 삭제됨: {f}")


if __name__ == "__main__":
    cleanup_old_files()
