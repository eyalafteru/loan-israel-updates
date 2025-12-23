# 🎯 סוכן QA לאזור הטמעה - בדיקה ותיקון

## 📋 תיאור הסוכן

סוכן QA ממוקד שבודק **רק את אזור ההטמעה** של מחשבונים.
**בודק ומתקן אוטומטית** שהכל עובד: צבעים מתחלפים, קוד מיוצא עם CSS, טאבים עובדים.

### 📂 תיקיית הקבצים:
```
C:\Users\eyal\loan-israel-updaets\loan-israel-updates\מחשבונים חדשים\
```

---

## 🚀 הפעלת הסוכן

```
בדוק ותקן אזור הטמעה: [שם הקובץ].html
```

---

# 🔴 בדיקות אזור הטמעה - הכי קריטי!

## 0️⃣ בדיקת תוכן אזור ההטמעה - התאמה למחשבון!

**קריטי!** כל התוכן באזור ההטמעה חייב להתאים למחשבון הספציפי.

### מה לבדוק:

| אלמנט | צריך להכיל | דוגמה (ריבית דריבית) |
|-------|-----------|----------------------|
| **כותרת ראשית** | שם המחשבון | "מחשבון הריבית דריבית" |
| **תיאור הערך** | סכום בשקלים | "₪15,000 בפיתוח" |
| **מספר טאבים** | מספר נכון | "4 טאבים" |
| **מילות מפתח SEO** | רלוונטיות למחשבון | "ריבית דריבית, חיסכון לטווח ארוך, השקעות" |
| **דפים מומלצים** | רלוונטיים | "חיסכון ריבית דריבית, השקעות לטווח ארוך" |
| **תנאי שימוש** | שם האתר | "loan-israel.co.il" |

### טבלת התאמה לפי סוג מחשבון:

```javascript
const CALCULATOR_CONTENT = {
    'compound-int': {
        name: 'מחשבון הריבית דריבית',
        shortName: 'ריבית דריבית',
        value: '₪15,000',
        tabs: 4,
        keywords: ['ריבית דריבית', 'חיסכון לטווח ארוך', 'השקעות', 'ערך עתידי'],
        relatedPages: ['חיסכון ריבית דריבית', 'השקעות לטווח ארוך', 'תכנון פיננסי']
    },
    'salary': {
        name: 'מחשבון ברוטו נטו',
        shortName: 'ברוטו נטו',
        value: '₪10,000',
        tabs: 3,
        keywords: ['שכר נטו', 'מס הכנסה', 'מדרגות מס', 'חישוב שכר'],
        relatedPages: ['חישוב שכר', 'מדרגות מס 2025', 'מס הכנסה']
    },
    'mortgage': {
        name: 'מחשבון המשכנתא',
        shortName: 'משכנתא',
        value: '₪18,000',
        tabs: 4,
        keywords: ['מחשבון משכנתא', 'החזר חודשי', 'ריבית משכנתא', 'הלוואת דיור'],
        relatedPages: ['רכישת דירה', 'הלוואות דיור', 'משכנתא ראשונה']
    },
    'savings': {
        name: 'מחשבון החיסכון',
        shortName: 'חיסכון',
        value: '₪12,000',
        tabs: 3,
        keywords: ['מחשבון חיסכון', 'תכנון פיננסי', 'הפקדה חודשית'],
        relatedPages: ['תכנון חיסכון', 'השקעות לטווח ארוך']
    },
    'loan': {
        name: 'מחשבון ההלוואות',
        shortName: 'הלוואות',
        value: '₪12,000',
        tabs: 4,
        keywords: ['מחשבון הלוואה', 'ריבית הלוואה', 'החזר חודשי'],
        relatedPages: ['השוואת הלוואות', 'מימון', 'הלוואה אישית']
    },
    'pension': {
        name: 'מחשבון הפנסיה',
        shortName: 'פנסיה',
        value: '₪14,000',
        tabs: 3,
        keywords: ['חישוב פנסיה', 'גיל פרישה', 'קצבה חודשית'],
        relatedPages: ['תכנון פרישה', 'חיסכון פנסיוני']
    },
    'tax': {
        name: 'מחשבון מס רכישה',
        shortName: 'מס רכישה',
        value: '₪10,000',
        tabs: 3,
        keywords: ['מס רכישה', 'רכישת דירה', 'מדרגות מס'],
        relatedPages: ['קניית דירה', 'מיסוי נדלן']
    },
    'employer-cost': {
        name: 'מחשבון עלות מעסיק',
        shortName: 'עלות מעסיק',
        value: '₪10,000',
        tabs: 2,
        keywords: ['עלות מעסיק', 'שכר עובד', 'עלויות העסקה'],
        relatedPages: ['ניהול שכר', 'עלויות עובד']
    }
};
```

### בדיקת התאמת תוכן:

