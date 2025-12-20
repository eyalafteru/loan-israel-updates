# 🤖 סוכן AI לבניית עמודי מחשבון פיננסי - איפיון מלא

## 📋 תיאור הסוכן

סוכן AI שמקבל **נושא של מחשבון פיננסי** ובונה **עמוד HTML מלא ומוכן לוורדפרס** מאפס, כולל:
- מחשבון אינטראקטיבי עם טאבים
- אזור AWG (טופס בדיקת זכאות)
- מערכת הטמעה מלאה עם תצוגה מקדימה
- תוכן SEO איכותי
- Schema.org מלא
- עיצוב רספונסיבי לכל המכשירים

### 📂 תיקיית פיתוח:
```
C:\Users\eyal\loan-israel-updaets\loan-israel-updates\מחשבונים חדשים\
```
**כל המחשבונים החדשים נוצרים בתיקייה זו!**

---

## 🎯 קלט הסוכן

הסוכן מקבל את הפרמטרים הבאים:

| פרמטר | חובה | תיאור | דוגמה |
|-------|------|-------|--------|
| `topic` | ✅ | נושא המחשבון | "הלוואות", "ריבית דריבית", "חיסכון" |
| `topic_english` | ✅ | נושא באנגלית לprefix | "loans", "compound-int", "savings" |
| `main_title` | ✅ | כותרת H1 ראשית | "מחשבון הלוואות מתקדם" |
| `tabs` | ✅ | מערך של טאבים (2-5 טאבים) | ראה מבנה למטה |
| `awg_post_id` | ✅ | מזהה הטופס AWG | "32400" |
| `prime_rate` | ❌ | ריבית פריים עדכנית | "5.75%" |
| `boi_rate` | ❌ | ריבית בנק ישראל | "4.25%" |
| `faq_items` | ✅ | מערך שאלות ותשובות (5-10) | ראה מבנה למטה |

### מבנה טאב:
```json
{
  "id": "basic",
  "icon": "🧮",
  "name": "חישוב בסיסי",
  "title": "חישוב תשלום חודשי להלוואה",
  "inputs": [
    {
      "type": "slider",
      "id": "loan-amount",
      "label": "סכום הלוואה (₪)",
      "min": 10000,
      "max": 500000,
      "default": 100000,
      "step": 5000,
      "format": "currency"
    },
    {
      "type": "button-group",
      "id": "period",
      "label": "תקופה (שנים)",
      "options": [1, 3, 5, 10, 15, 20],
      "default": 5
    }
  ],
  "outputs": [
    {
      "id": "monthly-payment",
      "label": "תשלום חודשי",
      "format": "currency"
    }
  ],
  "formula": "PMT" // או "FV", "PV", "compound", "custom"
}
```

### מבנה FAQ:
```json
{
  "question": "כמה זמן לוקח לקבל הלוואה?",
  "answer": "בדרך כלל בין 24-72 שעות...",
  "icon": "⏰"
}
```

---

## 🏗️ מבנה הפלט - עמוד HTML מלא

### 1. התחלה חובה (בלי DOCTYPE/HTML/HEAD/BODY!)

```html
<script>
// בדיקה והוספת viewport meta tag אם חסר
if (!document.querySelector('meta[name="viewport"]')) {
  const viewport = document.createElement('meta');
  viewport.name = 'viewport';
  viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=yes';
  document.head.appendChild(viewport);
}
</script>

<style>
/* === CSS Variables + Base Styles === */
/* PREFIX חובה: wpc-calc-[topic]-[4random]- */
</style>
```

### 2. מבנה HTML ראשי

