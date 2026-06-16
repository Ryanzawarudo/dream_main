import os
import random
import smtplib
import ssl
import sqlite3
import json
from flask import send_from_directory
from datetime import datetime
from email.mime.text import MIMEText
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.secret_key = 'dream_secret_key_look_at_here' #新增的行數喔
verification_codes = {}

# 資料庫檔案路徑（放在專案根目錄，檔名為 account.db）
DB_PATH = os.path.join(os.path.dirname(__file__), 'account.db')
UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOADS_FOLDER, exist_ok=True)

# 廖子峰
# =======================================================
# 🔒 在這裡直接填入你的 GMAIL 帳號與 16 位應用程式密碼
# =======================================================
EMAIL_ADDRESS = '' 
EMAIL_APP_PASSWORD = '' # ⚠️ 注意：不能填一般密碼，要填 Google 申請的應用程式密碼
# =======================================================


def init_account_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON;')

    # 使用者帳號表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )
    ''')

    # 夢境資料表，與使用者 ID 關聯
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dreams (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        dream_content TEXT NOT NULL,
        reality_content TEXT,
        emotion_tag TEXT,
        ai_analysis TEXT,
        image_path TEXT,
        dream_date TEXT NOT NULL DEFAULT (date('now','localtime')),
        timestamp TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # 使用者遊戲統計表（每位使用者一列）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_game_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        angry_corrected INTEGER DEFAULT 0,
        electric_success INTEGER DEFAULT 0,
        electric_fail INTEGER DEFAULT 0,
        mines_success INTEGER DEFAULT 0,
        mines_fail INTEGER DEFAULT 0,
        popfat_max_kg REAL DEFAULT 0,
        tetris_lines_cleared INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    # 預設測試帳號（如果尚未存在）
    cursor.execute('SELECT id FROM users WHERE email = ?', ('test@gmail.com',))
    if cursor.fetchone() is None:
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            ('夢境觀測員', 'test@gmail.com', generate_password_hash('password123'))
        )

    conn.commit()
    conn.close()


init_account_db()

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

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash FROM users WHERE email = ?', (email,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row or not check_password_hash(user_row['password_hash'], password):
        return jsonify(success=False, message='Invalid email or password'), 401

    session['user'] = user_row['username']
    session['user_id'] = user_row['id']
    session['user_email'] = email

    return jsonify(success=True, message='Login successful', user={'username': user_row['username'], 'email': email})

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

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone() is not None:
        conn.close()
        return jsonify(success=False, message='Email already registered'), 409

    cursor.execute(
        'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
        (username, email, generate_password_hash(password))
    )
    conn.commit()
    conn.close()

    return jsonify(success=True, message='Account created successfully')

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify(success=False, message='Email is required'), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify(success=False, message='No account found for that email'), 404
    conn.close()

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

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify(success=False, message='No account found for that email'), 404

    expected_code = verification_codes.get(email)
    if expected_code != code:
        conn.close()
        return jsonify(success=False, message='Invalid verification code'), 400

    cursor.execute(
        'UPDATE users SET password_hash = ? WHERE email = ?',
        (generate_password_hash(password), email)
    )
    conn.commit()
    conn.close()
    verification_codes.pop(email, None)
    return jsonify(success=True, message='Password reset successfully')

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify(success=True, message='已登出，您現在為訪客。')

@app.route('/api/session', methods=['GET'])
def api_session():
    user = session.get('user')
    if user and session.get('user_id'):
        return jsonify(success=True, user={'username': user, 'email': session.get('user_email')})
    return jsonify(success=True, user=None)


# ------------------ Dream Weaver Room 後端擴充 ------------------
# 以下內容會附加在檔案末尾，採「新增」方式，不會改動上方任何既有路由或設定。
# 鄭崇恩
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
    model="gemini-2.5-flash-lite", 
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
        return render_template(
            'data.html',
            user=None,
            dreams=[],
            message='您目前為訪客，請登入後再使用此功能。'
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, dream_content, reality_content, emotion_tag, ai_analysis, image_path, dream_date, timestamp FROM dreams WHERE user_id = ? ORDER BY COALESCE(dream_date, substr(timestamp,1,10)) DESC, timestamp DESC',
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    dreams = [dict(row) for row in rows]
    return render_template('data.html', user=username, dreams=dreams, message=None)

# ------------------ Dream Weaver Room 擴充結束 ------------------


# ------------------ Dreams 資料表與儲存輔助函式（新增） ------------------
# 使用 account.db 作為單一 SQLite 資料庫，包含 users 與 dreams 表

def ensure_dreams_table_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(dreams)')
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'image_path' not in columns:
        cursor.execute('ALTER TABLE dreams ADD COLUMN image_path TEXT')
    if 'dream_date' not in columns:
        cursor.execute('ALTER TABLE dreams ADD COLUMN dream_date TEXT')
    # ✅ 偷偷新增一個儲存「細分情緒比例」的欄位
    if 'emotion_details' not in columns:
        cursor.execute('ALTER TABLE dreams ADD COLUMN emotion_details TEXT')
        
    conn.commit()
    conn.close()

ensure_dreams_table_schema()


def ensure_user_game_stats_table_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(user_game_stats)')
    columns = [row[1] for row in cursor.fetchall()]

    # If table doesn't exist, create it (defensive)
    if not columns:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_game_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            angry_corrected INTEGER DEFAULT 0,
            electric_success INTEGER DEFAULT 0,
            electric_fail INTEGER DEFAULT 0,
            mines_success INTEGER DEFAULT 0,
            mines_fail INTEGER DEFAULT 0,
            popfat_max_kg REAL DEFAULT 0,
            tetris_lines_cleared INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        conn.commit()
    conn.close()


ensure_user_game_stats_table_schema()


def get_or_create_user_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_game_stats WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        result = dict(row)
        conn.close()
        return result

    # create default
    cursor.execute('''
    INSERT INTO user_game_stats (user_id) VALUES (?)
    ''', (user_id,))
    conn.commit()
    cursor.execute('SELECT * FROM user_game_stats WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    result = dict(row) if row else None
    conn.close()
    return result


# GET current user's game stats
@app.route('/api/game-stats', methods=['GET'])
def api_get_game_stats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify(success=False, message='請先登入'), 401

    try:
        stats = get_or_create_user_stats(user_id)
        # remove internal id and user_id duplication for client
        if stats and 'user_id' in stats:
            stats.pop('id', None)
        return jsonify(success=True, stats=stats)
    except Exception as e:
        return jsonify(success=False, message=f'無法取得統計: {e}'), 500


# POST update: accepts payload like {"angry_corrected": {"op":"inc","val":1}, "popfat_max_kg": {"op":"max","val":2.3}}
@app.route('/api/game-stats', methods=['POST'])
def api_update_game_stats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify(success=False, message='請先登入'), 401

    data = request.get_json() or {}
    if not isinstance(data, dict) or not data:
        return jsonify(success=False, message='缺少更新資料'), 400

    allowed = {
        'angry_corrected': 'INTEGER',
        'electric_success': 'INTEGER',
        'electric_fail': 'INTEGER',
        'mines_success': 'INTEGER',
        'mines_fail': 'INTEGER',
        'popfat_max_kg': 'REAL',
        'tetris_lines_cleared': 'INTEGER'
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for key, payload in data.items():
            if key not in allowed:
                continue

            # normalize payload
            op = None
            val = None
            if isinstance(payload, dict):
                op = payload.get('op')
                val = payload.get('val')
            elif isinstance(payload, (int, float)):
                op = 'inc'
                val = payload
            else:
                continue

            if op == 'inc':
                cursor.execute(f'UPDATE user_game_stats SET {key} = COALESCE({key},0) + ?, updated_at = datetime(\'now\',\'localtime\') WHERE user_id = ?', (val, user_id))
            elif op == 'set':
                cursor.execute(f'UPDATE user_game_stats SET {key} = ?, updated_at = datetime(\'now\',\'localtime\') WHERE user_id = ?', (val, user_id))
            elif op == 'max' and val is not None:
                cursor.execute(f'UPDATE user_game_stats SET {key} = CASE WHEN ? > COALESCE({key},0) THEN ? ELSE {key} END, updated_at = datetime(\'now\',\'localtime\') WHERE user_id = ?', (val, val, user_id))
            else:
                # unknown op -> skip
                continue

        conn.commit()
        conn.close()

        stats = get_or_create_user_stats(user_id)
        if stats and 'user_id' in stats:
            stats.pop('id', None)
        return jsonify(success=True, stats=stats)
    except Exception as e:
        return jsonify(success=False, message=f'更新失敗: {e}'), 500


def save_dream_to_db(user_id, dream, reality=None, emotion=None, analysis=None, image_path=None, dream_date=None, emotion_details=None):
    """
    將夢境資料寫入 `dreams` 資料表的輔助函式。包含隱藏的 emotion_details 比例儲存。
    """
    # 檢查目前 session 是否有登入的 user_id
    session_user_id = session.get('user_id')

    # 若 session 中沒有 user_id，或 session 的 user_id 與傳入的 user_id 不符，則視為未登入或不允許寫入
    if not session_user_id or session_user_id != user_id:
        return False

    # 若通過檢查，建立連線並寫入資料
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not dream_date:
        dream_date = datetime.now().strftime('%Y-%m-%d')

    # 使用參數化查詢避免 SQL injection
    cursor.execute(
        '''
        INSERT INTO dreams (user_id, dream_content, reality_content, emotion_tag, ai_analysis, image_path, dream_date, emotion_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (user_id, dream, reality, emotion, analysis, image_path, dream_date, emotion_details)
    )

    conn.commit()
    conn.close()

    return True

