# 🤖 סוכן AI לבניית עמודי מחשבון פיננסי - איפיון מלא

## 📋 תיאור הסוכן

סוכן AI שמקבל **נושא של מחשבון פיננסי** ובונה **עמוד HTML מלא ומוכן לוורדפרס** מאפס, כולל:
- מחשבון אינטראקטיבי עם טאבים
- אזור AWG (טופס בדיקת זכאות)
- מערכת הטמעה מלאה עם תצוגה מקדימה
- תוכן SEO איכותי
- Schema.org מלא
- עיצוב רספונסיבי לכל המכשירים

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
| `author_name` | ❌ | שם הכותב | "אייל עובדיה" |
| `author_image` | ❌ | URL לתמונת הכותב | "https://..." |
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
│   │   └── כפתור CTA + כפתור הטמעה ירוק
│   │       └── AWG Content (נסתר עד לחיצה)
│   │           └── [awg postid="XXXXX"]
│   │
│   ├── Content Section (תוכן SEO)
│   │   ├── כותרת משנית
│   │   ├── הסברים על כל טאב
│   │   ├── טיפים ודוגמאות
│   │   └── מידע נוסף רלוונטי
│   │
│   ├── FAQ Section (שאלות נפוצות)
│   │   └── Accordion Items (5-10 שאלות)
│   │
│   ├── Author Section (פרופיל כותב)
│   │   ├── תמונה
│   │   ├── טקסט ביו
│   │   ├── פרטים מקצועיים
│   │   └── ציטוט
│   │
│   ├── Embed Section (מערכת הטמעה)
│   │   ├── הוראות הטמעה
│   │   ├── כפתור העתקת קוד HTML
│   │   ├── בורר צבעים (10 צבעים + color picker)
│   │   ├── תצוגה מקדימה דינמית
│   │   ├── כפתור העתקה עם צבע
│   │   ├── תנאי שימוש
│   │   └── CTA למחשבון מותאם אישית
│   │
│   ├── Disclaimer (הצהרה משפטית)
│   │
│   └── [related-shortcode-instert] (חובה בסוף!)
│
└── Schema.org Scripts (JSON-LD)
    ├── FAQPage
    ├── FinancialProduct
    ├── Person (Author)
    ├── HowTo
    └── Organization
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

### 1. הוראות הטמעה
- הסבר ברור בעברית
- שלבים ממוספרים
- דגש על קרדיט חובה

### 2. כפתור העתקת קוד HTML מלא
```html
<button class="wpc-calc-[topic]-[random]-embed-button-large" 
        data-action="copy-embed-code">
    📋 העתק קוד HTML מלא - לחצו כאן!
</button>
```

### 3. בורר צבעים - 10 צבעים מוכנים
```javascript
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

### 4. Color Picker מותאם אישית
```html
<input type="color" id="wpc-calc-[topic]-[random]-custom-color" 
       value="#1e5490" data-action="preview-custom-color">
```

### 5. תצוגה מקדימה דינמית
- שכפול המחשבון עם הצבע הנבחר
- אינטראקטיביות מלאה (סליידרים, טאבים)
- כפתור העתקה עם הצבע הנוכחי

### 6. לוגיקת העתקת קוד
```javascript
function copyEmbedCode() {
    // שכפל את המחשבון
    const calcClone = calculator.cloneNode(true);
    
    // הסר אלמנטים מיותרים
    calcClone.querySelector('.title-container')?.remove();
    calcClone.querySelector('[data-action="scroll-to-embed"]')?.remove();
    calcClone.querySelector('.awg-section')?.remove();
    
    // הסר תאריך ומידע ריבית
    calcClone.querySelectorAll('p').forEach(p => {
        if (p.textContent.includes('עודכן לאחרונה') || 
            p.textContent.includes('current_date') ||
            p.textContent.includes('הריביות בתוכן')) {
            p.remove();
        }
    });
    
    // צור קוד עם קרדיט
    let code = calcStyles + '\n' + calcClone.outerHTML;
    code += `\n<p style="text-align:center; font-size:0.9em; margin-top:20px; color:#666;">
        מחשבון זה סופק על ידי 
        <a href="https://loan-israel.co.il/" target="_blank" 
           style="color:#1e5490; text-decoration:underline;">
           ${getRandomAnchor()}
        </a>
    </p>`;
    
    navigator.clipboard.writeText(code);
    alert('הקוד הועתק!');
}
```

### 7. אנכורים דינמיים לקרדיט (23 וריאנטים)
```javascript
const ANCHOR_VARIANTS = [
    "לוון ישראל - פורטל ההלוואות המוביל בישראל",
    "רק תבקש - הלוואות וייעוץ פיננסי",
    "מחשבוני הלוואות חינמיים",
    "פורטל הלוואות ישראלי",
    // ... 19 נוספים
];

