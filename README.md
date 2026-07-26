# 내 정보 대시보드 (Streamlit Apps)

개인용 정보 수집 & 유틸리티 서비스를 모아둔 Streamlit 기반 대시보드입니다.
각 앱은 독립된 프로세스/포트로 실행되며, 허브 페이지에서 한눈에 모아볼 수 있습니다.

## 앱 구성

| 앱 | 포트 | 설명 | 상태 |
|---|---|---|---|
| 🏠 허브 (portal.py) | 8500 | 전체 앱 소개 및 바로가기 | 운영중 |
| 🏕️ 캠핑장 빈자리 찾기 | 8502 | 날짜별 캠핑장 예약 가능 현황 조회 (xticket API) | 운영중 |
| 🎵 유튜브 음악 다운로드 | 8503 | 유튜브 URL → MP3 변환/다운로드, 3일 후 자동 삭제 | 운영중 |
| 📚 도서관 책 찾기 | 8501 | 관심 도서 대여 현황 조회 | 보류중 (샘플 데이터만 표시) |

## 프로젝트 구조

```
.
├── portal.py                   # 허브 (앱 소개 + 바로가기)
├── apps/
│   ├── camping/                 # 캠핑장 빈자리 찾기
│   │   ├── app.py                # Streamlit 화면
│   │   ├── config.py             # 캠핑장 목록/설정 (여기에 캠핑장 추가)
│   │   └── scraper.py            # xticket API 조회 로직
│   ├── youtube_music/            # 유튜브 음악 다운로드
│   │   ├── app.py                # Streamlit 화면
│   │   ├── config.py             # 다운로드 경로/보관 기간 설정
│   │   ├── downloader.py         # yt-dlp 기반 다운로드 로직
│   │   └── cleanup.py            # 오래된 파일 자동 삭제 스크립트
│   └── library/                  # 도서관 책 찾기 (보류중)
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
- 실행에 필요한 `logs/`, `pids/` 디렉토리 생성
- 실행 스크립트에 실행 권한 부여

MP3 변환을 위해 FFmpeg도 설치해야 합니다.

```bash
sudo apt update
sudo apt install ffmpeg -y
```

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

1. 조회할 시작/종료 날짜를 선택합니다.
2. 조회할 캠핑장을 선택합니다 (다중 선택 가능).
3. "🔍 빈자리 조회" 버튼을 누르면 선택한 기간/캠핑장의 예약 가능 현황을 보여줍니다.

새 캠핑장을 추가하려면 `apps/camping/config.py`의 `CAMPSITES` 리스트에 xticket API 정보(`shop_code`, `product_group_code` 등)를 추가하면 됩니다.

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

### 📚 도서관 책 찾기 (보류중)

현재는 화면 구조와 샘플 데이터만 존재하며, 실제 도서관 크롤링 로직(`apps/library/scraper.py`)은 아직 구현되지 않았습니다.

## 로컬 개발 환경에서 개별 앱 실행

```bash
streamlit run portal.py --server.port 8500
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
