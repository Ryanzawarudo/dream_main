import os
import random
import smtplib
import ssl
from email.mime.text import MIMEText

from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.secret_key = 'dream_secret_key_look_at_here' #新增的行數喔
# 為了方便你直接測試，我幫你加了一個預設的測試帳號
# 格式為 { "信箱": { "username": "用戶名", "password": "密碼" } }
users = {
    'test@gmail.com': {
        'username': '夢境觀測員',
        'password': 'password123'
    }
}
verification_codes = {}
#廖子峰
# =======================================================
# 🔒 在這裡直接填入你的 GMAIL 帳號與 16 位應用程式密碼
# =======================================================
EMAIL_ADDRESS = '' 
EMAIL_APP_PASSWORD = '' # ⚠️ 注意：不能填一般密碼，要填 Google 申請的應用程式密碼
# =======================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify(success=False, message='Email and password are required'), 400

    user = users.get(email)
    if not user or user['password'] != password:
        return jsonify(success=False, message='Invalid email or password'), 401

    # ─── 幫同學新增這兩行，把登入狀態寫進後端 session ───
    # 這樣你的夢境分析路由才能成功抓到是哪一個 user_id 在存東西
    session['user'] = user['username']
    session['user_id'] = email # 目前同學沒有用數字 ID，先用 email 當作唯一識別碼
    # ─────────────────────────────────────────────────────

    return jsonify(success=True, message='Login successful', user={'username': user['username'], 'email': email})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    confirm_password = data.get('confirmPassword') or ''

    if not username or not email or not password or not confirm_password:
        return jsonify(success=False, message='All fields are required'), 400
    if password != confirm_password:
        return jsonify(success=False, message='Passwords do not match'), 400
    if email in users:
        return jsonify(success=False, message='Email already registered'), 409

    users[email] = {
        'username': username,
        'password': password,
    }
    return jsonify(success=True, message='Account created successfully')

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify(success=False, message='Email is required'), 400
    if email not in users:
        return jsonify(success=False, message='No account found for that email'), 404
        
    # 防止你忘記改範例帳密的安全檢查
    if EMAIL_ADDRESS == '你的帳號@gmail.com' or not EMAIL_APP_PASSWORD:
        return jsonify(success=False, message='Email service not configured. Please check app.py line 24.'), 500

    code = f"{random.randint(100000, 999999)}"
    verification_codes[email] = code

    subject = 'Subconscious Observation System 密碼重設驗證碼'
    body = (
        f'您好，\n\n請使用以下 6 位數驗證碼重設您的密碼：{code}\n\n'
        '如果您沒有提出重設請求，請忽略此郵件。'
    )

    try:
        message = MIMEText(body, _charset='utf-8')
        message['Subject'] = subject
        message['From'] = EMAIL_ADDRESS
        message['To'] = email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, email, message.as_string())
    except Exception as error:
        return jsonify(success=False, message=f'Email send failed: {error}'), 500

    return jsonify(success=True, message='Verification code sent')

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()
    password = data.get('password') or ''

    if not email or not code or not password:
        return jsonify(success=False, message='Email, code, and new password are required'), 400
    if email not in users:
        return jsonify(success=False, message='No account found for that email'), 404
    expected_code = verification_codes.get(email)
    if expected_code != code:
        return jsonify(success=False, message='Invalid verification code'), 400

    users[email]['password'] = password
    verification_codes.pop(email, None)
    return jsonify(success=True, message='Password reset successfully')

if __name__ == '__main__':
    app.run(debug=True)


# ------------------ Dream Weaver Room 後端擴充 ------------------
# 以下內容會附加在檔案末尾，採「新增」方式，不會改動上方任何既有路由或設定。
#   鄭崇恩
# 從設定檔讀取 Gemini API Key，並用指定的模型初始化 ChatGoogleGenerativeAI
from configparser import ConfigParser
# 建立 ConfigParser 物件以讀取 config.ini
config = ConfigParser()
# 讀取同一層目錄下的 config.ini 檔案
config.read("config.ini")
# 匯入 LangChain 的 Google Generative AI 客戶端
from langchain_google_genai import ChatGoogleGenerativeAI

