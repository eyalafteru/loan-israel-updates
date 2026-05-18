# System Patterns

## מבנה תיקיות
```
project-root/
├── דפים לשינוי/              # דפי תוכן WordPress לעדכון (HTML)
├── מחשבונים חדשים/            # מחשבונים בפיתוח (HTML)
├── מחשבונים מוכנים לעלייה לאוויר/  # מחשבונים מוכנים לפרסום (HTML)
├── פרומטים/                   # הוראות לסוכני AI (MD)
├── פרומטים ישנים/             # פרומטים בארכיון
├── תיקונים לעמודים/           # דוחות תיקונים (MD)
├── שיווק אטומי/               # חומרי שיווק אטומי (MD)
├── docs/                      # תיעוד + memory bank
│   ├── architecture.md
│   └── memory-bank/
├── tools/                     # כלי אוטומציה (hook scripts)
├── .cursor/rules/             # כללי Cursor
├── server.py                  # שרת תצוגה מקדימה
├── run_agent.py               # מריץ סוכן DataLayer
├── סוכן_הטמעת_דאטא_לייר.py   # סוכן DataLayer מלא
├── temp_update_links.py       # עדכון קישורים מ-CSV
├── open_page.py               # פתיחת דף בדפדפן
└── *.bat                      # סקריפטי Windows
```

## תבנית מחשבון HTML
כל מחשבון הוא קובץ HTML עצמאי שמכיל:
- CSS embedded (בתוך `<style>`)
- JavaScript embedded (בתוך `<script>`)
- קוד חישוב + UI
- כפתורי copy: `data-action="copy-embed-code"` ו-`data-action="copy-preview-code"`
- `CALCULATOR_NAME` const לזיהוי
- `dataLayer.push` לאירועי copy (מוזרק ע"י סוכן DataLayer)

## מחזור חיים של מחשבון
1. נוצר ב-`מחשבונים חדשים/`
2. עובר QA (פרומט סוכן QA)
3. עובר SEO audit (פרומט סוכן SEO)
4. מקבל DataLayer injection (סוכן DataLayer)
5. עובר ל-`מחשבונים מוכנים לעלייה לאוויר/`
6. מועתק ידנית ל-WordPress

## מחזור חיים של דף תוכן
1. HTML מקורי ב-`דפים לשינוי/`
2. עובר שכתוב שיווקי (שיווק אטומי)
3. עובר QA
4. מועתק ל-WordPress

## פרומטים לסוכני AI
תיקיית `פרומטים/` מכילה הוראות מפורטות ל:
- **סוכן AI — בניית עמודי מחשבון** — יצירת מחשבונים חדשים
- **סוכן QA אזור הטמעה** — בדיקת אזור embed
- **סוכן QA לפלט** — בדיקת HTML output
- **סוכן SEO Auditor** — ביקורת SEO
- **סוכן הטמעת DataLayer** — הוראות להטמעת tracking
- **סוכן מתקן SEO** — תיקוני SEO
- **סוכן מתקן שיווק אטומי** — תיקוני תוכן שיווקי

## Conventions
- שמות קבצים בעברית
- כל HTML הוא UTF-8
- מחשבונים — self-contained (אין תלויות חיצוניות)
- DataLayer events — תמיד `copy_code_click` עם `calculator_name` ו-`button_type`
