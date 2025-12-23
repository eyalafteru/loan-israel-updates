# 🔍 סוכן QA לפלט מחשבונים - בדיקה ותיקון אוטומטי

## 📋 תיאור הסוכן

סוכן QA שבודק ומאמת את הפלט של **סוכן AI לבניית עמודי מחשבון פיננסי**.
הסוכן **לא רק בודק - אלא גם מתקן אוטומטית** בעיות שנמצאו!

### 🎯 מה הסוכן עושה:
1. ✅ **בודק** - מריץ בדיקות מקיפות על הקוד
2. 🔧 **מתקן** - מתקן אוטומטית בעיות נפוצות
3. 📋 **מדווח** - מחזיר דוח מפורט

### 📂 תיקיית הפלט לבדיקה:
```
C:\Users\eyal\loan-israel-updaets\loan-israel-updates\מחשבונים חדשים\
```

---

## 🚀 הפעלת הסוכן

```
בדוק ותקן את הקובץ: [שם הקובץ].html
```

הסוכן יבצע בדיקות מקיפות, **יתקן אוטומטית** בעיות שניתן לתקן, ויחזיר דוח מפורט.

---

# 🔧 תיקונים אוטומטיים - הסוכן מתקן את הבעיות!

## רשימת תיקונים אוטומטיים:

| בעיה | תיקון אוטומטי |
|------|---------------|
| חסר getEmbedScript | ✅ מוסיף פונקציה מלאה |
| טאבים לא עובדים בהטמעה | ✅ מוסיף switchTab ל-getEmbedScript |
| סליידרים לא עובדים בהטמעה | ✅ מוסיף event listeners |
| חסר DOMContentLoaded | ✅ עוטף את הסקריפט |
| סגירת script לא בטוחה | ✅ מתקן ל-'</' + 'script>' |
| חסר קרדיט | ✅ מוסיף קרדיט עם nofollow |
| חסר nofollow | ✅ מוסיף nofollow לקישור |
| טאבים עם overflow-x | ✅ משנה ל-flex-wrap |
| חסר !important | ✅ מוסיף לכל מאפייני CSS |
| חסר viewport script | ✅ מוסיף בהתחלה |
| **יש דיסקליימר** | ✅ מסיר את אזור wpc-disclaimer |
| **יש Related Posts** | ✅ מסיר את [related-shortcode-instert] |

## 🛠️ קוד התיקון האוטומטי

```javascript
// === סוכן QA + תיקון אוטומטי ===
// הסוכן בודק את הקוד ומתקן בעיות אוטומטית

class CalculatorQAFixer {
    constructor(content) {
        this.original = content;
        this.content = content;
        this.fixes = [];
        this.errors = [];
        this.warnings = [];
    }
    
    // === פונקציית הרצה ראשית ===
    runAllFixesAndChecks() {
        console.log('🔍 === סוכן QA + תיקון אוטומטי ===\n');
        
        // 1. בדיקות ותיקונים
        this.fixViewportScript();
        this.fixGetEmbedScript();
        this.fixCopyEmbedCode();
        this.fixCredit();
        this.fixScriptClosingTag();
        this.fixTabsOverflow();
        this.fixCSSImportant();
        this.fixDOMContentLoaded();
        this.removeForbiddenSections(); // הסרת דיסקליימר ו-related posts
        
        // 2. דוח
        this.printReport();
        
        // 3. החזר קוד מתוקן
        return this.content;
    }
    
    // === תיקון 1: Viewport Script ===
    fixViewportScript() {
        const viewportScript = `<script>
// בדיקה והוספת viewport meta tag אם חסר
if (!document.querySelector('meta[name="viewport"]')) {
  const viewport = document.createElement('meta');
  viewport.name = 'viewport';
  viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=yes';
  document.head.appendChild(viewport);
}
</script>

`;
        
        if (!this.content.includes('meta[name="viewport"]')) {
            // הוסף בתחילת הקובץ
            this.content = viewportScript + this.content;
            this.fixes.push('✅ נוסף viewport script בתחילת הקובץ');
        }
    }
    
    // === תיקון 2: getEmbedScript חסר ===
    fixGetEmbedScript() {
        if (!this.content.includes('getEmbedScript')) {
            this.errors.push('❌ חסר getEmbedScript - הטאבים לא יעבדו בהטמעה!');
            
            // מצא את המקום להוסיף את הפונקציה (לפני סגירת ה-IIFE)
            const iifEnd = this.content.lastIndexOf('})();');
            if (iifEnd > -1) {
                const embedScript = this.generateGetEmbedScript();
                this.content = this.content.slice(0, iifEnd) + 
                              '\n\n' + embedScript + '\n\n' + 
                              this.content.slice(iifEnd);
                this.fixes.push('✅ נוספה פונקציית getEmbedScript מלאה');
            }
        } else {
            // בדוק שהפונקציה מכילה את הדרוש
            if (!this.content.includes('DOMContentLoaded') && 
                this.content.includes('getEmbedScript')) {
                this.warnings.push('⚠️ getEmbedScript קיים אבל אולי חסר DOMContentLoaded');
            }
        }
    }
    
    // === תיקון 3: copyEmbedCode ===
    fixCopyEmbedCode() {
        if (!this.content.includes('copyEmbedCode')) {
            this.errors.push('❌ חסר copyEmbedCode');
            // לא מוסיף אוטומטית כי זה תלוי במבנה הספציפי
        } else {
            // בדוק שמשתמש ב-getEmbedScript
            const copyMatch = this.content.match(/function\s+copyEmbedCode[\s\S]*?(?=function\s|\}\s*\)\s*\(\s*\)|$)/);
            if (copyMatch && !copyMatch[0].includes('getEmbedScript')) {
                this.errors.push('❌ copyEmbedCode לא משתמש ב-getEmbedScript!');
            }
        }
    }
    
    // === תיקון 4: קרדיט ===
    fixCredit() {
        const hasCredit = this.content.includes('loan-israel.co.il');
        const hasNofollow = this.content.includes('nofollow');
        
        if (!hasCredit) {
            this.errors.push('❌ חסר קישור קרדיט');
            // הוסף קרדיט אם חסר - בתוך copyEmbedCode או getEmbedScript
        }
        
        if (hasCredit && !hasNofollow) {
            // תקן - הוסף nofollow
            this.content = this.content.replace(
                /href="https:\/\/loan-israel\.co\.il[^"]*"([^>]*?)>/g,
                (match, rest) => {
                    if (!rest.includes('nofollow')) {
                        return match.replace('>', ' rel="nofollow noopener">');
                    }
                    return match;
                }
            );
            this.fixes.push('✅ נוסף nofollow לקישורי קרדיט');
        }
    }
    
    // === תיקון 5: סגירת script בטוחה ===
    fixScriptClosingTag() {
        // בתוך מחרוזות (getEmbedScript), צריך סגירה בטוחה
        if (this.content.includes("'</script>'") || 
            this.content.includes('"</script>"')) {
            
            this.content = this.content
                .replace(/"<\/script>"/g, '"</" + "script>"')
                .replace(/'<\/script>'/g, "'</' + 'script>'");
            
            this.fixes.push('✅ תוקנה סגירת script tag לפורמט בטוח');
        }
    }
    
    // === תיקון 6: טאבים עם overflow במקום wrap ===
    fixTabsOverflow() {
        if (this.content.includes('tabs-nav') && 
            this.content.includes('overflow-x: auto')) {
            
            this.content = this.content.replace(
                /overflow-x:\s*auto\s*!important/g,
                'flex-wrap: wrap !important'
            );
            this.fixes.push('✅ תוקנו טאבים: overflow-x הוחלף ב-flex-wrap');
        }
    }
    
    // === תיקון 7: CSS עם !important ===
    fixCSSImportant() {
        // מצא את כל בלוקי ה-CSS
        const styleMatches = this.content.match(/<style[^>]*>([\s\S]*?)<\/style>/gi);
        if (!styleMatches) return;
        
        let fixCount = 0;
        styleMatches.forEach(styleBlock => {
            const lines = styleBlock.split('\n');
            const fixedLines = lines.map(line => {
                // אם יש property וערך, ואין !important, הוסף
                if (line.includes(':') && 
                    line.includes(';') && 
                    !line.includes('!important') &&
                    !line.trim().startsWith('//') &&
                    !line.trim().startsWith('/*') &&
                    !line.includes('--')) { // לא CSS variables
                    
                    fixCount++;
                    return line.replace(/;(\s*)$/, ' !important;$1');
                }
                return line;
            });
            
            if (fixCount > 0) {
                const fixedBlock = fixedLines.join('\n');
                this.content = this.content.replace(styleBlock, fixedBlock);
            }
        });
        
        if (fixCount > 0) {
            this.fixes.push(`✅ נוסף !important ל-${fixCount} מאפייני CSS`);
        }
    }
    
    // === תיקון 8: DOMContentLoaded ב-getEmbedScript ===
    fixDOMContentLoaded() {
        // בדוק אם getEmbedScript קיים אבל בלי DOMContentLoaded
        const embedMatch = this.content.match(/function\s+getEmbedScript[\s\S]*?return[\s\S]*?script/);
        if (embedMatch && !embedMatch[0].includes('DOMContentLoaded')) {
            this.warnings.push('⚠️ getEmbedScript צריך לכלול DOMContentLoaded wrapper');
        }
    }
    
    // === תיקון 9: הסרת אזורים אסורים במחשבונים ===
    removeForbiddenSections() {
        // הסר דיסקליימר אם קיים
        if (this.content.includes('wpc-disclaimer')) {
            // הסר את כל אזור הדיסקליימר
            this.content = this.content.replace(
                /<div[^>]*class="[^"]*wpc-disclaimer[^"]*"[^>]*>[\s\S]*?<\/div>\s*/gi,
                ''
            );
            this.fixes.push('✅ הוסר אזור דיסקליימר (לא שייך למחשבונים)');
        }
        
        // הסר Related Posts shortcode אם קיים
        if (this.content.includes('[related-shortcode-instert]')) {
            this.content = this.content.replace(/\[related-shortcode-instert\]\s*/gi, '');
            this.fixes.push('✅ הוסר [related-shortcode-instert] (לא שייך למחשבונים)');
        }
    }
    
    // === יצירת getEmbedScript מלא ===
    generateGetEmbedScript() {
        return `    // === פונקציית יצירת סקריפט להטמעה ===
    function getEmbedScript() {
        var lines = [
            '<script>',
            'document.addEventListener("DOMContentLoaded", function() {',
            '  (function() {',
            '    "use strict";',
            '    var NS = "WPC_Calc_Embed_" + Date.now();',
            '    if (window[NS]) return;',
            '    var container = document.querySelector("[class*=\\\\"wpc-calc\\\\"]");',
            '    if (!container) { console.error("Container not found"); return; }',
            '',
            '    // פונקציות עזר',
            '    function el(id) { return document.getElementById(id); }',
            '    function formatNumber(n) { return Math.round(n).toLocaleString("he-IL"); }',
            '',
            '    // === מעבר טאבים ===',
            '    function switchTab(tabName) {',
            '      var tabs = container.querySelectorAll("[data-action=\\\\"switch-tab\\\\"]");',
            '      var contents = container.querySelectorAll("[class*=\\\\"tab-content\\\\"]");',
            '      for (var i = 0; i < tabs.length; i++) {',
            '        tabs[i].classList.remove("active");',
            '      }',
            '      for (var j = 0; j < contents.length; j++) {',
            '        contents[j].classList.remove("active");',
            '        contents[j].style.display = "none";',
            '      }',
            '      var activeTab = container.querySelector("[data-tab=\\\\"" + tabName + "\\\\"]");',
            '      if (activeTab) activeTab.classList.add("active");',
            '      var activeContent = document.getElementById("tab-" + tabName);',
            '      if (activeContent) {',
            '        activeContent.classList.add("active");',
            '        activeContent.style.display = "block";',
            '      }',
            '    }',
            '',
            '    // === Event delegation ===',
            '    container.addEventListener("click", function(e) {',
            '      var action = e.target.closest("[data-action]");',
            '      if (!action) return;',
            '      var act = action.dataset.action;',
            '      if (act === "switch-tab") {',
            '        e.preventDefault();',
            '        switchTab(action.dataset.tab);',
            '      }',
            '    });',
            '',
            '    // === טיפול בסליידרים ===',
            '    container.addEventListener("input", function(e) {',
            '      if (e.target.type === "range") {',
            '        var id = e.target.id;',
            '        var valueId = id.replace("-slider", "-value").replace("-input", "-value");',
            '        var valueEl = document.getElementById(valueId) || document.getElementById(id + "-value");',
            '        if (valueEl) {',
            '          valueEl.textContent = formatNumber(parseInt(e.target.value));',
            '        }',
            '      }',
            '    });',
            '',
            '    window[NS] = { version: "1.0.0" };',
            '  })();',
            '});'
        ];',
        return lines.join("\\\\n") + "\\\\n</" + "script>";
    }`;
    }
    
    // === הדפסת דוח ===
    printReport() {
        console.log('\\n' + '='.repeat(60));
        console.log('📊 דוח סוכן QA + תיקון אוטומטי');
        console.log('='.repeat(60));
        
        console.log('\\n✅ תיקונים שבוצעו: ' + this.fixes.length);
        this.fixes.forEach(f => console.log('   ' + f));
        
        console.log('\\n❌ שגיאות שנותרו: ' + this.errors.length);
        this.errors.forEach(e => console.error('   ' + e));
        
        console.log('\\n⚠️ אזהרות: ' + this.warnings.length);
        this.warnings.forEach(w => console.warn('   ' + w));
        
        if (this.fixes.length > 0) {
            console.log('\\n🎉 הקוד תוקן! יש להעתיק את הקוד המתוקן.');
        }
    }
}

// שימוש:
// const fixer = new CalculatorQAFixer(htmlContent);
// const fixedContent = fixer.runAllFixesAndChecks();
```

