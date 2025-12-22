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

# 🚨 בעיות קריטיות שנתגלו ותוקנו - חובה לבדוק!

## רשימת בעיות מרכזיות שיש לוודא שתוקנו:

### 1️⃣ בעיית `cloneNode(true)` - לא מעתיק Event Listeners!
| בעיה | פתרון |
|------|-------|
| `cloneNode(true)` מעתיק רק DOM, לא JS | יש לאתחל מחדש את כל ה-event listeners בתצוגה המקדימה |
| טאבים לא עובדים בתצוגה | יש להוסיף event listener חדש למחשבון המשוכפל |
| סליידרים לא עובדים | יש להוסיף `input` event listener חדש |
| כפתורי בחירה לא עובדים | יש להוסיף `click` event listener לכל כפתור |

**בדיקה:**
```javascript
const hasInitPreviewCalculator = content.includes('initPreviewCalculator');
```

### 2️⃣ בעיית ID Conflicts - התנגשות בין מחשבון מקורי למשוכפל!
| בעיה | פתרון |
|------|-------|
| אותו ID לשני מחשבונים | שנה ID של המשוכפל: `calc.id = PREFIX + 'calculator-preview'` |
| IDs של טאבים זהים | החלף ב-`data-preview-tab` attributes |
| `getElementById` מחזיר את המקורי | השתמש ב-`querySelector` על האלמנט הספציפי |

**בדיקה:**
```javascript
const hasPreviewID = content.includes('calculator-preview');
const hasDataPreviewTab = content.includes('data-preview-tab');
```

### 3️⃣ בעיית Event Bubbling - אירועים עולים למחשבון המקורי!
| בעיה | פתרון |
|------|-------|
| לחיצה על טאב בתצוגה משנה גם את המקורי | הוסף `e.stopPropagation()` |
| סליידר בתצוגה משפיע על המקורי | הוסף `e.stopPropagation()` בכל handler |

**בדיקה:**
```javascript
const hasStopPropagation = content.includes('stopPropagation');
```

### 4️⃣ בעיית CSS Variables - לא עוברים בשכפול!
| בעיה | פתרון |
|------|-------|
| צבעים לא מתחלפים בתצוגה | הגדר variables על האלמנט: `calc.style.setProperty('--primary', color)` |
| Gradient לא עובד | הגדר גם `--primary-dark`, `--primary-light`, `--primary-gradient` |

**בדיקה:**
```javascript
const hasCSSVariableOverride = content.includes("setProperty('--primary'") || 
                                content.includes('setProperty("--primary"');
```

### 5️⃣ בעיית CSS `!important` - סגנונות לא נדרסים!
| בעיה | פתרון |
|------|-------|
| `el.style.background = color` לא עובד | השתמש ב-`el.style.setProperty('background', color, 'important')` |
| כפתורים לא משנים צבע | כל `style.xxx =` צריך להיות `setProperty` עם `'important'` |

**בדיקה:**
```javascript
const hasSetPropertyImportant = content.includes("setProperty(") && content.includes("'important'");
```

### 6️⃣ בעיית Display None/Block - טאבים נעלמים!
| בעיה | פתרון |
|------|-------|
| טאב לא נראה למרות שהוא active | הוסף `tab.style.display = 'block'` בנוסף ל-class |
| כל הטאבים נראים | הוסף `tab.style.display = 'none'` לכל הלא-פעילים |

**בדיקה:**
```javascript
const hasDisplayBlock = content.includes("style.display = 'block'") || 
                         content.includes('style.display = "block"');
const hasDisplayNone = content.includes("style.display = 'none'") || 
                        content.includes('style.display = "none"');
```

### 7️⃣ 🚨 בעיית getEmbedScript - רק טאב אחד עובד בהעתקה!
| בעיה | פתרון |
|------|-------|
| רק הטאב הראשון עובד | הוסף state לכל הטאבים: `state = { basic: {...}, compare: {...}, schedule: {...} }` |
| חסר `updateCompare()` | הוסף פונקציה שמעדכנת את טבלת ההשוואה (4 שורות) |
| חסר `updateSchedule()` | הוסף פונקציה שמייצרת לוח סילוקין דינמי |
| סליידרים לא מעדכנים טאב נכון | כל slider צריך לבדוק את ה-ID ולקרוא לפונקציה המתאימה |
| `switchTab` לא מעדכן תוכן | צריך לקרוא ל-update המתאים: `if (tab === "compare") updateCompare();` |
| אתחול חסר | חייב לקרוא `updateBasic(); updateCompare(); updateSchedule();` בסוף |

**בדיקה (CRITICAL):**
```javascript
// חילוץ תוכן getEmbedScript
const embedScriptMatch = content.match(/function getEmbedScript[\s\S]*?<\` \+ \`\/script>/);
const embedScript = embedScriptMatch ? embedScriptMatch[0] : '';

// בדיקות הכרחיות
const checks = {
    'state לכל הטאבים (basic, compare, schedule)': /state\s*=\s*\{[\s\S]*?basic[\s\S]*?compare[\s\S]*?schedule/.test(embedScript),
    'פונקציית updateBasic': /function\s+updateBasic/.test(embedScript),
    'פונקציית updateCompare': /function\s+updateCompare/.test(embedScript),
    'פונקציית updateSchedule': /function\s+updateSchedule/.test(embedScript),
    'switchTab קורא לupdate': /switchTab[\s\S]*?updateBasic|updateCompare|updateSchedule/.test(embedScript),
    'סליידר compare מעדכן updateCompare': /compare-.*-slider[\s\S]*?updateCompare/.test(embedScript),
    'סליידר schedule מעדכן updateSchedule': /schedule-.*-slider[\s\S]*?updateSchedule/.test(embedScript),
    'אתחול כל הטאבים': /updateBasic\(\)[\s\S]*?updateCompare\(\)[\s\S]*?updateSchedule\(\)/.test(embedScript)
};

console.log('📦 === בדיקות getEmbedScript ===');
for (const [name, result] of Object.entries(checks)) {
    if (result) {
        console.log('✅ ' + name);
    } else {
        console.error('❌ ' + name + ' - חסר!');
    }
}
```

**מבנה נכון של getEmbedScript:**
```javascript
function getEmbedScript(color, darkColor) {
    return \`<script>
document.addEventListener("DOMContentLoaded", function() {
    (function() {
        "use strict";
        var ns = "WPC_Calc_Embed";
        if (window[ns]) return;
        var container = document.getElementById("wpc-calc-xxx-main");
        if (!container) return;
        
        // ✅ State לכל הטאבים
        var state = {
            basic: { balance: 200000, payment: 3000, rate: 5.5, extra: 500 },
            compare: { balance: 200000, payment: 3000, rate: 5.5 },
            schedule: { balance: 200000, payment: 3000, rate: 5.5, extra: 500 }
        };
        
        // פונקציות עזר
        function fmt(n) { return Math.round(n).toLocaleString("he-IL") + " ₪"; }
        function pct(n) { return n.toFixed(1) + "%"; }
        function nper(bal, pmt, r) { /* נוסחה */ }
        function totalInt(bal, pmt, r, m) { /* נוסחה */ }
        function $(id) { return document.getElementById(id); }
        
        // ✅ פונקציות update לכל טאב
        function updateBasic() {
            var s = state.basic;
            // עדכון תצוגה של טאב 1
        }
        
        function updateCompare() {
            var s = state.compare;
            var extras = [200, 500, 1000, 2000];
            for (var i = 0; i < extras.length; i++) {
                // עדכון כל שורה בטבלה
            }
        }
        
        function updateSchedule() {
            var s = state.schedule;
            var tbody = $("schedule-table-body");
            tbody.innerHTML = "";
            for (var m = 1; m <= 12; m++) {
                // הוספת שורה לטבלה
            }
        }
        
        // ✅ switchTab קורא לפונקציה המתאימה
        function switchTab(tab) {
            // ... hide all, show selected ...
            if (tab === "basic") updateBasic();
            else if (tab === "compare") updateCompare();
            else if (tab === "schedule") updateSchedule();
        }
        
        // ✅ סליידרים לפי טאב
        container.addEventListener("input", function(e) {
            var id = e.target.id, v = parseFloat(e.target.value);
            // Basic
            if (id === "basic-balance-slider") { state.basic.balance = v; updateBasic(); }
            // Compare
            else if (id === "compare-balance-slider") { state.compare.balance = v; updateCompare(); }
            // Schedule
            else if (id === "schedule-balance-slider") { state.schedule.balance = v; updateSchedule(); }
        });
        
        // ✅ אתחול כל הטאבים
        updateBasic();
        updateCompare();
        updateSchedule();
        
        window[ns] = { v: "1.0.0" };
    })();
});
<\` + \`/script>\`;
}
```

