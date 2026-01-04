#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_page_info.py - Creates page_info.json for each page folder

This script reads the CSV file with page data and creates a page_info.json
file in each existing page folder with the URL and Post ID.
"""

import os
import json
import csv
import re
from urllib.parse import unquote

# Configuration
CSV_FILE = "קישורי ויקי - מילות מפתח.csv"
PAGES_FOLDER = "דפים לשינוי"
OUTPUT_FILENAME = "page_info.json"

def normalize_name(name):
    """Normalize a name for comparison."""
    # Remove special characters, extra spaces, and convert to lowercase
    name = name.strip().lower()
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    # Remove common suffixes/prefixes
    name = re.sub(r'\s*-\s*✔️\s*רק\s*תבקש\s*', '', name)
    name = re.sub(r'\s*✔️.*$', '', name)
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def extract_page_name_from_url(url):
    """Extract page name from URL for matching."""
    # Get the last part of the URL path
    parts = url.rstrip('/').split('/')
    if parts:
        last_part = parts[-1]
        # URL decode
        decoded = unquote(last_part)
        return normalize_name(decoded)
    return ""

def load_csv_data():
    """Load page data from CSV file."""
    pages = {}
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file not found: {CSV_FILE}")
        return pages
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 4:
                page_name = row[0].strip()
                keyword = row[1].strip()
                url = row[2].strip()
                post_id = row[3].strip() if row[3].strip() else None
                
                # Store with multiple keys for matching
                normalized = normalize_name(page_name)
                keyword_normalized = normalize_name(keyword)
                url_name = extract_page_name_from_url(url)
                
                entry = {
                    'page_name': page_name,
                    'keyword': keyword,
                    'url': url,
                    'post_id': post_id
                }
                
                # Store by different keys for matching
                pages[normalized] = entry
                if keyword_normalized and keyword_normalized != normalized:
                    pages[keyword_normalized] = entry
                if url_name and url_name not in pages:
                    pages[url_name] = entry
    
    print(f"📊 Loaded {len(pages)} page entries from CSV")
    return pages

def find_matching_entry(folder_name, csv_data):
    """Find matching CSV entry for a folder name."""
    normalized_folder = normalize_name(folder_name)
    
    # Direct match
    if normalized_folder in csv_data:
        return csv_data[normalized_folder]
    
    # Partial match - folder name contains keyword
    for key, entry in csv_data.items():
        if normalized_folder in key or key in normalized_folder:
            return entry
    
    # Match by keyword
    for key, entry in csv_data.items():
        keyword = normalize_name(entry.get('keyword', ''))
        if keyword and (normalized_folder in keyword or keyword in normalized_folder):
            return entry
    
    return None

def create_page_info_files():
    """Create page_info.json files for all page folders."""
    csv_data = load_csv_data()
    
    if not csv_data:
        print("❌ No CSV data loaded, exiting")
        return
    
    if not os.path.exists(PAGES_FOLDER):
        print(f"❌ Pages folder not found: {PAGES_FOLDER}")
        return
    
    created = 0
    skipped = 0
    not_found = 0
    
    # Get all folders in the pages directory
    folders = [f for f in os.listdir(PAGES_FOLDER) 
               if os.path.isdir(os.path.join(PAGES_FOLDER, f))]
    
    print(f"📁 Found {len(folders)} page folders")
    print("-" * 50)
    
    for folder_name in sorted(folders):
        folder_path = os.path.join(PAGES_FOLDER, folder_name)
        info_file_path = os.path.join(folder_path, OUTPUT_FILENAME)
        
        # Check if page_info.json already exists
        if os.path.exists(info_file_path):
            print(f"⏭️  {folder_name}: page_info.json already exists")
            skipped += 1
            continue
        
        # Find matching CSV entry
        entry = find_matching_entry(folder_name, csv_data)
        
        if entry:
            # Create page_info.json
            page_info = {
                "page_name": entry['page_name'],
                "keyword": entry['keyword'],
                "url": entry['url'],
                "post_id": entry['post_id']
            }
            
            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(page_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {folder_name}: Created (Post ID: {entry['post_id']})")
            created += 1
        else:
            print(f"❓ {folder_name}: No matching CSV entry found")
            not_found += 1
    
    print("-" * 50)
    print(f"📊 Summary:")
    print(f"   ✅ Created: {created}")
    print(f"   ⏭️  Skipped (exists): {skipped}")
    print(f"   ❓ Not found: {not_found}")

def main():
    print("=" * 50)
    print("🚀 Page Info Generator")
    print("=" * 50)
    create_page_info_files()
    print("=" * 50)
    print("Done!")

if __name__ == "__main__":
    main()




