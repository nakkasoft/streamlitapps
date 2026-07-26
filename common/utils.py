"""
공통 유틸리티 모듈
크롤링, API 호출 등 공통 기능을 정의합니다.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional


def fetch_html(url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
    """URL에서 HTML을 가져와 BeautifulSoup 객체로 반환합니다.

    Args:
        url: 요청할 URL
        timeout: 요청 타임아웃 (초)

    Returns:
        BeautifulSoup 객체 또는 실패 시 None
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"[ERROR] HTML 가져오기 실패: {url} - {e}")
        return None


def fetch_json(url: str, timeout: int = 10) -> Optional[dict]:
    """URL에서 JSON 데이터를 가져옵니다.

    Args:
        url: 요청할 URL
        timeout: 요청 타임아웃 (초)

    Returns:
        JSON 딕셔너리 또는 실패 시 None
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] JSON 가져오기 실패: {url} - {e}")
        return None