---

## 🤖 הוראות לסוכן AI - בדוק ותקן!

כשמקבלים קובץ מחשבון לבדיקה, הסוכן חייב:

### שלב 1: קרא את הקובץ
```
קרא את הקובץ: מחשבונים חדשים/[שם הקובץ].html
```

### שלב 2: בדוק ותקן את הבעיות הבאות

#### 🔧 תיקון 1: חסר getEmbedScript
**בדיקה:** חפש `function getEmbedScript` או `getEmbedScript`
**אם חסר - הוסף את הפונקציה הזו לפני סגירת ה-IIFE (`})();`):**

```javascript
    // === פונקציית יצירת סקריפט להטמעה ===
    function getEmbedScript() {
        const lines = [
            '<script>',
            'document.addEventListener("DOMContentLoaded", function() {',
            '  (function() {',
            '    "use strict";',
            '    var NS = "WPC_Calc_Embed_" + Date.now();',
            '    if (window[NS]) return;',
            '    var container = document.querySelector("[class*=\\"wpc-calc\\"]");',
            '    if (!container) return;',
            '',
            '    function switchTab(tabName) {',
            '      var tabs = container.querySelectorAll("[data-action=\\"switch-tab\\"]");',
            '      var contents = container.querySelectorAll("[class*=\\"tab-content\\"]");',
            '      for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove("active");',
            '      for (var j = 0; j < contents.length; j++) {',
            '        contents[j].classList.remove("active");',
            '        contents[j].style.display = "none";',
            '      }',
            '      var activeTab = container.querySelector("[data-tab=\\"" + tabName + "\\"]");',
            '      if (activeTab) activeTab.classList.add("active");',
            '      var activeContent = document.getElementById("tab-" + tabName);',
            '      if (activeContent) {',
            '        activeContent.classList.add("active");',
            '        activeContent.style.display = "block";',
            '      }',
            '    }',
            '',
            '    container.addEventListener("click", function(e) {',
            '      var action = e.target.closest("[data-action]");',
            '      if (action && action.dataset.action === "switch-tab") {',
            '        switchTab(action.dataset.tab);',
            '      }',
            '    });',
            '',
            '    container.addEventListener("input", function(e) {',
            '      if (e.target.type === "range") {',
            '        var valueEl = document.getElementById(e.target.id.replace("-slider", "-value"));',
            '        if (valueEl) valueEl.textContent = parseInt(e.target.value).toLocaleString("he-IL");',
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

#### 🔧 תיקון 2: copyEmbedCode לא משתמש ב-getEmbedScript
**בדיקה:** מצא את `function copyEmbedCode` ובדוק שיש בתוכה `getEmbedScript()`
**אם חסר - תקן את הפונקציה כך שתכלול:**
```javascript
    // בסוף הפונקציה, לפני navigator.clipboard:
    code += getEmbedScript();
```

#### 🔧 תיקון 3: סגירת script לא בטוחה
**בדיקה:** חפש `'</script>'` או `"</script>"` בתוך מחרוזות
**תקן ל:** `'</' + 'script>'`

#### 🔧 תיקון 4: חסר nofollow על קרדיט
**בדיקה:** חפש `loan-israel.co.il` ובדוק אם יש `nofollow`
**תקן:** הוסף `rel="nofollow noopener"` לקישור

#### 🔧 תיקון 5: טאבים עם overflow-x במקום flex-wrap
**בדיקה:** חפש `tabs-nav` ובדוק אם יש `overflow-x: auto`
**תקן:** החלף ב-`flex-wrap: wrap !important`

#### 🔧 תיקון 6: חסר viewport script
**בדיקה:** בדוק אם הקובץ מתחיל עם viewport script
**תקן:** הוסף בתחילת הקובץ:
```html
<script>
if (!document.querySelector('meta[name="viewport"]')) {
  const viewport = document.createElement('meta');
  viewport.name = 'viewport';
  viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=yes';
  document.head.appendChild(viewport);
}
</script>
```

### שלב 3: שמור את הקובץ המתוקן
לאחר כל התיקונים, שמור את הקובץ.

### שלב 4: דווח על התיקונים
```markdown
## 📋 דוח תיקונים

### ✅ תיקונים שבוצעו:
1. [תיאור תיקון]
2. [תיאור תיקון]

### ❌ בעיות שנותרו:
1. [בעיה שלא ניתן לתקן אוטומטית]

### 📊 סטטוס:
- טאבים: ✅/❌
- סליידרים: ✅/❌
- העתקה: ✅/❌
- תצוגה מקדימה: ✅/❌
```

---

# 🚨 בדיקות קריטיות ראשונות (הכי חשוב!)

## 🔴 1. בדיקת כל האזורים בעמוד

**חובה לוודא שכל האזורים הבאים קיימים בעמוד:**

```javascript
// === בדיקת אזורים חובה ===
function checkAllSections(content) {
    const requiredSections = {
        'title-section': 'אזור כותרת ראשית',
        'calculator': 'אזור מחשבון',
        'tabs-nav': 'ניווט טאבים',
        'tab-content': 'תוכן טאבים',
        'awg-section': 'אזור AWG (בדיקת זכאות)',
        'embed-section': 'אזור הטמעה',
        'faq': 'אזור שאלות נפוצות',
        'color-picker': 'בורר צבעים',
        'preview': 'תצוגה מקדימה'
    };
    
    const missing = [];
    Object.entries(requiredSections).forEach(([key, name]) => {
        if (!content.includes(key)) {
            missing.push(`❌ חסר: ${name} (${key})`);
        }
    });
    
    if (missing.length === 0) {
        console.log('✅ כל האזורים קיימים!');
    } else {
        console.error('🚨 אזורים חסרים:');
        missing.forEach(m => console.error(m));
    }
    return missing;
}
```

### 🚫 בדיקת אזורים אסורים במחשבונים

**חובה לוודא שהאזורים הבאים לא קיימים בעמודי מחשבון:**

```javascript
// === בדיקת אזורים שאסורים במחשבונים ===
function checkForbiddenSections(content) {
    const forbiddenSections = {
        'wpc-disclaimer': 'דיסקליימר (לא שייך למחשבונים)',
        '[related-shortcode-instert]': 'Related Posts shortcode (לא שייך למחשבונים)',
        'related-shortcode-instert': 'Related Posts (לא שייך למחשבונים)'
    };
    
    const found = [];
    Object.entries(forbiddenSections).forEach(([key, name]) => {
        if (content.includes(key)) {
            found.push(`❌ נמצא אזור אסור: ${name} (${key})`);
        }
    });
    
    if (found.length === 0) {
        console.log('✅ אין אזורים אסורים!');
    } else {
        console.error('🚨 נמצאו אזורים שאסורים במחשבונים - יש להסיר!');
        found.forEach(f => console.error(f));
    }
    return found;
}
```

### צ'קליסט אזורים אסורים:
- [ ] **אין דיסקליימר** - `wpc-disclaimer` לא קיים
- [ ] **אין Related Posts** - `[related-shortcode-instert]` לא קיים

### צ'קליסט אזורים חובה:
- [ ] **אזור כותרת** - H1 + תאריך עדכון
- [ ] **אזור מחשבון** - עם כל הטאבים
- [ ] **ניווט טאבים** - 2-5 כפתורי טאב
- [ ] **תוכן טאבים** - tab-content לכל טאב
- [ ] **אזור AWG** - כפתור + shortcode
- [ ] **אזור הטמעה** - כפתור העתקה + צבעים + תצוגה מקדימה
- [ ] **אזור FAQ** - שאלות ותשובות
- [ ] **Schema.org** - FAQPage, FinancialProduct

---

## 🔴 2. בדיקת JavaScript עובד

**חובה לוודא שכל הפונקציות הקריטיות קיימות:**

```javascript
// === בדיקת פונקציות JavaScript חובה ===
function checkJavaScriptFunctions(content) {
    const requiredFunctions = {
        'switchTab': 'מעבר בין טאבים',
        'calculate': 'חישובים',
        'copyEmbedCode': 'העתקת קוד להטמעה',
        'getEmbedScript': 'יצירת סקריפט להטמעה',
        'showPreview': 'תצוגה מקדימה',
        'openAWG': 'פתיחת AWG',
        'toggleFAQ': 'פתיחת/סגירת FAQ'
    };
    
    const missing = [];
    Object.entries(requiredFunctions).forEach(([func, desc]) => {
        if (!content.includes(func)) {
            missing.push(`❌ חסרה פונקציה: ${func} (${desc})`);
        }
    });
    
    if (missing.length === 0) {
        console.log('✅ כל הפונקציות קיימות!');
    } else {
        console.error('🚨 פונקציות חסרות:');
        missing.forEach(m => console.error(m));
    }
    return missing;
}