# 使用指定的模型與從 config 取得的金鑰來初始化 LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=config["Gemini"]["API_KEY"]
)

import requests
import base64

# ==================== 完整替換掉原本的 generate_dream_image ====================
def generate_dream_image(image_prompt: str) -> str:
    try:
        import urllib.parse
        # 1. 將英文提示詞進行網址安全編碼，並動態加上高品質渲染字眼
        # 通用結構與畫質防禦詞：同時兼顧人體（anatomy）與物體邊緣（proportions, clean lines）
        encoded_prompt = urllib.parse.quote(f"{image_prompt}, surrealism style, crisp anatomy, flawless proportions, clean clear outlines, refined textures, 4k resolution")
        
        # 2. 呼叫 Pollinations 繪圖 API（API key 從 config.ini 讀取）
        pollinations_key = config.get('Pollinations', 'API_KEY', fallback='')
        url = f"https://gen.pollinations.ai/image/{encoded_prompt}?model=flux&width=1024&height=1024&seed=0&enhance=false&key={pollinations_key}"
        
        # 3. 發送 GET 請求取得圖片二進位數據
        response = requests.get(url, timeout=60) # 設定較長的超時時間以應對可能的延遲
        response.raise_for_status()
        
        # 4. 儲存圖片到 static/uploads，並回傳前端可直接存取的 URL
        image_bytes = response.content
        filename = f"dream_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}.jpg"
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        return f"/static/uploads/{filename}"
    except Exception as e:
        print(f"\n❌ 【備用繪圖 API 失敗報錯】: {e}\n")
        print(f"\nprompt: {image_prompt}\n")
        return ""
# =========================================================================

# 新增 /weaver 路由（GET）以呈現 weaver.html 模板
# 此路由會檢查 Flask session 是否有登入資訊，但仍允許訪客（guest）存取
from flask import session

@app.route('/weaver', methods=['GET'])
def weaver():
    # 取得 session 中儲存的使用者資訊（若有）
    # 注意：既有專案可能尚未設定 session 資料，這裡只做安全的取值檢查
    user = session.get('user') if isinstance(session, dict) or session else session.get('user') if hasattr(session, 'get') else None

    # 將 user 傳給模板以便前端視需要顯示已登入資訊；若為 None 則代表訪客
    return render_template('weaver.html', user=user)

@app.route('/data', methods=['GET'])
def data():
    user_id = session.get('user_id')
    username = session.get('user')
    if not user_id:
        return render_template('data.html', user=None, dreams=[], message='請先登入後再進入心靈數據室。')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, dream_content, reality_content, emotion_tag, ai_analysis, image_path, timestamp FROM dreams WHERE CAST(user_id AS TEXT) = ? ORDER BY timestamp DESC',
        (str(user_id),)
    )
    rows = cursor.fetchall()
    conn.close()

    dreams = [dict(row) for row in rows]
    return render_template('data.html', user=username, dreams=dreams, message=None)

# ------------------ Dream Weaver Room 擴充結束 ------------------


# ------------------ Dreams 資料表與儲存輔助函式（新增） ------------------
# 以下程式碼會在應用啟動時建立一個本地 Lite`SQ` 資料庫檔案，並建立 `dreams` 資料表（若尚未存在）
import sqlite3
from datetime import datetime

# 資料庫檔案路徑（放在專案根目錄，檔名為 dreams.db）
DB_PATH = os.path.join(os.path.dirname(__file__), 'dreams.db')
UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOADS_FOLDER, exist_ok=True)


