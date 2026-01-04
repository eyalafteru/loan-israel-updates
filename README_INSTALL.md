# מדריך התקנה - מערכת ניהול אתרים
# Installation Guide - Page Management Dashboard

---

## 🚀 התקנה בלחיצה אחת (הכי פשוט!)

### מה שצריך:
1. קובץ `SETUP.bat` 
2. קובץ `setup_standalone.ps1`

### איך להתקין:
1. הורד את שני הקבצים למחשב החדש
2. לחץ לחיצה ימנית על `SETUP.bat` → **"הפעל כמנהל"**
3. הסקריפט יעשה **הכל אוטומטית**:
   - יתקין Python, Node.js, Git
   - ישכפל את המאגר מ-GitHub
   - יתקין את כל החבילות
   - יגדיר את Claude CLI
   - ייצור קיצור דרך בשולחן העבודה
   - יפעיל את הדשבורד!

---

## 📁 קבצי התקנה

| קובץ | תיאור | שימוש |
|------|-------|-------|
| `SETUP.bat` | נקודת כניסה פשוטה | לחיצה כפולה |
| `setup_standalone.ps1` | המתקין המלא | מופעל ע"י SETUP.bat |
| `install.bat` | מתקין חלופי | אם יש כבר את כל הקבצים |
| `install.ps1` | מתקין מפורט | אפשרויות מתקדמות |

---

## 🔧 התקנה מ-GitHub בלבד

אם יש לך רק את קובץ ה-PowerShell:

### אפשרות 1: הורד והרץ
```powershell
# פתח PowerShell כמנהל והרץ:
Set-ExecutionPolicy Bypass -Scope Process -Force
.\setup_standalone.ps1
```

### אפשרות 2: הרץ ישירות מ-URL
```powershell
# הורד והרץ בפקודה אחת:
irm https://raw.githubusercontent.com/YOUR_USER/loan-israel-updates/main/setup_standalone.ps1 | iex
```

---

## 📋 מה הסקריפט מתקין

### תוכנות (אם חסרות):
- **Python 3.12** - שרת Backend
- **Node.js 20 LTS** - הרצת Claude CLI  
- **Git** - שכפול המאגר

### חבילות Python:
```
flask, flask-cors, requests, pyperclip, markdown,
python-dotenv, psutil, trafilatura, lxml, beautifulsoup4
```

### Claude CLI:
```
npm install -g @anthropic-ai/claude-code
```

---

## 🔄 התהליך המלא

```
┌─────────────────────────────────────────────────────────────┐
│  1. הרץ SETUP.bat כמנהל                                    │
├─────────────────────────────────────────────────────────────┤
│  2. התקנת דרישות מקדימות                                   │
│     ├─ Python 3.12 (winget או הורדה ישירה)               │
│     ├─ Node.js 20 LTS                                      │
│     └─ Git                                                 │
├─────────────────────────────────────────────────────────────┤
│  3. בחירת תיקיית התקנה                                     │
│     ברירת מחדל: C:\loan-dashboard                         │
├─────────────────────────────────────────────────────────────┤
│  4. שכפול מ-GitHub                                         │
│     git clone https://github.com/.../loan-israel-updates  │
├─────────────────────────────────────────────────────────────┤
│  5. התקנת חבילות Python                                    │
│     pip install -r requirements.txt                        │
├─────────────────────────────────────────────────────────────┤
│  6. התקנת Claude CLI                                       │
│     npm install -g @anthropic-ai/claude-code              │
├─────────────────────────────────────────────────────────────┤
│  7. עדכון config.json עם נתיב Claude                       │
├─────────────────────────────────────────────────────────────┤
│  8. יצירת תיקיות tmp, logs                                 │
├─────────────────────────────────────────────────────────────┤
│  9. יצירת קיצור דרך בשולחן העבודה                          │
├─────────────────────────────────────────────────────────────┤
│  10. הפעלת הדשבורד ופתיחת דפדפן                            │
│      http://localhost:5000                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ שינוי הגדרות

### לפני ההתקנה
ערוך את `setup_standalone.ps1` ושנה:

```powershell
$REPO_URL = "https://github.com/YOUR_USER/loan-israel-updates.git"
$INSTALL_DIR = "C:\loan-dashboard"
```

### אחרי ההתקנה
ערוך את `api_config.env`:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

---

## 🔑 הגדרת API Key

1. הרשם ב-[Anthropic Console](https://console.anthropic.com/)
2. צור API Key
3. ערוך `api_config.env` והכנס את המפתח
4. **או** הגדר משתנה סביבה:
   ```cmd
   setx ANTHROPIC_API_KEY "sk-ant-api03-..."
   ```

---

## 🆘 פתרון בעיות

### "הסקריפט לא רץ"
```powershell
# הרץ ב-PowerShell כמנהל:
Set-ExecutionPolicy Bypass -Scope CurrentUser
```

### "Python/Node/Git לא נמצא אחרי התקנה"
- **פתרון:** הפעל מחדש את המחשב
- הסיבה: PATH עדיין לא התעדכן

### "git clone נכשל"
- בדוק חיבור אינטרנט
- בדוק שה-URL נכון
- למאגר פרטי, השתמש ב:
  ```
  https://USERNAME:TOKEN@github.com/USER/REPO.git
  ```

### "Claude CLI לא עובד"
```cmd
# מצא את הנתיב:
where claude

# עדכן ב-config.json:
"command": "C:\\Users\\YOUR_USER\\AppData\\Roaming\\npm\\claude.cmd"
```

### "Port 5000 תפוס"
```cmd
netstat -ano | findstr :5000
taskkill /F /PID <מספר_התהליך>
```

---

## 📂 מבנה לאחר התקנה

```
C:\loan-dashboard\
├── dashboard_server.py     # שרת ראשי
├── dashboard.html          # ממשק משתמש
├── start_dashboard.bat     # הפעלה
├── config.json             # הגדרות
├── api_config.env          # מפתח API
├── agents\                 # סוכני AI
├── פרומטים\               # פרומפטים
├── דפים לשינוי\           # תוכן האתר
├── מאגרי מידע\            # מאגרי ידע
├── js\                     # JavaScript
├── tmp\                    # זמניים
└── logs\                   # לוגים
```

---

## ✅ רשימת בדיקה

- [ ] SETUP.bat הורץ בהצלחה
- [ ] Python מותקן (`python --version`)
- [ ] Node.js מותקן (`node --version`)
- [ ] Git מותקן (`git --version`)
- [ ] המאגר שוכפל ל-C:\loan-dashboard
- [ ] Claude CLI מותקן
- [ ] API key מוגדר
- [ ] הדשבורד עולה ב-http://localhost:5000
- [ ] קיצור דרך נוצר בשולחן העבודה

---

## 📞 תמיכה

1. בדוק את `logs\` לשגיאות
2. בדוק את הקונסול בדפדפן (F12)
3. בדוק את חלון ה-CMD של השרת

---

**גרסה:** 2.0  
**עדכון אחרון:** ינואר 2026
