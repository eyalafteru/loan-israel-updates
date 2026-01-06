# 🤖 מידע לפיתוח AI - מערכת ניהול עמודים

> **קובץ זה מסכם את כל מה ש-AI צריך לדעת כדי להמשיך לפתח את הפרויקט**

---

## 📋 תקציר מנהלים

מערכת זו היא **Dashboard לניהול ועדכון תוכן** לאתרי WordPress עבור loan-israel.co.il.
המערכת מאפשרת הפעלת **סוכני AI (Claude)** על עמודי HTML, ביצוע אופטימיזציית SEO, ועדכון אוטומטי לוורדפרס.

### טכנולוגיות עיקריות
- **Backend:** Python Flask (dashboard_server.py)
- **Frontend:** HTML/CSS/JS בקובץ אחד (dashboard.html)
- **AI:** Claude Code (CLI) + Anthropic API
- **CMS:** WordPress עם JWT Authentication
- **APIs חיצוניות:** Apify (SERP, Autocomplete)

---

## 🗂️ מבנה הפרויקט

```
📁 loan-israel-updates/
├── 📄 dashboard_server.py    # ← השרת הראשי (Flask) ~12,000 שורות
├── 📄 dashboard.html         # ← הממשק הגרפי (HTML/JS/CSS) ~20,000 שורות
├── 📄 config.json           # ← הגדרות מערכת, אתרים, נתיבים
├── 📁 agents/               # ← הגדרות סוכנים (JSON)
│   ├── seo.json
│   ├── atomic_marketing.json
│   └── business_loans_content.json
├── 📁 פרומטים/              # ← קבצי הוראות לסוכנים (Markdown)
│   ├── SEO/שלב 1-6.md
│   ├── אטומי/שלב 1-4.md
│   └── הלוואות לעסקים/
├── 📁 דפים לשינוי/          # ← העמודים לעריכה
│   ├── main/               # אתר ראשי
│   └── business/           # אתר עסקים
├── 📁 מאגרי מידע/           # ← מקורות מידע לשורטקודים
├── 📄 requirements.txt
└── 📄 start_dashboard.bat   # ← הרצת המערכת
```

> ⚠️ **אל תתייחס לתיקיית `v2/`** - זו גרסה חדשה בפיתוח

---

## 🚀 הרצת המערכת

```bash
# הרצה רגילה (לוקח פורט 5000)
python dashboard_server.py

# או דרך הבאטץ'
start_dashboard.bat
```

**גישה:** `http://localhost:5000`

---

## 🏗️ ארכיטקטורה

### 1. Backend - dashboard_server.py

שרת Flask עם ~120 endpoints. החלוקה העיקרית:

| קבוצה | Endpoints | תפקיד |
|-------|-----------|--------|
| `/api/pages` | GET/POST | ניהול עמודים |
| `/api/agents` | CRUD | ניהול סוכנים |
| `/api/workflow/step<N>` | POST | הרצת שלבי סוכנים |
| `/api/wordpress/*` | GET/POST | אינטגרציה עם WP |
| `/api/seo/*` | POST | כלי SEO (SERP, מתחרים) |
| `/api/git/*` | GET/POST | סנכרון Git |

### 2. Frontend - dashboard.html

קובץ אחד ענק עם:
- **CSS:** משתני עיצוב ב-`:root`, עיצוב כהה (dark mode)
- **HTML:** תבניות לטאבים שונים (עמודים, סוכנים, הגדרות)
- **JavaScript:** פונקציות API, ניהול מצב, אירועים

**טאבים עיקריים:**
1. ניהול עמודים - בחירה והפעלת סוכנים
2. בונה סוכנים - יצירה/עריכת סוכנים
3. הגדרות - WordPress, Git, מקורות מידע

---

## 🤖 מערכת הסוכנים

### מהו סוכן?

סוכן = סט של **שלבים** שמופעלים ברצף על עמוד.
כל שלב מריץ **Claude Code** עם פרומפט ספציפי.

### מבנה סוכן (JSON)