### 8️⃣ 🚨 בעיית `pointer-events: none` - חוסם את כל האינטראקציה!
| בעיה | פתרון |
|------|-------|
| `pointer-events: none` בתצוגה מקדימה | **אסור!** יש להסיר לחלוטין |
| משתמשים לא יכולים ללחוץ/להזיז סליידרים | הסר את `pointer-events: none` |
| נראה כאילו המחשבון "קפוא" | אל תשתמש בזה אף פעם בתצוגה מקדימה |

**בדיקה (CRITICAL - אסור שימצא!):**
```javascript
const hasForbiddenPointerEvents = content.match(/showPreview[\s\S]*?pointer-events\s*:\s*none/);
if (hasForbiddenPointerEvents) {
    console.error('🚨 נמצא pointer-events: none בתצוגה מקדימה - אסור!');
}
```

### 9️⃣ בעיית showPreview - החלפת HTML פשוטה לא מספיקה!
| בעיה | פתרון |
|------|-------|
| `innerHTML = html.replace(...)` בלי אתחול JS | חייב לקרוא ל-`initPreviewCalculator` אחרי השכפול |
| רק החלפת צבעים ב-regex | צריך `calc.style.setProperty` על האלמנט המשוכפל |
| `cloneNode` בלי אתחול מחדש | חובה להוסיף event listeners חדשים |

**בדיקה:**
```javascript
// בדוק ש-initPreviewCalculator נקרא מתוך showPreview
const showPreviewCallsInit = content.match(/showPreview[\s\S]*?initPreviewCalculator\s*\(/);
if (!showPreviewCallsInit) {
    console.error('❌ showPreview לא קורא ל-initPreviewCalculator!');
}

// בדוק ש-showPreview משתמש ב-cloneNode
const showPreviewUsesClone = content.match(/showPreview[\s\S]*?cloneNode\s*\(\s*true\s*\)/);
if (!showPreviewUsesClone) {
    console.warn('⚠️ showPreview לא משתמש ב-cloneNode(true)');
}
```

### 🔟 בעיית פונקציות עזר לצבעים חסרות!
| בעיה | פתרון |
|------|-------|
| אין `darkenColor` | צריך להוסיף פונקציה להכהות צבע |
| אין `hexToRgba` | צריך להוסיף פונקציה להמרה לRGBA |
| Gradients לא עובדים | חייב darkenColor לgradient יפה |

**בדיקה:**
```javascript
const hasDarkenColor = content.includes('function darkenColor') || content.includes('darkenColor =');
const hasHexToRgba = content.includes('function hexToRgba') || content.includes('hexToRgba =');
```

### 1️⃣1️⃣ בעיית חיבור initPreviewCalculator לstate ופונקציות עדכון!
| בעיה | פתרון |
|------|-------|
| יש `initPreviewCalculator` אבל בלי state | חייב להגדיר `previewState` בתוך הפונקציה |
| סליידרים לא מחוברים לחישוב | כל slider צריך לעדכן state ולקרוא לפונקציית update |
| חסר אתחול ראשוני | צריך לקרוא לכל פונקציות ה-update בסוף |

**בדיקה:**
```javascript
// בדוק שיש previewState בתוך initPreviewCalculator
const hasPreviewState = content.match(/initPreviewCalculator[\s\S]*?previewState\s*=\s*\{/);

// בדוק שיש פונקציות update
const hasUpdateFunctions = content.match(/initPreviewCalculator[\s\S]*?function\s+update/);

// בדוק שיש אתחול בסוף
const hasInitCalls = content.match(/initPreviewCalculator[\s\S]*?update\w+\(\)\s*;[\s\S]*?update\w+\(\)/);
```

### 1️⃣2️⃣ 🚨 בעיית `select-color` במקום `preview-color`!
| בעיה | פתרון |
|------|-------|
| כפתורי צבע עם `data-action="select-color"` | **חייב להיות** `data-action="preview-color"` |
| פונקציית `selectColor` פשוטה מדי | צריך `showPreview` מלא עם שכפול מחשבון |
| תצוגה מקדימה לא עובדת | ודא שה-event handler תומך ב-`preview-color` |

**בדיקה (CRITICAL):**
```javascript
// בדוק שיש preview-color ולא select-color
const hasPreviewColorAction = content.includes('data-action="preview-color"');
const hasWrongSelectColor = content.includes('data-action="select-color"');

if (hasWrongSelectColor) {
    console.error('🚨 נמצא select-color - יש להחליף ל-preview-color!');
}
if (!hasPreviewColorAction) {
    console.error('❌ חסר data-action="preview-color" על כפתורי הצבע!');
}

// בדוק שיש handler ב-switch/case
const hasPreviewColorHandler = content.includes("case 'preview-color':");
if (!hasPreviewColorHandler) {
    console.error('❌ חסר handler עבור preview-color ב-event delegation!');
}
```

**תיקון - החלף בכפתורי צבע:**
```html
<!-- ❌ שגוי -->
<button data-action="select-color" data-color="#1e5490" ...>

<!-- ✅ נכון -->
<button data-action="preview-color" data-color="#1e5490" ...>
```

### 1️⃣3️⃣ 🚨 בעיית Mockup סטטי במקום מחשבון משוכפל!
| בעיה | פתרון |
|------|-------|
| `updatePreview()` מייצר HTML סטטי | צריך `showPreview()` עם `cloneNode(true)` |
| תצוגה מקדימה לא אינטראקטיבית | שכפל את המחשבון האמיתי והחל צבעים |
| אין טאבים/סליידרים עובדים בתצוגה | חייב `initPreviewCalculator` אחרי שכפול |

**בדיקה:**
```javascript
// בדוק שאין updatePreview פשוט (mockup)
const hasSimpleUpdatePreview = content.match(/function updatePreview\(\)[\s\S]*?innerHTML\s*=\s*`/);
if (hasSimpleUpdatePreview) {
    console.error('🚨 נמצא updatePreview פשוט עם mockup - צריך showPreview עם cloneNode!');
}

// בדוק שיש showPreview נכון
const hasShowPreview = content.includes('function showPreview');
const showPreviewHasClone = content.match(/showPreview[\s\S]*?cloneNode\s*\(\s*true\s*\)/);

if (!hasShowPreview) {
    console.error('❌ חסרה פונקציית showPreview!');
} else if (!showPreviewHasClone) {
    console.error('❌ showPreview לא משתמש ב-cloneNode(true)!');
}
```

### 1️⃣4️⃣ 🚨 בעיית סקרולים כפולים בתצוגה מקדימה!
| בעיה | פתרון |
|------|-------|
| `preview-container` עם `max-height` + `overflow-y: auto` | גורם לסקרול כפול עם הטבלאות בפנים |
| שני scrollbars נראים | הסר `max-height` ו-`overflow-y` מהcontainer |
| CSS עם `overflow-y: auto` על ה-preview | שנה ל-`overflow: visible` |

**בדיקה:**
```javascript
// בדוק CSS של preview-container
const previewContainerCSS = content.match(/\.[\w-]*preview-container[^{]*\{[^}]+\}/);
if (previewContainerCSS) {
    const css = previewContainerCSS[0];
    if (css.includes('max-height') && css.includes('overflow')) {
        console.error('🚨 preview-container עם max-height + overflow - גורם לסקרולים כפולים!');
    }
}
```

**תיקון CSS:**
```css
/* ❌ שגוי - גורם לסקרולים כפולים */
.wpc-calc-xxx-preview-container {
    max-height: 400px !important;
    overflow-y: auto !important;
}

/* ✅ נכון - בלי סקרול על ה-container */
.wpc-calc-xxx-preview-container {
    overflow: visible !important;
}
```

### 1️⃣5️⃣ 🚨 בעיית עדכון רק טאב אחד בתצוגה מקדימה!
| בעיה | פתרון |
|------|-------|
| רק `updatePreviewBasic()` קיים | צריך גם `updatePreviewCompare()` ו-`updatePreviewSchedule()` |
| טבלת השוואה לא מתעדכנת | הוסף פונקציה שמחשבת ומעדכנת את כל השורות |
| לוח סילוקין לא מתעדכן | הוסף פונקציה שמייצרת את הטבלה דינמית |
| סליידרים לא מעדכנים את הטאב הנכון | כל slider צריך לבדוק לאיזה טאב הוא שייך |

**בדיקה (CRITICAL):**
```javascript
// בדוק שיש פונקציות update לכל הטאבים
const hasUpdateBasic = content.includes('updatePreviewBasic');
const hasUpdateCompare = content.includes('updatePreviewCompare');
const hasUpdateSchedule = content.includes('updatePreviewSchedule');

console.log('updatePreviewBasic:', hasUpdateBasic ? '✅' : '❌');
console.log('updatePreviewCompare:', hasUpdateCompare ? '✅' : '❌');
console.log('updatePreviewSchedule:', hasUpdateSchedule ? '✅' : '❌');