```
├── Wrapper ראשי (.wpc-calc-[topic]-[random]-wrapper)
│   ├── Container (.wpc-calc-[topic]-[random]-container)
│   │   ├── Title Container
│   │   │   ├── H1 כותרת ראשית
│   │   │   ├── תאריך עדכון [current_date]
│   │   │   └── מידע ריבית (אם רלוונטי)
│   │   └── Calculator Wrapper
│   │       ├── Navigation Tabs (2-5 טאבים)
│   │       └── Content Panels (לכל טאב)
│   │
│   ├── AWG Section (אזור בדיקת זכאות)
│   │   └── כפתור CTA + כפתור הטמעה
│   │       └── AWG Content (נסתר עד לחיצה)
│   │           └── [awg postid="XXXXX"]
│   │
│   ├── Content Section (תוכן SEO)
│   │   ├── כותרת משנית
│   │   ├── הסברים על כל טאב
│   │   ├── טיפים ודוגמאות
│   │   └── מידע נוסף רלוונטי
│   │
│   ├── Embed Section (מערכת הטמעה)
│   │   ├── הוראות הטמעה
│   │   ├── כפתור העתקת קוד HTML
│   │   ├── בורר צבעים (10 עיגולים ללא טקסט + color picker)
│   │   ├── תצוגה מקדימה דינמית
│   │   ├── כפתור העתקה עם צבע
│   │   └── תנאי שימוש
│   │
│   └── FAQ Section (שאלות נפוצות)
│       └── Accordion Items (5-10 שאלות)
│
└── Schema.org Scripts (JSON-LD)
    ├── FAQPage
    ├── FinancialProduct
    └── HowTo
```

---

## 🎨 דרישות CSS חובה

### Prefix ייחודי
```css
/* כל הקלאסים חייבים להתחיל ב: */
.wpc-calc-[topic]-[4random]-wrapper { }
.wpc-calc-[topic]-[4random]-container { }
.wpc-calc-[topic]-[4random]-title { }
/* וכו' */
```

### CSS Variables חובה
```css
:root {
  --primary: #1e5490;
  --primary-dark: #2a5fa0;
  --danger: #ff3b3b;
  --success: #25D366;
  --warning: #FF9800;
  --text-dark: #222222;
  --text-light: #444444;
  --bg-light: #f5f5f5;
  --white: #ffffff;
  --border: #999999;
  --max-width-container: 1200px;
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-md: 0 5px 20px rgba(0,0,0,0.1);
  --radius-sm: 8px;
  --radius-md: 15px;
  --radius-lg: 20px;
  --transition: all 0.3s ease;
  --gradient-primary: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
}
```

### Media Queries חובה
```css
/* Desktop - ברירת מחדל */
.wpc-calc-[topic]-[random]-wrapper { }

/* Tablet */
@media (max-width: 768px) { }

/* Mobile */
@media (max-width: 480px) { }

/* Small Mobile */
@media (max-width: 375px) { }
```

### כללים קריטיים
- ✅ כל מאפיין עם `!important`
- ✅ `all: initial` על ה-wrapper
- ✅ `direction: rtl` על ה-wrapper
- ✅ `font-family: 'Assistant', sans-serif`
- ✅ `box-sizing: border-box` על כל האלמנטים
- ✅ מניעת Dark Mode עם `color-scheme: light`

### טאבים - ללא סקרול אופקי!
**חשוב:** הטאבים חייבים להשתמש ב-`flex-wrap: wrap` ולא ב-`overflow-x: auto`:

```css
/* ניווט טאבים - ללא סקרול! */
.wpc-calc-[topic]-[random]-tabs-nav {
  display: flex !important;
  flex-wrap: wrap !important; /* עובר לשורה חדשה במקום סקרול */
  background: var(--bg-light) !important;
  border-bottom: 2px solid var(--border) !important;
  /* ❌ אין overflow-x: auto! */
}

.wpc-calc-[topic]-[random]-tab-btn {
  flex: 1 1 auto !important;
  min-width: 100px !important;
  /* ... */
}

/* מובייל - 2x2 grid */
@media (max-width: 768px) {
  .wpc-calc-[topic]-[random]-tab-btn {
    flex: 1 1 45% !important; /* 2 טאבים בשורה */
    min-width: auto !important;
  }
}
```

---

## ⚡ דרישות JavaScript חובה

