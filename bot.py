# -*- coding: utf-8 -*-

import logging
import sqlite3
import json
import os
import asyncio
from datetime import datetime
import shutil
import pandas as pd
from bandit.core import config as bandit_config
from bandit.core import manager as bandit_manager
from googleapiclient.discovery import build
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
ContextTypes,
ConversationHandler,
filters,
)
from telegram.constants import ParseMode

# — ✅ الإعدادات الأساسية —

TELEGRAM_TOKEN = ‘8441468702:AAG7a6mpJpPcUkGB8wng26kkmSIMQKytJ10’
OPENAI_API_KEY = ‘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’
GEMINI_API_KEY = ‘AIzaSyBRM8KrqUAhDJlQWs_zoV95e1-hfLuTAlY’
GOOGLE_API_KEY = ‘AIzaSyCotgvCY3cXSPrYf5NvC5HuNMzSd0IXMc4’
CSE_ID = ‘96bf47cbbf6114d21’
DEVELOPER_ID = 69145166
DEVELOPER_USER = ‘aa3a3’

# — إعدادات نماذج الذكاء الاصطناعي —

OPENAI_BASE_URL = “https://api.openai.com/v1”
OPENAI_MODEL_NAME = “gpt-4o”

# — إعداد السجلات —

logging.basicConfig(
format=’%(asctime)s | %(levelname)s | %(message)s’,
level=logging.INFO,
handlers=[
logging.FileHandler(‘bot.log’, encoding=‘utf-8’),
logging.StreamHandler(),
],
)
logger = logging.getLogger(**name**)

# — حالات المحادثة —

(WAIT_ACT_ID, WAIT_DEACT_ID, WAIT_CODE_EXPLAIN, WAIT_CODE_AUDIT,
WAIT_DOCS_SEARCH, WAIT_DATA_CONVERT_FILE, WAIT_PROJECT_PROMPT) = range(7)

# — لغات البرمجة المدعومة —

PROGRAMMING_LANGS = [
‘Python’, ‘JavaScript’, ‘TypeScript’, ‘Java’, ‘C++’, ‘C#’,
‘Go’, ‘Rust’, ‘PHP’, ‘Swift’, ‘Kotlin’, ‘Dart’, ‘SQL’, ‘HTML/CSS’
]

# — نصوص الواجهة —