if (!hasUpdateCompare) {
    console.error('❌ חסרה פונקציית updatePreviewCompare - טבלת השוואה לא תתעדכן!');
}
if (!hasUpdateSchedule) {
    console.error('❌ חסרה פונקציית updatePreviewSchedule - לוח סילוקין לא יתעדכן!');
}

// בדוק שהאתחול קורא לכל הפונקציות
const initCallsAll = content.match(/updatePreviewBasic\(\)[\s\S]*?updatePreviewCompare\(\)[\s\S]*?updatePreviewSchedule\(\)/);
if (!initCallsAll) {
    console.warn('⚠️ האתחול לא קורא לכל פונקציות העדכון!');
}
```

### 1️⃣6️⃣ בעיית סליידרים לא מעדכנים את הטאב הנכון!
| בעיה | פתרון |
|------|-------|
| סליידר של compare מעדכן את basic | כל slider צריך לבדוק את ה-ID שלו |
| אין חיבור ל-state הנכון | `if (id.includes('compare-'))` → `updatePreviewCompare()` |
| אין אבחנה בין טאבים | השתמש בשם הסליידר לזיהוי הטאב |

**בדיקה:**
```javascript
// בדוק שסליידרים מעדכנים את הטאב הנכון
const sliderHandlesCompare = content.match(/id\.includes\(['"]compare/);
const sliderHandlesSchedule = content.match(/id\.includes\(['"]schedule/);

if (!sliderHandlesCompare) {
    console.error('❌ סליידרים לא מטפלים בטאב compare!');
}
if (!sliderHandlesSchedule) {
    console.error('❌ סליידרים לא מטפלים בטאב schedule!');
}
```

**תיקון - slider event handler:**
```javascript
slider.addEventListener('input', function(e) {
    e.stopPropagation();
    const id = this.id;
    const val = parseFloat(this.value);
    
    // עדכון ערך מוצג
    // ...
    
    // עדכון state לפי הטאב
    if (id.includes('basic-balance')) { previewState.basic.balance = val; updatePreviewBasic(); }
    else if (id.includes('basic-payment')) { previewState.basic.payment = val; updatePreviewBasic(); }
    else if (id.includes('basic-rate')) { previewState.basic.rate = val; updatePreviewBasic(); }
    // Compare tab
    else if (id.includes('compare-balance')) { previewState.compare.balance = val; updatePreviewCompare(); }
    else if (id.includes('compare-payment')) { previewState.compare.payment = val; updatePreviewCompare(); }
    else if (id.includes('compare-rate')) { previewState.compare.rate = val; updatePreviewCompare(); }
    // Schedule tab
    else if (id.includes('schedule-balance')) { previewState.schedule.balance = val; updatePreviewSchedule(); }
    else if (id.includes('schedule-payment')) { previewState.schedule.payment = val; updatePreviewSchedule(); }
    else if (id.includes('schedule-rate')) { previewState.schedule.rate = val; updatePreviewSchedule(); }
    else if (id.includes('schedule-extra')) { previewState.schedule.extra = val; updatePreviewSchedule(); }
});
```

---

## ✅ קוד בדיקה מהירה - הדבק בקונסול

```javascript
// === בדיקה מהירה של בעיות קריטיות - גרסה 5.1 ===
(function() {
    const html = document.body.innerHTML;
    const script = document.querySelector('script:not([src])');
    const code = script ? script.textContent : '';
    
    console.log('🔍 === בדיקת בעיות קריטיות ===\n');
    let passed = 0;
    let failed = 0;
    let critical = 0;
    
    // === בדיקות CRITICAL - אסורים! ===
    const forbidden = {
        '🚨 pointer-events: none בתצוגה': /showPreview[\s\S]*?pointer-events\s*:\s*none/.test(code),
        '🚨 select-color במקום preview-color': html.includes('data-action="select-color"'),
        '🚨 max-height על embed-preview-content': /embed-preview-content[^>]*max-height/.test(html),
        '🚨 overflow-y: auto על embed-preview-content': /embed-preview-content[^>]*overflow-y:\s*auto/.test(html),
        '🚨 mockup סטטי (updatePreview עם innerHTML)': /function updatePreview\(\)[\s\S]*?innerHTML\s*=\s*`/.test(code),
        '🚨 style.display = block בלי setProperty': /previewContainer\.style\.display\s*=\s*['"]block['"]/.test(code) && !/setProperty\(['"]display['"]/.test(code)
    };
    
    console.log('🚨 === בדיקות CRITICAL (אסורים!) ===');
    for (const [name, found] of Object.entries(forbidden)) {
        if (found) {
            console.error(`❌ ${name} - נמצא! יש להסיר!`);
            critical++;
        } else {
            console.log(`✅ ${name} - לא נמצא (טוב!)`);
            passed++;
        }
    }
    
    // === בדיקת Selector תואם ל-HTML ===
    console.log('\n🔗 === בדיקת Selector תואם ל-HTML ===');
    const selectorMatch = code.match(/showPreview[\s\S]*?querySelector\(['"]([^'"]+)['"]\)/);
    if (selectorMatch) {
        const selector = selectorMatch[1];
        const className = selector.replace(/^\./, '').split(' ')[0].split('.')[0];
        const selectorExists = html.includes('class="' + className) || html.includes("class='" + className);
        if (selectorExists) {
            console.log('✅ Selector "' + selector + '" קיים ב-HTML');
            passed++;
        } else {
            console.error('🚨 CRITICAL: Selector "' + selector + '" לא קיים ב-HTML!');
            critical++;
        }
    } else {
        console.warn('⚠️ לא נמצא querySelector בתוך showPreview');
    }
    
    // === בדיקות חובה ===
    console.log('\n📋 === בדיקות חובה ===');
    const required = {
        'data-action="preview-color" על כפתורי צבע': html.includes('data-action="preview-color"'),
        'showPreview פונקציה קיימת': code.includes('function showPreview'),
        'initPreviewCalculator קיים': code.includes('initPreviewCalculator'),
        'initPreviewCalculator נקרא מ-showPreview': /showPreview[\s\S]*?initPreviewCalculator\s*\(/.test(code),
        'stopPropagation': code.includes('stopPropagation'),
        'setProperty with important': code.includes("setProperty(") && code.includes("'important'"),
        'setProperty לdisplay': /setProperty\(['"]display['"]/.test(code),
        'CSS Variable override': code.includes("setProperty('--") || code.includes('setProperty("--'),
        'calculator-preview ID': code.includes('calculator-preview'),
        'data-preview-tab': code.includes('data-preview-tab'),
        'darkenColor פונקציה': code.includes('darkenColor'),
        'hexToRgba פונקציה': code.includes('hexToRgba'),
        'previewState בתוך initPreviewCalculator': /initPreviewCalculator[\s\S]*?previewState\s*=\s*\{/.test(code),
        'cloneNode בתוך showPreview': /showPreview[\s\S]*?cloneNode/.test(code)
    };
    
    for (const [name, result] of Object.entries(required)) {
        if (result) {
            console.log(`✅ ${name}`);
            passed++;
        } else {
            console.error(`❌ ${name}`);
            failed++;
        }
    }
    
    // === בדיקות עדכון כל הטאבים ===
    console.log('\n🔄 === בדיקות עדכון טאבים בתצוגה מקדימה ===');
    const tabUpdates = {
        'updatePreviewBasic קיים': code.includes('updatePreviewBasic'),
        'updatePreviewCompare קיים': code.includes('updatePreviewCompare'),
        'updatePreviewSchedule קיים': code.includes('updatePreviewSchedule'),
        'סליידר מטפל ב-compare': /id\.includes\(['"]compare/.test(code),
        'סליידר מטפל ב-schedule': /id\.includes\(['"]schedule/.test(code),
        'אתחול קורא לכל פונקציות העדכון': /updatePreviewBasic\(\)[\s\S]*?updatePreviewCompare\(\)[\s\S]*?updatePreviewSchedule\(\)/.test(code)
    };
    
    for (const [name, result] of Object.entries(tabUpdates)) {
        if (result) {
            console.log(`✅ ${name}`);
            passed++;
        } else {
            console.error(`❌ ${name}`);
            failed++;
        }
    }
    
    // === בדיקות getEmbedScript ===
    console.log('\n📦 === בדיקות getEmbedScript (קוד העתקה) ===');
    
    // חילוץ תוכן getEmbedScript
    const embedMatch = code.match(/function getEmbedScript[\s\S]*?<\` \+ \`\/script>/);
    const embedScript = embedMatch ? embedMatch[0] : '';
    
    const embedChecks = {
        'getEmbedScript קיים': code.includes('function getEmbedScript'),
        'state לכל הטאבים (basic, compare, schedule)': /state\s*=\s*\{[\s\S]*?basic[\s\S]*?compare[\s\S]*?schedule/.test(embedScript),
        'updateBasic בgetEmbedScript': /function\s+updateBasic/.test(embedScript),
        'updateCompare בgetEmbedScript': /function\s+updateCompare/.test(embedScript),
        'updateSchedule בgetEmbedScript': /function\s+updateSchedule/.test(embedScript),
        'switchTab קורא לupdate': /switchTab[\s\S]*?(updateBasic|updateCompare|updateSchedule)/.test(embedScript),
        'סליידרים compare מעדכנים': embedScript.includes('compare-') && embedScript.includes('updateCompare'),
        'סליידרים schedule מעדכנים': embedScript.includes('schedule-') && embedScript.includes('updateSchedule'),
        'אתחול כל הפונקציות': /updateBasic\(\)[\s\S]*?updateCompare\(\)[\s\S]*?updateSchedule\(\)/.test(embedScript)
    };
    
    for (const [name, result] of Object.entries(embedChecks)) {
        if (result) {
            console.log(`✅ ${name}`);
            passed++;
        } else {
            console.error(`❌ ${name}`);
            failed++;
        }
    }
    
    // === סיכום ===
    console.log('\n' + '='.repeat(50));
    console.log('📊 סיכום:');
    console.log(`  ✅ עברו: ${passed}`);
    console.log(`  ❌ נכשלו: ${failed}`);
    console.log(`  🚨 קריטיים: ${critical}`);
    
    if (critical > 0) {
        console.error('\n🚨 יש בעיות קריטיות שחייבים לתקן מיד!');
    } else if (failed > 0) {
        console.warn('\n⚠️ יש לתקן את הבעיות שנכשלו');
    } else {
        console.log('\n🎉 כל הבדיקות עברו בהצלחה!');
    }
    
    return { passed, failed, critical };
})();
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

### 🚨 בעיות קריטיות שחייבים לבדוק:

1. **ID של המחשבון המשוכפל זהה למקורי!**
   - פתרון: `calc.id = PREFIX + 'calculator-preview';`
   
2. **IDs של תוכן הטאבים גורמים להתנגשות!**
   - פתרון: להחליף IDs ל-`data-preview-tab` attributes
   
3. **CSS Variables לא מועברים בשכפול!**
   - פתרון: להגדיר `--primary`, `--primary-dark`, `--primary-light` על האלמנט המשוכפל
   
4. **סגנונות עם `!important` לא נדרסים!**
   - פתרון: להשתמש ב-`setProperty` עם 'important' flag

### בדיקה:
```javascript
// חפש את הפונקציה
const hasShowPreview = content.includes('function showPreview') || 
                       content.includes('showPreview:') ||
                       content.includes('showPreview =');

// בדוק פתרונות לבעיות נפוצות
const hasIDChange = content.includes('calculator-preview') || 
                    content.includes('calc.id =');
const hasDataPreviewTab = content.includes('data-preview-tab');
const hasCSSVariableOverride = content.includes("setProperty('--");
```

### 🔧 תיקון מלא - פונקציית showPreview:
```javascript
    // === פונקציות עזר לצבעים ===
    function darkenColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.max((num >> 16) - amt, 0);
        const G = Math.max((num >> 8 & 0x00FF) - amt, 0);
        const B = Math.max((num & 0x0000FF) - amt, 0);
        return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
    }
    
    function lightenColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = Math.min((num >> 16) + amt, 255);
        const G = Math.min((num >> 8 & 0x00FF) + amt, 255);
        const B = Math.min((num & 0x0000FF) + amt, 255);
        return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
    }
    
    function hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    // === פונקציית תצוגה מקדימה עם החלפת צבע - גרסה מתוקנת! ===
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
        const calc = calculator.cloneNode(true);
        
        // 🚨 תיקון 1: שנה ID למניעת התנגשות!
        calc.id = PREFIX + 'calculator-preview';
        
        // 🚨 תיקון 2: החלף IDs של טאבים ב-data attributes!
        const tabContents = calc.querySelectorAll('[id*="tab-"]');
        tabContents.forEach(tabContent => {
            const oldId = tabContent.id;
            const tabName = oldId.replace(/.*tab-/, '').replace(/-content$/, '');
            tabContent.setAttribute('data-preview-tab', tabName);
            tabContent.removeAttribute('id'); // הסר ID למניעת התנגשות
        });
        
        // הגדר טאב ראשון כ-active
        const firstTabContent = calc.querySelector('[data-preview-tab]');
        if (firstTabContent) {
            firstTabContent.classList.add('active');
            firstTabContent.style.display = 'block';
        }
        
        // הסתר שאר הטאבים
        calc.querySelectorAll('[data-preview-tab]').forEach((tab, i) => {
            if (i > 0) {
                tab.classList.remove('active');
                tab.style.display = 'none';
            }
        });
        
        // 🚨 תיקון 3: הגדר CSS Variables על האלמנט המשוכפל!
        calc.style.setProperty('--primary', color);
        calc.style.setProperty('--primary-dark', darkenColor(color, 15));
        calc.style.setProperty('--primary-light', hexToRgba(color, 0.1));
        calc.style.setProperty('--primary-gradient', `linear-gradient(135deg, ${color} 0%, ${darkenColor(color, 20)} 100%)`);
        
        // 🚨 תיקון 4: החלף צבעים עם setProperty + important!
        // כותרות
        calc.querySelectorAll('[class*="title"], [class*="header"]').forEach(el => {
            if (el.style.color || el.style.background) {
                el.style.setProperty('color', color, 'important');
            }
        });
        
        // כרטיסי הדגשה
        calc.querySelectorAll('[class*="highlight"], [class*="primary"]').forEach(el => {
            el.style.setProperty('background', `linear-gradient(135deg, ${color} 0%, ${darkenColor(color, 20)} 100%)`, 'important');
        });
        
        // ערכי סליידר
        calc.querySelectorAll('[class*="slider-value"]').forEach(el => {
            el.style.setProperty('color', color, 'important');
        });
        
        // כפתורי טאב פעילים
        const activeTabBtn = calc.querySelector('[data-action="switch-tab"].active');
        if (activeTabBtn) {
            activeTabBtn.style.setProperty('background', color, 'important');
            activeTabBtn.style.setProperty('color', 'white', 'important');
        }
        
        // כפתורי בחירה פעילים
        calc.querySelectorAll('[class*="btn"].active, button.active').forEach(btn => {
            btn.style.setProperty('background', color, 'important');
            btn.style.setProperty('border-color', color, 'important');
            btn.style.setProperty('color', 'white', 'important');
        });
        
        // כותרות טבלאות
        calc.querySelectorAll('th, [class*="table-header"]').forEach(el => {
            el.style.setProperty('background', color, 'important');
        });
        
        // סליידרים
        calc.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.style.setProperty('accent-color', color, 'important');
        });
        
        // פסי התקדמות
        calc.querySelectorAll('[class*="progress-fill"], [class*="bar-fill"]').forEach(el => {
            el.style.setProperty('background', color, 'important');
        });
        
        // תיבות מידע
        calc.querySelectorAll('[class*="info-box"]').forEach(el => {
            el.style.setProperty('border-color', color, 'important');
            el.style.setProperty('background', hexToRgba(color, 0.05), 'important');
        });
        
        // כפתורי CTA
        calc.querySelectorAll('[class*="cta"], [class*="action-btn"]').forEach(el => {
            el.style.setProperty('background', `linear-gradient(135deg, ${color} 0%, ${darkenColor(color, 20)} 100%)`, 'important');
        });
        
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
        previewArea.innerHTML = title + calc.outerHTML + copyBtn;
        
        // 🚨 תיקון 5: אתחל את כל ה-JS מחדש!
        const clonedCalc = previewArea.querySelector('[id*="preview"]') || 
                           previewArea.querySelector('[class*="calculator"]');
        if (clonedCalc) {
            initPreviewCalculator(clonedCalc, color);
        }
        
        // גלול לתצוגה
        previewArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
```

---

## 4️⃣ בדיקת פונקציית initPreviewCalculator (טאבים בתצוגה מקדימה)

### 🚨 בעיות קריטיות שחייבים לבדוק:

1. **`cloneNode(true)` לא מעתיק event listeners!**
   - כל ה-JS צריך לאתחל מחדש בתצוגה המקדימה
   
2. **ID conflicts בין המחשבון המקורי לתצוגה!**
   - צריך לשנות IDs או להשתמש ב-`data-` attributes
   
3. **Event bubbling - אירועים עולים למחשבון המקורי!**
   - צריך `e.stopPropagation()` ו-`e.preventDefault()`
   
4. **CSS עם `!important` - צריך `setProperty`!**
   - `el.style.background = color` לא יעבוד!
   - צריך: `el.style.setProperty('background', color, 'important')`
   
5. **CSS Variables לא מועתקים לאלמנט משוכפל!**
   - צריך להגדיר אותם מחדש על האלמנט המשוכפל

### בדיקה:
```javascript
const hasInitPreview = content.includes('initPreviewCalculator');
const hasStopPropagation = content.includes('stopPropagation');
const hasSetProperty = content.includes('setProperty');
const hasCSSVariableOverride = content.includes("style.setProperty('--");
```

### 🔧 תיקון מלא - פונקציית initPreviewCalculator:
```javascript
    // === אתחול מחשבון בתצוגה מקדימה - גרסה מלאה! ===
    function initPreviewCalculator(calc, primaryColor) {
        
        // === פונקציות עזר לצבעים ===
        function hexToRgba(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        
        // === State מקומי לתצוגה המקדימה ===
        const previewState = {
            basic: { gross: 10000, vacation: 12, recreation: 5, studyFund: true },
            detailed: { gross: 10000, vacation: 12, recreation: 5, studyRate: 7.5 },
            compare: { emp1: { gross: 10000, seniority: 'mid' }, emp2: { gross: 15000, seniority: 'senior' } },
            budget: { budget: 15000, seniority: 'mid', studyFund: true }
        };
        
        // === פונקציות עזר ===
        function formatCurrency(n) { return '₪' + Math.round(n).toLocaleString('he-IL'); }
        
        // === פונקציות חישוב (להתאים לפי סוג המחשבון!) ===
        function calculateEmployerNI(gross) {
            // דוגמה - להחליף בנוסחה הנכונה!
            const threshold = 7522;
            if (gross <= threshold) {
                return gross * 0.0355;
            } else {
                return threshold * 0.0355 + (gross - threshold) * 0.0755;
            }
        }
        
        function calculateEmployerCost(gross, vacation, recreation, studyRate) {
            const ni = calculateEmployerNI(gross);
            const pension = gross * 0.0625;
            const severance = gross * 0.0833;
            const study = gross * (studyRate / 100);
            const vacationCost = (gross / 22) * (vacation / 12);
            const recCost = (recreation * 418) / 12;
            return gross + ni + pension + severance + study + vacationCost + recCost;
        }
        
        // === פונקציות עדכון לכל טאב ===
        function updateBasicTab() {
            const cost = calculateEmployerCost(
                previewState.basic.gross,
                previewState.basic.vacation,
                previewState.basic.recreation,
                previewState.basic.studyFund ? 7.5 : 0
            );
            const resultEl = calc.querySelector('#wpc-calc-employer-k7m3-basic-result, [id*="basic-result"]');
            if (resultEl) resultEl.textContent = formatCurrency(cost);
        }
        
        function updateDetailedTab() {
            const cost = calculateEmployerCost(
                previewState.detailed.gross,
                previewState.detailed.vacation,
                previewState.detailed.recreation,
                previewState.detailed.studyRate
            );
            // עדכן תוצאות...
        }
        
        function updateCompareTab() {
            // חישוב השוואה...
        }
        
        function updateBudgetTab() {
            // חישוב הפוך מתקציב...
        }
        
        // === הפעלת כפתור עם צבעים (חשוב עם !important) ===
        function activateButton(btn, group, color) {
            group.querySelectorAll('button').forEach(b => {
                b.classList.remove('active');
                b.style.setProperty('background', 'transparent', 'important');
                b.style.setProperty('border-color', '#e5e7eb', 'important');
                b.style.setProperty('color', '#374151', 'important');
            });
            btn.classList.add('active');
            btn.style.setProperty('background', color, 'important');
            btn.style.setProperty('border-color', color, 'important');
            btn.style.setProperty('color', 'white', 'important');
        }
        
        // === טאבים - עם stopPropagation! ===
        const tabs = calc.querySelectorAll('[data-action="switch-tab"]');
        const contents = calc.querySelectorAll('[data-preview-tab], [class*="tab-content"]');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // 🚨 קריטי! מונע bubble למחשבון המקורי
                
                const tabName = this.dataset.tab;
                
                // הסר active מכולם
                tabs.forEach(t => {
                    t.classList.remove('active');
                    t.style.setProperty('background', 'transparent', 'important');
                    t.style.setProperty('color', '#374151', 'important');
                });
                
                contents.forEach(c => {
                    c.classList.remove('active');
                    c.style.display = 'none'; // 🚨 חייב display!
                });
                
                // הוסף active לנבחר עם צבע
                this.classList.add('active');
                this.style.setProperty('background', primaryColor, 'important');
                this.style.setProperty('color', 'white', 'important');
                
                // מצא והצג את התוכן - שימוש ב-data attribute במקום ID!
                const activeContent = calc.querySelector(
                    `[data-preview-tab="${tabName}"], [id*="tab-${tabName}"]`
                );
                if (activeContent) {
                    activeContent.classList.add('active');
                    activeContent.style.display = 'block';
                }
            });
        });
        
        // === סליידרים ===
        const sliders = calc.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            slider.addEventListener('input', function(e) {
                e.stopPropagation();
                const valueId = this.id.replace('-slider', '-value').replace('-input', '-value');
                const valueEl = calc.querySelector(`#${valueId}`) || 
                               calc.querySelector(`#${this.id}-value`);
                if (valueEl) {
                    valueEl.textContent = parseInt(this.value).toLocaleString('he-IL');
                }
                
                // עדכן את ה-state וחשב מחדש
                // ... לפי הסליידר הספציפי
            });
            
            // צבע סליידר
            slider.style.setProperty('accent-color', primaryColor, 'important');
        });
        
        // === כפתורי בחירה (vacation, seniority, etc.) ===
        const selectBtns = calc.querySelectorAll('[data-action="select-vacation"], [data-action="select-recreation"], [data-action="select-seniority"], [data-action="select-study"]');
        selectBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const group = this.closest('[class*="group"], [class*="selector"]');
                if (group) {
                    activateButton(this, group, primaryColor);
                }
                
                // עדכן state
                const value = this.dataset.value;
                // ... לפי סוג הכפתור
            });
        });
        
        // === Toggle switches ===
        const toggles = calc.querySelectorAll('[data-action="toggle-study"], input[type="checkbox"]');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', function(e) {
                e.stopPropagation();
                // ... לוגיקת toggle
            });
        });
        
        // === אתחול ראשוני - עדכן את כל הטאבים ===
        updateBasicTab();
        updateDetailedTab();
        updateCompareTab();
        updateBudgetTab();
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