```javascript
// === בדיקת התאמת תוכן אזור הטמעה ===
function checkEmbedContent(content, calculatorType) {
    const errors = [];
    const warnings = [];
    const expected = CALCULATOR_CONTENT[calculatorType];
    
    if (!expected) {
        warnings.push('⚠️ סוג מחשבון לא מוכר - בדיקה ידנית נדרשת');
        return { errors, warnings };
    }
    
    // 1. בדוק שם המחשבון בכותרת
    if (!content.includes(expected.name) && !content.includes(expected.shortName)) {
        errors.push(`❌ כותרת לא מכילה את שם המחשבון: "${expected.name}"`);
    }
    
    // 2. בדוק ערך המחשבון
    if (!content.includes(expected.value)) {
        warnings.push(`⚠️ ערך המחשבון לא מופיע: ${expected.value}`);
    }
    
    // 3. בדוק מספר טאבים
    const tabsPattern = new RegExp(`${expected.tabs}\\s*טאב`);
    if (!tabsPattern.test(content)) {
        warnings.push(`⚠️ מספר טאבים לא מופיע: ${expected.tabs} טאבים`);
    }
    
    // 4. בדוק מילות מפתח
    const foundKeywords = expected.keywords.filter(kw => content.includes(kw));
    if (foundKeywords.length < expected.keywords.length / 2) {
        warnings.push(`⚠️ חסרות מילות מפתח רלוונטיות. נמצאו: ${foundKeywords.join(', ')}`);
    }
    
    // 5. בדוק שאין תוכן ממחשבון אחר!
    const wrongContent = checkForWrongContent(content, calculatorType);
    if (wrongContent.length > 0) {
        errors.push(`❌ תוכן לא מתאים למחשבון! נמצא: ${wrongContent.join(', ')}`);
    }
    
    return { errors, warnings };
}

// בדיקת תוכן שגוי (ממחשבון אחר)
function checkForWrongContent(content, calculatorType) {
    const wrongTerms = [];
    
    // מיפוי מונחים ייחודיים לכל מחשבון
    const uniqueTerms = {
        'compound-int': ['ריבית דריבית', 'ערך עתידי'],
        'salary': ['ברוטו נטו', 'שכר נטו', 'מדרגות מס הכנסה'],
        'mortgage': ['משכנתא', 'הלוואת דיור'],
        'loan': ['הלוואה', 'ריבית הלוואה'],
        'pension': ['פנסיה', 'גיל פרישה'],
        'tax': ['מס רכישה', 'דירה יחידה'],
        'savings': ['חיסכון', 'הפקדה חודשית']
    };
    
    // בדוק אם יש מונחים ממחשבון אחר
    Object.entries(uniqueTerms).forEach(([type, terms]) => {
        if (type !== calculatorType) {
            terms.forEach(term => {
                // בדוק רק במקומות קריטיים (כותרות, תיאורים)
                const embedSection = content.match(/embed-section[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/i);
                if (embedSection && embedSection[0].includes(term)) {
                    // ודא שזה לא רק אזכור קונטקסטואלי
                    const termCount = (embedSection[0].match(new RegExp(term, 'gi')) || []).length;
                    if (termCount > 2) {
                        wrongTerms.push(`"${term}" (${termCount} פעמים)`);
                    }
                }
            });
        }
    });
    
    return wrongTerms;
}
```

### 🔧 תיקון - תבנית תוכן נכון לאזור הטמעה:

```html
<!-- === תבנית אזור הטמעה - להתאים לפי סוג המחשבון === -->
<div class="wpc-calc-[PREFIX]-embed-section" id="embed-section">
    
    <!-- כותרת ראשית - שם המחשבון -->
    <h2>🎁 רוצים להטמיע את [CALCULATOR_NAME] באתר שלכם? חינם לחלוטין!</h2>
    
    <!-- תיאור ערך -->
    <div style="background: rgba(30, 84, 144, 0.08); padding: 20px; border-radius: 12px; margin-bottom: 30px; border-right: 4px solid var(--primary);">
        <p style="font-size: 1.1em; line-height: 1.7; margin: 0; color: #222;">
            <strong>💎 אנחנו נותנים לכם את [CALCULATOR_NAME] המתקדם הזה לחלוטין בחינם!</strong><br>
            תמורת קישור קרדיט קטן לאתר שלנו, תקבלו מחשבון מקצועי עם [TAB_COUNT] טאבים, חישובים מדויקים ועיצוב responsive מלא.<br>
            <strong>שווי המחשבון:</strong> מעל [VALUE] בפיתוח 💰 | <strong>מה ששילמתם:</strong> ₪0 🎉
        </p>
    </div>
    
    <!-- יתרונות SEO - מילות מפתח רלוונטיות -->
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 25px; border-radius: 12px; margin: 30px 0; border: 2px solid #0ea5e9;">
        <h3 style="color: #0369a1; margin-top: 0;">🚀 למה להטמיע מחשבון באתר שלכם? זה משפר את ה-SEO!</h3>
        <p style="line-height: 1.8; color: #222; margin-bottom: 15px;">
            <strong>הוספת מחשבון אינטראקטיבי לאתר היא אחת הדרכים הטובות ביותר לשפר את דירוג האתר במנועי החיפוש!</strong>
        </p>
        <ul style="line-height: 2; color: #222; margin: 0;">
            <li>📈 <strong>תוכן אינטראקטיבי איכותי</strong> - גוגל אוהבת דפים עם כלים שימושיים</li>
            <li>⏱️ <strong>זמן שהייה ארוך יותר</strong> - מבקרים נשארים בדף יותר זמן</li>
            <li>🔗 <strong>מילות מפתח רלוונטיות</strong> - המחשבון כולל מילות מפתח כמו "[KEYWORDS]"</li>
            <li>🎯 <strong>מחשבון בחינם להטמעה</strong> - תוכן ייחודי בלי עלות פיתוח</li>
            <li>💼 <strong>מקצועיות ואמינות</strong> - אתר עם כלי מחשבון נראה מקצועי יותר</li>
            <li>📱 <strong>Mobile Friendly</strong> - מחשבון responsive מלא</li>
            <li>🔄 <strong>עדכונים חוזרים</strong> - משתמשים חוזרים לאתר</li>
            <li>📊 <strong>הקטנת Bounce Rate</strong> - המבקרים נשארים להשתמש בכלי</li>
        </ul>
        <p style="margin-top: 20px; margin-bottom: 0; padding: 15px; background: white; border-radius: 8px; color: #0369a1; font-weight: 700;">
            💡 <strong>טיפ SEO:</strong> הוסיפו את המחשבון בדפים רלוונטיים כמו "[RELATED_PAGES]" - 
            זה יחזק את הדף בדיוק במילות המפתח שאתם רוצים לדרג עליהן!
        </p>
    </div>
    
    <!-- ... המשך האזור (הוראות, צבעים, תנאים) ... -->
</div>
```

### רשימת Placeholders להחלפה:

| Placeholder | תיאור | דוגמה |
|-------------|-------|--------|
| `[CALCULATOR_NAME]` | שם המחשבון המלא | מחשבון הריבית דריבית |
| `[TAB_COUNT]` | מספר הטאבים | 4 |
| `[VALUE]` | שווי הפיתוח | ₪15,000 |
| `[KEYWORDS]` | מילות מפתח (מופרדות בפסיק) | ריבית דריבית, חיסכון לטווח ארוך |
| `[RELATED_PAGES]` | דפים מומלצים | חיסכון ריבית דריבית, השקעות |

