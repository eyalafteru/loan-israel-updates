#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to fetch WordPress post and save full response
"""

import requests
import json
import os
from datetime import datetime

# Load from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
wp_config = config.get("wordpress", {}).get("sites", {}).get("main", {})

# WordPress credentials from config.json
WP_SITE_URL = wp_config.get("site_url", "https://loan-israel.co.il")
WP_USERNAME = wp_config.get("username", "")
WP_PASSWORD = wp_config.get("password", "")

# Post ID to fetch (הלוואה חוץ בנקאית)
POST_ID = "98"

def get_token():
    """Get JWT token from WordPress"""
    token_url = f"{WP_SITE_URL}/wp-json/jwt-auth/v1/token"
    response = requests.post(token_url, json={
        "username": WP_USERNAME,
        "password": WP_PASSWORD
    }, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to get token: {response.status_code}")
        print(response.text)
        return None
    
    return response.json().get("token")

def fetch_post(post_id, token):
    """Fetch post with context=edit"""
    fetch_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}?context=edit"
    
    print(f"🔗 Fetching: {fetch_url}")
    
    response = requests.get(
        fetch_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    
    return response

def main():
    print("=" * 60)
    print(f"📡 WordPress API Test - Post ID: {POST_ID}")
    print(f"🕐 Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Check credentials
    if not WP_USERNAME or not WP_PASSWORD:
        print("❌ Missing credentials!")
        print("Set WP_MAIN_USERNAME and WP_MAIN_PASSWORD environment variables")
        return
    
    print(f"👤 Username: {WP_USERNAME}")
    
    # Get token
    print("\n🔑 Getting JWT token...")
    token = get_token()
    if not token:
        return
    print(f"✅ Token received: {token[:20]}...")
    
    # Fetch post
    print(f"\n📥 Fetching post {POST_ID}...")
    response = fetch_post(POST_ID, token)
    
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"📊 Response Size: {len(response.text)} bytes")
    
    # Save raw response
    raw_file = f"wp_test_raw_{POST_ID}.txt"
    with open(raw_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"💾 Saved raw response to: {raw_file}")
    
    # Parse and analyze
    if response.status_code == 200:
        data = response.json()
        
        # Save full JSON
        json_file = f"wp_test_full_{POST_ID}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved parsed JSON to: {json_file}")
        
        # Analyze content fields
        print("\n" + "=" * 60)
        print("📊 CONTENT ANALYSIS")
        print("=" * 60)
        
        content = data.get("content", {})
        raw_content = content.get("raw", "")
        rendered_content = content.get("rendered", "")
        
        print(f"\n📝 content.raw:")
        print(f"   Length: {len(raw_content)} chars")
        print(f"   Has '<style': {'<style' in raw_content}")
        print(f"   Has '<script': {'<script' in raw_content}")
        print(f"   Has '<!-- wp:html': {'<!-- wp:html' in raw_content}")
        print(f"   First 300 chars:")
        print(f"   {raw_content[:300]}")
        
        print(f"\n📝 content.rendered:")
        print(f"   Length: {len(rendered_content)} chars")
        print(f"   Has '<style': {'<style' in rendered_content}")
        print(f"   Has '<script': {'<script' in rendered_content}")
        print(f"   Has '<!-- wp:html': {'<!-- wp:html' in rendered_content}")
        print(f"   First 300 chars:")
        print(f"   {rendered_content[:300]}")
        
        # Save content fields separately
        if raw_content:
            with open(f"wp_test_content_raw_{POST_ID}.html", 'w', encoding='utf-8') as f:
                f.write(raw_content)
            print(f"\n💾 Saved content.raw to: wp_test_content_raw_{POST_ID}.html")
        
        if rendered_content:
            with open(f"wp_test_content_rendered_{POST_ID}.html", 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            print(f"💾 Saved content.rendered to: wp_test_content_rendered_{POST_ID}.html")
        
        # Check all top-level keys
        print("\n" + "=" * 60)
        print("📋 ALL RESPONSE KEYS:")
        print("=" * 60)
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, str):
                print(f"   {key}: (string, {len(value)} chars)")
            elif isinstance(value, dict):
                print(f"   {key}: (dict, keys: {list(value.keys())})")
            elif isinstance(value, list):
                print(f"   {key}: (list, {len(value)} items)")
            else:
                print(f"   {key}: {type(value).__name__}")
    
    else:
        print(f"❌ Error: {response.text[:500]}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