def init_dreams_table():
    # 建立或開啟 SQLite 連線（若檔案不存在會自動建立）
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 啟用 foreign key 支援（SQLite 預設關閉，需要明確開啟）
    cursor.execute('PRAGMA foreign_keys = ON;')

    # 建立 `dreams` 資料表，若已存在則不會覆寫
    # 欄位說明：
    # - id: 主鍵整數（自動遞增）
    # - user_id: 整數，用來關聯到使用者（若您有資料庫中的 users 表，可視為外鍵）
    # - dream_content: 夢境文字內容（不可為 NULL）
    # - reality_content: 與現實事件的關聯說明（可為 NULL）
    # - emotion_tag: 情緒標籤（字串）
    # - ai_analysis: AI 分析結果文字
    # - timestamp: 儲存時間（預設使用本機時間的 YYYY-MM-DD HH:MM:SS）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dreams (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        dream_content TEXT NOT NULL,
        reality_content TEXT,
        emotion_tag TEXT,
        ai_analysis TEXT,
        image_path TEXT,
        timestamp TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # 提交並關閉連線
    conn.commit()
    conn.close()


# 在模組載入時初始化資料表，確保應用啟動後可直接使用
init_dreams_table()


def ensure_dreams_table_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(dreams)')
    columns = [row[1] for row in cursor.fetchall()]
    if 'image_path' not in columns:
        cursor.execute('ALTER TABLE dreams ADD COLUMN image_path TEXT')
    conn.commit()
    conn.close()

ensure_dreams_table_schema()