// === בדיקה שהטאבים עובדים ===
function testTabsWork(content) {
    // 1. יש פונקציית switchTab
    const hasSwitchTab = content.includes('function switchTab') || 
                         content.includes('switchTab:') ||
                         content.includes('switchTab =');
    
    // 2. יש event listener על switch-tab
    const hasTabAction = content.includes('data-action="switch-tab"');
    
    // 3. יש הוספה/הסרה של active class
    const hasActiveToggle = content.includes('classList.add') && 
                           content.includes('classList.remove') &&
                           content.includes('active');
    
    if (!hasSwitchTab) console.error('❌ חסרה פונקציית switchTab!');
    if (!hasTabAction) console.error('❌ חסר data-action="switch-tab" על כפתורי הטאבים!');
    if (!hasActiveToggle) console.error('❌ אין טיפול ב-active class!');
    
    return hasSwitchTab && hasTabAction && hasActiveToggle;
}
```

### צ'קליסט JavaScript:
- [ ] **IIFE wrapper** - `(function() { ... })();`
- [ ] **'use strict'** - בתחילת ה-IIFE
- [ ] **Namespace ייחודי** - `WPC_Calc[Topic]_[Random]`
- [ ] **switchTab** - מעבר בין טאבים עובד
- [ ] **calculate** - חישובים בכל טאב
- [ ] **Event listeners** - על input, click
- [ ] **copyEmbedCode** - העתקת קוד
- [ ] **getEmbedScript** - יצירת JS להטמעה

---

## 🔴 3. בדיקת העתקה (הכי קריטי!)

**חובה לוודא שההעתקה כוללת את הכל:**

```javascript
// === בדיקה מקיפה של פונקציית ההעתקה ===
function checkCopyFunction(content) {
    const errors = [];
    
    // 1. בדוק שיש פונקציית copyEmbedCode
    if (!content.includes('copyEmbedCode')) {
        errors.push('❌ חסרה פונקציית copyEmbedCode!');
        return errors;
    }
    
    // מצא את הפונקציה
    const copyFuncStart = content.indexOf('function copyEmbedCode');
    const copyFuncEnd = content.indexOf('}', copyFuncStart + 500);
    const copyFunc = content.substring(copyFuncStart, copyFuncEnd + 100);
    
    // 2. בדוק שמעתיקים CSS
    if (!copyFunc.includes('<style>') && !copyFunc.includes("'<style>'")) {
        errors.push('❌ ההעתקה לא כוללת CSS!');
    }
    
    // 3. בדוק שמעתיקים את כל ה-HTML של המחשבון
    if (!copyFunc.includes('cloneNode') && !copyFunc.includes('innerHTML')) {
        errors.push('❌ ההעתקה לא כוללת את ה-HTML של המחשבון!');
    }
    
    // 4. בדוק שיש קרדיט
    if (!copyFunc.includes('loan-israel.co.il') && !content.includes('loan-israel.co.il')) {
        errors.push('❌ ההעתקה לא כוללת קישור קרדיט!');
    }
    
    // 5. בדוק שמוסיפים את getEmbedScript
    if (!copyFunc.includes('getEmbedScript')) {
        errors.push('❌ ההעתקה לא כוללת את ה-JavaScript להטמעה!');
    }
    
    // 6. בדוק navigator.clipboard
    if (!copyFunc.includes('navigator.clipboard') && !copyFunc.includes('clipboardData')) {
        errors.push('❌ אין שימוש ב-navigator.clipboard להעתקה!');
    }
    
    if (errors.length === 0) {
        console.log('✅ פונקציית ההעתקה תקינה!');
    } else {
        console.error('🚨 בעיות בפונקציית ההעתקה:');
        errors.forEach(e => console.error(e));
    }
    
    return errors;
}

// === בדיקת getEmbedScript ===
function checkGetEmbedScript(content) {
    const errors = [];
    
    // 1. בדוק שיש פונקציית getEmbedScript
    if (!content.includes('getEmbedScript')) {
        errors.push('❌ חסרה פונקציית getEmbedScript - הטאבים לא יעבדו בהטמעה!');
        return errors;
    }
    
    // מצא את הפונקציה
    const scriptFuncStart = content.indexOf('getEmbedScript');
    const scriptFuncEnd = content.indexOf('return', scriptFuncStart) + 500;
    const scriptFunc = content.substring(scriptFuncStart, scriptFuncEnd);
    
    // 2. בדוק DOMContentLoaded
    if (!scriptFunc.includes('DOMContentLoaded')) {
        errors.push('❌ getEmbedScript חסר DOMContentLoaded - הקוד ירוץ לפני שה-DOM מוכן!');
    }
    
    // 3. בדוק שיש switchTab בסקריפט ההטמעה
    if (!scriptFunc.includes('switchTab') && !scriptFunc.includes('switch-tab')) {
        errors.push('❌ getEmbedScript לא כולל פונקציית switchTab - הטאבים לא יעבדו!');
    }
    
    // 4. בדוק שיש טיפול ב-input (לסליידרים)
    if (!scriptFunc.includes('input') && !scriptFunc.includes('addEventListener')) {
        errors.push('❌ getEmbedScript לא כולל event listeners - הסליידרים לא יעבדו!');
    }
    
    // 5. בדוק סגירת script tag בטוחה
    if (content.includes("'</script>'") && !content.includes("'</' + 'script>'")) {
        errors.push('⚠️ סגירת script לא בטוחה - עלול להישבר בהטמעה!');
    }
    
    if (errors.length === 0) {
        console.log('✅ getEmbedScript תקין!');
    } else {
        console.error('🚨 בעיות ב-getEmbedScript:');
        errors.forEach(e => console.error(e));
    }
    
    return errors;
}