# ------------------ Dreams 邏輯新增結束 ------------------


# ------------------ 分析路由：整合 LLM 與資料庫儲存（新增） ------------------

@app.route('/api/save-dream-only', methods=['POST'])
def save_dream_only():
    data = request.get_json() or {}
    dream = (data.get('dream') or '').strip()
    reality = data.get('reality')
    if isinstance(reality, str):
        reality = reality.strip() or None
    dream_date = (data.get('dream_date') or '').strip() or None

    if not dream:
        return jsonify(success=False, message='夢境內容為空'), 400

    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify(success=False, message='請先登入後再使用此功能'), 401

    try:
        # 新增的欄位給予 None
        save_dream_to_db(session_user_id, dream, reality, None, None, None, dream_date, None)
    except Exception as err:
        return jsonify(success=False, message=f'儲存失敗：{err}'), 500

    return jsonify(success=True, message='夢境已儲存，不進行 AI 分析')


@app.route('/api/analyze-dream', methods=['POST'])
def analyze_dream():
    data = request.get_json() or {}
    dream = (data.get('dream') or '').strip()
    reality = data.get('reality')
    if isinstance(reality, str):
        reality = reality.strip() or None
    dream_date = (data.get('dream_date') or '').strip() or None

    if not dream:
        return jsonify(success=False, message='夢境內容為空'), 400

    # ✅ 將你的完美情緒清單融入 Prompt 中，並要求 AI 給出細分比例與單一顯示標籤
    system_prompt = (
        "你是一位精通潛意識符號學與現代心理學的「神祕學夢境分析師」。\n"
        "【輸出限制】\n"
        "嚴格只輸出標準 JSON 格式，不可包含 Markdown 語法標記（如 ```json）。格式如下：\n"
        "{\n"
        '  "emotion_tag": "單一核心情緒（例如：被背叛感、悵然若失、欣喜若狂等，供前端版面顯示用）",\n'
        '  "emotion_details": {"難過": 70, "生氣": 30},\n'
        '  "symbol_tags": ["象徵標籤1", "象徵標籤2", "象徵標籤3"],\n'
        '  "ai_analysis": "詳細的夢境解析文字",\n'
        '  "image_prompt": "Act as an expert prompt engineer for text-to-image AI. Generate a highly descriptive, atmospheric English prompt (60-80 words). You must strictly analyze the dream and apply the following compositional laws to prevent AI rendering glitches: 1. STYLE MATCHING: Dynamically match the style to the dream\'s emotion (e.g., Dali-Surrealism for fear, soft Ethereal Watercolor for calm, Muted Expressionism for sadness, Vibrant Whimsical Art for joy). Never use photo-realism. 2. CONDITIONAL SCENARIOS: [Scenario A: Close-up/Single Character] If the focus is on one person, explicitly specify \'clear defined facial features, sharp focus eyes, anatomically perfect hands, clean outlines\'. [Scenario B: Wide Shot/Multi-character/Sports] If the scene has multiple people or a wide landscape, FORBID micro-details. Instead, force the characters to be rendered as \'artistic back-lit silhouettes\', \'impressionistic figures with bold brushstrokes\', or \'stylized shadows\' to naturally bypass finger/face melting. 3. COMPOSITION AND STRUCTURE: Always enforce \'crisp geometry, structurally logical layout, balanced composition, no floating artifacts\'. Avoid overlapping complex grids like nets or wires unless stylized as solid art elements. Append premium quality tags like \'masterful composition, cinematic lighting, refined textures, 4k resolution\' at the very end."\n'
        "}\n\n"
        "【情緒細分邏輯 (emotion_details)】\n"
        "請發揮心理學專業，將夢境情緒「解構」成多種比例（總和必須為 100）。\n"
        "例如：被朋友出賣的夢，其實往往不是只有氣，可能是 {\"難過\": 70, \"生氣\": 30}。\n"
        "請善用以下細膩的情緒詞彙分類：\n"
        "- 快樂類：欣喜若狂, 滿足, 愜意, 成就感, 歸屬感, 期待感, 刺激, 被肯定\n"
        "- 悲傷類：悵然若失, 依依不捨, 心碎, 無助, 沮喪, 委屈, 遺憾, 自責\n"
        "- 憤怒類：暴怒, 煩躁, 怨氣, 不甘心, 吃醋, 被背叛感\n"
        "- 恐懼類：驚恐, 忐忑, 怕被拋棄, 社交焦慮, 惶恐\n"
        "- 驚奇類：驚喜, 錯愕, 駭然\n"
        "- 愛與平靜：心動, 佔有慾, 患得患失, 放鬆, 釋然, 寧靜\n"
        "- 混合型：五味雜陳, 愛恨交織, 哭笑不得, 既感動又愧疚\n\n"
        "【分析邏輯與欄位規範】\n"
        "1. 當純粹分析夢境（無現實情況）時：\n"
        "   - `ai_analysis` 的內文「必須」直接以『這個夢境代表……』或『你的夢境情況很特別……』作為開頭。\n"
        "   - 請深入剖析夢中的象徵物在心理學上的隱喻。\n\n"
        "2. 當同時包含夢境與現實情況時：\n"
        "   - 你必須精準評估現實事件與夢境的相似性，解釋現實壓力如何轉化為夢境，並提供具體舒壓建議。\n\n"
        "3. 核心氛圍：文字請保持超現實、富有心靈探索感的文學高質感，字數控制在 150 - 300 字之間。"
    )

    user_parts = [f"夢境內容:\n{dream}"]
    if reality:
        user_parts.append(f"現實情況:\n{reality}")
    user_prompt = "\n\n".join(user_parts)
    full_prompt = system_prompt + "\n\n" + user_prompt

    try:
        response = llm.invoke(full_prompt)
        raw = response.content
    except Exception as error:
        return jsonify(success=False, message=f'LLM 呼叫失敗: {error}'), 500

    emotion_tag = "中性"
    emotion_details_str = None
    ai_analysis = raw if isinstance(raw, str) else str(raw)
    symbol_tags = []
    image_prompt = ""

    try:
        cleaned_raw = raw.strip()
        # 將反引號拆開寫，避開複製時的 Markdown Bug
        if cleaned_raw.startswith("```" + "json"): 
            cleaned_raw = cleaned_raw[7:]
        elif cleaned_raw.startswith("```"): 
            cleaned_raw = cleaned_raw[3:]
        if cleaned_raw.endswith("```"): 
            cleaned_raw = cleaned_raw[:-3]
        cleaned_raw = cleaned_raw.strip()

        parsed = json.loads(cleaned_raw)
        
        # 解析出供拍立得顯示的單一情緒與其他常規屬性
        emotion_tag = parsed.get('emotion_tag', '中性')
        ai_analysis = parsed.get('ai_analysis', ai_analysis)
        symbol_tags = parsed.get('symbol_tags', [])
        image_prompt = parsed.get('image_prompt', "")
        
        # 解析出圖表要用的細分情緒比例，轉成 JSON 字串以便存入隱藏欄位
        details = parsed.get('emotion_details')
        if isinstance(details, dict):
            emotion_details_str = json.dumps(details, ensure_ascii=False)
            
    except Exception:
        pass

    image_url = generate_dream_image(image_prompt) if image_prompt else ""

    try:
        session_user_id = session.get('user_id')
        if session_user_id:
            save_dream_to_db(
                session_user_id, dream, reality, emotion_tag, ai_analysis, image_url or None, dream_date, emotion_details_str
            )
    except Exception:
        pass

    # 回傳給前端時，依舊只送單一的 emotion_tag，完全保護你的介面不被破壞！
    return jsonify(success=True, result={
        'emotion_tag': emotion_tag,
        'ai_analysis': ai_analysis,
        'image_url': image_url,
        'symbol_tags': symbol_tags,
        'emotion_details': json.loads(emotion_details_str) if emotion_details_str else None 
    })