def save_dream_to_db(user_id, dream, reality=None, emotion=None, analysis=None, image_path=None):
    """
    將夢境資料寫入 `dreams` 資料表的輔助函式。

    參數：
    - user_id: 要儲存的使用者 ID（整數）
    - dream: 夢境內容（字串）
    - reality: 與現實相關的說明（字串或 None）
    - emotion: 情緒標籤（字串或 None）
    - analysis: AI 分析結果（字串或 None）

    回傳值：
    - True: 成功寫入資料庫
    - False: 未寫入（例如：沒有在 session 中找到對應的 user_id，即為訪客）

    注意：此函式會檢查 Flask 的 `session` 是否包含 `user_id`，
    若 session 中沒有 `user_id`（代表訪客），則不會進行寫入以保護資料完整性。
    """

    # 檢查目前 session 是否有登入的 user_id
    session_user_id = session.get('user_id')

    # 若 session 中沒有 user_id，或 session 的 user_id 與傳入的 user_id 不符，則視為未登入或不允許寫入
    if not session_user_id:
        # 不儲存，回傳 False 表示 bypass
        return False

    # 可選：若希望強制 session 中的 user_id 與參數 user_id 必須相符，啟用以下檢查
    if session_user_id != user_id:
        # 若不相符，拒絕寫入
        return False

    # 若通過檢查，建立連線並寫入資料
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 使用參數化查詢避免 SQL injection
    cursor.execute(
        '''
        INSERT INTO dreams (user_id, dream_content, reality_content, emotion_tag, ai_analysis, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (user_id, dream, reality, emotion, analysis, image_path)
    )

    conn.commit()
    conn.close()

    return True

# ------------------ Dreams 邏輯新增結束 ------------------


# ------------------ 分析路由：整合 LLM 與資料庫儲存（新增） ------------------
import json


@app.route('/api/analyze-dream', methods=['POST'])
def analyze_dream():
    # 此路由負責：
    # 1) 從前端接收夢境與可選的現實情況
    # 2) 使用已初始化的 Gemini LLM (`llm`) 扮演「專業夢境分析師」來產生分析結果
    # 3) 嘗試解析 LLM 回傳的 JSON（包含 emotion_tag 與 ai_analysis環境）
    # 4) 若使用者已登入（session 內有 user_id），則呼叫 save_dream_to_db 儲存紀錄

    data = request.get_json() or {}
    # 取得前端送來的夢境內容（必填）與現實情況（可為 None）
    dream = (data.get('dream') or '').strip()
    reality = data.get('reality')
    if isinstance(reality, str):
        reality = reality.strip() or None

    # 若夢境內容為空，回傳錯誤
    if not dream:
        return jsonify(success=False, message='夢境內容為空'), 400

    # 建立 system prompt，要求 LLM 扮演專業夢境分析師，並輸出結構化 JSON
    system_prompt = (
    "你是一位精通潛意識符號學與現代心理學的「神祕學夢境分析師」。"
    "請以溫和、沉穩且富有洞察力的語氣，為觀測者解密潛意識的訊號。\n\n"
    "【輸出限制】\n"
    "你必須「嚴格只輸出標準 JSON 格式」，絕對不可包含任何 Markdown 語法標記（如 ```json）或任何前後導言。回傳格式如下：\n"
    "{\n"
    '  "emotion_tag": "情緒標籤（必須且只能從『開心』、『難過』、『焦慮』、『憤怒』、『平靜』這五個詞中選擇一個）",\n'
    # ✅ 新增這一行
    '  "symbol_tags": ["象徵標籤1", "象徵標籤2", "象徵標籤3"],\n'
    '  "ai_analysis": "詳細的夢境解析文字",\n'
    '  "image_prompt": "Act as an expert prompt engineer for text-to-image AI. Generate a highly descriptive, atmospheric English prompt (60-80 words). You must strictly analyze the dream and apply the following compositional laws to prevent AI rendering glitches: 1. STYLE MATCHING: Dynamically match the style to the dream\'s emotion (e.g., Dali-Surrealism for fear, soft Ethereal Watercolor for calm, Muted Expressionism for sadness, Vibrant Whimsical Art for joy). Never use photo-realism. 2. CONDITIONAL SCENARIOS: [Scenario A: Close-up/Single Character] If the focus is on one person, explicitly specify \'clear defined facial features, sharp focus eyes, anatomically perfect hands, clean outlines\'. [Scenario B: Wide Shot/Multi-character/Sports] If the scene has multiple people or a wide landscape, FORBID micro-details. Instead, force the characters to be rendered as \'artistic back-lit silhouettes\', \'impressionistic figures with bold brushstrokes\', or \'stylized shadows\' to naturally bypass finger/face melting. 3. COMPOSITION AND STRUCTURE: Always enforce \'crisp geometry, structurally logical layout, balanced composition, no floating artifacts\'. Avoid overlapping complex grids like nets or wires unless stylized as solid art elements. Append premium quality tags like \'masterful composition, cinematic lighting, refined textures, 4k resolution\' at the very end."\n'
    "}\n\n"
    # --- 以下【分析邏輯與欄位規範】區塊在原本內容後面補上 symbol_tags 說明 ---
    "【分析邏輯與欄位規範】\n"
    "1. 當純粹分析夢境（無現實情況）時：\n"
    "   - `ai_analysis` 的內文「必須」直接以『這個夢境代表……』或『你的夢境情況很特別……』作為開頭。\n"
    "   - 請深入剖析夢中的象徵物（例如：蛇、墜落、被追逐）在心理學上的隱喻。\n\n"
    "2. 當同時包含夢境與現實情況時：\n"
    "   - `ai_analysis` 內文不需受到前述開頭限制。\n"
    "   - 你必須精準評估現實事件與夢境的相似性，並詳細解釋現實中的壓力、記憶或情感是如何被大腦轉化、投射進夢境的「因果關係」。\n"
    "   - 請提供觀測者具體的潛意識舒壓建議。\n\n"
    "3. `symbol_tags`：從夢境內容中提取 2 至 3 個最具代表性的潛意識象徵物或主題，\n"  # ✅ 新增說明
    "   以繁體中文短詞表示（每個標籤 2-5 個字，例如：「追逐」、「深海」、「陌生人」、「墜落感」）。\n\n"  # ✅ 新增說明
    "4. 核心氛圍：文字請保持超現實、富有心靈探索感的文學高質感，字數控制在 150 - 300 字之間。"
)

    # 組合要送給 LLM 的 user prompt（包含夢境與可能的現實情況）
    user_parts = [f"夢境內容:\n{dream}"]
    if reality:
        user_parts.append(f"現實情況:\n{reality}")
    user_prompt = "\n\n".join(user_parts)

    # 將 system 與 user prompt 合併為單一輸入
    full_prompt = system_prompt + "\n\n" + user_prompt

    #  修正後的部分：使用現代 LangChain 標準的 invoke 方法
    try:
        response = llm.invoke(full_prompt)
        raw = response.content
    except Exception as error:
        # 若 LLM 呼叫失敗，回報錯誤給前端
        return jsonify(success=False, message=f'LLM 呼叫失敗: {error}'), 500

    # 填補原本的代碼位置：解析 LLM 回傳（預期為 JSON 字串）
    emotion_tag = None
    ai_analysis = None
    parsed = None
    try:
        # ─── 新增：字串清洗邏輯，拔除 AI 自動加上的 Markdown 標籤 ───
        cleaned_raw = raw.strip()
        # 如果開頭帶有 ```json，就把這 7 個字元切掉
        if cleaned_raw.startswith("```json"):
            cleaned_raw = cleaned_raw[7:]
        # 如果開頭只有 ```，把這 3 個字元切掉
        elif cleaned_raw.startswith("```"):
            cleaned_raw = cleaned_raw[3:]
        # 如果結尾有 ```，把最後 3 個字元切掉
        if cleaned_raw.endswith("```"):
            cleaned_raw = cleaned_raw[:-3]
        # 清除前後多餘的空白或換行
        cleaned_raw = cleaned_raw.strip()
        # ──────────────────────────────────────────────────────────

        # 使用清洗乾淨的字串來轉成 Python 字典
        parsed = json.loads(cleaned_raw)
        
        # 取出兩個必要欄位
        emotion_tag = parsed.get('emotion_tag')
        ai_analysis = parsed.get('ai_analysis')
        symbol_tags = parsed.get('symbol_tags') or []
    except Exception:
        # 若不幸還是解析失敗，才走原本的備用流程
        ai_analysis = raw
        lowered = raw.lower() if isinstance(raw, str) else ''
        if any(k in lowered for k in ['開心', '高興', '愉快', '快樂', 'joy']):
            emotion_tag = '開心'
        elif any(k in lowered for k in ['難過', '悲傷', '沮喪', 'sad']):
            emotion_tag = '難過'
        elif any(k in lowered for k in ['焦慮', '緊張', '不安', 'anx']):
            emotion_tag = '焦慮'
        else:
            emotion_tag = '中性'
            symbol_tags = []

    # 若解析後欄位仍為 None，給予合理預設
    if not emotion_tag:
        emotion_tag = '中性'
    if not ai_analysis:
        ai_analysis = raw if isinstance(raw, str) else str(raw)

    # 1. 取出 Gemini 回傳 JSON 中的 image_prompt
    image_prompt = ""
    if isinstance(parsed, dict):
        image_prompt = parsed.get("image_prompt", "") or ""
    
    # 2. 呼叫第一步做好的影像生成函式
    image_url = generate_dream_image(image_prompt) if image_prompt else ""

    # 3. 若使用者已登入，將生成圖片路徑一併存儲到資料庫
    try:
        session_user_id = session.get('user_id')
        if session_user_id:
            save_dream_to_db(session_user_id, dream, reality, emotion_tag, ai_analysis, image_url or None)
    except Exception:
        pass  # 資料庫儲存失敗時安全的 pass，不影響網頁回傳

    # 4. 回傳給前端，記得把 image_url 一併打包送出
    return jsonify(success=True, result={
        'emotion_tag': emotion_tag,
        'ai_analysis': ai_analysis,
        'image_url': image_url,
        'symbol_tags': symbol_tags 
    })
# ------------------ 分析路由新增結束 ------------------