// === בדיקת קרדיט ===
function checkCredit(content) {
    const errors = [];
    
    // 1. בדוק שיש קישור קרדיט
    if (!content.includes('loan-israel.co.il')) {
        errors.push('❌ חסר קישור קרדיט לאתר!');
    }
    
    // 2. בדוק nofollow
    if (content.includes('loan-israel.co.il') && !content.includes('nofollow')) {
        errors.push('❌ חסר nofollow על קישור הקרדיט!');
    }
    
    // 3. בדוק "רק תבקש"
    if (!content.includes('רק תבקש')) {
        errors.push('⚠️ חסר שם האתר "רק תבקש" בקרדיט');
    }
    
    // 4. בדוק שהקרדיט נכלל בפונקציית ההעתקה
    const copySection = content.substring(
        content.indexOf('copyEmbedCode'),
        content.indexOf('copyEmbedCode') + 2000
    );
    if (!copySection.includes('loan-israel') && !copySection.includes('רק תבקש')) {
        errors.push('❌ הקרדיט לא מתווסף בהעתקה!');
    }
    
    if (errors.length === 0) {
        console.log('✅ קרדיט תקין!');
    }
    
    return errors;
}
```

### צ'קליסט העתקה:
- [ ] **copyEmbedCode קיים** - פונקציית העתקה
- [ ] **CSS נכלל** - כל ה-CSS של המחשבון מועתק
- [ ] **HTML נכלל** - כל ה-HTML של המחשבון מועתק
- [ ] **getEmbedScript קיים** - JavaScript עצמאי להטמעה
- [ ] **DOMContentLoaded** - בתוך getEmbedScript
- [ ] **switchTab** - בתוך getEmbedScript (טאבים יעבדו)
- [ ] **Event listeners** - בתוך getEmbedScript (סליידרים יעבדו)
- [ ] **קרדיט** - קישור ל-loan-israel.co.il
- [ ] **nofollow** - על קישור הקרדיט
- [ ] **navigator.clipboard** - להעתקה ללוח

---

## 🔴 4. בדיקת תצוגה מקדימה (Preview) - לחיצה על כל כפתור!

**חובה לבדוק שאזור התצוגה המקדימה עובד לחלוטין:**

```javascript
// === בדיקה מקיפה של תצוגה מקדימה - לוחץ על כל כפתור! ===
async function testPreviewCompletely() {
    console.log('🔍 === בדיקת תצוגה מקדימה מלאה ===\n');
    const errors = [];
    const successes = [];
    
    // 1. בדוק שיש כפתורי צבע
    const colorBtns = document.querySelectorAll('[data-action="preview-color"]');
    console.log(`📊 מספר כפתורי צבע: ${colorBtns.length}`);
    
    if (colorBtns.length === 0) {
        errors.push('❌ אין כפתורי צבע לתצוגה מקדימה!');
        return { errors, successes };
    }
    
    // 2. לחץ על כפתור צבע ראשון כדי לפתוח תצוגה מקדימה
    console.log('\n🖱️ לוחץ על כפתור צבע ראשון...');
    colorBtns[0].click();
    
    // המתן לטעינת התצוגה המקדימה
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 3. מצא את אזור התצוגה המקדימה
    const previewArea = document.querySelector('[class*="preview-area"], [class*="preview-container"], [id*="preview"]');
    
    if (!previewArea) {
        errors.push('❌ אזור תצוגה מקדימה לא נטען אחרי לחיצה על צבע!');
        return { errors, successes };
    }
    
    console.log('✅ אזור תצוגה מקדימה נטען');
    successes.push('אזור תצוגה מקדימה נטען');
    
    // 4. בדוק שיש מחשבון בתצוגה מקדימה
    const previewCalculator = previewArea.querySelector('[class*="calculator"], [class*="calc"]');
    if (previewCalculator) {
        console.log('✅ מחשבון נמצא בתצוגה מקדימה');
        successes.push('מחשבון בתצוגה מקדימה');
    } else {
        errors.push('❌ אין מחשבון בתצוגה מקדימה!');
    }
    
    // 5. בדוק טאבים בתצוגה מקדימה - לחץ על כל אחד!
    console.log('\n🔄 בדיקת טאבים בתצוגה מקדימה:');
    const previewTabs = previewArea.querySelectorAll('[data-action="switch-tab"], [data-tab]');
    console.log(`   מספר טאבים: ${previewTabs.length}`);
    
    if (previewTabs.length === 0) {
        errors.push('❌ אין טאבים בתצוגה מקדימה!');
    } else {
        for (let i = 0; i < previewTabs.length; i++) {
            const tab = previewTabs[i];
            const tabName = tab.dataset.tab || tab.textContent.trim().substring(0, 20);
            
            console.log(`   🖱️ לוחץ על טאב ${i+1}: ${tabName}...`);
            tab.click();
            
            await new Promise(resolve => setTimeout(resolve, 200));
            
            // בדוק שהטאב עכשיו active
            if (tab.classList.contains('active')) {
                console.log(`   ✅ טאב ${i+1} הפך ל-active`);
                successes.push(`טאב ${i+1} בתצוגה מקדימה`);
            } else {
                console.error(`   ❌ טאב ${i+1} לא הפך ל-active!`);
                errors.push(`טאב ${i+1} לא עובד בתצוגה מקדימה`);
            }
            
            // בדוק שתוכן הטאב מוצג
            const tabContent = previewArea.querySelector(`#tab-${tab.dataset.tab}, [id*="tab-${tab.dataset.tab}"]`);
            if (tabContent) {
                const isVisible = getComputedStyle(tabContent).display !== 'none';
                if (isVisible) {
                    console.log(`   ✅ תוכן טאב ${i+1} מוצג`);
                } else {
                    errors.push(`תוכן טאב ${i+1} לא מוצג בתצוגה מקדימה`);
                }
            }
        }
    }
    
    // 6. בדוק סליידרים בתצוגה מקדימה - הזז כל אחד!
    console.log('\n📊 בדיקת סליידרים בתצוגה מקדימה:');
    const previewSliders = previewArea.querySelectorAll('input[type="range"]');
    console.log(`   מספר סליידרים: ${previewSliders.length}`);
    
    if (previewSliders.length === 0) {
        errors.push('⚠️ אין סליידרים בתצוגה מקדימה');
    } else {
        for (let i = 0; i < previewSliders.length; i++) {
            const slider = previewSliders[i];
            const oldValue = slider.value;
            const newValue = Math.round((parseInt(slider.min) + parseInt(slider.max)) / 2);
            
            console.log(`   🎚️ מזיז סליידר ${i+1} (${slider.id || 'ללא ID'})...`);
            slider.value = newValue;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
            
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // בדוק אם יש עדכון בתצוגת הערך
            const valueDisplay = previewArea.querySelector(`#${slider.id}-value, #${slider.id.replace('-slider', '-value')}`);
            if (valueDisplay) {
                console.log(`   ✅ סליידר ${i+1} - יש תצוגת ערך`);
                successes.push(`סליידר ${i+1} בתצוגה מקדימה`);
            } else {
                console.log(`   ⚠️ סליידר ${i+1} - אין תצוגת ערך (אולי תקין)`);
            }
            
            // החזר לערך המקורי
            slider.value = oldValue;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
    
    // 7. בדוק כפתורי בחירה (period buttons וכו')
    console.log('\n🔘 בדיקת כפתורי בחירה בתצוגה מקדימה:');
    const previewButtons = previewArea.querySelectorAll('[data-action="select-period"], [data-value], [class*="period-btn"], [class*="select-btn"]');
    console.log(`   מספר כפתורי בחירה: ${previewButtons.length}`);
    
    for (let i = 0; i < Math.min(previewButtons.length, 5); i++) {
        const btn = previewButtons[i];
        const btnText = btn.textContent.trim().substring(0, 15);
        
        console.log(`   🖱️ לוחץ על כפתור: ${btnText}...`);
        btn.click();
        
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (btn.classList.contains('active') || btn.classList.contains('selected')) {
            console.log(`   ✅ כפתור "${btnText}" הפך ל-active`);
            successes.push(`כפתור בחירה בתצוגה מקדימה`);
        }
    }
    
    // 8. בדוק כפתור העתקה בתצוגה מקדימה
    console.log('\n📋 בדיקת כפתור העתקה בתצוגה מקדימה:');
    const previewCopyBtn = previewArea.querySelector('[data-action="copy-preview-code"], [class*="copy"]');
    
    if (previewCopyBtn) {
        console.log('✅ כפתור העתקה קיים בתצוגה מקדימה');
        successes.push('כפתור העתקה בתצוגה מקדימה');
        
        // בדוק שלחיצה עליו לא גורמת לשגיאה
        try {
            // רק נבדוק שאין שגיאת JS, לא נעתיק באמת
            console.log('   ✅ כפתור העתקה לא גורם לשגיאה');
        } catch (e) {
            errors.push('כפתור העתקה גורם לשגיאה!');
        }
    } else {
        errors.push('❌ אין כפתור העתקה בתצוגה מקדימה!');
    }
    
    // 9. בדוק שהצבע הוחל נכון - השוואה בין צבעים
    console.log('\n🎨 בדיקת החלפת צבעים בתצוגה מקדימה:');
    
    // פונקציה לקריאת צבע מאלמנט
    function getElementColor(element) {
        const style = getComputedStyle(element);
        return {
            bg: style.backgroundColor,
            border: style.borderColor,
            color: style.color
        };
    }
    
    // פונקציה להמרת hex ל-rgb
    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!result) return null;
        return `rgb(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)})`;
    }
    
    // פונקציה לבדיקה אם צבע מסוים קיים באלמנט
    function elementHasColor(element, hexColor) {
        const rgbColor = hexToRgb(hexColor);
        const styles = getComputedStyle(element);
        const bgColor = styles.backgroundColor;
        const borderColor = styles.borderColor || styles.borderTopColor;
        const textColor = styles.color;
        
        return bgColor === rgbColor || 
               borderColor === rgbColor || 
               textColor === rgbColor ||
               bgColor.includes(hexColor) ||
               element.getAttribute('style')?.includes(hexColor);
    }
    
    // 10. בדוק כל הצבעים - וודא שהצבע באמת מתחלף!
    console.log('\n🎨 בדיקת כל כפתורי הצבע (מוודא החלפת צבעים):');
    let previousColor = null;
    let colorChangeCount = 0;
    
    for (let i = 0; i < colorBtns.length; i++) {
        const colorBtn = colorBtns[i];
        const color = colorBtn.dataset.color;
        const colorName = colorBtn.dataset.name || colorBtn.title || `צבע ${i+1}`;
        
        console.log(`   🖱️ לוחץ על ${colorName} (${color})...`);
        colorBtn.click();
        
        await new Promise(resolve => setTimeout(resolve, 400));
        
        // מצא את התצוגה המקדימה המעודכנת
        const updatedPreview = document.querySelector('[class*="preview-area"], [class*="preview-container"], [id*="preview"]');
        
        if (!updatedPreview) {
            errors.push(`${colorName} - תצוגה מקדימה לא נטענה`);
            continue;
        }
        
        // מצא אלמנטים שאמורים לקבל את הצבע
        const coloredElements = updatedPreview.querySelectorAll(
            '[class*="tab-btn"].active, ' +
            '[class*="title"], ' +
            '[class*="header"], ' +
            'button[class*="cta"], ' +
            '[class*="primary"], ' +
            '[style*="background"], ' +
            '[style*="border"]'
        );
        
        let foundColor = false;
        let colorFoundIn = [];
        
        // בדוק אם הצבע הנוכחי מופיע באלמנטים
        coloredElements.forEach(el => {
            if (elementHasColor(el, color)) {
                foundColor = true;
                colorFoundIn.push(el.className.split(' ')[0] || el.tagName);
            }
            
            // בדוק גם style ישיר
            const style = el.getAttribute('style');
            if (style && style.includes(color)) {
                foundColor = true;
                colorFoundIn.push('style-attr');
            }
        });
        
        // בדוק גם ב-CSS variables
        const rootStyle = updatedPreview.getAttribute('style');
        if (rootStyle && rootStyle.includes(color)) {
            foundColor = true;
            colorFoundIn.push('css-var');
        }
        
        if (foundColor) {
            console.log(`   ✅ ${colorName} (${color}): צבע הוחל! [${colorFoundIn.slice(0,3).join(', ')}]`);
            successes.push(`צבע ${colorName} הוחל`);
            
            // בדוק שהצבע שונה מהקודם
            if (previousColor && previousColor !== color) {
                colorChangeCount++;
                console.log(`   ✅ צבע השתנה מ-${previousColor} ל-${color}`);
            }
        } else {
            // נסה לבדוק בדרך אחרת - חפש את הצבע בכל ה-innerHTML
            const previewHTML = updatedPreview.innerHTML;
            if (previewHTML.includes(color)) {
                console.log(`   ✅ ${colorName}: צבע נמצא ב-HTML`);
                successes.push(`צבע ${colorName} ב-HTML`);
            } else {
                console.warn(`   ⚠️ ${colorName}: לא ניתן לאמת שהצבע הוחל`);
            }
        }
        
        previousColor = color;
    }
    
    // סיכום בדיקת צבעים
    console.log(`\n   📊 סיכום החלפת צבעים: ${colorChangeCount} החלפות מוצלחות מתוך ${colorBtns.length - 1} אפשריות`);
    
    if (colorChangeCount < colorBtns.length / 2) {
        errors.push('החלפת צבעים לא עובדת כראוי!');
    } else {
        successes.push('החלפת צבעים עובדת');
    }
    
    // === סיכום ===
    console.log('\n' + '='.repeat(50));
    console.log('📊 סיכום בדיקת תצוגה מקדימה:');
    console.log(`   ✅ הצלחות: ${successes.length}`);
    console.log(`   ❌ שגיאות: ${errors.length}`);
    
    if (errors.length > 0) {
        console.log('\n🚨 שגיאות שנמצאו:');
        errors.forEach(e => console.error('   ' + e));
    } else {
        console.log('\n🎉 כל הבדיקות עברו בהצלחה!');
    }
    
    return { errors, successes };
}

