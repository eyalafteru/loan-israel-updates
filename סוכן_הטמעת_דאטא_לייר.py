#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🏷️ סוכן הטמעת DataLayer לכפתורי העתקת קוד
============================================

📋 מה הסוכן עושה:
-----------------
הסוכן עובר על כל קבצי ה-HTML בתיקיית המחשבונים ומוסיף
אירועי dataLayer לכל כפתורי "העתקת הקוד" לצורך מעקב ב-Google Tag Manager.

🔍 כפתורים שהסוכן מזהה:
------------------------
1. data-action="copy-embed-code" - העתקת קוד HTML מלא
2. data-action="copy-preview-code" - העתקת קוד עם צבע נבחר
3. כל כפתור אחר שמכיל "copy" ב-data-action

📊 מבנה ה-DataLayer שנוסף:
---------------------------
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
    'event': 'copy_code_click',
    'calculator_name': 'שם המחשבון',
    'button_type': 'סוג הכפתור'
});

📁 תיקיית יעד:
---------------
C:\Users\eyal\עדכון עמודים מיוחדים מאני\מחשבונים מוכנים לעלייה לאוויר

🚀 הפעלה:
----------
python סוכן_הטמעת_דאטא_לייר.py

או עם פרמטר --dry-run לבדיקה בלבד (ללא שינויים):
python סוכן_הטמעת_דאטא_לייר.py --dry-run

או עם נתיב מותאם:
python סוכן_הטמעת_דאטא_לייר.py --folder "C:\path\to\folder"

🔄 תוצאות:
-----------
הסוכן מייצר דוח מפורט לכל קובץ שעובר עליו, כולל:
- מספר כפתורי העתקה שנמצאו
- אילו פונקציות עודכנו
- האם הקובץ כבר הכיל dataLayer (דילוג)
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

# הגדרות - נתיב ברירת מחדל (יחסי לקובץ הסוכן)
SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_TARGET_FOLDER = SCRIPT_DIR / "מחשבונים מוכנים לעלייה לאוויר"

# דפוסים לזיהוי פונקציות העתקה
COPY_FUNCTION_PATTERNS = [
    r'function\s+copyEmbedCode\s*\(\s*\)\s*\{',
    r'function\s+copyPreviewCode\s*\(\s*\)\s*\{',
    r'function\s+copy\w*Code\s*\(\s*\)\s*\{',  # כל פונקציה שמתחילה ב-copy ומסתיימת ב-Code
]

# דפוסים לזיהוי כפתורי העתקה
COPY_BUTTON_PATTERNS = [
    r'data-action=["\']copy-embed-code["\']',
    r'data-action=["\']copy-preview-code["\']',
    r'data-action=["\']copy-\w+-code["\']',
]

