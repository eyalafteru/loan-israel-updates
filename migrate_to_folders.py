# -*- coding: utf-8 -*-
"""
סקריפט מיגרציה - העברת קבצים למבנה תיקיות חדש

מבנה יעד:
דפים לשינוי/
├── [שם העמוד]/
│   ├── [שם העמוד].html              (קובץ מקור)
│   ├── שיווק אטומי/                  (תיקיית הסוכן)
│   │   ├── דוח שלב 1.md
│   │   ├── דוח שלב 2.md
│   │   ├── דוח דיבאג.md
│   │   └── גרסה מתוקנת.html
│   └── מטא.json
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

# תיקיות מקור
PAGES_FOLDER = BASE_DIR / "דפים לשינוי"
REPORTS_FOLDER = BASE_DIR / "תיקונים לעמודים"
FIXED_FOLDER = BASE_DIR / "עמודים מתוקנים"

# מיפוי סיומות לשמות קבצים חדשים
AGENT_FOLDERS = {
    "שיווק אטומי": {
        "report_patterns": ["_דוח תיקונים שיווק אטומי.md"],
        "step2_report_patterns": ["_דוח סיום שלב 2.md"],
        "debug_report_patterns": ["_דוח דיבאג.md"],
        "fixed_patterns": ["_מתוקן_אטומי.html", "_סופי.html"],
        "new_names": {
            "report": "דוח שלב 1.md",
            "step2_report": "דוח שלב 2.md",
            "debug_report": "דוח דיבאג.md",
            "fixed": "גרסה מתוקנת.html"
        }
    }
}

def get_page_name(html_file):
    """מחזיר את שם העמוד בלי סיומת, מנקה רווחים מיותרים"""
    return html_file.stem.strip()

def create_page_folder(page_name):
    """יוצר תיקייה לעמוד אם לא קיימת"""
    folder = PAGES_FOLDER / page_name
    folder.mkdir(exist_ok=True)
    return folder

def find_related_files(page_name, patterns, source_folder):
    """מחפש קבצים קשורים לעמוד לפי דפוסים"""
    found = []
    if source_folder.exists():
        for pattern in patterns:
            for file in source_folder.glob(f"*{pattern}"):
                if page_name in file.name:
                    found.append(file)
    return found

def migrate_page(html_file):
    """מעביר עמוד למבנה החדש"""
    page_name = get_page_name(html_file)
    print(f"\n📄 מעבד: {page_name}")
    
    # צור תיקיית עמוד
    page_folder = create_page_folder(page_name)
    
    # העבר את קובץ ה-HTML לתיקייה
    new_html_path = page_folder / html_file.name
    if html_file != new_html_path:
        if new_html_path.exists():
            print(f"  ⚠️ קובץ HTML כבר קיים בתיקייה")
        else:
            shutil.move(str(html_file), str(new_html_path))
            print(f"  ✅ HTML הועבר לתיקייה")
    
    # עבור על כל סוכן ומצא קבצים קשורים
    for agent_name, agent_config in AGENT_FOLDERS.items():
        agent_folder = page_folder / agent_name
        files_found = False
        
        # חפש דוחות שלב 1
        for file in find_related_files(page_name, agent_config["report_patterns"], REPORTS_FOLDER):
            agent_folder.mkdir(exist_ok=True)
            new_path = agent_folder / agent_config["new_names"]["report"]
            shutil.move(str(file), str(new_path))
            print(f"  ✅ דוח שלב 1 הועבר")
            files_found = True
        
        # חפש דוחות שלב 2
        for file in find_related_files(page_name, agent_config["step2_report_patterns"], REPORTS_FOLDER):
            agent_folder.mkdir(exist_ok=True)
            new_path = agent_folder / agent_config["new_names"]["step2_report"]
            shutil.move(str(file), str(new_path))
            print(f"  ✅ דוח שלב 2 הועבר")
            files_found = True
        
        # חפש דוחות דיבאג
        for file in find_related_files(page_name, agent_config["debug_report_patterns"], REPORTS_FOLDER):
            agent_folder.mkdir(exist_ok=True)
            new_path = agent_folder / agent_config["new_names"]["debug_report"]
            shutil.move(str(file), str(new_path))
            print(f"  ✅ דוח דיבאג הועבר")
            files_found = True
        
        # חפש קבצים מתוקנים
        for file in find_related_files(page_name, agent_config["fixed_patterns"], FIXED_FOLDER):
            agent_folder.mkdir(exist_ok=True)
            new_path = agent_folder / agent_config["new_names"]["fixed"]
            shutil.move(str(file), str(new_path))
            print(f"  ✅ קובץ מתוקן הועבר")
            files_found = True
        
        if files_found:
            print(f"  📁 נוצרה תיקייה: {agent_name}/")

def main():
    print("=" * 60)
    print("🚀 מתחיל מיגרציה למבנה תיקיות חדש")
    print("=" * 60)
    
    # מצא את כל קבצי ה-HTML בתיקייה הראשית (לא בתת-תיקיות)
    html_files = list(PAGES_FOLDER.glob("*.html"))
    
    if not html_files:
        print("⚠️ לא נמצאו קבצי HTML בתיקייה דפים לשינוי")
        return
    
    print(f"\n📊 נמצאו {len(html_files)} עמודים להעברה")
    
    for html_file in html_files:
        migrate_page(html_file)
    
    # טפל גם בתיקיית מחשבונים מוכנים
    calculators_folder = PAGES_FOLDER / "מחשבונים מוכנים לעלייה לאוויר"
    if calculators_folder.exists():
        calc_files = list(calculators_folder.glob("*.html"))
        print(f"\n📊 נמצאו {len(calc_files)} מחשבונים")
        for html_file in calc_files:
            page_name = get_page_name(html_file)
            page_folder = calculators_folder / page_name
            page_folder.mkdir(exist_ok=True)
            new_html_path = page_folder / html_file.name
            if html_file != new_html_path and not new_html_path.exists():
                shutil.move(str(html_file), str(new_html_path))
                print(f"  ✅ {page_name} הועבר")
    
    print("\n" + "=" * 60)
    print("✅ המיגרציה הושלמה!")
    print("=" * 60)
    
    # הצג סיכום
    print("\n📁 מבנה חדש:")
    for folder in PAGES_FOLDER.iterdir():
        if folder.is_dir() and folder.name != "מחשבונים מוכנים לעלייה לאוויר":
            print(f"  📂 {folder.name}/")
            for sub in folder.iterdir():
                if sub.is_dir():
                    print(f"      📁 {sub.name}/")

if __name__ == "__main__":
    main()

