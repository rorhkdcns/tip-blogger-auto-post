import base64
import datetime
import html
import json
import os
import pickle
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

# [1단계] 라이브러리 자동 설치 및 검증
required_modules = [
    "google-auth-oauthlib", 
    "google-auth-httplib2", 
    "google-api-python-client", 
    "google-genai",
    "Pillow",
    "requests"
]

print("🔄 깃허브 액션 서버 환경 내 라이브러리 자동 설치 시작...")
for module in required_modules:
    try:
        if module == "google-genai":
            import google.genai
        elif module == "Pillow":
            import PIL
        else:
            __import__(module.replace('-', '_'))
    except ImportError:
        print(f"📦 {module} 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", module])
        time.sleep(1)

print("✅ 모든 라이브러리 설치 및 인식 완료! 본 코드를 시작합니다.")
print("-" * 60)

from googleapiclient.discovery import build
from google import genai 
from google.genai import types 
from PIL import Image, ImageDraw, ImageFont
import requests

# =====================================================================
# ⚙️ 고유 설정 정보 (대표님 맞춤형 인프라 각인)
# =====================================================================
BLOG_ID = "4906024564279839597"  # <생활 단축키> 고유 ID
FIREBASE_URL = "https://tip-blog-d03f8-default-rtdb.asia-southeast1.firebasedatabase.app/life/"

GOOGLE_ADSENSE_CLIENT = "ca-pub-**********7157" # 대표님 애드센스 정보 유지
GOOGLE_ADSENSE_SLOT = "798***********325"

GITHUB_USER_ID = "rorhkdcns"  
GITHUB_REPO_NAME = "tip-blogger-auto-post"  

# 🔋 [초대형 씨앗 탱크] 1년 무중단 가동용 고밀도 IT 트러블슈팅 키워드 120선
IT_LIFE_SEEDS = [
    # 1. 스마트폰 & SNS 오류 코어 덱
    "아이폰 카카오톡", "갤럭시 배터리", "인스타그램 스토리", "카톡 백업", "에어팟 연결 끊김",
    "아이패드 필기앱", "아이폰 화면 어두워짐", "카톡 글씨체", "아이폰 폰트", "카톡 단톡방 나가지기",
    "카톡 용량 줄이기", "아이폰 단축어", "아이폰 핫스팟 연결", "갤럭시 캡처 방법", "카카오페이 송금취소",
    "아이폰 사진 컴퓨터로", "갤럭시 사진 옮기기", "아이폰 무한사과", "에어팟 한쪽 소리", "버즈 연결 끊김",
    "카톡 캘린더 삭제", "아이폰 키보드 천지인", "인스타 계정 삭제", "인스타 비활성화", "페이스북 탈퇴",
    "갤럭시 안전모드", "아이폰 텍스트 대치", "카톡 생일 안뜨게", "아이폰 화면 녹화", "갤럭시 화면 녹화",
    "카톡 사진 고화질", "에어팟 프로 노이즈캔슬링", "갤럭시 듀얼메신저", "카톡 알림음 변경", "인스타 해킹 확인",
    "카톡 멀티프로필 확인", "네이버 앱 캐시삭제", "아이폰 에어드롭 안됨", "갤럭시 퀵쉐어 오류", "카톡 오픈프로필 삭제",
    
    # 2. PC & 브라우저 & 윈도우 에러 해결 덱
    "윈도우11 속도", "구글 크롬 메모리", "노트북 발열", "모니터 주사율", "와이파이 느릴때",
    "네이버 인증서", "구글 드라이브 공유", "지메일 수신확인", "알약 광고 제거", "윈도우 캡처 단축키",
    "윈도우 디펜더 끄기", "크롬 팝업 차단 해제", "프린터 오프라인", "공공와이파이 보안", "아이패드 미러링",
    "윈도우11 초기화", "맥북 한영전환", "구글 검색기록 삭제", "디스코드 마이크 안됨", "크롬 쿠키 삭제",
    "알약 삭제 오류", "윈도우 블루스크린", "공유기 비밀번호 초기화", "노트북 블루투스 사라짐", "윈도우 파일 영구삭제",
    "구글 계정 탈퇴", "노트북 터치패드 잠금", "윈도우 작업관리자 단축키", "구글 포토 백업 끄기", "윈도우 포맷 방법",
    "웨일 브라우저 다크모드", "윈도우 마우스 멈춤", "맥북 단축키 모음", "노트북 정전기 방전", "윈도우 업데이트 무한로딩",
    "크롬 느려질 때", "윈도우 비트락커 해제", "공인인증서 복사", "공동인증서 발급", "윈도우11 사양 확인",
    
    # 3. 업무 & 오피스 프로그램 생산성 덱
    "엑셀 단축키", "PDF 용량 줄이기", "엑셀 오류", "엑셀 파일 깨짐", "한글 파일 pdf 변환",
    "엑셀 vlookup 함수", "엑셀 드롭다운 만들기", "엑셀 시트 보호 해제", "피디에프 글자 수정", "엑셀 행고정",
    "피피티 글꼴 포함", "한글 자음 모음 분리", "워드 글자수 세기", "엑셀 중복값 제거", "노션 템플릿 복사",
    
    # 4. 스트리밍 & 여가 & 대중 트래픽 덱
    "유튜브 프리미엄", "넷플릭스 화질", "애플워치 방수", "티빙 동시접속", "쿠팡플레이 에러",
    "유튜브 음원 추출", "당근마켓 동네인증", "배달의민족 오류", "에어컨 제습 냉방", "스마트티비 연결",
    "스마트싱스 오류", "트위터 계정 찾기", "애플아이디 잠김", "갤럭시 무한부팅", "유튜브 시청기록 중지",
    "유튜브 알고리즘 초기화", "네이버 플러스 멤버십 해지", "네이버 메일 발송취소", "줌 마이크 소리", "유튜브 자막 끄기",
    "아이폰 통화녹음 방법", "갤럭시 통화자동녹음", "구글 플레이스토어 다운로드 대기", "아이폰 아이클라우드 백업", "멜론 이용권 해지"
]

ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 30px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