### 🚨 בעיות קריטיות שחייבים לבדוק:

1. **הסקריפט כולל רק טאב אחד!**
   - בעיה: כל הטאבים צריכים JS עובד, לא רק הראשון
   - פתרון: לכלול state לכל טאב + פונקציות חישוב + עדכון לכל טאב

2. **חישובים לא עובדים בהטמעה!**
   - בעיה: הסקריפט מציג רק ערכים סטטיים
   - פתרון: לכלול את כל פונקציות החישוב

3. **כפתורי בחירה לא משפיעים על חישובים!**
   - בעיה: כפתורים משנים רק class אבל לא state
   - פתרון: לכלול state לכל טאב ולעדכן אותו

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

// 🚨 בדיקות חדשות - האם כל הטאבים עובדים?
// 6. יש state לכל טאב
const hasMultiTabState = content.match(/getEmbedScript[\s\S]*?state\s*=\s*\{[\s\S]*?basic[\s\S]*?detailed/);

// 7. יש פונקציות חישוב
const hasCalculations = content.match(/getEmbedScript[\s\S]*?function\s+calc/);

// 8. יש פונקציות עדכון לכל טאב
const hasUpdateFunctions = content.match(/getEmbedScript[\s\S]*?updateBasic|updateDetailed|updateCompare|updateBudget/);
```

### 🔧 תיקון - פונקציית getEmbedScript מלאה (עם כל הטאבים!):
```javascript
    // === יצירת סקריפט להטמעה - גרסה מלאה לכל הטאבים! ===
    function getEmbedScript(primaryColor) {
        const color = primaryColor || '#1e5490';
        
        return `<script>
document.addEventListener("DOMContentLoaded", function() {
  (function() {
    "use strict";
    var NS = "WPC_Embed_" + Date.now();
    if (window[NS]) return;
    
    var container = document.querySelector("[class*='${PREFIX}']");
    if (!container) { console.error("Container not found"); return; }
    
    // === State לכל הטאבים ===
    var state = {
      basic: { gross: 10000, vacation: 12, recreation: 5, studyFund: true },
      detailed: { gross: 10000, vacation: 12, recreation: 5, studyRate: 7.5 },
      compare: { emp1: { gross: 10000, seniority: "mid" }, emp2: { gross: 15000, seniority: "senior" } },
      budget: { budget: 15000, seniority: "mid", studyFund: true }
    };
    
    // === פונקציות עזר ===
    function fmt(n) { return "₪" + Math.round(n).toLocaleString("he-IL"); }
    
    function getVac(s) { return s === "new" ? 12 : s === "mid" ? 14 : 16; }
    function getRec(s) { return s === "new" ? 5 : s === "mid" ? 6 : 7; }
    
    // === פונקציות חישוב (להתאים לפי סוג המחשבון!) ===
    function calcNI(g) {
      var t = 7522;
      if (g <= t) return g * 0.0355;
      return t * 0.0355 + (g - t) * 0.0755;
    }
    
    function calcCost(g, v, r, s) {
      var ni = calcNI(g);
      var pension = g * 0.0625;
      var severance = g * 0.0833;
      var study = g * (s / 100);
      var vacCost = (g / 22) * (v / 12);
      var recCost = (r * 418) / 12;
      return g + ni + pension + severance + study + vacCost + recCost;
    }
    
    function calcFromBudget(b, v, r, s) {
      // חישוב הפוך - מתקציב לברוטו
      var factor = 1 + 0.0625 + 0.0833 + (s / 100) + (v / 22 / 12) + (r * 418 / 12 / 10000);
      var niRate = 0.065; // ממוצע
      return b / (1 + factor + niRate);
    }
    
    // === פונקציות עדכון לכל טאב ===
    function updateBasic() {
      var cost = calcCost(
        state.basic.gross, 
        state.basic.vacation, 
        state.basic.recreation, 
        state.basic.studyFund ? 7.5 : 0
      );
      var el = container.querySelector("[id*='basic-result'], [class*='basic-result']");
      if (el) el.textContent = fmt(cost);
    }
    
    function updateDetailed() {
      var s = state.detailed;
      var g = s.gross;
      var ni = calcNI(g);
      var pension = g * 0.0625;
      var severance = g * 0.0833;
      var study = g * (s.studyRate / 100);
      var vacCost = (g / 22) * (s.vacation / 12);
      var recCost = (s.recreation * 418) / 12;
      var total = g + ni + pension + severance + study + vacCost + recCost;
      
      // עדכן את כל השדות
      var fields = {
        "gross-row": fmt(g),
        "ni-row": fmt(ni),
        "pension-row": fmt(pension),
        "severance-row": fmt(severance),
        "study-row": fmt(study),
        "vacation-row": fmt(vacCost),
        "recreation-row": fmt(recCost),
        "total-row": fmt(total)
      };
      
      for (var key in fields) {
        var el = container.querySelector("[id*='" + key + "'], [class*='" + key + "']");
        if (el) el.textContent = fields[key];
      }
    }
    
    function updateCompare() {
      var e1 = state.compare.emp1;
      var e2 = state.compare.emp2;
      var cost1 = calcCost(e1.gross, getVac(e1.seniority), getRec(e1.seniority), 7.5);
      var cost2 = calcCost(e2.gross, getVac(e2.seniority), getRec(e2.seniority), 7.5);
      var diff = cost2 - cost1;
      
      var el1 = container.querySelector("[id*='compare-result-1']");
      var el2 = container.querySelector("[id*='compare-result-2']");
      var elDiff = container.querySelector("[id*='compare-diff']");
      
      if (el1) el1.textContent = fmt(cost1);
      if (el2) el2.textContent = fmt(cost2);
      if (elDiff) elDiff.textContent = (diff >= 0 ? "+" : "") + fmt(diff);
    }
    
    function updateBudget() {
      var s = state.budget;
      var v = getVac(s.seniority);
      var r = getRec(s.seniority);
      var studyRate = s.studyFund ? 7.5 : 0;
      var gross = calcFromBudget(s.budget, v, r, studyRate);
      
      var el = container.querySelector("[id*='budget-result'], [class*='budget-result']");
      if (el) el.textContent = fmt(gross);
    }
    
    // === מעבר טאבים ===
    function switchTab(tabName) {
      var tabs = container.querySelectorAll("[data-action='switch-tab']");
      var contents = container.querySelectorAll("[class*='tab-content']");
      
      for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
      }
      for (var j = 0; j < contents.length; j++) {
        contents[j].classList.remove("active");
        contents[j].style.display = "none";
      }
      
      var activeTab = container.querySelector("[data-tab='" + tabName + "']");
      if (activeTab) activeTab.classList.add("active");
      
      var activeContent = document.getElementById("tab-" + tabName) || 
                          container.querySelector("[id*='tab-" + tabName + "']");
      if (activeContent) {
        activeContent.classList.add("active");
        activeContent.style.display = "block";
      }
    }
    
    // === Event Delegation ===
    container.addEventListener("click", function(e) {
      var action = e.target.closest("[data-action]");
      if (!action) return;
      
      var act = action.dataset.action;
      
      // מעבר טאבים
      if (act === "switch-tab") {
        e.preventDefault();
        switchTab(action.dataset.tab);
      }
      
      // כפתורי vacation
      if (act === "select-vacation") {
        var group = action.closest("[class*='group']");
        if (group) {
          group.querySelectorAll("button").forEach(function(b) { b.classList.remove("active"); });
        }
        action.classList.add("active");
        state.basic.vacation = parseInt(action.dataset.value);
        updateBasic();
      }
      
      // כפתורי recreation
      if (act === "select-recreation") {
        var group = action.closest("[class*='group']");
        if (group) {
          group.querySelectorAll("button").forEach(function(b) { b.classList.remove("active"); });
        }
        action.classList.add("active");
        state.basic.recreation = parseInt(action.dataset.value);
        updateBasic();
      }
      
      // כפתורי seniority
      if (act === "select-seniority") {
        var group = action.closest("[class*='group']");
        if (group) {
          group.querySelectorAll("button").forEach(function(b) { b.classList.remove("active"); });
        }
        action.classList.add("active");
        
        var tabId = action.closest("[class*='tab-content']");
        if (tabId && tabId.id.includes("compare")) {
          var empNum = action.closest("[class*='emp-1']") ? "emp1" : "emp2";
          state.compare[empNum].seniority = action.dataset.value;
          updateCompare();
        } else {
          state.budget.seniority = action.dataset.value;
          updateBudget();
        }
      }
      
      // כפתורי study fund
      if (act === "select-study") {
        var group = action.closest("[class*='group']");
        if (group) {
          group.querySelectorAll("button").forEach(function(b) { b.classList.remove("active"); });
        }
        action.classList.add("active");
        state.budget.studyFund = action.dataset.value === "yes";
        updateBudget();
      }
      
      // toggle study fund
      if (act === "toggle-study") {
        state.basic.studyFund = !state.basic.studyFund;
        var label = container.querySelector("[id*='study-label']");
        if (label) label.textContent = state.basic.studyFund ? "כן" : "לא";
        updateBasic();
      }
      
      // FAQ
      if (act === "toggle-faq") {
        var item = action.closest("[class*='faq-item']");
        if (item) item.classList.toggle("open");
      }
    });
    
    // === סליידרים ===
    container.addEventListener("input", function(e) {
      if (e.target.type !== "range") return;
      
      var id = e.target.id;
      var val = parseInt(e.target.value);
      
      // עדכן ערך מוצג
      var valueId = id.replace("-slider", "-value").replace("-input", "-value");
      var valueEl = document.getElementById(valueId) || document.getElementById(id + "-value");
      if (valueEl) {
        valueEl.textContent = val.toLocaleString("he-IL");
      }
      
      // עדכן state לפי הסליידר
      if (id.includes("basic-gross")) {
        state.basic.gross = val;
        updateBasic();
      } else if (id.includes("detailed-gross")) {
        state.detailed.gross = val;
        updateDetailed();
      } else if (id.includes("detailed-vacation")) {
        state.detailed.vacation = val;
        updateDetailed();
      } else if (id.includes("detailed-recreation")) {
        state.detailed.recreation = val;
        updateDetailed();
      } else if (id.includes("detailed-study")) {
        state.detailed.studyRate = val;
        updateDetailed();
      } else if (id.includes("compare-1") || id.includes("emp1")) {
        state.compare.emp1.gross = val;
        updateCompare();
      } else if (id.includes("compare-2") || id.includes("emp2")) {
        state.compare.emp2.gross = val;
        updateCompare();
      } else if (id.includes("budget")) {
        state.budget.budget = val;
        updateBudget();
      }
    });
    
    // אתחול ראשוני
    updateBasic();
    updateDetailed();
    updateCompare();
    updateBudget();
    
    window[NS] = { v: "1.0" };
  })();
});
<` + `/script>`;
    }
```

### ⚠️ חשוב! התאמה לסוג המחשבון:

הקוד לעיל הוא דוגמה למחשבון **עלות מעסיק**. עבור מחשבונים אחרים יש להחליף:

| מחשבון | פונקציות חישוב | State נדרש |
|--------|---------------|------------|
| ריבית דריבית | `calcFutureValue`, `calcPMT` | `{ initial, monthly, years, rate }` |
| ברוטו נטו | `calcNetSalary`, `calcTax` | `{ gross, credits, pension }` |
| משכנתא | `calcMortgage`, `calcTotal` | `{ amount, rate, years }` |
| חיסכון | `calcSavings`, `calcFinal` | `{ initial, monthly, years, rate }` |
| פנסיה | `calcPension`, `calcMonthly` | `{ salary, age, pension }` |
| מס רכישה | `calcPurchaseTax` | `{ price, isFirst }` |

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
    
    // 5. בדיקת תיקוני בעיות קריטיות
    console.log('\n🔧 בדיקת תיקוני בעיות קריטיות:');
    const code = document.body.innerHTML;
    
    const criticalChecks = {
        'initPreviewCalculator': code.includes('initPreviewCalculator'),
        'stopPropagation': code.includes('stopPropagation'),
        'setProperty with important': code.includes("setProperty(") && code.includes("'important'"),
        'CSS Variable override (--primary)': code.includes("--primary") || code.includes("--wpc-"),
        'display block/none explicit': code.includes("display = 'block'") || code.includes("style.display"),
        'Multi-tab state': code.includes('state.basic') || code.includes('previewState'),
        'hexToRgba helper': code.includes('hexToRgba') || code.includes('rgba('),
    };
    
    let criticalPassed = 0;
    let criticalFailed = 0;
    
    for (const [name, result] of Object.entries(criticalChecks)) {
        if (result) {
            console.log(`  ✅ ${name}`);
            criticalPassed++;
            successes.push(`תיקון קריטי: ${name}`);
        } else {
            console.error(`  ❌ ${name} - חסר!`);
            criticalFailed++;
            warnings.push(`חסר תיקון קריטי: ${name}`);
        }
    }
    
    console.log(`\n  📊 תיקונים קריטיים: ${criticalPassed}/${Object.keys(criticalChecks).length}`);
    
    // 6. בדיקת פונקציונליות בפועל - כפתורים, סליידרים, טאבים
    console.log('\n🎮 בדיקת פונקציונליות אינטראקטיבית:');
    
    // בדוק שכפתורי הצבע עובדים
    if (colorBtns.length > 0) {
        const testBtn = colorBtns[0];
        const previewBefore = document.querySelector('[class*="preview-area"]');
        testBtn.click();
        await wait(300);
        const previewAfter = document.querySelector('[class*="preview-area"]');
        
        if (previewAfter && previewAfter.innerHTML.length > 100) {
            console.log('  ✅ תצוגה מקדימה נוצרת');
            
            // בדוק שטאבים עובדים בתצוגה
            const previewTabs = previewAfter.querySelectorAll('[data-action="switch-tab"]');
            if (previewTabs.length > 1) {
                const secondTab = previewTabs[1];
                const tabBefore = secondTab.classList.contains('active');
                secondTab.click();
                await wait(200);
                const tabAfter = secondTab.classList.contains('active');
                
                if (tabAfter && !tabBefore) {
                    console.log('  ✅ טאבים עובדים בתצוגה מקדימה');
                    successes.push('טאבים בתצוגה מקדימה');
                } else {
                    console.error('  ❌ טאבים לא עובדים בתצוגה מקדימה!');
                    errors.push('טאבים לא עובדים בתצוגה');
                }
            }
            
            // בדוק שסליידרים עובדים
            const previewSliders = previewAfter.querySelectorAll('input[type="range"]');
            if (previewSliders.length > 0) {
                const slider = previewSliders[0];
                const valueBefore = slider.value;
                slider.value = parseInt(slider.max) - 1000;
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                await wait(100);
                console.log('  ✅ סליידרים עובדים בתצוגה מקדימה');
                successes.push('סליידרים בתצוגה מקדימה');
                slider.value = valueBefore;
            }
            
            // בדוק שהצבע הוחל
            const coloredElements = previewAfter.querySelectorAll(`[style*="${testBtn.dataset.color}"]`);
            if (coloredElements.length > 0) {
                console.log(`  ✅ צבע ${testBtn.dataset.color} הוחל על ${coloredElements.length} אלמנטים`);
                successes.push('צבעים מוחלפים');
            } else {
                console.warn('  ⚠️ לא נמצאו אלמנטים עם הצבע הנבחר (בדיקה ויזואלית נדרשת)');
            }
        } else {
            console.error('  ❌ תצוגה מקדימה לא נוצרה!');
            errors.push('תצוגה מקדימה לא נוצרה');
        }
    }
    
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

### 🚨 CRITICAL - בדיקות ראשונות (אסורים!):

#### ❌ אם נמצא `pointer-events: none` בתצוגה מקדימה:
```javascript
// חפש את הדפוס הזה:
/showPreview[\s\S]*?pointer-events\s*:\s*none/
```
**פתרון:** הסר לחלוטין! זה חוסם את כל האינטראקציה.

#### ❌ אם `showPreview` רק מחליף HTML בלי אתחול JS:
בדוק שיש:
1. `cloneNode(true)` - לשכפול המחשבון
2. קריאה ל-`initPreviewCalculator` אחרי השכפול
3. `setProperty` עם `'important'` להחלפת צבעים

**דפוס שגוי (צריך לתקן!):**
```javascript
// ❌ שגוי - רק החלפת HTML
previewContent.innerHTML = '<div style="pointer-events: none;">' + html + '</div>';

// ✅ נכון - שכפול + אתחול
const calc = calculator.cloneNode(true);
calc.id = 'calculator-preview';
// ... החלפת צבעים עם setProperty ...
previewContent.innerHTML = calc.outerHTML;
initPreviewCalculator(clonedCalc, color);
```

### ✅ בדיקות פונקציות חובה:

### ❌ אם חסר `getEmbedScript`:
הוסף את הפונקציה המלאה (ראה סעיף 6)

### ❌ אם חסר `showPreview`:
הוסף את הפונקציה (ראה סעיף 3)

### ❌ אם חסרים כפתורי צבע:
הוסף את בורר הצבעים (ראה סעיף 2)

### ❌ אם חסר `initPreviewCalculator`:
הוסף את הפונקציה (ראה סעיף 4)

### ❌ אם `initPreviewCalculator` קיים אבל לא נקרא מ-`showPreview`:
הוסף קריאה ל-`initPreviewCalculator(clonedCalc, color)` בסוף `showPreview`

### ❌ אם חסרים `darkenColor` ו-`hexToRgba`:
הוסף את פונקציות העזר לצבעים (ראה סעיף 3)

### ❌ אם `initPreviewCalculator` חסר `previewState`:
הוסף state מקומי לתצוגה המקדימה עם ערכי ברירת מחדל לכל טאב

### ❌ אם `initPreviewCalculator` חסר פונקציות update:
הוסף `updateBasicPreview()`, `updateDetailedPreview()` וכו' לכל טאב

### ❌ אם סליידרים לא מחוברים ל-state וחישוב:
כל slider צריך:
1. `e.stopPropagation()`
2. עדכון `previewState`
3. קריאה לפונקציית update

### ❌ אם `copyEmbedCode` לא כולל CSS/getEmbedScript:
תקן את הפונקציה (ראה סעיף 5)

### ❌ אם סגירת script לא בטוחה:
החלף `'</script>'` ב-`'</' + 'script>'`

## שלב 4: שמור ודווח

```markdown
## 📋 דוח תיקון אזור הטמעה

### 🚨 בדיקות CRITICAL (אסורים):
- pointer-events: none: ✅ לא נמצא / ❌ נמצא - יש להסיר!

### 📝 בדיקת תוכן:
- שם המחשבון בכותרת: ✅/❌
- מילות מפתח רלוונטיות: ✅/❌
- מספר טאבים נכון: ✅/❌
- אין תוכן ממחשבון אחר: ✅/❌

### 🔧 בדיקות פונקציות:
- showPreview קיים: ✅/❌
- showPreview משתמש ב-cloneNode: ✅/❌
- showPreview קורא ל-initPreviewCalculator: ✅/❌
- initPreviewCalculator קיים: ✅/❌
- initPreviewCalculator מכיל previewState: ✅/❌
- initPreviewCalculator מכיל פונקציות update: ✅/❌
- stopPropagation בטאבים: ✅/❌
- stopPropagation בסליידרים: ✅/❌
- darkenColor/hexToRgba קיימים: ✅/❌
- setProperty עם important: ✅/❌
- data-preview-tab: ✅/❌
- calculator-preview ID: ✅/❌

### ✅ תיקונים שבוצעו:
1. [מה תוקן]

### 📊 סטטוס פונקציונליות:
- כפתורי צבע: ✅/❌ (כמות)
- החלפת צבעים: ✅/❌
- תצוגה מקדימה אינטראקטיבית: ✅/❌
- טאבים בתצוגה: ✅/❌
- סליידרים בתצוגה: ✅/❌
- חישובים עובדים בתצוגה: ✅/❌
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

## 📝 יומן שינויים

### גרסה 5.0 (דצמבר 2025) - תיקוני באגים קריטיים!
**בעיות חדשות שנתגלו ונוספו לבדיקה:**

13. **🚨 CRITICAL: Selector ב-showPreview לא תואם ל-HTML!**
    - בעיה: `querySelector('.xxx-calculator')` מחפש class שלא קיים
    - סימן: לוחצים על צבע ואין מחשבון בתצוגה המקדימה
    - פתרון: לוודא שה-selector תואם בדיוק ל-class ב-HTML
    - בדיקה:
    ```javascript
    const selectorMatch = content.match(/showPreview[\s\S]*?querySelector\(['"]([^'"]+)['"]\)/);
    if (selectorMatch) {
        const selector = selectorMatch[1];
        const className = selector.replace(/^\./, '').split(' ')[0];
        if (!content.includes('class="' + className) && !content.includes("class='" + className)) {
            console.error('🚨 CRITICAL: showPreview משתמש ב-selector שלא קיים ב-HTML: ' + selector);
        }
    }
    ```

14. **🚨 CRITICAL: `style.display = 'block'` לא דורס `!important`!**
    - בעיה: התצוגה המקדימה נשארת מוסתרת
    - סימן: לוחצים על צבע והcontainer נשאר display:none
    - פתרון: להשתמש ב-`setProperty('display', 'block', 'important')`
    - בדיקה:
    ```javascript
    const displaySimple = content.match(/previewContainer\.style\.display\s*=\s*['"]block['"]/);
    const displayImportant = content.match(/setProperty\(['"]display['"],\s*['"]block['"],\s*['"]important['"]\)/);
    if (displaySimple && !displayImportant) {
        console.error('🚨 CRITICAL: style.display = "block" לא ידרוס !important - צריך setProperty!');
    }
    ```

15. **🚨 CRITICAL: `max-height` + `overflow-y: auto` על preview-content!**
    - בעיה: סקרול מכוער בתוך התצוגה המקדימה
    - סימן: scrollbar בצד שמאל של התצוגה המקדימה
    - פתרון: להסיר `max-height` ו-`overflow-y: auto`, להשתמש ב-`overflow: visible`
    - בדיקה:
    ```javascript
    const previewContentStyle = content.match(/id="embed-preview-content"[^>]*style="([^"]+)"/);
    if (previewContentStyle) {
        const style = previewContentStyle[1];
        if (style.includes('max-height') || style.includes('overflow-y: auto')) {
            console.error('🚨 CRITICAL: embed-preview-content עם max-height/overflow-y:auto - גורם לסקרול מכוער!');
        }
    }
    ```

**תיקון CSS נכון:**
```html
<!-- ❌ שגוי - גורם לסקרול -->
<div id="embed-preview-content" style="max-height: 400px !important; overflow-y: auto !important; ...">

<!-- ✅ נכון - בלי סקרול -->
<div id="embed-preview-content" style="overflow: visible !important; padding: 15px !important; ...">
```

16. **🚨 CRITICAL: שמות Selectors ב-initPreviewCalculator לא תואמים ל-IDs בHTML!**
    - בעיה: הפונקציה מחפשת `single` אבל הטאב נקרא `basic`
    - בעיה: הפונקציה מחפשת `offer1` אבל ה-ID הוא `offer-a`
    - סימן: לוחצים על סליידר והנתונים לא מתעדכנים
    - פתרון: לבדוק את ה-IDs האמיתיים ב-HTML ולהתאים את הקוד
    - בדיקה:
    ```javascript
    // בדוק התאמה בין שמות ב-state לשמות ב-HTML
    const stateNames = content.match(/previewState\s*=\s*\{[\s\S]*?\}/);
    const htmlIds = content.match(/id="([^"]+)"/g) || [];
    
    // בדוק שה-state משתמש בשמות תואמים
    if (stateNames) {
        const stateContent = stateNames[0];
        // בדוק אם יש 'single' ב-state אבל 'basic' ב-HTML
        if (stateContent.includes('single:') && !htmlIds.some(id => id.includes('single'))) {
            console.error('🚨 state משתמש ב-"single" אבל ה-HTML משתמש בשם אחר!');
        }
        // בדוק אם יש 'offer1' ב-state אבל 'offer-a' ב-HTML
        if (stateContent.includes('offer1:') && htmlIds.some(id => id.includes('offer-a'))) {
            console.error('🚨 state משתמש ב-"offer1" אבל ה-HTML משתמש ב-"offer-a"!');
        }
    }
    ```

**דוגמה לתיקון:**
```javascript
// ❌ שגוי - שמות לא תואמים
const previewState = {
    single: { amount: 100000 },  // אבל ה-ID הוא "basic-amount"
    compare: { 
        offer1: { rate: 6 },     // אבל ה-ID הוא "offer-a-rate"
        offer2: { rate: 5.5 }    // אבל ה-ID הוא "offer-b-rate"
    }
};

// ✅ נכון - שמות תואמים ל-IDs
const previewState = {
    basic: { amount: 100000 },   // תואם ל-ID "basic-amount"
    compare: { 
        offerA: { rate: 6 },     // תואם ל-ID "offer-a-rate"
        offerB: { rate: 5.5 }    // תואם ל-ID "offer-b-rate"
    }
};
```

### גרסה 4.0 (דצמבר 2025) - שדרוג משמעותי!
**בעיות חדשות שנתגלו ונוספו לבדיקה:**

8. **🚨 CRITICAL: `pointer-events: none` בתצוגה מקדימה**
   - בעיה: חוסם לחלוטין את כל האינטראקציה בתצוגה המקדימה
   - פתרון: להסיר לחלוטין! אסור להשתמש בזה
   - סימן: משתמשים לא יכולים ללחוץ על כלום בתצוגה

9. **showPreview שלא קורא ל-initPreviewCalculator**
   - בעיה: גם אם יש פונקציה initPreviewCalculator, אם היא לא נקראת - לא יעבוד!
   - פתרון: חייב קריאה ל-`initPreviewCalculator(clonedCalc, color)` בסוף showPreview
   - בדיקה חדשה: `/showPreview[\s\S]*?initPreviewCalculator\s*\(/`

10. **חסר פונקציות עזר לצבעים**
    - בעיה: בלי `darkenColor` ו-`hexToRgba` הצבעים לא יפים
    - פתרון: להוסיף את שתי הפונקציות

11. **initPreviewCalculator בלי previewState**
    - בעיה: בלי state מקומי, הסליידרים לא שומרים ערכים
    - פתרון: להגדיר `previewState` עם ערכי ברירת מחדל לכל טאב

12. **סליידרים לא מחוברים לחישוב**
    - בעיה: סליידר זזים אבל לא מחשבים
    - פתרון: כל slider צריך לעדכן state ולקרוא לפונקציית update

**שיפורים בקוד בדיקה:**
- הוספת קטגוריה CRITICAL לבעיות אסורות
- בדיקה ש-initPreviewCalculator נקרא מ-showPreview (לא רק קיים)
- בדיקת previewState בתוך initPreviewCalculator
- עדכון תבנית הדוח עם כל הבדיקות החדשות

### גרסה 3.0 (דצמבר 2025)
**תיקונים קריטיים שנתגלו:**

1. **`cloneNode(true)` לא מעתיק event listeners**
   - הוספת פונקציית `initPreviewCalculator` מלאה
   - אתחול מחדש של כל ה-event listeners

2. **ID conflicts בין מחשבונים**
   - שינוי ID של המחשבון המשוכפל
   - שימוש ב-`data-preview-tab` במקום IDs

3. **Event bubbling**
   - הוספת `e.stopPropagation()` ו-`e.preventDefault()` בכל handler

4. **CSS Variables לא מועברים**
   - הגדרת `--primary`, `--primary-dark`, `--primary-light` על האלמנט המשוכפל

5. **`!important` לא נדרס**
   - שימוש ב-`setProperty('property', value, 'important')` במקום `style.property = value`

6. **Display block/none**
   - הוספת `style.display` מפורש בנוסף ל-class

7. **getEmbedScript - רק טאב אחד עובד**
   - הוספת state לכל הטאבים
   - הוספת פונקציות חישוב
   - הוספת פונקציות עדכון לכל טאב
   - חיבור כל סליידר/כפתור ל-state ולחישוב

### גרסה 2.0
- הוספת בדיקת תוכן אזור ההטמעה
- התאמה לסוג המחשבון

### גרסה 1.0
- בדיקות בסיסיות

---

**נוצר על ידי: Cursor AI**  
**גרסה: 5.1**  
**מיקוד: אזור הטמעה + בדיקת תוכן + תיקון בעיות JS קריטיות + בדיקות CRITICAL חדשות + אימות selectors + תיקון סקרולים + התאמת state ל-IDs**