### 🤖 הוראות לסוכן - בדיקת ותיקון תוכן:

1. **זהה את סוג המחשבון** מתוך ה-prefix או הכותרת
2. **בדוק שכל האזכורים תואמים** - שם המחשבון, מילות מפתח, דפים מומלצים
3. **אם נמצא תוכן ממחשבון אחר** - תקן והחלף בתוכן המתאים
4. **עדכן את מספר הטאבים** לפי המספר האמיתי במחשבון
5. **עדכן את הערך** לפי סוג המחשבון

---

## 1️⃣ בדיקת קיום אזור הטמעה

**בדוק שקיימים:**
- [ ] `embed-section` - אזור הטמעה ראשי
- [ ] `color-picker` או כפתורי `preview-color` - בורר צבעים
- [ ] `preview` - אזור תצוגה מקדימה
- [ ] `copy-embed-code` - כפתור העתקה
- [ ] `getEmbedScript` - פונקציית יצירת סקריפט

```javascript
// בדיקה בקוד:
const checks = {
    embedSection: content.includes('embed-section') || content.includes('embed'),
    colorPicker: content.includes('preview-color'),
    previewArea: content.includes('preview'),
    copyButton: content.includes('copy-embed-code'),
    getEmbedScript: content.includes('getEmbedScript'),
    copyEmbedCode: content.includes('copyEmbedCode')
};
```

---

## 2️⃣ בדיקת בורר צבעים והחלפת צבעים

### בדיקה:
```javascript
// מצא את כל כפתורי הצבע
const colorButtons = content.match(/data-action="preview-color"[^>]*data-color="([^"]+)"/g);
```

### צבעים נדרשים (10 צבעים):
```javascript
const REQUIRED_COLORS = [
    { color: '#1e5490', name: 'כחול מקצועי' },
    { color: '#10b981', name: 'ירוק צמיחה' },
    { color: '#ef4444', name: 'אדום אנרגטי' },
    { color: '#8b5cf6', name: 'סגול יוקרתי' },
    { color: '#f59e0b', name: 'כתום דינמי' },
    { color: '#ec4899', name: 'ורוד מודרני' },
    { color: '#06b6d4', name: 'טורקיז רענן' },
    { color: '#84cc16', name: 'ליים עז' },
    { color: '#f97316', name: 'כתום בוהק' },
    { color: '#0891b2', name: 'כחול ים' }
];
```

### 🔧 תיקון - אם חסרים כפתורי צבע:
```html
<!-- הוסף את זה באזור ההטמעה: -->
<div class="wpc-calc-[PREFIX]-color-picker">
    <p style="text-align: center; margin-bottom: 15px; font-weight: 600;">🎨 בחר צבע לתצוגה מקדימה:</p>
    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 12px;">
        <button style="background: #1e5490; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#1e5490" data-name="כחול מקצועי" title="כחול מקצועי 💙"></button>
        <button style="background: #10b981; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#10b981" data-name="ירוק צמיחה" title="ירוק צמיחה 💚"></button>
        <button style="background: #ef4444; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#ef4444" data-name="אדום אנרגטי" title="אדום אנרגטי ❤️"></button>
        <button style="background: #8b5cf6; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#8b5cf6" data-name="סגול יוקרתי" title="סגול יוקרתי 💜"></button>
        <button style="background: #f59e0b; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#f59e0b" data-name="כתום דינמי" title="כתום דינמי 🧡"></button>
        <button style="background: #ec4899; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#ec4899" data-name="ורוד מודרני" title="ורוד מודרני 💗"></button>
        <button style="background: #06b6d4; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#06b6d4" data-name="טורקיז רענן" title="טורקיז רענן 🩵"></button>
        <button style="background: #84cc16; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#84cc16" data-name="ליים עז" title="ליים עז 💛"></button>
        <button style="background: #f97316; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#f97316" data-name="כתום בוהק" title="כתום בוהק 🔥"></button>
        <button style="background: #0891b2; width: 50px; height: 50px; border-radius: 50%; border: 3px solid #fff; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" 
                data-action="preview-color" data-color="#0891b2" data-name="כחול ים" title="כחול ים 🌊"></button>
    </div>
</div>
```

---

## 3️⃣ בדיקת פונקציית showPreview (החלפת צבעים)

### בדיקה:
```javascript
// חפש את הפונקציה
const hasShowPreview = content.includes('function showPreview') || 
                       content.includes('showPreview:') ||
                       content.includes('showPreview =');
```