class DataLayerAgent:
    """סוכן להטמעת DataLayer בכפתורי העתקה"""
    
    def __init__(self, target_folder, dry_run=False):
        self.target_folder = Path(target_folder)
        self.dry_run = dry_run
        self.results = []
        self.total_files = 0
        self.modified_files = 0
        self.skipped_files = 0
        self.buttons_found = 0
        self.functions_updated = 0
        
    def extract_calculator_name(self, filename):
        """חילוץ שם המחשבון מהקובץ"""
        # הסרת .html והמרה לשם נקי
        name = filename.replace('.html', '')
        return name
    
    def extract_calculator_name_from_content(self, content):
        """ניסיון לחלץ שם מחשבון מתוך הקוד עצמו"""
        # חיפוש CALCULATOR_NAME
        match = re.search(r"const\s+CALCULATOR_NAME\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
        
        # חיפוש כותרת H1
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def find_copy_buttons(self, content):
        """מציאת כל כפתורי ההעתקה בקובץ"""
        buttons = []
        for pattern in COPY_BUTTON_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                # חילוץ סוג הכפתור
                button_type = re.search(r'copy-[\w-]+-code|copy-\w+-code', match)
                if button_type:
                    buttons.append(button_type.group())
                else:
                    action_match = re.search(r"data-action=['\"]([^'\"]+)['\"]", match)
                    if action_match:
                        buttons.append(action_match.group(1))
        return list(set(buttons))  # הסרת כפילויות
    
    def check_if_datalayer_exists(self, content):
        """בדיקה אם כבר קיים dataLayer בקובץ לאירועי copy"""
        return 'copy_code_click' in content
    
    def generate_datalayer_code(self, calculator_name, button_type):
        """יצירת קוד DataLayer להטמעה"""
        return f'''
        // 🏷️ DataLayer Push - מעקב Tag Manager
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({{
            'event': 'copy_code_click',
            'calculator_name': '{calculator_name}',
            'button_type': '{button_type}'
        }});'''
    
    def update_copy_function(self, content, func_name, calculator_name, button_type):
        """עדכון פונקציית העתקה עם DataLayer"""
        
        # דפוס לזיהוי הפונקציה
        pattern = rf'(function\s+{func_name}\s*\(\s*\)\s*\{{)'
        
        # בדיקה אם כבר יש dataLayer בפונקציה הזו
        func_match = re.search(pattern, content)
        if not func_match:
            return content, False
        
        # מציאת גוף הפונקציה
        func_start = func_match.end()
        
        # בדיקה אם כבר יש dataLayer בפונקציה
        # מחפשים את סוף הפונקציה (} הראשון שמאזן את הפונקציה)
        brace_count = 1
        func_end = func_start
        while brace_count > 0 and func_end < len(content):
            if content[func_end] == '{':
                brace_count += 1
            elif content[func_end] == '}':
                brace_count -= 1
            func_end += 1
        
        func_body = content[func_start:func_end]
        
        # אם כבר יש dataLayer, לא לעדכן
        if 'dataLayer.push' in func_body:
            return content, False
        
        # יצירת קוד DataLayer
        datalayer_code = self.generate_datalayer_code(calculator_name, button_type)
        
        # הוספת הקוד בתחילת הפונקציה
        new_func_start = func_match.group(1) + datalayer_code + '\n        '
        new_content = content[:func_match.start()] + new_func_start + content[func_start:]
        
        return new_content, True
    
    def process_file(self, filepath):
        """עיבוד קובץ בודד"""
        result = {
            'file': filepath.name,
            'path': str(filepath),
            'status': 'pending',
            'buttons_found': [],
            'functions_updated': [],
            'calculator_name': '',
            'message': ''
        }
        
        try:
            # קריאת הקובץ
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # חילוץ שם המחשבון
            calc_name = self.extract_calculator_name_from_content(content)
            if not calc_name:
                calc_name = self.extract_calculator_name(filepath.name)
            result['calculator_name'] = calc_name
            
            # בדיקה אם כבר קיים dataLayer
            if self.check_if_datalayer_exists(content):
                result['status'] = 'skipped'
                result['message'] = 'DataLayer כבר קיים - דילוג'
                self.skipped_files += 1
                return result
            
            # מציאת כפתורי העתקה
            buttons = self.find_copy_buttons(content)
            result['buttons_found'] = buttons
            self.buttons_found += len(buttons)
            
            if not buttons:
                result['status'] = 'no_buttons'
                result['message'] = 'לא נמצאו כפתורי העתקה'
                return result
            
            # עדכון פונקציות ההעתקה
            modified = False
            
            # מיפוי בין סוגי כפתורים לשמות פונקציות
            button_to_function = {
                'copy-embed-code': 'copyEmbedCode',
                'copy-preview-code': 'copyPreviewCode',
            }
            
            for button in buttons:
                func_name = button_to_function.get(button)
                if func_name:
                    content, was_updated = self.update_copy_function(
                        content, func_name, calc_name, button
                    )
                    if was_updated:
                        result['functions_updated'].append(func_name)
                        modified = True
                        self.functions_updated += 1
            
            # בדיקת שינויים
            if modified and content != original_content:
                if not self.dry_run:
                    # שמירת הקובץ
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    result['status'] = 'updated'
                    result['message'] = f'עודכן בהצלחה - {len(result["functions_updated"])} פונקציות'
                else:
                    result['status'] = 'would_update'
                    result['message'] = f'יעודכן (dry-run) - {len(result["functions_updated"])} פונקציות'
                self.modified_files += 1
            else:
                result['status'] = 'no_changes'
                result['message'] = 'לא נדרשו שינויים'
            
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f'שגיאה: {str(e)}'
        
        return result
    
    def run(self):
        """הפעלת הסוכן על כל הקבצים"""
        print("\n" + "="*70)
        print("🏷️  סוכן הטמעת DataLayer לכפתורי העתקת קוד")
        print("="*70)
        print(f"\n📁 תיקיית יעד: {self.target_folder}")
        print(f"🔧 מצב: {'בדיקה בלבד (dry-run)' if self.dry_run else 'עדכון אמיתי'}")
        print("-"*70)
        
        # רשימת קבצי HTML
        html_files = list(self.target_folder.glob("*.html"))
        self.total_files = len(html_files)
        
        print(f"\n📊 נמצאו {self.total_files} קבצי HTML\n")
        
        # עיבוד כל קובץ
        for i, filepath in enumerate(html_files, 1):
            print(f"\n[{i}/{self.total_files}] 📄 {filepath.name}")
            print("-"*50)
            
            result = self.process_file(filepath)
            self.results.append(result)
            
            # הדפסת תוצאות
            status_icons = {
                'updated': '✅',
                'would_update': '🔄',
                'skipped': '⏭️',
                'no_buttons': '⚠️',
                'no_changes': '➖',
                'error': '❌'
            }
            
            icon = status_icons.get(result['status'], '❓')
            print(f"   {icon} סטטוס: {result['message']}")
            print(f"   📛 שם מחשבון: {result['calculator_name']}")
            
            if result['buttons_found']:
                print(f"   🔘 כפתורים שנמצאו: {', '.join(result['buttons_found'])}")
            
            if result['functions_updated']:
                print(f"   🔧 פונקציות שעודכנו: {', '.join(result['functions_updated'])}")
        
        # סיכום
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """הדפסת סיכום"""
        print("\n" + "="*70)
        print("📊 סיכום הפעלה")
        print("="*70)
        print(f"""
    📁 סה"כ קבצים:        {self.total_files}
    ✅ קבצים שעודכנו:     {self.modified_files}
    ⏭️ קבצים שדולגו:      {self.skipped_files}
    🔘 כפתורים שנמצאו:    {self.buttons_found}
    🔧 פונקציות שעודכנו:  {self.functions_updated}
    
    📅 תאריך הפעלה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        if self.dry_run:
            print("⚠️  הרצה במצב dry-run - לא בוצעו שינויים בפועל!")
            print("   הפעל שוב ללא --dry-run לביצוע השינויים")
        
        print("="*70)
        
        # פירוט לפי סטטוס
        print("\n📋 פירוט לפי קובץ:")
        print("-"*70)
        
        for result in self.results:
            status_text = {
                'updated': 'עודכן',
                'would_update': 'יעודכן',
                'skipped': 'דולג (כבר קיים)',
                'no_buttons': 'ללא כפתורים',
                'no_changes': 'ללא שינויים',
                'error': 'שגיאה'
            }
            print(f"   • {result['file']}: {status_text.get(result['status'], result['status'])}")


def main():
    """פונקציה ראשית"""
    # בדיקת פרמטרים
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    # בדיקת נתיב מותאם
    target_folder = DEFAULT_TARGET_FOLDER
    for i, arg in enumerate(sys.argv):
        if arg == '--folder' and i + 1 < len(sys.argv):
            target_folder = Path(sys.argv[i + 1])
            break
    
    # בדיקה שהתיקייה קיימת
    if not target_folder.exists():
        print(f"❌ שגיאה: התיקייה לא נמצאה: {target_folder}")
        print(f"ℹ️  ניסיתי לחפש ב: {target_folder.resolve()}")
        sys.exit(1)
    
    # הפעלת הסוכן
    agent = DataLayerAgent(target_folder, dry_run=dry_run)
    agent.run()


if __name__ == "__main__":
    main()

