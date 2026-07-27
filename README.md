# 내 정보 대시보드 (Streamlit Apps)

개인용 정보 수집 & 유틸리티 서비스를 모아둔 Streamlit 기반 대시보드입니다.
각 앱은 독립된 프로세스/포트로 실행되며, 허브 페이지에서 한눈에 모아볼 수 있습니다.

## 앱 구성

| 앱 | 포트 | 설명 | 상태 |
|---|---|---|---|
| 🏠 허브 (portal.py) | 8500 | 전체 앱 소개 및 바로가기 | 운영중 |
| 🏕️ 캠핑장 빈자리 찾기 | 8502 | 날짜별 캠핑장 예약 가능 현황 조회 (Playwright + xticket) | 운영중 |
| 🎵 유튜브 음악 다운로드 | 8503 | 유튜브 URL → MP3 변환/다운로드, 3일 후 자동 삭제 | 운영중 |
| 📚 도서관 책 찾기 | 8501 | 서울시립도서관 통합검색 무인예약 가능 도서관 확인 | 운영중 |

## 프로젝트 구조

```
.
├── portal.py                   # 허브 (앱 소개 + 바로가기)
├── apps/
│   ├── camping/                 # 캠핑장 빈자리 찾기
│   │   ├── app.py                # Streamlit 화면
│   │   ├── config.py             # 캠핑장 목록/설정 (여기에 캠핑장 추가)
│   │   ├── scraper.py            # Playwright 기반 세션/조회 로직
│   │   └── scraper_sample.py     # 콘솔 출력용 원본 스크립트 (동작 참고용)
│   ├── youtube_music/            # 유튜브 음악 다운로드
│   │   ├── app.py                # Streamlit 화면
│   │   ├── config.py             # 다운로드 경로/보관 기간 설정
│   │   ├── downloader.py         # yt-dlp 기반 다운로드 로직
│   │   └── cleanup.py            # 오래된 파일 자동 삭제 스크립트
│   └── library/                  # 도서관 책 찾기 (서울시립도서관 무인예약 확인)
│       ├── app.py                # Streamlit 화면 (도서 CRUD + 확인 작업 실행)
│       ├── config.py             # 도서 목록 파일 경로/속도제한/재시도 설정
│       ├── books.txt             # 관심 도서 목록 (CLI와 동일한 파일 형식)
│       └── lib/                  # 핵심 로직 (원본 sblib-search/src 포팅)
│           ├── errors.py, models.py, list_loader.py
│           ├── searcher.py, result_parser.py, status.py
│           ├── rate_limiter.py, retry_policy.py
│           ├── repository.py     # 도서 목록 CRUD + books.txt 동기화
│           └── check_runner.py   # 확인 작업 실행기 (진행 콜백 포함)
├── common/
│   ├── config.py                 # 서버 호스트 등 공통 설정
│   └── utils.py                  # 공통 유틸 (HTTP 요청 헬퍼)
├── requirements.txt
├── setup_linux.sh                # 최초 1회 환경설정 (venv, 패키지 설치)
├── start_all.sh                  # 전체 서비스 시작
└── stop_all.sh                   # 전체 서비스 종료
```

## 요구 사항

- Python 3.10 이상
- Linux 서버 (Ubuntu 기준으로 작성됨)
- FFmpeg (유튜브 음악 다운로드 앱에서 MP3 변환에 필요)
- Playwright + Chromium (캠핑장 앱에서 예약 사이트 세션을 만들기 위해 headless로 사용, 화면은 뜨지 않음)
- lxml (도서관 앱의 HTML 파싱에 사용, BeautifulSoup의 파서 백엔드)

## 설치 및 실행 (서버)

### 1. 최초 1회 환경설정

```bash
git clone https://github.com/nakkasoft/streamlitapps.git
cd streamlitapps

chmod +x setup_linux.sh
./setup_linux.sh
```

`setup_linux.sh`가 하는 일:
- Python 가상환경(`venv`) 생성
- `requirements.txt` 패키지 설치
- Playwright용 Chromium 및 시스템 의존성 설치 (`playwright install --with-deps chromium`)
- 실행에 필요한 `logs/`, `pids/` 디렉토리 생성
- 실행 스크립트에 실행 권한 부여