function getRandomAnchor() {
    return ANCHOR_VARIANTS[Math.floor(Math.random() * ANCHOR_VARIANTS.length)];
}
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

### 3. Person Schema (כותב)
```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "אייל עובדיה",
  "jobTitle": "מנהל מקצועי ויועץ ראשי",
  "worksFor": {
    "@type": "Organization",
    "name": "רק תבקש - אפטריו בע״מ"
  },
  "knowsAbout": ["תחום 1", "תחום 2"],
  "image": "URL לתמונה"
}
```

### 4. HowTo Schema
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

### 5. Organization Schema
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "רק תבקש - אפטריו בע״מ",
  "url": "https://loan-israel.co.il",
  "telephone": "+972-53-428-8957",
  "founder": {
    "@type": "Person",
    "name": "אייל עובדיה"
  }
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
            <!-- כפתור ירוק - מפנה להטמעה -->
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

### 2. Disclaimer משפטי
```html
<div class="wpc-calc-[topic]-[random]-disclaimer">
    <p><strong>הצהרה משפטית:</strong> המידע באתר זה מוצג למטרות אינפורמטיביות בלבד 
    ואינו מהווה ייעוץ פיננסי, משפטי או מקצועי. תוצאות החישובים הן הערכות בלבד 
    ועשויות להשתנות בהתאם לתנאים בפועל. מומלץ להתייעץ עם גורם מקצועי מוסמך 
    לפני קבלת החלטות פיננסיות.</p>
</div>
```

### 3. Related Posts (חובה בסוף!)
```html
[related-shortcode-instert]
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
- [ ] סליידרים עם עדכון ערכים
- [ ] כפתורי בחירה עם active state
- [ ] נוסחאות מדויקות
- [ ] תוצאות מתעדכנות בזמן אמת

### AWG Section:
- [ ] כפתור אדום "בדוק זכאות"
- [ ] כפתור ירוק "הטמע בחינם"
- [ ] AWG content נסתר עד לחיצה
- [ ] Shortcode [awg postid="XXXXX"]

### מערכת הטמעה:
- [ ] הוראות הטמעה ברורות
- [ ] כפתור העתקת קוד HTML
- [ ] 10 כפתורי צבעים + color picker
- [ ] תצוגה מקדימה דינמית
- [ ] כפתור העתקה עם צבע
- [ ] קרדיט עם אנכור דינמי לעמוד הבית
- [ ] תנאי שימוש
- [ ] CTA למחשבון מותאם

### תוכן:
- [ ] H1 עם כותרת ראשית
- [ ] תאריך עדכון [current_date]
- [ ] תוכן SEO רלוונטי
- [ ] FAQ עם 5-10 שאלות
- [ ] פרופיל כותב

### סיום:
- [ ] Disclaimer משפטי
- [ ] [related-shortcode-instert]
- [ ] Schema.org מלא (5 סוגים)

### JavaScript:
- [ ] IIFE עם namespace
- [ ] Event delegation מרכזי
- [ ] מקסימום 10 event listeners
- [ ] פונקציות embed מלאות
- [ ] initPreviewCalculator עובד
- [ ] טאבים בתצוגה מקדימה עובדים

### בדיקות:
- [ ] עברית 100% (אין אנגלית בממשק)
- [ ] רספונסיבי - 375px עובד
- [ ] כל הכפתורים פונקציונליים
- [ ] העתקת קוד לא כוללת H1/תאריך/ריבית
- [ ] קרדיט מפנה לעמוד הבית בלבד

---

## 📁 דוגמת קובץ מלא

ראה קובץ ייחוס: `מחשבון חיסכון.html`

זהו דוגמה מלאה לעמוד מחשבון עם כל האלמנטים הנדרשים.

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
