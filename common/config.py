"""
공통 서버 설정
서버 호스트/IP를 한 곳에서 관리합니다.
서버를 옮기거나 도메인을 연결하면 이 값만 바꾸면 됩니다.
"""

# 대시보드가 실행되는 서버의 호스트 (IP 또는 도메인)
SERVER_HOST = "146.56.116.10"

# 허브(포털) 포트
HUB_PORT = 8500


def build_url(port: int) -> str:
    """SERVER_HOST 기준으로 특정 포트의 URL을 생성합니다."""
    return f"http://{SERVER_HOST}:{port}"


HUB_URL = build_url(HUB_PORT)