### מבנה IIFE בטוח
```javascript
(function() {
    'use strict';
    
    // 1. בדיקת namespace
    const NS = 'WPC_Calc[Topic]_[Random]';
    if (window[NS]) return;
    
    // 2. Container validation
    const container = document.getElementById('wpc-calc-[topic]-[random]-main');
    if (!container) return;
    
    // 3. CSS Variables for color manipulation
    const PRIMARY_COLOR = '#1e5490';
    
    // 4. Utility functions
    function formatCurrency(num) {
        return '₪' + num.toLocaleString('he-IL');
    }
    
    function darkenColor(color, amount = 15) {
        // לוגיקה להכהות צבע
    }
    
    // 5. Financial formulas
    function calculatePMT(principal, rate, periods) {
        // נוסחת PMT להלוואות
    }
    
    function calculateFV(principal, rate, periods, monthlyDeposit) {
        // נוסחת Future Value
    }
    
    // 6. Calculation functions per tab
    function calculateTab1() { }
    function calculateTab2() { }
    
    // 7. Tab switching
    function switchTab(tabName) { }
    
    // 8. Embed functions
    function scrollToEmbed() { }
    function copyEmbedCode() { }
    function copyEmbedCodeWithColor(color) { }
    function showPreview(color, colorName) { }
    function initPreviewCalculator(wrapper, color) { }
    function copyPreviewCode() { }
    
    // 9. AWG handler
    function openAWG() { }
    
    // 10. FAQ accordion
    function toggleFAQ(header) { }
    
    // 11. Event Delegation (מקסימום 10 listeners!)
    container.addEventListener('click', function(e) {
        const action = e.target.closest('[data-action]');
        if (!action) return;
        
        switch(action.dataset.action) {
            case 'switch-tab': switchTab(action.dataset.tab); break;
            case 'open-awg': openAWG(); break;
            case 'scroll-to-embed': scrollToEmbed(); break;
            case 'copy-embed-code': copyEmbedCode(); break;
            case 'preview-color': showPreview(action.dataset.color, action.dataset.name); break;
            case 'copy-preview-code': copyPreviewCode(); break;
            case 'toggle-faq': toggleFAQ(action); break;
            // ...
        }
    });
    
    // 12. Initialize
    function init() {
        calculateTab1();
        // ...
    }
    
    init();
    
    // 13. Expose minimal API
    window[NS] = { version: '1.0.0' };
})();
```

---

## 📱 מערכת הטמעה - דרישות מלאות

### 1. טקסט דינמי באזור ההטמעה
**חשוב מאוד!** כל הטקסטים באזור ההטמעה חייבים להיות **דינמיים לפי סוג המחשבון**:

| Placeholder | תיאור |
|------------|---------|
| `{CALCULATOR_NAME}` | שם המחשבון בעברית |
| `{CALCULATOR_VALUE}` | שווי הפיתוח בשקלים |
| `{TAB_COUNT}` | מספר הטאבים במחשבון |
| `{KEYWORDS}` | מילות מפתח רלוונטיות |
| `{RELATED_PAGES}` | דפים מומלצים להטמעה |

**דוגמאות לפי סוג מחשבון:**

| מחשבון | CALCULATOR_NAME | VALUE | KEYWORDS | RELATED_PAGES |
|--------|-----------------|-------|----------|---------------|
| חיסכון | מחשבון החיסכון | ₪12,000 | מחשבון חיסכון, תכנון פיננסי | תכנון חיסכון, השקעות לטווח ארוך |
| ברוטו נטו | מחשבון ברוטו נטו | ₪10,000 | שכר נטו, מס הכנסה, מדרגות מס | חישוב שכר, מדרגות מס 2025 |
| משכנתא | מחשבון המשכנתא | ₪18,000 | מחשבון משכנתא, החזר חודשי | רכישת דירה, הלוואות דיור |
| ריבית דריבית | מחשבון הריבית דריבית | ₪15,000 | ריבית דריבית, חיסכון ארוך טווח | השקעות, קרן השתלמות |
| פנסיה | מחשבון הפנסיה | ₪14,000 | חישוב פנסיה, גיל פרישה | תכנון פרישה, חיסכון פנסיוני |
| הלוואות | מחשבון ההלוואות | ₪12,000 | מחשבון הלוואה, ריבית הלוואה | השוואת הלוואות, מימון |

