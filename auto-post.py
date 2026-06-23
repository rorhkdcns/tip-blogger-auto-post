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

# [1단계] 라이브러리 자동 설치 및 검증 (Pillow, requests 탑재 완료)
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
# ⚙️ 고유 설정 정보 (2호기 심장 ID 완벽 각인)
# =====================================================================
BLOG_ID = "4906024564279839597"  # <생활 단축키> tip.gwangchoon.com 고유 ID
FIREBASE_URL = "https://tip-blog-d03f8-default-rtdb.asia-southeast1.firebasedatabase.app/" # 파이어베이스 주소 (추후 입력 가능)

GOOGLE_ADSENSE_CLIENT = "ca-pub-4292478378917157" # 대표님 애드센스 계정 유지
GOOGLE_ADSENSE_SLOT = "7988651325"

GITHUB_USER_ID = "rorhkdcns"  
GITHUB_REPO_NAME = "tip-blogger-auto-post"  

# 💡 구글이 검열하지 않는 안전한 'IT/생활 트러블슈팅' 씨앗 키워드 덱
IT_LIFE_SEEDS = [
    "아이폰 카카오톡", "갤럭시 배터리", "윈도우11 속도", "엑셀 단축키", "유튜브 프리미엄",
    "넷플릭스 화질", "인스타그램 스토리", "구글 크롬 메모리", "PDF 용량 줄이기", "카톡 백업",
    "에어팟 연결 끊김", "아이패드 필기앱", "노트북 발열", "모니터 주사율", "와이파이 느릴때",
    "애플워치 방수", "티빙 동시접속", "쿠팡플레이 에러", "아이폰 화면 어두워짐", "엑셀 오류"
]

ADSENSE_CODE = """
<div class="adsense-container" style="text-align:center; margin: 30px 0;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={CLIENT}" crossorigin="anonymous"></script>
    <ins class="adsbygoogle" style="display:block" data-ad-client="{CLIENT}" data-ad-slot="{SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
""".replace("{CLIENT}", GOOGLE_ADSENSE_CLIENT).replace("{SLOT}", GOOGLE_ADSENSE_SLOT)

