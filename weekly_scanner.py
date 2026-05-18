# -*- coding: utf-8 -*-
"""
Weekly Scanner - Automated Source Scanning and Change Detection
סורק שבועי אוטומטי לזיהוי שינויים במקורות מידע
"""

import sys
import json
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from project modules
from ai_summarizer import OllamaSummarizer, check_ollama_status

# Import SourceStorageManager and DataSourceScraper dynamically
# to avoid circular imports
def get_storage_manager():
    """Get SourceStorageManager instance"""
    from dashboard_server import SourceStorageManager
    return SourceStorageManager()

def get_scraper():
    """Get DataSourceScraper instance"""
    from dashboard_server import DataSourceScraper
    import os
    from dotenv import load_dotenv
    load_dotenv('api_config.env')
    token = os.getenv('APIFY_TOKEN', '')
    
    if not token:
        # Try to load from config
        try:
            config_path = Path(__file__).parent / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    token = config.get('apify_token', '')
        except:
            pass
    
    from dashboard_server import DataSourceScraper
    return DataSourceScraper(token)


class WeeklySourceScanner:
    """
    סורק שבועי לזיהוי שינויים במקורות מידע
    """
    
    def __init__(self, use_ai=True):
        self.storage = get_storage_manager()
        self.scraper = get_scraper()
        self.use_ai = use_ai
        self.summarizer = None
        
        if use_ai:
            self.summarizer = OllamaSummarizer()
            if not self.summarizer.is_available():
                print("[Scanner] Warning: Ollama not available, running without AI analysis")
                self.use_ai = False
    
    def get_all_data_sources(self):
        """קבלת כל מקורות המידע מכל העמודים"""
        from dashboard_server import BASE_DIR
        
        sources = {}  # url -> {source info}
        pages_dir = BASE_DIR / "דפים לשינוי"
        
        if not pages_dir.exists():
            print(f"[Scanner] Pages directory not found: {pages_dir}")
            return sources
        
        # Scan all page folders
        for page_type in ["main", "business"]:
            type_dir = pages_dir / page_type
            if not type_dir.exists():
                continue
            
            for page_dir in type_dir.iterdir():
                if not page_dir.is_dir():
                    continue
                
                page_info_path = page_dir / "page_info.json"
                if not page_info_path.exists():
                    continue
                
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    
                    page_path = f"{page_type}/{page_dir.name}"
                    data_sources = page_info.get("data_sources", [])
                    
                    for ds in data_sources:
                        url = ds.get("url")
                        if url:
                            if url not in sources:
                                sources[url] = {
                                    "url": url,
                                    "description": ds.get("description", ""),
                                    "used_by_pages": []
                                }
                            sources[url]["used_by_pages"].append({
                                "path": page_path,
                                "name": page_info.get("name", page_dir.name)
                            })
                            
                except Exception as e:
                    print(f"[Scanner] Error reading {page_info_path}: {e}")
        
        print(f"[Scanner] Found {len(sources)} unique data sources")
        return sources
    
    def scan_source(self, url, description=""):
        """סריקת מקור בודד"""
        source_id = self.storage.get_source_id(url)
        
        print(f"[Scanner] Scanning: {url}")
        
        # Get previous version for comparison
        previous = self.storage.get_previous_version(source_id)
        previous_hash = previous.get("content_hash") if previous else None
        
        # Scrape the source
        result = self.scraper.scrape(url, force_refresh=True)
        
        if not result.get("success"):
            return {
                "source_id": source_id,
                "url": url,
                "success": False,
                "error": result.get("error", "Scraping failed")
            }
        
        content = result.get("content", "")
        title = result.get("title", description)
        
        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # Save to history
        self.storage.save_to_history(source_id, url, title, content, content_hash)
        
        # Check if content changed
        has_changes = previous_hash != content_hash if previous_hash else True
        
        scan_result = {
            "source_id": source_id,
            "url": url,
            "title": title,
            "success": True,
            "has_changes": has_changes,
            "content_hash": content_hash,
            "previous_hash": previous_hash,
            "word_count": len(content.split()),
            "scraped_at": datetime.now().isoformat()
        }
        
        # If content changed and AI is available, analyze
        if has_changes and self.use_ai and previous:
            print(f"[Scanner] Changes detected, analyzing with AI...")
            
            # Compare versions
            comparison = self.summarizer.compare_versions(
                previous.get("content", ""),
                content
            )
            
            if comparison.get("success"):
                scan_result["ai_analysis"] = comparison
                scan_result["changes"] = comparison.get("changes", [])
                scan_result["importance"] = comparison.get("importance", "medium")
                scan_result["changes_summary"] = comparison.get("summary", "")
                
                # Save AI summary
                self.storage.save_ai_summary(source_id, comparison)
            else:
                scan_result["ai_analysis"] = None
        
        return scan_result
    
    def run_full_scan(self):
        """הרצת סריקה מלאה של כל המקורות"""
        print("=" * 60)
        print("[Scanner] Starting full weekly scan")
        print(f"[Scanner] Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Get all sources
        all_sources = self.get_all_data_sources()
        
        if not all_sources:
            print("[Scanner] No data sources found")
            return {
                "success": True,
                "stats": {"sources_scanned": 0, "changes_detected": 0},
                "changes": []
            }
        
        # Scan each source
        results = []
        changes = []
        errors = []
        
        for url, source_info in all_sources.items():
            try:
                result = self.scan_source(url, source_info.get("description", ""))
                result["used_by_pages"] = source_info.get("used_by_pages", [])
                results.append(result)
                
                if result.get("has_changes") and result.get("success"):
                    changes.append(result)
                
                if not result.get("success"):
                    errors.append(result)
                    
            except Exception as e:
                print(f"[Scanner] Error scanning {url}: {e}")
                errors.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        # Generate report
        report = self.generate_report(results, changes, errors)
        
        # Save report
        self.storage.save_weekly_report(report)
        
        # Cleanup old files
        self.cleanup_old_history()
        
        print("=" * 60)
        print(f"[Scanner] Scan complete!")
        print(f"[Scanner] Sources scanned: {len(results)}")
        print(f"[Scanner] Changes detected: {len(changes)}")
        print(f"[Scanner] Errors: {len(errors)}")
        print("=" * 60)
        
        return report
    
    def generate_report(self, results, changes, errors):
        """יצירת דוח שבועי"""
        report_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get previous report date
        reports = self.storage.list_weekly_reports()
        previous_date = reports[0]["date"] if reports else None
        
        report = {
            "report_date": report_date,
            "period": {
                "from": previous_date or report_date,
                "to": report_date
            },
            "generated_at": datetime.now().isoformat(),
            "ai_enabled": self.use_ai,
            "stats": {
                "sources_scanned": len(results),
                "changes_detected": len(changes),
                "unchanged": len([r for r in results if r.get("success") and not r.get("has_changes")]),
                "errors": len(errors),
                "high_importance": len([c for c in changes if c.get("importance") == "high"]),
                "medium_importance": len([c for c in changes if c.get("importance") == "medium"]),
                "low_importance": len([c for c in changes if c.get("importance") == "low"])
            },
            "changes": [
                {
                    "source_id": c.get("source_id"),
                    "url": c.get("url"),
                    "title": c.get("title"),
                    "importance": c.get("importance", "medium"),
                    "changes_summary": c.get("changes_summary", "התוכן השתנה"),
                    "changes": c.get("changes", []),
                    "affected_pages": [p.get("name") for p in c.get("used_by_pages", [])],
                    "affected_page_paths": [p.get("path") for p in c.get("used_by_pages", [])],
                    "scraped_at": c.get("scraped_at")
                }
                for c in changes
            ],
            "errors": [
                {
                    "url": e.get("url"),
                    "error": e.get("error", "Unknown error")
                }
                for e in errors
            ]
        }
        
        return report
    
    def cleanup_old_history(self, max_age_days=365):
        """ניקוי קבצי היסטוריה ישנים (מעל שנה)"""
        print(f"[Scanner] Cleaning up files older than {max_age_days} days...")
        
        source_ids = self.storage.get_all_source_ids()
        total_deleted = 0
        
        for source_id in source_ids:
            deleted = self.storage.cleanup_old_files(source_id, max_age_days)
            total_deleted += deleted
        
        print(f"[Scanner] Cleaned up {total_deleted} old files")
        return total_deleted
    
    def scan_single_source(self, url):
        """סריקת מקור בודד (לבדיקות)"""
        print(f"[Scanner] Scanning single source: {url}")
        return self.scan_source(url)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Weekly Source Scanner')
    parser.add_argument('--full-scan', action='store_true', help='Run full scan of all sources')
    parser.add_argument('--url', type=str, help='Scan a single URL')
    parser.add_argument('--no-ai', action='store_true', help='Run without AI analysis')
    parser.add_argument('--cleanup', action='store_true', help='Only run cleanup of old files')
    parser.add_argument('--status', action='store_true', help='Check scanner status')
    
    args = parser.parse_args()
    
    if args.status:
        # Check status
        print("Checking scanner status...")
        ollama_status = check_ollama_status()
        print(f"Ollama: {'Available' if ollama_status['ollama_available'] else 'Not available'}")
        print(f"Model: {ollama_status['model']}")
        print(f"URL: {ollama_status['base_url']}")
        return
    
    scanner = WeeklySourceScanner(use_ai=not args.no_ai)
    
    if args.cleanup:
        scanner.cleanup_old_history()
        return
    
    if args.url:
        result = scanner.scan_single_source(args.url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    if args.full_scan:
        report = scanner.run_full_scan()
        print("\n" + "=" * 60)
        print("WEEKLY REPORT SUMMARY")
        print("=" * 60)
        print(f"Date: {report['report_date']}")
        print(f"Sources Scanned: {report['stats']['sources_scanned']}")
        print(f"Changes Detected: {report['stats']['changes_detected']}")
        print(f"  - High Importance: {report['stats']['high_importance']}")
        print(f"  - Medium Importance: {report['stats']['medium_importance']}")
        print(f"  - Low Importance: {report['stats']['low_importance']}")
        print(f"Errors: {report['stats']['errors']}")
        
        if report['changes']:
            print("\nCHANGES:")
            for change in report['changes']:
                print(f"\n  [{change['importance'].upper()}] {change['title']}")
                print(f"    URL: {change['url']}")
                print(f"    Summary: {change['changes_summary']}")
                print(f"    Affects: {', '.join(change['affected_pages'])}")
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