STRINGS = {
‘ar’: {
‘start’: ‘⌯ مرحبًا بك، أنا مساعدك البرمجي الشخصي.\n\nاختر إحدى الخدمات من القائمة أدناه أو أرسل طلبك مباشرة.’,
‘not_activated’: ‘⌯ عذرًا، هذا البوت مدفوع.\nللتفعيل، يرجى مراسلة المطور.’,
‘choose_lang’: ‘‹ اختر لغة البرمجة التي تعمل عليها حاليًا:’,
‘lang_set’: ‘⌯ تم تحديد لغة البرمجة إلى: {lang}\n\n⌯ الآن، يمكنك إرسال طلبك.’,
‘interface_lang_ar’: ‘🇸🇾 العربية’,
‘interface_lang_en’: ‘🇺🇸 English’,
‘dev_btn’: ‘المطور 👨🏻‍💻’,
‘clear_btn’: ‘‹ مسح المحادثة’,
‘current_btn’: ‘‹ حالتي’,
‘ideas_btn’: ‘‹ أفكار مشاريع’,
‘back_btn’: ‘‹ رجوع’,
‘thinking’: ‘⌯ جاري المعالجة، يرجى الانتظار…’,
‘error_ai’: ‘⌯ حدث خطأ في الاتصال بخدمات الذكاء الاصطناعي.\nيرجى المحاولة مرة أخرى.’,
‘admin_panel’: ‘⌯ لوحة تحكم المطور’,
‘stats_btn’: ‘‹ الإحصائيات’,
‘activate_btn’: ‘‹ تفعيل مستخدم’,
‘deactivate_btn’: ‘‹ إلغاء تفعيل’,
‘stats_text’: ‘⌯ إحصائيات البوت\n\n- إجمالي المستخدمين: {total}\n- المستخدمون المفعلون: {active}\n- النشطون اليوم: {today}’,
‘enter_id’: ‘⌯ أرسل ID المستخدم:’,
‘success_act’: ‘⌯ تم تفعيل المستخدم {uid} بنجاح.’,
‘success_deact’: ‘⌯ تم إلغاء تفعيل المستخدم {uid} بنجاح.’,
‘fail_act’: ‘⌯ فشل التفعيل، تأكد من صحة الـ ID.’,
‘cancel’: ‘⌯ تم الإلغاء.’,
‘features_btn’: ‘‹ قائمة الميزات’,
‘features_text’: ‘اختر إحدى الميزات المتقدمة:’,
‘explain_code_btn’: ‘شرح كود’,
‘audit_code_btn’: ‘فحص أمني للكود’,
‘scaffold_project_btn’: ‘إنشاء مشروع (ZIP)’,
‘search_docs_btn’: ‘بحث في التوثيق’,
‘convert_data_btn’: ‘تحويل صيغ البيانات’,
‘save_snippet_btn’: ‘حفظ الكود’,
‘view_snippets_btn’: ‘أكوادي المحفوظة’,
‘prompt_explain_code’: ‘⌯ أرسل الآن الكود الذي تريد شرحه.’,
‘prompt_audit_code’: ‘⌯ أرسل الآن كود بايثون الذي تريد فحصه أمنيًا.’,
‘prompt_scaffold’: ‘⌯ اكتب وصفًا للمشروع الذي تريد إنشاءه.’,
‘prompt_search_docs’: ‘⌯ اكتب استعلام البحث.’,
‘prompt_convert_data’: ‘⌯ أرسل ملف JSON لتحويله إلى Excel.’,
‘snippet_saved’: ‘⌯ تم حفظ الكود بنجاح!’,
‘no_snippets’: ‘⌯ لا يوجد لديك أكواد محفوظة.’,
‘snippet_deleted’: ‘⌯ تم حذف الكود المحفوظ.’,
‘delete_btn’: ‘حذف’,
‘project_generating’: ‘⌯ جاري إنشاء ملفات المشروع وضغطها…’,
‘project_ready’: ‘⌯ مشروعك جاهز للتحميل.’,
‘audit_results’: ‘⌯ نتائج الفحص الأمني للكود:’,
‘no_issues_found’: ‘لم يتم العثور على مشاكل أمنية عالية الخطورة.’,
‘docs_results’: ‘⌯ أفضل 3 نتائج من التوثيق الرسمي:’,
‘conversion_done’: ‘⌯ تم تحويل الملف بنجاح.’,
‘conversion_fail’: ‘⌯ فشل التحويل. تأكد من أن الملف بصيغة JSON صحيحة.’,
‘send_code_to_save’: ‘⌯ أرسل الكود الذي تريد حفظه.’,
},
‘en’: {
‘start’: ‘⌯ Welcome! I am your personal programming assistant.\n\nChoose a service from the menu below or send your request directly.’,
‘not_activated’: ‘⌯ Sorry, this bot is paid.\nTo activate, please contact the developer.’,
‘choose_lang’: ‘‹ Choose your current programming language:’,
‘lang_set’: ‘⌯ Programming language set to: {lang}\n\n⌯ Now you can send your request.’,
‘interface_lang_ar’: ‘🇸🇾 العربية’,
‘interface_lang_en’: ‘🇺🇸 English’,
‘dev_btn’: ‘Developer 👨🏻‍💻’,
‘clear_btn’: ‘‹ Clear Chat’,
‘current_btn’: ‘‹ My Status’,
‘ideas_btn’: ‘‹ Project Ideas’,
‘back_btn’: ‘‹ Back’,
‘thinking’: ‘⌯ Processing, please wait…’,
‘error_ai’: ‘⌯ An error occurred connecting to AI services.\nPlease try again.’,
‘admin_panel’: ‘⌯ Developer Panel’,
‘stats_btn’: ‘‹ Statistics’,
‘activate_btn’: ‘‹ Activate User’,
‘deactivate_btn’: ‘‹ Deactivate User’,
‘stats_text’: ‘⌯ Bot Statistics\n\n- Total Users: {total}\n- Active Users: {active}\n- Active Today: {today}’,
‘enter_id’: ‘⌯ Send the User ID:’,
‘success_act’: ‘⌯ User {uid} activated successfully.’,
‘success_deact’: ‘⌯ User {uid} deactivated successfully.’,
‘fail_act’: ‘⌯ Activation failed. Check the ID.’,
‘cancel’: ‘⌯ Cancelled.’,
‘features_btn’: ‘‹ Features’,
‘features_text’: ‘Choose an advanced feature:’,
‘explain_code_btn’: ‘Explain Code’,
‘audit_code_btn’: ‘Security Audit’,
‘scaffold_project_btn’: ‘Create Project (ZIP)’,
‘search_docs_btn’: ‘Search Docs’,
‘convert_data_btn’: ‘Convert Data’,
‘save_snippet_btn’: ‘Save Snippet’,
‘view_snippets_btn’: ‘My Snippets’,
‘prompt_explain_code’: ‘⌯ Send the code you want explained.’,
‘prompt_audit_code’: ‘⌯ Send the Python code to audit.’,
‘prompt_scaffold’: ‘⌯ Describe the project you want to create.’,
‘prompt_search_docs’: ‘⌯ Write your search query.’,
‘prompt_convert_data’: ‘⌯ Send a JSON file to convert to Excel.’,
‘snippet_saved’: ‘⌯ Snippet saved successfully!’,
‘no_snippets’: ‘⌯ You have no saved snippets.’,
‘snippet_deleted’: ‘⌯ Snippet deleted.’,
‘delete_btn’: ‘Delete’,
‘project_generating’: ‘⌯ Generating project files…’,
‘project_ready’: ‘⌯ Your project is ready to download.’,
‘audit_results’: ‘⌯ Security Audit Results:’,
‘no_issues_found’: ‘No high-severity security issues found.’,
‘docs_results’: ‘⌯ Top 3 results from official documentation:’,
‘conversion_done’: ‘⌯ File converted successfully.’,
‘conversion_fail’: ‘⌯ Conversion failed. Make sure the file is valid JSON.’,
‘send_code_to_save’: ‘⌯ Send the code you want to save.’,
}
}

