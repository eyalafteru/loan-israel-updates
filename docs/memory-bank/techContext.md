# Tech Context

## Stack
- **Python 3** — standard library only (no requirements.txt / pip packages)
- **HTML + inline JS** — static calculator pages, content pages
- **CSS** — embedded in HTML files
- **Batch scripts (.bat)** — Windows automation

## Key Scripts

### server.py — שרת תצוגה מקדימה
- Python `http.server` על port 8080
- משרת את תיקיית הפרויקט כ-static files
- הפעלה: `python server.py` או `start_server.bat`

### run_agent.py — מריץ סוכן DataLayer
- מפעיל את `DataLayerAgent` על תיקיית מחשבונים מוכנים
- תומך ב-`--dry-run` לבדיקה ללא שינויים
- הפעלה: `py run_agent.py` או `run_datalayer_agent.bat`

### סוכן_הטמעת_דאטא_לייר.py — סוכן DataLayer מלא
- סורק HTML files ומוסיף `dataLayer.push` לכפתורי copy
- מזהה כפתורים: `copy-embed-code`, `copy-preview-code`
- תומך ב-`--folder` לנתיב מותאם

### temp_update_links.py — עדכון קישורים
- קורא מ-CSV (`קישורי ויקי - מילות מפתח.csv`)
- מעדכן לינקים בקבצי HTML

### open_page.py — פתיחת דף בדפדפן
- עוזר לפתוח HTML files לתצוגה מקדימה

## Batch Scripts
- `start_server.bat` — מפעיל שרת תצוגה מקדימה
- `git_commit.bat` — commit מהיר
- `git_pull.bat` — pull מהיר
- `run_datalayer_agent.bat` — מריץ סוכן DataLayer

## Deployment
- **אין deploy אוטומטי** — העתקה ידנית ל-WordPress
- תהליך: עריכה → תצוגה מקדימה (localhost:8080) → QA → copy to WordPress

## DataLayer Pattern
```javascript
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
    'event': 'copy_code_click',
    'calculator_name': 'שם המחשבון',
    'button_type': 'copy-embed-code'
});
```

## Encoding
- כל הקבצים ב-UTF-8
- תמיכה בעברית בשמות קבצים ותיקיות
- Windows-specific encoding handling ב-Python scripts
