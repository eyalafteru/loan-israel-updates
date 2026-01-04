# -*- coding: utf-8 -*-
"""
import_business_pages.py - Import pages from עמודים לייבוא הלוואות לעסקים.txt

This script:
1. Reads the import file (Title, Keyword, URL, Post ID)
2. Creates folders in דפים לשינוי/business/
3. Fetches content from WordPress
4. Saves page_info.json, HTML content, and metadata backup
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

BASE_DIR = Path(__file__).parent
IMPORT_FILE = BASE_DIR / "עמודים לייבוא הלוואות לעסקים.txt"
PAGES_FOLDER = BASE_DIR / "דפים לשינוי" / "business"

# Load config
CONFIG_PATH = BASE_DIR / "config.json"
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# WordPress credentials for business site
WP_SITE = config["wordpress"]["sites"]["business"]
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
    
    fetch_url = f"{WP_SITE['site_url']}{WP_SITE['api_base']}/posts/{post_id}?context=edit"
    
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

def import_page(title, keyword, url, post_id, dry_run=False):
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
    meta_title = yoast.get("title", post_data.get("title", {}).get("rendered", ""))
    meta_description = yoast.get("description", "")
    
    # Save page_info.json
    page_info = {
        "keyword": keyword,
        "url": url,
        "post_id": str(post_id),
        "site": "business",
        "title": meta_title,
        "description": meta_description,
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
    
    print(f"  ✅ Imported: {len(content_raw)} chars")
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
            if len(parts) != 4:
                print(f"⚠️  Line {line_num}: Expected 4 columns, got {len(parts)}")
                continue
            
            title, keyword, url, post_id = parts
            pages.append({
                "title": title,
                "keyword": keyword,
                "url": url,
                "post_id": post_id,
                "line_num": line_num
            })
    
    return pages

def main():
    parser = argparse.ArgumentParser(description="Import Business pages from WordPress")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be imported without making changes")
    parser.add_argument('--start', type=int, default=1, help="Start from this line number (1-based)")
    parser.add_argument('--limit', type=int, default=0, help="Limit number of pages to import (0=all)")
    parser.add_argument('--delay', type=float, default=1.0, help="Delay between API calls in seconds")
    args = parser.parse_args()
    
    if not REQUESTS_AVAILABLE:
        print("❌ 'requests' library is required. Install with: pip install requests")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 Business Pages Import")
    print("=" * 60)
    print(f"📁 Source: {IMPORT_FILE}")
    print(f"📁 Target: {PAGES_FOLDER}")
    
    if args.dry_run:
        print("⚠️  DRY RUN - No changes will be made")
    
    print()
    
    # Create target folder
    if not args.dry_run:
        PAGES_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Read import file
    pages = read_import_file()
    print(f"📄 Found {len(pages)} pages in import file")
    
    # Apply filters
    pages = [p for p in pages if p["line_num"] >= args.start]
    if args.limit > 0:
        pages = pages[:args.limit]
    
    print(f"📊 Will process {len(pages)} pages (start={args.start}, limit={args.limit or 'all'})")
    print("-" * 60)
    
    success = 0
    errors = 0
    skipped = 0
    
    for i, page in enumerate(pages, 1):
        keyword = page["keyword"]
        post_id = page["post_id"]
        url = page["url"]
        
        # Check if already exists
        page_folder = PAGES_FOLDER / keyword
        if page_folder.exists() and (page_folder / "page_info.json").exists():
            print(f"[{i}/{len(pages)}] ⏭️  {keyword} - already exists")
            skipped += 1
            continue
        
        print(f"[{i}/{len(pages)}] 📥 {keyword} (post {post_id})")
        
        try:
            if import_page(page["title"], keyword, url, post_id, dry_run=args.dry_run):
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