MP3 변환을 위해 FFmpeg도 설치해야 합니다.

```bash
sudo apt update
sudo apt install ffmpeg -y
```

> **참고 (저사양 서버):** Playwright의 Chromium 설치는 용량이 크고(약 150~300MB) 실행 시 메모리를 소비합니다.
> RAM이 1GB 내외인 서버에서는 `playwright install --with-deps chromium` 단계가 느리거나 실패할 수 있습니다.
> 이 경우 스왑 메모리를 늘리거나, 캠핑장 앱만 별도의 조금 더 넉넉한 서버/스케줄에서 운영하는 것을 고려하세요.
> 조회는 상시 구동이 아니라 "🔍 빈자리 조회" 버튼을 눌렀을 때만 브라우저를 잠깐 띄우고 끄는 방식이라, 상시 리소스 점유는 없습니다.

### 2. 서버 호스트 설정

`common/config.py`에서 서버의 IP 또는 도메인을 지정합니다. 허브의 "바로가기" 링크와 각 앱의 "허브로 돌아가기" 링크가 이 값을 기준으로 생성됩니다.

```python
# common/config.py
SERVER_HOST = "YOUR_SERVER_IP_OR_DOMAIN"
```

### 3. 서비스 시작 / 종료

```bash
./start_all.sh   # 전체 서비스 시작 (백그라운드, nohup)
./stop_all.sh    # 전체 서비스 종료
```

시작 후 접속 주소:

```
http://<서버 IP>:8500   # 허브
http://<서버 IP>:8501   # 도서관 책 찾기
http://<서버 IP>:8502   # 캠핑장 빈자리 찾기
http://<서버 IP>:8503   # 유튜브 음악 다운로드
```

방화벽(iptables/ufw) 및 클라우드 보안 그룹에서 8500~8503 포트를 열어야 외부에서 접속할 수 있습니다.

### 4. 로그 확인

```bash
tail -f logs/*.log
```

## 앱별 사용법

### 🏕️ 캠핑장 빈자리 찾기

1. 조회할 시작/종료 날짜를 선택합니다 (최대 31일).
2. 조회할 캠핑장을 선택합니다 (다중 선택 가능).
3. "🔍 빈자리 조회" 버튼을 누르면 headless Chromium이 각 캠핑장의 예약 페이지에 접속해 세션을 만들고, 상품군(야영데크/글램핑 등)별로 예약 가능 현황을 조회합니다.

camp.xticket.kr은 예약 조회 API를 호출하기 전에 반드시 실제 예약 페이지 접속을 통한 브라우저 세션이 필요해서, 단순 HTTP 요청만으로는 조회가 되지 않습니다. 이 때문에 Playwright로 페이지를 열어 세션을 만든 뒤, 그 세션 위에서 조회 API를 호출하는 방식을 사용합니다 (자세한 내용은 `apps/camping/scraper.py` 상단 주석 참고).

새 캠핑장을 추가하려면 `apps/camping/config.py`의 `CAMPSITES` 리스트에 이름과 `shop_encode`(예약 페이지 URL의 `shopEncode=` 뒤에 오는 값)를 추가하면 됩니다.

```python
CAMPSITES = [
    {"name": "캠핑장 이름", "shop_encode": "예약 페이지 URL의 shopEncode 값"},
    ...
]
```

### 🎵 유튜브 음악 다운로드

1. 유튜브 URL을 한 줄에 하나씩 입력합니다 (여러 개 가능).
2. "🎵 다운로드 시작"을 누르면 순차적으로 다운로드하며 진행률이 표시됩니다.
3. 다운로드된 파일은 서버에 저장되고, 목록에서 확인할 수 있습니다.
4. 다운로드된 파일은 **3일**이 지나면 자동으로 삭제 대상이 됩니다 (`apps/youtube_music/cleanup.py`).

파일 자동 삭제를 매일 실행하려면 crontab에 등록합니다.