```json
{
  "id": "seo",
  "name": "SEO Audit",
  "type": "update",           // update / analyze / create
  "status": "active",         // active / test / disabled
  "folder_name": "SEO",       // תיקייה לשמירת דוחות
  "model": {
    "provider": "claude",
    "name": "claude-sonnet-4"
  },
  "steps": [
    {
      "id": "step1",
      "name": "בדיקת תוכן",
      "order": 1,
      "prompt_file": "פרומטים/SEO/שלב 1.md",
      "prompt_template": "...",
      "shortcodes": ["PAGE_HTML", "PAGE_KEYWORD"],
      "output": {
        "path": "דוח שלב 1.md",
        "shortcode_name": "STEP1_REPORT"
      }
    }
  ],
  "wordpress": {
    "action": "update",
    "site": "main"
  }
}
```

### סוכנים קיימים

| סוכן | שלבים | תפקיד |
|------|-------|--------|
| `seo` | 6 | בדיקת SEO, תיקון מבנה, הסרת AI |
| `atomic_marketing` | 4 | שיווק אטומי: דוח → QA → תיקון → דיבאג |
| `business_loans_content` | 6 | תוכן לאתר עסקים |

---

## 🏷️ מערכת השורטקודים

שורטקודים = **placeholders דינמיים** שמוחלפים בערכים אמיתיים לפני שליחה לקלוד.

### שורטקודים לעמוד
| שורטקוד | תיאור |
|----------|---------|
| `{{PAGE_HTML}}` | תוכן ה-HTML של העמוד |
| `{{PAGE_PATH}}` | נתיב מלא לקובץ |
| `{{PAGE_KEYWORD}}` | מילת מפתח ראשית |
| `{{PAGE_URL}}` | כתובת העמוד |

### שורטקודים גלובליים
| שורטקוד | תיאור |
|----------|---------|
| `{{TODAY_DATE}}` | תאריך נוכחי |
| `{{BOI_INTEREST_RATE}}` | ריבית בנק ישראל |
| `{{INTERNAL_LINKS_DB}}` | מאגר קישורים פנימיים |

### שורטקודים לשלבים
| שורטקוד | תיאור |
|----------|---------|
| `{{STEP1_REPORT}}` | דוח משלב 1 (לשימוש בשלבים הבאים) |
| `{{STEP1_PROMPT_FILE}}` | נתיב לקובץ הוראות של שלב 1 |
| `{{OUTPUT_PATH}}` | נתיב לשמירת הפלט |

### הגדרת מקורות מידע חדשים

ב-`config.json` תחת `custom_data_sources`:

```json
{
  "id": "internal_links",
  "name": "קישורים פנימיים",
  "shortcode": "INTERNAL_LINKS_DB",
  "path": "דטה בייס לקישורים פנימיים.txt",
  "type": "text"
}
```

---

## 📁 מבנה עמוד

כל עמוד נמצא בתיקייה נפרדת עם:

```
📁 הלוואה דיגיטלית/
├── 📄 הלוואה דיגיטלית.html     # העמוד עצמו
├── 📄 page_info.json           # מטא-דאטה
├── 📄 *_backup.html            # גיבוי לפני עריכה
├── 📁 SEO/                     # דוחות סוכן SEO
│   ├── דוח שלב 1.md
│   └── דוח שלב 2.md
└── 📁 שיווק אטומי/             # דוחות סוכן אטומי
```

### page_info.json

```json
{
  "keyword": "הלוואה דיגיטלית",
  "url": "https://loan-israel.co.il/הלוואה-דיגיטלית/",
  "wordpress_id": 1234,
  "site": "main",
  "fetched_keywords": {
    "autocomplete": ["הלוואה דיגיטלית מהירה", ...],
    "related": [...],
    "serp": {...}
  }
}
```

---

## 🔌 WordPress Integration

### אתרים מוגדרים

| מזהה | שם | כתובת |
|------|-----|--------|
| `main` | אתר ראשי | loan-israel.co.il |
| `business` | עסקים | loan-israel.co.il/Business |

### אותנטיקציה
- **סוג:** JWT (JSON Web Token)
- **Endpoint:** `/wp-json/jwt-auth/v1/token`
- הטוקנים נשמרים בזיכרון (`jwt_tokens` dict)

### פעולות נתמכות
- `fetch` - משיכת עמוד מ-WP (שמירה כ-HTML)
- `update` - עדכון תוכן עמוד קיים
- `create` - יצירת עמוד חדש

