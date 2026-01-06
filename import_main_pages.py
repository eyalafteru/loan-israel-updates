# -*- coding: utf-8 -*-
"""
import_main_pages.py - Import pages from עמודים לייבוא main.txt

This script:
1. Reads the import file (Keyword, URL, Post ID)
2. Scans existing folders to find already imported pages
3. Creates folders in דפים לשינוי/main/
4. Fetches content from WordPress
5. Saves page_info.json, HTML content, and metadata backup
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Check for requests library
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: 'requests' library not installed. Install with: pip install requests")

import sys

# Handle PyInstaller bundled exe
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as script
    BASE_DIR = Path(__file__).parent

IMPORT_FILE = BASE_DIR / "עמודים לייבוא main.txt"
PAGES_FOLDER = BASE_DIR / "דפים לשינוי" / "main"

# Load config
CONFIG_PATH = BASE_DIR / "config.json"
if not CONFIG_PATH.exists():
    print(f"❌ לא נמצא config.json בנתיב: {CONFIG_PATH}")
    print(f"   העתק את הקובץ לתיקייה: {BASE_DIR}")
    sys.exit(1)

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# WordPress credentials for main site
WP_SITE = config["wordpress"]["sites"]["main"]
jwt_token = None


def get_jwt_token():
    """Get or refresh JWT token"""
    global jwt_token
    if jwt_token:
        return jwt_token
    
    token_url = WP_SITE["site_url"] + WP_SITE["token_endpoint"]
    print(f"🔑 Authenticating to {WP_SITE['site_url']}...")
    
    response = requests.post(token_url, json={
        "username": WP_SITE["username"],
        "password": WP_SITE["password"]
    }, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate: {response.status_code} - {response.text}")
    
    jwt_token = response.json().get("token")
    print("✅ Authenticated successfully")
    return jwt_token


def fetch_wordpress_page(post_id):
    """Fetch page data from WordPress"""
    token = get_jwt_token()
    
    # Try posts endpoint first
    fetch_url = f"{WP_SITE['site_url']}{WP_SITE['api_base']}/posts/{post_id}?context=edit"
    
    response = requests.get(
        fetch_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    
    # If post not found, try pages endpoint
    if response.status_code == 404:
        fetch_url = f"{WP_SITE['site_url']}{WP_SITE['api_base']}/pages/{post_id}?context=edit"
        response = requests.get(
            fetch_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
    
    if response.status_code == 403:
        # Token expired, clear and retry
        global jwt_token
        jwt_token = None
        token = get_jwt_token()
        response = requests.get(
            fetch_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch post {post_id}: {response.status_code}")
    
    return response.json()


def count_words(html_content):
    """Count words in HTML content (rough estimate)"""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Count words
    return len(text.split())


def scan_existing_pages():
    """Scan existing folders and return a set of post_ids already imported"""
    existing_post_ids = set()
    
    if not PAGES_FOLDER.exists():
        return existing_post_ids
    
    for folder in PAGES_FOLDER.iterdir():
        if not folder.is_dir():
            continue
        
        page_info_path = folder / "page_info.json"
        if page_info_path.exists():
            try:
                with open(page_info_path, 'r', encoding='utf-8') as f:
                    page_info = json.load(f)
                    post_id = page_info.get("post_id", "")
                    if post_id:
                        existing_post_ids.add(str(post_id))
            except Exception:
                pass
    
    return existing_post_ids


def import_page(keyword, url, post_id, dry_run=False):
    """Import a single page"""
    # Create folder
    page_folder = PAGES_FOLDER / keyword
    
    if dry_run:
        print(f"  📁 Would create: {page_folder}")
        return True
    
    page_folder.mkdir(parents=True, exist_ok=True)
    
    # Fetch WordPress data
    try:
        post_data = fetch_wordpress_page(post_id)
    except Exception as e:
        print(f"  ❌ Error fetching: {e}")
        return False
    
    # Extract content
    content_raw = post_data.get("content", {}).get("raw", "")
    yoast = post_data.get("yoast_head_json", {})
    page_title = post_data.get("title", {}).get("rendered", "")
    meta_title = yoast.get("title", page_title)
    meta_description = yoast.get("description", "")
    word_count = count_words(content_raw)
    
    # Save page_info.json
    page_info = {
        "page_name": page_title,
        "keyword": keyword,
        "url": url,
        "post_id": str(post_id),
        "site": "main",
        "title": meta_title,
        "description": meta_description,
        "word_count": word_count,
        "is_special": False,
        "imported_at": datetime.now().isoformat(),
        "fetched_keywords": {}
    }
    
    page_info_path = page_folder / "page_info.json"
    with open(page_info_path, 'w', encoding='utf-8') as f:
        json.dump(page_info, f, ensure_ascii=False, indent=2)
    
    # Save HTML content
    html_path = page_folder / f"{keyword}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content_raw)
    
    # Save backup copy
    backup_path = page_folder / f"{keyword}_backup.html"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content_raw)
    
    # Save metadata backup
    meta_backup = {
        "title": meta_title,
        "description": meta_description,
        "slug": post_data.get("slug", ""),
        "og_title": yoast.get("og_title", ""),
        "og_description": yoast.get("og_description", ""),
        "fetched_at": datetime.now().isoformat()
    }
    
    meta_path = page_folder / f"{keyword}_backup_meta.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta_backup, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ Imported: {word_count} words, {len(content_raw)} chars")
    return True


def read_import_file():
    """Read the import file and return list of pages"""
    pages = []
    
    with open(IMPORT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                print(f"⚠️  Line {line_num}: Expected 3 columns, got {len(parts)}: {line[:50]}...")
                continue
            
            keyword, url, post_id = parts[0], parts[1], parts[2]
            
            # Skip if no post_id
            if not post_id.strip():
                print(f"⚠️  Line {line_num}: No post_id for '{keyword}'")
                continue
            
            pages.append({
                "keyword": keyword.strip(),
                "url": url.strip(),
                "post_id": post_id.strip(),
                "line_num": line_num
            })
    
    return pages


def main():
    parser = argparse.ArgumentParser(description="Import Main site pages from WordPress")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be imported without making changes")
    parser.add_argument('--start', type=int, default=1, help="Start from this line number (1-based)")
    parser.add_argument('--limit', type=int, default=0, help="Limit number of pages to import (0=all)")
    parser.add_argument('--delay', type=float, default=1.0, help="Delay between API calls in seconds")
    parser.add_argument('--force', action='store_true', help="Re-import even if page exists")
    args = parser.parse_args()
    
    if not REQUESTS_AVAILABLE:
        print("❌ 'requests' library is required. Install with: pip install requests")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 Main Site Pages Import")
    print("=" * 60)
    print(f"📁 Source: {IMPORT_FILE}")
    print(f"📁 Target: {PAGES_FOLDER}")
    
    if args.dry_run:
        print("⚠️  DRY RUN - No changes will be made")
    
    print()
    
    # Scan existing pages
    existing_post_ids = scan_existing_pages()
    print(f"📂 Found {len(existing_post_ids)} existing pages with post_id")
    
    # Create target folder
    if not args.dry_run:
        PAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Read import file
    pages = read_import_file()
    print(f"📄 Found {len(pages)} pages in import file")
    
    # Filter out already existing pages (by post_id)
    if not args.force:
        new_pages = [p for p in pages if p["post_id"] not in existing_post_ids]
        already_imported = len(pages) - len(new_pages)
        if already_imported > 0:
            print(f"⏭️  {already_imported} pages already imported (by post_id)")
        pages = new_pages
    
    # Apply filters
    pages = [p for p in pages if p["line_num"] >= args.start]
    if args.limit > 0:
        pages = pages[:args.limit]
    
    print(f"📊 Will process {len(pages)} new pages (start={args.start}, limit={args.limit or 'all'})")
    print("-" * 60)
    
    if len(pages) == 0:
        print("✅ Nothing to import!")
        return
    
    success = 0
    errors = 0
    skipped = 0
    
    for i, page in enumerate(pages, 1):
        keyword = page["keyword"]
        post_id = page["post_id"]
        url = page["url"]
        
        # Double-check if folder already exists
        page_folder = PAGES_FOLDER / keyword
        if not args.force and page_folder.exists() and (page_folder / "page_info.json").exists():
            print(f"[{i}/{len(pages)}] ⏭️  {keyword} - folder already exists")
            skipped += 1
            continue
        
        print(f"[{i}/{len(pages)}] 📥 {keyword} (post {post_id})")
        
        try:
            if import_page(keyword, url, post_id, dry_run=args.dry_run):
                success += 1
            else:
                errors += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            errors += 1
        
        # Delay between API calls
        if not args.dry_run and i < len(pages):
            time.sleep(args.delay)
    
    print("-" * 60)
    print(f"\n📊 Summary:")
    print(f"   ✅ Imported: {success}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    print(f"   📁 Total in folder: {len(list(PAGES_FOLDER.iterdir())) if PAGES_FOLDER.exists() else 0}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