```bash
crontab -e
```

```
0 3 * * * cd /path/to/streamlitapps && venv/bin/python -m apps.youtube_music.cleanup
```

보관 기간을 변경하려면 `apps/youtube_music/config.py`의 `FILE_RETENTION_DAYS` 값을 수정하세요.

### 📚 도서관 책 찾기

서울시립도서관 통합검색에서 관심 도서의 무인예약 가능 도서관을 확인합니다.
원본 CLI 프로젝트(`library-reservation-checker`)의 검색/파싱/재시도 로직을
그대로 포팅했고(`apps/library/lib/`), 도서 목록 관리와 결과 표시는 Streamlit
UI로 새로 구현했습니다.

1. **도서 목록 관리** — 화면에서 제목(필수)/저자(선택)를 입력해 도서를 추가/수정/삭제합니다.
   - 목록은 `apps/library/books.txt`에 자동 저장되며, 파일을 직접 편집해도 반영됩니다.
   - 형식: 한 줄에 한 권, `제목` 또는 `제목 | 저자`. `#`으로 시작하는 줄은 주석.
   - 도서는 1권 이상 50권 이하만 허용됩니다(마지막 1권은 삭제할 수 없습니다).
2. **확인 작업 실행** — "🚀 확인 작업 시작"을 누르면 등록된 도서를 순서대로 검색합니다.
   - 도서 1권당 최소 1초 간격으로 순차 조회합니다(대상 사이트 부하 방지).
   - 네트워크 오류는 최대 3회 재시도하며, 재시도가 소진되면 "요청 오류"로 표시합니다.
   - 진행 중 프로그레스 바로 현재 처리 중인 도서를 확인할 수 있습니다.
3. **결과 확인** — 도서별로 다음 5가지 상태 중 하나로 표시됩니다.
   - `무인예약 가능` (가능한 도서관 목록 함께 표시)
   - `무인예약 불가` (소장은 하지만 무인예약 미지원)
   - `검색 결과 없음`
   - `요청 오류` (네트워크 재시도 소진)
   - `파싱 오류` (응답 구조 해석 실패, 대상 사이트 구조 변경 가능성)

> **보안 참고:** 원본 프로젝트의 HANDOFF.md에는 "API에 인증/접근 제어가 없다"는
> 미해결 경고가 있었습니다. 이 앱은 Streamlit 자체로 통합되어 별도 API를
> 노출하지 않지만, 서버가 인터넷에 공개되어 있다면 누구나 이 화면에 접근해
> 도서 목록을 보거나 수정할 수 있다는 점은 동일하게 적용됩니다. 필요하면
> 리버스 프록시 레벨의 Basic Auth나 IP 허용목록을 고려하세요.

## 로컬 개발 환경에서 개별 앱 실행

```bash
streamlit run portal.py --server.port 8500
streamlit run apps/library/app.py --server.port 8501
streamlit run apps/camping/app.py --server.port 8502
streamlit run apps/youtube_music/app.py --server.port 8503
```

## 배포 스크립트 안내

로컬(Windows)에서 서버로 파일을 전송하는 `deploy.bat` 스크립트를 각자 환경에 맞게 만들어 사용할 수 있습니다. 이 스크립트는 서버 접속 정보(IP, SSH 키 경로)를 담고 있어 저장소에는 포함하지 않았습니다 (`.gitignore` 처리됨).

직접 만들 경우 아래와 같은 형태로 구성하면 됩니다.

```bat
scp -r -i "<SSH 키 경로>" "apps" "<사용자>@<서버 IP>:<원격 경로>/"
scp -r -i "<SSH 키 경로>" "common" "<사용자>@<서버 IP>:<원격 경로>/"
scp -i "<SSH 키 경로>" "portal.py" "requirements.txt" "setup_linux.sh" "start_all.sh" "stop_all.sh" "<사용자>@<서버 IP>:<원격 경로>/"
```

또는 서버에서 `git pull`로 최신 코드를 받는 방식도 간단합니다.

```bash
cd streamlitapps
git pull
./stop_all.sh
./start_all.sh
```
