#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick runner for DataLayer Agent
Avoids path issues with Hebrew characters

Usage:
    py run_agent.py --dry-run    (test without changes)
    py run_agent.py              (apply changes)
"""
import sys
import os
import re
from pathlib import Path
from datetime import datetime

# Set proper encoding for Windows
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Get script directory and target folder
try:
    SCRIPT_DIR = Path(__file__).parent.resolve()
except NameError:
    # When run via exec(), __file__ might not be defined
    SCRIPT_DIR = Path.cwd()

TARGET_FOLDER = SCRIPT_DIR / "מחשבונים מוכנים לעלייה לאוויר"

# If target folder not found, try to find it
if not TARGET_FOLDER.exists():
    for item in SCRIPT_DIR.iterdir():
        if item.is_dir():
            calc_folder = item / "מחשבונים מוכנים לעלייה לאוויר"
            if calc_folder.exists():
                TARGET_FOLDER = calc_folder
                SCRIPT_DIR = item
                break


class DataLayerAgent:
    """Agent for injecting DataLayer into copy buttons"""
    
    def __init__(self, target_folder, dry_run=False):
        self.target_folder = Path(target_folder)
        self.dry_run = dry_run
        self.results = []
        self.total_files = 0
        self.modified_files = 0
        self.skipped_files = 0
        self.buttons_found = 0
        self.functions_updated = 0
    
    def extract_calculator_name(self, filename, content):
        """Extract calculator name from file"""
        # Try CALCULATOR_NAME constant
        match = re.search(r"const\s+CALCULATOR_NAME\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
        
        # Try H1 tag
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Use filename
        return filename.replace('.html', '')
    
    def find_copy_buttons(self, content):
        """Find all copy buttons in file"""
        patterns = [
            r'data-action=["\']copy-embed-code["\']',
            r'data-action=["\']copy-preview-code["\']',
        ]
        buttons = []
        for pattern in patterns:
            if re.search(pattern, content):
                match = re.search(r'copy-\w+-code', pattern)
                if match:
                    buttons.append(match.group().replace('\\', '').replace('"', '').replace("'", ''))
        
        # Direct search
        if 'copy-embed-code' in content:
            buttons.append('copy-embed-code')
        if 'copy-preview-code' in content:
            buttons.append('copy-preview-code')
        
        return list(set(buttons))
    
    def check_if_datalayer_exists(self, content):
        """Check if dataLayer already exists"""
        return 'copy_code_click' in content
    
    def generate_datalayer_code(self, calculator_name, button_type):
        """Generate dataLayer code"""
        return f'''
        // DataLayer Push - Tag Manager tracking
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({{
            'event': 'copy_code_click',
            'calculator_name': '{calculator_name}',
            'button_type': '{button_type}'
        }});'''
    
    def update_copy_function(self, content, func_name, calculator_name, button_type):
        """Update copy function with dataLayer"""
        pattern = rf'(function\s+{func_name}\s*\(\s*\)\s*\{{)'
        
        func_match = re.search(pattern, content)
        if not func_match:
            return content, False
        
        # Check if already has dataLayer
        func_start = func_match.end()
        brace_count = 1
        func_end = func_start
        while brace_count > 0 and func_end < len(content):
            if content[func_end] == '{':
                brace_count += 1
            elif content[func_end] == '}':
                brace_count -= 1
            func_end += 1
        
        func_body = content[func_start:func_end]
        if 'dataLayer.push' in func_body:
            return content, False
        
        # Add dataLayer code
        datalayer_code = self.generate_datalayer_code(calculator_name, button_type)
        new_func_start = func_match.group(1) + datalayer_code + '\n        '
        new_content = content[:func_match.start()] + new_func_start + content[func_start:]
        
        return new_content, True
    
    def process_file(self, filepath):
        """Process a single file"""
        result = {
            'file': filepath.name,
            'status': 'pending',
            'buttons_found': [],
            'functions_updated': [],
            'calculator_name': '',
            'message': ''
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Extract calculator name
            calc_name = self.extract_calculator_name(filepath.name, content)
            result['calculator_name'] = calc_name
            
            # Check if already has dataLayer
            if self.check_if_datalayer_exists(content):
                result['status'] = 'skipped'
                result['message'] = 'DataLayer already exists - skipping'
                self.skipped_files += 1
                return result
            
            # Find copy buttons
            buttons = self.find_copy_buttons(content)
            result['buttons_found'] = buttons
            self.buttons_found += len(buttons)
            
            if not buttons:
                result['status'] = 'no_buttons'
                result['message'] = 'No copy buttons found'
                return result
            
            # Update functions
            modified = False
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
            
            # Save changes
            if modified and content != original_content:
                if not self.dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    result['status'] = 'updated'
                    result['message'] = f'Updated - {len(result["functions_updated"])} functions'
                else:
                    result['status'] = 'would_update'
                    result['message'] = f'Would update (dry-run) - {len(result["functions_updated"])} functions'
                self.modified_files += 1
            else:
                result['status'] = 'no_changes'
                result['message'] = 'No changes needed'
            
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f'Error: {str(e)}'
        
        return result
    
    def run(self):
        """Run the agent"""
        print("\n" + "="*70)
        print("DataLayer Agent for Copy Buttons")
        print("="*70)
        print(f"\nTarget folder: {self.target_folder}")
        print(f"Mode: {'DRY RUN (no changes)' if self.dry_run else 'LIVE (applying changes)'}")
        print("-"*70)
        
        html_files = list(self.target_folder.glob("*.html"))
        self.total_files = len(html_files)
        
        print(f"\nFound {self.total_files} HTML files\n")
        
        for i, filepath in enumerate(html_files, 1):
            print(f"\n[{i}/{self.total_files}] {filepath.name}")
            print("-"*50)
            
            result = self.process_file(filepath)
            self.results.append(result)
            
            status_icons = {
                'updated': '[OK]',
                'would_update': '[DRY]',
                'skipped': '[SKIP]',
                'no_buttons': '[WARN]',
                'no_changes': '[-]',
                'error': '[ERR]'
            }
            
            icon = status_icons.get(result['status'], '[?]')
            print(f"   {icon} Status: {result['message']}")
            print(f"   Calculator: {result['calculator_name']}")
            
            if result['buttons_found']:
                print(f"   Buttons: {', '.join(result['buttons_found'])}")
            
            if result['functions_updated']:
                print(f"   Updated: {', '.join(result['functions_updated'])}")
        
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"""
    Total files:        {self.total_files}
    Updated:            {self.modified_files}
    Skipped:            {self.skipped_files}
    Buttons found:      {self.buttons_found}
    Functions updated:  {self.functions_updated}
    
    Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
        if self.dry_run:
            print("*** DRY RUN - No changes were made! ***")
            print("    Run without --dry-run to apply changes")
        
        print("="*70)


def main():
    """Main function"""
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Target folder: {TARGET_FOLDER}")
    print(f"Dry run: {dry_run}")
    
    if not TARGET_FOLDER.exists():
        print(f"ERROR: Target folder not found: {TARGET_FOLDER}")
        sys.exit(1)
    
    agent = DataLayerAgent(TARGET_FOLDER, dry_run=dry_run)
    agent.run()


if __name__ == "__main__":
    main()