# 기존 주식 계산기 모음판을 대체하는 'IT 트러블슈팅 자가진단표' (레이어 풍부함 유지용)
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
# 🎨 썸네일 간판 실시간 렌더링 및 깃허브 REST API 푸시 모듈
# =====================================================================
def create_and_upload_thumbnail(title_text):
    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        print("⚠️ GITHUB_TOKEN이 감지되지 않아 썸네일 원격 전송을 생략합니다. (텍스트 전용 모드 가동)")
        return ""

    # 한글 깨짐 방지용 폰트 자동 다운로드
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
    font_path = "NanumGothic-Bold.ttf"
    if not os.path.exists(font_path):
        try: urllib.request.urlretrieve(font_url, font_path)
        except: pass

    # 📐 [정사각형 변환] 1200x630 규격을 스마트폰 최적화 800x800 정방형으로 체인지!
    img = Image.new('RGB', (800, 800), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype(font_path, 52) # 정사각형 매칭 폰트 크기 밸런스 조정
        badge_font = ImageFont.truetype(font_path, 26)
    except:
        title_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # 카테고리 뱃지 재배치 (좌측 여백 60 규격으로 통일)
    draw.rounded_rectangle([(60, 60), (330, 115)], radius=8, fill="#2563eb")
    draw.text((85, 72), "IT / 트러블슈팅 💡", fill="white", font=badge_font)

    # ✂️ [줄바꿈 최적화] 가로 폭이 좁아진 만큼, 12자 기준으로 더 찰지게 끊어지도록 설계!
    words = title_text.split(' ')
    lines, curr = [], []
    for w in words:
        curr.append(w)
        if len(' '.join(curr)) > 12:
            lines.append(' '.join(curr[:-1]))
            curr = [w]
    lines.append(' '.join(curr))
    # 정방형 공간 특성상 최대 3줄까지 이쁘게 수용 가능
    if len(lines) > 3: lines = [lines[0], lines[1], lines[2] + "..."]
    formatted_title = '\n'.join(lines)

    # 본문 제목 및 푸터 워터마크 정밀 고정
    draw.multiline_text((60, 180), formatted_title, fill="#f8fafc", font=title_font, spacing=22)
    draw.text((60, 710), "© tip.gwangchoon.com", fill="#64748b", font=badge_font)

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
        print(f"🎨 1:1 정방형 썸네일 간판 깃허브 업로드 성공! ({file_name})")
        return f"https://cdn.jsdelivr.net/gh/{GITHUB_USER_ID}/{GITHUB_REPO_NAME}@main/{git_path}"
    else:
        print(f"❌ [썸네일 업로드 실패] 코드: {res_put.status_code}, 사유: {res_put.text}")
        
    return ""

# =====================================================================
# 🌐 파이어베이스 무중단 중복검사 및 구글 자동완성 수집 모듈
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
        for kw in reversed(suggestions): # 구체적 롱테일(배열 뒤쪽)부터 추출
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
        "2. [모바일 최적화]: 문장은 25자 내외로 짧게 끊고, 불필요한 접속사(또한, 반면에 등)는 100% 삭제하라. 첫 문장에 독자의 답답함에 1초 만에 공감한 뒤 곧바로 해결 스텝을 제시하라.\n"
        "3. [본문 전개]: 해결 순서는 글머리기호(-, 1. 2.)를 쓰고, 원인 분석이나 설정값 비교는 반드시 마크다운 표(|구분|내용|)로 포맷팅하라.\n"
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
        print("🚨 [🚨비상] GITHUB Secrets에 'TOKEN_PICKLE_BASE64' 열쇠가 등록되지 않았습니다! 메인을 종료합니다.")
        return
        
    blogger = build('blogger', 'v3', credentials=pickle.loads(base64.b64decode(b64_token)))
    
    if check_already_posted(blogger, BLOG_ID): 
        print("🛑 오늘 일일 발행 한도(4개)에 도달하여 스킵합니다.")
        return
    
    try:
        posts = blogger.posts().list(blogId=BLOG_ID, maxResults=1).execute()
      # ✅ 변경 코드 ('return' 앞에 #을 붙여서 락을 일시 무력화!)
        if posts.get('items'):
            last_pub_time = datetime.datetime.fromisoformat(posts['items'][0].get('published', '').replace('Z', '+00:00')).astimezone(kst)
            if (datetime.datetime.now(kst) - last_pub_time).total_seconds() < 3600:
                print("⏳ 1시간 이내 연속 발행 방지 락 작동 중.")
                # return   # 🌟 앞에 샵(#)을 붙여서 이 줄을 그냥 주석(메모)처리 합니다!
    except: pass
    
    target_keyword = get_unique_life_keyword()
    print(f"🎯 [수집 완료] 오늘 요리할 타겟 키워드: '{target_keyword}'")

    ai_json_response = generate_blog_content(target_keyword)
    try:
        # ★[수정 완료] 줄바꿈 에러 유발하던 replace 구문 정갈하게 한 줄로 봉합 완료!
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

    # 썸네일 간판 렌더링 및 깃허브 CDN 업로드
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
        # ★[수정 완료] 'published' 미래 예약 인자를 과감히 삭제하여 즉시 전광판에 꽂히도록 봉합!
        blogger.posts().insert(blogId=BLOG_ID, body={'title': title, 'content': final_html, 'labels': tags}, isDraft=False).execute()
        print(f"🚀 <생활 단축키> 2호기 규격화 포스팅 완벽 발행 성공! ({title})")
    except Exception as e:
        print(f"❌ 발행 에러: {e}")

if __name__ == "__main__":
    main()