### 🔧 תיקון - אם חסרה פונקציית showPreview:
```javascript
    // === פונקציית תצוגה מקדימה עם החלפת צבע ===
    function showPreview(color, colorName) {
        // מצא את אזור התצוגה המקדימה
        let previewArea = container.querySelector('[class*="preview-area"]');
        
        // אם אין אזור תצוגה - צור אותו
        if (!previewArea) {
            previewArea = document.createElement('div');
            previewArea.className = PREFIX + 'preview-area';
            previewArea.style.cssText = 'margin-top: 30px; padding: 20px; border: 2px dashed #ddd; border-radius: 15px; background: #fafafa;';
            
            const embedSection = container.querySelector('[class*="embed"]');
            if (embedSection) {
                embedSection.appendChild(previewArea);
            }
        }
        
        // מצא את המחשבון המקורי
        const calculator = container.querySelector('[class*="calculator"]');
        if (!calculator) {
            console.error('לא נמצא מחשבון לשכפול');
            return;
        }
        
        // שכפל את המחשבון
        const clone = calculator.cloneNode(true);
        
        // החלף צבעים בשכפול
        replaceColors(clone, color);
        
        // כותרת
        const title = `<div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: ${color}; margin: 0;">תצוגה מקדימה - ${colorName}</h3>
            <p style="color: #666; font-size: 0.9em;">כך יראה המחשבון באתר שלך</p>
        </div>`;
        
        // כפתור העתקה
        const copyBtn = `<div style="text-align: center; margin-top: 20px;">
            <button data-action="copy-preview-code" data-color="${color}" 
                    style="background: ${color}; color: white; padding: 15px 40px; border: none; border-radius: 10px; font-size: 1.1em; cursor: pointer; font-weight: 600;">
                📋 העתק קוד עם צבע ${colorName}
            </button>
        </div>`;
        
        // הצג
        previewArea.innerHTML = title + clone.outerHTML + copyBtn;
        
        // אתחל את המחשבון בתצוגה המקדימה
        initPreviewCalculator(previewArea, color);
        
        // גלול לתצוגה
        previewArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // === פונקציה להחלפת צבעים ===
    function replaceColors(element, newColor) {
        const PRIMARY_COLOR = '#1e5490'; // הצבע המקורי
        
        // החלף בסגנונות inline
        element.querySelectorAll('*').forEach(el => {
            const style = el.getAttribute('style');
            if (style && style.includes(PRIMARY_COLOR)) {
                el.setAttribute('style', style.replace(new RegExp(PRIMARY_COLOR, 'gi'), newColor));
            }
            
            // החלף גם גרסה כהה יותר
            const darkColor = darkenColor(PRIMARY_COLOR, 15);
            const newDarkColor = darkenColor(newColor, 15);
            if (style && style.includes(darkColor)) {
                el.setAttribute('style', style.replace(new RegExp(darkColor, 'gi'), newDarkColor));
            }
        });
        
        // הוסף CSS variable override
        element.style.setProperty('--primary', newColor);
        element.style.setProperty('--primary-dark', darkenColor(newColor, 15));
    }
    
    // === פונקציה להכהיית צבע ===
    function darkenColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.max((num >> 16) - amt, 0);
        const G = Math.max((num >> 8 & 0x00FF) - amt, 0);
        const B = Math.max((num & 0x0000FF) - amt, 0);
        return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
    }
```

---

## 4️⃣ בדיקת פונקציית initPreviewCalculator (טאבים בתצוגה מקדימה)

### בדיקה:
```javascript
const hasInitPreview = content.includes('initPreviewCalculator');
```

### 🔧 תיקון - אם חסרה:
```javascript
    // === אתחול מחשבון בתצוגה מקדימה ===
    function initPreviewCalculator(previewArea, color) {
        // טאבים
        const tabs = previewArea.querySelectorAll('[data-action="switch-tab"]');
        const contents = previewArea.querySelectorAll('[class*="tab-content"]');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                const tabName = this.dataset.tab;
                
                // הסר active מכולם
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => {
                    c.classList.remove('active');
                    c.style.display = 'none';
                });
                
                // הוסף active לנבחר
                this.classList.add('active');
                const activeContent = previewArea.querySelector(`#tab-${tabName}, [id*="tab-${tabName}"]`);
                if (activeContent) {
                    activeContent.classList.add('active');
                    activeContent.style.display = 'block';
                }
            });
        });
        
        // סליידרים
        const sliders = previewArea.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            slider.addEventListener('input', function() {
                const valueId = this.id.replace('-slider', '-value').replace('-input', '-value');
                const valueEl = previewArea.querySelector(`#${valueId}`) || 
                               previewArea.querySelector(`#${this.id}-value`);
                if (valueEl) {
                    valueEl.textContent = parseInt(this.value).toLocaleString('he-IL');
                }
            });
        });
        
        // כפתורי בחירה
        const selectBtns = previewArea.querySelectorAll('[data-action="select-period"], [data-value]');
        selectBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const group = this.closest('[class*="group"], [class*="selector"]');
                if (group) {
                    group.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                }
                this.classList.add('active');
            });
        });
    }
```

---

## 5️⃣ בדיקת copyEmbedCode (העתקה כוללת CSS + JS)

### בדיקות קריטיות:
```javascript
// 1. הפונקציה קיימת
const hasCopyEmbed = content.includes('copyEmbedCode');

// 2. מעתיקה CSS
const copyIncludesCSS = content.includes("'<style>'") || content.includes('"<style>"') || 
                        content.includes('styles');

// 3. משתמשת ב-getEmbedScript
const copyUsesGetEmbed = content.match(/copyEmbedCode[\s\S]*?getEmbedScript/);

// 4. כוללת קרדיט
const copyIncludesCredit = content.match(/copyEmbedCode[\s\S]*?loan-israel/);
```

### 🔧 תיקון - פונקציית copyEmbedCode מלאה:
```javascript
    // === העתקת קוד להטמעה ===
    function copyEmbedCode() {
        // 1. אסוף את כל ה-CSS
        let styles = '';
        document.querySelectorAll('style').forEach(style => {
            if (style.textContent.includes(PREFIX)) {
                styles += style.textContent;
            }
        });
        
        // 2. קבל את ה-HTML של המחשבון
        const calculator = container.querySelector('[class*="calculator"]');
        if (!calculator) {
            alert('שגיאה: לא נמצא מחשבון');
            return;
        }
        
        const calcClone = calculator.cloneNode(true);
        
        // 3. בנה את הקוד המלא
        let code = '';
        
        // CSS
        code += '<style>\n';
        code += styles;
        code += '\n</style>\n\n';
        
        // HTML
        code += '<div class="' + PREFIX + 'wrapper" id="' + PREFIX + 'main">\n';
        code += calcClone.outerHTML;
        code += '\n</div>\n\n';
        
        // קרדיט
        code += '<p style="text-align:center; font-size:0.9em; margin-top:20px; color:#666;">\n';
        code += '  מחשבון זה פותח על ידי \n';
        code += '  <a href="https://loan-israel.co.il/" target="_blank" rel="nofollow noopener" ';
        code += 'style="color:#1e5490; text-decoration:underline;">רק תבקש פיננסים</a>\n';
        code += '</p>\n\n';
        
        // JavaScript
        code += getEmbedScript();
        
        // 4. העתק ללוח
        navigator.clipboard.writeText(code).then(() => {
            alert('✅ הקוד הועתק בהצלחה!\n\nהקוד כולל:\n• CSS מלא\n• HTML של המחשבון\n• JavaScript לטאבים וסליידרים\n• קרדיט');
        }).catch(err => {
            console.error('שגיאה בהעתקה:', err);
            // Fallback
            const textarea = document.createElement('textarea');
            textarea.value = code;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            alert('✅ הקוד הועתק!');
        });
    }