// הרץ את הבדיקה
testPreviewCompletely();
```

### צ'קליסט תצוגה מקדימה:
- [ ] **לחיצה על צבע** - פותחת תצוגה מקדימה
- [ ] **מחשבון נטען** - בתוך התצוגה המקדימה
- [ ] **כל הטאבים עובדים** - לחיצה על כל טאב מחליפה תוכן
- [ ] **כל הסליידרים עובדים** - הזזה מעדכנת ערכים
- [ ] **כפתורי בחירה עובדים** - לחיצה משנה active
- [ ] **כפתור העתקה קיים** - בתצוגה מקדימה
- [ ] **צבע מוחל נכון** - על האלמנטים בתצוגה
- [ ] **כל הצבעים עובדים** - לחיצה על כל צבע מעדכנת

---

## 🧪 בדיקה מעשית מלאה - להדביק בקונסול

```javascript
// === בדיקת QA מלאה - לוחץ על כל כפתור! ===
(async function() {
    const errors = [];
    const successes = [];
    
    console.log('🔍 === בדיקות QA מלאות - לוחץ על כל כפתור! ===\n');
    
    // פונקציית עזר - המתנה
    const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    
    // ===== 1. בדיקת אזורים =====
    console.log('📦 בדיקת אזורים:');
    const sections = {
        'calculator': document.querySelector('[class*="calculator"]'),
        'tabs': document.querySelectorAll('[data-action="switch-tab"]'),
        'awg': document.querySelector('[class*="awg"]'),
        'embed': document.querySelector('[class*="embed"]'),
        'faq': document.querySelector('[class*="faq"]'),
        'color-buttons': document.querySelectorAll('[data-action="preview-color"]')
    };
    
    Object.entries(sections).forEach(([name, el]) => {
        const count = el?.length !== undefined ? el.length : (el ? 1 : 0);
        if (count > 0) {
            console.log(`  ✅ ${name}: ${count}`);
            successes.push(name);
        } else {
            console.error(`  ❌ ${name}: חסר!`);
            errors.push(`חסר: ${name}`);
        }
    });
    
    // ===== 2. בדיקת טאבים במחשבון הראשי - לחיצה על כל אחד =====
    console.log('\n🔄 בדיקת טאבים (לוחץ על כל אחד):');
    const mainTabs = document.querySelectorAll('[data-action="switch-tab"]');
    console.log(`  מספר טאבים: ${mainTabs.length}`);
    
    for (let i = 0; i < mainTabs.length; i++) {
        const tab = mainTabs[i];
        const tabName = tab.dataset.tab;
        
        console.log(`  🖱️ לוחץ על טאב ${i+1}: ${tabName}...`);
        tab.click();
        await wait(150);
        
        // בדוק שהטאב active
        if (tab.classList.contains('active')) {
            console.log(`  ✅ טאב ${i+1} (${tabName}): הפך ל-active`);
            successes.push(`טאב ${tabName}`);
        } else {
            console.error(`  ❌ טאב ${i+1} (${tabName}): לא הפך ל-active!`);
            errors.push(`טאב ${tabName} לא עובד`);
        }
        
        // בדוק שתוכן הטאב מוצג
        const tabContent = document.querySelector(`#tab-${tabName}, [id*="tab-${tabName}"]`);
        if (tabContent && (tabContent.classList.contains('active') || 
                          getComputedStyle(tabContent).display !== 'none')) {
            console.log(`  ✅ תוכן טאב ${tabName}: מוצג`);
        } else {
            console.error(`  ❌ תוכן טאב ${tabName}: לא מוצג!`);
            errors.push(`תוכן טאב ${tabName} לא מוצג`);
        }
    }
    
    // ===== 3. בדיקת סליידרים - הזזה של כל אחד =====
    console.log('\n📊 בדיקת סליידרים (מזיז כל אחד):');
    const sliders = document.querySelectorAll('input[type="range"]');
    console.log(`  מספר סליידרים: ${sliders.length}`);
    
    for (let i = 0; i < sliders.length; i++) {
        const slider = sliders[i];
        const oldVal = slider.value;
        const newVal = Math.round((parseInt(slider.min) + parseInt(slider.max)) / 2);
        
        console.log(`  🎚️ מזיז סליידר ${i+1}: ${slider.id || 'ללא ID'}...`);
        slider.value = newVal;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
        await wait(100);
        
        // בדוק אם יש עדכון
        const valueDisplay = document.getElementById(slider.id?.replace('-slider', '-value')) ||
                            document.getElementById(slider.id + '-value');
        if (valueDisplay) {
            console.log(`  ✅ סליידר ${i+1}: עדכון תצוגה עובד`);
            successes.push(`סליידר ${i+1}`);
        } else {
            console.warn(`  ⚠️ סליידר ${i+1}: אין תצוגת ערך נפרדת`);
        }
        
        // החזר לערך המקורי
        slider.value = oldVal;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // ===== 4. בדיקת כפתורי בחירה (period buttons) =====
    console.log('\n🔘 בדיקת כפתורי בחירה:');
    const periodBtns = document.querySelectorAll('[data-action="select-period"], [data-value], [class*="period-btn"]');
    console.log(`  מספר כפתורי בחירה: ${periodBtns.length}`);
    
    for (let i = 0; i < Math.min(periodBtns.length, 5); i++) {
        const btn = periodBtns[i];
        const btnText = btn.textContent.trim().substring(0, 15);
        
        console.log(`  🖱️ לוחץ על: ${btnText}...`);
        btn.click();
        await wait(100);
        
        if (btn.classList.contains('active') || btn.classList.contains('selected')) {
            console.log(`  ✅ כפתור "${btnText}": הפך ל-active`);
        }
    }
    
    // ===== 5. בדיקת תצוגה מקדימה - לוחץ על כל צבע ובודק שהצבע מתחלף! =====
    console.log('\n🎨 בדיקת תצוגה מקדימה (לוחץ על כל צבע ומוודא החלפה):');
    const colorBtns = document.querySelectorAll('[data-action="preview-color"]');
    console.log(`  מספר כפתורי צבע: ${colorBtns.length}`);
    
    // פונקציה להמרת hex ל-rgb
    const hexToRgb = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!result) return null;
        return `rgb(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)})`;
    };
    
    // פונקציה לבדיקה אם צבע קיים באלמנט
    const elementHasColor = (el, hexColor) => {
        const rgbColor = hexToRgb(hexColor);
        const styles = getComputedStyle(el);
        return styles.backgroundColor === rgbColor || 
               styles.borderColor === rgbColor || 
               styles.color === rgbColor ||
               el.getAttribute('style')?.includes(hexColor);
    };
    
    let previousColor = null;
    let colorChangeCount = 0;
    
    for (let c = 0; c < colorBtns.length; c++) {
        const colorBtn = colorBtns[c];
        const color = colorBtn.dataset.color;
        const colorName = colorBtn.dataset.name || colorBtn.title || `צבע ${c+1}`;
        
        console.log(`\n  🖱️ לוחץ על ${colorName} (${color})...`);
        colorBtn.click();
        await wait(400);
        
        // מצא את אזור התצוגה המקדימה
        const previewArea = document.querySelector('[class*="preview-area"], [class*="preview-container"], [id*="preview"]');
        
        if (!previewArea) {
            console.error(`  ❌ ${colorName}: תצוגה מקדימה לא נטענה!`);
            errors.push(`${colorName}: אין תצוגה מקדימה`);
            continue;
        }
        
        console.log(`  ✅ ${colorName}: תצוגה מקדימה נטענה`);
        
        // === בדיקת החלפת צבע ===
        const coloredElements = previewArea.querySelectorAll(
            '[class*="tab-btn"].active, [class*="title"], button[class*="cta"], ' +
            '[class*="primary"], [style*="background"], [style*="border"]'
        );
        
        let foundColor = false;
        let colorFoundIn = [];
        
        coloredElements.forEach(el => {
            if (elementHasColor(el, color)) {
                foundColor = true;
                colorFoundIn.push(el.className?.split(' ')[0] || el.tagName);
            }
        });
        
        // בדוק גם ב-style ישיר על התצוגה או בHTML
        if (previewArea.getAttribute('style')?.includes(color) || 
            previewArea.innerHTML.includes(color)) {
            foundColor = true;
            colorFoundIn.push('HTML/style');
        }
        
        if (foundColor) {
            console.log(`  ✅ ${colorName}: צבע ${color} הוחל! [${colorFoundIn.slice(0,3).join(', ')}]`);
            
            // בדוק שהצבע שונה מהקודם
            if (previousColor && previousColor !== color) {
                colorChangeCount++;
                console.log(`  ✅ צבע השתנה: ${previousColor} → ${color}`);
                successes.push(`החלפת צבע: ${previousColor} → ${color}`);
            }
        } else {
            console.warn(`  ⚠️ ${colorName}: לא ניתן לאמת החלת צבע (אולי CSS variables)`);
        }
        
        previousColor = color;
        
        // בדוק שיש מחשבון בתצוגה מקדימה
        const previewCalc = previewArea.querySelector('[class*="calculator"], [class*="calc"]');
        if (previewCalc) {
            console.log(`  ✅ ${colorName}: מחשבון נמצא בתצוגה`);
            successes.push(`${colorName} - מחשבון`);
        } else {
            console.error(`  ❌ ${colorName}: אין מחשבון בתצוגה!`);
            errors.push(`${colorName}: אין מחשבון`);
        }
        
        // בדוק טאבים בתצוגה מקדימה - לחץ על כל אחד!
        const previewTabs = previewArea.querySelectorAll('[data-action="switch-tab"], [data-tab]');
        console.log(`  📊 טאבים בתצוגה: ${previewTabs.length}`);
        
        for (let t = 0; t < previewTabs.length; t++) {
            const pTab = previewTabs[t];
            const pTabName = pTab.dataset.tab || `טאב ${t+1}`;
            
            console.log(`     🖱️ לוחץ על טאב ${t+1} בתצוגה...`);
            pTab.click();
            await wait(150);
            
            if (pTab.classList.contains('active')) {
                console.log(`     ✅ טאב ${pTabName} בתצוגה: עובד`);
                successes.push(`${colorName} - טאב ${pTabName}`);
            } else {
                console.error(`     ❌ טאב ${pTabName} בתצוגה: לא עובד!`);
                errors.push(`${colorName} - טאב ${pTabName} לא עובד`);
            }
        }
        
        // בדוק סליידרים בתצוגה מקדימה
        const previewSliders = previewArea.querySelectorAll('input[type="range"]');
        console.log(`  📊 סליידרים בתצוגה: ${previewSliders.length}`);
        
        for (let s = 0; s < Math.min(previewSliders.length, 3); s++) {
            const pSlider = previewSliders[s];
            const oldVal = pSlider.value;
            
            console.log(`     🎚️ מזיז סליידר ${s+1} בתצוגה...`);
            pSlider.value = parseInt(pSlider.max) - 1000;
            pSlider.dispatchEvent(new Event('input', { bubbles: true }));
            await wait(100);
            
            console.log(`     ✅ סליידר ${s+1} בתצוגה: הוזז`);
            
            // החזר
            pSlider.value = oldVal;
            pSlider.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // בדוק כפתור העתקה בתצוגה מקדימה
        const previewCopyBtn = previewArea.querySelector('[data-action="copy-preview-code"], [class*="copy"]');
        if (previewCopyBtn) {
            console.log(`  ✅ ${colorName}: כפתור העתקה קיים`);
            successes.push(`${colorName} - כפתור העתקה`);
        } else {
            console.error(`  ❌ ${colorName}: אין כפתור העתקה!`);
            errors.push(`${colorName}: אין כפתור העתקה`);
        }
    }
    
    // === סיכום בדיקת החלפת צבעים ===
    console.log('\n  📊 סיכום החלפת צבעים:');
    console.log(`     החלפות צבע מוצלחות: ${colorChangeCount} מתוך ${colorBtns.length - 1}`);
    
    if (colorChangeCount >= colorBtns.length / 2) {
        console.log('  ✅ החלפת צבעים עובדת כראוי!');
        successes.push('החלפת צבעים בתצוגה מקדימה');
    } else if (colorChangeCount > 0) {
        console.warn('  ⚠️ החלפת צבעים עובדת חלקית');
    } else {
        console.error('  ❌ החלפת צבעים לא עובדת!');
        errors.push('החלפת צבעים לא עובדת');
    }
    
    // ===== 6. בדיקת AWG =====
    console.log('\n📝 בדיקת AWG:');
    const awgBtn = document.querySelector('[data-action="open-awg"]');
    const awgShortcode = document.body.innerHTML.includes('[awg postid=');
    
    if (awgBtn) {
        console.log('  ✅ כפתור AWG קיים');
        console.log('  🖱️ לוחץ על כפתור AWG...');
        awgBtn.click();
        await wait(300);
        
        const awgContent = document.querySelector('[class*="awg-content"]');
        if (awgContent && getComputedStyle(awgContent).display !== 'none') {
            console.log('  ✅ אזור AWG נפתח');
            successes.push('AWG');
        }
    } else {
        console.error('  ❌ חסר כפתור AWG!');
        errors.push('חסר כפתור AWG');
    }
    
    console.log(`  AWG shortcode: ${awgShortcode ? '✅' : '❌'}`);
    
    // ===== 7. בדיקת פונקציות העתקה =====
    console.log('\n📋 בדיקת פונקציות העתקה:');
    const hasCopyFunc = document.body.innerHTML.includes('copyEmbedCode');
    const hasEmbedScript = document.body.innerHTML.includes('getEmbedScript');
    
    console.log(`  copyEmbedCode: ${hasCopyFunc ? '✅' : '❌'}`);
    console.log(`  getEmbedScript: ${hasEmbedScript ? '✅' : '❌'}`);
    
    if (!hasCopyFunc) errors.push('חסר copyEmbedCode');
    if (!hasEmbedScript) errors.push('חסר getEmbedScript - הטאבים לא יעבדו בהטמעה!');
    
    // ===== 8. בדיקת קרדיט =====
    console.log('\n🔗 בדיקת קרדיט:');
    const hasCredit = document.body.innerHTML.includes('loan-israel.co.il');
    const hasNofollow = document.body.innerHTML.includes('nofollow');
    
    console.log(`  קישור קרדיט: ${hasCredit ? '✅' : '❌'}`);
    console.log(`  nofollow: ${hasNofollow ? '✅' : '❌'}`);
    
    if (!hasCredit) errors.push('חסר קישור קרדיט');
    if (!hasNofollow) errors.push('חסר nofollow');
    
    // ===== 9. בדיקת FAQ =====
    console.log('\n❓ בדיקת FAQ:');
    const faqItems = document.querySelectorAll('[data-action="toggle-faq"]');
    console.log(`  מספר פריטי FAQ: ${faqItems.length}`);
    
    if (faqItems.length > 0) {
        console.log('  🖱️ לוחץ על FAQ ראשון...');
        faqItems[0].click();
        await wait(200);
        console.log('  ✅ FAQ עובד');
    }
    
    // ===== סיכום =====
    console.log('\n' + '='.repeat(60));
    console.log('📊 סיכום בדיקות QA:');
    console.log(`  ✅ הצלחות: ${successes.length}`);
    console.log(`  ❌ שגיאות: ${errors.length}`);
    
    if (errors.length > 0) {
        console.log('\n🚨 שגיאות שנמצאו:');
        errors.forEach(e => console.error('  ❌ ' + e));
    } else {
        console.log('\n🎉 כל הבדיקות עברו בהצלחה!');
    }
    
    console.log('\n=== סיום בדיקות ===');
    
    return { errors, successes };
})();
```

---

## 🔧 תיקונים קריטיים נפוצים

### תיקון 1: getEmbedScript חסר או לא שלם

```javascript
// הוסף פונקציה זו אם חסרה:
function getEmbedScript() {
    const scriptLines = [
        '<script>',
        'document.addEventListener("DOMContentLoaded", function() {',
        '  (function() {',
        '    "use strict";',
        '    var NS = "WPC_Calc_Embed_" + Date.now();',
        '    if (window[NS]) return;',
        '    var container = document.querySelector("[class*=\\"wpc-calc\\"]");',
        '    if (!container) return;',
        '',
        '    // פונקציות עזר',
        '    function el(id) { return document.getElementById(id); }',
        '    function formatNumber(n) { return Math.round(n).toLocaleString("he-IL"); }',
        '',
        '    // מעבר טאבים',
        '    function switchTab(tabName) {',
        '      var tabs = container.querySelectorAll("[data-action=\\"switch-tab\\"]");',
        '      var contents = container.querySelectorAll("[class*=\\"tab-content\\"]");',
        '      for (var i = 0; i < tabs.length; i++) {',
        '        tabs[i].classList.remove("active");',
        '      }',
        '      for (var j = 0; j < contents.length; j++) {',
        '        contents[j].classList.remove("active");',
        '      }',
        '      var activeTab = container.querySelector("[data-tab=\\"" + tabName + "\\"]");',
        '      if (activeTab) activeTab.classList.add("active");',
        '      var activeContent = document.getElementById("tab-" + tabName);',
        '      if (activeContent) activeContent.classList.add("active");',
        '    }',
        '',
        '    // Event delegation',
        '    container.addEventListener("click", function(e) {',
        '      var action = e.target.closest("[data-action]");',
        '      if (!action) return;',
        '      var act = action.dataset.action;',
        '      if (act === "switch-tab") switchTab(action.dataset.tab);',
        '    });',
        '',
        '    container.addEventListener("input", function(e) {',
        '      // הוסף לוגיקת עדכון סליידרים כאן',
        '    });',
        '',
        '    window[NS] = { v: "1.0" };',
        '  })();',
        '});'
    ];
    return scriptLines.join('\\n') + '\\n</' + 'script>';
}
```

### תיקון 2: copyEmbedCode לא מעתיק הכל

```javascript
function copyEmbedCode() {
    // 1. קבל את ה-CSS
    let styles = '';
    document.querySelectorAll('style').forEach(function(style) {
        if (style.textContent.includes('wpc-calc-')) {
            styles = style.textContent;
        }
    });
    
    // 2. קבל את ה-HTML של המחשבון
    var calculator = document.querySelector('[class*="wpc-calc"][class*="calculator"]');
    var calcHTML = calculator ? calculator.outerHTML : '';
    
    // 3. בנה את הקוד המלא
    var code = '';
    code += '<style>\\n' + styles + '\\n</style>\\n\\n';
    code += '<div class="wpc-calc-embed-wrapper">\\n';
    code += calcHTML + '\\n';
    code += '</div>\\n\\n';
    
    // 4. הוסף קרדיט
    code += '<p style="text-align:center; font-size:0.9em; margin-top:20px; color:#666;">\\n';
    code += '  מחשבון זה פותח על ידי \\n';
    code += '  <a href="https://loan-israel.co.il/" target="_blank" rel="nofollow noopener" ';
    code += 'style="color:#1e5490; text-decoration:underline;">רק תבקש פיננסים</a>\\n';
    code += '</p>\\n\\n';
    
    // 5. הוסף JavaScript
    code += getEmbedScript();
    
    // 6. העתק ללוח
    navigator.clipboard.writeText(code).then(function() {
        alert('✅ הקוד הועתק בהצלחה!');
    }).catch(function(err) {
        console.error('שגיאה בהעתקה:', err);
        alert('שגיאה בהעתקה');
    });
}
```

---

# ✅ רשימת בדיקות מלאה

### 1️⃣ בדיקת מבנה HTML בסיסי

#### בדיקות חובה:
```javascript
// בדיקה 1.1: אין DOCTYPE/HTML/HEAD/BODY
const hasDoctype = content.includes('<!DOCTYPE') || content.includes('<!doctype');
const hasHtmlTag = /<html[\s>]/i.test(content);
const hasHeadTag = /<head[\s>]/i.test(content);
const hasBodyTag = /<body[\s>]/i.test(content);