---

## 🔧 APIs חשובות (לפיתוח)

### הרצת סוכן

```javascript
// הרצת שלב בודד
POST /api/workflow/step/1
{
  "page_path": "דפים לשינוי/main/הלוואה/הלוואה.html",
  "agent_id": "seo",
  "model": "claude-sonnet-4"
}

// הרצה אוטומטית (כל השלבים)
POST /api/workflow/single
{
  "page_path": "...",
  "agent_id": "seo",
  "full_auto": true
}
```

### ניהול סוכנים

```javascript
GET  /api/agents                    // רשימת סוכנים
GET  /api/agents/<agent_id>         // סוכן ספציפי
POST /api/agents                    // יצירת סוכן
PUT  /api/agents/<agent_id>         // עדכון סוכן
DELETE /api/agents/<agent_id>       // מחיקת סוכן
```

### פעולות WordPress

```javascript
POST /api/wordpress/fetch
{ "url": "https://...", "site": "main" }

POST /api/wordpress/update
{ "page_path": "...", "site": "main" }
```

---

## 💡 טיפים לפיתוח

### 1. הוספת Endpoint חדש

ב-`dashboard_server.py`:

```python
@app.route('/api/my-endpoint', methods=['POST'])
def my_endpoint():
    data = request.get_json()
    # לוגיקה
    return jsonify({"success": True, "result": ...})
```

### 2. הוספת פונקציונליות ב-Frontend

ב-`dashboard.html`, פונקציות JavaScript:

```javascript
async function myFunction() {
    const result = await apiCall('/api/my-endpoint', {
        method: 'POST',
        body: JSON.stringify({ key: value })
    });
    
    if (result.success) {
        showToast('הצלחה!', 'success');
    }
}
```

### 3. יצירת סוכן חדש

1. צור קובץ `agents/my_agent.json`
2. צור תיקייה `פרומטים/my_agent/` עם קבצי `.md` לכל שלב
3. הסוכן יופיע אוטומטית בממשק

### 4. הוספת שורטקוד

ב-`dashboard_server.py`, בתוך `ShortcodeEngine`:

```python
# בתוך get_shortcode_value()
elif shortcode_name == "MY_SHORTCODE":
    return "הערך שלי"
```

---

## 🔄 זרימת עבודה טיפוסית

```
1. בחירת עמוד מהרשימה
       ↓
2. בחירת סוכן (SEO / אטומי / אחר)
       ↓
3. הרצת שלב 1 (ניתוח / דוח)
       ↓
4. הרצת שלבים 2-N (תיקונים)
       ↓
5. בדיקת תוצאות (Preview)
       ↓
6. עדכון ל-WordPress
```

---

## ⚙️ קבצי הגדרות

| קובץ | תפקיד |
|------|--------|
| `config.json` | הגדרות מערכת, אתרים, נתיבים |
| `api_config.env` | מפתחות API (Anthropic, Apify) |
| `full_auto_jobs.json` | עבודות אוטומציה מתוזמנות |
| `running_jobs.json` | עבודות רצות כרגע |

---

## 🐛 Debugging

### Logs
- טרמינל - כל הפעולות מודפסות עם `[Prefix]`
- `logs/` - קבצי לוג (אם קיימים)
- `*_debug.log` - קבצי דיבאג ספציפיים

### בדיקת Claude
```bash
# בדיקה שקלוד זמין
where claude

# הרצה ידנית
claude --model sonnet --print "test"
```

---

## 📝 הערות חשובות

1. **הקבצים גדולים** - השרת ~12K שורות, הפרונט ~20K שורות
2. **עברית** - שמות קבצים ותיקיות בעברית, זה תקין
3. **Encoding** - תמיד UTF-8 עם BOM (`utf-8-sig` לקריאה)
4. **Windows** - הפרויקט רץ על Windows, נתיבים עם `\`

---

## 🔗 קישורים שימושיים

- **Claude Code CLI:** https://docs.anthropic.com/en/docs/claude-code
- **Flask Docs:** https://flask.palletsprojects.com/
- **WordPress REST API:** https://developer.wordpress.org/rest-api/

---

*עודכן לאחרונה: ינואר 2026*