```

---

## 6️⃣ בדיקת getEmbedScript (טאבים וסליידרים בהטמעה)

### בדיקות קריטיות:
```javascript
// 1. הפונקציה קיימת
const hasGetEmbed = content.includes('getEmbedScript');

// 2. עטופה ב-DOMContentLoaded
const hasDOMContent = content.match(/getEmbedScript[\s\S]*?DOMContentLoaded/);

// 3. כוללת switchTab
const hasSwitchInEmbed = content.match(/getEmbedScript[\s\S]*?switchTab/);

// 4. כוללת event listener ל-input (סליידרים)
const hasInputListener = content.match(/getEmbedScript[\s\S]*?addEventListener.*input/);

// 5. סגירת script בטוחה
const safeScriptClose = content.includes("'</' + 'script>'") || 
                        content.includes('"</" + "script>"');
```

### 🔧 תיקון - פונקציית getEmbedScript מלאה:
```javascript
    // === יצירת סקריפט להטמעה ===
    function getEmbedScript() {
        const lines = [
            '<script>',
            'document.addEventListener("DOMContentLoaded", function() {',
            '  (function() {',
            '    "use strict";',
            '    var NS = "WPC_Embed_" + Date.now();',
            '    if (window[NS]) return;',
            '    var container = document.querySelector("[class*=\\"' + PREFIX + '\\"]");',
            '    if (!container) { console.error("Container not found"); return; }',
            '',
            '    // === מעבר טאבים ===',
            '    function switchTab(tabName) {',
            '      var tabs = container.querySelectorAll("[data-action=\\"switch-tab\\"]");',
            '      var contents = container.querySelectorAll("[class*=\\"tab-content\\"]");',
            '      for (var i = 0; i < tabs.length; i++) {',
            '        tabs[i].classList.remove("active");',
            '      }',
            '      for (var j = 0; j < contents.length; j++) {',
            '        contents[j].classList.remove("active");',
            '        contents[j].style.display = "none";',
            '      }',
            '      var activeTab = container.querySelector("[data-tab=\\"" + tabName + "\\"]");',
            '      if (activeTab) activeTab.classList.add("active");',
            '      var activeContent = document.getElementById("tab-" + tabName);',
            '      if (!activeContent) activeContent = container.querySelector("[id*=\\"tab-" + tabName + "\\"]");',
            '      if (activeContent) {',
            '        activeContent.classList.add("active");',
            '        activeContent.style.display = "block";',
            '      }',
            '    }',
            '',
            '    // === Event Delegation ===',
            '    container.addEventListener("click", function(e) {',
            '      var action = e.target.closest("[data-action]");',
            '      if (!action) return;',
            '      var act = action.dataset.action;',
            '      if (act === "switch-tab") {',
            '        e.preventDefault();',
            '        switchTab(action.dataset.tab);',
            '      }',
            '      if (act === "select-period" || action.dataset.value) {',
            '        var group = action.closest("[class*=\\"group\\"], [class*=\\"selector\\"]");',
            '        if (group) {',
            '          var btns = group.querySelectorAll("button");',
            '          for (var k = 0; k < btns.length; k++) btns[k].classList.remove("active");',
            '        }',
            '        action.classList.add("active");',
            '      }',
            '    });',
            '',
            '    // === סליידרים ===',
            '    container.addEventListener("input", function(e) {',
            '      if (e.target.type === "range") {',
            '        var id = e.target.id;',
            '        var valueId = id.replace("-slider", "-value").replace("-input", "-value");',
            '        var valueEl = document.getElementById(valueId);',
            '        if (!valueEl) valueEl = document.getElementById(id + "-value");',
            '        if (valueEl) {',
            '          valueEl.textContent = parseInt(e.target.value).toLocaleString("he-IL");',
            '        }',
            '      }',
            '    });',
            '',
            '    window[NS] = { v: "1.0" };',
            '  })();',
            '});'
        ];
        return lines.join('\\n') + '\\n</' + 'script>';
    }
```

---

## 7️⃣ בדיקת copyPreviewCode (העתקה עם צבע נבחר)

### בדיקה:
```javascript
const hasCopyPreview = content.includes('copy-preview-code') || 
                       content.includes('copyPreviewCode');