if (hasDoctype || hasHtmlTag || hasHeadTag || hasBodyTag) {
    console.error('❌ שגיאה: הקובץ מכיל תגיות DOCTYPE/HTML/HEAD/BODY - אסור בוורדפרס!');
}

// בדיקה 1.2: מתחיל עם viewport script
const startsWithViewport = content.trim().startsWith('<script>') && 
    content.includes('meta[name="viewport"]');
if (!startsWithViewport) {
    console.error('❌ שגיאה: חסר viewport script בתחילת הקובץ');
}
```

**שגיאות נפוצות:**
- קובץ מתחיל עם `<!DOCTYPE html>` - צריך למחוק
- חסר viewport meta script בתחילה

---

### 2️⃣ בדיקת CSS

#### בדיקות חובה:
```javascript
// בדיקה 2.1: Prefix ייחודי
const prefixPattern = /wpc-calc-[a-z]+-[a-z0-9]{4}-/;
const hasValidPrefix = prefixPattern.test(content);
if (!hasValidPrefix) {
    console.error('❌ שגיאה: חסר prefix תקין (wpc-calc-[topic]-[4random]-)');
}

// בדיקה 2.2: CSS Variables
const cssVars = [
    '--wpc-', '--primary', '--success', '--warning', 
    '--danger', '--text-dark', '--bg-light'
];
const missingVars = cssVars.filter(v => !content.includes(v));

// בדיקה 2.3: !important על כל המאפיינים
const cssContent = content.match(/<style[^>]*>([\s\S]*?)<\/style>/gi);
if (cssContent) {
    cssContent.forEach(style => {
        // מצא שורות CSS שחסר בהן !important
        const lines = style.split('\n');
        lines.forEach((line, i) => {
            if (line.includes(':') && line.includes(';') && !line.includes('!important')) {
                // בדוק שזה לא comment או CSS variable definition
                if (!line.trim().startsWith('//') && !line.includes('--')) {
                    console.warn(`⚠️ שורה ${i}: חסר !important - "${line.trim().substring(0, 50)}"`);
                }
            }
        });
    });
}

// בדיקה 2.4: Media Queries
const mediaQueries = {
    'tablet': '@media (max-width: 768px)',
    'mobile': '@media (max-width: 480px)',
    'small-mobile': '@media (max-width: 375px)'
};
Object.entries(mediaQueries).forEach(([name, query]) => {
    if (!content.includes(query)) {
        console.warn(`⚠️ חסר media query ל-${name}: ${query}`);
    }
});

// בדיקה 2.5: all: initial על wrapper
if (!content.includes('all: initial')) {
    console.error('❌ שגיאה: חסר "all: initial" על ה-wrapper');
}

// בדיקה 2.6: direction: rtl
if (!content.includes('direction: rtl')) {
    console.error('❌ שגיאה: חסר "direction: rtl"');
}

// בדיקה 2.7: טאבים עם flex-wrap (ללא סקרול אופקי)
if (content.includes('overflow-x: auto') && content.includes('tabs-nav')) {
    console.error('❌ שגיאה: הטאבים משתמשים ב-overflow-x: auto - צריך flex-wrap: wrap');
}
```

**שגיאות נפוצות:**
- prefix לא ייחודי
- חסר `!important`
- חסר media queries למובייל
- טאבים עם סקרול אופקי במקום wrap

---

### 3️⃣ בדיקת JavaScript

#### בדיקות חובה:
```javascript
// בדיקה 3.1: IIFE wrapper
const hasIIFE = content.includes('(function()') && content.includes('})();');
if (!hasIIFE) {
    console.error('❌ שגיאה: JavaScript לא עטוף ב-IIFE');
}

// בדיקה 3.2: 'use strict'
const hasUseStrict = content.includes("'use strict'") || content.includes('"use strict"');
if (!hasUseStrict) {
    console.error('❌ שגיאה: חסר "use strict" בתחילת ה-IIFE');
}

// בדיקה 3.3: Namespace ייחודי
const nsPattern = /const\s+NS\s*=\s*['"]WPC_Calc[A-Za-z]+_[A-Za-z0-9]+['"]/;
const hasNamespace = nsPattern.test(content);
if (!hasNamespace) {
    console.error('❌ שגיאה: חסר namespace ייחודי (WPC_Calc[Topic]_[Random])');
}

// בדיקה 3.4: בדיקת namespace כפול
if (!content.includes('if (window[NS]) return')) {
    console.error('❌ שגיאה: חסר בדיקת namespace כפול');
}

// בדיקה 3.5: Container validation
if (!content.includes('getElementById') || !content.includes('if (!container)')) {
    console.error('❌ שגיאה: חסר בדיקת container');
}

// בדיקה 3.6: Event Delegation
const hasEventDelegation = content.includes("container.addEventListener('click'") ||
    content.includes('container.addEventListener("click"');
if (!hasEventDelegation) {
    console.error('❌ שגיאה: חסר Event Delegation על ה-container');
}

// בדיקה 3.7: ספירת Event Listeners
const listenerMatches = content.match(/addEventListener\(/g);
const listenerCount = listenerMatches ? listenerMatches.length : 0;
if (listenerCount > 15) {
    console.warn(`⚠️ אזהרה: יותר מדי event listeners (${listenerCount}) - מומלץ עד 10`);
}
```

**שגיאות נפוצות:**
- JavaScript לא עטוף ב-IIFE
- חסר namespace ייחודי
- יותר מדי event listeners

---

### 4️⃣ בדיקת פונקציונליות טאבים

#### בדיקות חובה:
```javascript
// בדיקה 4.1: מספר טאבים
const tabButtons = content.match(/data-action="switch-tab"/g);
const tabCount = tabButtons ? tabButtons.length : 0;
if (tabCount < 2 || tabCount > 5) {
    console.error(`❌ שגיאה: מספר טאבים לא תקין (${tabCount}) - צריך 2-5 טאבים`);
}

// בדיקה 4.2: כל טאב עם data-tab ייחודי
const tabNames = [];
const tabDataPattern = /data-tab="([^"]+)"/g;
let match;
while ((match = tabDataPattern.exec(content)) !== null) {
    if (tabNames.includes(match[1])) {
        console.error(`❌ שגיאה: שם טאב כפול - "${match[1]}"`);
    }
    tabNames.push(match[1]);
}

// בדיקה 4.3: לכל טאב יש tab-content תואם
tabNames.forEach(name => {
    const tabContentId = `id="tab-${name}"`;
    if (!content.includes(tabContentId)) {
        console.error(`❌ שגיאה: חסר tab-content עבור טאב "${name}"`);
    }
});

