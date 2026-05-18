# -*- coding: utf-8 -*-
"""
Local Scraper with Playwright/Chrome
סקרייפר מקומי עם Chrome אמיתי - מהיר יותר מ-Apify
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional


class PlaywrightScraper:
    """
    סקרייפר מקומי עם Playwright ו-Chrome
    פותח דפדפן אמיתי עם User-Agent אמיתי
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.timeout = 30000  # 30 seconds per page
    
    def _get_real_user_agent(self) -> str:
        """מחזיר User-Agent אמיתי של Chrome על Windows"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def _is_blocked(self, content: str, title: str) -> bool:
        """בודק אם הדף חסום או דורש CAPTCHA"""
        if not content:
            return True
        
        # Check for common blocking indicators
        blocking_patterns = [
            r'access\s*denied',
            r'blocked',
            r'captcha',
            r'cloudflare',
            r'please\s*verify',
            r'are\s*you\s*a\s*robot',
            r'הגישה\s*נחסמה',
            r'אימות',
            r'bot\s*detection',
            r'rate\s*limit',
            r'too\s*many\s*requests',
            r'403\s*forbidden',
            r'just\s*a\s*moment',
            r'checking\s*your\s*browser'
        ]
        
        combined_text = (content + ' ' + title).lower()
        
        for pattern in blocking_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                # Only consider blocked if content is very short
                if len(content) < 500:
                    return True
        
        return False
    
    def _extract_content(self, page) -> Dict[str, str]:
        """חילוץ תוכן מהדף - משופר לחילוץ נתונים פיננסיים"""
        try:
            # Get title
            title = page.title()
            
            # Remove unwanted elements - more aggressive cleaning
            page.evaluate("""() => {
                const removeSelectors = [
                    'script', 'style', 'nav', 'header', 'footer', 'aside',
                    'noscript', '.cookie-banner', '.popup', '.modal',
                    '.advertisement', '.ads', '[hidden]', '.hidden',
                    '#cookie', '.cookie', '.consent', '.gdpr',
                    'iframe', '.social-share', '.breadcrumb', '.menu',
                    '.navigation', '.sidebar', '.widget', '.related-posts',
                    '.comments', 'form:not(.calculator)', '.newsletter'
                ];
                removeSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            }""")
            
            # Extract structured data - tables, lists, key-value pairs
            structured_data = page.evaluate("""() => {
                let data = [];
                
                // Extract table data (important for financial info)
                document.querySelectorAll('table').forEach(table => {
                    const rows = [];
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = [];
                        tr.querySelectorAll('th, td').forEach(cell => {
                            cells.push(cell.innerText.trim());
                        });
                        if (cells.length > 0) rows.push(cells.join(' | '));
                    });
                    if (rows.length > 0) data.push('טבלה: ' + rows.join(' ; '));
                });
                
                // Extract definition lists (common for loan terms)
                document.querySelectorAll('dl').forEach(dl => {
                    const items = [];
                    const dts = dl.querySelectorAll('dt');
                    const dds = dl.querySelectorAll('dd');
                    dts.forEach((dt, i) => {
                        const dd = dds[i];
                        if (dd) items.push(dt.innerText.trim() + ': ' + dd.innerText.trim());
                    });
                    if (items.length > 0) data.push(items.join(' | '));
                });
                
                // Extract key financial indicators with context
                const patterns = [
                    /ריבית[^\\d]*(\\d+[.,]?\\d*\\s*%)/gi,
                    /עד\\s*(\\d+[,.]?\\d*\\s*₪)/gi,
                    /מ?-?\\s*(\\d+[,.]?\\d*)\\s*(שנ|חוד|שנים|חודשים)/gi,
                    /פריים\\s*\\+?\\s*(\\d+[.,]?\\d*%?)/gi,
                    /אחוז\\s*מימון[^\\d]*(\\d+[.,]?\\d*\\s*%)/gi,
                    /LTV[^\\d]*(\\d+[.,]?\\d*\\s*%)/gi
                ];
                
                return data.join('\\n');
            }""")
            
            # Try to get main content first
            content = page.evaluate("""() => {
                const mainSelectors = [
                    'main', 'article', '.content', '.main-content',
                    '#content', '#main', '.page-content', '.entry-content',
                    '[role="main"]', '.post-content', '.article-content',
                    '.loan-details', '.product-info', '.terms-conditions'
                ];
                
                for (const sel of mainSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim().length > 100) {
                        return el.innerText.trim();
                    }
                }
                
                // Fallback to body
                return document.body.innerText.trim();
            }""")
            
            # Combine structured data with content
            if structured_data:
                content = f"=== נתונים מובנים ===\n{structured_data}\n\n=== תוכן הדף ===\n{content}"
            
            # Clean up whitespace but preserve some structure
            content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 newlines
            content = re.sub(r'[ \t]+', ' ', content)  # Clean horizontal whitespace
            content = content.strip()
            
            return {
                'title': title,
                'content': content
            }
            
        except Exception as e:
            print(f"[LocalScraper] Error extracting content: {e}")
            return {'title': '', 'content': ''}
    
    def scrape(self, url: str, headless: bool = False) -> Dict[str, Any]:
        """
        סריקת URL עם Chrome מקומי
        
        Args:
            url: הכתובת לסריקה
            headless: True = רקע, False = חלון גלוי
            
        Returns:
            {
                'success': bool,
                'content': str,
                'title': str,
                'url': str,
                'method': 'local_chrome',
                'timestamp': str,
                'error': str (if failed)
            }
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {
                'success': False,
                'error': 'Playwright לא מותקן. הרץ: pip install playwright && playwright install chromium',
                'method': 'local_chrome'
            }
        
        print(f"[LocalScraper] Scraping {url} (headless={headless})...")
        
        try:
            with sync_playwright() as p:
                # Launch Chrome (visible mode by default)
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                # Create context with real user agent
                context = browser.new_context(
                    user_agent=self._get_real_user_agent(),
                    viewport={'width': 1920, 'height': 1080},
                    locale='he-IL',
                    timezone_id='Asia/Jerusalem'
                )
                
                # Create page
                page = context.new_page()
                
                # Navigate to URL
                try:
                    page.goto(url, wait_until='networkidle', timeout=self.timeout)
                except Exception as nav_error:
                    # Try with domcontentloaded if networkidle times out
                    print(f"[LocalScraper] networkidle failed, trying domcontentloaded: {nav_error}")
                    page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                
                # Wait a bit for dynamic content
                page.wait_for_timeout(2000)
                
                # Extract content
                extracted = self._extract_content(page)
                title = extracted['title']
                content = extracted['content']
                
                # Close browser
                browser.close()
                
                # Check if blocked
                if self._is_blocked(content, title):
                    print(f"[LocalScraper] Detected blocking on {url}")
                    return {
                        'success': False,
                        'error': 'הדף חסום או דורש אימות',
                        'method': 'local_chrome',
                        'blocked': True
                    }
                
                # Check if we got meaningful content
                if not content or len(content) < 50:
                    return {
                        'success': False,
                        'error': 'לא נמצא תוכן בדף',
                        'method': 'local_chrome'
                    }
                
                print(f"[LocalScraper] Success: {len(content)} chars extracted")
                
                return {
                    'success': True,
                    'content': content,
                    'title': title,
                    'url': url,
                    'method': 'local_chrome',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            error_msg = str(e)
            print(f"[LocalScraper] Error: {error_msg}")
            
            # Check for specific errors
            if 'Executable doesn\'t exist' in error_msg or 'browserType.launch' in error_msg:
                return {
                    'success': False,
                    'error': 'Chrome לא מותקן. הרץ: playwright install chromium',
                    'method': 'local_chrome'
                }
            
            return {
                'success': False,
                'error': error_msg,
                'method': 'local_chrome'
            }


# Quick test
if __name__ == "__main__":
    print("Testing Local Scraper...")
    scraper = PlaywrightScraper()
    
    # Test with a simple page
    test_url = "https://www.google.com"
    result = scraper.scrape(test_url, headless=False)
    
    print(f"\nResult: {result.get('success')}")
    if result.get('success'):
        print(f"Title: {result.get('title')}")
        print(f"Content length: {len(result.get('content', ''))}")
    else:
        print(f"Error: {result.get('error')}")