### 2. מבנה אזור ההטמעה (תבנית)
```html
<div class="wpc-calc-[topic]-[random]-embed-section" id="embed-section">
    <!-- כותרת ראשית -->
    <h2>🎁 רוצים להטמיע את {CALCULATOR_NAME} באתר שלכם? חינם לחלוטין!</h2>
    
    <!-- הצעת ערך -->
    <div class="embed-value-box">
        <p>
            <strong>💎 אנחנו נותנים לכם את {CALCULATOR_NAME} המתקדם הזה לחלוטין בחינם!</strong><br>
            תמורת קישור קרדיט קטן לאתר שלנו, תקבלו מחשבון מקצועי עם {TAB_COUNT} טאבים, חישובים מדויקים, ועיצוב responsive מלא.<br>
            <strong>שווי המחשבון:</strong> מעל {CALCULATOR_VALUE} בפיתוח 💰 | <strong>מה ששילמתם:</strong> ₪0 🎉
        </p>
    </div>
    
    <!-- יתרונות SEO -->
    <div class="embed-seo-box">
        <h3>🚀 למה להטמיע מחשבון באתר שלכם? זה משפר את ה-SEO!</h3>
        <p><strong>הוספת מחשבון אינטראקטיבי לאתר היא אחת הדרכים הטובות ביותר לשפר את דירוג האתר במנועי החיפוש!</strong></p>
        <ul>
            <li>📈 <strong>תוכן אינטראקטיבי איכותי</strong> - גוגל אוהבת דפים עם כלים שימושיים</li>
            <li>⏱️ <strong>זמן שהייה ארוך יותר</strong> - מבקרים נשארים בדף יותר זמן</li>
            <li>🔗 <strong>מילות מפתח רלוונטיות</strong> - המחשבון כולל מילות מפתח כמו "{KEYWORDS}"</li>
            <li>🎯 <strong>מחשבון בחינם להטמעה</strong> - תוכן ייחודי בלי עלות פיתוח</li>
            <li>💼 <strong>מקצועיות ואמינות</strong> - אתר עם כלי מחשבון נראה מקצועי יותר</li>
            <li>📱 <strong>Mobile Friendly</strong> - מחשבון responsive = נקודות SEO נוספות</li>
            <li>🔄 <strong>עדכונים חוזרים</strong> - משתמשים חוזרים לאתר להשתמש במחשבון</li>
            <li>📊 <strong>הקטנת Bounce Rate</strong> - המבקרים נשארים להשתמש בכלי</li>
        </ul>
        <p class="seo-tip">
            💡 <strong>טיפ SEO:</strong> הוסיפו את המחשבון בדפים רלוונטיים כמו "{RELATED_PAGES}" - 
            זה יחזק את הדף בדיוק במילות המפתח שאתם רוצים לדרג עליהן!
        </p>
    </div>
    
    <!-- הוראות הטמעה -->
    <h3>📋 איך מטמיעים? (3 דקות בלבד)</h3>
    <p><strong>✅ יתרונות SEO:</strong> קישור הקרדיט נמצא ב-DOM המקורי - גוגל רואה ומזהה אותו מיידית!</p>
    <ol>
        <li><strong>לחצו</strong> על הכפתור הירוק "העתק קוד HTML" למטה 👇</li>
        <li><strong>פתחו</strong> את עורך וורדפרס שלכם (מצב <code>Text/HTML</code>, לא Visual)</li>
        <li><strong>הדביקו</strong> את הקוד במיקום הרצוי בעמוד</li>
        <li><strong>פרסמו!</strong> המחשבון יעבוד מיידית ללא הגדרות נוספות ✨</li>
    </ol>
    
    <!-- כפתור העתקה + בורר צבעים + תצוגה מקדימה -->
    <!-- ... המשך ... -->
    
    <!-- תנאי שימוש -->
    <div class="embed-terms">
        <h4>⚠️ חשוב לדעת - זכויות יוצרים ומגבלות שימוש</h4>
        <p>
            מחשבון זה מוגן בזכויות יוצרים © וניתן להטמעה באתר שלכם בחינם רק תמורת השארת קישור הקרדיט.<br>
            המחשבון כולל מנגנוני הגנה מתקדמים שישיבו אוטומטית את הקרדיט אם ינסו להסירו.
        </p>
        <p><strong>אסור בהחלט:</strong> הסרת/שינוי/הסתרת קישור הקרדיט, שימוש מסחרי ישיר ללא אישור, מכירת המחשבון.</p>
    </div>
    
    <!-- CTA למחשבון מותאם -->
    <div class="embed-custom-cta">
        <h3>🎯 רוצים מחשבון מותאם אישית לאתר שלכם?</h3>
        <p>יש לכם צורך בלוגיקת חישוב שונה? עיצוב מותאם? שדות נוספים? אנחנו נשמח לפתח לכם מחשבון ייעודי בחינם!</p>
        <p>📧 שלחו לנו מייל ל: <strong>info@loan-israel.co.il</strong></p>
        <p>כתבו: "בקשה למחשבון מותאם" + תיאור קצר של מה שאתם צריכים 💚</p>
    </div>
</div>
```