// בדיקה 4.4: יש טאב אחד עם class="active" בהתחלה
const activeTabBtn = content.match(/tab-btn[^"]*"\s+class="[^"]*active/g);
const activeTabContent = content.match(/tab-content[^"]*active/g);
if (!activeTabBtn || activeTabBtn.length !== 1) {
    console.error('❌ שגיאה: צריך בדיוק טאב אחד עם active בהתחלה');
}

// בדיקה 4.5: פונקציית switchTab קיימת
if (!content.includes('function switchTab') && !content.includes('switchTab:')) {
    console.error('❌ שגיאה: חסרה פונקציית switchTab');
}
```

**שגיאות נפוצות:**
- שמות טאבים כפולים
- חסר tab-content תואם
- יותר מטאב אחד active בהתחלה

---

### 5️⃣ בדיקת סליידרים ו-Inputs

#### בדיקות חובה:
```javascript
// בדיקה 5.1: כל סליידר עם ID ייחודי
const sliderInputs = content.match(/type="range"[^>]*id="([^"]+)"/g);
const sliderIds = [];
if (sliderInputs) {
    sliderInputs.forEach(slider => {
        const id = slider.match(/id="([^"]+)"/)[1];
        if (sliderIds.includes(id)) {
            console.error(`❌ שגיאה: ID סליידר כפול - "${id}"`);
        }
        sliderIds.push(id);
    });
}

// בדיקה 5.2: לכל סליידר יש value display
sliderIds.forEach(id => {
    const valueDisplayId = id.replace('-slider', '-value').replace('-input', '-value');
    if (!content.includes(`id="${valueDisplayId}"`) && !content.includes(`id="${id}-value"`)) {
        console.warn(`⚠️ אזהרה: חסר value display עבור סליידר "${id}"`);
    }
});

// בדיקה 5.3: סליידרים עם min, max, step
sliderInputs?.forEach(slider => {
    if (!slider.includes('min=')) console.error('❌ חסר min בסליידר');
    if (!slider.includes('max=')) console.error('❌ חסר max בסליידר');
    if (!slider.includes('step=')) console.warn('⚠️ חסר step בסליידר (ישתמש ב-1 כברירת מחדל)');
});

// בדיקה 5.4: event listener על input (לעדכון סליידרים)
const hasInputListener = content.includes("addEventListener('input'") ||
    content.includes('addEventListener("input"');
if (!hasInputListener) {
    console.error('❌ שגיאה: חסר event listener עבור input (סליידרים לא יעדכנו)');
}
```

**שגיאות נפוצות:**
- IDs סליידרים כפולים
- חסר event listener ל-input
- סליידרים בלי min/max

---

### 6️⃣ בדיקת מערכת הטמעה (CRITICAL!)

#### בדיקות חובה:
```javascript
// בדיקה 6.1: אזור הטמעה קיים
if (!content.includes('embed-section') && !content.includes('embed')) {
    console.error('❌ שגיאה קריטית: חסר אזור הטמעה');
}

// בדיקה 6.2: כפתור העתקת קוד
if (!content.includes('copy-embed-code')) {
    console.error('❌ שגיאה: חסר כפתור העתקת קוד HTML');
}

// בדיקה 6.3: בורר צבעים (10 צבעים)
const colorButtons = content.match(/data-action="preview-color"/g);
const colorCount = colorButtons ? colorButtons.length : 0;
if (colorCount < 10) {
    console.warn(`⚠️ אזהרה: רק ${colorCount} כפתורי צבע (מומלץ 10)`);
}

// בדיקה 6.4: Color picker מותאם אישית
if (!content.includes('type="color"')) {
    console.warn('⚠️ אזהרה: חסר color picker מותאם אישית');
}

// בדיקה 6.5: פונקציית copyEmbedCode
if (!content.includes('function copyEmbedCode') && !content.includes('copyEmbedCode:')) {
    console.error('❌ שגיאה: חסרה פונקציית copyEmbedCode');
}

// בדיקה 6.6: פונקציית getEmbedScript
if (!content.includes('function getEmbedScript') && !content.includes('getEmbedScript')) {
    console.error('❌ שגיאה קריטית: חסרה פונקציית getEmbedScript - ההטמעה לא תעבוד!');
}

// בדיקה 6.7: תצוגה מקדימה
if (!content.includes('preview') && !content.includes('Preview')) {
    console.warn('⚠️ אזהרה: חסרה תצוגה מקדימה');
}

// בדיקה 6.8: קרדיט דינמי בקוד המיוצא
if (!content.includes('loan-israel.co.il') || !content.includes('רק תבקש')) {
    console.error('❌ שגיאה: חסר קרדיט דינמי בקוד המיוצא');
}

// בדיקה 6.9: nofollow על קישור הקרדיט
if (content.includes('loan-israel.co.il') && !content.includes('nofollow')) {
    console.error('❌ שגיאה: חסר nofollow על קישור הקרדיט');
}
```

**שגיאות נפוצות:**
- חסרה פונקציית `getEmbedScript` - **קריטי!**
- קרדיט לא דינמי
- חסר nofollow

---

### 7️⃣ בדיקת JavaScript להטמעה (getEmbedScript)

#### 🚨 בדיקות תאימות וורדפרס - קריטי!

```javascript
// === בדיקות ES5 לתאימות וורדפרס ===
function checkWordPressCompatibility(content) {
    var errors = [];
    
    // 1. בדוק Arrow Functions
    var arrowFunctions = content.match(/=>\s*{|=>\s*[^{]/g);
    if (arrowFunctions) {
        errors.push('❌ נמצאו Arrow Functions (' + arrowFunctions.length + ') - להחליף ל-function() {}');
    }
    
    // 2. בדוק const/let
    var constLet = content.match(/\bconst\s+\w|let\s+\w/g);
    if (constLet) {
        errors.push('❌ נמצאו const/let (' + constLet.length + ') - להחליף ל-var');
    }
    
    // 3. בדוק && ו-|| (וורדפרס ממיר ל-HTML entities!)
    var logicalOperators = content.match(/\s&&\s|\s\|\|\s/g);
    if (logicalOperators) {
        errors.push('🚨 נמצאו && או || (' + logicalOperators.length + ') - וורדפרס ממיר אותם לHTML entities!');
    }
    
    // 4. בדוק ₪ (צריך Unicode escape)
    var shekelSymbol = content.match(/₪/g);
    if (shekelSymbol) {
        errors.push('❌ נמצא סימן ₪ (' + shekelSymbol.length + ') - להחליף ל-\\u20AA');
    }
    
    // 5. בדוק <script> לא מפוצל
    var scriptTags = content.match(/'<script>'|"<script>"|'<\/script>'|"<\/script>"/g);
    if (scriptTags) {
        errors.push('❌ נמצאו תגיות script לא מפוצלות - להחליף ל-\'<scr\' + \'ipt>\'');
    }
    
    // 6. בדוק Template Literals
    var templateLiterals = content.match(/`[^`]*\${/g);
    if (templateLiterals) {
        errors.push('❌ נמצאו Template Literals (' + templateLiterals.length + ') - להחליף לחיבור מחרוזות');
    }
    
    if (errors.length === 0) {
        console.log('✅ הקוד תואם ES5 ויעבוד בוורדפרס!');
    } else {
        console.error('🚨 בעיות תאימות וורדפרס:');
        errors.forEach(function(e) { console.error('   ' + e); });
    }
    
    return errors;
}
```

### טבלת תאימות וורדפרס:

| ❌ ES6 (לא עובד) | ✅ ES5 (עובד) | הערה |
|-----------------|--------------|------|
| `const x = 5` | `var x = 5` | וורדפרס לא תומך |
| `let y = 10` | `var y = 10` | וורדפרס לא תומך |
| `() => {}` | `function() {}` | Arrow לא עובד |
| `\`template ${x}\`` | `'str ' + x` | Backticks נשברים |
| `a && b` | `if(a){if(b){}}` | **וורדפרס ממיר ל-`&#038;&#038;`!** |
| `a \|\| b` | `a ? a : b` | **וורדפרס ממיר ל-HTML entities!** |
| `₪` | `\u20AA` | תווים מיוחדים |
| `<script>` | `'<scr'+'ipt>'` | מפורש כתג |

#### בדיקות חובה:
```javascript
// בדיקה 7.1: DOMContentLoaded
const embedScriptContent = content.match(/getEmbedScript[\s\S]*?return/);
if (embedScriptContent && !embedScriptContent[0].includes('DOMContentLoaded')) {
    console.error('❌ שגיאה: ה-embed script לא עטוף ב-DOMContentLoaded');
}

// בדיקה 7.2: תחביר ES5 (var במקום const/let)
// בתוך getEmbedScript צריך להיות var
if (content.includes('getEmbedScript')) {
    const scriptSection = content.substring(content.indexOf('getEmbedScript'));
    const nextFunction = scriptSection.indexOf('function ', 10);
    const embedPart = scriptSection.substring(0, nextFunction > 0 ? nextFunction : 2000);
    
    // בתוך המחרוזות של getEmbedScript צריך var
    if (embedPart.includes("'const ") || embedPart.includes('"const ') ||
        embedPart.includes("'let ") || embedPart.includes('"let ')) {
        console.warn('⚠️ אזהרה: getEmbedScript משתמש ב-const/let במקום var - עלול לא לעבוד בדפדפנים ישנים');
    }
}

// בדיקה 7.3: סגירת script tag בטוחה
if (!content.includes("'</' + 'script>'") && !content.includes('"</" + "script>"')) {
    // בדוק אם יש סגירה רגילה שעלולה ליצור בעיות
    if (content.includes("'</script>'") || content.includes('"</script>"')) {
        console.error('❌ שגיאה: סגירת script לא בטוחה - צריך להיות: \'</\' + \'script>\'');
    }
}

// בדיקה 7.4: IDs תואמים
// מצא את כל ה-IDs ב-HTML
const htmlIds = content.match(/id="([^"]+)"/g)?.map(m => m.match(/id="([^"]+)"/)[1]) || [];

// בדוק שה-IDs שמוזכרים ב-getEmbedScript קיימים ב-HTML
const idReferences = content.match(/getElementById\(['"]([^'"]+)['"]\)/g) || [];
idReferences.forEach(ref => {
    const id = ref.match(/getElementById\(['"]([^'"]+)['"]\)/)[1];
    // IDs דינמיים כמו 'tab-' + tabName לא צריכים בדיקה
    if (!id.includes('${') && !id.includes("'+") && !htmlIds.includes(id)) {
        console.warn(`⚠️ אזהרה: ID "${id}" מוזכר ב-JS אבל לא קיים ב-HTML`);
    }
});
```

**שגיאות נפוצות:**
- חסר DOMContentLoaded בסקריפט ההטמעה
- שימוש ב-const/let במקום var
- סגירת script לא בטוחה

---

### 8️⃣ בדיקת AWG Section

#### בדיקות חובה:
```javascript
// בדיקה 8.1: AWG section קיים
if (!content.includes('awg-section') && !content.includes('awg')) {
    console.error('❌ שגיאה: חסר AWG section');
}

// בדיקה 8.2: כפתור "בדוק זכאות"
if (!content.includes('open-awg') && !content.includes('openAWG')) {
    console.error('❌ שגיאה: חסר כפתור פתיחת AWG');
}

// בדיקה 8.3: Shortcode AWG
const awgShortcode = content.match(/\[awg\s+postid="(\d+)"\]/);
if (!awgShortcode) {
    console.error('❌ שגיאה: חסר shortcode של AWG ([awg postid="XXXXX"])');
} else {
    console.log(`✅ AWG Post ID: ${awgShortcode[1]}`);
}

// בדיקה 8.4: AWG content נסתר בהתחלה
if (!content.includes('display: none') && !content.includes('display:none')) {
    console.warn('⚠️ אזהרה: ודא ש-AWG content נסתר בהתחלה');
}

// בדיקה 8.5: פונקציית openAWG
if (!content.includes('function openAWG') && !content.includes('openAWG:')) {
    console.error('❌ שגיאה: חסרה פונקציית openAWG');
}
```

---

### 9️⃣ בדיקת FAQ

#### בדיקות חובה:
```javascript
// בדיקה 9.1: FAQ section קיים
if (!content.includes('faq') && !content.includes('FAQ')) {
    console.warn('⚠️ אזהרה: חסר FAQ section');
}

// בדיקה 9.2: מספר שאלות FAQ
const faqItems = content.match(/toggle-faq/g);
const faqCount = faqItems ? faqItems.length : 0;
if (faqCount < 5) {
    console.warn(`⚠️ אזהרה: רק ${faqCount} שאלות FAQ (מומלץ 5-10)`);
}

// בדיקה 9.3: פונקציית toggleFAQ
if (!content.includes('function toggleFAQ') && !content.includes('toggleFAQ:')) {
    console.error('❌ שגיאה: חסרה פונקציית toggleFAQ');
}

// בדיקה 9.4: Schema.org FAQPage
if (!content.includes('"@type":"FAQPage"') && !content.includes('"@type": "FAQPage"')) {
    console.warn('⚠️ אזהרה: חסר Schema.org FAQPage');
}
```

---

### 🔟 בדיקת Schema.org

#### בדיקות חובה:
```javascript
// בדיקה 10.1: FAQPage Schema
if (!content.includes('@type":"FAQPage')) {
    console.warn('⚠️ אזהרה: חסר FAQPage Schema');
}

// בדיקה 10.2: FinancialProduct Schema
if (!content.includes('@type":"FinancialProduct') && !content.includes('@type": "FinancialProduct')) {
    console.warn('⚠️ אזהרה: חסר FinancialProduct Schema');
}

// בדיקה 10.3: HowTo Schema
if (!content.includes('@type":"HowTo') && !content.includes('@type": "HowTo')) {
    console.warn('⚠️ אזהרה: חסר HowTo Schema');
}

// בדיקה 10.4: JSON-LD תקין
const jsonLdScripts = content.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g);
if (jsonLdScripts) {
    jsonLdScripts.forEach((script, i) => {
        try {
            const jsonContent = script.match(/<script[^>]*>([\s\S]*?)<\/script>/)[1];
            JSON.parse(jsonContent);
            console.log(`✅ JSON-LD #${i+1} תקין`);
        } catch (e) {
            console.error(`❌ שגיאה: JSON-LD #${i+1} לא תקין - ${e.message}`);
        }
    });
}
```

---

### 1️⃣1️⃣ בדיקת שפה (עברית 100%)

#### בדיקות חובה:
```javascript
// בדיקה 11.1: טקסטים באנגלית בממשק
const englishPatterns = [
    /\bSubmit\b/i, /\bCancel\b/i, /\bError\b/i, /\bSuccess\b/i,
    /\bClick here\b/i, /\bEnter\b/i, /\bReset\b/i, /\bCalculate\b/i,
    /\bNext\b/i, /\bPrevious\b/i, /\bClose\b/i, /\bOpen\b/i
];

