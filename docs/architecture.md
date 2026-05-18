# Architecture

## סקירה כללית

הפרויקט הוא workspace מבוסס קבצים סטטיים. אין backend, אין DB, אין framework. כל קובץ HTML הוא יחידה עצמאית.

```
┌─────────────────────────────────────────────┐
│              Workspace (local)               │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ מחשבונים │  │  דפים    │  │  כלי      │  │
│  │  חדשים   │──│ לשינוי   │  │ אוטומציה  │  │
│  └────┬─────┘  └────┬─────┘  └───────────┘  │
│       │QA+SEO       │שיווק אטומי            │
│       ▼             ▼                        │
│  ┌──────────┐  ┌──────────┐                  │
│  │ מוכנים   │  │  פלט     │                  │
│  │ לאוויר   │  │  סופי    │                  │
│  └────┬─────┘  └────┬─────┘                  │
│       │             │                        │
│       └──────┬──────┘                        │
│              │ copy to WP                    │
└──────────────┼───────────────────────────────┘
               ▼
        ┌─────────────┐
        │  WordPress   │
        │ loan-israel  │
        └─────────────┘
```

## תהליכי עבודה

### יצירת מחשבון חדש
1. יצירת HTML ב-`מחשבונים חדשים/` (לפי פרומט "סוכן AI — בניית עמודי מחשבון")
2. הרצת QA (לפי פרומטי "סוכן QA אזור הטמעה" + "סוכן QA לפלט")
3. הרצת SEO audit (לפי פרומט "סוכן SEO Auditor")
4. הרצת סוכן DataLayer: `py run_agent.py --dry-run` ואז `py run_agent.py`
5. העברה ל-`מחשבונים מוכנים לעלייה לאוויר/`
6. העתקת embed code ל-WordPress

### עדכון דף תוכן
1. עריכת HTML ב-`דפים לשינוי/`
2. אודיט שיווק אטומי (לפי "סוכן משכתב תוכן שיווק אטומי")
3. מתקן שיווק אטומי (לפי "סוכן מתקן שיווק אטומי")
4. אודיט SEO (לפי "סוכן SEO Auditor")
5. מתקן SEO (לפי "סוכן מתקן SEO")
6. **בדיקת עובדות** — Gemini (לפי "סוכן בדיקת עובדות (Gemini)") — אימות נתונים מול מקורות סמכות
7. **תאימות וורדפרס** — כיווץ CSS/JS, מבנה WP (לפי "תאימות וורדפרס — הוראות פלט")
8. העתקה ל-WordPress

> **לוג תהליך:** לכל דף שעובר את התהליך נוצר קובץ לוג ב-`לוגים/` (לפי תבנית "לוג תהליך עדכון דף.md"). כל סוכן מעדכן את הלוג בסיום.

### תצוגה מקדימה
```bash
python server.py
# פתיחה: http://localhost:8080
# או: http://localhost:8080/מחשבונים%20חדשים/שם-קובץ.html
```

## מבנה מחשבון HTML

כל מחשבון הוא קובץ HTML עצמאי עם המבנה:

```html
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>שם המחשבון</title>
    <style>
        /* כל ה-CSS embedded */
    </style>
</head>
<body>
    <!-- UI של המחשבון -->
    <div class="calculator-container">
        <!-- שדות קלט -->
        <!-- כפתור חישוב -->
        <!-- אזור תוצאות -->
    </div>

    <!-- אזור הטמעה -->
    <div class="embed-section">
        <button data-action="copy-embed-code" onclick="copyEmbedCode()">העתק קוד הטמעה</button>
        <button data-action="copy-preview-code" onclick="copyPreviewCode()">העתק קוד תצוגה</button>
    </div>

    <script>
        const CALCULATOR_NAME = 'שם המחשבון';

        function copyEmbedCode() {
            // DataLayer push (injected by agent)
            window.dataLayer = window.dataLayer || [];
            window.dataLayer.push({
                'event': 'copy_code_click',
                'calculator_name': CALCULATOR_NAME,
                'button_type': 'copy-embed-code'
            });
            // Copy logic...
        }

        function copyPreviewCode() {
            // DataLayer push (injected by agent)
            // Copy logic...
        }
    </script>
</body>
</html>
```

## כלי אוטומציה

### DataLayer Agent
- קובץ: `run_agent.py` / `סוכן_הטמעת_דאטא_לייר.py`
- מטרה: הזרקת `dataLayer.push` לכל פונקציית copy
- זיהוי: מחפש `data-action="copy-*-code"` ו-`function copy*Code()`
- שמירה: מוסיף קוד בתחילת הפונקציה, לא דורס קיים

### Link Updater
- קובץ: `temp_update_links.py`
- מטרה: עדכון קישורים בקבצי HTML מתוך CSV
- מקור: `קישורי ויקי - מילות מפתח.csv`

### סוכן בדיקת עובדות (Gemini)
- פרומט: `פרומטים/סוכן בדיקת עובדות (Gemini).md`
- מטרה: אימות נתונים עובדתיים (ריביות, תנאים, סכומים) מול מקורות סמכות
- מודל: Gemini (עם גישה לאינטרנט)
- פלט: דוח ב-`תיקונים לעמודים/FactCheck_[שם].md`

### לוג תהליך
- תבנית: `פרומטים/לוג תהליך עדכון דף.md`
- תיקיית לוגים: `לוגים/`
- מטרה: דיבוג ומעקב אחר כל שלב בתהליך עדכון דף
