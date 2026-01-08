# הוראות מקדימות ל-3 שלבים החדשים - סוכן הלוואות לעסקים

## שלב 1 חדש: ניתוח וכתיבה

```
קרא את קובץ ההוראות {{STEP1_PROMPT_FILE}} ובצע ניתוח וכתיבה על העמוד {{PAGE_HTML_PATH}}.

השלב משלב שני תת-שלבים:
- **חלק א: ניתוח העמוד** - ניתוח מקיף של מצב קיים
- **חלק ב: כתיבת תוכן חדש** - יישום הניתוח וכתיבה

## נתוני עמוד:
- **מילת מפתח ראשית:** {{PAGE_KEYWORD}}
- **מיקום נוכחי ב-SERP:** {{OUR_SERP_RANK}}
- **כמות מילים קיימת בעמוד כיום:** {{PAGE_WORD_COUNT}}

## מילות מפתח נלוות לשילוב:
{{KEYWORDS_AUTOCOMPLETE}}

**רשימת שימור:** המילים הבאות חייבות להופיע בתוכן:
{{KEYWORDS_AUTOCOMPLETE_LIST}}

## מידע ממתחרים מדורגים:
{{SERP_ORGANIC}}

## תוצאות AI Overview של גוגל:
{{SERP_AI_OVERVIEW}}

## מאגרי מידע:
- מאגר כללי: {{KNOWLEDGE_BASE_GENERAL}}
- מאגר מסלולים: {{KNOWLEDGE_BASE_TRACKS}}
- חודש נוכחי: {{CURRENT_MONTH}}
- ריבית הפריים העדכנית: {{BOI_INTEREST_RATE}}

## דומיינים מאושרים למידע פיננסי:
{{APPROVED_DOMAINS}}

**חובה לשמור:**
- דוח משולב (ניתוח + כתיבה): {{OUTPUT_PATH}}
- שם הקובץ: {{STEP1_REPORT}}
- העמוד המעודכן: {{PAGE_HTML_PATH}} (עריכה במקום)
```

## שלב 2 חדש: SEO + QA תוכן

```
קרא את קובץ ההוראות {{STEP2_PROMPT_FILE}} ובצע SEO ו-QA על העמוד {{PAGE_HTML_PATH}}.

השלב משלב שני תת-שלבים:
- **חלק א: SEO והטמעה טכנית** - Schema, תגיות HEAD, שורטקודים
- **חלק ב: QA ודיבאג** - בדיקות איכות מקיפות

## דוח משלב קודם:
{{STEP1_REPORT}}

## נתוני עמוד:
- **מילת מפתח ראשית:** {{PAGE_KEYWORD}}
- **כמות מילים:** {{PAGE_WORD_COUNT}}

## מילות מפתח שחייבות להופיע:
{{KEYWORDS_AUTOCOMPLETE_LIST}}

## מאגר מידע כללי (לפרטי Schema):
{{KNOWLEDGE_BASE_GENERAL}}

**חובה לשמור:**
- דוח SEO + QA: {{OUTPUT_PATH}}
- שם הקובץ: {{STEP2_REPORT}}
- העמוד המעודכן: {{PAGE_HTML_PATH}} (עריכה במקום)
```

## שלב 3 חדש: ויזואליזציה + QA ויזואלי

```
קרא את קובץ ההוראות {{STEP3_PROMPT_FILE}} והוסף ויזואליזציות ו-QA על העמוד {{PAGE_HTML_PATH}}.

השלב משלב שני תת-שלבים:
- **חלק א: הוספת אלמנטים ויזואליים** - עיצוב והעשרה גרפית
- **חלק ב: QA ויזואליזציה** - בדיקות איכות ותקינות

## דוח משלב קודם:
{{STEP2_REPORT}}

## נתוני עמוד:
- **מילת מפתח ראשית:** {{PAGE_KEYWORD}}
- **כמות מילים:** {{PAGE_WORD_COUNT}}

## מקורות עיצוב:
- קובץ עיצוב: מאגרי מידע/visual.html
- כללי WordPress: מאגרי מידע/wordpress-ruls.html

**חובה לשמור:**
- דוח ויזואליזציה + QA: {{OUTPUT_PATH}}
- שם הקובץ: {{STEP3_REPORT}}
- העמוד הסופי: {{PAGE_HTML_PATH}} (עריכה במקום)
```

---

## מפתח השורטקודים

### שורטקודים משותפים לכל השלבים:
- `{{PAGE_HTML_PATH}}` - נתיב לקובץ העבודה
- `{{PAGE_KEYWORD}}` - מילת המפתח הראשית
- `{{PAGE_WORD_COUNT}}` - כמות המילים בעמוד
- `{{OUTPUT_PATH}}` - איפה לשמור את הדוח
- `{{STEP1_REPORT}}`, `{{STEP2_REPORT}}`, `{{STEP3_REPORT}}` - דוחות משלבים קודמים
- `{{STEP1_PROMPT_FILE}}`, `{{STEP2_PROMPT_FILE}}`, `{{STEP3_PROMPT_FILE}}` - נתיבי קבצי ההוראות

### שורטקודים ספציפיים לשלב 1:
- `{{OUR_SERP_RANK}}` - מיקום נוכחי ב-SERP
- `{{KEYWORDS_AUTOCOMPLETE}}` - מילות מפתח נלוות
- `{{KEYWORDS_AUTOCOMPLETE_LIST}}` - רשימת מילות מפתח חובה
- `{{SERP_ORGANIC}}` - תוצאות אורגניות מהמתחרים
- `{{SERP_AI_OVERVIEW}}` - תוצאות AI של גוגל
- `{{KNOWLEDGE_BASE_GENERAL}}` - מאגר מידע כללי
- `{{KNOWLEDGE_BASE_TRACKS}}` - מאגר מסלולי הלוואות
- `{{CURRENT_MONTH}}` - חודש נוכחי
- `{{BOI_INTEREST_RATE}}` - ריבית בנק ישראל
- `{{APPROVED_DOMAINS}}` - דומיינים מאושרים למידע פיננסי

### שורטקודים ספציפיים לשלב 2:
- `{{KEYWORDS_AUTOCOMPLETE_LIST}}` - רשימת מילות מפתח לבדיקה
- `{{KNOWLEDGE_BASE_GENERAL}}` - לפרטי Schema

### שורטקודים ספציפיים לשלב 3:
- אין שורטקודים נוספים - מסתמך על הדוחות הקודמים
