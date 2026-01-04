# -*- coding: utf-8 -*-
"""
migrate_existing_to_main.py - Migrate existing pages to new multi-site structure

This script moves all existing page folders from:
    דפים לשינוי/*
To:
    דפים לשינוי/main/*

And creates the business folder for new imports.
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
PAGES_FOLDER = BASE_DIR / "דפים לשינוי"
MAIN_FOLDER = PAGES_FOLDER / "main"
BUSINESS_FOLDER = PAGES_FOLDER / "business"

def migrate():
    print("=" * 60)
    print("🚀 Migration to Multi-Site Structure")
    print("=" * 60)
    
    # Check if already migrated
    if MAIN_FOLDER.exists() and any(MAIN_FOLDER.iterdir()):
        print("⚠️  main/ folder already exists and has content.")
        print("   Migration may have already been done.")
        print("   Continuing to move any remaining folders...")
        # Continue anyway - will skip existing folders
    
    # Create target folders
    MAIN_FOLDER.mkdir(exist_ok=True)
    BUSINESS_FOLDER.mkdir(exist_ok=True)
    print(f"✅ Created: {MAIN_FOLDER}")
    print(f"✅ Created: {BUSINESS_FOLDER}")
    
    # Get all items in דפים לשינוי (except main and business)
    items_to_move = []
    for item in PAGES_FOLDER.iterdir():
        if item.is_dir() and item.name not in ['main', 'business']:
            items_to_move.append(item)
    
    print(f"\n📁 Found {len(items_to_move)} folders to migrate")
    print("-" * 60)
    
    moved = 0
    skipped = 0
    errors = 0
    
    for item in items_to_move:
        target = MAIN_FOLDER / item.name
        try:
            if target.exists():
                print(f"⏭️  {item.name}: Already exists in main/, skipping")
                skipped += 1
            else:
                shutil.move(str(item), str(target))
                print(f"✅ {item.name}")
                moved += 1
        except Exception as e:
            print(f"❌ {item.name}: Error - {e}")
            errors += 1
    
    print("-" * 60)
    print(f"\n📊 Summary:")
    print(f"   ✅ Moved: {moved}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    
    print("\n" + "=" * 60)
    print("✅ Migration complete!")
    print("=" * 60)
    
    # Show new structure
    print("\n📁 New structure:")
    print(f"   {PAGES_FOLDER}/")
    print(f"   ├── main/     ({len(list(MAIN_FOLDER.iterdir())) if MAIN_FOLDER.exists() else 0} folders)")
    print(f"   └── business/ ({len(list(BUSINESS_FOLDER.iterdir())) if BUSINESS_FOLDER.exists() else 0} folders)")

if __name__ == "__main__":
    migrate()