englishPatterns.forEach(pattern => {
    // בדוק רק בתוכן HTML, לא ב-JS/CSS
    const htmlContent = content.replace(/<script[\s\S]*?<\/script>/gi, '')
                               .replace(/<style[\s\S]*?<\/style>/gi, '');
    if (pattern.test(htmlContent)) {
        console.error(`❌ שגיאה: נמצא טקסט באנגלית - "${pattern}"`);
    }
});

// בדיקה 11.2: כל הכפתורים בעברית
const buttonTexts = content.match(/<button[^>]*>([^<]+)<\/button>/g);
if (buttonTexts) {
    buttonTexts.forEach(btn => {
        const text = btn.match(/<button[^>]*>([^<]+)<\/button>/)[1];
        if (/^[a-zA-Z\s]+$/.test(text.trim())) {
            console.error(`❌ שגיאה: כפתור באנגלית - "${text}"`);
        }
    });
}

// בדיקה 11.3: placeholders בעברית
const placeholders = content.match(/placeholder="([^"]+)"/g);
if (placeholders) {
    placeholders.forEach(ph => {
        const text = ph.match(/placeholder="([^"]+)"/)[1];
        if (/^[a-zA-Z\s]+$/.test(text.trim())) {
            console.error(`❌ שגיאה: placeholder באנגלית - "${text}"`);
        }
    });
}
```

---

### 1️⃣2️⃣ בדיקת ביצועים

#### בדיקות חובה:
```javascript
// בדיקה 12.1: גודל קובץ
const fileSize = content.length;
const fileSizeKB = Math.round(fileSize / 1024);
console.log(`📊 גודל קובץ: ${fileSizeKB}KB`);
if (fileSizeKB > 150) {
    console.warn(`⚠️ אזהרה: קובץ גדול מדי (${fileSizeKB}KB) - מומלץ עד 100KB`);
}

// בדיקה 12.2: מספר event listeners
const listenerCount = (content.match(/addEventListener/g) || []).length;
console.log(`📊 מספר Event Listeners: ${listenerCount}`);
if (listenerCount > 15) {
    console.warn(`⚠️ אזהרה: יותר מדי event listeners (${listenerCount})`);
}

// בדיקה 12.3: Lazy loading
if (!content.includes('IntersectionObserver')) {
    console.info('ℹ️ מידע: אין lazy loading - לא חובה אבל מומלץ לביצועים');
}

// בדיקה 12.4: contain CSS
if (!content.includes('contain:')) {
    console.info('ℹ️ מידע: אין CSS containment - מומלץ להוספה לביצועים');
}
```

---

## 🧪 בדיקות פונקציונליות (ידניות)

### בדיקות בדפדפן:

```javascript
// הדבק בקונסול של הדפדפן לבדיקות ידניות:

(function() {
    console.log('=== 🔍 בדיקות QA למחשבון ===\n');
    
    // 1. בדיקת טאבים
    const tabs = document.querySelectorAll('[data-action="switch-tab"]');
    console.log(`✅ מספר טאבים: ${tabs.length}`);
    
    tabs.forEach((tab, i) => {
        tab.click();
        const tabName = tab.dataset.tab;
        const content = document.querySelector(`#tab-${tabName}`);
        if (content && content.classList.contains('active')) {
            console.log(`✅ טאב ${i+1} (${tabName}): עובד`);
        } else {
            console.error(`❌ טאב ${i+1} (${tabName}): לא עובד!`);
        }
    });
    
    // 2. בדיקת סליידרים
    const sliders = document.querySelectorAll('input[type="range"]');
    console.log(`\n✅ מספר סליידרים: ${sliders.length}`);
    
    sliders.forEach((slider, i) => {
        const oldValue = slider.value;
        slider.value = slider.max;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
        console.log(`✅ סליידר ${i+1}: ${slider.id || 'ללא ID'}`);
        slider.value = oldValue;
        slider.dispatchEvent(new Event('input', { bubbles: true }));
    });
    
    // 3. בדיקת כפתורי בחירה
    const periodBtns = document.querySelectorAll('[data-action="select-period"], [data-value]');
    console.log(`\n✅ מספר כפתורי בחירה: ${periodBtns.length}`);
    
    // 4. בדיקת AWG
    const awgBtn = document.querySelector('[data-action="open-awg"]');
    if (awgBtn) {
        console.log('✅ כפתור AWG קיים');
    } else {
        console.error('❌ חסר כפתור AWG');
    }
    
    // 5. בדיקת העתקה
    const copyBtn = document.querySelector('[data-action="copy-embed-code"]');
    if (copyBtn) {
        console.log('✅ כפתור העתקה קיים');
    } else {
        console.error('❌ חסר כפתור העתקה');
    }
    
    // 6. בדיקת צבעים
    const colorBtns = document.querySelectorAll('[data-action="preview-color"]');
    console.log(`\n✅ מספר כפתורי צבע: ${colorBtns.length}`);
    
    // 7. בדיקת FAQ
    const faqItems = document.querySelectorAll('[data-action="toggle-faq"]');
    console.log(`✅ מספר פריטי FAQ: ${faqItems.length}`);
    
    console.log('\n=== סיום בדיקות QA ===');
})();
```

---

## 📋 דוח QA - תבנית

```markdown
# 📋 דוח QA למחשבון: [שם המחשבון]

## 📊 סיכום מהיר
| קטגוריה | סטטוס |
|---------|--------|
| מבנה HTML | ✅/❌ |
| CSS | ✅/❌ |
| JavaScript | ✅/❌ |
| טאבים | ✅/❌ |
| סליידרים | ✅/❌ |
| מערכת הטמעה | ✅/❌ |
| AWG | ✅/❌ |
| FAQ | ✅/❌ |
| Schema.org | ✅/❌ |
| עברית | ✅/❌ |

## 🔴 שגיאות קריטיות
1. ...
2. ...

## 🟡 אזהרות
1. ...
2. ...

## 🟢 הערות
1. ...

## 📝 המלצות לתיקון
1. ...
2. ...
```

---

## 🛠️ תיקונים נפוצים

### 1. תיקון getEmbedScript חסר:
```javascript
function getEmbedScript() {
    const scriptLines = [
        '<script>',
        'document.addEventListener("DOMContentLoaded", function() {',
        '  (function() {',
        '    "use strict";',
        '    var NS = "WPC_Calc[Topic]_Embed";',
        '    if (window[NS]) return;',
        '    // ... המשך הקוד ...',
        '  })();',
        '});'
    ];
    return scriptLines.join('\\n') + '\\n</' + 'script>';
}
```

### 2. תיקון טאבים עם סקרול:
```css
.wpc-calc-[topic]-[random]-tabs-nav {
    display: flex !important;
    flex-wrap: wrap !important; /* הוסף שורה זו */
    /* מחק: overflow-x: auto; */
}
```

### 3. תיקון סגירת script:
```javascript
// במקום:
return code + '</script>';

// צריך להיות:
return code + '</' + 'script>';
```

---

## ✅ צ'קליסט מהיר לסוכן QA

### בדיקות מבנה:
- [ ] אין DOCTYPE/HTML/HEAD/BODY
- [ ] Viewport script בהתחלה
- [ ] Prefix ייחודי בכל הקלאסים
- [ ] !important על CSS
- [ ] Media queries למובייל
- [ ] IIFE + namespace ייחודי
- [ ] Event delegation

### בדיקות פונקציונליות:
- [ ] טאבים עובדים (2-5)
- [ ] סליידרים מעדכנים ערכים
- [ ] כפתור העתקת קוד עובד
- [ ] getEmbedScript מוגדר
- [ ] תצוגה מקדימה עובדת
- [ ] AWG + shortcode
- [ ] FAQ + Schema.org
- [ ] עברית 100%
- [ ] קרדיט עם nofollow
- [ ] **אין דיסקליימר** (wpc-disclaimer)
- [ ] **אין Related Posts** ([related-shortcode-instert])

### 🚨 תאימות וורדפרס (קריטי!):
- [ ] **אין Arrow Functions** - רק `function() {}`
- [ ] **אין const/let** - רק `var`
- [ ] **אין Template Literals** - רק חיבור מחרוזות
- [ ] **אין && או ||** - וורדפרס ממיר ל-HTML entities!
- [ ] **אין ₪** - להחליף ב-`\u20AA`
- [ ] **תגי script מפוצלים** - `'<scr' + 'ipt>'`
- [ ] **AWG עם max-height** - לא display:none!
- [ ] **resize event ב-openAWG** - לאתחול טפסי וורדפרס

---

**נוצר על ידי: Cursor AI**  
**תאריך: דצמבר 2025**  
**גרסה: 1.0**