# — قاعدة البيانات —

def init_db():
with sqlite3.connect(‘bot.db’) as con:
con.executescript(’’’
CREATE TABLE IF NOT EXISTS users (
user_id    INTEGER PRIMARY KEY,
username   TEXT    DEFAULT ‘’,
first_name TEXT    DEFAULT ‘’,
activated  INTEGER DEFAULT 0,
ui_lang    TEXT    DEFAULT ‘ar’,
joined_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
last_seen  TEXT    DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sessions (
user_id  INTEGER PRIMARY KEY,
language TEXT    DEFAULT ‘Python’,
history  TEXT    DEFAULT ‘[]’
);
CREATE TABLE IF NOT EXISTS snippets (
snippet_id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id    INTEGER NOT NULL,
code       TEXT NOT NULL,
saved_at   TEXT DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES users(user_id)
);
‘’’)

def get_con():
con = sqlite3.connect(‘bot.db’)
con.row_factory = sqlite3.Row
return con

def register_user(user_id: int, username: str, first_name: str):
now = datetime.now().isoformat()
with get_con() as con:
con.execute(
‘INSERT OR IGNORE INTO users (user_id,username,first_name,joined_at,last_seen) VALUES(?,?,?,?,?)’,
(user_id, username, first_name, now, now),
)
con.execute(
‘UPDATE users SET username=?,first_name=?,last_seen=CURRENT_TIMESTAMP WHERE user_id=?’,
(username, first_name, user_id),
)

def get_user_lang(user_id: int) -> str:
with get_con() as con:
row = con.execute(‘SELECT ui_lang FROM users WHERE user_id=?’, (user_id,)).fetchone()
return row[‘ui_lang’] if row else ‘ar’

def set_user_lang(user_id: int, lang: str):
with get_con() as con:
con.execute(‘UPDATE users SET ui_lang=? WHERE user_id=?’, (lang, user_id))

def is_activated(user_id: int) -> bool:
if user_id == DEVELOPER_ID:
return True
with get_con() as con:
row = con.execute(‘SELECT activated FROM users WHERE user_id=?’, (user_id,)).fetchone()
return bool(row and row[‘activated’])

def activate_user(user_id: int) -> bool:
with get_con() as con:
cur = con.execute(‘UPDATE users SET activated=1 WHERE user_id=?’, (user_id,))
return cur.rowcount > 0

def deactivate_user(user_id: int) -> bool:
with get_con() as con:
cur = con.execute(‘UPDATE users SET activated=0 WHERE user_id=?’, (user_id,))
return cur.rowcount > 0

def get_stats():
with get_con() as con:
total = con.execute(‘SELECT COUNT(*) FROM users’).fetchone()[0]
active = con.execute(’SELECT COUNT(*) FROM users WHERE activated=1’).fetchone()[0]
today = con.execute(“SELECT COUNT(*) FROM users WHERE DATE(last_seen) = DATE(‘now’, ‘localtime’)”).fetchone()[0]
return total, active, today

def get_session(user_id: int):
with get_con() as con:
row = con.execute(‘SELECT language,history FROM sessions WHERE user_id=?’, (user_id,)).fetchone()
if row:
return row[‘language’], json.loads(row[‘history’])
return ‘Python’, []

def save_session(user_id: int, language: str, history: list):
with get_con() as con:
con.execute(
‘INSERT OR REPLACE INTO sessions (user_id,language,history) VALUES(?,?,?)’,
(user_id, language, json.dumps(history, ensure_ascii=False))
)

def save_snippet(user_id: int, code: str):
with get_con() as con:
con.execute(‘INSERT INTO snippets (user_id, code) VALUES (?, ?)’, (user_id, code))

def get_snippets(user_id: int):
with get_con() as con:
return con.execute(
‘SELECT snippet_id, code FROM snippets WHERE user_id=? ORDER BY saved_at DESC’,
(user_id,)
).fetchall()

def delete_snippet(snippet_id: int, user_id: int):
with get_con() as con:
cur = con.execute(
‘DELETE FROM snippets WHERE snippet_id=? AND user_id=?’,
(snippet_id, user_id)
)
return cur.rowcount > 0

# — الكيبوردات —

def main_keyboard(user_id: int):
lang = get_user_lang(user_id)
s = STRINGS[lang]
return InlineKeyboardMarkup([
[InlineKeyboardButton(s[‘features_btn’], callback_data=‘features’)],
[InlineKeyboardButton(s[‘choose_lang’], callback_data=‘choose_lang’)],
[
InlineKeyboardButton(s[‘clear_btn’], callback_data=‘clear’),
InlineKeyboardButton(s[‘current_btn’], callback_data=‘current_lang’),
],
[InlineKeyboardButton(s[‘ideas_btn’], callback_data=‘ideas’)],
[
InlineKeyboardButton(s[‘interface_lang_ar’], callback_data=‘set_ui_ar’),
InlineKeyboardButton(s[‘interface_lang_en’], callback_data=‘set_ui_en’),
],
[InlineKeyboardButton(s[‘dev_btn’], url=f’tg://user?id={DEVELOPER_ID}’)]
])

def features_keyboard(user_id: int):
lang = get_user_lang(user_id)
s = STRINGS[lang]
return InlineKeyboardMarkup([
[InlineKeyboardButton(s[‘explain_code_btn’], callback_data=‘feature_explain’)],
[InlineKeyboardButton(s[‘audit_code_btn’], callback_data=‘feature_audit’)],
[InlineKeyboardButton(s[‘scaffold_project_btn’], callback_data=‘feature_scaffold’)],
[InlineKeyboardButton(s[‘search_docs_btn’], callback_data=‘feature_docs’)],
[InlineKeyboardButton(s[‘convert_data_btn’], callback_data=‘feature_convert’)],
[InlineKeyboardButton(s[‘view_snippets_btn’], callback_data=‘feature_snippets’)],
[InlineKeyboardButton(s[‘save_snippet_btn’], callback_data=‘feature_save_snippet’)],
[InlineKeyboardButton(s[‘back_btn’], callback_data=‘back_main’)]
])

def lang_keyboard(user_id: int):
lang = get_user_lang(user_id)
s = STRINGS[lang]
rows = [
[InlineKeyboardButton(l, callback_data=‘lang_’ + l) for l in PROGRAMMING_LANGS[i:i+3]]
for i in range(0, len(PROGRAMMING_LANGS), 3)
]
rows.append([InlineKeyboardButton(s[‘back_btn’], callback_data=‘back_main’)])
return InlineKeyboardMarkup(rows)

def admin_keyboard(user_id: int):
lang = get_user_lang(user_id)
s = STRINGS[lang]
return InlineKeyboardMarkup([
[InlineKeyboardButton(s[‘stats_btn’], callback_data=‘admin_stats’)],
[
InlineKeyboardButton(s[‘activate_btn’], callback_data=‘admin_act’),
InlineKeyboardButton(s[‘deactivate_btn’], callback_data=‘admin_deact’),
],
[InlineKeyboardButton(s[‘back_btn’], callback_data=‘back_main’)]
])

# — دالة إرسال الرسائل الطويلة —

async def send_long_message(message, text: str, reply_markup=None):
“”“ترسل رسالة طويلة، وتقسمها إذا تجاوزت 4096 حرفاً.”””
max_len = 4096
if len(text) <= max_len:
try:
await message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
except Exception:
await message.reply_text(text, reply_markup=reply_markup)
else:
parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
for i, part in enumerate(parts):
try:
await message.reply_text(
part,
parse_mode=ParseMode.MARKDOWN,
reply_markup=reply_markup if i == len(parts) - 1 else None
)
except Exception:
await message.reply_text(
part,
reply_markup=reply_markup if i == len(parts) - 1 else None
)

# — الذكاء الاصطناعي مع آلية التبديل —

async def ask_ai(user_id: int, user_message: str, system_prompt_override: str = None) -> str:
ui_lang = get_user_lang(user_id)
prog_lang, history = get_session(user_id)

```
system_prompt = system_prompt_override or (
    f"You are an expert AI programmer. Current programming language: {prog_lang}.\n"
    f"Always reply in {'Arabic' if ui_lang == 'ar' else 'English'}.\n"
    "Provide clean, professional code. Explain each block clearly. Suggest improvements."
)

# محاولة OpenAI أولاً
try:
    logger.info(f"Attempting OpenAI for user {user_id}")
    async with httpx.AsyncClient() as client:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['content']})
        if user_message:
            messages.append({"role": "user", "content": user_message})

        response = await client.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": OPENAI_MODEL_NAME, "messages": messages},
            timeout=60,
        )
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']

    if user_message:
        history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': reply})
    save_session(user_id, prog_lang, history[-10:])
    return reply

except Exception as e:
    logger.error(f"OpenAI failed for user {user_id}: {e}. Trying Gemini.")

# محاولة Gemini كبديل
try:
    logger.info(f"Attempting Gemini for user {user_id}")
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_prompt
    )

    gemini_history = [
        {
            'role': 'user' if msg['role'] == 'user' else 'model',
            'parts': [{'text': msg['content']}]
        }
        for msg in history
    ]
    chat = model.start_chat(history=gemini_history)
    response = await chat.send_message_async(user_message or system_prompt)
    reply = response.text

    if user_message:
        history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': reply})
    save_session(user_id, prog_lang, history[-10:])
    return reply

except Exception as e:
    logger.error(f"Both APIs failed for user {user_id}: {e}")
    return STRINGS[ui_lang]['error_ai']
```

# — معالجات الميزات —

async def handle_code_explanation(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
thinking_msg = await update.message.reply_text(s['thinking'])
prompt = (
    f"اشرح الكود التالي بالتفصيل سطرًا بسطر باللغة العربية المبسطة، "
    f"مع توضيح كل مفهوم:\n\n```\n{update.message.text}\n```"
)
reply = await ask_ai(user_id, "", system_prompt_override=prompt)
await thinking_msg.delete()
await send_long_message(update.message, reply, main_keyboard(user_id))
return ConversationHandler.END
```

async def handle_code_audit(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
code_to_audit = update.message.text
temp_file = f"temp_audit_{user_id}.py"

try:
    b_config = bandit_config.BanditConfig()
    b_mgr = bandit_manager.BanditManager(b_config, "file")

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(code_to_audit)

    b_mgr.discover_files([temp_file])
    b_mgr.run_tests()

    # استخدام HIGH/MEDIUM/LOW بدل logging constants
    from bandit.core.constants import HIGH, MEDIUM, LOW
    results = b_mgr.get_issue_list(sev_level=LOW, conf_level=LOW)

    if not results:
        reply = f"**{s['audit_results']}**\n\n✅ {s['no_issues_found']}"
    else:
        reply = f"**{s['audit_results']}**\n\n"
        for issue in results:
            reply += (
                f"⚠️ **المشكلة:** {issue.text}\n"
                f"   **الخطورة:** {issue.severity}\n"
                f"   **السطر:** {issue.lineno}\n"
                f"   **الكود:** `{issue.get_code().strip()}`\n\n"
            )

except Exception as e:
    logger.error(f"Audit error: {e}")
    reply = f"حدث خطأ أثناء الفحص: {str(e)}"
finally:
    if os.path.exists(temp_file):
        os.remove(temp_file)

await send_long_message(update.message, reply, main_keyboard(user_id))
return ConversationHandler.END
```

async def handle_project_scaffolding(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
thinking_msg = await update.message.reply_text(s['thinking'])

prompt = (
    f"قم بإنشاء هيكل ملفات لمشروع بناءً على الوصف التالي: '{update.message.text}'.\n"
    "يجب أن تكون الاستجابة بصيغة JSON فقط، بدون أي نص إضافي أو backticks.\n"
    "يجب أن يحتوي الـ JSON على مفتاح 'files' وهو قائمة من الكائنات، "
    "كل كائن يحتوي على 'name' (اسم الملف مع المسار) و 'content' (محتوى الملف).\n"
    'مثال: {"files": [{"name": "index.html", "content": "<h1>Hello</h1>"}]}'
)

project_name = f"project_{user_id}"
zip_path = f"{project_name}.zip"

try:
    response_json_str = await ask_ai(user_id, "", system_prompt_override=prompt)

    # استخراج JSON من الرد
    start = response_json_str.find('{')
    end = response_json_str.rfind('}') + 1
    json_part = response_json_str[start:end]
    file_structure = json.loads(json_part)

    if os.path.exists(project_name):
        shutil.rmtree(project_name)
    os.makedirs(project_name, exist_ok=True)

    for file_info in file_structure.get('files', []):
        file_path = os.path.join(project_name, file_info['name'])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_info.get('content', ''))

    await thinking_msg.edit_text(s['project_generating'])
    shutil.make_archive(project_name, 'zip', project_name)

    with open(zip_path, 'rb') as zf:
        await update.message.reply_document(
            document=zf,
            caption=s['project_ready'],
            reply_markup=main_keyboard(user_id)
        )

except Exception as e:
    logger.error(f"Project scaffolding failed: {e}")
    await thinking_msg.edit_text(s['error_ai'], reply_markup=main_keyboard(user_id))

finally:
    if os.path.exists(zip_path):
        os.remove(zip_path)
    if os.path.exists(project_name):
        shutil.rmtree(project_name)

return ConversationHandler.END
```

async def handle_docs_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
thinking_msg = await update.message.reply_text(s['thinking'])

try:
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    res = service.cse().list(q=update.message.text, cx=CSE_ID, num=3).execute()

    items = res.get('items', [])
    if not items:
        reply = "لم أجد أي نتائج في التوثيق الرسمي."
    else:
        reply = f"**{s['docs_results']}**\n\n"
        for i, item in enumerate(items):
            reply += f"{i+1}. **{item['title']}**\n   [رابط]({item['link']})\n\n"

    await thinking_msg.delete()
    await send_long_message(update.message, reply, main_keyboard(user_id))

except Exception as e:
    logger.error(f"Docs search failed: {e}")
    await thinking_msg.edit_text(
        "حدث خطأ أثناء البحث. تأكد من صحة مفاتيح Google API.",
        reply_markup=main_keyboard(user_id)
    )

return ConversationHandler.END
```

async def handle_data_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
if not update.message.document:
    await update.message.reply_text(s['prompt_convert_data'], reply_markup=main_keyboard(user_id))
    return WAIT_DATA_CONVERT_FILE

thinking_msg = await update.message.reply_text(s['thinking'])

json_path = f"temp_data_{user_id}.json"
excel_path = f"output_{user_id}.xlsx"

try:
    file = await context.bot.get_file(update.message.document.file_id)
    await file.download_to_drive(json_path)

    df = pd.read_json(json_path)
    df.to_excel(excel_path, index=False)

    with open(excel_path, 'rb') as ef:
        await update.message.reply_document(
            document=ef,
            caption=s['conversion_done'],
            reply_markup=main_keyboard(user_id)
        )

    await thinking_msg.delete()

except Exception as e:
    logger.error(f"Data conversion failed: {e}")
    await thinking_msg.edit_text(s['conversion_fail'], reply_markup=main_keyboard(user_id))

finally:
    for f in [json_path, excel_path]:
        if os.path.exists(f):
            os.remove(f)

return ConversationHandler.END
```

async def handle_save_snippet(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
code = update.message.text
save_snippet(user_id, code)
await update.message.reply_text(s['snippet_saved'], reply_markup=main_keyboard(user_id))
return ConversationHandler.END
```

# — معالجات الأوامر —

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
register_user(user.id, user.username or ‘’, user.first_name or ‘’)
lang = get_user_lang(user.id)
s = STRINGS[lang]

```
if not is_activated(user.id):
    await update.message.reply_text(
        s['not_activated'],
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(s['dev_btn'], url=f'tg://user?id={DEVELOPER_ID}')
        ]])
    )
    return

await update.message.reply_text(s['start'], reply_markup=main_keyboard(user.id))
```

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != DEVELOPER_ID:
return
lang = get_user_lang(update.effective_user.id)
s = STRINGS[lang]
await update.message.reply_text(s[‘admin_panel’], reply_markup=admin_keyboard(update.effective_user.id))

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
await update.message.reply_text(STRINGS[lang][‘cancel’], reply_markup=main_keyboard(user_id))
return ConversationHandler.END

# — معالج لوحة الإدارة —

async def handle_admin_act_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
try:
    target_id = int(update.message.text.strip())
    if activate_user(target_id):
        await update.message.reply_text(s['success_act'].format(uid=target_id), reply_markup=admin_keyboard(user_id))
    else:
        await update.message.reply_text(s['fail_act'], reply_markup=admin_keyboard(user_id))
except ValueError:
    await update.message.reply_text(s['fail_act'], reply_markup=admin_keyboard(user_id))

return ConversationHandler.END
```

async def handle_admin_deact_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
try:
    target_id = int(update.message.text.strip())
    if deactivate_user(target_id):
        await update.message.reply_text(s['success_deact'].format(uid=target_id), reply_markup=admin_keyboard(user_id))
    else:
        await update.message.reply_text(s['fail_act'], reply_markup=admin_keyboard(user_id))
except ValueError:
    await update.message.reply_text(s['fail_act'], reply_markup=admin_keyboard(user_id))

return ConversationHandler.END
```

# — معالج الكول باك الرئيسي —

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
user_id = query.from_user.id
data = query.data
lang = get_user_lang(user_id)
s = STRINGS[lang]

```
if data == 'back_main':
    await query.message.edit_text(s['start'], reply_markup=main_keyboard(user_id))

elif data == 'features':
    await query.message.edit_text(s['features_text'], reply_markup=features_keyboard(user_id))

elif data == 'choose_lang':
    await query.message.edit_text(s['choose_lang'], reply_markup=lang_keyboard(user_id))

elif data.startswith('lang_'):
    p_lang = data.replace('lang_', '')
    save_session(user_id, p_lang, get_session(user_id)[1])
    await query.message.edit_text(s['lang_set'].format(lang=p_lang), reply_markup=main_keyboard(user_id))

elif data.startswith('set_ui_'):
    new_lang = data.replace('set_ui_', '')
    if new_lang in STRINGS:
        set_user_lang(user_id, new_lang)
        await query.message.edit_text(STRINGS[new_lang]['start'], reply_markup=main_keyboard(user_id))

elif data == 'clear':
    save_session(user_id, get_session(user_id)[0], [])
    await query.message.edit_text(s['start'], reply_markup=main_keyboard(user_id))

elif data == 'current_lang':
    p_lang, hist = get_session(user_id)
    await query.answer(f"لغة البرمجة: {p_lang}\nطول المحادثة: {len(hist)//2}", show_alert=True)

elif data == 'ideas':
    await query.message.edit_text(s['thinking'])
    p_lang, _ = get_session(user_id)
    reply = await ask_ai(user_id, f"اقترح 5 أفكار مشاريع بسيطة ومبتكرة للغة {p_lang}")
    try:
        await query.message.edit_text(reply, reply_markup=main_keyboard(user_id))
    except Exception:
        await query.message.delete()
        await context.bot.send_message(chat_id=user_id, text=reply, reply_markup=main_keyboard(user_id))

elif data == 'admin_stats':
    if user_id == DEVELOPER_ID:
        total, active, today = get_stats()
        await query.message.edit_text(
            s['stats_text'].format(total=total, active=active, today=today),
            reply_markup=admin_keyboard(user_id)
        )

elif data == 'admin_act':
    if user_id == DEVELOPER_ID:
        await query.message.edit_text(s['enter_id'])
        context.user_data['admin_action'] = 'act'

elif data == 'admin_deact':
    if user_id == DEVELOPER_ID:
        await query.message.edit_text(s['enter_id'])
        context.user_data['admin_action'] = 'deact'

elif data == 'feature_snippets':
    snippets = get_snippets(user_id)
    if not snippets:
        await query.message.edit_text(s['no_snippets'], reply_markup=features_keyboard(user_id))
        return

    buttons = []
    for snippet in snippets:
        code_preview = snippet['code'].strip().split('\n')[0][:30] + '...'
        buttons.append([
            InlineKeyboardButton(code_preview, callback_data=f"snippet_show_{snippet['snippet_id']}"),
            InlineKeyboardButton(s['delete_btn'], callback_data=f"snippet_del_{snippet['snippet_id']}")
        ])
    buttons.append([InlineKeyboardButton(s['back_btn'], callback_data='features')])
    await query.message.edit_text("أكوادك المحفوظة:", reply_markup=InlineKeyboardMarkup(buttons))

elif data.startswith('snippet_show_'):
    snippet_id = int(data.split('_')[2])
    all_snippets = get_snippets(user_id)
    snippet = next((sn for sn in all_snippets if sn['snippet_id'] == snippet_id), None)
    if snippet:
        await send_long_message(query.message, f"```\n{snippet['code']}\n```")

elif data.startswith('snippet_del_'):
    snippet_id = int(data.split('_')[2])
    if delete_snippet(snippet_id, user_id):
        await query.answer(s['snippet_deleted'], show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=user_id,
            text=s['features_text'],
            reply_markup=features_keyboard(user_id)
        )
```

# — معالج الرسائل النصية العام —

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id

```
if not is_activated(user_id):
    lang = get_user_lang(user_id)
    await update.message.reply_text(STRINGS[lang]['not_activated'])
    return

# معالجة إجراءات الأدمن
if user_id == DEVELOPER_ID and 'admin_action' in context.user_data:
    action = context.user_data.pop('admin_action')
    lang = get_user_lang(user_id)
    s = STRINGS[lang]
    try:
        target_id = int(update.message.text.strip())
        if action == 'act':
            success = activate_user(target_id)
            msg = s['success_act'].format(uid=target_id) if success else s['fail_act']
        else:
            success = deactivate_user(target_id)
            msg = s['success_deact'].format(uid=target_id) if success else s['fail_act']
        await update.message.reply_text(msg, reply_markup=admin_keyboard(user_id))
    except ValueError:
        await update.message.reply_text(s['fail_act'], reply_markup=admin_keyboard(user_id))
    return

lang = get_user_lang(user_id)
s = STRINGS[lang]
thinking_msg = await update.message.reply_text(s['thinking'])
reply = await ask_ai(user_id, update.message.text)
await thinking_msg.delete()
await send_long_message(update.message, reply, main_keyboard(user_id))
```

# — دالة التشغيل الرئيسية —

def main():
init_db()
logger.info(“Bot starting…”)

```
app = Application.builder().token(TELEGRAM_TOKEN).build()

# ConversationHandler لميزة شرح الكود
explain_conv = ConversationHandler(
    entry_points=[],  # يُفعَّل من الكول باك
    states={
        WAIT_CODE_EXPLAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_explanation)],
    },
    fallbacks=[CommandHandler('cancel', cmd_cancel)],
)

# ConversationHandler لميزة الفحص الأمني
audit_conv = ConversationHandler(
    entry_points=[],
    states={
        WAIT_CODE_AUDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_audit)],
    },
    fallbacks=[CommandHandler('cancel', cmd_cancel)],
)

# ConversationHandler لإنشاء مشروع
scaffold_conv = ConversationHandler(
    entry_points=[],
    states={
        WAIT_PROJECT_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_scaffolding)],
    },
    fallbacks=[CommandHandler('cancel', cmd_cancel)],
)

# ConversationHandler للبحث في التوثيق
docs_conv = ConversationHandler(
    entry_points=[],
    states={
        WAIT_DOCS_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_docs_search)],
    },
    fallbacks=[CommandHandler('cancel', cmd_cancel)],
)

# ConversationHandler لتحويل البيانات
convert_conv = ConversationHandler(
    entry_points=[],
    states={
        WAIT_DATA_CONVERT_FILE: [MessageHandler(filters.Document.ALL, handle_data_conversion)],
    },
    fallbacks=[CommandHandler('cancel', cmd_cancel)],
)

# ConversationHandler لحفظ الكود
snippet_conv = ConversationHandler(
    entry_points=[],
    states={
        # WAIT_SAVE_SNIPPET يمكن تعريفه لاحقاً إن احتجت
    },
    fallbacks=[CommandHandler('cancel', cmd_cancel)],
)

# ConversationHandler موحد يشمل كل الميزات (عبر callback)
master_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handle_feature_entry, pattern='^feature_(explain|audit|scaffold|docs|convert|save_snippet)$'),
    ],
    states={
        WAIT_CODE_EXPLAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_explanation)],
        WAIT_CODE_AUDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_audit)],
        WAIT_PROJECT_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_scaffolding)],
        WAIT_DOCS_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_docs_search)],
        WAIT_DATA_CONVERT_FILE: [MessageHandler(filters.Document.ALL, handle_data_conversion)],
    },
    fallbacks=[
        CommandHandler('cancel', cmd_cancel),
        CallbackQueryHandler(handle_callback, pattern='^back_main$'),
    ],
    per_message=False,
)

# التسجيل
app.add_handler(CommandHandler('start', cmd_start))
app.add_handler(CommandHandler('admin', cmd_admin))
app.add_handler(CommandHandler('cancel', cmd_cancel))
app.add_handler(master_conv)
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.Document.ALL, handle_data_conversion))

logger.info("Bot is running...")
app.run_polling(drop_pending_updates=True)
```

# — دالة إدخال الميزة من الكول باك —

async def handle_feature_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
user_id = query.from_user.id
lang = get_user_lang(user_id)
s = STRINGS[lang]
feature = query.data.replace(‘feature_’, ‘’)

```
state_map = {
    'explain': (WAIT_CODE_EXPLAIN, s['prompt_explain_code']),
    'audit': (WAIT_CODE_AUDIT, s['prompt_audit_code']),
    'scaffold': (WAIT_PROJECT_PROMPT, s['prompt_scaffold']),
    'docs': (WAIT_DOCS_SEARCH, s['prompt_search_docs']),
    'convert': (WAIT_DATA_CONVERT_FILE, s['prompt_convert_data']),
}

if feature == 'save_snippet':
    await query.message.edit_text(
        s['send_code_to_save'],
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(s['back_btn'], callback_data='features')]])
    )
    context.user_data['waiting_for_snippet'] = True
    return ConversationHandler.END

if feature in state_map:
    state, prompt_text = state_map[feature]
    await query.message.edit_text(
        prompt_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(s['back_btn'], callback_data='features')]])
    )
    return state

return ConversationHandler.END
```

if **name** == ‘**main**’:
main()