### 3. כפתור העתקת קוד HTML מלא
```html
<button class="wpc-calc-[topic]-[random]-embed-button-large" 
        data-action="copy-embed-code">
    📋 העתק קוד HTML מלא - לחצו כאן!
</button>
```

### 4. בורר צבעים - 10 עיגולי צבע (ללא טקסט!)
**חשוב: הכפתורים הם עיגולים בלבד, ללא טקסט! שם הצבע מופיע רק ב-title (tooltip)**

```html
<!-- מבנה בורר הצבעים - עיגולים בלבד -->
<div class="wpc-calc-[topic]-[random]-color-picker" style="display: flex; flex-wrap: wrap; justify-content: center; gap: 12px;">
    <button style="background: #1e5490; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
            data-action="preview-color" data-color="#1e5490" data-name="כחול מקצועי" title="כחול מקצועי 💙"></button>
    <button style="background: #10b981; width: 50px; height: 50px; border-radius: 50%; ..." 
            data-action="preview-color" data-color="#10b981" data-name="ירוק צמיחה" title="ירוק צמיחה 💚"></button>
    <!-- ... 8 כפתורים נוספים ... -->
</div>
```

```javascript
// מערך הצבעים ב-JavaScript
const COLORS = [
    { color: '#1e5490', name: 'כחול מקצועי', emoji: '💙' },
    { color: '#10b981', name: 'ירוק צמיחה', emoji: '💚' },
    { color: '#ef4444', name: 'אדום אנרגטי', emoji: '❤️' },
    { color: '#8b5cf6', name: 'סגול יוקרתי', emoji: '💜' },
    { color: '#f59e0b', name: 'כתום דינמי', emoji: '🧡' },
    { color: '#ec4899', name: 'ורוד מודרני', emoji: '💗' },
    { color: '#06b6d4', name: 'טורקיז רענן', emoji: '🩵' },
    { color: '#84cc16', name: 'ליים עז', emoji: '💛' },
    { color: '#f97316', name: 'כתום בוהק', emoji: '🔥' },
    { color: '#0891b2', name: 'כחול ים', emoji: '🌊' }
];
```

### 5. Color Picker מותאם אישית
```html
<input type="color" id="wpc-calc-[topic]-[random]-custom-color" 
       value="#1e5490" data-action="preview-custom-color"
       style="width: 50px; height: 50px; border-radius: 50%; cursor: pointer; border: 2px solid #ddd;">
```

### 6. תצוגה מקדימה דינמית
- שכפול מלא של המחשבון עם הצבע הנבחר
- כל הטאבים עובדים בתצוגה מקדימה
- סליידרים וכפתורי בחירה אינטראקטיביים
- כפתור העתקה עם הצבע הנוכחי

### 6. לוגיקת העתקת קוד עם CSS + JS + קרדיט דינמי
```javascript
// הגדר את שם המחשבון בתחילת הסקריפט
const CALCULATOR_NAME = 'ברוטו נטו'; // שנה לפי סוג המחשבון

function copyEmbedCode() {
    const calculator = document.getElementById('wpc-calc-[topic]-[random]-calculator');
    const calcClone = calculator.cloneNode(true);
    
    // מצא את כל ה-CSS הרלוונטי
    let styles = '';
    document.querySelectorAll('style').forEach(style => {
        if (style.textContent.includes('wpc-calc-[topic]-[random]')) {
            styles = style.textContent;
        }
    });
    
    // צור קוד עם CSS
    let code = '<style>\n' + styles + '\n</style>\n';
    code += '<div class="wpc-calc-[topic]-[random]-wrapper" id="wpc-calc-[topic]-[random]-main">\n';
    code += '<div class="wpc-calc-[topic]-[random]-calculator" id="wpc-calc-[topic]-[random]-calculator">';
    code += calcClone.innerHTML + '</div>\n';
    code += '</div>\n';
    
    // הוסף קרדיט דינמי
    code += `<p style="text-align:center; font-size:0.9em; margin-top:20px; color:#666;">
        מחשבון ${CALCULATOR_NAME} פותח על ידי 
        <a href="https://loan-israel.co.il/" target="_blank" rel="nofollow noopener" 
           style="color:#1e5490; text-decoration:underline;">
           רק תבקש פיננסים
        </a>
    </p>\n`;
    
    // הוסף JavaScript עצמאי להטמעה
    code += getEmbedScript();
    
    navigator.clipboard.writeText(code);
    alert('הקוד הועתק!');
}
```