```

### 🔧 תיקון - הוסף פונקציה:
```javascript
    // === העתקת קוד מתצוגה מקדימה עם צבע ===
    function copyPreviewCode(color) {
        // אסוף CSS
        let styles = '';
        document.querySelectorAll('style').forEach(style => {
            if (style.textContent.includes(PREFIX)) {
                // החלף את הצבע הראשי בצבע הנבחר
                styles += style.textContent.replace(/#1e5490/gi, color);
            }
        });
        
        // קבל את המחשבון מהתצוגה המקדימה
        const previewArea = container.querySelector('[class*="preview-area"]');
        const calculator = previewArea ? 
            previewArea.querySelector('[class*="calculator"]') : 
            container.querySelector('[class*="calculator"]');
        
        if (!calculator) {
            alert('שגיאה: לא נמצא מחשבון');
            return;
        }
        
        const calcClone = calculator.cloneNode(true);
        
        // בנה קוד
        let code = '<style>\n' + styles + '\n</style>\n\n';
        code += '<div class="' + PREFIX + 'wrapper">\n' + calcClone.outerHTML + '\n</div>\n\n';
        code += '<p style="text-align:center; font-size:0.9em; margin-top:20px; color:#666;">';
        code += 'מחשבון זה פותח על ידי <a href="https://loan-israel.co.il/" target="_blank" rel="nofollow noopener" style="color:' + color + '; text-decoration:underline;">רק תבקש פיננסים</a></p>\n\n';
        code += getEmbedScript().replace(/#1e5490/gi, color);
        
        navigator.clipboard.writeText(code).then(() => {
            alert('✅ הקוד הועתק עם הצבע הנבחר!');
        });
    }
```

---

## 8️⃣ בדיקת Event Handlers לאזור הטמעה

### בדיקה שיש טיפול ב-actions:
```javascript
// בתוך ה-event delegation צריך להיות:
const requiredActions = [
    'preview-color',      // לחיצה על צבע
    'copy-embed-code',    // העתקת קוד בסיסי
    'copy-preview-code',  // העתקה מתצוגה מקדימה
    'scroll-to-embed'     // גלילה לאזור הטמעה
];
```

### 🔧 תיקון - הוסף לתוך Event Delegation:
```javascript
    // בתוך container.addEventListener('click', ...)
    case 'preview-color':
        showPreview(action.dataset.color, action.dataset.name);
        break;
    
    case 'copy-embed-code':
        copyEmbedCode();
        break;
    
    case 'copy-preview-code':
        copyPreviewCode(action.dataset.color);
        break;
    
    case 'scroll-to-embed':
        const embedSection = container.querySelector('[class*="embed"]');
        if (embedSection) {
            embedSection.scrollIntoView({ behavior: 'smooth' });
        }
        break;
```

---

# 🧪 בדיקה בדפדפן - קוד להדבקה בקונסול

```javascript
// === בדיקת אזור הטמעה מלאה + תוכן ===
(async function() {
    console.log('🔍 === בדיקת אזור הטמעה מלאה ===\n');
    const errors = [];
    const successes = [];
    const warnings = [];
    const wait = (ms) => new Promise(r => setTimeout(r, ms));
    
    // === 0. בדיקת תוכן אזור ההטמעה ===
    console.log('📝 בדיקת תוכן אזור ההטמעה:');
    
    const embedSection = document.querySelector('[class*="embed-section"], [id*="embed"]');
    if (!embedSection) {
        errors.push('אין אזור הטמעה!');
    } else {
        const embedText = embedSection.textContent;
        const embedHTML = embedSection.innerHTML;
        
        // זהה את סוג המחשבון מהכותרת הראשית
        const mainTitle = document.querySelector('h1');
        const titleText = mainTitle ? mainTitle.textContent : '';
        console.log(`  📌 כותרת ראשית: ${titleText}`);
        
        // מילות מפתח לפי סוג מחשבון
        const calculatorTypes = {
            'ריבית דריבית': { keywords: ['ריבית דריבית', 'ערך עתידי', 'חיסכון'], wrong: ['משכנתא', 'הלוואה', 'ברוטו נטו'] },
            'ברוטו נטו': { keywords: ['ברוטו נטו', 'שכר', 'מס הכנסה'], wrong: ['משכנתא', 'ריבית דריבית'] },
            'משכנתא': { keywords: ['משכנתא', 'דירה', 'החזר חודשי'], wrong: ['ברוטו נטו', 'ריבית דריבית'] },
            'חיסכון': { keywords: ['חיסכון', 'הפקדה', 'ערך עתידי'], wrong: ['משכנתא', 'הלוואה'] },
            'הלוואות': { keywords: ['הלוואה', 'ריבית', 'החזר'], wrong: ['משכנתא', 'ברוטו נטו'] },
            'פנסיה': { keywords: ['פנסיה', 'גיל פרישה', 'קצבה'], wrong: ['משכנתא', 'הלוואה'] },
            'מס רכישה': { keywords: ['מס רכישה', 'דירה', 'נדלן'], wrong: ['ברוטו נטו', 'הלוואה'] },
            'עלות מעסיק': { keywords: ['עלות מעסיק', 'שכר עובד', 'העסקה'], wrong: ['משכנתא', 'ריבית דריבית'] }
        };
        
        // זהה סוג המחשבון
        let detectedType = null;
        for (const [type, data] of Object.entries(calculatorTypes)) {
            if (titleText.includes(type) || embedText.includes(type)) {
                detectedType = type;
                break;
            }
        }
        
        if (detectedType) {
            console.log(`  ✅ סוג מחשבון מזוהה: ${detectedType}`);
            
            const typeData = calculatorTypes[detectedType];
            
            // בדוק מילות מפתח נכונות
            const foundKeywords = typeData.keywords.filter(kw => embedText.includes(kw));
            console.log(`  📊 מילות מפתח נמצאו: ${foundKeywords.length}/${typeData.keywords.length}`);
            
            if (foundKeywords.length >= typeData.keywords.length / 2) {
                console.log(`  ✅ מילות מפתח תואמות`);
                successes.push('מילות מפתח תואמות');
            } else {
                warnings.push(`חסרות מילות מפתח: ${typeData.keywords.filter(kw => !embedText.includes(kw)).join(', ')}`);
            }
            
            // בדוק תוכן שגוי
            const foundWrong = typeData.wrong.filter(term => {
                // ספור כמה פעמים מופיע
                const count = (embedText.match(new RegExp(term, 'gi')) || []).length;
                return count > 2; // מותר אזכור אחד או שניים
            });
            
            if (foundWrong.length > 0) {
                console.error(`  ❌ תוכן שגוי נמצא: ${foundWrong.join(', ')}`);
                errors.push(`תוכן ממחשבון אחר: ${foundWrong.join(', ')}`);
            } else {
                console.log(`  ✅ אין תוכן שגוי`);
                successes.push('אין תוכן ממחשבון אחר');
            }
        } else {
            warnings.push('לא זוהה סוג מחשבון - בדיקה ידנית נדרשת');
        }
        
        // בדוק מספר טאבים
        const tabButtons = document.querySelectorAll('[data-action="switch-tab"]');
        const tabCountInText = embedText.match(/(\d+)\s*טאב/);
        if (tabCountInText) {
            const mentioned = parseInt(tabCountInText[1]);
            if (mentioned === tabButtons.length) {
                console.log(`  ✅ מספר טאבים תואם: ${mentioned}`);
                successes.push(`מספר טאבים נכון (${mentioned})`);
            } else {
                console.error(`  ❌ מספר טאבים לא תואם! כתוב: ${mentioned}, בפועל: ${tabButtons.length}`);
                errors.push(`מספר טאבים שגוי (כתוב ${mentioned}, יש ${tabButtons.length})`);
            }
        }
        
        // בדוק שם המחשבון מופיע בכותרת אזור ההטמעה
        const embedTitle = embedSection.querySelector('h2');
        if (embedTitle && detectedType && embedTitle.textContent.includes(detectedType)) {
            console.log(`  ✅ שם המחשבון בכותרת ההטמעה`);
            successes.push('שם המחשבון בכותרת');
        } else if (embedTitle) {
            warnings.push('שם המחשבון לא מופיע בכותרת אזור ההטמעה');
        }
        
        // בדוק ערך המחשבון
        const valueMatch = embedText.match(/₪[\d,]+\s*(?:בפיתוח|שווי)/);
        if (valueMatch) {
            console.log(`  ✅ ערך המחשבון מוזכר: ${valueMatch[0]}`);
            successes.push('ערך המחשבון מוזכר');
        } else {
            warnings.push('ערך המחשבון לא מוזכר');
        }
    }
    
    console.log('');
    
    // 1. בדיקת כפתורי צבע
    const colorBtns = document.querySelectorAll('[data-action="preview-color"]');
    console.log(`🎨 כפתורי צבע: ${colorBtns.length}`);
    
    if (colorBtns.length < 5) {
        errors.push('חסרים כפתורי צבע (צריך לפחות 10)');
    } else {
        successes.push(`${colorBtns.length} כפתורי צבע`);
    }
    
    // 2. בדיקת החלפת צבעים
    console.log('\n🎨 בדיקת החלפת צבעים:');
    let colorChangeWorks = true;
    let previousPreviewHTML = '';
    
    for (let i = 0; i < Math.min(colorBtns.length, 3); i++) {
        const btn = colorBtns[i];
        const color = btn.dataset.color;
        const name = btn.dataset.name || `צבע ${i+1}`;
        
        console.log(`  🖱️ לוחץ על ${name} (${color})...`);
        btn.click();
        await wait(500);
        
        // בדוק שיש תצוגה מקדימה
        const preview = document.querySelector('[class*="preview-area"], [class*="preview-container"]');
        if (!preview) {
            console.error(`  ❌ אין תצוגה מקדימה!`);
            errors.push(`${name}: אין תצוגה מקדימה`);
            colorChangeWorks = false;
            continue;
        }
        
        // בדוק שהתוכן השתנה
        if (preview.innerHTML === previousPreviewHTML && i > 0) {
            console.warn(`  ⚠️ התצוגה לא השתנתה`);
        } else {
            console.log(`  ✅ תצוגה מקדימה הופיעה`);
        }
        
        // בדוק שהצבע מופיע
        if (preview.innerHTML.includes(color) || preview.outerHTML.includes(color)) {
            console.log(`  ✅ צבע ${color} מופיע בתצוגה`);
            successes.push(`${name}: צבע הוחל`);
        } else {
            console.warn(`  ⚠️ צבע ${color} לא נמצא בתצוגה`);
        }
        
        // בדוק טאבים בתצוגה
        const previewTabs = preview.querySelectorAll('[data-action="switch-tab"]');
        console.log(`  📊 טאבים בתצוגה: ${previewTabs.length}`);
        
        if (previewTabs.length > 0) {
            // לחץ על טאב שני
            if (previewTabs[1]) {
                previewTabs[1].click();
                await wait(200);
                if (previewTabs[1].classList.contains('active')) {
                    console.log(`  ✅ טאבים עובדים בתצוגה`);
                    successes.push(`${name}: טאבים עובדים`);
                } else {
                    console.error(`  ❌ טאבים לא עובדים!`);
                    errors.push(`${name}: טאבים לא עובדים`);
                }
            }
        }
        
        // בדוק סליידרים בתצוגה
        const previewSliders = preview.querySelectorAll('input[type="range"]');
        if (previewSliders.length > 0) {
            const slider = previewSliders[0];
            const oldVal = slider.value;
            slider.value = parseInt(slider.max) - 1000;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
            console.log(`  ✅ סליידרים עובדים בתצוגה`);
            slider.value = oldVal;
        }
        
        // בדוק כפתור העתקה
        const copyBtn = preview.querySelector('[data-action="copy-preview-code"]');
        if (copyBtn) {
            console.log(`  ✅ כפתור העתקה קיים`);
            successes.push(`${name}: כפתור העתקה`);
        } else {
            console.error(`  ❌ חסר כפתור העתקה בתצוגה!`);
            errors.push(`${name}: חסר כפתור העתקה`);
        }
        
        previousPreviewHTML = preview.innerHTML;
    }
    
    // 3. בדיקת פונקציות
    console.log('\n📋 בדיקת פונקציות:');
    const hasGetEmbed = document.body.innerHTML.includes('getEmbedScript');
    const hasCopyEmbed = document.body.innerHTML.includes('copyEmbedCode');
    const hasShowPreview = document.body.innerHTML.includes('showPreview');
    
    console.log(`  getEmbedScript: ${hasGetEmbed ? '✅' : '❌'}`);
    console.log(`  copyEmbedCode: ${hasCopyEmbed ? '✅' : '❌'}`);
    console.log(`  showPreview: ${hasShowPreview ? '✅' : '❌'}`);
    
    if (!hasGetEmbed) errors.push('חסר getEmbedScript');
    if (!hasCopyEmbed) errors.push('חסר copyEmbedCode');
    if (!hasShowPreview) errors.push('חסר showPreview');
    
    // 4. בדיקת קרדיט
    console.log('\n🔗 בדיקת קרדיט:');
    const hasCredit = document.body.innerHTML.includes('loan-israel.co.il');
    const hasNofollow = document.body.innerHTML.includes('nofollow');
    console.log(`  קרדיט: ${hasCredit ? '✅' : '❌'}`);
    console.log(`  nofollow: ${hasNofollow ? '✅' : '❌'}`);
    
    // סיכום
    console.log('\n' + '='.repeat(50));
    console.log('📊 סיכום:');
    console.log(`  ✅ הצלחות: ${successes.length}`);
    console.log(`  ⚠️ אזהרות: ${warnings.length}`);
    console.log(`  ❌ שגיאות: ${errors.length}`);
    
    if (warnings.length > 0) {
        console.log('\n⚠️ אזהרות:');
        warnings.forEach(w => console.warn('  ' + w));
    }
    
    if (errors.length > 0) {
        console.log('\n🚨 שגיאות:');
        errors.forEach(e => console.error('  ' + e));
    } else {
        console.log('\n🎉 אזור ההטמעה תקין!');
    }
    
    return { errors, warnings, successes };
})();
```

---

# 🤖 הוראות לסוכן AI - בדוק ותקן אזור הטמעה

## שלב 0: זהה את סוג המחשבון
מתוך הכותרת הראשית או ה-prefix, זהה את סוג המחשבון:
- `compound-int` = ריבית דריבית
- `salary` = ברוטו נטו
- `mortgage` = משכנתא
- `savings` = חיסכון
- `loan` = הלוואות
- `pension` = פנסיה
- `tax` = מס רכישה

## שלב 1: קרא את הקובץ
```
קרא את: מחשבונים חדשים/[שם].html
```

## שלב 2: בדוק ותקן תוכן

### ❌ אם התוכן לא מתאים למחשבון:
החלף את התוכן באזור ההטמעה לפי סוג המחשבון:

| אלמנט | מה לבדוק | מה לתקן |
|-------|---------|---------|
| כותרת H2 | שם המחשבון | "רוצים להטמיע את **[שם המחשבון]** באתר שלכם?" |
| תיאור ערך | סכום ומספר טאבים | "מחשבון עם **[X] טאבים**... שווי **₪[X]** בפיתוח" |
| מילות מפתח | רלוונטיות למחשבון | "מילות מפתח כמו **[מילות מפתח רלוונטיות]**" |
| דפים מומלצים | רלוונטיים | "הוסיפו בדפים כמו **[דפים רלוונטיים]**" |

### ❌ אם יש תוכן ממחשבון אחר:
מצא והחלף מונחים לא רלוונטיים:
- אם זה מחשבון ריבית דריבית אבל כתוב "משכנתא" - תקן!
- אם זה מחשבון ברוטו נטו אבל כתוב "הלוואה" - תקן!

### ❌ אם מספר הטאבים שגוי:
ספור את מספר הטאבים בפועל ועדכן את הטקסט.

## שלב 3: בדוק ותקן פונקציונליות

### ❌ אם חסר `getEmbedScript`:
הוסף את הפונקציה המלאה (ראה סעיף 6)

### ❌ אם חסר `showPreview`:
הוסף את הפונקציה (ראה סעיף 3)

### ❌ אם חסרים כפתורי צבע:
הוסף את בורר הצבעים (ראה סעיף 2)

### ❌ אם חסר `initPreviewCalculator`:
הוסף את הפונקציה (ראה סעיף 4)

### ❌ אם `copyEmbedCode` לא כולל CSS/getEmbedScript:
תקן את הפונקציה (ראה סעיף 5)

### ❌ אם סגירת script לא בטוחה:
החלף `'</script>'` ב-`'</' + 'script>'`

## שלב 4: שמור ודווח

```markdown
## 📋 דוח תיקון אזור הטמעה

### 📝 בדיקת תוכן:
- שם המחשבון בכותרת: ✅/❌
- מילות מפתח רלוונטיות: ✅/❌
- מספר טאבים נכון: ✅/❌
- אין תוכן ממחשבון אחר: ✅/❌

### ✅ תיקונים שבוצעו:
1. [מה תוקן]

### 📊 סטטוס פונקציונליות:
- כפתורי צבע: ✅/❌ (כמות)
- החלפת צבעים: ✅/❌
- תצוגה מקדימה: ✅/❌
- טאבים בתצוגה: ✅/❌
- סליידרים בתצוגה: ✅/❌
- העתקת קוד: ✅/❌
- CSS בהעתקה: ✅/❌
- JS בהעתקה: ✅/❌
- קרדיט: ✅/❌
```

---

## 📋 דוגמאות לתוכן נכון לפי סוג מחשבון

### מחשבון ריבית דריבית:
```
כותרת: "מחשבון הריבית דריבית"
טאבים: 4
ערך: ₪15,000
מילות מפתח: "ריבית דריבית, חיסכון לטווח ארוך, השקעות, ערך עתידי"
דפים: "חיסכון ריבית דריבית, השקעות לטווח ארוך, תכנון פיננסי"
```

### מחשבון ברוטו נטו:
```
כותרת: "מחשבון ברוטו נטו"
טאבים: 3
ערך: ₪10,000
מילות מפתח: "שכר נטו, מס הכנסה, מדרגות מס, חישוב שכר"
דפים: "חישוב שכר, מדרגות מס 2025, מס הכנסה"
```

### מחשבון משכנתא:
```
כותרת: "מחשבון המשכנתא"
טאבים: 4
ערך: ₪18,000
מילות מפתח: "משכנתא, החזר חודשי, ריבית משכנתא, הלוואת דיור"
דפים: "רכישת דירה, הלוואות דיור, משכנתא ראשונה"
```

### מחשבון מס רכישה:
```
כותרת: "מחשבון מס רכישה"
טאבים: 3
ערך: ₪10,000
מילות מפתח: "מס רכישה, רכישת דירה, דירה יחידה, מדרגות מס"
דפים: "קניית דירה, מיסוי נדלן, דירה ראשונה"
```

---

**נוצר על ידי: Cursor AI**  
**גרסה: 2.0**  
**מיקוד: אזור הטמעה + בדיקת תוכן**