IT_CHECKLIST_CODE = """
<div class="calc-board-container" style="margin: 35px 0; padding: 22px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
    <p style="margin: 0 0 14px 0; font-size: 15px; font-weight: 700; color: #1e293b; border-left: 4px solid #2563eb; padding-left: 10px;">🛠️ 기기 및 프로그램 먹통 시 3대 자가점검표</p>
    <div style="font-size: 14px; color: #475569; line-height: 1.8;">
        1. <b>백그라운드 충돌:</b> 실행 중인 모든 앱 완전 종료 후 재시도<br>
        2. <b>네트워크 캐시:</b> 비행기 모드 10초 활성화 후 해제<br>
        3. <b>임시 파일 꼬임:</b> 기기 전원 끄기 후 2분 정지, 재부팅
    </div>
</div>
"""

CTA_CODE = """
<div class="cta-box" style="border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; background-color: #f8fafc; margin-top: 40px; text-align: center;">
    <p style="font-size: 15px; color: #2563eb; font-weight: 700; margin-bottom: 8px;">⚡ 생활 단축키 공식 매뉴얼 안내</p>
    <p style="font-size: 14px; color: #475569; line-height: 1.7; margin: 0;">
        IT 기기나 소프트웨어 오류는 공식 규격에 맞춘 스텝별 초기화가 가장 안전하고 빠릅니다.<br>
        위 솔루션을 순서대로 적용해 보신 후, 해결되지 않는 복합 증상은 하단의 재발 방지 권장 세팅을 유지해 주시기 바랍니다.
    </p>
</div>
"""