### 7. פונקציית getEmbedScript - JavaScript עצמאי להטמעה

**עקרונות חשובים:**
1. **עטיפה ב-DOMContentLoaded** - מבטיח שה-DOM מוכן לפני הרצת הקוד
2. **תחביר ES5** - `var` במקום `const/let`, פונקציות רגילות במקום arrow functions
3. **סגירת תג script בטוחה** - `'</' + 'script>'` למניעת פרשנות שגויה
4. **בניית הסקריפט כמערך שורות** - למניעת בעיות escaping

```javascript
function getEmbedScript() {
    const scriptLines = [
        '<script>',
        'document.addEventListener("DOMContentLoaded", function() {',
        '  (function() {',
        '    "use strict";',
        '    var NS = "WPC_Calc[Topic]_Embed";',
        '    if (window[NS]) return;',
        '    var container = document.getElementById("wpc-calc-[topic]-[random]-main");',
        '    if (!container) { console.error("Container not found"); return; }',
        '',
        '    // === פונקציות חישוב ===',
        '    function formatCurrency(n) { return Math.round(n).toLocaleString("he-IL") + " ₪"; }',
        '    // ... שאר פונקציות החישוב ...',
        '',
        '    // === State management ===',
        '    var state = {',
        '      tab1: { /* ערכים התחלתיים */ },',
        '      tab2: { /* ערכים התחלתיים */ }',
        '    };',
        '',
        '    // === Update functions לכל טאב ===',
        '    function el(id) { return document.getElementById(id); }',
        '    function updateTab1() { /* עדכון אלמנטים לפי state */ }',
        '    function updateTab2() { /* עדכון אלמנטים לפי state */ }',
        '',
        '    // === Tab switching ===',
        '    function switchTab(tab) {',
        '      var tabs = container.querySelectorAll(".wpc-calc-[topic]-[random]-tab-btn");',
        '      var contents = container.querySelectorAll(".wpc-calc-[topic]-[random]-tab-content");',
        '      for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove("active");',
        '      for (var j = 0; j < contents.length; j++) contents[j].classList.remove("active");',
        '      var tabBtn = container.querySelector("[data-tab=\\"" + tab + "\\"]");',
        '      if (tabBtn) tabBtn.classList.add("active");',
        '      var tabContent = document.getElementById("tab-" + tab);',
        '      if (tabContent) tabContent.classList.add("active");',
        '    }',
        '',
        '    // === Event delegation ===',
        '    container.addEventListener("click", function(e) {',
        '      var action = e.target.closest("[data-action]");',
        '      if (!action) return;',
        '      var act = action.dataset.action;',
        '      if (act === "switch-tab") switchTab(action.dataset.tab);',
        '      // ... טיפול בשאר הactions ...',
        '    });',
        '',
        '    container.addEventListener("input", function(e) {',
        '      var id = e.target.id;',
        '      // טיפול בסליידרים לפי ID',
        '      if (id === "tab1-slider") { state.tab1.value = parseInt(e.target.value); updateTab1(); }',
        '    });',
        '',
        '    // === אתחול ===',
        '    updateTab1(); updateTab2();',
        '    window[NS] = { version: "1.0.0" };',
        '  })();',
        '});'
    ];
    // סגירת תג script בצורה בטוחה
    return scriptLines.join('\\n') + '\\n</' + 'script>';
}
```

**חשוב - התאמת IDs:**
ודא שה-IDs בסקריפט תואמים בדיוק ל-HTML:
- סליידרים: `[tab-name]-[field]-slider` (לדוגמה: `basic-gross-slider`)
- ערכים: `[tab-name]-[field]-value` (לדוגמה: `basic-gross-value`)  
- תוצאות: `[tab-name]-result-[field]` (לדוגמה: `basic-result-net`)

### 8. קרדיט דינמי לעמוד הבית (nofollow)
הקרדיט תמיד מפנה לעמוד הבית עם:
- **שם המחשבון דינמי** - משתנה לפי סוג המחשבון
- **אנקור קבוע**: "רק תבקש פיננסים"
- **קישור nofollow** לעמוד הבית

```javascript
// דוגמאות לשמות מחשבונים:
const CALCULATOR_NAMES = {
    'salary': 'ברוטו נטו',
    'loan': 'הלוואות',
    'mortgage': 'משכנתא',
    'pension': 'פנסיה',
    'savings': 'חיסכון',
    'compound': 'ריבית דריבית'
};
```