# ------------------ 時空膠囊（情緒圖表）路由擴充（新增） ------------------

@app.route('/capsule', methods=['GET'])
def capsule():
    """
    負責渲染 capsule.html（情緒圖表室）的頁面。
    """
    user = session.get('user')
    return render_template('capsule.html', user=user)

@app.route('/api/emotion-data', methods=['GET'])
def api_emotion_data():
    """
    負責從資料庫撈取當前登入使用者的所有夢境情緒，
    計算次數/比例，並回傳「情緒 -> 夢境列表」的映射字典供懸停使用。
    """
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify(success=False, message='請先登入後再檢視情緒圖表'), 401

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 多撈出 dream_date 和 dream_content，並依照時間新到舊排序
        cursor.execute('''
            SELECT emotion_tag, emotion_details, dream_date, dream_content 
            FROM dreams
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()

        emotion_counter = {}
        dream_mapping = {}  # ✅ 新增：用來記錄每個情緒對應了哪些夢境

        for row in rows:
            tag_data = row[0]
            details_data = row[1]
            d_date = row[2] or "未知日期"
            d_content = row[3] or ""
            
            # 截短夢境內容避免畫面被塞爆 (取前 45 個字)
            snippet = d_content[:45] + '...' if len(d_content) > 45 else d_content
            emotions_in_this_dream = []

            # 讀取細分情緒比例
            if details_data:
                try:
                    emotions = json.loads(details_data)
                    if isinstance(emotions, dict):
                        for e_name, e_weight in emotions.items():
                            emotion_counter[e_name] = emotion_counter.get(e_name, 0) + float(e_weight)
                            if e_name not in emotions_in_this_dream:
                                emotions_in_this_dream.append(e_name)
                except:
                    pass
            else:
                # 兼容舊版：單一情緒
                if tag_data and tag_data != '中性' and tag_data != '':
                    emotion_counter[tag_data] = emotion_counter.get(tag_data, 0) + 100.0
                    emotions_in_this_dream.append(tag_data)

            # ✅ 將這個夢境的日期與摘要，分類塞進對應的情緒清單裡
            for e_name in emotions_in_this_dream:
                if e_name not in dream_mapping:
                    dream_mapping[e_name] = []
                dream_mapping[e_name].append({
                    'date': d_date,
                    'snippet': snippet
                })

        labels = list(emotion_counter.keys())
        values = list(emotion_counter.values())

        # 把 mapping 一起回傳給前端
        return jsonify(success=True, labels=labels, values=values, mapping=dream_mapping)

    except Exception as e:
        print(f"撈取情緒數據失敗: {e}")
        return jsonify(success=False, message='資料庫讀取發生錯誤'), 500

# ------------------ 時空膠囊路由擴充結束 ------------------

# ==================== 生氣遊戲路由 ====================
angry_paper_index = -1
ANGRY_PAPERS = ['paper1.jpg', 'paper2.jpg', 'paper3.jpg', 'paper4.jpg']

@app.route('/games/angry')
def angry_game():
    return send_from_directory('static/games/angry', 'index.html')

@app.route('/get_next_paper', methods=['POST', 'GET'])
def get_next_paper():
    global angry_paper_index
    angry_paper_index += 1
    total = len(ANGRY_PAPERS)
    if angry_paper_index >= total:
        return jsonify({'game_over': True, 'message': '遊戲結束'})
    paper_url = f'/static/games/angry/{ANGRY_PAPERS[angry_paper_index]}'
    return jsonify({
        'paper_url': paper_url,
        'current': angry_paper_index + 1,
        'total': total,
        'game_over': False
    })

@app.route('/reset', methods=['POST'])
def reset_angry_game():
    global angry_paper_index
    angry_paper_index = -1
    return jsonify({'message': '遊戲已重置'})

# ==================== Electric 遊戲路由 ====================
@app.route('/games/electric')
def electric_game():
    return send_from_directory('static/games/electric', 'index.html')

@app.route('/api/check-music', methods=['GET'])
def check_music():
    try:
        music_folder = os.path.join(os.path.dirname(__file__), 'static', 'games', 'electric', 'music')
        music_data = {'background': [], 'success': [], 'scare': [], 'all_available': False}
        if os.path.exists(music_folder):
            for file in os.listdir(music_folder):
                file_lower = file.lower()
                if file_lower.startswith('background') and file_lower.endswith('.mp3'):
                    music_data['background'].append(file)
                elif (file_lower.startswith('success') or file_lower.startswith('win')) and file_lower.endswith('.mp3'):
                    music_data['success'].append(file)
                elif file_lower.startswith('scare') and file_lower.endswith('.mp3'):
                    music_data['scare'].append(file)
            music_data['all_available'] = (
                len(music_data['background']) > 0 and
                len(music_data['success']) > 0 and
                len(music_data['scare']) > 0
            )
        return jsonify(music_data)
    except Exception as e:
        return jsonify({'error': '檢查音樂失敗'}), 500
    
    # ==================== 俄羅斯方塊遊戲路由 ====================
@app.route('/games/tetris')
def tetris_game():
    return send_from_directory('static/games/tetris', 'index.html')

# ==================== 個人資料功能擴充（新增）====================
# 功能：個人資料頁、大頭照上傳、bio 編輯
# 需要在 app.py 末尾（if __name__ == '__main__': 之前）貼上此段
# 鄭崇恩
import uuid
from werkzeug.utils import secure_filename

AVATAR_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'avatars')
os.makedirs(AVATAR_FOLDER, exist_ok=True)

ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_avatar_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS

def ensure_profile_columns():
    """確保 users 表有 bio 和 avatar_path 欄位（安全新增，不影響現有資料）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(users)')
    columns = [row[1] for row in cursor.fetchall()]
    if 'bio' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
    if 'avatar_path' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_path TEXT DEFAULT ''")
    conn.commit()
    conn.close()

ensure_profile_columns()


@app.route('/profile', methods=['GET'])
def profile_page():
    """渲染個人資料頁面"""
    user = session.get('user')
    return render_template('profile.html', user=user)


@app.route('/api/profile', methods=['GET'])
def api_get_profile():
    """取得當前登入使用者的個人資料"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify(success=False, message='請先登入'), 401

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT username, email, bio, avatar_path, created_at FROM users WHERE id = ?',
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify(success=False, message='找不到使用者'), 404

    return jsonify(success=True, profile={
        'username': row['username'],
        'email': row['email'],
        'bio': row['bio'] or '',
        'avatar_path': row['avatar_path'] or '',
        'created_at': row['created_at'] or ''
    })


@app.route('/api/profile', methods=['POST'])
def api_update_profile():
    """更新使用者的 username 和 bio"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify(success=False, message='請先登入'), 401

    data = request.get_json() or {}
    new_username = (data.get('username') or '').strip()
    new_bio = (data.get('bio') or '').strip()

    if not new_username:
        return jsonify(success=False, message='使用者名稱不能為空'), 400
    if len(new_username) > 30:
        return jsonify(success=False, message='名稱最多 30 個字元'), 400
    if len(new_bio) > 150:
        return jsonify(success=False, message='自我介紹最多 150 字'), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET username = ?, bio = ? WHERE id = ?',
        (new_username, new_bio, user_id)
    )
    conn.commit()
    conn.close()

    # 同步更新 session 中的名稱
    session['user'] = new_username

    return jsonify(success=True, message='個人資料已更新', username=new_username)


@app.route('/api/profile/avatar', methods=['POST'])
def api_upload_avatar():
    """上傳使用者大頭照"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify(success=False, message='請先登入'), 401

    if 'avatar' not in request.files:
        return jsonify(success=False, message='沒有收到圖片檔案'), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify(success=False, message='未選擇檔案'), 400

    if not allowed_avatar_file(file.filename):
        return jsonify(success=False, message='僅支援 PNG、JPG、GIF、WEBP 格式'), 400

    # 限制檔案大小：最大 3MB
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 3 * 1024 * 1024:
        return jsonify(success=False, message='圖片大小不能超過 3MB'), 400

    # 用 UUID 產生唯一檔名，避免覆蓋或路徑攻擊
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(AVATAR_FOLDER, filename)
    file.save(save_path)

    avatar_url = f"/static/uploads/avatars/{filename}"

    # 更新資料庫
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET avatar_path = ? WHERE id = ?', (avatar_url, user_id))
    conn.commit()
    conn.close()

    return jsonify(success=True, message='大頭照已更新', avatar_path=avatar_url)

# ==================== 個人資料功能擴充結束 ====================

if __name__ == '__main__':
    app.run(debug=True)
# ------------------ 分析路由新增結束 ------------------