# =====================================================================
# 🎨 [정교한 1:1 정가운데 정렬] 미니멀리즘 썸네일 생성 모듈
# =====================================================================
def create_and_upload_thumbnail(title_text):
    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        print("⚠️ GITHUB_TOKEN이 감지되지 않아 썸네일 원격 전송을 생략합니다. (텍스트 전용 모드 가동)")
        return ""

    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
    font_path = "NanumGothic-Bold.ttf"
    if not os.path.exists(font_path):
        try: urllib.request.urlretrieve(font_url, font_path)
        except: pass

    # 📐 스마트폰 최적화 800x800 정방형 도화지 세팅
    img = Image.new('RGB', (800, 800), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype(font_path, 58) # 가시성 폭발하는 58 규격 고정
    except:
        title_font = ImageFont.load_default()

    # ✂️ 글자 줄바꿈 알고리즘 (가로폭에 맞춰 12자 기준 분할)
    words = title_text.split(' ')
    lines, curr = [], []
    for w in words:
        curr.append(w)
        if len(' '.join(curr)) > 12:
            lines.append(' '.join(curr[:-1]))
            curr = [w]
    lines.append(' '.join(curr))
    if len(lines) > 3: lines = [lines[0], lines[1], lines[2] + "..."]
    formatted_title = '\n'.join(lines)

    # 🎯 [정가운데 꽉 찬 자석 정렬] 상하좌우 불필요 요소를 다 지우고 글자만 정중앙 고정!
    draw.multiline_text((400, 400), formatted_title, fill="#f8fafc", font=title_font, spacing=26, anchor="mm", align="center")

    file_name = f"thumb_{int(time.time())}.webp"
    img.save(file_name, "WEBP", quality=82)

    with open(file_name, "rb") as f:
        encoded_content = base64.b64encode(f.read()).decode("utf-8")
        
    git_path = f"blog_images/life/{file_name}"
    url = f"https://api.github.com/repos/{GITHUB_USER_ID}/{GITHUB_REPO_NAME}/contents/{git_path}"
    headers = {"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github.v3+json"}
    
    sha = ""
    res_get = requests.get(url, headers=headers)
    if res_get.status_code == 200: sha = res_get.json().get("sha", "")

    payload = {"message": f"Auto-thumbnail: {file_name}", "content": encoded_content, "branch": "main"}
    if sha: payload["sha"] = sha
    
    res_put = requests.put(url, headers=headers, json=payload)
    if res_put.status_code in [200, 201]:
        print(f"🎨 정가운데 미니멀 썸네일 깃허브 업로드 성공! ({file_name})")
        return f"https://cdn.jsdelivr.net/gh/{GITHUB_USER_ID}/{GITHUB_REPO_NAME}@main/{git_path}"
    else:
        print(f"❌ [썸네일 업로드 실패] 코드: {res_put.status_code}, 사유: {res_put.text}")
        
    return ""

# =====================================================================
# 🌐 파이어베이스 중복검사 및 구글 자동완성 수집 모듈
# =====================================================================
def get_google_suggest(seed_word):
    url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={urllib.parse.quote(seed_word)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        return json.loads(res.text)[1]
    except: return []

def check_and_save_firebase(keyword):
    if not FIREBASE_URL or "your-project-id" in FIREBASE_URL:
        return False
        
    safe_kw = urllib.parse.quote(keyword.replace(".", "_").replace("/", "_").replace("$", "_").replace("#", "_"))
    url = f"{FIREBASE_URL}history/{safe_kw}.json"
    
    try:
        if requests.get(url, timeout=5).json() is not None: return True
        requests.put(url, json={"posted_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, timeout=5)
    except: pass
    return False

def get_unique_life_keyword():
    random.shuffle(IT_LIFE_SEEDS)
    for seed in IT_LIFE_SEEDS:
        suggestions = get_google_suggest(seed)
        for kw in reversed(suggestions):
            if not check_and_save_firebase(kw): return kw
    fallback = random.choice(IT_LIFE_SEEDS) + f" 오류 해결법 {random.randint(1,99)}"
    check_and_save_firebase(fallback)
    return fallback

# =====================================================================
# ✍️ 마크다운 표 포맷팅 및 AI 칼럼니스트 생성부
# =====================================================================
def format_paragraphs(text):
    if not text or not text.strip(): return ""
    processed_chunks = []
    in_table = False
    table_html = []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                in_table = True
                table_html = ['<div style="overflow-x:auto; margin: 25px 0;"><table style="width:100%; border-collapse:collapse; border:1px solid #cbd5e1;">']
            if not re.match(r'^\|(?:[\s\-:]+\|)+$', line):
                tds = ''.join([f'<td style="border:1px solid #cbd5e1; padding:12px; font-size:14px;">{c.strip()}</td>' for c in line.split('|')[1:-1]])
                table_html.append(f'<tr>{tds}</tr>')
        else:
            if in_table:
                in_table = False
                table_html.append('</table></div>')
                processed_chunks.append("".join(table_html))
                table_html = []
            processed_chunks.append(f'<p style="margin-bottom:20px; line-height:1.7; font-size:15px; color:#334155;">{line}</p>')
    if in_table:
        table_html.append('</table></div>')
        processed_chunks.append("".join(table_html))
    return "".join(processed_chunks)

def generate_blog_content(target_keyword):
    api_key_direct = os.environ.get("API_KEY")
    client = genai.Client(api_key=api_key_direct, http_options=types.HttpOptions(api_version="v1beta"))
    
    prompt = (
        "너는 10년 차 수석 IT 시스템 엔지니어이자 '생활 단축키' 전문 칼럼니스트야. "
        f"[{target_keyword}] 오류를 해결하기 위해 검색한 사용자의 시간을 10분의 1로 단축해주는 실전 매뉴얼을 작성해줘.\n\n"
        "[필수 작성 지침]\n"
        "1. [제목]: 직관적인 에러 증상과 '~~하는 법', '~~해결 방법' 형태의 명쾌한 가치를 담아라.\n"
        "2. [모바일 최적화]: 문장은 25자 내외로 짧게 끊고, 불필요한 접속사는 100% 삭제하라. 첫 문장에 독자의 답답함에 공감한 뒤 곧바로 해결 스텝을 제시하라.\n"
        "3. [본문 전개]: 해결 순서는 글머리기호를 쓰고, 원인 분석이나 설정값 비교는 반드시 마크다운 표(|구분|내용|)로 포맷팅하라.\n"
        "4. [재발 방지 팁]: 마지막 3번 소제목 하단에는 '수석 엔지니어가 짚어주는 재발 방지 꿀팁' 문단을 반드시 넣어라.\n"
        "5. [금지어]: '파소나', 'PASONA', '카피라이팅', 'AI', '인공지능', '자동화', '프로그램'.\n\n"
        "반드시 아래의 JSON 규격에 맞춰서 작성하고, JSON 데이터 외에 다른 설명 텍스트나 마크다운 문법은 일절 출력하지 마라.\n"
        "{\n"
        '  "title": "증상과 해결책이 명확한 제목",\n'
        '  "global_summary": "에러 증상 1줄, 핵심 해결법 2줄의 총 3문장 요약",\n'
        '  "tags": ["IT꿀팁", "오류해결", "생활단축키"],\n'
        '  "sub_title_1": "1. 가장 빠른 증상 해결 스텝",\n'
        '  "body_1": "1단계 본문 내용 (스텝별 정답 우선 배치)",\n'
        '  "sub_title_2": "2. 근본적인 에러 발생 원인",\n'
        '  "body_2": "2단계 본문 내용 (원인 분석용 마크다운 표 반드시 삽입)",\n'
        '  "sub_title_3": "3. 수석 엔지니어의 재발 방지 팁",\n'
        '  "body_3": "3단계 본문 내용 (권장 세팅 제안)"\n'
        "}"
    )
    
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7)
    
    for model in ['gemini-2.5-flash', 'gemini-2.5-pro']:
        for attempt in range(3):
            try:
                print(f"🤖 Gemini API 호출 중... (모델: {model}, 시도: {attempt+1}/3)")
                response = client.models.generate_content(model=model, contents=prompt, config=config)
                if response and response.text: return response.text
            except Exception as e:
                print(f"⚠️ 지연 발생: {e}")
                if attempt < 2: time.sleep(10)
    raise RuntimeError("🚨 데이터 생성 실패")

def check_already_posted(blogger, blog_id):
    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    try:
        posts = blogger.posts().list(blogId=blog_id, maxResults=10).execute()
        count = sum(1 for item in posts.get('items', []) if item.get('published', '').startswith(now.strftime('%Y-%m-%d')))
        if count >= 4: return True
    except: pass
    return False

# =====================================================================
# 🚀 메인 오퍼레이션 실행부
# =====================================================================
def main():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    b64_token = os.environ.get("TOKEN_PICKLE_BASE64")
    if not b64_token: 
        print("🚨 [🚨비상] GITHUB Secrets에 열쇠가 없습니다.")
        return
        
    blogger = build('blogger', 'v3', credentials=pickle.loads(base64.b64decode(b64_token)))
    
    if check_already_posted(blogger, BLOG_ID): 
        print("🛑 오늘 일일 발행 한도(4개)에 도달하여 스킵합니다.")
        return
    
    # 🔓 [트래블슈팅 완료] 새로운 지정 스케줄 운영을 위해 구형 1시간 연속 발행 제한 가드 제거
    
    target_keyword = get_unique_life_keyword()
    print(f"🎯 [수집 완료] 오늘 요리할 타겟 키워드: '{target_keyword}'")

    ai_json_response = generate_blog_content(target_keyword)
    try:
        clean_json = ai_json_response.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
    except Exception as e:
        raise ValueError(f"🚨 JSON 파싱 에러: {e}")

    title = data.get("title", f"{target_keyword} 완벽 해결법")
    tags = data.get("tags", ["IT꿀팁", "오류해결"])
    sub1, body1 = data.get("sub_title_1", "1. 핵심 해결 스텝"), data.get("body_1", "")
    sub2, body2 = data.get("sub_title_2", "2. 원인 분석"), data.get("body_2", "")
    sub3, body3 = data.get("sub_title_3", "3. 재발 방지 팁"), data.get("body_3", "")
    global_summary = data.get("global_summary", "")

    if len(body1) < 15 or len(body2) < 15: raise ValueError("🚨 본문 실종 에러")

    thumbnail_cdn_url = create_and_upload_thumbnail(title)
    
    thumb_html = f'<div style="text-align:center; margin:20px 0;"><img src="{thumbnail_cdn_url}" alt="{title}" style="max-width:100%; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);"/></div>' if thumbnail_cdn_url else ""
    gs_html = format_paragraphs(global_summary) if global_summary else ""
    quick_summary_box = f'<div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 18px; margin: 25px 0; border-radius: 0 8px 8px 0;"><p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 700; color: #2563eb;">⚡ QUICK TROUBLESHOOTING</p><div style="font-size: 14px; color: #334155;">{gs_html}</div></div>' if gs_html else ""

    final_html = thumb_html + quick_summary_box + ADSENSE_CODE + \
                 f'<h3 style="border-left:4px solid #2563eb; padding-left:10px; margin-top:30px;">{sub1}</h3>{format_paragraphs(body1)}' + IT_CHECKLIST_CODE + \
                 f'<h3 style="border-left:4px solid #2563eb; padding-left:10px; margin-top:30px;">{sub2}</h3>{format_paragraphs(body2)}' + ADSENSE_CODE + \
                 f'<h3 style="border-left:4px solid #2563eb; padding-left:10px; margin-top:30px;">{sub3}</h3>{format_paragraphs(body3)}' + \
                 ADSENSE_CODE + CTA_CODE

    try:
        # 구글 패치 우회 즉시 라이브 발행
        blogger.posts().insert(blogId=BLOG_ID, body={'title': title, 'content': final_html, 'labels': tags}, isDraft=False).execute()
        print(f"🚀 <생활 단축키> 2호기 규격화 포스팅 완벽 발행 성공! ({title})")
    except Exception as e:
        print(f"❌ 발행 에러: {e}")

if __name__ == "__main__":
    main()