```html
<!-- פורמט הקרדיט -->
<p style="text-align:center; font-size:0.9em; margin-top:20px; color:#666;">
    מחשבון [שם דינמי] פותח על ידי 
    <a href="https://loan-israel.co.il/" target="_blank" rel="nofollow noopener" 
       style="color:#1e5490; text-decoration:underline;">
       רק תבקש פיננסים
    </a>
</p>
```

---

## 🔍 SEO - דרישות Schema.org

### 1. FAQPage Schema
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "שאלה?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "תשובה..."
      }
    }
  ]
}
```

### 2. FinancialProduct Schema
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialProduct",
  "name": "שם המחשבון",
  "description": "תיאור המחשבון",
  "category": "Financial Calculator",
  "featureList": ["פיצ'ר 1", "פיצ'ר 2"],
  "provider": {
    "@type": "Organization",
    "name": "רק תבקש - אפטריו בע״מ",
    "url": "https://loan-israel.co.il"
  },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "ILS"
  }
}
```

### 3. HowTo Schema
```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "איך להשתמש במחשבון",
  "step": [
    {
      "@type": "HowToStep",
      "name": "שלב 1",
      "text": "הסבר..."
    }
  ]
}
```

---

## ⚠️ אזורים חובה בכל עמוד

### 1. AWG Section עם כפתורים כפולים
```html
<div class="wpc-calc-[topic]-[random]-awg-section">
    <div class="wpc-calc-[topic]-[random]-awg-container">
        <div class="wpc-calc-[topic]-[random]-cta-buttons-wrapper">
            <!-- כפתור אדום - פותח AWG -->
            <button class="wpc-calc-[topic]-[random]-cta-btn" 
                    data-action="open-awg">
                בדוק זכאות להלוואה עכשיו - קבל הצעה מיידית!
            </button>
            <!-- כפתור הטמעה -->
            <button class="wpc-calc-[topic]-[random]-cta-embed" 
                    data-action="scroll-to-embed">
                🎁 רוצה להטמיע את המחשבון בחינם באתרך? לחץ כאן!
            </button>
        </div>
        <div class="wpc-calc-[topic]-[random]-awg-content">
            <div class="wpc-calc-[topic]-[random]-shortcode-item">
                [awg postid="XXXXX"]
            </div>
        </div>
    </div>
</div>
```

---

## 📊 נוסחאות פיננסיות נפוצות

### PMT - תשלום חודשי להלוואה
```javascript
function calculatePMT(principal, annualRate, months) {
    const monthlyRate = annualRate / 100 / 12;
    if (monthlyRate === 0) return principal / months;
    return principal * (monthlyRate * Math.pow(1 + monthlyRate, months)) / 
           (Math.pow(1 + monthlyRate, months) - 1);
}
```

### FV - ערך עתידי עם הפקדות
```javascript
function calculateFV(principal, annualRate, years, monthlyDeposit) {
    const monthlyRate = annualRate / 100 / 12;
    const months = years * 12;
    
    // ערך עתידי של סכום התחלתי
    const fvPrincipal = principal * Math.pow(1 + monthlyRate, months);
    
    // ערך עתידי של הפקדות חודשיות
    const fvDeposits = monthlyDeposit * 
        ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate);
    
    return fvPrincipal + fvDeposits;
}
```

### ריבית דריבית פשוטה
```javascript
function compoundInterest(principal, annualRate, years, compoundsPerYear = 12) {
    return principal * Math.pow(1 + annualRate / 100 / compoundsPerYear, 
                                compoundsPerYear * years);
}
```

### חישוב תשלום נדרש ליעד
```javascript
function calculateRequiredPayment(goal, initial, annualRate, years) {
    const monthlyRate = annualRate / 100 / 12;
    const months = years * 12;
    
    const fvInitial = initial * Math.pow(1 + monthlyRate, months);
    const remaining = goal - fvInitial;
    
    if (remaining <= 0) return 0;
    
    return remaining / ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate);
}
```

---

## ✅ צ'קליסט סופי לסוכן

### לפני יצירת העמוד:
- [ ] וודא prefix ייחודי: `wpc-calc-[topic]-[4random]-`
- [ ] וודא namespace ייחודי: `WPC_Calc[Topic]_[Random]`
- [ ] אסוף את כל הנתונים הנדרשים (נושא, טאבים, FAQ)

### מבנה העמוד:
- [ ] התחלה עם viewport script (בלי DOCTYPE!)
- [ ] CSS Variables מוגדרים
- [ ] כל הקלאסים עם prefix ייחודי
- [ ] כל ה-CSS עם `!important`
- [ ] Media queries ל-768px, 480px, 375px

### מחשבון:
- [ ] טאבים עובדים (2-5)
- [ ] טאבים עם flex-wrap (ללא סקרול אופקי!)
- [ ] סליידרים עם עדכון ערכים
- [ ] כפתורי בחירה עם active state
- [ ] נוסחאות מדויקות
- [ ] תוצאות מתעדכנות בזמן אמת

### AWG Section:
- [ ] כפתור אדום "בדוק זכאות"
- [ ] כפתור "הטמע בחינם"
- [ ] AWG content נסתר עד לחיצה
- [ ] Shortcode [awg postid="XXXXX"]

### מערכת הטמעה:
- [ ] הוראות הטמעה ברורות
- [ ] כפתור העתקת קוד HTML
- [ ] 10 עיגולי צבע (ללא טקסט, רק title) + color picker
- [ ] קוד מיוצא כולל CSS + HTML + JS עצמאי
- [ ] JS עטוף ב-DOMContentLoaded
- [ ] JS בתחביר ES5 (var, function רגיל)
- [ ] סגירת script tag בטוחה: `'</' + 'script>'`
- [ ] IDs בסקריפט תואמים ל-HTML בדיוק
- [ ] כל הטאבים עובדים בהטמעה
- [ ] תצוגה מקדימה דינמית עובדת (כל הטאבים)
- [ ] כפתור העתקה עם צבע נבחר
- [ ] תנאי שימוש ברורים

### תוכן:
- [ ] H1 עם כותרת ראשית
- [ ] תאריך עדכון [current_date]
- [ ] תוכן SEO רלוונטי
- [ ] FAQ עם 5-10 שאלות
- [ ] Schema.org מלא (FAQPage, FinancialProduct, HowTo)

### JavaScript:
- [ ] IIFE עם namespace ייחודי
- [ ] Event delegation מרכזי
- [ ] מקסימום 10 event listeners
- [ ] פונקציות embed מלאות (getEmbedScript)
- [ ] תצוגה מקדימה עובדת עם כל הטאבים

### בדיקות סופיות:
- [ ] עברית 100% (אין אנגלית בממשק)
- [ ] רספונסיבי - 375px עובד
- [ ] כל הכפתורים פונקציונליים
- [ ] הטמעה חיצונית עובדת (כל הטאבים, כל הסליידרים)
- [ ] קרדיט דינמי מופיע בקוד המיוצא

---

## 📁 תיקיית פיתוח ודוגמאות

### תיקיית עבודה:
```
C:\Users\eyal\loan-israel-updaets\loan-israel-updates\מחשבונים חדשים\
```

כל המחשבונים החדשים נוצרים ונשמרים בתיקייה זו.

### קבצי ייחוס:
| קובץ | תיאור |
|------|-------|
| `מחשבון חיסכון.html` | דוגמה מלאה עם כל האלמנטים |
| `מחשבון ברוטו נטו.html` | מחשבון שכר עם מערכת הטמעה מלאה |
| `מחשבון משכנתא.html` | מחשבון מורכב עם טאבים מרובים |
| `מחשבון ריבית דה ריבית.html` | דוגמה לחישובים פיננסיים |

### יצירת מחשבון חדש:
1. צור קובץ חדש בתיקייה `מחשבונים חדשים`
2. השתמש בprefix ייחודי: `wpc-calc-[topic]-[4random]-`
3. עקוב אחרי המבנה בקבצי הייחוס

---

## 🚀 הפעלת הסוכן

```
נושא: [הכנס נושא]
נושא באנגלית: [הכנס topic באנגלית]
כותרת: [הכנס כותרת H1]
טאבים: [הכנס 2-5 טאבים עם פרטים]
AWG Post ID: [הכנס מזהה]
FAQ: [הכנס 5-10 שאלות ותשובות]
```

הסוכן יפיק עמוד HTML מלא ומוכן להדבקה בוורדפרס!

---

**נוצר על ידי: Cursor AI**  
**תאריך: דצמבר 2025**  
**גרסה: 1.0**
