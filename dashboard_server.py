# -*- coding: utf-8 -*-
"""
Page Management Dashboard - Flask Server
מערכת ניהול עמודים עם תמיכה בסוכנים חד/דו/תלת-שלביים
"""

import os
import sys
import json
import csv
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path

def get_python_command():
    """Get the correct Python command for this system"""
    # Try py -3 first (Windows Python Launcher)
    try:
        result = subprocess.run(['py', '-3', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return 'py -3'
    except:
        pass
    
    # Try python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0 and 'Python' in result.stdout:
            return 'python'
    except:
        pass
    
    # Fallback to python3
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return 'python3'
    except:
        pass
    
    return 'python'  # Default fallback

PYTHON_CMD = get_python_command()
print(f"[System] Using Python command: {PYTHON_CMD}")

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from dotenv import load_dotenv

# Import AI detection module
try:
    import ai_detection
    AI_DETECTION_AVAILABLE = True
except ImportError:
    AI_DETECTION_AVAILABLE = False

# Load environment variables from multiple sources
load_dotenv()  # Load .env if exists
load_dotenv(Path(__file__).parent / "api_config.env")  # Load api_config.env

# Get Anthropic API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

app = Flask(__name__)
CORS(app)

# Track running Claude process
running_claude_process = None

# Step completion events for SSE (webhook-based step tracking)
step_events = {}

# ============ Configuration ============

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def save_config(config):
    """Save configuration to config.json"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# Global config
config = load_config()

# JWT tokens cache - dynamically populated for all sites
jwt_tokens = {}

def get_jwt_token(site_id):
    """Get JWT token for a site"""
    return jwt_tokens.get(site_id)

def set_jwt_token(site_id, token):
    """Set JWT token for a site"""
    jwt_tokens[site_id] = token

# ============ Claude Command Helper ============

def get_claude_command():
    """Get Claude command - find dynamically or use from config.
    This ensures the command works on any computer regardless of username."""
    config_cmd = config.get("claude_code", {}).get("command", "claude")
    
    # If it's just "claude", find full path dynamically
    if config_cmd == "claude":
        try:
            result = subprocess.run(['where', 'claude'], capture_output=True, text=True)
            if result.returncode == 0:
                # Get the .cmd version (preferred on Windows)
                for line in result.stdout.strip().split('\n'):
                    if line.strip().endswith('.cmd'):
                        return line.strip()
                # Fallback to first result
                first_line = result.stdout.strip().split('\n')[0].strip()
                if first_line:
                    return first_line
        except Exception as e:
            print(f"[Claude] Error finding claude command: {e}")
    
    return config_cmd

# ============ Agent Loading (New System) ============

def load_agents_from_folder():
    """Load all agents from the agents/ folder"""
    agents = {}
    agents_folder = BASE_DIR / config.get("paths", {}).get("agents_folder", "agents")
    
    if not agents_folder.exists():
        print(f"[Agents] Folder not found: {agents_folder}")
        return agents
    
    for agent_file in agents_folder.glob("*.json"):
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                agent = json.load(f)
                agent_id = agent.get("id", agent_file.stem)
                agents[agent_id] = agent
                print(f"[Agents] Loaded: {agent_id}")
        except Exception as e:
            print(f"[Agents] Error loading {agent_file}: {e}")
    
    return agents

def get_agent_by_id(agent_id):
    """Get a specific agent by ID from agents folder OR config.json"""
    agents_folder = BASE_DIR / config.get("paths", {}).get("agents_folder", "agents")
    
    # First try exact filename match
    agent_file = agents_folder / f"{agent_id}.json"
    if agent_file.exists():
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                agent = json.load(f)
                agent["id"] = agent_id  # Ensure ID is set
                return agent
        except Exception as e:
            print(f"[Agents] Error loading {agent_id}: {e}")
    
    # Search all files for matching internal ID
    if agents_folder.exists():
        for file in agents_folder.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    agent = json.load(f)
                    if agent.get("id") == agent_id:
                        return agent
            except Exception as e:
                print(f"[Agents] Error reading {file}: {e}")
    
    # Fallback to config.json
    if "agents" in config and agent_id in config["agents"]:
        agent = config["agents"][agent_id].copy()
        agent["id"] = agent_id
        return agent
    
    return None

def get_agent_unified(agent_id):
    """Get agent from agents/ folder first, then fallback to config.json
    This connects the new agent builder with the old workflow system."""
    # First try the new agents folder
    agent = get_agent_by_id(agent_id)
    if agent:
        print(f"[Agents] Found '{agent_id}' in agents/ folder (new system)")
        return agent
    
    # Fallback to config.json (old system)
    agent = config.get("agents", {}).get(agent_id)
    if agent:
        print(f"[Agents] Found '{agent_id}' in config.json (legacy)")
        return agent
    
    print(f"[Agents] Agent '{agent_id}' not found in either location")
    return None

def save_agent(agent):
    """Save an agent to the agents folder"""
    agents_folder = BASE_DIR / config.get("paths", {}).get("agents_folder", "agents")
    agents_folder.mkdir(parents=True, exist_ok=True)
    
    agent_id = agent.get("id")
    if not agent_id:
        raise ValueError("Agent must have an id")
    
    agent["updated"] = datetime.now().isoformat()
    
    agent_file = agents_folder / f"{agent_id}.json"
    with open(agent_file, 'w', encoding='utf-8') as f:
        json.dump(agent, f, ensure_ascii=False, indent=2)
    
    return agent_file

def delete_agent_file(agent_id):
    """Delete an agent file from the agents folder"""
    agents_folder = BASE_DIR / config.get("paths", {}).get("agents_folder", "agents")
    agent_file = agents_folder / f"{agent_id}.json"
    
    if agent_file.exists():
        agent_file.unlink()
        return True
    return False

# ============ ShortcodeEngine ============

class ShortcodeEngine:
    """Engine for processing dynamic shortcodes in agent prompts"""
    
    # Per-page shortcodes (dynamic, based on page folder/info)
    PAGE_SHORTCODES = {
        "PAGE_HTML": "תוכן HTML של העמוד",
        "PAGE_HTML_PATH": "נתיב לקובץ HTML של העמוד",
        "PAGE_PATH": "נתיב לקובץ HTML של העמוד",
        "PAGE_KEYWORD": "מילת מפתח ראשית",
        "PAGE_URL": "כתובת העמוד",
        "PAGE_WORD_COUNT": "מספר מילים בעמוד",
        "KEYWORDS_AUTOCOMPLETE": "מילות מפתח מהשלמות אוטומטיות",
        "KEYWORDS_RELATED": "מילות מפתח מחיפושים קשורים",
        "SERP_ORGANIC": "תוצאות חיפוש אורגניות",
        "SERP_AI_OVERVIEW": "תוצאות AI Overview של גוגל",
        "OUR_SERP_RANK": "המיקום שלנו בתוצאות"
    }
    
    # Global shortcodes (static, not per-page)
    GLOBAL_SHORTCODES = {
        "TODAY_DATE": "תאריך נוכחי",
        "CURRENT_MONTH": "החודש הנוכחי בעברית",
        "BOI_INTEREST_RATE": "ריבית בנק ישראל"
    }
    
    # Combined for backward compatibility
    BUILTIN_SHORTCODES = {**PAGE_SHORTCODES, **GLOBAL_SHORTCODES}
    
    # Step-specific shortcodes (resolved per step)
    STEP_SHORTCODES = {
        "PROMPT_FILE_PATH": "נתיב לקובץ ההוראות של השלב הנוכחי",
        "OUTPUT_PATH": "נתיב לקובץ הפלט של השלב הנוכחי",
        "STEP_NUM": "מספר השלב הנוכחי",
        "STEP_NAME": "שם השלב הנוכחי"
    }
    
    def __init__(self, page_path=None, agent=None, step_num=None):
        self.page_path = page_path
        self.page_folder = get_page_folder(page_path) if page_path else None
        self.agent = agent
        self.step_num = step_num
        self.step_reports = {}
        self.custom_sources = {}
        self.context = {}
        
        # Set step-specific context if agent and step provided
        if agent and step_num:
            self._set_step_context(agent, step_num)
        
        # Load custom data sources from config
        self._load_custom_sources()
    
    def _set_step_context(self, agent, step_num):
        """Set step-specific shortcode values based on agent configuration"""
        step_key = f"step{step_num}"
        step_data = agent.get(step_key, {})
        
        # Also check steps array (new format)
        steps = agent.get("steps", [])
        for s in steps:
            if s.get("order") == step_num or s.get("id") == step_key:
                step_data = s
                break
        
        # Get prompt file path
        prompt_file = step_data.get("prompt_file") or step_data.get("agent", "")
        if prompt_file and not prompt_file.endswith(".md"):
            prompt_file += ".md"
        self.context["PROMPT_FILE_PATH"] = str(BASE_DIR / prompt_file) if prompt_file else ""
        
        # Get output path
        output = step_data.get("output", {})
        output_name = output.get("path") or step_data.get("output_name", f"דוח שלב {step_num}.md")
        if self.page_folder:
            # Use folder_name first (e.g., "הלוואות לעסקים"), then name, then id
            agent_folder_name = agent.get("folder_name") or agent.get("name") or agent.get("id", "agent")
            agent_folder = BASE_DIR / self.page_folder / agent_folder_name
            self.context["OUTPUT_PATH"] = str(agent_folder / output_name)
        else:
            self.context["OUTPUT_PATH"] = output_name
        
        # Step info
        self.context["STEP_NUM"] = str(step_num)
        self.context["STEP_NAME"] = step_data.get("name", f"שלב {step_num}")
        
        # Page HTML path
        if self.page_path:
            self.context["PAGE_HTML_PATH"] = str(BASE_DIR / self.page_path)
        
        print(f"[Shortcode] Step {step_num} context set: PROMPT_FILE_PATH={self.context.get('PROMPT_FILE_PATH')}")
    
    def _load_custom_sources(self):
        """Load custom data sources from config"""
        for source in config.get("custom_data_sources", []):
            try:
                source_path = BASE_DIR / source["path"]
                source_type = source.get("type", "text")
                
                if source_type == "file_path":
                    # For file_path type, store the absolute path (not content)
                    self.custom_sources[source["shortcode"]] = str(source_path)
                    print(f"[Shortcode] Registered file path: {source['shortcode']} -> {source_path}")
                elif source_path.exists():
                    # For text type, read and store content
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.custom_sources[source["shortcode"]] = content
                    print(f"[Shortcode] Loaded custom source: {source['shortcode']}")
                else:
                    print(f"[Shortcode] File not found: {source_path}")
            except Exception as e:
                print(f"[Shortcode] Error loading {source['id']}: {e}")
    
    def register_step_report(self, step_id, content):
        """Register a step report as a shortcode for subsequent steps"""
        shortcode_name = f"STEP{step_id}_REPORT"
        self.step_reports[shortcode_name] = content
        self.step_reports["PREVIOUS_STEP_REPORT"] = content
        print(f"[Shortcode] Registered step report: {shortcode_name}")
    
    def load_step_report(self, agent_folder, step_num):
        """Load a step report from file and register as shortcode"""
        report_name = f"דוח שלב {step_num}.md"
        report_path = agent_folder / report_name
        
        if report_path.exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.register_step_report(step_num, content)
                return content
            except Exception as e:
                print(f"[Shortcode] Error loading step {step_num} report: {e}")
        
        return None
    
    def get_page_info(self):
        """Get page info from page_info.json"""
        if not self.page_folder:
            return {}
        
        page_info_path = BASE_DIR / self.page_folder / "page_info.json"
        if page_info_path.exists():
            try:
                with open(page_info_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Shortcode] Error loading page_info: {e}")
        
        return {}
    
    def get_shortcode_value(self, shortcode_name):
        """Get the value for a specific shortcode"""
        # 1. Check step reports first
        if shortcode_name in self.step_reports:
            return self.step_reports[shortcode_name]
        
        # 2. Check custom sources
        if shortcode_name in self.custom_sources:
            return self.custom_sources[shortcode_name]
        
        # 3. Check context (dynamically set values)
        if shortcode_name in self.context:
            return self.context[shortcode_name]
        
        # 3.5 Check for step-specific prompt file shortcodes (STEP1_PROMPT_FILE, etc.)
        import re
        step_prompt_match = re.match(r'STEP(\d+)_PROMPT_FILE', shortcode_name)
        if step_prompt_match and self.agent:
            step_num = int(step_prompt_match.group(1))
            step_key = f"step{step_num}"
            step_data = self.agent.get(step_key, {})
            
            # Also check steps array (new format)
            steps = self.agent.get("steps", [])
            for s in steps:
                if s.get("order") == step_num or s.get("id") == step_key:
                    step_data = s
                    break
            
            prompt_file = step_data.get("prompt_file") or step_data.get("agent", "")
            if prompt_file and not prompt_file.endswith(".md"):
                prompt_file += ".md"
            return str(BASE_DIR / prompt_file) if prompt_file else ""
        
        # 4. Built-in shortcodes
        page_info = self.get_page_info()
        fetched_kw = page_info.get("fetched_keywords", {})
        
        if shortcode_name == "PAGE_KEYWORD":
            return page_info.get("keyword", "")
        
        elif shortcode_name == "PAGE_URL":
            return page_info.get("url", "")
        
        elif shortcode_name == "PAGE_HTML":
            if self.page_path:
                try:
                    with open(BASE_DIR / self.page_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except:
                    pass
            return ""
        
        elif shortcode_name == "PAGE_HTML_PATH" or shortcode_name == "PAGE_PATH":
            if self.page_path:
                return str(BASE_DIR / self.page_path)
            return ""
        
        # Handle STEPx_REPORT_NAME shortcodes (just the file name, e.g., "דוח ניתוח.md")
        step_report_name_match = re.match(r'STEP(\d+)_REPORT_NAME', shortcode_name)
        if step_report_name_match and self.agent:
            step_num = int(step_report_name_match.group(1))
            step_key = f"step{step_num}"
            step_data = None
            
            # Check steps array (new format)
            steps = self.agent.get("steps", [])
            for s in steps:
                if s.get("order") == step_num or s.get("id") == step_key:
                    step_data = s
                    break
            
            # Fallback to old format
            if not step_data:
                step_data = self.agent.get(step_key, {})
            
            output = step_data.get("output", {}) if step_data else {}
            report_name = output.get("path") if isinstance(output, dict) else None
            if not report_name:
                report_name = step_data.get("output_name", f"דוח שלב {step_num}.md") if step_data else f"דוח שלב {step_num}.md"
            
            return report_name
        
        # Handle STEPx_REPORT_PATH shortcodes (path to previous step reports)
        step_report_path_match = re.match(r'STEP(\d+)_REPORT_PATH', shortcode_name)
        if step_report_path_match and self.agent and self.page_folder:
            step_num = int(step_report_path_match.group(1))
            agent_folder = self.agent.get("folder_name") or self.agent.get("name") or self.agent.get("id", "agent")
            
            # Get the report name from agent config
            step_key = f"step{step_num}"
            step_data = None
            
            # Check steps array (new format)
            steps = self.agent.get("steps", [])
            for s in steps:
                if s.get("order") == step_num or s.get("id") == step_key:
                    step_data = s
                    break
            
            # Fallback to old format
            if not step_data:
                step_data = self.agent.get(step_key, {})
            
            output = step_data.get("output", {}) if step_data else {}
            report_name = output.get("path") if isinstance(output, dict) else None
            if not report_name:
                report_name = step_data.get("output_name", f"דוח שלב {step_num}.md") if step_data else f"דוח שלב {step_num}.md"
            
            report_path = BASE_DIR / self.page_folder / agent_folder / report_name
            return str(report_path)
        
        elif shortcode_name == "TODAY_DATE":
            return datetime.now().strftime("%Y-%m-%d")
        
        elif shortcode_name == "CURRENT_MONTH":
            # Return Hebrew month name with year
            hebrew_months = {
                1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
                5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
                9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
            }
            now = datetime.now()
            month_name = hebrew_months.get(now.month, str(now.month))
            return f"{month_name} {now.year}"
        
        elif shortcode_name == "PAGE_WORD_COUNT":
            # Get word count from page info
            word_count = page_info.get("word_count", 0)
            return str(word_count) if word_count else "0"
        
        elif shortcode_name == "BOI_INTEREST_RATE":
            # Get Bank of Israel interest rate from global values in config
            global_values = config.get("global_values", {})
            boi_data = global_values.get("BOI_INTEREST_RATE", {})
            return boi_data.get("value", "לא הוגדר")
        
        # APPROVED_DOMAINS is now loaded from custom_data_sources (config.json)
        # No hardcoded handler needed - it's read from the file
        
        elif shortcode_name == "KEYWORDS_AUTOCOMPLETE":
            kw_list = fetched_kw.get("final_keywords", [])
            if kw_list:
                return f"""
## מילות מפתח נלוות לשילוב

**רשימה:** {', '.join(kw_list)}

### רשימת שימור:
המילים הבאות חייבות להופיע בתוכן הסופי: {', '.join(kw_list)}
"""
            return ""
        
        elif shortcode_name == "KEYWORDS_RELATED":
            related = fetched_kw.get("related_searches", [])
            if related:
                return f"""
## חיפושים קשורים

**רשימה:** {', '.join(related)}
"""
            return ""
        
        elif shortcode_name == "SERP_ORGANIC":
            competitor_data = fetched_kw.get("competitor_data", []) or fetched_kw.get("organic_results", [])
            our_url = page_info.get("url", "")
            our_domain = our_url.replace('https://', '').replace('http://', '').split('/')[0] if our_url else ""
            
            # Filter out our own results
            if our_domain and competitor_data:
                competitor_data = [c for c in competitor_data if our_domain not in c.get('url', '')]
            
            if competitor_data:
                comp_lines = []
                for c in competitor_data:
                    if c.get('description'):
                        comp_lines.append(f"- **{c.get('title', '')}** ({c.get('url', 'אין URL')}): {c.get('description', '')}")
                
                if comp_lines:
                    return f"""
## מידע ממתחרים מדורגים

להלן תיאורים מאתרים המדורגים גבוה עבור מילת המפתח:

{chr(10).join(comp_lines)}
"""
            return ""
        
        elif shortcode_name == "SERP_AI_OVERVIEW":
            ai_results = fetched_kw.get("ai_mode_results", [])
            ai_rank = fetched_kw.get("ai_rank_position")
            our_url = page_info.get("url", "")
            our_domain = our_url.replace('https://', '').replace('http://', '').split('/')[0] if our_url else ""
            
            # Filter out our own results (keep summary)
            if our_domain and ai_results:
                ai_results = [a for a in ai_results if a.get('is_summary') or our_domain not in a.get('url', '')]
            
            if ai_results:
                ai_lines = []
                for ai_r in ai_results:
                    if ai_r.get('is_summary'):
                        ai_lines.insert(0, f"**סיכום AI:** {ai_r.get('description', '')}")
                    elif ai_r.get('description'):
                        ai_lines.append(f"- {ai_r.get('title', '')} ({ai_r.get('url', '')}): {ai_r.get('description', '')}")
                
                if ai_lines:
                    status = f"**סטטוס:** אנחנו מופיעים במיקום {ai_rank}" if ai_rank else "**סטטוס:** לא מופיעים ב-AI Overview"
                    return f"""
## תוצאות AI Overview של גוגל

הנה מה שגוגל AI מציג לגולשים שמחפשים את מילת המפתח:

{chr(10).join(ai_lines)}

{status}
"""
            return ""
        
        elif shortcode_name == "OUR_SERP_RANK":
            rank = fetched_kw.get("rank_position")
            ai_rank = fetched_kw.get("ai_rank_position")
            result = ""
            if rank:
                result += f"**דירוג אורגני:** מיקום {rank}\n"
            if ai_rank:
                result += f"**דירוג AI Overview:** מיקום {ai_rank}\n"
            return result
        
        elif shortcode_name == "ALL_PREVIOUS_REPORTS":
            all_reports = []
            for key, value in sorted(self.step_reports.items()):
                if key.startswith("STEP") and key.endswith("_REPORT"):
                    all_reports.append(f"## {key}\n\n{value}")
            return "\n\n---\n\n".join(all_reports)
        
        return ""
    
    def process(self, template):
        """Replace all shortcodes in a template with their values"""
        result = template
        
        # Find all {{SHORTCODE}} patterns
        import re
        pattern = r'\{\{([A-Z0-9_]+)\}\}'
        
        for match in re.finditer(pattern, template):
            shortcode_name = match.group(1)
            value = self.get_shortcode_value(shortcode_name)
            result = result.replace(f"{{{{{shortcode_name}}}}}", value)
        
        return result
    
    def get_available_shortcodes(self):
        """Get list of all available shortcodes with descriptions"""
        shortcodes = []
        
        # Per-page shortcodes (dynamic based on page)
        for name, desc in self.PAGE_SHORTCODES.items():
            shortcodes.append({
                "name": name,
                "type": "per_page",
                "description": desc,
                "syntax": f"{{{{{name}}}}}",
                "category": "page"
            })
        
        # Global shortcodes (static)
        for name, desc in self.GLOBAL_SHORTCODES.items():
            shortcodes.append({
                "name": name,
                "type": "global",
                "description": desc,
                "syntax": f"{{{{{name}}}}}",
                "category": "global"
            })
        
        # Step-specific shortcodes
        for name, desc in self.STEP_SHORTCODES.items():
            shortcodes.append({
                "name": name,
                "type": "step_context",
                "description": desc,
                "syntax": f"{{{{{name}}}}}",
                "note": "ערך משתנה לפי השלב הנוכחי",
                "category": "step"
            })
        
        # Step reports
        for name in self.step_reports:
            shortcodes.append({
                "name": name,
                "type": "step_report",
                "description": f"דוח מ{name.replace('_REPORT', '').replace('STEP', 'שלב ')}",
                "syntax": f"{{{{{name}}}}}",
                "category": "step"
            })
        
        # Custom data sources (global files)
        for source in config.get("custom_data_sources", []):
            shortcodes.append({
                "name": source["shortcode"],
                "type": "custom",
                "description": source.get("description", ""),
                "syntax": f"{{{{{source['shortcode']}}}}}",
                "path": source.get("path", ""),
                "category": "custom"
            })
        
        return shortcodes

# ============ Page History Logging ============

def log_agent_run(page_path, agent, mode, result):
    """Log an agent run to the page's history files"""
    if mode == "test":
        print(f"[History] Skipping log for test mode run on {page_path}")
        return
    
    page_folder = BASE_DIR / get_page_folder(page_path)
    history_json_path = page_folder / "history.json"
    history_md_path = page_folder / "history.md"
    
    # Load or create history.json
    history = {
        "page_path": str(page_path),
        "keyword": "",
        "created": datetime.now().isoformat(),
        "runs": []
    }
    
    if history_json_path.exists():
        try:
            with open(history_json_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass
    
    # Get keyword from page_info
    page_info_path = page_folder / "page_info.json"
    if page_info_path.exists():
        try:
            with open(page_info_path, 'r', encoding='utf-8') as f:
                page_info = json.load(f)
                history["keyword"] = page_info.get("keyword", "")
        except:
            pass
    
    # Create run entry
    import uuid
    run_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "agent": {
            "id": agent.get("id", "unknown"),
            "name": agent.get("name", "Unknown"),
            "mode": mode
        },
        "model": agent.get("model", {}).get("name", "claude-sonnet-4"),
        "steps_completed": result.get("steps_completed", []),
        "duration_seconds": result.get("duration_seconds", 0),
        "wordpress_update": result.get("wordpress_update", {"performed": False}),
        "changes_summary": result.get("changes_summary", {})
    }
    
    history["runs"].append(run_entry)
    
    # Save history.json
    with open(history_json_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    # Update history.md
    md_entry = f"""
## {datetime.now().strftime('%Y-%m-%d %H:%M')} - {agent.get('name', 'Unknown')} (פעיל)
**מודל:** {run_entry['model']}
**משך:** {run_entry['duration_seconds']} שניות

### שינויים שבוצעו:
"""
    
    if run_entry["wordpress_update"].get("performed"):
        wp = run_entry["wordpress_update"]
        md_entry += f"- ✅ עודכן ב-WordPress (Post ID: {wp.get('post_id', 'N/A')})\n"
        md_entry += f"- 📝 שדות: {', '.join(wp.get('fields_updated', []))}\n"
    else:
        md_entry += "- ⏸️ לא עודכן ב-WordPress\n"
    
    md_entry += "\n---\n"
    
    # Append to history.md
    md_header = f"# היסטוריית שינויים - {history['keyword']}\n\n"
    
    if history_md_path.exists():
        with open(history_md_path, 'r', encoding='utf-8') as f:
            existing_md = f.read()
        # Insert new entry after header
        if existing_md.startswith("# היסטוריית"):
            lines = existing_md.split('\n', 2)
            if len(lines) > 2:
                existing_md = lines[0] + '\n' + lines[1] + '\n' + md_entry + lines[2]
            else:
                existing_md = md_header + md_entry
        else:
            existing_md = md_header + md_entry + existing_md
    else:
        existing_md = md_header + md_entry
    
    with open(history_md_path, 'w', encoding='utf-8') as f:
        f.write(existing_md)
    
    print(f"[History] Logged run for {page_path}")

# ============ Helper Functions ============

def get_page_folder(page_path):
    """Get the folder for a page based on the new structure"""
    # page_path is like "דפים לשינוי/הלוואה בצ_יקים/הלוואה בצ_יקים.html"
    # Returns the folder path "דפים לשינוי/הלוואה בצ_יקים"
    path = Path(page_path)
    return path.parent

def get_agent_folder(page_path, agent_id):
    """Get the agent folder for a page (e.g., דפים לשינוי/הלוואה/שיווק אטומי)"""
    page_folder = get_page_folder(page_path)
    
    # Try new agent system first
    agent = get_agent_by_id(agent_id)
    if agent:
        agent_folder_name = agent.get("folder_name", agent.get("name", agent_id))
    else:
        # Fallback to legacy config (for backward compatibility)
        legacy_agents = config.get("agents", {})
        if isinstance(legacy_agents, dict) and agent_id in legacy_agents:
            agent = legacy_agents[agent_id]
            agent_folder_name = agent.get("folder_name", agent.get("name", agent_id))
        else:
            agent_folder_name = agent_id
    
    return BASE_DIR / page_folder / agent_folder_name

def get_wordpress_site(url_or_path):
    """Determine which WordPress site to use based on URL or file path - DYNAMIC"""
    path_lower = (url_or_path or "").lower().replace("\\", "/")
    
    # Get editable pages config to match path to site
    editable = config.get("paths", {}).get("editable_pages", {})
    wp_sites = config.get("wordpress", {}).get("sites", {})
    
    # Try to match path against configured folders
    for site_id, folder in editable.items():
        folder_str = folder if isinstance(folder, str) else folder.get("folder", "")
        folder_normalized = folder_str.lower().replace("\\", "/")
        
        if folder_normalized and folder_normalized in path_lower:
            if site_id in wp_sites:
                return site_id, wp_sites[site_id]
    
    # Also check by site_id name in path
    for site_id in wp_sites.keys():
        if f"/{site_id}/" in path_lower or path_lower.endswith(f"/{site_id}"):
            return site_id, wp_sites[site_id]
    
    # Fallback to first site
    first_site_id = list(wp_sites.keys())[0] if wp_sites else "main"
    return first_site_id, wp_sites.get(first_site_id, {})

def get_page_site(page_path):
    """Get the site ID from a page path - for agent site validation"""
    editable = config.get("paths", {}).get("editable_pages", {})
    path_norm = (page_path or "").lower().replace("\\", "/")
    
    for site_id, folder in editable.items():
        folder_str = folder if isinstance(folder, str) else folder.get("folder", "")
        if folder_str and folder_str.lower().replace("\\", "/") in path_norm:
            return site_id
    
    # Default to first site
    return list(editable.keys())[0] if editable else "main"

def is_agent_allowed_for_site(agent, page_site):
    """Check if agent is allowed to run on a specific site"""
    sites = agent.get('sites', []) if agent else []
    # Empty sites list = all sites allowed
    return not sites or page_site in sites

def read_csv_pages():
    """Read pages from CSV file"""
    csv_path = BASE_DIR / config["paths"]["csv_file"]
    pages = []
    
    if not csv_path.exists():
        return pages
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) >= 4:
                pages.append({
                    "name": row[0],
                    "keywords": row[1],
                    "url": row[2],
                    "post_id": row[3] if len(row) > 3 else ""
                })
    
    return pages

def write_csv_page(name, keywords, url, post_id):
    """Add or update a page in CSV"""
    csv_path = BASE_DIR / config["paths"]["csv_file"]
    pages = read_csv_pages()
    
    # Check if URL already exists
    found = False
    for page in pages:
        if page["url"] == url:
            page["name"] = name
            page["keywords"] = keywords
            page["post_id"] = post_id
            found = True
            break
    
    if not found:
        pages.append({
            "name": name,
            "keywords": keywords,
            "url": url,
            "post_id": post_id
        })
    
    # Write back
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        for page in pages:
            writer.writerow([page["name"], page["keywords"], page["url"], page["post_id"]])

def get_html_files():
    """Get all HTML files from editable directories (new folder structure: page folder -> HTML)"""
    files = []
    csv_pages = {p["name"]: p for p in read_csv_pages()}
    
    # Support both dict (new multi-site) and array (legacy) formats
    editable = config["paths"]["editable_pages"]
    if isinstance(editable, dict):
        folders = [(site_id, path) for site_id, path in editable.items()]
    else:
        # Legacy array format - assume main site
        folders = [("main", path) for path in editable]
    
    for site_id, folder in folders:
        folder_path = BASE_DIR / folder
        if folder_path.exists():
            # Scan each subfolder (page folder)
            for page_folder in folder_path.iterdir():
                if page_folder.is_dir():
                    # Look for HTML files inside the page folder
                    for file in page_folder.glob("*.html"):
                        # Skip agent output files
                        if "מתוקנת" in file.name or "סופית" in file.name:
                            continue
                        name = file.stem
                        page_info = csv_pages.get(name, {})
                        files.append({
                            "name": name,
                            "path": str(file.relative_to(BASE_DIR)),
                            "folder": folder,
                            "site": site_id,
                            "post_id": page_info.get("post_id", ""),
                            "url": page_info.get("url", ""),
                            "keywords": page_info.get("keywords", ""),
                            "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                        })
    
    return files

def get_agent_files():
    """Get all agent files from prompts folder"""
    agents_folder = BASE_DIR / config["paths"]["agents"]
    agents = []
    
    if agents_folder.exists():
        for file in agents_folder.glob("*.md"):
            agents.append({
                "name": file.stem,
                "path": str(file.relative_to(BASE_DIR))
            })
        # Also include files without extension
        for file in agents_folder.iterdir():
            if file.is_file() and not file.suffix:
                agents.append({
                    "name": file.name,
                    "path": str(file.relative_to(BASE_DIR))
                })
    
    return agents

def create_archive_folder(page_name):
    """Create dated archive folder for a page"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_name = page_name.replace(" ", "-")
    folder_name = f"{date_str}_{safe_name}"
    
    archive_path = BASE_DIR / config["paths"]["archive"] / folder_name
    archive_path.mkdir(parents=True, exist_ok=True)
    
    return archive_path

# ============ API Routes - Pages ============

@app.route('/api/pages', methods=['GET'])
def get_pages():
    """Get all editable pages"""
    try:
        files = get_html_files()
        return jsonify({"success": True, "pages": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/<path:page_path>', methods=['GET'])
def get_page_content(page_path):
    """Get content of a specific page"""
    try:
        file_path = BASE_DIR / page_path
        if not file_path.exists():
            return jsonify({"success": False, "error": "File not found"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/preview/<path:page_path>')
def preview_page(page_path):
    """Serve HTML page for preview"""
    try:
        from urllib.parse import unquote
        decoded_path = unquote(page_path)
        file_path = BASE_DIR / decoded_path
        if file_path.exists():
            return send_file(file_path, mimetype='text/html')
        return f"File not found: {decoded_path}", 404
    except Exception as e:
        return str(e), 500

# ============ API Routes - Agents ============

# ============ API Routes - Agent Management (New System) ============

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all configured agents - merges config.json and agents/ folder"""
    try:
        # Start with agents from config.json (for backward compatibility)
        agents = dict(config.get("agents", {}))
        
        # Then overlay with agents from folder (new system)
        folder_agents = load_agents_from_folder()
        for agent_id, agent in folder_agents.items():
            # Folder agents take precedence if they have more fields
            if agent_id not in agents or len(agent) > len(agents.get(agent_id, {})):
                agents[agent_id] = agent
        
        return jsonify({
            "success": True, 
            "agents": agents,
            "agent_files": get_agent_files()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a specific agent by ID"""
    try:
        agent = get_agent_by_id(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        return jsonify({"success": True, "agent": agent})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents', methods=['POST'])
@app.route('/api/agents/create', methods=['POST'])
def create_agent():
    """Create a new agent configuration"""
    try:
        data = request.json
        
        # Support both old format (id + config) and new format (full agent)
        if "config" in data:
            # Old format
            agent_id = data.get("id")
            agent_config = data.get("config")
            agent_config["id"] = agent_id
        else:
            # New format - full agent object
            agent_config = data
            agent_id = agent_config.get("id")
        
        if not agent_id:
            return jsonify({"success": False, "error": "Missing agent id"}), 400
        
        # Set created timestamp
        agent_config["created"] = datetime.now().isoformat()
        agent_config["updated"] = datetime.now().isoformat()
        
        # Ensure version
        if "version" not in agent_config:
            agent_config["version"] = "1.0"
        
        # Save to agents folder
        save_agent(agent_config)
        
        return jsonify({"success": True, "agent": agent_config})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update an existing agent configuration"""
    try:
        data = request.json
        
        # Check if agent exists
        existing = get_agent_by_id(agent_id)
        if not existing:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        # Preserve original created date
        data["id"] = agent_id
        data["created"] = existing.get("created", datetime.now().isoformat())
        
        # Save updated agent
        save_agent(data)
        
        return jsonify({"success": True, "agent": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent configuration from both folder and config.json"""
    try:
        if not get_agent_by_id(agent_id):
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        # Delete from agents folder
        deleted_from_folder = delete_agent_file(agent_id)
        
        # Also delete from config.json if exists there
        deleted_from_config = False
        global config
        if "agents" in config and agent_id in config["agents"]:
            del config["agents"][agent_id]
            # Save updated config
            config_path = BASE_DIR / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            deleted_from_config = True
        
        if deleted_from_folder or deleted_from_config:
            return jsonify({"success": True, "deleted_from_folder": deleted_from_folder, "deleted_from_config": deleted_from_config})
        else:
            return jsonify({"success": False, "error": "Agent not found in any location"}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>/duplicate', methods=['POST'])
def duplicate_agent_full(agent_id):
    """Duplicate an agent with its prompt folder - creates a full independent copy"""
    try:
        data = request.json or {}
        new_id = data.get('new_id')
        new_name = data.get('new_name')
        
        if not new_id or not new_name:
            return jsonify({"success": False, "error": "חסר new_id או new_name"}), 400
        
        # Check if agent exists
        original = get_agent_by_id(agent_id)
        if not original:
            return jsonify({"success": False, "error": f"סוכן {agent_id} לא נמצא"}), 404
        
        # Check if new ID already exists
        if get_agent_by_id(new_id):
            return jsonify({"success": False, "error": f"סוכן עם מזהה {new_id} כבר קיים"}), 400
        
        # Copy prompt folder if exists
        original_folder_name = original.get("folder_name") or original.get("name") or agent_id
        prompts_base = BASE_DIR / config.get("paths", {}).get("agents", "פרומטים")
        src_folder = prompts_base / original_folder_name
        dst_folder = prompts_base / new_name
        
        if src_folder.exists():
            import shutil
            shutil.copytree(src_folder, dst_folder)
            print(f"[Duplicate] Copied prompt folder: {src_folder} -> {dst_folder}")
        else:
            print(f"[Duplicate] Source folder not found: {src_folder}")
        
        # Create new agent config
        import copy
        new_agent = copy.deepcopy(original)
        new_agent["id"] = new_id
        new_agent["name"] = new_name
        new_agent["folder_name"] = new_name
        new_agent["created"] = datetime.now().isoformat()
        
        # Update prompt file paths in steps
        if new_agent.get("steps"):
            for step in new_agent["steps"]:
                if step.get("prompt_file"):
                    step["prompt_file"] = step["prompt_file"].replace(
                        original_folder_name, new_name
                    )
        
        # Update old format step paths if they exist
        for i in range(1, 10):
            step_key = f"step{i}"
            if step_key in new_agent and new_agent[step_key].get("agent"):
                new_agent[step_key]["agent"] = new_agent[step_key]["agent"].replace(
                    original_folder_name, new_name
                )
        
        # Save new agent
        save_agent(new_agent)
        
        return jsonify({
            "success": True, 
            "agent": new_agent,
            "message": f"סוכן {new_name} נוצר בהצלחה עם כל הקבצים"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Prompt Files ============

@app.route('/api/prompt-file', methods=['GET'])
def get_prompt_file():
    """Load content of a prompt file"""
    try:
        path = request.args.get('path')
        if not path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        # Build list of paths to try
        paths_to_try = []
        
        # 1. Original path as-is
        paths_to_try.append(BASE_DIR / path)
        
        # 2. If path ends with .md, try without extension
        if path.endswith('.md'):
            paths_to_try.append(BASE_DIR / path[:-3])
        
        # 3. If path doesn't end with .md, try with .md
        if not path.endswith('.md'):
            paths_to_try.append(BASE_DIR / f"{path}.md")
        
        # 4. Try with .txt
        paths_to_try.append(BASE_DIR / f"{path}.txt")
        
        # Debug logging
        print(f"[PromptFile] Looking for: {path}")
        for p in paths_to_try:
            print(f"[PromptFile]   Trying: {p} - exists: {p.exists()}")
        
        # Find first existing path
        full_path = None
        for p in paths_to_try:
            if p.exists() and p.is_file():
                full_path = p
                print(f"[PromptFile] Found: {full_path}")
                break
        
        if not full_path:
            tried_paths = [str(p) for p in paths_to_try]
            return jsonify({"success": False, "error": f"קובץ לא נמצא: {path}", "tried": tried_paths}), 404
        
        # Security: make sure path is within BASE_DIR
        try:
            full_path.resolve().relative_to(BASE_DIR.resolve())
        except ValueError:
            return jsonify({"success": False, "error": "נתיב לא חוקי"}), 403
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "content": content,
            "path": str(full_path.relative_to(BASE_DIR))
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/prompt-file', methods=['POST'])
def save_prompt_file():
    """Save content to a prompt file"""
    try:
        data = request.json
        path = data.get('path')
        content = data.get('content', '')
        
        if not path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        # Security check - path should be within project
        full_path = BASE_DIR / path
        
        # Security: make sure path is within BASE_DIR
        try:
            full_path.resolve().relative_to(BASE_DIR.resolve())
        except ValueError:
            return jsonify({"success": False, "error": "נתיב לא חוקי"}), 403
        
        # Create directory if it doesn't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup original file if it exists - save to backup/ subfolder with date
        if full_path.exists():
            import shutil
            # Create backup folder in the same directory as the prompt file
            backup_folder = full_path.parent / "backup"
            backup_folder.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with date: שלב 1_2026-01-03.backup.md
            date_str = datetime.now().strftime("%Y-%m-%d")
            backup_filename = f"{full_path.stem}_{date_str}.backup{full_path.suffix}"
            backup_path = backup_folder / backup_filename
            
            shutil.copy(full_path, backup_path)
            print(f"[PromptFile] Backup created: {backup_path}")
        
        # Save the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[PromptFile] Saved: {path}")
        
        return jsonify({
            "success": True,
            "message": "הקובץ נשמר בהצלחה",
            "path": str(full_path.relative_to(BASE_DIR))
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Shortcodes ============

@app.route('/api/shortcodes', methods=['GET'])
def get_shortcodes():
    """Get list of all available shortcodes"""
    try:
        page_path = request.args.get('page_path')
        engine = ShortcodeEngine(page_path)
        shortcodes = engine.get_available_shortcodes()
        
        return jsonify({
            "success": True,
            "shortcodes": shortcodes
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/shortcodes/preview', methods=['POST'])
def preview_shortcode():
    """Preview shortcode replacement in a template"""
    try:
        data = request.json
        page_path = data.get('page_path')
        template = data.get('template', '')
        agent_id = data.get('agent_id')
        step_num = data.get('step_num')
        
        # Get agent if specified
        agent = get_agent_unified(agent_id) if agent_id else None
        
        engine = ShortcodeEngine(page_path, agent, step_num)
        processed = engine.process(template)
        
        return jsonify({
            "success": True,
            "original": template,
            "processed": processed
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>/shortcodes', methods=['GET'])
def get_agent_shortcodes(agent_id):
    """Get all shortcodes available for a specific agent, including step-specific ones"""
    try:
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        result = {
            "global": [],
            "step_context": [],
            "step_reports": [],
            "custom": []
        }
        
        # Global shortcodes
        for name, desc in ShortcodeEngine.BUILTIN_SHORTCODES.items():
            result["global"].append({
                "name": name,
                "description": desc,
                "syntax": f"{{{{{name}}}}}"
            })
        
        # Step-context shortcodes (change per step)
        for name, desc in ShortcodeEngine.STEP_SHORTCODES.items():
            result["step_context"].append({
                "name": name,
                "description": desc,
                "syntax": f"{{{{{name}}}}}",
                "note": "ערך משתנה לפי השלב הנוכחי"
            })
        
        # Get step-specific report shortcodes
        steps = agent.get("steps", [])
        if not steps:
            # Old format: stepX
            for i in range(1, 11):
                step = agent.get(f"step{i}")
                if step:
                    output = step.get("output", {})
                    shortcode_name = output.get("shortcode_name", f"STEP{i}_REPORT")
                    result["step_reports"].append({
                        "name": shortcode_name,
                        "step": i,
                        "description": f"דוח משלב {i}: {step.get('name', '')}",
                        "syntax": f"{{{{{shortcode_name}}}}}",
                        "prompt_file": step.get("agent", step.get("prompt_file", ""))
                    })
        else:
            for step in steps:
                step_num = step.get("order", 0)
                output = step.get("output", {})
                shortcode_name = output.get("shortcode_name", f"STEP{step_num}_REPORT")
                result["step_reports"].append({
                    "name": shortcode_name,
                    "step": step_num,
                    "description": f"דוח משלב {step_num}: {step.get('name', '')}",
                    "syntax": f"{{{{{shortcode_name}}}}}",
                    "prompt_file": step.get("prompt_file", step.get("agent", ""))
                })
        
        # Custom data sources
        for source in config.get("custom_data_sources", []):
            result["custom"].append({
                "name": source["shortcode"],
                "description": source.get("description", ""),
                "syntax": f"{{{{{source['shortcode']}}}}}",
                "path": source.get("path", "")
            })
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "shortcodes": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Page History ============

@app.route('/api/pages/<path:page_path>/history', methods=['GET'])
def get_page_history(page_path):
    """Get history for a specific page"""
    try:
        page_folder = BASE_DIR / get_page_folder(page_path)
        history_json_path = page_folder / "history.json"
        
        if history_json_path.exists():
            with open(history_json_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return jsonify({"success": True, "history": history})
        else:
            return jsonify({
                "success": True, 
                "history": {
                    "page_path": page_path,
                    "runs": []
                }
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Custom Data Sources ============

@app.route('/api/data-sources', methods=['GET'])
def get_data_sources():
    """Get list of custom data sources"""
    try:
        sources = config.get("custom_data_sources", [])
        return jsonify({"success": True, "sources": sources})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/data-sources', methods=['POST'])
def add_data_source():
    """Add a new custom data source"""
    try:
        data = request.json
        source_id = data.get("id")
        
        if not source_id:
            return jsonify({"success": False, "error": "Missing source id"}), 400
        
        # Ensure custom_data_sources exists
        if "custom_data_sources" not in config:
            config["custom_data_sources"] = []
        
        # Check if source already exists
        for i, source in enumerate(config["custom_data_sources"]):
            if source["id"] == source_id:
                config["custom_data_sources"][i] = data
                save_config(config)
                return jsonify({"success": True, "source": data})
        
        # Add new source
        config["custom_data_sources"].append(data)
        save_config(config)
        
        return jsonify({"success": True, "source": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/data-sources/<source_id>', methods=['DELETE'])
def delete_data_source(source_id):
    """Delete a custom data source"""
    try:
        if "custom_data_sources" not in config:
            return jsonify({"success": False, "error": "Source not found"}), 404
        
        config["custom_data_sources"] = [
            s for s in config["custom_data_sources"] if s["id"] != source_id
        ]
        save_config(config)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/data-sources/<source_id>', methods=['PUT'])
def update_data_source(source_id):
    """Update a custom data source"""
    try:
        data = request.json
        if "custom_data_sources" not in config:
            return jsonify({"success": False, "error": "Source not found"}), 404
        
        for i, source in enumerate(config["custom_data_sources"]):
            if source["id"] == source_id:
                # Update fields
                if "name" in data:
                    config["custom_data_sources"][i]["name"] = data["name"]
                if "shortcode" in data:
                    config["custom_data_sources"][i]["shortcode"] = data["shortcode"]
                if "path" in data:
                    config["custom_data_sources"][i]["path"] = data["path"]
                if "description" in data:
                    config["custom_data_sources"][i]["description"] = data["description"]
                
                save_config(config)
                return jsonify({"success": True, "source": config["custom_data_sources"][i]})
        
        return jsonify({"success": False, "error": "Source not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Agent Execution (New System) ============

@app.route('/api/agents/<agent_id>/run', methods=['POST'])
def run_agent_new(agent_id):
    """Run an agent on a page using the new system"""
    try:
        data = request.json
        page_path = data.get('page_path')
        mode = data.get('mode', 'active')  # 'active' or 'test'
        model_override = data.get('model')  # Optional model override
        step_from = data.get('step_from', 1)  # Start from step
        step_to = data.get('step_to')  # End at step (None = all)
        
        if not page_path:
            return jsonify({"success": False, "error": "Missing page_path"}), 400
        
        agent = get_agent_by_id(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        # Use model override or agent default
        model = model_override or agent.get("model", {}).get("name", "claude-sonnet-4")
        
        # Get model flag from config
        model_config = config.get("claude_code", {}).get("models", {})
        model_flag = model_config.get(model, {}).get("flag", "sonnet")
        
        return jsonify({
            "success": True,
            "message": f"Agent {agent_id} execution started",
            "mode": mode,
            "model": model,
            "model_flag": model_flag,
            "agent": agent,
            "page_path": page_path,
            "steps": len(agent.get("steps", [])),
            "step_range": {"from": step_from, "to": step_to}
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>/test', methods=['POST'])
def test_agent(agent_id):
    """Run an agent in test mode (no logging, no WordPress update)"""
    data = request.json or {}
    data['mode'] = 'test'
    
    # Call the run endpoint with test mode
    with app.test_request_context(json=data):
        return run_agent_new(agent_id)

# ============ API Routes - WordPress Categories ============

def ensure_jwt_token(site_id):
    """Ensure we have a valid JWT token for the site, getting a new one if needed"""
    global jwt_tokens
    
    token = jwt_tokens.get(site_id)
    if token:
        return token
    
    site = config["wordpress"]["sites"].get(site_id)
    if not site:
        return None
    
    password = site.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD")
    username = site.get("username") or os.getenv(f"WP_{site_id.upper()}_USERNAME")
    
    if not username or not password:
        return None
    
    try:
        token_url = site["site_url"] + site["token_endpoint"]
        response = requests.post(token_url, json={
            "username": username,
            "password": password
        }, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            jwt_tokens[site_id] = token_data.get("token")
            return jwt_tokens[site_id]
    except Exception as e:
        print(f"[JWT] Error getting token for {site_id}: {e}")
    
    return None

@app.route('/api/wordpress/categories', methods=['GET'])
def get_wordpress_categories():
    """Get WordPress categories"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        site = request.args.get('site', 'main')
        site_config = config["wordpress"]["sites"].get(site)
        
        if not site_config:
            return jsonify({"success": False, "error": "Site not found"}), 404
        
        # Get JWT token
        token = ensure_jwt_token(site)
        if not token:
            return jsonify({"success": False, "error": "Authentication failed - check credentials"}), 401
        
        # Fetch categories
        url = f"{site_config['site_url']}{site_config['api_base']}/categories?per_page=100"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            categories = response.json()
            return jsonify({
                "success": True,
                "categories": [{"id": c["id"], "name": c["name"], "slug": c["slug"]} for c in categories]
            })
        else:
            return jsonify({"success": False, "error": f"Failed to fetch categories: {response.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wordpress/categories', methods=['POST'])
def create_wordpress_category():
    """Create a new WordPress category"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        data = request.json
        site = data.get('site', 'main')
        name = data.get('name')
        
        if not name:
            return jsonify({"success": False, "error": "Missing category name"}), 400
        
        site_config = config["wordpress"]["sites"].get(site)
        if not site_config:
            return jsonify({"success": False, "error": "Site not found"}), 404
        
        # Get JWT token
        token = ensure_jwt_token(site)
        if not token:
            return jsonify({"success": False, "error": "Authentication failed - check credentials"}), 401
        
        # Create category
        url = f"{site_config['site_url']}{site_config['api_base']}/categories"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={"name": name})
        if response.status_code in [200, 201]:
            category = response.json()
            return jsonify({
                "success": True,
                "category": {"id": category["id"], "name": category["name"], "slug": category["slug"]}
            })
        else:
            return jsonify({"success": False, "error": f"Failed to create category: {response.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wordpress/create-post', methods=['POST'])
def create_wordpress_post():
    """Create a new WordPress post (for build agents)"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        data = request.json
        site = data.get('site', 'main')
        title = data.get('title')
        content = data.get('content')
        category_id = data.get('category_id')
        status = data.get('status', 'draft')  # 'draft', 'publish', 'pending'
        slug = data.get('slug')
        excerpt = data.get('excerpt', '')
        
        if not title or not content:
            return jsonify({"success": False, "error": "Missing title or content"}), 400
        
        site_config = config["wordpress"]["sites"].get(site)
        if not site_config:
            return jsonify({"success": False, "error": "Site not found"}), 404
        
        # Get JWT token
        token = ensure_jwt_token(site)
        if not token:
            return jsonify({"success": False, "error": "Authentication failed - check credentials"}), 401
        
        # Create post
        url = f"{site_config['site_url']}{site_config['api_base']}/posts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        post_data = {
            "title": title,
            "content": content,
            "status": status,
            "excerpt": excerpt
        }
        
        if category_id:
            post_data["categories"] = [int(category_id)]
        
        if slug:
            post_data["slug"] = slug
        
        response = requests.post(url, headers=headers, json=post_data)
        
        if response.status_code in [200, 201]:
            post = response.json()
            return jsonify({
                "success": True,
                "post": {
                    "id": post["id"],
                    "title": post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"],
                    "slug": post["slug"],
                    "link": post["link"],
                    "status": post["status"]
                }
            })
        else:
            return jsonify({"success": False, "error": f"Failed to create post: {response.status_code} - {response.text}"}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pages/create-folder', methods=['POST'])
def create_page_folder():
    """Create a new page folder for a build agent"""
    try:
        data = request.json
        keyword = data.get('keyword')
        page_name = data.get('page_name') or keyword
        site_id = data.get('site', 'main')  # Default to main site
        
        if not keyword:
            return jsonify({"success": False, "error": "Missing keyword"}), 400
        
        # Get folder path - support both dict (new) and array (legacy)
        editable = config["paths"]["editable_pages"]
        if isinstance(editable, dict):
            editable_pages_path = editable.get(site_id, editable.get("main", "דפים לשינוי/main"))
        else:
            # Legacy array format
            editable_pages_path = editable[0] if editable else "דפים לשינוי"
        
        page_folder = BASE_DIR / editable_pages_path / page_name
        page_folder.mkdir(parents=True, exist_ok=True)
        
        # Create page_info.json
        page_info = {
            "keyword": keyword,
            "url": "",
            "post_id": "",
            "site": site_id,
            "created": datetime.now().isoformat(),
            "fetched_keywords": {}
        }
        
        page_info_path = page_folder / "page_info.json"
        with open(page_info_path, 'w', encoding='utf-8') as f:
            json.dump(page_info, f, ensure_ascii=False, indent=2)
        
        # Create empty HTML file placeholder
        html_path = page_folder / f"{page_name}.html"
        if not html_path.exists():
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- עמוד חדש: {page_name} -->\n")
        
        return jsonify({
            "success": True,
            "folder": str(page_folder),
            "site": site_id,
            "page_path": f"{editable_pages_path}/{page_name}/{page_name}.html"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Claude Models ============

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available Claude models"""
    try:
        models = config.get("claude_code", {}).get("models", {
            "claude-sonnet-4": {"name": "Claude Sonnet 4", "flag": "sonnet"},
            "claude-opus-4": {"name": "Claude Opus 4", "flag": "opus"}
        })
        
        return jsonify({
            "success": True,
            "models": [
                {"id": k, "name": v["name"], "flag": v["flag"]} 
                for k, v in models.items()
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Legacy Agent Routes ============

def generate_agent_template(name, agent_type):
    """Generate template for new agent files"""
    if agent_type == "two-step":
        return {
            "step1": f"""# סוכן דוח {name}

## 📋 הוראות הפעלה
1. תייג את הקובץ הזה
2. תייג את קובץ ה-HTML
3. ציין את מילת המפתח

⚠️ **חשוב:** הסוכן הזה לא משנה קבצים! רק יוצר דוח.

---

## הנחיות ניתוח
[הוסף את ההנחיות שלך כאן]

---

## פורמט הדוח
📝 דוח {name}

## ממצאים
...

## תיקונים נדרשים
...
""",
            "step2": f"""# סוכן מבצע {name}

## 📋 הוראות הפעלה
1. תייג את הקובץ הזה
2. תייג את דוח התיקונים
3. תייג את קובץ ה-HTML
4. פקודה: "בצע את התיקונים מהדוח"

---

## הנחיות ביצוע
- קרא את הדוח
- בצע את התיקונים לפי הסדר
- שמור על מבנה ה-HTML

---

## בדיקות לפני שליחה
- [ ] כל התיקונים מהדוח בוצעו
- [ ] המבנה לא נשבר
- [ ] הקוד תקין
"""
        }
    else:
        return f"""# סוכן {name}

## 📋 הוראות הפעלה
1. תייג את הקובץ הזה (`@{name}.md`)
2. תייג את קובץ ה-HTML
3. פקודה: "בצע את הפעולה על הקובץ"

---

## 🤖 הנחיות מערכת
**תפקיד:** [תיאור התפקיד]
**מטרה:** [מה הסוכן עושה]

---

## כללי עבודה
### מותר:
- [כלל 1]

### אסור:
- [כלל 1]

---

## פורמט הפלט
[תיאור הפלט הצפוי]
"""

# ============ API Routes - CSV ============

@app.route('/api/csv/pages', methods=['GET'])
def get_csv_pages():
    """Get all pages from CSV"""
    try:
        pages = read_csv_pages()
        return jsonify({"success": True, "pages": pages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/csv/add', methods=['POST'])
def add_csv_page():
    """Add a new page to CSV"""
    try:
        data = request.json
        write_csv_page(
            data.get("name", ""),
            data.get("keywords", ""),
            data.get("url", ""),
            data.get("post_id", "")
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Workflow ============

# Live progress logs folder
LIVE_LOGS_FOLDER = Path(__file__).parent / "logs"

# Temp files folder (runner scripts, batch files, lock files)
TMP_FOLDER = Path(__file__).parent / "tmp"

def init_tmp_folder():
    """Initialize tmp folder - clear old temp files on startup"""
    if TMP_FOLDER.exists():
        # Clear all temp files in folder
        for temp_file in TMP_FOLDER.glob("temp_*"):
            try:
                temp_file.unlink()
            except:
                pass
        print(f"[Cleanup] Cleared tmp folder")
    else:
        TMP_FOLDER.mkdir(exist_ok=True)
        print(f"[Cleanup] Created tmp folder")

# Initialize tmp folder on import
init_tmp_folder()

def init_logs_folder():
    """Initialize logs folder - clear old logs on startup"""
    # Delete old log files from previous versions
    old_logs = [
        BASE_DIR / "claude_work_log.txt",
        BASE_DIR / "claude_live_log.txt",
    ]
    for old_log in old_logs:
        if old_log.exists():
            try:
                old_log.unlink()
                print(f"[Cleanup] Deleted old log: {old_log.name}")
            except:
                pass
    
    # Create/recreate logs folder
    if LIVE_LOGS_FOLDER.exists():
        # Clear all logs in folder
        for log_file in LIVE_LOGS_FOLDER.glob("*.txt"):
            try:
                log_file.unlink()
            except:
                pass
        print(f"[Cleanup] Cleared logs folder")
    else:
        LIVE_LOGS_FOLDER.mkdir(exist_ok=True)
        print(f"[Cleanup] Created logs folder")

# Initialize logs on import
init_logs_folder()

def get_log_file_for_page(page_path):
    """Get the log file path for a specific page (DEPRECATED - use get_log_file_for_job)"""
    # Create a safe filename from page path
    safe_name = Path(page_path).stem  # Get filename without extension
    # Remove any problematic characters
    safe_name = safe_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return LIVE_LOGS_FOLDER / f"{safe_name}_log.txt"

def get_log_file_for_job(page_path, agent_id):
    """Get the log file path for a specific job (page + agent combination)"""
    # Create a safe filename from page path and agent_id
    safe_name = Path(page_path).stem  # Get filename without extension
    # Remove any problematic characters
    safe_name = safe_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_agent = agent_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return LIVE_LOGS_FOLDER / f"{safe_name}_{safe_agent}_log.txt"

def clear_live_log_for_job(page_path, agent_id):
    """Clear the live log file for a specific job"""
    try:
        log_file = get_log_file_for_job(page_path, agent_id)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("")
    except:
        pass

def append_live_log_for_job(page_path, agent_id, message):
    """Append a message to the live log for a specific job"""
    try:
        log_file = get_log_file_for_job(page_path, agent_id)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(message + "\n")
    except:
        pass

def clear_live_log(page_path):
    """Clear the live log file for a specific page"""
    try:
        log_file = get_log_file_for_page(page_path)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("")
    except:
        pass

def append_live_log(page_path, message):
    """Append a message to the live log for a specific page"""
    try:
        log_file = get_log_file_for_page(page_path)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(message + "\n")
    except:
        pass

def save_step_prompt(page_path, step_name, prompt, agent_folder_name="output"):
    """Save the prompt sent to Claude for a specific step.
    Uses agent_folder_name for dynamic folder naming - no hardcoded defaults."""
    try:
        page_folder = get_page_folder(page_path)
        # Use the provided folder name directly - callers must provide it
        prompts_folder = BASE_DIR / page_folder / agent_folder_name
        prompts_folder.mkdir(parents=True, exist_ok=True)
        
        prompt_file = prompts_folder / f"prompt_{step_name}.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(f"=== פרומפט שנשלח לקלוד - {step_name} ===\n")
            f.write(f"זמן: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(prompt)
        print(f"[Prompt Save] Saved prompt for {step_name} to {prompt_file}")
    except Exception as e:
        print(f"[Prompt Save] Error saving prompt: {e}")
        pass

@app.route('/api/workflow/clipboard', methods=['POST'])
def copy_to_clipboard():
    """Copy command to clipboard for Cursor mode"""
    try:
        if not CLIPBOARD_AVAILABLE:
            return jsonify({"success": False, "error": "pyperclip not installed"}), 500
        
        data = request.json
        command = data.get("command", "")
        
        pyperclip.copy(command)
        
        return jsonify({"success": True, "message": "Copied to clipboard"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/run-claude', methods=['POST'])
def run_claude_code():
    """Run Claude Code CLI command"""
    try:
        if not config["claude_code"]["enabled"]:
            return jsonify({"success": False, "error": "Claude Code is disabled"}), 400
        
        data = request.json
        prompt = data.get("prompt", "")
        
        cmd = get_claude_command()
        
        # Check if command exists
        if not Path(cmd).exists() and not shutil.which(cmd):
            return jsonify({
                "success": False, 
                "error": f"Claude Code not found at: {cmd}. Please check config.json"
            }), 400
        
        print(f"[Claude Code] Running: {cmd}")
        print(f"[Claude Code] Prompt: {prompt[:100]}...")
        
        # Run claude with prompt
        result = subprocess.run(
            [cmd, "-p", prompt],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=300,  # 5 minute timeout
            shell=True  # Needed for .cmd files on Windows
        )
        
        print(f"[Claude Code] Return code: {result.returncode}")
        if result.stderr:
            print(f"[Claude Code] Stderr: {result.stderr}")
        
        return jsonify({
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Command timed out (5 min)"}), 500
    except FileNotFoundError as e:
        return jsonify({"success": False, "error": f"File not found: {e}"}), 500
    except Exception as e:
        print(f"[Claude Code] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/step1', methods=['POST'])
def run_step1():
    """Run step 1 of a two-step agent (generate report)"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        keyword = data.get("keyword", "")
        mode = data.get("mode", "cursor")  # cursor or claude
        full_auto = data.get("full_auto", False)  # Full Auto mode flag
        total_steps = data.get("total_steps", 4)  # Total steps for this agent
        
        # === DUPLICATE CALL PROTECTION (TRIPLE CHECK) ===
        normalized_path = page_path.replace('\\', '/')
        
        # Check 1: In-memory
        current_info = running_pages.get(normalized_path)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= 1:
                print(f"[Step1] BLOCKED (memory): Step {running_step} already running for {page_path}")
                return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {running_step} already running", "blocked": True})
        
        # Check 2: File-based
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if normalized_path in saved_pages:
                    saved_step = saved_pages[normalized_path].get('step', 0)
                    if saved_step >= 1:
                        print(f"[Step1] BLOCKED (file): Step {saved_step} already running for {page_path}")
                        return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {saved_step} already running", "blocked": True})
        except Exception as e:
            print(f"[Step1] Warning: Could not check running_jobs.json: {e}")
        
        # === SITE RESTRICTION VALIDATION ===
        agent = get_agent_unified(agent_id)
        if agent:
            page_site = get_page_site(page_path)
            if not is_agent_allowed_for_site(agent, page_site):
                error_msg = f"הסוכן '{agent.get('name', agent_id)}' לא מוגדר לאתר '{page_site}'"
                print(f"[Step1] BLOCKED (site restriction): {error_msg}")
                return jsonify({"success": False, "error": error_msg}), 400
        
        # Debug logging for Full Auto
        print(f"[Step1] ===== RECEIVED REQUEST =====")
        print(f"[Step1] agent_id: {agent_id}")
        print(f"[Step1] page_path: {page_path}")
        print(f"[Step1] full_auto: {full_auto}")
        print(f"[Step1] total_steps: {total_steps}")
        print(f"[Step1] raw data: {data}")
        print(f"[Step1] =============================")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # Check if agent has step1 - dynamically count steps instead of checking type
        step_count = get_agent_step_count(agent)
        if step_count < 1:
            return jsonify({"success": False, "error": "Agent has no steps defined"}), 400
        
        # Get step1 from either old format (step1) or new format (steps[0])
        if "step1" in agent:
            step1 = agent["step1"]
        elif agent.get("steps") and len(agent.get("steps", [])) >= 1:
            step1 = agent["steps"][0]
        else:
            return jsonify({"success": False, "error": "Agent has no step1 defined"}), 400
        
        # Handle both old format (agent), new format (prompt_file), and inline (prompt_template)
        agent_file = step1.get("agent") or step1.get("prompt_file")
        prompt_template = step1.get("prompt_template", "")
        
        if not agent_file and not prompt_template:
            return jsonify({"success": False, "error": f"שלב 1 לא מוגדר - נא להגדיר קובץ פרומפט או תבנית בהגדרות הסוכן"}), 400
        
        # Get folder name dynamically from agent config - no hardcoded defaults
        agent_folder_name = agent.get("folder_name") or agent.get("name") or agent_id
        # Handle output path from old (output_name) or new (output.path) format
        output_name = step1.get("output_name") or (step1.get("output", {}).get("path", "דוח שלב 1.md") if isinstance(step1.get("output"), dict) else "דוח שלב 1.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Build paths for prompt
        agent_file_path = BASE_DIR / agent_file
        page_full_path = BASE_DIR / page_path
        report_full_path = output_folder / output_name
        
        # Build and save prompt for debugging (for both modes)
        keywords_instruction = ""
        page_info_path = BASE_DIR / page_folder / 'page_info.json'
        if page_info_path.exists():
            try:
                with open(page_info_path, 'r', encoding='utf-8') as f:
                    page_info = json.load(f)
                if 'fetched_keywords' in page_info:
                    kw_data = page_info['fetched_keywords']
                    kw_list = kw_data.get('final_keywords', [])
                    competitor_data = kw_data.get('competitor_data', [])
                    ai_mode_results = kw_data.get('ai_mode_results', [])
                    ai_rank = kw_data.get('ai_rank_position')
                    rank_position = kw_data.get('rank_position')
                    
                    # Fallback: if competitor_data is empty but organic_results exists, use that
                    if not competitor_data and kw_data.get('organic_results'):
                        competitor_data = kw_data.get('organic_results', [])
                    
                    # Get our URL to filter ourselves from results
                    our_url = page_info.get('url', '')
                    our_domain = ''
                    if our_url:
                        our_domain = our_url.replace('https://', '').replace('http://', '').split('/')[0]
                    
                    # Filter out our own results
                    if our_domain and competitor_data:
                        competitor_data = [c for c in competitor_data if our_domain not in c.get('url', '')]
                    if our_domain and ai_mode_results:
                        ai_mode_results = [a for a in ai_mode_results if a.get('is_summary') or our_domain not in a.get('url', '')]
                    
                    if kw_list:
                        # Build full keywords instruction with ranks
                        rank_info = ""
                        if rank_position:
                            rank_info += f"\n**דירוג אורגני:** מיקום {rank_position}"
                        if ai_rank:
                            rank_info += f"\n**דירוג AI Overview:** מיקום {ai_rank}"
                        
                        keywords_instruction = f"""

## מילות מפתח נלוות לשילוב

**רשימה:** {', '.join(kw_list)}{rank_info}

### רשימת שימור:

המילים הבאות חייבות להופיע בתוכן הסופי: {', '.join(kw_list)}
"""
                        # Add competitor data if available
                        if competitor_data:
                            comp_text = "\\n".join([f"- **{c.get('title', '')}** ({c.get('url', 'אין URL')}): {c.get('description', '')}" for c in competitor_data if c.get('description')])
                            if comp_text:
                                keywords_instruction += f"""
## מידע ממתחרים מדורגים

להלן תיאורים מאתרים המדורגים גבוה עבור מילת המפתח:

{comp_text}
"""
                        
                        # Add AI Overview results if available
                        if ai_mode_results:
                            ai_texts = []
                            for ai_r in ai_mode_results:
                                if ai_r.get('is_summary'):
                                    ai_texts.insert(0, f"**סיכום AI:** {ai_r.get('description', '')}")
                                elif ai_r.get('description'):
                                    ai_texts.append(f"- {ai_r.get('title', '')} ({ai_r.get('url', '')}): {ai_r.get('description', '')}")
                            
                            if ai_texts:
                                ai_status = f"**סטטוס:** אנחנו מופיעים במיקום {ai_rank}" if ai_rank else "**סטטוס:** לא מופיעים ב-AI Overview"
                                ai_texts_str = '\n'.join(ai_texts)
                                keywords_instruction += f"""
## תוצאות AI Overview של גוגל

הנה מה שגוגל AI מציג לגולשים שמחפשים את מילת המפתח:

{ai_texts_str}

{ai_status}
"""
                        print(f"[Step1] Built prompt with {len(kw_list)} keywords, {len(competitor_data)} competitors, {len(ai_mode_results)} AI results")
            except Exception as e:
                print(f"[Step1 Cursor] Could not load keywords: {e}")
        
        # Determine agent type from folder name
        # Save prompt for debugging - use agent folder name directly
        user_prompt_basic = f"קרא את קובץ ההוראות {agent_file_path} ובצע את ההוראות על הקובץ {page_full_path}. מילת מפתח: {keyword}.{keywords_instruction} בסוף חובה לשמור את הדוח בנתיב המדויק: {report_full_path}"
        save_step_prompt(page_path, "step1", user_prompt_basic, agent_folder_name)
        
        # Build command
        command = f"@{agent_file} @{page_path}"
        if keyword:
            command += f' מילת מפתח: "{keyword}"'
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command,
                    "message": "Command copied to clipboard. Paste in Cursor and run."
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command,
                    "message": "Copy this command to Cursor"
                })
        else:
            # Claude Code mode - run with streaming JSON for live progress
            global running_claude_process
            cmd = get_claude_command()
            
            # Get API key
            api_key = ANTHROPIC_API_KEY
            
            # Load fetched keywords if available
            keywords_instruction = ""
            page_folder_path = get_page_folder(page_path)
            page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
            print(f"[Step1 Keywords] page_path: {page_path}")
            print(f"[Step1 Keywords] page_folder_path: {page_folder_path}")
            print(f"[Step1 Keywords] page_info_path: {page_info_path}")
            print(f"[Step1 Keywords] exists: {page_info_path.exists()}")
            if page_info_path.exists():
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    print(f"[Step1 Keywords] Loaded page_info, has fetched_keywords: {'fetched_keywords' in page_info}")
                    if 'fetched_keywords' in page_info:
                        kw_data = page_info['fetched_keywords']
                        kw_list = kw_data.get('final_keywords', [])
                        competitor_data = kw_data.get('competitor_data', [])
                        ai_mode_results = kw_data.get('ai_mode_results', [])
                        ai_rank = kw_data.get('ai_rank_position')
                        
                        # Fallback: if competitor_data is empty but organic_results exists, use that
                        if not competitor_data and kw_data.get('organic_results'):
                            competitor_data = kw_data.get('organic_results', [])
                            print(f"[Step1] Using organic_results as competitor_data (fallback)")
                        
                        # Get our URL to filter ourselves from results
                        our_url = page_info.get('url', '')
                        our_domain = ''
                        if our_url:
                            # Extract domain from URL (e.g., "loan-israel.co.il" from "https://loan-israel.co.il/...")
                            our_domain = our_url.replace('https://', '').replace('http://', '').split('/')[0]
                            print(f"[Step1] Filtering out our domain: {our_domain}")
                        
                        # Filter out our own results from competitor data
                        if our_domain and competitor_data:
                            original_count = len(competitor_data)
                            competitor_data = [c for c in competitor_data if our_domain not in c.get('url', '')]
                            print(f"[Step1] Filtered competitors: {original_count} -> {len(competitor_data)}")
                        
                        # Filter out our own results from AI mode results (keep summary)
                        if our_domain and ai_mode_results:
                            original_count = len(ai_mode_results)
                            ai_mode_results = [a for a in ai_mode_results if a.get('is_summary') or our_domain not in a.get('url', '')]
                            print(f"[Step1] Filtered AI results: {original_count} -> {len(ai_mode_results)}")
                        
                        if kw_list:
                            keywords_instruction = f"""

## מילות מפתח נלוות לשילוב

**רשימה:** {', '.join(kw_list)}

### עקרונות שילוב דינאמיים:

⚠️ **חשוב:** כל עמוד הוא ייחודי! אל תשתמש בתבניות קבועות. חשוב מחדש עבור כל מילה בהקשר של התוכן הספציפי.

**לכל מילה ברשימה, בצע ניתוח עצמאי:**

1. **בדוק קיום:** האם המילה או משמעותה כבר קיימת בתוכן?
   - אם כן באותו הקשר → דלג
   - אם כן בהקשר אחר → שקול להוסיף זווית חדשה

2. **הערך פוטנציאל ערך:** מה הגולש ירוויח אם נרחיב על המילה הזו?
   - הרבה ← תוכן חדש (פסקה/FAQ/משפט - מה שמתאים)
   - מעט ← הטמעה טבעית בלבד
   - כלום ← דלג

3. **מצא מיקום אופטימלי:** היכן בתוכן הקיים זה הכי רלוונטי?
   - בתוך פסקה קיימת → הוסף משפט
   - ב-FAQ קיים → הרחב תשובה
   - אין מקום מתאים ויש ערך → צור חדש

4. **וודא ייחודיות:** 
   - אל תשתמש בניסוחים זהים בעמודים שונים
   - התאם את הסגנון לטון הספציפי של העמוד
   - השתמש במילות קישור ומעברים שונים

### הגבלות:
- מקסימום 3 תוספות משמעותיות (פסקה/FAQ) לעמוד
- אין הגבלה על משפטים בתוך תוכן קיים
- עדיפות: העשרת קיים > יצירת חדש

### רשימת שימור:
המילים הבאות חייבות להופיע בתוכן הסופי: {', '.join(kw_list)}
"""
                            # Add competitor data if available
                            if competitor_data:
                                comp_text = "\\n".join([f"- **{c.get('title', '')}** ({c.get('url', 'אין URL')}): {c.get('description', '')}" for c in competitor_data if c.get('description')])
                                if comp_text:
                                    keywords_instruction += f"""

## מידע ממתחרים מדורגים

להלן תיאורים מאתרים המדורגים גבוה עבור מילת המפתח:

{comp_text}

**הנחיות:**
- אם יש מידע בעל ערך שלא קיים בתוכן שלנו - שלב אותו
- התמקד במידע שמוסיף ערך לגולש, לא בנתונים טכניים
- אל תעתיק ישירות - נסח מחדש בסגנון שלנו
"""
                            
                            # Add AI Overview results if available (show all, not just 5)
                            if ai_mode_results:
                                ai_texts = []
                                for ai_r in ai_mode_results:
                                    if ai_r.get('is_summary'):
                                        ai_texts.insert(0, f"**סיכום AI:** {ai_r.get('description', '')}")
                                    elif ai_r.get('description'):
                                        ai_texts.append(f"- {ai_r.get('title', '')} ({ai_r.get('url', '')}): {ai_r.get('description', '')}")
                                
                                if ai_texts:
                                    ai_status = f"אנחנו מופיעים במיקום {ai_rank}" if ai_rank else "אנחנו לא מופיעים ב-AI Overview"
                                    ai_texts_str = '\n'.join(ai_texts)
                                    keywords_instruction += f"""

## תוצאות AI Overview של גוגל

הנה מה שגוגל AI מציג לגולשים שמחפשים את מילת המפתח:

{ai_texts_str}

**סטטוס:** {ai_status}

**הנחיות:**
- זהה פערים - אם ה-AI מדגיש מידע שלא קיים אצלנו, שקול להוסיף
- אל תעתיק - השתמש כהשראה בלבד
- עדיפות - נסה להבין למה מתחרים מופיעים ב-AI ואנחנו לא (אם רלוונטי)
"""
                            
                            # Add financial verification rules
                            keywords_instruction += """

## אזהרה חשובה - מידע פיננסי

**מידע פיננסי חדש (ריביות, תנאים, אחוזים, מסלולים) מותר לקחת רק מדומייני סמכות!**

✅ **דומיינים מאושרים:**
- **רגולטורים:** boi.org.il, gov.il, btl.gov.il, isa.gov.il, creditdata.org.il
- **בנקים:** bankhapoalim.co.il, leumi.co.il, mizrahi-tefahot.co.il, discountbank.co.il, fibi.co.il, bank-yahav.co.il, onezerobank.com, bankjerusalem.co.il
- **ביטוח:** harel-group.co.il, migdal.co.il, clalbit.co.il, menoramivt.co.il, fnx.co.il, 555.co.il
- **אשראי:** max.co.il, cal-online.co.il, isracard.co.il
- **עיתונות כלכלית:** globes.co.il, calcalist.co.il, themarker.com, bizportal.co.il
- **מימון מורשה:** btb.co.il, tarya.co.il, blender.co.il, loans.blender.co.il, ogen.org

❌ **אסור לקחת מידע פיננסי מ:** אתרי תוכן/בלוגים, אתרי השוואה לא מוסדרים, פורומים

⚠️ אם מצאת מידע מעניין באתר לא מאושר - ציין זאת בדוח אך אל תכניס לתוכן!
"""
                            print(f"[Step1] Adding {len(kw_list)} keywords, {len(competitor_data)} competitors, {len(ai_mode_results)} AI results to prompt")
                except Exception as e:
                    print(f"[Step1] Could not load keywords: {e}")
            
            # DYNAMIC: Use prompt_template if defined, otherwise use file-based approach
            if prompt_template:
                # Use ShortcodeEngine to process the template
                print(f"[Step1] Using prompt_template for agent {agent_id}")
                page_folder_for_shortcode = get_page_folder(page_path)
                html_file_path = str(page_folder_for_shortcode / Path(page_path).name)
                
                engine = ShortcodeEngine(
                    page_path=html_file_path,
                    agent=agent,
                    step_num=1
                )
                
                # Set context for shortcodes
                engine.context["OUTPUT_PATH"] = str(report_full_path)
                engine.context["PAGE_PATH"] = str(page_full_path)
                engine.context["KEYWORD"] = keyword
                
                # Process the template
                user_prompt = engine.process(prompt_template)
                # Add keywords instruction if available
                if keywords_instruction:
                    user_prompt += keywords_instruction
                
                # For display purposes in log
                agent_display_name = agent.get("name") or agent.get("folder_name") or agent_id
            else:
                user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ובצע את ההוראות על הקובץ {page_full_path}. מילת מפתח: {keyword}.{keywords_instruction} בסוף חובה לשמור את הדוח בנתיב המדויק: {report_full_path}"
                agent_display_name = agent_file if agent_file else agent_id
            
            # Save prompt for debugging
            save_step_prompt(page_path, "step1", user_prompt, agent_folder_name)
            
            # Escape backslashes for the generated Python script
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            agent_file_escaped = agent_display_name.replace("\\", "/") if agent_display_name else ""
            page_full_path_escaped = str(page_full_path).replace("\\", "\\\\")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script that captures streaming JSON and writes to log
            runner_script = TMP_FOLDER / "temp_run_claude.py"
            
            runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🚀 Claude Code Agent - שלב 1 (הפקת דוח)")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📋 סוכן: {agent_file_escaped}")
log("")

prompt = """{user_prompt_escaped}"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"{BASE_DIR}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output - use stdin for long prompts
claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",  # Print mode (non-interactive)
    "--verbose",  # Required for stream-json
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

# Open prompt file for stdin
prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

# Read streaming output
try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            # Try to parse as JSON
            try:
                data = json.loads(decoded)
                
                # Extract useful info from streaming JSON
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    # Assistant is thinking/responding
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    # Streaming text delta
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    # Final result
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                # Not JSON, just log as-is
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server that job is complete (legacy endpoint)
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")

# === STEP WEBHOOK - Notify step 1 completion for Full Auto ===
try:
    report_path = r"{report_full_path}"
    report_exists = os.path.exists(report_path)
    
    # Fallback: check if report was saved in page folder directly (without agent subfolder)
    if not report_exists:
        page_folder = os.path.dirname(r"{page_full_path_escaped}")
        fallback_path = os.path.join(page_folder, "{output_name}")
        if os.path.exists(fallback_path):
            report_exists = True
            log(f"📁 Found report at fallback location: {{fallback_path}}")
            # Move to correct location
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            import shutil
            shutil.move(fallback_path, report_path)
            log(f"📦 Moved report to: {{report_path}}")
    
    webhook_data = json_lib.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": 1,
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 1 webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
            with open(runner_script, 'w', encoding='utf-8') as f:
                f.write(runner_content)
            
            batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
            batch_path = TMP_FOLDER / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Open in legacy CMD (bypass Windows Terminal)
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            # Mark page as running with PID
            set_page_running(page_path, agent_id, 1, running_claude_process.pid, full_auto=full_auto, total_steps=total_steps)
            
            # Register Full Auto backup job
            if full_auto:
                register_full_auto_job(page_path, agent_id, 1, total_steps)
            
            print(f"[Step1] Running Claude Code with streaming for {page_path} (Full Auto: {full_auto})")
            
            return jsonify({
                "success": True,
                "mode": "claude",
                "page_path": page_path,
                "message": "Claude Code running with live progress!"
            })
    except Exception as e:
        print(f"[Step1] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/step2', methods=['POST'])
def run_step2():
    """Run step 2 - QA and expand report (for four-step agents)"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        report1_path = data.get("report1_path")  # דוח שלב 1
        mode = data.get("mode", "cursor")
        full_auto = data.get("full_auto", False)  # Full Auto mode flag
        total_steps = data.get("total_steps", 4)  # Total steps for this agent
        
        # === DUPLICATE CALL PROTECTION (TRIPLE CHECK) ===
        # Check if step 2 is already running for this page
        normalized_path = page_path.replace('\\', '/')
        
        # Check 1: In-memory running_pages
        current_info = running_pages.get(normalized_path)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= 2:
                print(f"[Step2] BLOCKED (memory): Step {running_step} already running for {page_path}")
                return jsonify({
                    "success": True,
                    "mode": mode,
                    "page_path": page_path,
                    "message": f"Step {running_step} already running",
                    "blocked": True
                })
        
        # Check 2: File-based running_jobs.json (for race conditions)
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if normalized_path in saved_pages:
                    saved_step = saved_pages[normalized_path].get('step', 0)
                    if saved_step >= 2:
                        print(f"[Step2] BLOCKED (file): Step {saved_step} already running for {page_path}")
                        return jsonify({
                            "success": True,
                            "mode": mode,
                            "page_path": page_path,
                            "message": f"Step {saved_step} already running (from file)",
                            "blocked": True
                        })
        except Exception as e:
            print(f"[Step2] Warning: Could not check running_jobs.json: {e}")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # === SITE RESTRICTION VALIDATION ===
        page_site = get_page_site(page_path)
        if not is_agent_allowed_for_site(agent, page_site):
            error_msg = f"הסוכן '{agent.get('name', agent_id)}' לא מוגדר לאתר '{page_site}'"
            print(f"[Step2] BLOCKED (site restriction): {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 400
        
        # Check if agent has step2 - dynamically count steps
        step_count = get_agent_step_count(agent)
        # Remove old counting loop since get_agent_step_count handles it
        _dummy = 0  # Placeholder for backwards compatibility
        for i in range(1, 10):
            if f"step{i}" in agent:
                step_count = max(step_count, i)
        
        if agent.get("type") not in valid_types and step_count < 2:
            # For non-multi-step agents, call the old step2 logic (now step3)
            return run_step3_fixes()
        
        # Get step2 from either old format (step2) or new format (steps[1])
        step2 = agent.get("step2")
        if not step2 and agent.get("steps") and len(agent.get("steps", [])) >= 2:
            step2 = agent["steps"][1]
        if not step2:
            return jsonify({"success": False, "error": "Agent has no step2"}), 400
        
        # Handle both old format (agent) and new format (prompt_file)
        agent_file = step2.get("agent") or step2.get("prompt_file")
        if not agent_file:
            return jsonify({"success": False, "error": "Step2 has no agent/prompt_file defined"}), 400
        
        # Get folder name dynamically from agent config - no hardcoded defaults
        agent_folder_name = agent.get("folder_name") or agent.get("name") or agent_id
        output_name = step2.get("output_name") or (step2.get("output", {}).get("path", "דוח שלב 1 מורחב.md") if isinstance(step2.get("output"), dict) else "דוח שלב 1 מורחב.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Build paths for prompt
        agent_file_path = BASE_DIR / agent_file
        page_full_path = BASE_DIR / page_path
        report1_full = BASE_DIR / report1_path
        report_full_path = output_folder / output_name
        
        # Load fetched keywords if available (for both modes)
        keywords_instruction = ""
        page_folder_path = get_page_folder(page_path)
        page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
        if page_info_path.exists():
            try:
                with open(page_info_path, 'r', encoding='utf-8') as f:
                    page_info = json.load(f)
                if 'fetched_keywords' in page_info:
                    kw_data = page_info['fetched_keywords']
                    kw_list = kw_data.get('final_keywords', [])
                    competitor_data = kw_data.get('competitor_data', [])
                    ai_mode_results = kw_data.get('ai_mode_results', [])
                    ai_rank = kw_data.get('ai_rank_position')
                    rank_position = kw_data.get('rank_position')
                    
                    # Fallback: if competitor_data is empty but organic_results exists, use that
                    if not competitor_data and kw_data.get('organic_results'):
                        competitor_data = kw_data.get('organic_results', [])
                    
                    # Get our URL to filter ourselves from results
                    our_url = page_info.get('url', '')
                    our_domain = ''
                    if our_url:
                        our_domain = our_url.replace('https://', '').replace('http://', '').split('/')[0]
                    
                    # Filter out our own results
                    if our_domain and competitor_data:
                        competitor_data = [c for c in competitor_data if our_domain not in c.get('url', '')]
                    if our_domain and ai_mode_results:
                        ai_mode_results = [a for a in ai_mode_results if a.get('is_summary') or our_domain not in a.get('url', '')]
                    
                    if kw_list:
                        # Build full keywords instruction with ranks
                        rank_info = ""
                        if rank_position:
                            rank_info += f"\n**דירוג אורגני:** מיקום {rank_position}"
                        if ai_rank:
                            rank_info += f"\n**דירוג AI Overview:** מיקום {ai_rank}"
                        
                        keywords_instruction = f"""

## מילות מפתח נלוות לשילוב

**רשימה:** {', '.join(kw_list)}{rank_info}

### רשימת שימור:

המילים הבאות חייבות להופיע בתוכן הסופי: {', '.join(kw_list)}
"""
                        # Add competitor data if available
                        if competitor_data:
                            comp_text = "\\n".join([f"- **{c.get('title', '')}** ({c.get('url', 'אין URL')}): {c.get('description', '')}" for c in competitor_data if c.get('description')])
                            if comp_text:
                                keywords_instruction += f"""
## מידע ממתחרים מדורגים

להלן תיאורים מאתרים המדורגים גבוה עבור מילת המפתח:

{comp_text}
"""
                        
                        # Add AI Overview results if available
                        if ai_mode_results:
                            ai_texts = []
                            for ai_r in ai_mode_results:
                                if ai_r.get('is_summary'):
                                    ai_texts.insert(0, f"**סיכום AI:** {ai_r.get('description', '')}")
                                elif ai_r.get('description'):
                                    ai_texts.append(f"- {ai_r.get('title', '')} ({ai_r.get('url', '')}): {ai_r.get('description', '')}")
                            
                            if ai_texts:
                                ai_status = f"**סטטוס:** אנחנו מופיעים במיקום {ai_rank}" if ai_rank else "**סטטוס:** לא מופיעים ב-AI Overview"
                                ai_texts_str = '\n'.join(ai_texts)
                                keywords_instruction += f"""
## תוצאות AI Overview של גוגל

הנה מה שגוגל AI מציג לגולשים שמחפשים את מילת המפתח:

{ai_texts_str}

{ai_status}
"""
                        print(f"[Step2] Built prompt with {len(kw_list)} keywords, {len(competitor_data)} competitors, {len(ai_mode_results)} AI results")
            except Exception as e:
                print(f"[Step2 Cursor] Could not load keywords: {e}")
        
        # Determine agent type from folder name
        # Use agent_folder_name directly instead of hardcoded type detection
        
        # Build and save prompt for debugging (for both modes)
        user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת דוח שלב 1: {report1_full} ואת קובץ ה-HTML: {page_full_path}. בדוק את הדוח, הרחב אותו והוסף הצעות טקסט מלאות.{keywords_instruction} בסוף חובה לשמור את הדוח המורחב בנתיב המדויק: {report_full_path}"
        save_step_prompt(page_path, "step2", user_prompt, agent_folder_name)
        
        # Build command for Cursor mode
        command = f"@{agent_file} @{report1_path} @{page_path}"
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor", 
                    "command": command,
                    "message": "Command copied to clipboard. Paste in Cursor and run."
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command,
                    "message": "Copy this command to Cursor"
                })
        else:
            # Claude Code mode
            cmd = get_claude_command()
            api_key = ANTHROPIC_API_KEY
            
            # Build prompt for QA agent
            report_full_path = output_folder / output_name
            
            # Load fetched keywords if available
            keywords_instruction = ""
            page_folder_path = get_page_folder(page_path)
            page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
            if page_info_path.exists():
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    if 'fetched_keywords' in page_info:
                        kw_data = page_info['fetched_keywords']
                        kw_list = kw_data.get('final_keywords', [])
                        competitor_data = kw_data.get('competitor_data', [])
                        ai_mode_results = kw_data.get('ai_mode_results', [])
                        ai_rank = kw_data.get('ai_rank_position')
                        
                        # Fallback: if competitor_data is empty but organic_results exists, use that
                        if not competitor_data and kw_data.get('organic_results'):
                            competitor_data = kw_data.get('organic_results', [])
                            print(f"[Step2] Using organic_results as competitor_data (fallback)")
                        
                        # Get our URL to filter ourselves from results
                        our_url = page_info.get('url', '')
                        our_domain = ''
                        if our_url:
                            our_domain = our_url.replace('https://', '').replace('http://', '').split('/')[0]
                            print(f"[Step2] Filtering out our domain: {our_domain}")
                        
                        # Filter out our own results from competitor data
                        if our_domain and competitor_data:
                            original_count = len(competitor_data)
                            competitor_data = [c for c in competitor_data if our_domain not in c.get('url', '')]
                            print(f"[Step2] Filtered competitors: {original_count} -> {len(competitor_data)}")
                        
                        # Filter out our own results from AI mode results (keep summary)
                        if our_domain and ai_mode_results:
                            original_count = len(ai_mode_results)
                            ai_mode_results = [a for a in ai_mode_results if a.get('is_summary') or our_domain not in a.get('url', '')]
                            print(f"[Step2] Filtered AI results: {original_count} -> {len(ai_mode_results)}")
                        
                        if kw_list:
                            keywords_instruction = f"""

## מילות מפתח נלוות לשילוב

**רשימה:** {', '.join(kw_list)}

### עקרונות שילוב דינאמיים:

⚠️ **חשוב:** כל עמוד הוא ייחודי! אל תשתמש בתבניות קבועות. חשוב מחדש עבור כל מילה בהקשר של התוכן הספציפי.

**לכל מילה ברשימה, בצע ניתוח עצמאי:**

1. **בדוק קיום:** האם המילה או משמעותה כבר קיימת בתוכן?
   - אם כן באותו הקשר → דלג
   - אם כן בהקשר אחר → שקול להוסיף זווית חדשה

2. **הערך פוטנציאל ערך:** מה הגולש ירוויח אם נרחיב על המילה הזו?
   - הרבה ← תוכן חדש (פסקה/FAQ/משפט - מה שמתאים)
   - מעט ← הטמעה טבעית בלבד
   - כלום ← דלג

3. **מצא מיקום אופטימלי:** היכן בתוכן הקיים זה הכי רלוונטי?
   - בתוך פסקה קיימת → הוסף משפט
   - ב-FAQ קיים → הרחב תשובה
   - אין מקום מתאים ויש ערך → צור חדש

4. **וודא ייחודיות:** 
   - אל תשתמש בניסוחים זהים בעמודים שונים
   - התאם את הסגנון לטון הספציפי של העמוד
   - השתמש במילות קישור ומעברים שונים

### הגבלות:
- מקסימום 3 תוספות משמעותיות (פסקה/FAQ) לעמוד
- אין הגבלה על משפטים בתוך תוכן קיים
- עדיפות: העשרת קיים > יצירת חדש

### רשימת שימור:
המילים הבאות חייבות להופיע בתוכן הסופי: {', '.join(kw_list)}
"""
                            # Add competitor data if available
                            if competitor_data:
                                comp_text = "\\n".join([f"- **{c.get('title', '')}** ({c.get('url', 'אין URL')}): {c.get('description', '')}" for c in competitor_data if c.get('description')])
                                if comp_text:
                                    keywords_instruction += f"""

## מידע ממתחרים מדורגים

להלן תיאורים מאתרים המדורגים גבוה עבור מילת המפתח:

{comp_text}

**הנחיות:**
- אם יש מידע בעל ערך שלא קיים בתוכן שלנו - שלב אותו
- התמקד במידע שמוסיף ערך לגולש, לא בנתונים טכניים
- אל תעתיק ישירות - נסח מחדש בסגנון שלנו
"""
                            
                            # Add AI Overview results if available (show all, not just 5)
                            if ai_mode_results:
                                ai_texts = []
                                for ai_r in ai_mode_results:
                                    if ai_r.get('is_summary'):
                                        ai_texts.insert(0, f"**סיכום AI:** {ai_r.get('description', '')}")
                                    elif ai_r.get('description'):
                                        ai_texts.append(f"- {ai_r.get('title', '')} ({ai_r.get('url', '')}): {ai_r.get('description', '')}")
                                
                                if ai_texts:
                                    ai_status = f"אנחנו מופיעים במיקום {ai_rank}" if ai_rank else "אנחנו לא מופיעים ב-AI Overview"
                                    ai_texts_str = '\n'.join(ai_texts)
                                    keywords_instruction += f"""

## תוצאות AI Overview של גוגל

הנה מה שגוגל AI מציג לגולשים שמחפשים את מילת המפתח:

{ai_texts_str}

**סטטוס:** {ai_status}

**הנחיות:**
- זהה פערים - אם ה-AI מדגיש מידע שלא קיים אצלנו, שקול להוסיף
- אל תעתיק - השתמש כהשראה בלבד
- עדיפות - נסה להבין למה מתחרים מופיעים ב-AI ואנחנו לא (אם רלוונטי)
"""
                            
                            # Add financial verification rules
                            keywords_instruction += """

## אזהרה חשובה - מידע פיננסי

**מידע פיננסי חדש (ריביות, תנאים, אחוזים, מסלולים) מותר לקחת רק מדומייני סמכות!**

✅ **דומיינים מאושרים:**
- **רגולטורים:** boi.org.il, gov.il, btl.gov.il, isa.gov.il, creditdata.org.il
- **בנקים:** bankhapoalim.co.il, leumi.co.il, mizrahi-tefahot.co.il, discountbank.co.il, fibi.co.il, bank-yahav.co.il, onezerobank.com, bankjerusalem.co.il
- **ביטוח:** harel-group.co.il, migdal.co.il, clalbit.co.il, menoramivt.co.il, fnx.co.il, 555.co.il
- **אשראי:** max.co.il, cal-online.co.il, isracard.co.il
- **עיתונות כלכלית:** globes.co.il, calcalist.co.il, themarker.com, bizportal.co.il
- **מימון מורשה:** btb.co.il, tarya.co.il, blender.co.il, loans.blender.co.il, ogen.org

❌ **אסור לקחת מידע פיננסי מ:** אתרי תוכן/בלוגים, אתרי השוואה לא מוסדרים, פורומים

⚠️ אם מצאת מידע מעניין באתר לא מאושר - ציין זאת בדוח אך אל תכניס לתוכן!
"""
                            print(f"[Step2] Adding {len(kw_list)} keywords, {len(competitor_data)} competitors, {len(ai_mode_results)} AI results to prompt")
                except Exception as e:
                    print(f"[Step2] Could not load keywords: {e}")
            
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת דוח שלב 1: {report1_full} ואת קובץ ה-HTML: {page_full_path}. בדוק את הדוח, הרחב אותו והוסף הצעות טקסט מלאות.{keywords_instruction} בסוף חובה לשמור את הדוח המורחב בנתיב המדויק: {report_full_path}"
            
            # Save prompt for debugging
            save_step_prompt(page_path, "step2", user_prompt, agent_folder_name)
            
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script
            runner_script = TMP_FOLDER / "temp_run_claude.py"
            
            runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("📋 Claude Code Agent - שלב 2 (QA והרחבת דוח)")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("")

prompt = """{user_prompt_escaped}"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"{BASE_DIR}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

log("🔄 מריץ Claude Code עם streaming...")
log("🧠 מודל: Claude Opus | 💰 תקציב: 10$")
log("-" * 60)
log("")

claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

# Open prompt file for stdin
prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Legacy endpoint
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")

# === STEP WEBHOOK - Notify step 2 completion for Full Auto ===
try:
    report_path = r"{report_full_path}"
    report_exists = os.path.exists(report_path)
    webhook_data = json_lib.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": 2,
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 2 webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
            
            with open(runner_script, 'w', encoding='utf-8') as f:
                f.write(runner_content)
            
            batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
            batch_path = TMP_FOLDER / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            running_process = subprocess.Popen(
                ['C:\\Windows\\System32\\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            set_page_running(page_path, agent_id, 2, running_process.pid, full_auto=full_auto, total_steps=total_steps)
            
            return jsonify({
                "success": True,
                "mode": "claude_code",
                "message": "Claude Code running step 2 (QA)"
            })
    except Exception as e:
        print(f"[Step2] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/step3', methods=['POST'])
def run_step3_fixes():
    """Run step 3 - apply fixes (was step2 for three-step agents)"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        report_path = data.get("report_path")
        mode = data.get("mode", "cursor")
        full_auto = data.get("full_auto", False)  # Full Auto mode flag
        total_steps = data.get("total_steps", 4)  # Total steps for this agent
        
        # === DUPLICATE CALL PROTECTION (TRIPLE CHECK) ===
        normalized_path = page_path.replace('\\', '/')
        
        # Check 1: In-memory
        current_info = running_pages.get(normalized_path)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= 3:
                print(f"[Step3] BLOCKED (memory): Step {running_step} already running for {page_path}")
                return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {running_step} already running", "blocked": True})
        
        # Check 2: File-based
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if normalized_path in saved_pages:
                    saved_step = saved_pages[normalized_path].get('step', 0)
                    if saved_step >= 3:
                        print(f"[Step3] BLOCKED (file): Step {saved_step} already running for {page_path}")
                        return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {saved_step} already running", "blocked": True})
        except Exception as e:
            print(f"[Step3] Warning: Could not check running_jobs.json: {e}")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # === SITE RESTRICTION VALIDATION ===
        page_site = get_page_site(page_path)
        if not is_agent_allowed_for_site(agent, page_site):
            error_msg = f"הסוכן '{agent.get('name', agent_id)}' לא מוגדר לאתר '{page_site}'"
            print(f"[Step3] BLOCKED (site restriction): {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 400
        
        # For four-step/six-step agents, look at step3; for three-step, look at step2
        step_config = agent.get("step3") if agent.get("type") in ["four-step", "six-step"] else agent.get("step2")
        if not step_config:
            return jsonify({"success": False, "error": "Agent has no fixes step"}), 400
        
        agent_file = step_config["agent"]
        # Get folder name dynamically from agent config - no hardcoded defaults
        agent_folder_name = agent.get("folder_name") or agent.get("name") or agent_id
        report_output_name = step_config.get("report_name", "דוח שלב 3.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Validate that input report exists (step 2 expanded report)
        if report_path:
            report_full = BASE_DIR / report_path
            if not report_full.exists():
                return jsonify({"success": False, "error": f"דוח מורחב לא נמצא: {report_path}. הרץ שלב 2 קודם!"}), 400
        
        # Build paths and save prompt for debugging (for both modes)
        agent_file_path = BASE_DIR / agent_file
        page_full_path = BASE_DIR / page_path
        report_full = BASE_DIR / report_path if report_path else None
        report_full_path = output_folder / report_output_name
        
        # Determine agent type from folder name
        # Use agent_folder_name directly instead of hardcoded type detection
        
        user_prompt_basic = f"קרא את קובץ ההוראות {agent_file_path} ואת הדוח {report_full} ואת קובץ ה-HTML: {page_full_path}. בצע את ההוראות. בסוף שמור את הדוח בנתיב: {report_full_path}"
        save_step_prompt(page_path, "step3", user_prompt_basic, agent_folder_name)
        
        # Build command
        command = f"@{agent_file} @{report_path} @{page_path}"
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor", 
                    "command": command,
                    "message": "Command copied to clipboard. Paste in Cursor and run."
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command,
                    "message": "Copy this command to Cursor"
                })
        else:
            # Claude Code mode - run with streaming JSON for live progress
            global running_claude_process
            cmd = get_claude_command()
            api_key = ANTHROPIC_API_KEY
            report_full_path = BASE_DIR / report_path
            
            # Simple prompt - edit file in place, don't create new file
            report_save_path = output_folder / report_output_name
            
            # Load keywords for preservation
            keywords_preservation = ""
            page_folder_path = get_page_folder(page_path)
            page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
            if page_info_path.exists():
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    if 'fetched_keywords' in page_info:
                        kw_list = page_info['fetched_keywords'].get('final_keywords', [])
                        if kw_list:
                            keywords_preservation = f"""

## מילות מפתח חשובות - אל תמחק!

המילים הבאות חייבות להישאר בתוכן: {', '.join(kw_list)}

בעת עריכת הקובץ, וודא שמילים אלה לא נמחקות!
"""
                            print(f"[Step3] Adding {len(kw_list)} keywords preservation to prompt")
                except Exception as e:
                    print(f"[Step3] Could not load keywords: {e}")
            
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת הדוח {report_full_path}. ערוך את הקובץ {page_full_path} ישירות עם כלי Edit (לא Write!) - אל תיצור קובץ חדש!{keywords_preservation} בסוף חובה לשמור דוח סיכום בנתיב המדויק: {report_save_path}"
            
            # Save prompt for debugging
            save_step_prompt(page_path, "step3", user_prompt, agent_folder_name)
            
            # Escape backslashes for the generated Python script
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            report_path_escaped = report_path.replace("\\", "/")
            agent_file_escaped = agent_file.replace("\\", "/")
            report_save_path_escaped = str(report_save_path).replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script that captures streaming JSON and writes to log
            runner_script = TMP_FOLDER / "temp_run_claude.py"
            
            runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🔧 Claude Code Agent - שלב 3 (תיקונים)")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📋 דוח: {report_path_escaped}")
log("📋 סוכן: {agent_file_escaped}")
log("📝 דוח יישמר ב: {report_save_path_escaped}")
log("")

prompt = """{user_prompt_escaped}"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"{BASE_DIR}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output - use stdin for long prompts
claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",  # Print mode (non-interactive)
    "--verbose",  # Required for stream-json
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

# Open prompt file for stdin
prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

# Read streaming output
try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            # Try to parse as JSON
            try:
                data = json.loads(decoded)
                
                # Extract useful info from streaming JSON
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    # Assistant is thinking/responding
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    # Streaming text delta
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    # Final result
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                # Not JSON, just log as-is
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server that job is complete (legacy)
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")

# === STEP WEBHOOK - Notify step 3 completion for Full Auto ===
try:
    report_path = r"{report_save_path_escaped}"
    report_exists = os.path.exists(report_path)
    webhook_data = json_lib.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": 3,
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 3 webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
            with open(runner_script, 'w', encoding='utf-8') as f:
                f.write(runner_content)
            
            batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
            batch_path = TMP_FOLDER / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Open in legacy CMD (bypass Windows Terminal)
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            # Mark page as running with PID
            set_page_running(page_path, agent_id, 3, running_claude_process.pid, full_auto=full_auto, total_steps=total_steps)
            
            print(f"[Step3] Running Claude Code with streaming for {page_path} (Full Auto: {full_auto})")
            
            return jsonify({
                "success": True,
                "mode": "claude",
                "page_path": page_path,
                "message": "Claude Code running with live progress!"
            })
    except Exception as e:
        print(f"[Step2] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/step4', methods=['POST'])
def run_step4():
    """Run step 4 - debug (was step3 for three-step agents)"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        report1_path = data.get("report1_path")
        report2_path = data.get("report2_path")
        # fixed_file_path is no longer needed - we edit page_path directly
        mode = data.get("mode", "cursor")
        full_auto = data.get("full_auto", False)  # Full Auto mode flag
        total_steps = data.get("total_steps", 4)  # Total steps for this agent
        
        # === DUPLICATE CALL PROTECTION (TRIPLE CHECK) ===
        normalized_path = page_path.replace('\\', '/')
        
        # Check 1: In-memory
        current_info = running_pages.get(normalized_path)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= 4:
                print(f"[Step4] BLOCKED (memory): Step {running_step} already running for {page_path}")
                return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {running_step} already running", "blocked": True})
        
        # Check 2: File-based
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if normalized_path in saved_pages:
                    saved_step = saved_pages[normalized_path].get('step', 0)
                    if saved_step >= 4:
                        print(f"[Step4] BLOCKED (file): Step {saved_step} already running for {page_path}")
                        return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {saved_step} already running", "blocked": True})
        except Exception as e:
            print(f"[Step4] Warning: Could not check running_jobs.json: {e}")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # === SITE RESTRICTION VALIDATION ===
        page_site = get_page_site(page_path)
        if not is_agent_allowed_for_site(agent, page_site):
            error_msg = f"הסוכן '{agent.get('name', agent_id)}' לא מוגדר לאתר '{page_site}'"
            print(f"[Step4] BLOCKED (site restriction): {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 400
        
        # Validate that required reports exist
        if report2_path:
            report2_full = BASE_DIR / report2_path
            if not report2_full.exists():
                return jsonify({"success": False, "error": f"דוח שלב 3 לא נמצא: {report2_path}. הרץ שלב 3 קודם!"}), 400
        
        # For four-step/six-step agents, look at step4; for three-step, look at step3
        step_config = agent.get("step4") if agent.get("type") in ["four-step", "six-step"] else agent.get("step3")
        if not step_config:
            return jsonify({"success": False, "error": "Agent has no debug step"}), 400
        
        agent_file = step_config["agent"]
        # Get folder name dynamically from agent config - no hardcoded defaults
        agent_folder_name = agent.get("folder_name") or agent.get("name") or agent_id
        report_output_name = step_config.get("report_name", "דוח דיבאג.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Build paths and save prompt for debugging (for both modes)
        agent_file_path = BASE_DIR / agent_file
        page_full_path = BASE_DIR / page_path
        report1_full = BASE_DIR / report1_path if report1_path else None
        report2_full = BASE_DIR / report2_path if report2_path else None
        report_full_path = output_folder / report_output_name
        
        # Determine agent type from folder name
        # Use agent_folder_name directly instead of hardcoded type detection
        
        user_prompt_basic = f"קרא את קובץ ההוראות {agent_file_path} ואת הדוחות {report1_full}, {report2_full} ואת קובץ ה-HTML: {page_full_path}. בצע את ההוראות. בסוף שמור את הדוח בנתיב: {report_full_path}"
        save_step_prompt(page_path, "step4", user_prompt_basic, agent_folder_name)
        
        # Build command - page_path is the file to edit directly
        command = f"@{agent_file} @{report1_path} @{report2_path} @{page_path}"
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor", 
                    "command": command,
                    "message": "Command copied to clipboard. Paste in Cursor and run."
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command,
                    "message": "Copy this command to Cursor"
                })
        else:
            # Claude Code mode
            global running_claude_process
            cmd = get_claude_command()
            api_key = ANTHROPIC_API_KEY
            
            # Build paths
            agent_file_path = BASE_DIR / agent_file
            report1_full = BASE_DIR / report1_path
            report2_full = BASE_DIR / report2_path
            page_full_path = BASE_DIR / page_path
            # For 4-step: report1 is "דוח שלב 1 מורחב" (from QA), report2 is "דוח שלב 3" (from fixes)
            report_save_path = output_folder / report_output_name
            
            # Load keywords for preservation
            keywords_preservation = ""
            page_folder_path = get_page_folder(page_path)
            page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
            if page_info_path.exists():
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    if 'fetched_keywords' in page_info:
                        kw_list = page_info['fetched_keywords'].get('final_keywords', [])
                        if kw_list:
                            keywords_preservation = f"""

## מילות מפתח חשובות - אל תמחק!

המילים הבאות חייבות להישאר בתוכן: {', '.join(kw_list)}

בעת עריכת הקובץ, וודא שמילים אלה לא נמחקות!
"""
                            print(f"[Step4] Adding {len(kw_list)} keywords preservation to prompt")
                except Exception as e:
                    print(f"[Step4] Could not load keywords: {e}")
            
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת הדוח המורחב: {report1_full} ודוח התיקונים: {report2_full}. בדוק את הקובץ {page_full_path} ומצא מה לא בוצע מהדוחות. ערוך את הקובץ ישירות עם כלי Edit (לא Write!) - אל תיצור קובץ חדש!{keywords_preservation} בסוף חובה לשמור דוח דיבאג בנתיב המדויק: {report_save_path}"
            
            # Save prompt for debugging
            save_step_prompt(page_path, "step4", user_prompt, agent_folder_name)
            
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            report_save_path_escaped = str(report_save_path).replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script
            runner_script = TMP_FOLDER / "temp_run_claude.py"
            
            runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🔍 Claude Code Agent - שלב 4 (דיבאג)")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📝 דוח יישמר ב: {report_save_path_escaped}")
log("")

prompt = """{user_prompt_escaped}"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"{BASE_DIR}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",  # Print mode (non-interactive)
    "--verbose",  # Required for stream-json
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

log("🚀 מפעיל Claude Code...")
log("-" * 60)
log("")

# Open prompt file for stdin
prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

# Read streaming output
try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            # Try to parse as JSON
            try:
                data = json.loads(decoded)
                
                # Extract useful info from streaming JSON
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    # Assistant is thinking/responding
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    # Streaming text delta
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    # Final result
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                # Not JSON, just log as-is
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server that job is complete (legacy)
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")

# === STEP WEBHOOK - Notify step 4 completion for Full Auto ===
try:
    report_path = r"{report_save_path_escaped}"
    report_exists = os.path.exists(report_path)
    webhook_data = json_lib.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": 4,
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 4 webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
            
            with open(runner_script, 'w', encoding='utf-8') as f:
                f.write(runner_content)
            
            # Create batch file
            batch_content = f'''@echo off
chcp 65001 >nul
echo ============================================================
echo   Running Claude Code - Step 4 Debug
echo ============================================================
{PYTHON_CMD} "{runner_script}"
echo.
echo ============================================================
echo   Step 4 finished!
echo ============================================================
'''
            batch_path = TMP_FOLDER / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Open in legacy CMD
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            # Mark page as running
            set_page_running(page_path, agent_id, 4, running_claude_process.pid, full_auto=full_auto, total_steps=total_steps)
            
            print(f"[Step4] Running Claude Code debug for {page_path} (Full Auto: {full_auto})")
            
            return jsonify({
                "success": True,
                "mode": "claude",
                "page_path": page_path,
                "message": "Claude Code Step 3 running!"
            })
    except Exception as e:
        print(f"[Step3] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/step5', methods=['POST'])
def run_step5():
    """Run step 5 - AI removal (for six-step agents)"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        mode = data.get("mode", "cursor")
        full_auto = data.get("full_auto", False)  # Read full_auto from request
        total_steps = data.get("total_steps", 6)  # Read total_steps from request
        
        # === DUPLICATE CALL PROTECTION using COMPOSITE KEY ===
        normalized_path = page_path.replace('\\', '/')
        job_key = get_job_key(page_path, agent_id)
        
        # Check 1: In-memory using composite key
        current_info = running_pages.get(job_key)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= 5:
                print(f"[Step5] BLOCKED (memory): Step {running_step} already running for {job_key}")
                return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {running_step} already running", "blocked": True})
        
        # Check 2: File-based using composite key
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if job_key in saved_pages:
                    saved_step = saved_pages[job_key].get('step', 0)
                    if saved_step >= 5:
                        print(f"[Step5] BLOCKED (file): Step {saved_step} already running for {job_key}")
                        return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {saved_step} already running", "blocked": True})
        except Exception as e:
            print(f"[Step5] Warning: Could not check running_jobs.json: {e}")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # === SITE RESTRICTION VALIDATION ===
        page_site = get_page_site(page_path)
        if not is_agent_allowed_for_site(agent, page_site):
            error_msg = f"הסוכן '{agent.get('name', agent_id)}' לא מוגדר לאתר '{page_site}'"
            print(f"[Step5] BLOCKED (site restriction): {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 400
        
        # Check if agent has 5+ steps
        step_count = len(agent.get("steps", []))
        for i in range(1, 10):
            if f"step{i}" in agent:
                step_count = max(step_count, i)
        
        # Dynamically check if agent has step 5
        if step_count < 5:
            return jsonify({"success": False, "error": "Agent has less than 5 steps"}), 400
        
        # Get step5 from either old format (step5) or new format (steps[4])
        step5 = agent.get("step5")
        if not step5 and agent.get("steps") and len(agent.get("steps", [])) >= 5:
            step5 = agent["steps"][4]
        if not step5:
            return jsonify({"success": False, "error": "Agent has no step5"}), 400
        
        # Handle both old format (agent) and new format (prompt_file)
        agent_file = step5.get("agent") or step5.get("prompt_file")
        if not agent_file:
            return jsonify({"success": False, "error": "Step5 has no agent/prompt_file defined"}), 400
        
        agent_folder_name = agent.get("folder_name", "SEO")
        report_output_name = step5.get("report_name") or (step5.get("output", {}).get("path", "דוח שלב 5.md") if isinstance(step5.get("output"), dict) else "דוח שלב 5.md")
        
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Validate that step 4 report exists
        step4_report_name = agent.get("step4", {}).get("report_name", "דוח שלב 4.md")
        step4_report_path = output_folder / step4_report_name
        if not step4_report_path.exists():
            return jsonify({"success": False, "error": f"דוח שלב 4 לא נמצא. הרץ שלב 4 קודם!"}), 400
        
        # Build paths and save prompt for debugging (for both modes)
        agent_file_path = BASE_DIR / agent_file
        page_full_path = BASE_DIR / page_path
        report_full_path = output_folder / report_output_name
        
        # Determine agent type from folder name (step 5-6 are typically SEO only)
        # Use agent_folder_name directly instead of hardcoded type detection
        
        user_prompt_basic = f"קרא את קובץ ההוראות {agent_file_path} ואת קובץ ה-HTML: {page_full_path}. הסר עקבות AI. בסוף שמור את הדוח בנתיב: {report_full_path}"
        save_step_prompt(page_path, "step5", user_prompt_basic, agent_folder_name)
        
        command = f"@{agent_file} @{page_path}"
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor", 
                    "command": command,
                    "message": "Command copied to clipboard."
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command
                })
        else:
            # Claude Code mode
            global running_claude_process
            cmd = get_claude_command()
            api_key = ANTHROPIC_API_KEY
            
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            
            report_full_path = output_folder / report_output_name
            
            # Load keywords for preservation
            keywords_preservation = ""
            page_folder_path = get_page_folder(page_path)
            page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
            if page_info_path.exists():
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    if 'fetched_keywords' in page_info:
                        kw_list = page_info['fetched_keywords'].get('final_keywords', [])
                        if kw_list:
                            keywords_preservation = f"""

## מילות מפתח חשובות - אל תמחק!

המילים הבאות חייבות להישאר בתוכן: {', '.join(kw_list)}

בעת עריכת הקובץ, וודא שמילים אלה לא נמחקות!
"""
                            print(f"[Step5] Adding {len(kw_list)} keywords preservation to prompt")
                except Exception as e:
                    print(f"[Step5] Could not load keywords: {e}")
            
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path}. סרוק את הקובץ {page_full_path} והסר עקבות AI. ערוך את הקובץ ישירות עם כלי Edit (לא Write!).{keywords_preservation} בסוף חובה לשמור דוח בנתיב המדויק: {report_full_path}"
            
            # Save prompt for debugging
            save_step_prompt(page_path, "step5", user_prompt, agent_folder_name)
            
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            runner_script = TMP_FOLDER / "temp_run_claude.py"
            
            runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🤖 Claude Code Agent - שלב 5 (הסרת עקבות AI)")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📝 דוח יישמר ב: {report_full_path}")
log("")

prompt = """{user_prompt_escaped}"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"{BASE_DIR}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

log("🚀 מפעיל Claude Code...")
log("-" * 60)
log("")

# Open prompt file for stdin
prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Legacy endpoint
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")

# === STEP WEBHOOK - Notify step 5 completion for Full Auto ===
try:
    report_path = r"{report_full_path}"
    report_exists = os.path.exists(report_path)
    webhook_data = json_lib.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": 5,
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 5 webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
            
            with open(runner_script, 'w', encoding='utf-8') as f:
                f.write(runner_content)
            
            batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
            batch_path = TMP_FOLDER / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            set_page_running(page_path, agent_id, 5, running_claude_process.pid, full_auto=full_auto, total_steps=total_steps)
            
            print(f"[Step5] Running Claude Code AI removal for {page_path} (full_auto={full_auto})")
            
            return jsonify({
                "success": True,
                "mode": "claude",
                "page_path": page_path,
                "message": "Claude Code Step 5 running!"
            })
    except Exception as e:
        print(f"[Step5] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/step6', methods=['POST'])
def run_step6():
    """Run step 6 - AI debug (for six-step agents)"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        step5_report_path = data.get("step5_report_path")
        mode = data.get("mode", "cursor")
        full_auto = data.get("full_auto", False)  # Read full_auto from request
        total_steps = data.get("total_steps", 6)  # Read total_steps from request
        
        # === DUPLICATE CALL PROTECTION using COMPOSITE KEY ===
        normalized_path = page_path.replace('\\', '/')
        job_key = get_job_key(page_path, agent_id)
        
        # Check 1: In-memory using composite key
        current_info = running_pages.get(job_key)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= 6:
                print(f"[Step6] BLOCKED (memory): Step {running_step} already running for {job_key}")
                return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {running_step} already running", "blocked": True})
        
        # Check 2: File-based using composite key
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if job_key in saved_pages:
                    saved_step = saved_pages[job_key].get('step', 0)
                    if saved_step >= 6:
                        print(f"[Step6] BLOCKED (file): Step {saved_step} already running for {job_key}")
                        return jsonify({"success": True, "mode": mode, "page_path": page_path, "message": f"Step {saved_step} already running", "blocked": True})
        except Exception as e:
            print(f"[Step6] Warning: Could not check running_jobs.json: {e}")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # === SITE RESTRICTION VALIDATION ===
        page_site = get_page_site(page_path)
        if not is_agent_allowed_for_site(agent, page_site):
            error_msg = f"הסוכן '{agent.get('name', agent_id)}' לא מוגדר לאתר '{page_site}'"
            print(f"[Step6] BLOCKED (site restriction): {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 400
        
        # Check if agent has 6 steps
        step_count = len(agent.get("steps", []))
        for i in range(1, 10):
            if f"step{i}" in agent:
                step_count = max(step_count, i)
        
        # Dynamically check if agent has step 6
        if step_count < 6:
            return jsonify({"success": False, "error": "Agent has less than 6 steps"}), 400
        
        # Get step6 from either old format (step6) or new format (steps[5])
        step6 = agent.get("step6")
        if not step6 and agent.get("steps") and len(agent.get("steps", [])) >= 6:
            step6 = agent["steps"][5]
        if not step6:
            return jsonify({"success": False, "error": "Agent has no step6"}), 400
        
        # Handle both old format (agent) and new format (prompt_file)
        agent_file = step6.get("agent") or step6.get("prompt_file")
        if not agent_file:
            return jsonify({"success": False, "error": "Step6 has no agent/prompt_file defined"}), 400
        
        agent_folder_name = agent.get("folder_name", "SEO")
        report_output_name = step6.get("report_name") or (step6.get("output", {}).get("path", "דוח דיבאג AI.md") if isinstance(step6.get("output"), dict) else "דוח דיבאג AI.md")
        
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Validate that step 5 report exists
        step5_full = None
        if step5_report_path:
            step5_full = BASE_DIR / step5_report_path
            if not step5_full.exists():
                return jsonify({"success": False, "error": f"דוח שלב 5 לא נמצא. הרץ שלב 5 קודם!"}), 400
        
        # Build paths and save prompt for debugging (for both modes)
        agent_file_path = BASE_DIR / agent_file
        page_full_path = BASE_DIR / page_path
        report_full_path = output_folder / report_output_name
        
        # Determine agent type from folder name
        # Use agent_folder_name directly instead of hardcoded type detection
        
        user_prompt_basic = f"קרא את קובץ ההוראות {agent_file_path} ואת דוח שלב 5: {step5_full} ואת קובץ ה-HTML: {page_full_path}. בצע QA סופי. בסוף שמור את הדוח בנתיב: {report_full_path}"
        save_step_prompt(page_path, "step6", user_prompt_basic, agent_folder_name)
        
        command = f"@{agent_file} @{step5_report_path} @{page_path}"
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor", 
                    "command": command,
                    "message": "Command copied to clipboard."
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command
                })
        else:
            # Claude Code mode
            global running_claude_process
            cmd = get_claude_command()
            api_key = ANTHROPIC_API_KEY
            
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            step5_report_full = BASE_DIR / step5_report_path
            
            report_full_path = output_folder / report_output_name
            
            # Load keywords for preservation
            keywords_preservation = ""
            page_folder_path = get_page_folder(page_path)
            page_info_path = BASE_DIR / page_folder_path / 'page_info.json'
            if page_info_path.exists():
                try:
                    with open(page_info_path, 'r', encoding='utf-8') as f:
                        page_info = json.load(f)
                    if 'fetched_keywords' in page_info:
                        kw_list = page_info['fetched_keywords'].get('final_keywords', [])
                        if kw_list:
                            keywords_preservation = f"""

## מילות מפתח חשובות - אל תמחק!

המילים הבאות חייבות להישאר בתוכן: {', '.join(kw_list)}

בעת עריכת הקובץ, וודא שמילים אלה לא נמחקות!
"""
                            print(f"[Step6] Adding {len(kw_list)} keywords preservation to prompt")
                except Exception as e:
                    print(f"[Step6] Could not load keywords: {e}")
            
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת דוח שלב 5: {step5_report_full}. בדוק את הקובץ {page_full_path} שכל עקבות ה-AI הוסרו. ערוך את הקובץ ישירות עם כלי Edit אם צריך.{keywords_preservation} בסוף חובה לשמור דוח בנתיב המדויק: {report_full_path}"
            
            # Save prompt for debugging
            save_step_prompt(page_path, "step6", user_prompt, agent_folder_name)
            
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            runner_script = TMP_FOLDER / "temp_run_claude.py"
            
            runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🔍 Claude Code Agent - שלב 6 (דיבאג AI)")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📝 דוח יישמר ב: {report_full_path}")
log("")

prompt = """{user_prompt_escaped}"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"{BASE_DIR}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

log("🚀 מפעיל Claude Code...")
log("-" * 60)
log("")

# Open prompt file for stdin
prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Legacy endpoint
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")

# === STEP WEBHOOK - Notify step 6 completion for Full Auto ===
try:
    report_path = r"{report_full_path}"
    report_exists = os.path.exists(report_path)
    webhook_data = json_lib.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": 6,
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 6 webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
            
            with open(runner_script, 'w', encoding='utf-8') as f:
                f.write(runner_content)
            
            batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
            batch_path = TMP_FOLDER / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            set_page_running(page_path, agent_id, 6, running_claude_process.pid, full_auto=full_auto, total_steps=total_steps)
            
            print(f"[Step6] Running Claude Code AI debug for {page_path} (full_auto={full_auto})")
            
            return jsonify({
                "success": True,
                "mode": "claude",
                "page_path": page_path,
                "message": "Claude Code Step 6 running!"
            })
    except Exception as e:
        print(f"[Step6] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================
# COMBINED AUTO ENDPOINT - Run multiple agents in sequence
# =====================================================
@app.route('/api/workflow/combined', methods=['POST'])
def run_combined_auto():
    """Run multiple agents in sequence on a page.
    Each agent runs all its steps before the next agent starts."""
    try:
        data = request.json
        page_path = data.get("page_path")
        agent_queue = data.get("agent_queue", [])  # List of agent IDs
        
        if not page_path:
            return jsonify({"success": False, "error": "Missing page_path"}), 400
        
        if not agent_queue or len(agent_queue) == 0:
            return jsonify({"success": False, "error": "Empty agent queue"}), 400
        
        print(f"[Combined Auto] Starting queue for {page_path}: {agent_queue}")
        
        # Get the first agent
        first_agent_id = agent_queue[0]
        first_agent = get_agent_unified(first_agent_id)
        
        if not first_agent:
            return jsonify({"success": False, "error": f"Agent {first_agent_id} not found"}), 404
        
        # Calculate total steps for first agent
        total_steps = get_agent_step_count(first_agent)
        
        # Register the job with the full queue for tracking
        job_key = get_job_key(page_path, first_agent_id)
        
        # Store the queue in a separate tracking dict
        global combined_auto_queue
        if 'combined_auto_queue' not in globals():
            combined_auto_queue = {}
        
        combined_auto_queue[page_path.replace('\\', '/')] = {
            "agent_queue": agent_queue,
            "current_index": 0,
            "started": datetime.now().isoformat()
        }
        
        # Start the first agent's Full Auto
        trigger_step(page_path, first_agent_id, 1, total_steps)
        
        return jsonify({
            "success": True,
            "message": f"Started {first_agent.get('name', first_agent_id)}",
            "agent_queue": agent_queue,
            "total_agents": len(agent_queue)
        })
        
    except Exception as e:
        print(f"[Combined Auto] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# Global for tracking combined auto queues
combined_auto_queue = {}

# =====================================================
# GENERIC STEP ENDPOINT - Works for ANY step number
# =====================================================
@app.route('/api/workflow/step/<int:step_num>', methods=['POST'])
def run_step_generic(step_num):
    """Generic step runner for ANY step number.
    Uses composite key (page_path:agent_id) for duplicate protection.
    Supports parallel agent execution on the same page."""
    try:
        data = request.json
        page_path = data.get("page_path")
        agent_id = data.get("agent_id")
        full_auto = data.get("full_auto", False)
        total_steps = data.get("total_steps", step_num)
        
        if not page_path or not agent_id:
            return jsonify({"success": False, "error": "Missing page_path or agent_id"}), 400
        
        # === DUPLICATE CALL PROTECTION using COMPOSITE KEY ===
        normalized_path = page_path.replace('\\', '/')
        job_key = get_job_key(page_path, agent_id)
        
        # Check 1: In-memory running_pages
        current_info = running_pages.get(job_key)
        if current_info:
            running_step = current_info.get('step', 0)
            if running_step >= step_num:
                print(f"[Step{step_num}] BLOCKED: {job_key} already at step {running_step}")
                return jsonify({
                    "success": True,
                    "blocked": True,
                    "message": f"Step {running_step} already running",
                    "job_key": job_key
                })
        
        # Check 2: File-based persistence (survives server restart)
        try:
            jobs_file = BASE_DIR / "running_jobs.json"
            if jobs_file.exists():
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    saved_pages = json.load(f)
                if job_key in saved_pages:
                    saved_step = saved_pages[job_key].get('step', 0)
                    if saved_step >= step_num:
                        print(f"[Step{step_num}] BLOCKED (file): {job_key} already at step {saved_step}")
                        return jsonify({
                            "success": True,
                            "blocked": True,
                            "message": f"Step {saved_step} already running (from file)",
                            "job_key": job_key
                        })
        except Exception as e:
            print(f"[Step{step_num}] Warning: Could not check running_jobs.json: {e}")
        
        # Get agent configuration
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        # Check if agent has this step defined
        step_config = None
        if f"step{step_num}" in agent:
            step_config = agent[f"step{step_num}"]
        elif agent.get("steps") and len(agent.get("steps", [])) >= step_num:
            step_config = agent["steps"][step_num - 1]
        
        if not step_config:
            return jsonify({"success": False, "error": f"Agent has no step{step_num} defined"}), 400
        
        # Use trigger_step which has all the logic for running a step
        print(f"[Step{step_num}] Starting for {job_key} (full_auto={full_auto}, total_steps={total_steps})")
        
        # Run the step using the existing trigger_step function
        trigger_step(page_path, agent_id, step_num, total_steps)
        
        return jsonify({
            "success": True,
            "step": step_num,
            "page_path": page_path,
            "agent_id": agent_id,
            "job_key": job_key,
            "message": f"Step {step_num} started"
        })
        
    except Exception as e:
        print(f"[Step{step_num}] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/single', methods=['POST'])
def run_single_step():
    """Run a single-step agent"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        mode = data.get("mode", "cursor")
        
        agent = get_agent_unified(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent '{agent_id}' not found"}), 404
        
        if agent["type"] != "single-step":
            return jsonify({"success": False, "error": "Agent is not single-step"}), 400
        
        agent_file = agent["agent"]
        
        # Build command
        command = f"@{agent_file} @{page_path}"
        
        if mode == "cursor":
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(command)
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command,
                    "message": "Command copied to clipboard"
                })
            else:
                return jsonify({
                    "success": True,
                    "mode": "cursor",
                    "command": command
                })
        else:
            result = subprocess.run(
                [get_claude_command(), "-p", command],
                capture_output=True,
                text=True,
                cwd=str(BASE_DIR),
                timeout=300
            )
            
            return jsonify({
                "success": result.returncode == 0,
                "mode": "claude",
                "stdout": result.stdout,
                "stderr": result.stderr
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/continue', methods=['POST'])
def continue_conversation():
    """Continue Claude Code conversation with a correction/instruction"""
    try:
        global running_claude_process
        data = request.json
        page_path = data.get("page_path")
        correction = data.get("correction", "")
        
        if not page_path or not correction:
            return jsonify({"success": False, "error": "Missing page_path or correction"}), 400
        
        cmd = get_claude_command()
        api_key = ANTHROPIC_API_KEY
        
        # Escape for Python script
        correction_escaped = correction.replace("\\", "\\\\").replace('"', '\\"')
        page_path_escaped = page_path.replace("\\", "/")
        
        # Get log file for this page
        page_log_file = get_log_file_for_page(page_path)
        
        # Append to existing log
        append_live_log(page_path, "")
        append_live_log(page_path, "=" * 60)
        append_live_log(page_path, f"📝 המשך שיחה - תיקון חדש")
        append_live_log(page_path, "=" * 60)
        append_live_log(page_path, f"💬 {correction}")
        append_live_log(page_path, "")
        
        # Mark page as running
        set_page_running(page_path, "continue", 0)
        
        # Create runner script that continues the conversation
        runner_script = TMP_FOLDER / "temp_run_claude.py"
        
        runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("🔄 ממשיך שיחה עם Claude...")
log("-" * 60)
log("")

# Continue the conversation with --continue flag
claude_cmd = r"{cmd}"
correction = """{correction_escaped}"""

args = [
    claude_cmd,
    "--continue",  # Continue most recent conversation
    "-p",  # Print mode
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10",
    correction
]

process = subprocess.Popen(
    args,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

# Read streaming output
try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({{"page_path": "{page_path_escaped}"}}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {{e}}")
'''
        with open(runner_script, 'w', encoding='utf-8') as f:
            f.write(runner_content)
        
        batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
        batch_path = TMP_FOLDER / "temp_claude_run.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Open in legacy CMD
        running_claude_process = subprocess.Popen(
            [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
            cwd=str(BASE_DIR)
        )
        
        # Mark page as running with PID (continue uses step from previous or default to 1)
        current_step = running_pages.get(page_path, {}).get('step', 1)
        set_page_running(page_path, "continue", current_step, running_claude_process.pid)
        
        print(f"[Continue] Continuing conversation for {page_path}")
        
        return jsonify({
            "success": True,
            "message": "Continuing conversation..."
        })
    except Exception as e:
        print(f"[Continue] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/stop', methods=['POST'])
def stop_claude():
    """Stop a running Claude Code process.
    If page_path and agent_id are provided, stops only that specific job by PID.
    Otherwise, falls back to killing all Claude processes (legacy behavior)."""
    global running_claude_process
    try:
        data = request.json or {}
        page_path = data.get('page_path')
        agent_id = data.get('agent_id')
        
        # If specific job is requested, stop only that job by PID
        if page_path and agent_id:
            job_key = get_job_key(page_path, agent_id)
            job_info = running_pages.get(job_key)
            
            if job_info and job_info.get('pid'):
                pid = job_info['pid']
                print(f"[Stop] Stopping specific job: {job_key} (PID: {pid})")
                
                try:
                    # Kill specific process and its children
                    subprocess.run(f'taskkill /PID {pid} /T /F', shell=True, capture_output=True)
                except Exception as e:
                    print(f"[Stop] Error killing PID {pid}: {e}")
                
                # Remove from running_pages
                set_page_complete(page_path, agent_id)
                # Also unregister from Full Auto if applicable
                unregister_full_auto_job(page_path, agent_id)
                
                return jsonify({
                    "success": True,
                    "message": f"Job {job_key} stopped (PID: {pid})",
                    "job_key": job_key
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Job {job_key} not found or has no PID"
                }), 404
        
        # Legacy behavior: kill all Claude processes
        # Kill any running Claude Code processes by window title
        result = subprocess.run(
            'taskkill /FI "WINDOWTITLE eq ClaudeCodeAgent*" /F',
            shell=True,
            capture_output=True,
            text=True
        )
        
        # Also try to kill claude.exe directly
        subprocess.run(
            'taskkill /IM "claude.exe" /F',
            shell=True,
            capture_output=True
        )
        
        # Also try node processes related to claude
        subprocess.run(
            'taskkill /IM "node.exe" /FI "WINDOWTITLE eq ClaudeCodeAgent*" /F',
            shell=True,
            capture_output=True
        )
        
        running_claude_process = None
        
        print("[Stop] All Claude Code processes stopped")
        return jsonify({
            "success": True,
            "message": "All Claude Code processes stopped"
        })
    except Exception as e:
        print(f"[Stop] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/worklog', methods=['GET'])
def get_work_log():
    """Get the current work log content for a specific page and agent"""
    try:
        page_path = request.args.get('page', '')
        agent_id = request.args.get('agent_id', '')
        
        print(f"[Worklog] Request: page={page_path}, agent_id={agent_id}")
        
        if page_path and agent_id:
            # Use composite key log file (new system)
            log_file = get_log_file_for_job(page_path, agent_id)
            print(f"[Worklog] Using composite log file: {log_file}")
        elif page_path:
            # Try composite key first by checking running_pages
            job_key = None
            normalized_path = page_path.replace('\\', '/')
            for key, info in running_pages.items():
                if key.startswith(normalized_path + ':') or key == normalized_path:
                    job_key = key
                    break
            
            if job_key and ':' in job_key:
                # Extract agent_id from composite key
                parts = job_key.split(':')
                agent_id_from_key = parts[-1] if len(parts) > 1 else ''
                log_file = get_log_file_for_job(page_path, agent_id_from_key)
            else:
                # Fallback to legacy log file
                log_file = get_log_file_for_page(page_path)
        else:
            # Fallback: try to find any recent log file
            log_files = list(LIVE_LOGS_FOLDER.glob("*_log.txt"))
            if log_files:
                # Get most recently modified
                log_file = max(log_files, key=lambda f: f.stat().st_mtime)
            else:
                return jsonify({
                    "success": True,
                    "content": "",
                    "line_count": 0
                })
        
        print(f"[Worklog] Checking log file: {log_file}")
        if log_file.exists():
            # Read last N lines
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Parse and format the content for display
            lines = content.split('\n')
            # Keep last 200 lines for performance
            if len(lines) > 200:
                lines = lines[-200:]
            
            print(f"[Worklog] Found log with {len(lines)} lines")
            return jsonify({
                "success": True,
                "content": '\n'.join(lines),
                "line_count": len(lines),
                "log_file": log_file.name
            })
        else:
            print(f"[Worklog] Log file does not exist: {log_file}")
            return jsonify({
                "success": True,
                "content": "",
                "line_count": 0
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/worklog/page/<path:page_path>', methods=['DELETE'])
def delete_page_log(page_path):
    """Delete the work log file for a specific page"""
    try:
        log_file = get_log_file_for_page(page_path)
        if log_file.exists():
            log_file.unlink()
            print(f"[Log] Deleted log for {page_path}")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/worklog/clear', methods=['POST'])
def clear_work_log():
    """Clear the work log file for a specific page"""
    try:
        data = request.json or {}
        page_path = data.get('page', '')
        
        if page_path:
            log_file = get_log_file_for_page(page_path)
            if log_file.exists():
                log_file.unlink()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/worklog/all', methods=['GET'])
def get_all_work_logs():
    """Get status of all running jobs with their logs"""
    try:
        results = []
        
        for page_path, info in running_pages.items():
            log_file = get_log_file_for_page(page_path)
            log_content = ""
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.read().split('\n')
                    # Get last 5 lines as preview
                    log_content = '\n'.join(lines[-5:])
            
            results.append({
                "page_path": page_path,
                "page_name": Path(page_path).stem,
                "agent_id": info.get("agent_id"),
                "step": info.get("step"),
                "started": info.get("started"),
                "log_preview": log_content
            })
        
        return jsonify({
            "success": True,
            "running_jobs": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/workflow/status', methods=['GET'])
def get_claude_status():
    """Check if Claude is currently running"""
    global running_claude_process
    is_running = running_claude_process is not None and running_claude_process.poll() is None
    return jsonify({
        "running": is_running
    })

# ============ API Routes - Status & Monitoring ============

# Active jobs tracking - key is now COMPOSITE: "page_path:agent_id"
active_jobs = {}
running_pages = {}  # Track which jobs are currently running (key: page_path:agent_id)
job_locks = {}  # In-memory locks for preventing duplicate job runs

def get_job_key(page_path, agent_id):
    """Generate composite key for job tracking: page_path:agent_id"""
    normalized_path = page_path.replace('\\', '/')
    return f"{normalized_path}:{agent_id}"

# ============ JOB LOCK SYSTEM - Prevents duplicate runs ============
import threading

# Create locks folder for file-based locking (inside tmp folder)
LOCKS_FOLDER = TMP_FOLDER / "job_locks"
LOCKS_FOLDER.mkdir(parents=True, exist_ok=True)

def acquire_job_lock(page_path, agent_id):
    """Try to acquire exclusive lock for this job.
    Returns True if lock acquired, False if job is already running.
    Uses both in-memory check and file-based lock for robustness."""
    job_key = get_job_key(page_path, agent_id)
    
    # Check 1: In-memory running_pages
    if job_key in running_pages:
        print(f"[JobLock] BLOCKED: {job_key} already in running_pages")
        return False
    
    # Check 2: File-based lock (survives process crashes)
    safe_key = job_key.replace('/', '_').replace('\\', '_').replace(':', '_')
    lock_file = LOCKS_FOLDER / f"{safe_key}.lock"
    
    try:
        # Try to create lock file exclusively
        if lock_file.exists():
            # Check if lock is stale (older than 30 minutes)
            try:
                mtime = lock_file.stat().st_mtime
                age = time.time() - mtime
                if age > 1800:  # 30 minutes
                    print(f"[JobLock] Removing stale lock for {job_key} (age: {age:.0f}s)")
                    lock_file.unlink()
                else:
                    print(f"[JobLock] BLOCKED: {job_key} has active lock file")
                    return False
            except:
                pass
        
        # Create lock file with PID and timestamp
        with open(lock_file, 'w', encoding='utf-8') as f:
            f.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
        
        print(f"[JobLock] Acquired lock for {job_key}")
        return True
    except Exception as e:
        print(f"[JobLock] Error acquiring lock for {job_key}: {e}")
        return False

def release_job_lock(page_path, agent_id):
    """Release the job lock when job completes."""
    job_key = get_job_key(page_path, agent_id)
    safe_key = job_key.replace('/', '_').replace('\\', '_').replace(':', '_')
    lock_file = LOCKS_FOLDER / f"{safe_key}.lock"
    
    try:
        if lock_file.exists():
            lock_file.unlink()
            print(f"[JobLock] Released lock for {job_key}")
    except Exception as e:
        print(f"[JobLock] Error releasing lock for {job_key}: {e}")

def cleanup_stale_locks():
    """Clean up lock files older than 30 minutes (called on startup)"""
    try:
        for lock_file in LOCKS_FOLDER.glob("*.lock"):
            try:
                mtime = lock_file.stat().st_mtime
                age = time.time() - mtime
                if age > 1800:  # 30 minutes
                    lock_file.unlink()
                    print(f"[JobLock] Cleaned up stale lock: {lock_file.name}")
            except:
                pass
    except Exception as e:
        print(f"[JobLock] Error cleaning up locks: {e}")

# Clean up stale locks on startup
cleanup_stale_locks()

def set_page_running(page_path, agent_id, step, pid=None, full_auto=False, total_steps=4, job_uuid=None):
    """Mark a job as running using composite key (page_path:agent_id)"""
    normalized_path = page_path.replace('\\', '/')
    job_key = get_job_key(page_path, agent_id)
    print(f"[DEBUG] set_page_running: job_key='{job_key}' full_auto={full_auto} step={step}")
    running_pages[job_key] = {
        "page_path": normalized_path,  # Store original path for reference
        "agent_id": agent_id,
        "step": step,
        "started": datetime.now().isoformat(),
        "pid": pid,  # Store process ID for checking if still alive
        "full_auto": full_auto,  # True if running in Full Auto mode
        "total_steps": total_steps,  # Total steps for this agent
        "job_uuid": job_uuid  # UUID for temp file cleanup
    }
    # Save to file for persistence
    with open(BASE_DIR / "running_jobs.json", 'w', encoding='utf-8') as f:
        json.dump(running_pages, f, ensure_ascii=False)
    print(f"[Status] Job marked as running: {job_key} (step {step}, pid={pid}, full_auto={full_auto})")
    print(f"[Status] Running jobs: {list(running_pages.keys())}")

def cleanup_temp_files(job_uuid):
    """Clean up temp files for a specific job UUID"""
    if not job_uuid:
        return
    
    try:
        # Clean up temp files with this UUID
        for ext in ['.py', '.bat', '.job', '.md']:
            temp_file = TMP_FOLDER / f"temp_run_{job_uuid}{ext}"
            if temp_file.exists():
                try:
                    temp_file.unlink()
                    print(f"[Cleanup] Deleted temp file: {temp_file.name}")
                except Exception as e:
                    print(f"[Cleanup] Error deleting {temp_file.name}: {e}")
    except Exception as e:
        print(f"[Cleanup] Error cleaning temp files for job {job_uuid}: {e}")

def set_page_complete(page_path, agent_id=None):
    """Mark a job as complete using composite key"""
    normalized_path = page_path.replace('\\', '/')
    
    # If agent_id provided, use composite key
    if agent_id:
        job_key = get_job_key(page_path, agent_id)
        if job_key in running_pages:
            # Get job_uuid for cleanup before removing
            job_uuid = running_pages[job_key].get('job_uuid')
            
            del running_pages[job_key]
            with open(BASE_DIR / "running_jobs.json", 'w', encoding='utf-8') as f:
                json.dump(running_pages, f, ensure_ascii=False)
            # Release the job lock
            release_job_lock(page_path, agent_id)
            # Clean up temp files
            cleanup_temp_files(job_uuid)
            print(f"[Status] Job marked complete: {job_key}")
            return
    
    # Backward compatibility: search for any job with this page_path
    keys_to_remove = [k for k in running_pages.keys() if k.startswith(normalized_path + ":") or k == normalized_path]
    for key in keys_to_remove:
        # Get job_uuid for cleanup before removing
        job_uuid = running_pages[key].get('job_uuid') if key in running_pages else None
        del running_pages[key]
        cleanup_temp_files(job_uuid)
    if keys_to_remove:
        with open(BASE_DIR / "running_jobs.json", 'w', encoding='utf-8') as f:
            json.dump(running_pages, f, ensure_ascii=False)
        print(f"[Status] Jobs marked complete: {keys_to_remove}")

def clear_page_running(page_path, agent_id=None):
    """Remove a job from running status (alias for set_page_complete)"""
    set_page_complete(page_path, agent_id)

def load_running_pages():
    """Load running jobs from file and verify processes are still running.
    Jobs are now keyed by composite key: page_path:agent_id"""
    global running_pages
    jobs_file = BASE_DIR / "running_jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                loaded_pages = json.load(f)
            
            # Check each loaded job - only keep if not completed
            running_pages = {}
            for job_key, info in loaded_pages.items():
                # Extract page_path and agent_id from composite key or info
                if ':' in job_key:
                    # New composite key format: page_path:agent_id
                    parts = job_key.rsplit(':', 1)
                    page_path = parts[0]
                    agent_id = parts[1] if len(parts) > 1 else info.get('agent_id', 'unknown')
                else:
                    # Old format - just page_path (backward compatibility)
                    page_path = job_key
                    agent_id = info.get('agent_id', 'unknown')
                    # Convert to new format
                    job_key = get_job_key(page_path, agent_id)
                
                # Get log file for this job
                log_file = get_log_file_for_job(page_path, agent_id)
                should_keep = False
                
                # For Full Auto mode - always keep if not all steps completed
                is_full_auto = info.get('full_auto', False)
                current_step = info.get('step', 1)
                total_steps = info.get('total_steps', 4)
                
                if is_full_auto and current_step < total_steps:
                    # Full Auto not finished - keep it even if current step completed
                    should_keep = True
                    print(f"[Startup] Full Auto job {job_key} - step {current_step}/{total_steps} - keeping")
                elif log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        
                        # If no completion marker, check if recent
                        if '🏁 סיום!' not in content and '✅ Claude סיים!' not in content:
                            mtime = log_file.stat().st_mtime
                            age = time.time() - mtime
                            if age < 300:  # 5 minutes
                                should_keep = True
                                print(f"[Startup] Job {job_key} might still be running (log age: {age:.0f}s)")
                        else:
                            print(f"[Startup] Job {job_key} already completed")
                    except:
                        pass
                
                if should_keep:
                    # Ensure info has page_path and agent_id
                    info['page_path'] = page_path
                    info['agent_id'] = agent_id
                    running_pages[job_key] = info
                else:
                    print(f"[Startup] Removing stale job: {job_key}")
            
            # Save the cleaned up list
            if running_pages != loaded_pages:
                with open(jobs_file, 'w', encoding='utf-8') as f:
                    json.dump(running_pages, f, ensure_ascii=False)
            print(f"[Startup] Loaded {len(running_pages)} running jobs")
        except Exception as e:
            print(f"[Startup] Error loading running pages: {e}")
            running_pages = {}
    else:
        running_pages = {}

def clear_all_running_pages():
    """Clear all running pages (manual reset only)"""
    global running_pages
    running_pages = {}
    jobs_file = BASE_DIR / "running_jobs.json"
    if jobs_file.exists():
        jobs_file.unlink()

def is_process_running(pid, page_path=None, agent_id=None):
    """Check if a process is still running by checking log file activity.
    Uses new log file format with agent_id for parallel job support."""
    # First check: is the log file being updated recently?
    if page_path:
        # Use new format with agent_id if available, fallback to old format
        if agent_id:
            log_file = get_log_file_for_job(page_path, agent_id)
        else:
            log_file = get_log_file_for_page(page_path)
        
        # Also check old format as fallback
        old_log_file = get_log_file_for_page(page_path)
        
        print(f"[Check] Checking log file: {log_file}, exists: {log_file.exists()}")
        
        # Check new format first, then old format
        for lf in [log_file, old_log_file]:
            if lf.exists():
                try:
                    # Check if log was modified in the last 60 seconds (increased from 30)
                    mtime = lf.stat().st_mtime
                    age = time.time() - mtime
                    print(f"[Check] Log age: {age:.1f} seconds")
                    if age < 300:  # Active in last 5 minutes (increased from 60s to be safe)
                        return True
                except Exception as e:
                    print(f"[Check] Error checking log: {e}")
    
    # Second check: PID (as backup)
    if pid:
        try:
            import psutil
            exists = psutil.pid_exists(pid)
            print(f"[Check] PID {pid} exists: {exists}")
            return exists
        except ImportError:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                pass
    
    return False

# On startup, LOAD running pages (don't clear - process might still be running)
load_running_pages()

@app.route('/api/status/running', methods=['GET'])
def get_running_status():
    """Get status of all running jobs, check if processes completed.
    Jobs are keyed by composite key: page_path:agent_id"""
    global running_pages
    
    # Check each running job - only remove if log shows completion
    # CRITICAL: For Full Auto jobs, DON'T remove until ALL steps are complete!
    dead_jobs = []
    for job_key, info in running_pages.items():
        # Extract page_path and agent_id from info or key
        page_path = info.get('page_path', job_key.rsplit(':', 1)[0] if ':' in job_key else job_key)
        agent_id = info.get('agent_id', job_key.rsplit(':', 1)[1] if ':' in job_key else 'unknown')
        
        # === FULL AUTO PROTECTION ===
        # For Full Auto jobs, only remove when ALL steps completed
        is_full_auto = info.get('full_auto', False)
        current_step = info.get('step', 1)
        total_steps = info.get('total_steps', 4)
        
        if is_full_auto and current_step < total_steps:
            # Full Auto still has more steps - DON'T remove even if current step completed!
            # The webhook handler will update the step number when next step starts
            print(f"[Status] Full Auto job {job_key} - step {current_step}/{total_steps} - keeping")
            continue  # Skip this job, don't add to dead_jobs
        
        # Try new log file format first, fall back to old format
        log_file = get_log_file_for_job(page_path, agent_id)
        if not log_file.exists():
            log_file = get_log_file_for_page(page_path)  # Fallback for old format
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Check if completed (has completion marker)
                if '🏁 סיום!' in content or '✅ Claude סיים!' in content:
                    # For Full Auto on last step, only remove if truly done
                    if is_full_auto and current_step >= total_steps:
                        dead_jobs.append(job_key)
                        print(f"[Status] Full Auto COMPLETED (all {total_steps} steps done): {job_key}")
                    elif not is_full_auto:
                        dead_jobs.append(job_key)
                        print(f"[Status] Job {job_key} COMPLETED (found completion marker)")
                    # If Full Auto and not last step - DON'T remove (already handled by continue above)
                else:
                    # Check last modification time - if no update for 5 minutes, consider dead
                    # But for Full Auto, be more lenient (10 minutes)
                    mtime = log_file.stat().st_mtime
                    age = time.time() - mtime
                    timeout = 600 if is_full_auto else 300  # 10 min for Full Auto, 5 min for regular
                    if age > timeout:
                        dead_jobs.append(job_key)
                        print(f"[Status] Job {job_key} TIMEOUT (no update for {age:.0f}s)")
            except Exception as e:
                print(f"[Status] Error reading log for {job_key}: {e}")
    
    # Remove completed/dead jobs from running_pages using composite key
    for job_key in dead_jobs:
        if job_key in running_pages:
            del running_pages[job_key]
    
    if dead_jobs:
        with open(BASE_DIR / "running_jobs.json", 'w', encoding='utf-8') as f:
            json.dump(running_pages, f, ensure_ascii=False)
    
    return jsonify({"success": True, "running": running_pages})

@app.route('/api/status/clear-all', methods=['POST'])
def clear_all_status():
    """Clear all running status and logs (manual reset)"""
    clear_all_running_pages()
    # Also clear all log files
    if LIVE_LOGS_FOLDER.exists():
        for log_file in LIVE_LOGS_FOLDER.glob("*.txt"):
            try:
                log_file.unlink()
            except:
                pass
    print("[Status] All running status and logs cleared")
    return jsonify({"success": True, "message": "All status cleared"})

@app.route('/api/status/pages', methods=['GET'])
def get_pages_status():
    """Get status for all pages based on selected agent (new folder structure)"""
    agent_id = request.args.get('agent', '')
    status = {}
    
    # Get agent config - try agents folder first, then config.json
    agent = get_agent_by_id(agent_id) if agent_id else {}
    if not agent:
        agent = config["agents"].get(agent_id, {})
    
    agent_folder_name = agent.get("folder_name") or agent.get("name") or "שיווק אטומי"
    
    # DYNAMIC: Get step count and report names from agent config
    step_count = get_agent_step_count(agent)
    report_names = get_agent_report_names(agent, step_count)
    
    print(f"[get_pages_status] Agent: {agent_id}, folder: {agent_folder_name}, steps: {step_count}, reports: {report_names}")
    
    # Check each page using the new folder structure
    # Support both dict (new multi-site) and array (legacy) formats
    editable = config["paths"]["editable_pages"]
    if isinstance(editable, dict):
        folders = list(editable.values())
    else:
        folders = editable
    
    for folder in folders:
        folder_path = BASE_DIR / folder
        if folder_path.exists():
            for page_folder in folder_path.iterdir():
                if page_folder.is_dir():
                    page_name = page_folder.name
                    # Find the HTML file in the page folder
                    html_files = list(page_folder.glob("*.html"))
                    main_html = [f for f in html_files if "מתוקנת" not in f.name and "סופית" not in f.name]
                    if not main_html:
                        continue
                    
                    page_path = str(main_html[0].relative_to(BASE_DIR))
                    agent_folder = page_folder / agent_folder_name
                    
                    # DYNAMIC: Check files in agent folder for all steps
                    step_status = {}
                    has_any_report = False
                    
                    for i, report_name in enumerate(report_names):
                        step_num = i + 1
                        if report_name:
                            exists = (agent_folder / report_name).exists()
                            if step_num == 1:
                                step_status["hasReport"] = exists
                            step_status[f"hasStep{step_num}Report"] = exists
                            if exists:
                                has_any_report = True
                    
                    if has_any_report:
                        status[page_path] = step_status
    
    return jsonify({"success": True, "status": status})

def get_agent_step_count(agent):
    """Dynamically get step count from agent config"""
    # Try new format first: agent.steps[]
    if agent.get("steps") and isinstance(agent.get("steps"), list):
        return len(agent["steps"])
    # Old format: count stepX keys
    count = 0
    for i in range(1, 20):  # Support up to 20 steps
        if agent.get(f"step{i}"):
            count = i
    return count if count > 0 else 1

def get_agent_report_names(agent, max_steps):
    """Dynamically get report names for all steps of an agent"""
    report_names = []
    for i in range(1, max_steps + 1):
        step_key = f"step{i}"
        if agent.get("steps") and len(agent.get("steps", [])) >= i:
            # New format: steps[i-1].output.path
            step_config = agent["steps"][i - 1]
            output = step_config.get("output", {})
            if isinstance(output, dict):
                report_names.append(output.get("path", f"דוח שלב {i}.md"))
            else:
                report_names.append(step_config.get("output_name", f"דוח שלב {i}.md"))
        elif agent.get(step_key):
            # Old format: stepX.output_name or stepX.report_name
            step_config = agent[step_key]
            report_names.append(
                step_config.get("output_name") or 
                step_config.get("report_name") or 
                f"דוח שלב {i}.md"
            )
        else:
            report_names.append(f"דוח שלב {i}.md")
    return report_names

@app.route('/api/status/multi-agent', methods=['GET'])
def get_multi_agent_status():
    """Get status for ALL agents for each page (for multi-agent sidebar display).
    Dynamically loads ALL agents from agents folder and config."""
    status = {}
    
    # DYNAMICALLY load ALL agents from folder and config
    agents_to_check = {}
    
    # Load from agents folder (new dynamic agents)
    agents_folder = BASE_DIR / "agents"
    if agents_folder.exists():
        for agent_file in agents_folder.glob("*.json"):
            try:
                with open(agent_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                agent_id = agent_file.stem  # filename without extension
                agents_to_check[agent_id] = agent_data
            except Exception as e:
                print(f"[Multi-Agent Status] Error loading agent {agent_file}: {e}")
    
    # Also include agents from config.json for backward compatibility
    if config.get("agents"):
        for agent_id, agent_data in config["agents"].items():
            if agent_id not in agents_to_check:
                agents_to_check[agent_id] = agent_data
    
    # Check each page using the new folder structure
    # Support both dict (new multi-site) and array (legacy) formats
    editable = config["paths"]["editable_pages"]
    if isinstance(editable, dict):
        folders = list(editable.values())
    else:
        folders = editable
    
    for folder in folders:
        folder_path = BASE_DIR / folder
        if folder_path.exists():
            for page_folder in folder_path.iterdir():
                if page_folder.is_dir():
                    page_name = page_folder.name
                    # Find the HTML file in the page folder
                    html_files = list(page_folder.glob("*.html"))
                    main_html = [f for f in html_files if "מתוקנת" not in f.name and "סופית" not in f.name]
                    if not main_html:
                        continue
                    
                    page_path = str(main_html[0].relative_to(BASE_DIR))
                    page_status = {}
                    
                    # Check status for each agent DYNAMICALLY
                    for agent_id, agent in agents_to_check.items():
                        # Get folder name dynamically from agent config
                        agent_folder_name = agent.get("folder_name") or agent.get("name") or agent_id
                        agent_folder = page_folder / agent_folder_name
                        
                        # Get step count dynamically
                        max_steps = get_agent_step_count(agent)
                        
                        # Get report names dynamically
                        report_names = get_agent_report_names(agent, max_steps)
                        
                        # Count completed steps
                        completed_steps = 0
                        for i, report_name in enumerate(report_names):
                            if report_name and (agent_folder / report_name).exists():
                                completed_steps = i + 1
                        
                        page_status[agent_id] = {
                            "maxSteps": max_steps,
                            "completedSteps": completed_steps,
                            "agentName": agent.get("name", agent_id)
                        }
                    
                    # Check for backup status
                    backup_meta_path = page_folder / f"{page_name}_backup_meta.json"
                    # Also check old naming convention
                    if not backup_meta_path.exists():
                        backup_meta_path = page_folder / "wp_backup_meta.json"
                    
                    if backup_meta_path.exists():
                        try:
                            with open(backup_meta_path, 'r', encoding='utf-8') as f:
                                backup_meta = json.load(f)
                            page_status["backup"] = {
                                "exists": True,
                                "fetched_at": backup_meta.get("fetched_at", "")
                            }
                        except:
                            page_status["backup"] = {"exists": True, "fetched_at": ""}
                    else:
                        page_status["backup"] = {"exists": False}
                    
                    if page_status:
                        status[page_path] = page_status
    
    return jsonify({"success": True, "status": status})

@app.route('/api/status/completed-pages', methods=['GET'])
def get_completed_pages():
    """Get pages that have completed (have log files with completion marker)"""
    completed = {}
    
    if LIVE_LOGS_FOLDER.exists():
        for log_file in LIVE_LOGS_FOLDER.glob("*_log.txt"):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Check if log shows completion
                if '🏁 סיום!' in content or '✅ Claude סיים!' in content:
                    # Extract page name from log filename
                    page_name = log_file.stem.replace('_log', '')
                    
                    # Determine which step was completed
                    step = 1
                    if 'שלב 2' in content or 'Step 2' in content or 'תיקונים' in content:
                        step = 2
                    
                    # Find matching page path
                    # Support both dict (new multi-site) and array (legacy) formats
                    editable = config["paths"]["editable_pages"]
                    folders_to_check = list(editable.values()) if isinstance(editable, dict) else editable
                    for folder in folders_to_check:
                        possible_path = f"{folder}/{page_name}.html"
                        if (BASE_DIR / possible_path).exists():
                            completed[possible_path] = {
                                "completed_at": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
                                "step": step
                            }
                            break
            except:
                pass
    
    return jsonify({"success": True, "completed": completed})

@app.route('/api/status/complete', methods=['POST'])
def mark_complete():
    """Mark a page as complete"""
    data = request.json
    page_path = data.get("page_path")
    if page_path:
        set_page_complete(page_path)
        print(f"[Status] Page marked complete: {page_path}")
    return jsonify({"success": True})

# Track last webhook trigger time to prevent loops/duplicate triggers
# Structure: { "normalized_path:step_num": timestamp }
webhook_trigger_history = {}

@app.route('/api/step/complete', methods=['POST'])
def step_complete():
    """Webhook called by runner script when Claude Code completes a step"""
    global step_events, webhook_trigger_history
    data = request.json
    page_path = data.get('page_path')
    agent_id = data.get('agent_id')
    step_raw = data.get('step')
    status = data.get('status', 'success')  # "success" or "error"
    
    # Ensure step is an integer
    try:
        step = int(step_raw)
    except (TypeError, ValueError):
        step = step_raw  # Keep as is if can't convert
    
    event = {
        'page_path': page_path,
        'agent_id': agent_id,
        'step': step,
        'status': status,
        'timestamp': time.time()
    }
    
    # Store for SSE subscribers - use composite key
    key = f"{page_path}:{agent_id}"
    step_events[key] = event
    
    # Log to file for debugging
    log_file = BASE_DIR / "webhook_debug.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{datetime.now().isoformat()}] Webhook received\n")
        f.write(f"  page_path: {page_path}\n")
        f.write(f"  agent_id: {agent_id}\n")
        f.write(f"  step_raw: {step_raw} (type: {type(step_raw).__name__})\n")
        f.write(f"  step: {step} (type: {type(step).__name__})\n")
        f.write(f"  status: {status}\n")
    
    print(f"[Webhook] {agent_id} step {step} {status} for {page_path}")
    
    # === FULL AUTO: Trigger next step automatically ===
    # Check if this job is running in Full Auto mode
    # Use COMPOSITE KEY for lookup: page_path:agent_id
    normalized_path = page_path.replace('\\', '/')
    job_key = get_job_key(page_path, agent_id)
    print(f"[Webhook DEBUG] Looking for job_key: '{job_key}'")
    print(f"[Webhook DEBUG] running_pages keys: {list(running_pages.keys())}")
    
    # Log to file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"  job_key: {job_key}\n")
        f.write(f"  running_pages keys: {list(running_pages.keys())}\n")
    
    page_info = running_pages.get(job_key)
    if page_info:
        print(f"[Webhook DEBUG] Found job_info: {page_info}")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"  job_info: {page_info}\n")
    else:
        print(f"[Webhook DEBUG] Job NOT found in running_pages, checking full_auto_jobs...")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"  WARNING: Job NOT found in running_pages, checking full_auto_jobs.json...\n")
        
        # === FALLBACK: Check full_auto_jobs.json ===
        try:
            full_auto_file = BASE_DIR / "full_auto_jobs.json"
            if full_auto_file.exists():
                with open(full_auto_file, 'r', encoding='utf-8') as f:
                    full_auto_jobs = json.load(f)
                if job_key in full_auto_jobs:
                    job_data = full_auto_jobs[job_key]
                    page_info = {
                        'page_path': job_data.get('page_path'),
                        'agent_id': job_data.get('agent_id'),
                        'step': job_data.get('current_step', 1),
                        'full_auto': True,  # If it's in full_auto_jobs, it's definitely Full Auto
                        'total_steps': job_data.get('total_steps', 4)
                    }
                    print(f"[Webhook DEBUG] RECOVERED job_info from full_auto_jobs: {page_info}")
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"  RECOVERED from full_auto_jobs: {page_info}\n")
        except Exception as e:
            print(f"[Webhook DEBUG] Error reading full_auto_jobs: {e}")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  ERROR reading full_auto_jobs: {e}\n")
    
    if page_info and page_info.get('full_auto') and status == 'success':
        current_step = step
        total_steps = page_info.get('total_steps', 4)
        next_step = current_step + 1
        
        # === DEBOUNCE CHECK ===
        # Check if we already triggered this step for this job recently
        # Use composite key with agent_id to support parallel agents
        trigger_key = f"{job_key}:{next_step}"
        last_trigger = webhook_trigger_history.get(trigger_key, 0)
        now = time.time()
        
        # If triggered less than 5 minutes ago, BLOCK IT
        if now - last_trigger < 300:
            msg = f"[Full Auto] DEBOUNCE: Blocked duplicate trigger for {job_key} step {next_step}. Last trigger: {int(now - last_trigger)}s ago."
            print(msg)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  {msg}\n")
            return jsonify({"success": True, "event": event, "status": "debounced"})
        
        # Update trigger history
        webhook_trigger_history[trigger_key] = now
        
        # Check if next step is already running or completed
        running_step = page_info.get('step', 0)
        # If running_step is greater than current_step, it means the next step (or further)
        # has already been triggered (e.g., by the backup mechanism)
        if running_step >= next_step:
            msg = f"[Full Auto] SKIP: Step {next_step} already active (running: {running_step})"
            print(msg)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  {msg}\n")
            # Update event to reflect skip
            event['skipped'] = True
            event['reason'] = f"Step {next_step} already active"
            return jsonify({"success": True, "event": event, "status": "skipped"})
        
        print(f"[Full Auto] Step {current_step} completed for {job_key}. Total: {total_steps}. Next: {next_step}")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"  [FULL AUTO] job_key={job_key}, current_step={current_step}, total_steps={total_steps}, next_step={next_step}\n")
        
        if next_step <= total_steps:
            # Schedule next step after a short delay
            import threading
            def run_next_step():
                time.sleep(5)  # Wait 5 seconds before starting next step
                
                # Double check before triggering - race condition protection
                # Re-read job info to see if anything changed in the last 5 seconds
                current_info = running_pages.get(job_key)
                if current_info and current_info.get('step', 0) >= next_step:
                    print(f"[Full Auto] Aborting scheduled step {next_step} for {job_key} - already started!")
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"  [FULL AUTO] Abort: Step {next_step} started during delay\n")
                    return
                
                # Triple Check: read running_jobs.json directly to be sure
                try:
                    jobs_file = BASE_DIR / "running_jobs.json"
                    if jobs_file.exists():
                        with open(jobs_file, 'r', encoding='utf-8') as f:
                            saved_running_pages = json.load(f)
                        if job_key in saved_running_pages:
                             saved_step = saved_running_pages[job_key].get('step', 0)
                             if saved_step >= next_step:
                                 print(f"[Full Auto] (File Check) Step {saved_step} already running for {job_key}, aborting schedule")
                                 with open(log_file, 'a', encoding='utf-8') as f:
                                     f.write(f"  [FULL AUTO] Abort: Step {saved_step} found in running_jobs.json\n")
                                 return
                except Exception as e:
                    print(f"[Full Auto] Error checking running_jobs.json: {e}")

                print(f"[Full Auto] Triggering step {next_step} for {job_key}")
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"  [FULL AUTO] Triggering step {next_step}\n")
                trigger_step(page_path, agent_id, next_step, total_steps)
            
            thread = threading.Thread(target=run_next_step)
            thread.daemon = True
            thread.start()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  [FULL AUTO] Thread started for step {next_step}\n")
        else:
            print(f"[Full Auto] All {total_steps} steps completed for {page_path}!")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  [FULL AUTO] All {total_steps} steps completed!\n")
            
            # Check if there's a combined auto queue for this page
            normalized_path = page_path.replace('\\', '/')
            if normalized_path in combined_auto_queue:
                queue_info = combined_auto_queue[normalized_path]
                current_index = queue_info.get('current_index', 0)
                agent_queue = queue_info.get('agent_queue', [])
                
                next_index = current_index + 1
                
                if next_index < len(agent_queue):
                    # There are more agents in the queue
                    next_agent_id = agent_queue[next_index]
                    next_agent = get_agent_unified(next_agent_id)
                    
                    if next_agent:
                        next_total_steps = get_agent_step_count(next_agent)
                        
                        print(f"[Combined Auto] Starting next agent: {next_agent_id} ({next_index + 1}/{len(agent_queue)})")
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"  [COMBINED AUTO] Starting next agent: {next_agent_id}\n")
                        
                        # Update queue index
                        combined_auto_queue[normalized_path]['current_index'] = next_index
                        
                        # Wait a bit before starting next agent
                        import threading
                        def start_next_agent():
                            time.sleep(3)
                            trigger_step(page_path, next_agent_id, 1, next_total_steps)
                        
                        thread = threading.Thread(target=start_next_agent)
                        thread.daemon = True
                        thread.start()
                    else:
                        print(f"[Combined Auto] Agent {next_agent_id} not found!")
                        set_page_complete(page_path)
                        del combined_auto_queue[normalized_path]
                else:
                    # All agents in queue completed
                    print(f"[Combined Auto] All {len(agent_queue)} agents completed for {page_path}!")
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"  [COMBINED AUTO] All {len(agent_queue)} agents completed!\n")
                    set_page_complete(page_path)
                    del combined_auto_queue[normalized_path]
            else:
                # No combined queue - check if agent has chain.next_agent
                current_agent = get_agent_unified(agent_id)
                if current_agent and current_agent.get('chain', {}).get('enabled'):
                    next_agent_id = current_agent.get('chain', {}).get('next_agent')
                    if next_agent_id:
                        next_agent = get_agent_unified(next_agent_id)
                        if next_agent:
                            # Check if next agent is allowed for this site
                            page_site = get_page_site(page_path)
                            if is_agent_allowed_for_site(next_agent, page_site):
                                next_total_steps = get_agent_step_count(next_agent)
                                
                                print(f"[Chain Auto] Starting chained agent: {next_agent_id} for {page_path}")
                                with open(log_file, 'a', encoding='utf-8') as f:
                                    f.write(f"  [CHAIN AUTO] Starting chained agent: {next_agent_id}\n")
                                
                                import threading
                                def start_chained_agent():
                                    time.sleep(3)
                                    trigger_step(page_path, next_agent_id, 1, next_total_steps)
                                
                                thread = threading.Thread(target=start_chained_agent)
                                thread.daemon = True
                                thread.start()
                            else:
                                print(f"[Chain Auto] Agent {next_agent_id} not allowed for site {page_site}")
                                set_page_complete(page_path)
                        else:
                            print(f"[Chain Auto] Next agent {next_agent_id} not found!")
                            set_page_complete(page_path)
                    else:
                        set_page_complete(page_path)
                else:
                    # No chain config, just mark complete
                    set_page_complete(page_path)
    else:
        # Log why Full Auto didn't trigger
        with open(log_file, 'a', encoding='utf-8') as f:
            if not page_info:
                f.write(f"  [NO FULL AUTO] page_info is None\n")
            elif not page_info.get('full_auto'):
                f.write(f"  [NO FULL AUTO] full_auto is False or missing in page_info\n")
            elif status != 'success':
                f.write(f"  [NO FULL AUTO] status is '{status}', not 'success'\n")
    
    return jsonify({"success": True, "event": event})

# ============ Full Auto Backup Mechanism ============
# This mechanism checks for report files and triggers next steps
# even if the webhook didn't work or running_pages was cleared

full_auto_jobs = {}  # Track Full Auto jobs: {job_key: {page_path, agent_id, current_step, total_steps, last_check}}

def register_full_auto_job(page_path, agent_id, step, total_steps):
    """Register a Full Auto job for backup monitoring using COMPOSITE KEY"""
    normalized_path = page_path.replace('\\', '/')
    job_key = get_job_key(page_path, agent_id)
    full_auto_jobs[job_key] = {
        'page_path': normalized_path,
        'agent_id': agent_id,
        'current_step': step,
        'total_steps': total_steps,
        'started': datetime.now().isoformat(),
        'last_check': None
    }
    print(f"[Full Auto Backup] Registered job: {job_key} step {step}/{total_steps}")
    
    # Save to file for persistence
    backup_file = BASE_DIR / "full_auto_jobs.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(full_auto_jobs, f, ensure_ascii=False, indent=2)

def unregister_full_auto_job(page_path, agent_id=None):
    """Remove a Full Auto job (completed or cancelled) using COMPOSITE KEY"""
    normalized_path = page_path.replace('\\', '/')
    
    if agent_id:
        # Use composite key
        job_key = get_job_key(page_path, agent_id)
        if job_key in full_auto_jobs:
            del full_auto_jobs[job_key]
            print(f"[Full Auto Backup] Unregistered job: {job_key}")
    else:
        # Backward compatibility: remove all jobs for this page
        keys_to_remove = [k for k in full_auto_jobs.keys() if k.startswith(normalized_path + ":") or k == normalized_path]
        for key in keys_to_remove:
            del full_auto_jobs[key]
            print(f"[Full Auto Backup] Unregistered job: {key}")
    
    # Save to file
    backup_file = BASE_DIR / "full_auto_jobs.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(full_auto_jobs, f, ensure_ascii=False, indent=2)

def load_full_auto_jobs():
    """Load Full Auto jobs from file on startup"""
    global full_auto_jobs
    backup_file = BASE_DIR / "full_auto_jobs.json"
    if backup_file.exists():
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                loaded_jobs = json.load(f)
            
            # Convert old format keys to new composite format if needed
            full_auto_jobs = {}
            for key, info in loaded_jobs.items():
                if ':' in key:
                    # Already composite key format
                    full_auto_jobs[key] = info
                else:
                    # Old format - convert to composite key
                    agent_id = info.get('agent_id', 'unknown')
                    new_key = get_job_key(key, agent_id)
                    info['page_path'] = key
                    full_auto_jobs[new_key] = info
            
            print(f"[Full Auto Backup] Loaded {len(full_auto_jobs)} jobs from file")
        except Exception as e:
            print(f"[Full Auto Backup] Error loading jobs: {e}")
            full_auto_jobs = {}

def get_step_output_name(agent, step_num):
    """Dynamically get the output file name for a step from any agent format"""
    # Try new format first: agent.steps[n].output.path
    if agent.get("steps") and len(agent.get("steps", [])) >= step_num:
        step_config = agent["steps"][step_num - 1]
        # Check output.path (new format)
        if step_config.get("output") and step_config["output"].get("path"):
            return step_config["output"]["path"]
        # Check output_name
        if step_config.get("output_name"):
            return step_config["output_name"]
        # Check report_name
        if step_config.get("report_name"):
            return step_config["report_name"]
    
    # Try old format: agent.step1.output_name
    step_key = f"step{step_num}"
    if agent.get(step_key):
        step_config = agent[step_key]
        if step_config.get("output_name"):
            return step_config["output_name"]
        if step_config.get("report_name"):
            return step_config["report_name"]
        # Check output.path (hybrid format)
        if step_config.get("output") and step_config["output"].get("path"):
            return step_config["output"]["path"]
    
    # Fallback - standard naming
    return f"דוח שלב {step_num}.md"

def check_full_auto_reports():
    """Check if any Full Auto jobs have completed reports and trigger next step"""
    if not full_auto_jobs:
        return
    
    for page_path, job in list(full_auto_jobs.items()):
        agent_id = job['agent_id']
        current_step = job['current_step']
        total_steps = job['total_steps']
        job_started = job.get('started')
        
        # Get agent config dynamically
        agent = get_agent_unified(agent_id)
        if not agent:
            print(f"[Full Auto Backup] Agent {agent_id} not found, removing job")
            unregister_full_auto_job(page_path)
            continue
        
        # Get agent folder name dynamically from config
        agent_folder_name = agent.get("folder_name")
        if not agent_folder_name:
            # Fallback: use agent name or id
            agent_folder_name = agent.get("name", agent_id)
        
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Get output name dynamically from agent config
        output_name = get_step_output_name(agent, current_step)
        
        report_path = output_folder / output_name
        
        print(f"[Full Auto Backup] Checking: {report_path}")
        
        # Check if report exists and was created after job started
        if report_path.exists():
            # Check if file was created after job started
            file_mtime = datetime.fromtimestamp(report_path.stat().st_mtime)
            job_start_time = datetime.fromisoformat(job_started) if job_started else datetime.min
            
            if file_mtime < job_start_time:
                print(f"[Full Auto Backup] Report exists but is older than job start ({file_mtime} < {job_start_time})")
                continue
            
            print(f"[Full Auto Backup] Fresh report found: {report_path} (modified: {file_mtime})")
            
            # Lazy Backup Logic: Only trigger if report is older than 60 seconds
            # This gives the Webhook (which happens instantly) time to act first.
            now = datetime.now()
            report_age = (now - file_mtime).total_seconds()
            
            if report_age < 60:
                print(f"[Full Auto Backup] Report is too fresh ({report_age:.1f}s), waiting for Webhook...")
                continue
                
            print(f"[Full Auto Backup] Report is old enough ({report_age:.1f}s), checking if next step started...")

            # Check if next step is already running
            normalized_path = page_path.replace('\\', '/')
            if normalized_path in running_pages:
                running_step = running_pages[normalized_path].get('step', 0)
                # Loop Prevention: If running step is greater OR EQUAL to next step, skip!
                # If we want to trigger step 3, but step 3 is already running (running_step=3), SKIP.
                if running_step >= current_step + 1:
                    print(f"[Full Auto Backup] Step {running_step} already running/queued, skipping backup trigger for {current_step + 1}")
                    continue
            
            # Double Check: read running_jobs.json directly to be sure (in case of race conditions or server restarts)
            try:
                jobs_file = BASE_DIR / "running_jobs.json"
                if jobs_file.exists():
                    with open(jobs_file, 'r', encoding='utf-8') as f:
                        saved_running_pages = json.load(f)
                    if normalized_path in saved_running_pages:
                         saved_step = saved_running_pages[normalized_path].get('step', 0)
                         if saved_step >= current_step + 1:
                             print(f"[Full Auto Backup] (File Check) Step {saved_step} already running, skipping backup trigger")
                             # Update in-memory state just in case
                             running_pages[normalized_path] = saved_running_pages[normalized_path]
                             continue
            except Exception as e:
                print(f"[Full Auto Backup] Error checking running_jobs.json: {e}")

            next_step = current_step + 1
            if next_step <= total_steps:
                print(f"[Full Auto Backup] Triggering step {next_step} for {page_path}")
                
                # Debug log
                debug_log = BASE_DIR / "trigger_step_debug.log"
                with open(debug_log, 'a', encoding='utf-8') as f:
                    f.write(f"\n[{datetime.now().isoformat()}] Backup mechanism triggering step {next_step}\n")
                    f.write(f"  page_path: {page_path}\n")
                    f.write(f"  report found: {report_path}\n")
                
                # Update job to next step
                full_auto_jobs[normalized_path]['current_step'] = next_step
                full_auto_jobs[normalized_path]['last_check'] = datetime.now().isoformat()
                
                # Save updated jobs
                backup_file = BASE_DIR / "full_auto_jobs.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(full_auto_jobs, f, ensure_ascii=False, indent=2)
                
                # Trigger next step in a thread with captured variables
                next_step_copy = next_step
                page_path_copy = page_path
                agent_id_copy = agent_id
                total_steps_copy = total_steps
                
                def run_next():
                    time.sleep(3)  # Small delay
                    trigger_step(page_path_copy, agent_id_copy, next_step_copy, total_steps_copy)
                
                thread = threading.Thread(target=run_next)
                thread.daemon = True
                thread.start()
            else:
                print(f"[Full Auto Backup] All {total_steps} steps completed for {page_path}")
                unregister_full_auto_job(page_path)

# Background thread for Full Auto backup checks
def full_auto_backup_thread():
    """Background thread that periodically checks for completed reports"""
    print("[Full Auto Backup] Background checker started")
    
    # Log startup
    debug_log = BASE_DIR / "backup_thread_debug.log"
    with open(debug_log, 'w', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] Backup thread started\n")
    
    check_count = 0
    while True:
        try:
            check_count += 1
            # Log every 6 checks (every minute)
            if check_count % 6 == 0:
                with open(debug_log, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().isoformat()}] Check #{check_count}, jobs: {len(full_auto_jobs)}\n")
            time.sleep(10)  # Check every 10 seconds
            check_full_auto_reports()
        except Exception as e:
            print(f"[Full Auto Backup] Error in background check: {e}")

# Start background thread on module load
# import threading
# backup_thread = threading.Thread(target=full_auto_backup_thread, daemon=True)
# backup_thread.start()

# Load existing jobs on startup (just for status, not for backup)
load_full_auto_jobs()

def trigger_step(page_path, agent_id, step_num, total_steps):
    """Internal function to trigger a step - called from Full Auto mode"""
    # Debug log to file
    debug_log = BASE_DIR / "trigger_step_debug.log"
    normalized_path = page_path.replace('\\', '/')
    job_key = get_job_key(page_path, agent_id)
    
    with open(debug_log, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{datetime.now().isoformat()}] trigger_step called\n")
        f.write(f"  job_key: {job_key}\n")
        f.write(f"  step_num: {step_num}\n")
        f.write(f"  total_steps: {total_steps}\n")
    
    # === ENTRY POINT PROTECTION: Check if step is already running ===
    # This is the FIRST LINE OF DEFENSE against duplicate triggers
    # Uses COMPOSITE KEY for parallel agent support
    
    # Check 1: In-memory running_pages
    current_info = running_pages.get(job_key)
    if current_info:
        running_step = current_info.get('step', 0)
        if running_step >= step_num:
            msg = f"[trigger_step] BLOCKED: {job_key} step {step_num} - already at step {running_step} in memory"
            print(msg)
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"  {msg}\n")
            return  # Don't trigger!
    
    # Check 2: running_jobs.json (persistent state - survives server restart)
    try:
        jobs_file = BASE_DIR / "running_jobs.json"
        if jobs_file.exists():
            with open(jobs_file, 'r', encoding='utf-8') as f:
                saved_pages = json.load(f)
            if job_key in saved_pages:
                saved_step = saved_pages[job_key].get('step', 0)
                if saved_step >= step_num:
                    msg = f"[trigger_step] BLOCKED: {job_key} step {step_num} - already at step {saved_step} in running_jobs.json"
                    print(msg)
                    with open(debug_log, 'a', encoding='utf-8') as f:
                        f.write(f"  {msg}\n")
                    return  # Don't trigger!
    except Exception as e:
        print(f"[trigger_step] Warning: Could not check running_jobs.json: {e}")
    
    with open(debug_log, 'a', encoding='utf-8') as f:
        f.write(f"  Protection checks passed - proceeding with trigger\n")
    
    try:
        from flask import Flask
        
        agent = get_agent_unified(agent_id)
        if not agent:
            print(f"[Full Auto] Agent {agent_id} not found!")
            return
        
        # Get step config from agent
        step_key = f"step{step_num}"
        step_config = agent.get(step_key, {})
        if not step_config and agent.get("steps"):
            if len(agent.get("steps", [])) >= step_num:
                step_config = agent["steps"][step_num - 1]
        
        if not step_config:
            print(f"[Full Auto] No config for step {step_num}")
            return
        
        # Get agent file path OR prompt template (for dynamic agents)
        agent_file = step_config.get("agent") or step_config.get("prompt_file", "")
        prompt_template = step_config.get("prompt_template", "")
        
        # Check: must have either agent_file OR prompt_template
        if not agent_file and not prompt_template:
            print(f"[Full Auto] No agent file or prompt_template for step {step_num}")
            with open(debug_log, 'a', encoding='utf-8') as f:
                f.write(f"  ERROR: No agent file or prompt_template for step {step_num}\n")
            return
        
        # Build paths
        agent_folder_name = agent.get("folder_name", "שיווק אטומי")
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Output name for this step
        output_name = step_config.get("output_name") or step_config.get("report_name")
        if not output_name and step_config.get("output"):
            output_name = step_config["output"].get("path")
        if not output_name:
            output_name = f"דוח שלב {step_num}.md"
        
        # Previous step report (for context)
        prev_report = ""
        if step_num > 1:
            prev_step = agent.get(f"step{step_num-1}", {})
            if not prev_step and agent.get("steps") and len(agent.get("steps", [])) >= step_num - 1:
                prev_step = agent["steps"][step_num - 2]
            prev_output = prev_step.get("output_name") or prev_step.get("report_name")
            if not prev_output and prev_step.get("output"):
                prev_output = prev_step["output"].get("path")
            if prev_output:
                prev_report = str(output_folder / prev_output)
        
        # Get page keyword
        keyword = Path(page_path).stem
        
        # Build paths
        if agent_file:
            agent_file_path = BASE_DIR / agent_file
            if not str(agent_file_path).endswith('.md'):
                agent_file_path = Path(str(agent_file_path) + '.md')
        else:
            agent_file_path = None  # Template-based agent, no file
        page_full_path = BASE_DIR / page_path
        report_full_path = output_folder / output_name
        if prompt_template:
            # Create shortcode engine
            html_file_path = str(page_folder / f"{keyword}.html")
            engine = ShortcodeEngine(
                page_path=html_file_path,
                agent=agent,
                step_num=step_num
            )
            
            # Set context
            if agent_file_path:
                full_prompt_path = str(agent_file_path)
            else:
                full_prompt_path = ""
            engine.context[f"STEP{step_num}_PROMPT_FILE"] = full_prompt_path
            engine.context["PROMPT_FILE_PATH"] = full_prompt_path
            engine.context["PAGE_HTML_PATH"] = str(page_full_path)
            engine.context["PAGE_KEYWORD"] = keyword
            engine.context["OUTPUT_PATH"] = str(report_full_path)
            
            # Previous step report shortcode
            if prev_report:
                engine.context[f"STEP{step_num-1}_REPORT"] = prev_report
            
            # Process template
            user_prompt = engine.process(prompt_template)
        else:
            # File-based prompt (requires agent_file_path)
            if not agent_file_path:
                print(f"[Full Auto] ERROR: No agent_file_path for file-based step {step_num}")
                return
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path}"
            if prev_report:
                user_prompt += f" ואת הדוח {prev_report}"
            user_prompt += f" ואת קובץ ה-HTML: {page_full_path}. בצע את ההוראות. בסוף שמור את הדוח בנתיב: {report_full_path}"
        
        # Determine agent type for prompt saving
        # Use agent_folder_name directly instead of hardcoded type detection
        save_step_prompt(page_path, f"step{step_num}", user_prompt, agent_folder_name)
        
        print(f"[Full Auto] Creating runner for step {step_num}...")
        
        # Get log file for streaming to browser - use new format with agent_id
        page_log_file = get_log_file_for_job(page_path, agent_id)
        print(f"[trigger_step] Creating log file: {page_log_file}")
        clear_live_log_for_job(page_path, agent_id)
        
        # === SEND SSE EVENT FOR STEP STARTED ===
        # This notifies the frontend to update the log panel title
        key = f"{normalized_path}:{agent_id}"
        step_events[key] = {
            'type': 'step_started',
            'page_path': page_path,
            'agent_id': agent_id,
            'step': step_num,
            'total_steps': total_steps,
            'status': 'running',
            'timestamp': time.time()
        }
        
        # Create runner script with UNIQUE name to support parallel jobs
        import uuid
        job_uuid = str(uuid.uuid4())[:8]
        runner_script = TMP_FOLDER / f"temp_run_{job_uuid}.py"
        page_path_escaped = str(page_path).replace("\\", "/")
        api_key = ANTHROPIC_API_KEY
        cmd = get_claude_command()
        
        # Escape backslashes for Python string literals
        agent_file_escaped = str(agent_file_path).replace("\\", "\\\\") if agent_file_path else ""
        report_path_escaped = str(report_full_path).replace("\\", "\\\\")
        base_dir_escaped = str(BASE_DIR).replace("\\", "\\\\")
        log_file_escaped = str(page_log_file).replace("\\", "\\\\")
        cmd_escaped = str(cmd).replace("\\", "\\\\")
        
        runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import urllib.request
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{base_dir_escaped}")

LIVE_LOG = r"{log_file_escaped}"

def log(msg):
    """Write to live log file (same as original steps)"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🚀 Full Auto - שלב {step_num}")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📋 סוכן: {agent_file_escaped}")
log("📁 פלט: {report_path_escaped}")
log("")

# Save prompt to temp file
prompt = r"""{user_prompt}"""
prompt_file = r"{base_dir_escaped}" + r"\\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {{len(prompt)}} תווים")

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output
claude_cmd = r"{cmd_escaped}"
args = [
    claude_cmd,
    "-p",
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10"
]

prompt_input = open(prompt_file, "r", encoding="utf-8")

process = subprocess.Popen(
    args,
    stdin=prompt_input,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{base_dir_escaped}"
)

# Read streaming output
try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()

log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Step completion webhook
try:
    report_path = r"{report_path_escaped}"
    report_exists = os.path.exists(report_path)
    webhook_data = json.dumps({{
        "page_path": "{page_path_escaped}",
        "agent_id": "{agent_id}",
        "step": {step_num},
        "status": "success" if report_exists else "error"
    }}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={{"Content-Type": "application/json"}},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step {step_num} webhook: {{'success' if report_exists else 'error'}}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {{e}}")
'''
        
        with open(runner_script, 'w', encoding='utf-8') as f:
            f.write(runner_content)
        
        batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
        # Use unique batch file name for parallel job support
        batch_path = TMP_FOLDER / f"temp_run_{job_uuid}.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Run in new console (same as original step functions)
        running_process = subprocess.Popen(
            [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
            cwd=str(BASE_DIR)
        )
        
        # Update running status with composite key (include job_uuid for cleanup)
        set_page_running(page_path, agent_id, step_num, running_process.pid, full_auto=True, total_steps=total_steps, job_uuid=job_uuid)
        
        # Update Full Auto backup job
        register_full_auto_job(page_path, agent_id, step_num, total_steps)
        
        print(f"[Full Auto] Step {step_num} started with PID {running_process.pid}")
        
        # Debug log success
        with open(debug_log, 'a', encoding='utf-8') as f:
            f.write(f"  SUCCESS: Process started with PID {running_process.pid}\n")
        
    except Exception as e:
        print(f"[Full Auto] Error triggering step {step_num}: {e}")
        import traceback
        traceback.print_exc()
        
        # Debug log error
        debug_log = BASE_DIR / "trigger_step_debug.log"
        with open(debug_log, 'a', encoding='utf-8') as f:
            f.write(f"  ERROR: {e}\n")
            f.write(f"  {traceback.format_exc()}\n")

@app.route('/api/step/events')
def step_events_stream():
    """Server-Sent Events for step completion notifications"""
    from flask import Response
    
    page_path = request.args.get('page', '')
    if page_path:
        page_path = page_path.replace('\\', '/')
    
    def generate():
        last_seen = {}
        while True:
            for key, event in list(step_events.items()):
                if page_path and page_path in key:
                    event_time = event.get('timestamp', 0)
                    if key not in last_seen or last_seen[key] < event_time:
                        last_seen[key] = event_time
                        yield f"data: {json.dumps(event)}\n\n"
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    })

@app.route('/api/status/page/<path:page_path>', methods=['GET'])
def get_page_status(page_path):
    """Get running status of a specific page/job.
    If agent_id is provided, uses composite key. Otherwise checks all jobs for this page."""
    agent_id = request.args.get('agent_id')
    
    if agent_id:
        # Use composite key for specific job
        job_key = get_job_key(page_path, agent_id)
        if job_key in running_pages:
            return jsonify({"success": True, "running": True, "info": running_pages[job_key]})
    else:
        # Check for any job with this page_path (backward compatibility)
        normalized_path = page_path.replace('\\', '/')
        for job_key, info in running_pages.items():
            job_page = info.get('page_path', job_key.rsplit(':', 1)[0] if ':' in job_key else job_key)
            if job_page == normalized_path:
                return jsonify({"success": True, "running": True, "info": info})
    
    return jsonify({"success": True, "running": False})

@app.route('/api/status/check-files', methods=['POST'])
def check_for_new_files():
    """Check if expected output files exist (for polling)"""
    try:
        data = request.json
        files_to_check = data.get("files", [])
        
        results = {}
        for file_path in files_to_check:
            # Normalize path (handle both / and \)
            normalized_path = file_path.replace('/', os.sep).replace('\\', os.sep)
            full_path = BASE_DIR / normalized_path
            exists = full_path.exists()
            print(f"[Check] {file_path} -> {full_path} -> exists: {exists}")
            results[file_path] = {
                "exists": exists,
                "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat() if exists else None
            }
        
        return jsonify({"success": True, "files": results})
    except Exception as e:
        print(f"[Check] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/reset', methods=['POST'])
def reset_page():
    """Reset a page to its original state: delete reports, restore backup"""
    try:
        import shutil
        from urllib.parse import unquote
        
        print(f"[Reset] Request received")
        print(f"[Reset] Content-Type: {request.content_type}")
        print(f"[Reset] Raw data: {request.data}")
        
        # Get path from request body
        try:
            data = request.get_json(force=True) or {}
        except Exception as e:
            print(f"[Reset] JSON parse error: {e}")
            data = {}
        
        print(f"[Reset] Parsed data: {data}")
        page_path = data.get('path', '')
        
        if not page_path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        # Decode URL-encoded path and normalize separators
        page_path = unquote(page_path).replace('\\', '/')
        print(f"[Reset] Received path: {page_path}")
        
        # Get full path with BASE_DIR
        page_folder = BASE_DIR / get_page_folder(page_path)
        print(f"[Reset] Page folder: {page_folder}")
        
        if not page_folder.exists():
            return jsonify({"success": False, "error": f"Page folder not found: {page_folder}"}), 404
        
        # Get the base name without extension
        page_name = Path(page_path).stem
        print(f"[Reset] Page name: {page_name}")
        
        # Find main file and backup
        main_file = page_folder / f"{page_name}.html"
        backup_file = page_folder / f"{page_name}_backup.html"
        
        print(f"[Reset] Main file: {main_file} (exists: {main_file.exists()})")
        print(f"[Reset] Backup file: {backup_file} (exists: {backup_file.exists()})")
        
        deleted_items = []
        
        # 1. Delete agent report folders - DYNAMICALLY from all agents
        # Get all agent folder names
        all_agents = {}
        agents_folder = BASE_DIR / "agents"
        if agents_folder.exists():
            for agent_file in agents_folder.glob("*.json"):
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        agent_data = json.load(f)
                    agent_id = agent_file.stem
                    all_agents[agent_id] = agent_data
                except:
                    pass
        # Also from config
        for agent_id, agent_data in config.get("agents", {}).items():
            if agent_id not in all_agents:
                all_agents[agent_id] = agent_data
        
        # Delete each agent's folder
        for agent_id, agent_data in all_agents.items():
            folder_name = agent_data.get("folder_name") or agent_data.get("name") or agent_id
            folder_path = page_folder / folder_name
            if folder_path.exists() and folder_path.is_dir():
                shutil.rmtree(folder_path)
                deleted_items.append(f"📁 {folder_name}/")
                print(f"[Reset] Deleted folder: {folder_path}")
        
        # 2. Delete .bak files (intermediate backups, not the original backup)
        for bak_file in page_folder.glob("*.bak"):
            bak_file.unlink()
            deleted_items.append(f"📄 {bak_file.name}")
            print(f"[Reset] Deleted backup: {bak_file}")
        
        # 3. If backup doesn't exist, fetch from WordPress first
        if not backup_file.exists():
            print(f"[Reset] No backup found, fetching from WordPress...")
            
            # Read page_info.json to get post_id and url
            page_info_file = page_folder / "page_info.json"
            if not page_info_file.exists():
                return jsonify({"success": False, "error": "No backup and no page_info.json - cannot restore"}), 400
            
            with open(page_info_file, 'r', encoding='utf-8') as f:
                page_info = json.load(f)
            
            post_id = page_info.get('post_id')
            url = page_info.get('url', '')
            
            if not post_id:
                return jsonify({"success": False, "error": "No backup and no post_id in page_info - cannot restore from WordPress"}), 400
            
            # Fetch from WordPress
            if not REQUESTS_AVAILABLE:
                return jsonify({"success": False, "error": "No backup and requests library not installed - cannot fetch from WordPress"}), 500
            
            try:
                site_id, site = get_wordpress_site(url)
                
                # Get or refresh token
                token = jwt_tokens.get(site_id)
                if not token:
                    password = site.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD")
                    username = site.get("username") or os.getenv(f"WP_{site_id.upper()}_USERNAME")
                    
                    if not username or not password:
                        return jsonify({"success": False, "error": "No backup and missing WordPress credentials"}), 400
                    
                    token_url = site["site_url"] + site["token_endpoint"]
                    token_response = requests.post(token_url, json={
                        "username": username,
                        "password": password
                    }, timeout=10)
                    
                    if token_response.status_code != 200:
                        return jsonify({"success": False, "error": "No backup and failed to authenticate to WordPress"}), 401
                    
                    token = token_response.json().get("token")
                    jwt_tokens[site_id] = token
                
                # Fetch post data
                fetch_url = f"{site['site_url']}{site['api_base']}/posts/{post_id}?context=edit"
                response = requests.get(
                    fetch_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30
                )
                
                if response.status_code != 200:
                    if response.status_code == 403:
                        jwt_tokens[site_id] = None
                    return jsonify({"success": False, "error": f"Failed to fetch from WordPress: {response.text}"}), response.status_code
                
                post_data = response.json()
                raw_content = post_data.get("content", {}).get("raw", "")
                
                if not raw_content:
                    return jsonify({"success": False, "error": "No content returned from WordPress"}), 400
                
                # Save backup
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(raw_content)
                
                # Also save meta backup
                meta_backup = {
                    "title": post_data.get("yoast_head_json", {}).get("title", post_data.get("title", {}).get("rendered", "")),
                    "description": post_data.get("yoast_head_json", {}).get("description", ""),
                    "slug": post_data.get("slug", ""),
                    "fetched_at": datetime.now().isoformat()
                }
                meta_path = page_folder / f"{page_name}_backup_meta.json"
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta_backup, f, ensure_ascii=False, indent=2)
                
                deleted_items.append(f"📥 נמשך גיבוי מוורדפרס")
                print(f"[Reset] Fetched backup from WordPress and saved to {backup_file}")
                
            except requests.exceptions.Timeout:
                return jsonify({"success": False, "error": "WordPress connection timed out"}), 500
            except Exception as wp_error:
                return jsonify({"success": False, "error": f"WordPress fetch failed: {str(wp_error)}"}), 500
        
        # 4. Restore backup to main file
        if backup_file.exists() and main_file.exists():
            shutil.copy2(backup_file, main_file)
            deleted_items.append(f"🔄 שוחזר מגיבוי: {page_name}.html")
            print(f"[Reset] Restored backup: {backup_file} -> {main_file}")
        
        # 5. Reset page_info.json - remove upload/status fields but keep basic info
        page_info_file = page_folder / "page_info.json"
        if page_info_file.exists():
            with open(page_info_file, 'r', encoding='utf-8') as f:
                page_info = json.load(f)
            
            # Keep only essential fields
            essential_fields = ['page_name', 'keyword', 'url', 'post_id', 'title', 'description', 
                              'title_options', 'description_options']
            cleaned_info = {k: v for k, v in page_info.items() if k in essential_fields}
            
            with open(page_info_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_info, f, ensure_ascii=False, indent=2)
            deleted_items.append(f"🔄 אופס page_info.json")
            print(f"[Reset] Reset page_info.json")
        
        # 6. Clear from running pages if present
        if page_path in running_pages:
            del running_pages[page_path]
        
        return jsonify({
            "success": True, 
            "message": f"העמוד אופס בהצלחה",
            "deleted": deleted_items
        })
        
    except Exception as e:
        print(f"[Reset] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/reset-agent', methods=['POST'])
def reset_agent_for_page():
    """Reset a specific agent for a page - delete only that agent's reports folder"""
    try:
        import shutil
        from urllib.parse import unquote
        
        data = request.get_json(force=True) or {}
        page_path = data.get('path', '')
        agent_id = data.get('agent_id', '')
        
        if not page_path or not agent_id:
            return jsonify({"success": False, "error": "Missing path or agent_id"}), 400
        
        # Normalize path
        page_path = unquote(page_path).replace('\\', '/')
        
        # Get page folder
        page_folder = BASE_DIR / get_page_folder(page_path)
        if not page_folder.exists():
            return jsonify({"success": False, "error": f"Page folder not found"}), 404
        
        # Get agent config to find folder name
        agent = get_agent_by_id(agent_id)
        if not agent:
            return jsonify({"success": False, "error": f"Agent not found: {agent_id}"}), 404
        
        # Get the agent's folder name
        folder_name = agent.get("folder_name") or agent.get("name") or agent_id
        agent_folder = page_folder / folder_name
        
        deleted_items = []
        
        if agent_folder.exists() and agent_folder.is_dir():
            shutil.rmtree(agent_folder)
            deleted_items.append(f"📁 {folder_name}/")
            print(f"[Reset Agent] Deleted folder: {agent_folder}")
        else:
            return jsonify({"success": False, "error": f"Agent folder not found: {folder_name}"}), 404
        
        return jsonify({
            "success": True,
            "message": f"הסוכן אופס בהצלחה",
            "deleted": deleted_items,
            "agent_id": agent_id
        })
        
    except Exception as e:
        print(f"[Reset Agent] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/file/exists', methods=['GET'])
def check_file_exists():
    """Check if a single file exists - simple GET endpoint for polling"""
    try:
        file_path = request.args.get('path', '')
        if not file_path:
            return jsonify({"success": False, "error": "No path provided"}), 400
        
        # Normalize path
        normalized_path = file_path.replace('/', os.sep).replace('\\', os.sep)
        full_path = BASE_DIR / normalized_path
        exists = full_path.exists()
        
        result = {
            "success": True,
            "path": file_path,
            "exists": exists
        }
        
        if exists:
            stat = full_path.stat()
            result["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            result["size"] = stat.st_size
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/status/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a running job"""
    job = active_jobs.get(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    
    return jsonify({"success": True, "job": job})

@app.route('/api/status/recent-files', methods=['GET'])
def get_recent_files():
    """Get recently modified files in output folders"""
    try:
        recent = []
        
        # Check reports folder
        reports_folder = BASE_DIR / config["paths"]["reports"]
        if reports_folder.exists():
            for f in reports_folder.glob("*.md"):
                recent.append({
                    "type": "report",
                    "name": f.name,
                    "path": str(f.relative_to(BASE_DIR)),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        
        # Check output folder
        output_folder = BASE_DIR / config["paths"]["output"]
        if output_folder.exists():
            for f in output_folder.glob("*.html"):
                recent.append({
                    "type": "fixed",
                    "name": f.name,
                    "path": str(f.relative_to(BASE_DIR)),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        
        # Sort by modified date
        recent.sort(key=lambda x: x["modified"], reverse=True)
        
        return jsonify({"success": True, "files": recent[:20]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Reports ============

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Get all report files"""
    try:
        reports_folder = BASE_DIR / config["paths"]["reports"]
        reports = []
        
        if reports_folder.exists():
            for file in reports_folder.glob("*.md"):
                reports.append({
                    "name": file.stem,
                    "path": str(file.relative_to(BASE_DIR)),
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/report/<path:report_path>', methods=['GET'])
def get_report(report_path):
    """Get report content (optionally rendered as HTML)"""
    try:
        file_path = BASE_DIR / report_path
        if not file_path.exists():
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        render = request.args.get('render', 'false').lower() == 'true'
        
        if render and MARKDOWN_AVAILABLE:
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            return jsonify({
                "success": True,
                "content": content,
                "html": html_content
            })
        
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/report/delete', methods=['POST'])
def delete_report():
    """Delete a report file"""
    try:
        data = request.json
        report_path = data.get("path")
        
        if not report_path:
            return jsonify({"success": False, "error": "No path provided"}), 400
        
        file_path = BASE_DIR / report_path
        
        if not file_path.exists():
            return jsonify({"success": False, "error": "Report not found"}), 404
        
        # Safety check - only allow deleting from reports folder
        reports_folder = BASE_DIR / config["paths"]["reports"]
        if not str(file_path).startswith(str(reports_folder)):
            return jsonify({"success": False, "error": "Invalid path"}), 403
        
        file_path.unlink()
        print(f"[Delete] Report deleted: {report_path}")
        
        return jsonify({"success": True, "message": "Report deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Archive ============

@app.route('/api/archive', methods=['GET'])
def get_archive():
    """Get all archive folders"""
    try:
        archive_folder = BASE_DIR / config["paths"]["archive"]
        archives = []
        
        if archive_folder.exists():
            for folder in archive_folder.iterdir():
                if folder.is_dir():
                    meta_file = folder / "meta.json"
                    meta = {}
                    if meta_file.exists():
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                    
                    archives.append({
                        "name": folder.name,
                        "path": str(folder.relative_to(BASE_DIR)),
                        "meta": meta
                    })
        
        # Sort by name (date) descending
        archives.sort(key=lambda x: x["name"], reverse=True)
        
        return jsonify({"success": True, "archives": archives})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/archive/save', methods=['POST'])
def save_to_archive():
    """Save current state to archive"""
    try:
        data = request.json
        page_name = data.get("page_name")
        page_path = data.get("page_path")
        report_path = data.get("report_path")
        fixed_path = data.get("fixed_path")
        
        # Create archive folder
        archive_folder = create_archive_folder(page_name)
        
        # Copy files
        if page_path:
            src = BASE_DIR / page_path
            if src.exists():
                shutil.copy2(src, archive_folder / f"מקור_{src.name}")
        
        if report_path:
            src = BASE_DIR / report_path
            if src.exists():
                shutil.copy2(src, archive_folder / f"דוח_{src.name}")
        
        if fixed_path:
            src = BASE_DIR / fixed_path
            if src.exists():
                shutil.copy2(src, archive_folder / f"מתוקן_{src.name}")
        
        # Save metadata
        meta = {
            "page_name": page_name,
            "date": datetime.now().isoformat(),
            "original": page_path,
            "report": report_path,
            "fixed": fixed_path
        }
        
        with open(archive_folder / "meta.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "archive_path": str(archive_folder.relative_to(BASE_DIR))
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - WordPress ============

@app.route('/api/wordpress/settings', methods=['GET'])
def get_wp_settings():
    """Get WordPress settings (without passwords)"""
    try:
        sites = {}
        for site_id, site_config in config["wordpress"]["sites"].items():
            sites[site_id] = {
                "name": site_config["name"],
                "site_url": site_config["site_url"],
                "username": site_config["username"],
                "has_password": bool(site_config.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD"))
            }
        
        return jsonify({
            "success": True,
            "sites": sites,
            "auth_type": config["wordpress"]["auth_type"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wordpress/settings', methods=['POST'])
def save_wp_settings():
    """Save WordPress settings"""
    try:
        data = request.json
        site_id = data.get("site_id")
        
        if site_id not in config["wordpress"]["sites"]:
            return jsonify({"success": False, "error": "Site not found"}), 404
        
        site = config["wordpress"]["sites"][site_id]
        
        if "username" in data:
            site["username"] = data["username"]
        if "password" in data and data["password"]:
            site["password"] = data["password"]
        if "site_url" in data:
            site["site_url"] = data["site_url"]
        
        save_config(config)
        
        # Clear cached token
        jwt_tokens[site_id] = None
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Sites Settings ============

@app.route('/api/sites/settings', methods=['GET'])
def get_sites_settings():
    """Get sites settings with page counts and icons"""
    try:
        sites = {}
        editable = config["paths"]["editable_pages"]
        
        # Support both dict and array formats
        if isinstance(editable, dict):
            for site_id, folder in editable.items():
                folder_path = BASE_DIR / folder
                page_count = 0
                if folder_path.exists():
                    page_count = len([d for d in folder_path.iterdir() if d.is_dir()])
                
                # Get display name and icon from WordPress config if available
                wp_site = config.get("wordpress", {}).get("sites", {}).get(site_id, {})
                display_name = wp_site.get("name", site_id)
                icon = wp_site.get("icon", "📁")
                
                sites[site_id] = {
                    "name": display_name,
                    "icon": icon,
                    "folder": folder,
                    "page_count": page_count
                }
        else:
            # Legacy array format
            for i, folder in enumerate(editable):
                site_id = "main" if i == 0 else f"site_{i}"
                folder_path = BASE_DIR / folder
                page_count = len([d for d in folder_path.iterdir() if d.is_dir()]) if folder_path.exists() else 0
                sites[site_id] = {
                    "name": site_id,
                    "icon": "📁",
                    "folder": folder,
                    "page_count": page_count
                }
        
        return jsonify({"success": True, "sites": sites})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sites/settings', methods=['POST'])
def save_sites_settings():
    """Save sites settings (names and folders)"""
    try:
        data = request.json
        sites_data = data.get("sites", {})
        
        for site_id, site_info in sites_data.items():
            # Update WordPress site name
            if site_id in config.get("wordpress", {}).get("sites", {}):
                if "name" in site_info:
                    config["wordpress"]["sites"][site_id]["name"] = site_info["name"]
            
            # Update editable_pages folder path
            if "folder" in site_info:
                editable = config["paths"]["editable_pages"]
                if isinstance(editable, dict) and site_id in editable:
                    config["paths"]["editable_pages"][site_id] = site_info["folder"]
        
        save_config(config)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wordpress/test', methods=['POST'])
def test_wp_connection():
    """Test WordPress connection and get JWT token"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        data = request.json
        site_id = data.get("site_id", "main")
        
        site = config["wordpress"]["sites"].get(site_id)
        if not site:
            return jsonify({"success": False, "error": "Site not found"}), 404
        
        # Get password from config or env
        password = site.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD")
        username = site.get("username") or os.getenv(f"WP_{site_id.upper()}_USERNAME")
        
        if not username or not password:
            return jsonify({"success": False, "error": "Missing credentials"}), 400
        
        # Get JWT token
        token_url = site["site_url"] + site["token_endpoint"]
        
        response = requests.post(token_url, json={
            "username": username,
            "password": password
        }, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            jwt_tokens[site_id] = token_data.get("token")
            
            return jsonify({
                "success": True,
                "message": "Connected successfully",
                "user_display_name": token_data.get("user_display_name", "")
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Authentication failed: {response.text}"
            }), 401
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Connection timed out"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wordpress/update', methods=['POST'])
def update_wp_page():
    """Update page content in WordPress"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        data = request.json
        post_id = data.get("post_id")
        content = data.get("content")
        url = data.get("url", "")
        
        if not post_id or not content:
            return jsonify({"success": False, "error": "Missing post_id or content"}), 400
        
        # Determine which site to use
        site_id, site = get_wordpress_site(url)
        
        # Get or refresh token
        token = jwt_tokens.get(site_id)
        if not token:
            # Try to get a new token
            password = site.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD")
            username = site.get("username") or os.getenv(f"WP_{site_id.upper()}_USERNAME")
            
            if not username or not password:
                return jsonify({"success": False, "error": "Missing credentials. Configure in settings."}), 400
            
            token_url = site["site_url"] + site["token_endpoint"]
            token_response = requests.post(token_url, json={
                "username": username,
                "password": password
            }, timeout=10)
            
            if token_response.status_code != 200:
                return jsonify({"success": False, "error": "Failed to authenticate"}), 401
            
            token = token_response.json().get("token")
            jwt_tokens[site_id] = token
        
        # Update post
        update_url = f"{site['site_url']}{site['api_base']}/posts/{post_id}"
        
        response = requests.post(
            update_url,
            json={"content": content},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            # Save to WordPress update history if page_path provided
            page_path = data.get("page_path")
            if page_path:
                # Count words in content (strip HTML)
                import re
                text_only = re.sub(r'<[^>]+>', '', content)
                word_count = len(text_only.split())
                
                save_wordpress_update_to_history(
                    page_path=page_path,
                    update_type='body',
                    changes={'body_words': word_count},
                    triggered_by=data.get('triggered_by', 'manual')
                )
            
            return jsonify({
                "success": True,
                "message": "Page updated successfully",
                "site": site["name"]
            })
        elif response.status_code == 403:
            # Token might be expired, clear it
            jwt_tokens[site_id] = None
            return jsonify({
                "success": False,
                "error": "Authentication expired. Please reconnect."
            }), 403
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to update: {response.text}"
            }), response.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - WordPress Fetch ============

@app.route('/api/wordpress/fetch', methods=['POST'])
def fetch_wp_page():
    """Fetch page data from WordPress (metadata + content)"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        data = request.json
        post_id = data.get("post_id")
        url = data.get("url", "")
        page_folder = data.get("page_folder")  # Where to save backups
        
        if not post_id:
            return jsonify({"success": False, "error": "Missing post_id"}), 400
        
        # Determine which site to use
        site_id, site = get_wordpress_site(url)
        
        # Get or refresh token
        token = jwt_tokens.get(site_id)
        if not token:
            # Try to get a new token
            password = site.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD")
            username = site.get("username") or os.getenv(f"WP_{site_id.upper()}_USERNAME")
            
            if not username or not password:
                return jsonify({"success": False, "error": "Missing credentials. Configure in settings."}), 400
            
            token_url = site["site_url"] + site["token_endpoint"]
            token_response = requests.post(token_url, json={
                "username": username,
                "password": password
            }, timeout=10)
            
            if token_response.status_code != 200:
                return jsonify({"success": False, "error": "Failed to authenticate"}), 401
            
            token = token_response.json().get("token")
            jwt_tokens[site_id] = token
        
        # Fetch post data with context=edit to get raw content
        fetch_url = f"{site['site_url']}{site['api_base']}/posts/{post_id}?context=edit"
        
        response = requests.get(
            fetch_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code != 200:
            if response.status_code == 403:
                jwt_tokens[site_id] = None
            return jsonify({
                "success": False,
                "error": f"Failed to fetch: {response.text}"
            }), response.status_code
        
        # Debug: Print raw HTTP response first
        print(f"=" * 60)
        print(f"📡 WordPress RAW HTTP Response for post {post_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Response size: {len(response.text)} bytes")
        print(f"   Has '<style' in raw response: {'<style' in response.text}")
        print(f"   Has '<!-- wp:html' in raw response: {'<!-- wp:html' in response.text}")
        print(f"   First 500 chars of raw response:")
        print(response.text[:500])
        print(f"=" * 60)
        
        post_data = response.json()
        
        # Debug: Log what WordPress returns
        content_data = post_data.get("content", {})
        raw_text = content_data.get('raw', '')
        rendered_text = content_data.get('rendered', '')
        
        print(f"📊 WordPress parsed content for post {post_id}")
        print(f"   Content fields: {list(content_data.keys())}")
        print(f"   raw length: {len(raw_text)}")
        print(f"   rendered length: {len(rendered_text)}")
        print(f"   raw has <script>: {'<script' in raw_text}")
        print(f"   raw has <style>: {'<style' in raw_text}")
        print(f"   rendered has <script>: {'<script' in rendered_text}")
        print(f"   rendered has <style>: {'<style' in rendered_text}")
        print(f"=" * 60)
        
        # Extract relevant data
        result = {
            "title": post_data.get("title", {}).get("rendered", ""),
            "slug": post_data.get("slug", ""),
            "content_raw": post_data.get("content", {}).get("raw", ""),
            "content_rendered": post_data.get("content", {}).get("rendered", ""),
            "excerpt": post_data.get("excerpt", {}).get("rendered", ""),
            "date_modified": post_data.get("modified", ""),
            "yoast_head_json": post_data.get("yoast_head_json", {})
        }
        
        # Extract SEO metadata from yoast
        yoast = result.get("yoast_head_json", {})
        result["meta_title"] = yoast.get("title", result["title"])
        result["meta_description"] = yoast.get("description", "")
        result["og_title"] = yoast.get("og_title", "")
        result["og_description"] = yoast.get("og_description", "")
        
        # Save backups if page_folder is provided
        if page_folder:
            folder_path = BASE_DIR / page_folder
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Save metadata backup
            meta_backup = {
                "title": result["meta_title"],
                "description": result["meta_description"],
                "slug": result["slug"],
                "og_title": result["og_title"],
                "og_description": result["og_description"],
                "fetched_at": datetime.now().isoformat()
            }
            
            # Use page folder name for backup file names
            page_name = folder_path.name
            
            meta_path = folder_path / f"{page_name}_backup_meta.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_backup, f, ensure_ascii=False, indent=2)
            
            # Save content backup as HTML
            # WordPress strips <script> and <style> from rendered content
            # Use raw content - it should have everything
            content_path = folder_path / f"{page_name}_backup.html"
            
            raw_content = result.get("content_raw", "")
            rendered_content = result.get("content_rendered", "")
            
            print(f"📊 raw length: {len(raw_content)}, rendered length: {len(rendered_content)}")
            
            # Always use RAW content - it contains the original content with <!-- wp:html --> blocks
            # RAW preserves <style> and <script> tags when content is in Gutenberg HTML blocks
            backup_content = raw_content
            print(f"✅ Using RAW content: {len(raw_content)} chars")
            
            print(f"📊 Final backup content length: {len(backup_content)} chars")
            
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            
            result["backup_saved"] = True
            result["backup_meta_path"] = str(meta_path.relative_to(BASE_DIR))
            result["backup_content_path"] = str(content_path.relative_to(BASE_DIR))
        
        return jsonify({
            "success": True,
            "data": result,
            "site": site["name"]
        })
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Connection timed out"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ WordPress Content Cleanup ============

def cleanup_html_for_wordpress(original_html):
    """
    Clean HTML content for WordPress upload.
    Full implementation based on N8N cleanup code.
    Fixes unclosed tags, escapes special characters, removes placeholder traces.
    """
    import re
    
    if not original_html:
        return original_html, {"success": False, "error": "No content"}
    
    cleanup_info = {
        "original_length": len(original_html),
        "tag_issues": [],
        "auto_fixed_tags": [],
        "success": True
    }
    
    html = original_html
    
    # ====================================================================================
    # Step 0: Check and fix unclosed HTML tags
    # ====================================================================================
    
    critical_tags = ['th', 'td', 'tr', 'tbody', 'thead', 'table', 'li', 'ul', 'ol', 'h3', 'h2', 'h1', 'p', 'strong', 'a', 'div']
    
    for tag in critical_tags:
        open_pattern = re.compile(f'<{tag}[^>]*>', re.IGNORECASE)
        close_pattern = re.compile(f'</{tag}>', re.IGNORECASE)
        
        open_count = len(open_pattern.findall(html))
        close_count = len(close_pattern.findall(html))
        
        if open_count != close_count:
            diff = open_count - close_count
            cleanup_info["tag_issues"].append(f"{tag}: {open_count} open, {close_count} close (diff: {diff})")
            
            if diff > 0:
                closing_tags = f'</{tag}>' * diff
                
                if tag == 'div':
                    script_idx = html.find('<script type="application/ld+json">')
                    if script_idx != -1:
                        html = html[:script_idx] + closing_tags + html[script_idx:]
                    else:
                        html += closing_tags
                elif tag in ['table', 'tbody', 'thead', 'tr', 'th', 'td']:
                    if tag == 'th':
                        insert_idx = html.rfind('</thead>')
                    elif tag == 'td':
                        insert_idx = html.rfind('</tbody>')
                    elif tag == 'tr':
                        insert_idx = html.rfind('</tbody>')
                        if insert_idx == -1:
                            insert_idx = html.rfind('</thead>')
                    else:
                        insert_idx = html.rfind('</table>')
                    
                    if insert_idx != -1:
                        html = html[:insert_idx] + closing_tags + html[insert_idx:]
                    else:
                        html += closing_tags
                elif tag in ['ul', 'ol', 'li']:
                    ul_idx = html.rfind('</ul>')
                    ol_idx = html.rfind('</ol>')
                    insert_idx = max(ul_idx, ol_idx)
                    if insert_idx != -1:
                        html = html[:insert_idx] + closing_tags + html[insert_idx:]
                    else:
                        html += closing_tags
                else:
                    div_idx = html.rfind('</div>')
                    if div_idx != -1:
                        html = html[:div_idx] + closing_tags + html[div_idx:]
                    else:
                        html += closing_tags
                
                cleanup_info["auto_fixed_tags"].append({"tag": tag, "count": diff})
    
    # Failsafe for divs
    final_div_open = len(re.findall(r'<div[^>]*>', html, re.IGNORECASE))
    final_div_close = len(re.findall(r'</div>', html, re.IGNORECASE))
    
    if final_div_open > final_div_close:
        still_missing = final_div_open - final_div_close
        closing_divs = '</div>' * still_missing
        script_idx = html.find('<script type="application/ld+json">')
        if script_idx != -1:
            html = html[:script_idx] + closing_divs + html[script_idx:]
        else:
            html += closing_divs
        cleanup_info["auto_fixed_tags"].append({"tag": "div (failsafe)", "count": still_missing})
    
    # ====================================================================================
    # Step 1: Pre-cleanup - Remove broken placeholders BEFORE any escaping
    # ====================================================================================
    
    # Remove broken placeholders with various newline patterns
    html = re.sub(r'\r\n\r\n[a-z0-9]{1,2}-->\r\n', '\r\n', html)
    html = re.sub(r'\n\n[a-z0-9]{1,2}-->\n', '\n', html)
    html = re.sub(r'\r\n[a-z0-9]{1,2}-->\r\n', '\r\n', html)
    html = re.sub(r'\n[a-z0-9]{1,2}-->\n', '\n', html)
    html = re.sub(r'\s+[a-z0-9]{1,2}-->\s+', '\n\n', html)
    
    # Clean multiple newlines (3+ → 2)
    html = re.sub(r'(\r\n){3,}', '\r\n\r\n', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    # ====================================================================================
    # Step 2: Remove placeholder traces and cleanup attributes
    # ====================================================================================
    
    # Remove Schema Markup comment
    html = re.sub(r'<!--\s*Schema Markup\s*-->', '', html, flags=re.IGNORECASE)
    
    # Remove data-style-placeholder attributes
    html = re.sub(r'\s*data-style-placeholder="[^"]*"', '', html)
    
    # Remove broken/incomplete placeholders
    html = re.sub(r'<!--AP_[A-Z]+_\d+_(?![a-z0-9]{2}-->)', '', html)
    html = re.sub(r'(<!--AP_[A-Z]+_\d+_)+', '', html)
    html = re.sub(r'AP_[A-Z]+_\d+_[a-z0-9]{0,2}-->', '', html)
    
    # Remove all remaining valid placeholders
    html = re.sub(r'<!--AP_[A-Z]+_\d+_[a-z0-9]{2}-->', '', html)
    
    # ====================================================================================
    # Step 3: Handle special characters (tabs, null bytes)
    # ====================================================================================
    
    # Remove null bytes
    html = html.replace('\0', '')
    
    # ====================================================================================
    # Step 4: Force DIV closing - final check
    # ====================================================================================
    
    div_open_count = len(re.findall(r'<div[^>]*>', html, re.IGNORECASE))
    div_close_count = len(re.findall(r'</div>', html, re.IGNORECASE))
    
    if div_open_count > div_close_count:
        missing_divs = div_open_count - div_close_count
        closing_divs = '</div>' * missing_divs
        
        # Insert before first schema script if exists
        first_schema_idx = html.find('<script type="application/ld+json">')
        if first_schema_idx != -1:
            html = html[:first_schema_idx] + closing_divs + html[first_schema_idx:]
        else:
            html += closing_divs
        
        cleanup_info["auto_fixed_tags"].append({"tag": "div (final)", "count": missing_divs})
    
    # ====================================================================================
    # Step 5: Clean excessive newlines at the end
    # ====================================================================================
    
    # Normalize line endings
    html = html.replace('\r\n', '\n')
    
    # Remove excessive blank lines (3+ → 2)
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    # Trim trailing whitespace
    html = html.rstrip()
    
    # ====================================================================================
    # Step 6: Add WordPress Gutenberg block markers
    # ====================================================================================
    
    # First, remove any existing wp markers to avoid duplicates
    html = re.sub(r'<!--\s*wp:html\s*-->\s*', '', html)
    html = re.sub(r'<!--\s*/wp:html\s*-->\s*', '', html)
    html = re.sub(r'<!--\s*/?wp:[a-z-]+\s*(?:\{[^}]*\})?\s*-->\s*', '', html)
    html = html.strip()
    
    # Add Gutenberg HTML block marker at the start (WordPress format)
    html = '<!-- wp:html -->\n\n\n\n' + html
    cleanup_info["gutenberg_wrapper_added"] = True
    
    cleanup_info["cleaned_length"] = len(html)
    cleanup_info["chars_removed"] = cleanup_info["original_length"] - len(html)
    
    return html, cleanup_info

@app.route('/api/wordpress/upload', methods=['POST'])
def upload_to_wp():
    """Upload page content and metadata to WordPress"""
    try:
        if not REQUESTS_AVAILABLE:
            return jsonify({"success": False, "error": "requests library not installed"}), 500
        
        data = request.json
        post_id = data.get("post_id")
        url = data.get("url", "")
        content = data.get("content")  # HTML content
        title = data.get("title")  # Optional: update title
        meta_description = data.get("meta_description")  # Optional: update Yoast description
        skip_cleanup = data.get("skip_cleanup", False)  # Skip HTML cleanup for restore
        
        if not post_id:
            return jsonify({"success": False, "error": "Missing post_id"}), 400
        
        # Determine which site to use
        site_id, site = get_wordpress_site(url)
        
        # Get or refresh token
        token = jwt_tokens.get(site_id)
        if not token:
            password = site.get("password") or os.getenv(f"WP_{site_id.upper()}_PASSWORD")
            username = site.get("username") or os.getenv(f"WP_{site_id.upper()}_USERNAME")
            
            if not username or not password:
                return jsonify({"success": False, "error": "Missing credentials. Configure in settings."}), 400
            
            token_url = site["site_url"] + site["token_endpoint"]
            token_response = requests.post(token_url, json={
                "username": username,
                "password": password
            }, timeout=10)
            
            if token_response.status_code != 200:
                return jsonify({"success": False, "error": "Failed to authenticate"}), 401
            
            token = token_response.json().get("token")
            jwt_tokens[site_id] = token
        
        # Build update payload
        update_data = {}
        if content:
            if skip_cleanup:
                # Skip cleanup for restore operations (content already clean from WordPress)
                print(f"⏭️ Skipping cleanup (restore mode), content length: {len(content)} chars")
                update_data["content"] = content
                cleanup_info = {"skipped": True, "original_length": len(content)}
            else:
                # 🧹 Clean HTML before uploading to WordPress
                cleaned_content, cleanup_info = cleanup_html_for_wordpress(content)
                print(f"📊 Content cleanup: {cleanup_info['original_length']} → {cleanup_info['cleaned_length']} chars")
                if cleanup_info.get('auto_fixed_tags'):
                    print(f"🔧 Auto-fixed tags: {cleanup_info['auto_fixed_tags']}")
                update_data["content"] = cleaned_content
        if title:
            update_data["title"] = title
        
        # Check if we have anything to update
        if not update_data and not meta_description:
            print(f"⚠️ Warning: Nothing to update! No content, title, or description provided.")
            return jsonify({
                "success": False,
                "error": "No content, title, or description provided to update"
            }), 400
        
        # Update post (only if we have content or title)
        update_url = f"{site['site_url']}{site['api_base']}/posts/{post_id}"
        post_update_success = False
        
        if update_data:
            # Log request details BEFORE sending
            print(f"=" * 60)
            print(f"📤 WordPress upload request")
            print(f"   URL: {update_url}")
            print(f"   Post ID: {post_id}")
            print(f"   Payload keys: {list(update_data.keys())}")
            if title:
                print(f"   Title: {title[:50]}...")
            if update_data.get('content'):
                print(f"   Content length: {len(update_data.get('content', ''))} chars")
            print(f"   Token: {token[:20] if token else 'MISSING'}...")
            
            response = requests.post(
                update_url,
                json=update_data,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            
            # Log response details
            print(f"📥 WordPress response:")
            print(f"   Status: {response.status_code}")
            print(f"   Response preview: {response.text[:300] if response.text else 'empty'}...")
            print(f"=" * 60)
            
            post_update_success = response.status_code == 200
        else:
            # Only meta_description update - skip post update
            print(f"ℹ️ No content/title - only updating Yoast meta fields")
            post_update_success = True  # Consider success since we're only updating meta
        
        if post_update_success:
            # Parse response to verify what was updated
            if update_data:
                try:
                    wp_response = response.json()
                    print(f"✅ Post update successful")
                    print(f"   WP Post ID: {wp_response.get('id')}")
                    print(f"   WP Title: {wp_response.get('title', {}).get('rendered', 'N/A')[:50]}")
                    print(f"   WP Modified: {wp_response.get('modified')}")
                except:
                    print(f"✅ Post update returned 200 but couldn't parse response")
            else:
                print(f"ℹ️ Skipped post update - only updating meta fields")
            
            # Update Yoast SEO meta fields if provided
            yoast_title_updated = False
            yoast_desc_updated = False
            yoast_errors = []
            
            # Try to update Yoast fields via post meta
            if title or meta_description:
                try:
                    # Method 1: Try via meta field in same post update
                    meta_update = {"meta": {}}
                    if title:
                        # Yoast uses these meta keys
                        meta_update["meta"]["_yoast_wpseo_title"] = title
                    if meta_description:
                        meta_update["meta"]["_yoast_wpseo_metadesc"] = meta_description
                    
                    print(f"🔧 Attempting Yoast meta update: {meta_update}")
                    
                    meta_response = requests.post(
                        update_url,
                        json=meta_update,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    )
                    
                    print(f"🔧 Yoast meta response: {meta_response.status_code}")
                    
                    if meta_response.status_code == 200:
                        yoast_title_updated = bool(title)
                        yoast_desc_updated = bool(meta_description)
                    else:
                        # Method 2: Try Yoast REST API directly (if available)
                        yoast_errors.append(f"Meta update returned {meta_response.status_code}")
                        print(f"⚠️ Yoast meta via post meta failed: {meta_response.text[:200]}")
                        
                        # Try Yoast's own API endpoint
                        yoast_api_url = f"{site['site_url']}/wp-json/yoast/v1/metas"
                        yoast_payload = {
                            "post_id": post_id
                        }
                        if title:
                            yoast_payload["title"] = title
                        if meta_description:
                            yoast_payload["metadesc"] = meta_description
                        
                        try:
                            yoast_response = requests.post(
                                yoast_api_url,
                                json=yoast_payload,
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=10
                            )
                            print(f"🔧 Yoast API response: {yoast_response.status_code}")
                            if yoast_response.status_code == 200:
                                yoast_title_updated = bool(title)
                                yoast_desc_updated = bool(meta_description)
                        except Exception as ye:
                            yoast_errors.append(f"Yoast API: {str(ye)}")
                            print(f"⚠️ Yoast API failed: {ye}")
                            
                except Exception as e:
                    yoast_errors.append(str(e))
                    print(f"❌ Yoast meta update error: {e}")
            
            # Save to WordPress update history if page_path provided
            page_path = data.get("page_path")
            if page_path:
                import re
                changes = {}
                update_type_parts = []
                
                if title:
                    changes['title'] = title[:50] + '...' if len(title) > 50 else title
                    update_type_parts.append('title')
                if meta_description:
                    changes['description_length'] = len(meta_description)
                    update_type_parts.append('description')
                if content:
                    text_only = re.sub(r'<[^>]+>', '', content)
                    changes['body_words'] = len(text_only.split())
                    update_type_parts.append('body')
                
                update_type = '+'.join(update_type_parts) if update_type_parts else 'unknown'
                
                save_wordpress_update_to_history(
                    page_path=page_path,
                    update_type=update_type,
                    changes=changes,
                    triggered_by=data.get('triggered_by', 'manual')
                )
            
            result = {
                "success": True,
                "message": "Page uploaded successfully",
                "site": site["name"],
                "post_title_updated": bool(title and "title" in update_data),
                "content_updated": bool(content),
                "yoast_title_updated": yoast_title_updated,
                "yoast_desc_updated": yoast_desc_updated
            }
            
            # Add warnings if Yoast update failed
            if (title or meta_description) and not (yoast_title_updated or yoast_desc_updated):
                result["warning"] = "Title/Description שונו בפוסט אבל ייתכן ש-Yoast SEO לא התעדכן. יש לבדוק ידנית או להפעיל תוסף שחושף את ה-meta fields."
                if yoast_errors:
                    result["yoast_errors"] = yoast_errors
            
            # Add cleanup info if content was processed
            if content:
                result["cleanup_info"] = cleanup_info
            return jsonify(result)
        elif response.status_code == 403:
            jwt_tokens[site_id] = None
            return jsonify({
                "success": False,
                "error": "Authentication expired. Please reconnect."
            }), 403
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to upload: {response.text}"
            }), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Connection timed out"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def calculate_word_count(html_content):
    """Calculate word count from HTML content"""
    from bs4 import BeautifulSoup
    import re
    
    if not html_content:
        return 0
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Count words (split by whitespace)
        words = [w for w in text.split() if len(w) > 0]
        return len(words)
    except Exception as e:
        print(f"Error calculating word count: {e}")
        return 0

@app.route('/api/page/info', methods=['GET'])
def get_page_info():
    """Get page_info.json for a page folder"""
    try:
        page_path = request.args.get('path')
        if not page_path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        page_folder = get_page_folder(page_path)
        info_path = BASE_DIR / page_folder / "page_info.json"
        
        if not info_path.exists():
            return jsonify({
                "success": False,
                "error": "page_info.json not found",
                "has_info": False
            })
        
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        # Calculate word_count if not present
        if 'word_count' not in info:
            # Find HTML file in the folder
            folder_path = BASE_DIR / page_folder
            html_files = list(folder_path.glob("*.html"))
            html_file = None
            for hf in html_files:
                if '_backup' not in hf.name.lower():
                    html_file = hf
                    break
            
            if html_file and html_file.exists():
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                word_count = calculate_word_count(html_content)
                info['word_count'] = word_count
                
                # Save updated info
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "has_info": True,
            "info": info
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/update-info', methods=['POST'])
def update_page_info():
    """Update page_info.json with new post_id and keyword"""
    try:
        data = request.json
        page_folder = data.get('page_folder')
        
        if not page_folder:
            return jsonify({"success": False, "error": "Missing page_folder"}), 400
        
        info_path = BASE_DIR / page_folder / "page_info.json"
        
        # Load existing or create new
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
        else:
            info = {"page_name": Path(page_folder).name}
        
        # Update fields
        if 'post_id' in data:
            info['post_id'] = str(data['post_id'])
        if 'keyword' in data:
            info['keyword'] = data['keyword']
        if 'url' in data:
            info['url'] = data['url']
        
        # Save
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Updated page_info.json: post_id={info.get('post_id')}, keyword={info.get('keyword')}")
        
        return jsonify({
            "success": True,
            "message": "page_info.json updated",
            "info": info
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/edit-heading', methods=['POST'])
def edit_heading():
    """Edit a heading in the HTML file"""
    try:
        data = request.json
        file_path = data.get('file_path')
        tag_type = data.get('tag_type', '').lower()  # h1, h2, h3, etc.
        old_text = data.get('old_text', '')
        new_text = data.get('new_text', '')
        
        if not file_path or not tag_type or not old_text or not new_text:
            return jsonify({"success": False, "error": "Missing required parameters"}), 400
        
        # Validate tag type
        if tag_type not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return jsonify({"success": False, "error": f"Invalid tag type: {tag_type}"}), 400
        
        # Build full path
        full_path = BASE_DIR / file_path
        if not full_path.exists():
            return jsonify({"success": False, "error": f"File not found: {file_path}"}), 404
        
        # Read file
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find and update the heading
        headings = soup.find_all(tag_type)
        updated = False
        
        for heading in headings:
            # Get text content (strip whitespace)
            heading_text = heading.get_text(strip=True)
            if heading_text == old_text.strip():
                # Preserve any child elements (like spans, links) but update text
                # If heading has only text, replace it
                if len(heading.contents) == 1 and isinstance(heading.contents[0], str):
                    heading.string = new_text
                else:
                    # More complex structure - update text nodes
                    # Find the main text node and update it
                    for child in heading.children:
                        if isinstance(child, str) and old_text.strip() in child:
                            child.replace_with(child.replace(old_text.strip(), new_text))
                            break
                    else:
                        # Fallback: clear and set new text
                        heading.clear()
                        heading.string = new_text
                updated = True
                break
        
        if not updated:
            return jsonify({"success": False, "error": f"Heading not found: {old_text[:50]}..."}), 404
        
        # Save file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"✅ Updated {tag_type} heading: '{old_text[:30]}...' -> '{new_text[:30]}...'")
        
        return jsonify({
            "success": True,
            "message": f"Heading updated successfully",
            "tag_type": tag_type,
            "old_text": old_text,
            "new_text": new_text
        })
        
    except Exception as e:
        print(f"❌ Error editing heading: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/remove-link', methods=['POST'])
def remove_duplicate_link():
    """Remove a specific link occurrence from the page HTML"""
    try:
        data = request.json
        page_folder = data.get('page_folder')
        target_url = data.get('url')
        anchor_text = data.get('anchor_text', '')
        occurrence_index = data.get('occurrence_index', 0)
        
        if not page_folder or not target_url:
            return jsonify({"success": False, "error": "Missing page_folder or url"}), 400
        
        # Find the HTML file
        folder_path = BASE_DIR / page_folder
        html_files = list(folder_path.glob("*.html"))
        
        # Exclude backup files
        content_files = [f for f in html_files if not f.name.startswith('wp_backup')]
        
        if not content_files:
            return jsonify({"success": False, "error": "No HTML file found"}), 404
        
        html_file = content_files[0]
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all links with this URL
        removed = False
        occurrence = 0
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Normalize URL for comparison
            if href.rstrip('/').lower() == target_url.rstrip('/').lower():
                link_text = link.get_text(strip=True)
                # If anchor text matches or we're at the right occurrence index
                if (anchor_text and link_text == anchor_text) or occurrence == occurrence_index:
                    # Replace link with just its text content
                    link.replace_with(link.get_text())
                    removed = True
                    print(f"🗑️ Removed link: {target_url} with anchor '{link_text}'")
                    break
                occurrence += 1
        
        if not removed:
            return jsonify({"success": False, "error": "Link not found"}), 404
        
        # Save the modified content
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return jsonify({
            "success": True,
            "message": "Link removed successfully",
            "file": str(html_file)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/remove-bold', methods=['POST'])
def remove_bold_formatting():
    """Remove bold/strong formatting from specific text"""
    try:
        data = request.json
        page_folder = data.get('page_folder')
        bold_text = data.get('bold_text', '')
        occurrence_index = data.get('occurrence_index', 0)
        
        if not page_folder or not bold_text:
            return jsonify({"success": False, "error": "Missing page_folder or bold_text"}), 400
        
        # Find the HTML file
        folder_path = BASE_DIR / page_folder
        html_files = list(folder_path.glob("*.html"))
        
        # Exclude backup files
        content_files = [f for f in html_files if not f.name.startswith('wp_backup')]
        
        if not content_files:
            return jsonify({"success": False, "error": "No HTML file found"}), 404
        
        html_file = content_files[0]
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find bold/strong elements with matching text
        removed = False
        occurrence = 0
        for tag_name in ['strong', 'b']:
            for bold in soup.find_all(tag_name):
                if bold.get_text(strip=True) == bold_text:
                    if occurrence == occurrence_index:
                        # Replace bold tag with just its text content
                        bold.replace_with(bold.get_text())
                        removed = True
                        print(f"🔓 Removed bold formatting from: '{bold_text}'")
                        break
                    occurrence += 1
            if removed:
                break
        
        if not removed:
            return jsonify({"success": False, "error": "Bold text not found"}), 404
        
        # Save the modified content
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return jsonify({
            "success": True,
            "message": "Bold formatting removed successfully",
            "file": str(html_file)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/html-content', methods=['GET'])
def get_page_html_content():
    """Get the current HTML content of a page"""
    try:
        page_folder = request.args.get('page_folder')
        if not page_folder:
            return jsonify({"success": False, "error": "Missing page_folder"}), 400
        
        folder_path = BASE_DIR / page_folder
        html_files = list(folder_path.glob("*.html"))
        
        # Exclude backup files
        content_files = [f for f in html_files if not f.name.startswith('wp_backup')]
        
        if not content_files:
            return jsonify({"success": False, "error": "No HTML file found"}), 404
        
        html_file = content_files[0]
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "content": content,
            "file": str(html_file)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/page/backup', methods=['GET'])
def get_page_backup():
    """Get WordPress backup files for a page"""
    try:
        page_path = request.args.get('path')
        if not page_path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        page_folder = get_page_folder(page_path)
        folder_path = BASE_DIR / page_folder
        
        # Use page folder name for backup file names
        page_name = folder_path.name
        
        meta_path = folder_path / f"{page_name}_backup_meta.json"
        content_path = folder_path / f"{page_name}_backup.html"
        
        # Also check old naming convention for backwards compatibility
        if not meta_path.exists():
            old_meta_path = folder_path / "wp_backup_meta.json"
            if old_meta_path.exists():
                meta_path = old_meta_path
        if not content_path.exists():
            old_content_path = folder_path / "wp_backup_content.html"
            if old_content_path.exists():
                content_path = old_content_path
        
        result = {
            "has_meta": meta_path.exists(),
            "has_content": content_path.exists(),
            "meta": None,
            "content": None
        }
        
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                result["meta"] = json.load(f)
        
        if content_path.exists():
            with open(content_path, 'r', encoding='utf-8') as f:
                result["content"] = f.read()
        
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Files ============

@app.route('/api/files', methods=['GET'])
def list_files():
    """List files in a folder"""
    try:
        folder = request.args.get('folder')
        if not folder:
            return jsonify({"success": False, "error": "Missing folder parameter"}), 400
        
        folder_path = BASE_DIR / folder
        
        if not folder_path.exists():
            return jsonify({"success": False, "error": "Folder not found", "files": []})
        
        files = []
        for f in folder_path.iterdir():
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(BASE_DIR)),
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime
                })
        
        return jsonify({
            "success": True,
            "files": files
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/file/content', methods=['GET'])
def get_file_content():
    """Get content of a file"""
    try:
        file_path = request.args.get('path')
        if not file_path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        full_path = BASE_DIR / file_path
        
        if not full_path.exists():
            return jsonify({"success": False, "error": "File not found"})
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "content": content
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def strip_wordpress_markers(content):
    """Remove WordPress Gutenberg block markers and fix invalid HTML from content"""
    import re
    if not content:
        return content
    
    # Remove opening markers: <!-- wp:html --> and variations
    content = re.sub(r'<!--\s*wp:html\s*-->\s*', '', content)
    # Remove closing markers: <!-- /wp:html --> and variations  
    content = re.sub(r'<!--\s*/wp:html\s*-->\s*', '', content)
    # Remove other common wp blocks
    content = re.sub(r'<!--\s*/?wp:[a-z-]+\s*(?:\{[^}]*\})?\s*-->\s*', '', content)
    
    # Fix invalid HTML: <p><style>...</style></p> → <style>...</style>
    content = re.sub(r'<p>\s*(<style[^>]*>)', r'\1', content, flags=re.IGNORECASE)
    content = re.sub(r'(</style>)\s*</p>', r'\1', content, flags=re.IGNORECASE)
    
    # Fix invalid HTML: <p><script>...</script></p> → <script>...</script>
    content = re.sub(r'<p>\s*(<script[^>]*>)', r'\1', content, flags=re.IGNORECASE)
    content = re.sub(r'(</script>)\s*</p>', r'\1', content, flags=re.IGNORECASE)
    
    # Fix WordPress auto-formatting that wraps block elements in <p>
    # This helps with elements like <div>, <table>, <section> etc.
    content = re.sub(r'<p>\s*(<(?:div|table|section|article|aside|header|footer|nav|ul|ol|dl|figure|figcaption|blockquote|pre|hr|form)[^>]*>)', r'\1', content, flags=re.IGNORECASE)
    content = re.sub(r'(</(?:div|table|section|article|aside|header|footer|nav|ul|ol|dl|figure|figcaption|blockquote|pre|form)>)\s*</p>', r'\1', content, flags=re.IGNORECASE)
    
    return content.strip()

@app.route('/api/file/save-content', methods=['POST'])
def save_file_content():
    """Save content to a file"""
    try:
        data = request.json
        file_path = data.get('path')
        content = data.get('content')
        
        if not file_path:
            return jsonify({"success": False, "error": "Missing path parameter"}), 400
        
        if content is None:
            return jsonify({"success": False, "error": "Missing content"}), 400
        
        # Clean WordPress markers from local files
        if file_path.endswith('.html') and not file_path.endswith('_backup.html'):
            content = strip_wordpress_markers(content)
        
        full_path = BASE_DIR / file_path
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "success": True,
            "message": f"File saved: {file_path}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - AI Detection ============

@app.route('/api/ai-detection', methods=['POST'])
def analyze_ai_content():
    """Analyze content for AI-generated patterns"""
    try:
        if not AI_DETECTION_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "AI detection module not available"
            }), 500
        
        data = request.json
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "No content provided"
            }), 400
        
        # Run analysis
        results = ai_detection.analyze(content)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Link Check ============

@app.route('/api/check-link', methods=['GET'])
def check_link():
    """Check if a URL is accessible (for broken link detection)"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({"ok": False, "status": 400, "error": "Missing URL"})
        
        import requests
        
        # Set timeout and headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            return jsonify({
                "ok": response.status_code < 400,
                "status": response.status_code,
                "url": url
            })
        except requests.exceptions.Timeout:
            return jsonify({"ok": False, "status": "Timeout", "url": url})
        except requests.exceptions.ConnectionError:
            return jsonify({"ok": False, "status": "Connection Error", "url": url})
        except Exception as e:
            return jsonify({"ok": False, "status": str(e), "url": url})
            
    except Exception as e:
        return jsonify({"ok": False, "status": 500, "error": str(e)})

# ============ API Routes - Competitor Analysis ============

@app.route('/api/seo/autocomplete', methods=['POST'])
def seo_autocomplete():
    """Fetch Google autocomplete suggestions via Apify"""
    try:
        data = request.json
        keyword = data.get('keyword')
        
        if not keyword:
            return jsonify({"success": False, "error": "Missing keyword"}), 400
        
        # Get Apify config
        apify_config = config.get('apify', {})
        token = apify_config.get('token')
        actor = apify_config.get('autocomplete_actor', 'afteru7~hshlmvt-gvgl')
        
        if not token:
            return jsonify({"success": False, "error": "Apify token not configured"}), 400
        
        # Call Apify autocomplete API - use token as query param to avoid Cloudflare issues
        url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={token}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        payload = {
            "country": "il",
            "language": "iw",
            "maxSuggestions": 20,
            "queries": [keyword],
            "url": "https://www.google.co.il/"
        }
        
        print(f"[Autocomplete] Fetching suggestions for: {keyword}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        print(f"[Autocomplete] Response status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            print(f"[Autocomplete] Response text: {response.text[:500]}")
            return jsonify({
                "success": False, 
                "error": f"Apify error: {response.status_code}"
            }), 400
        
        results = response.json()
        suggestions = []
        
        # Extract suggestions from response
        if isinstance(results, list):
            for item in results:
                if 'suggestions' in item:
                    suggestions.extend(item['suggestions'])
                elif 'query' in item:
                    suggestions.append(item['query'])
        
        print(f"[Autocomplete] Found {len(suggestions)} suggestions")
        
        return jsonify({
            "success": True,
            "keyword": keyword,
            "suggestions": suggestions[:20]  # Limit to 20
        })
        
    except Exception as e:
        print(f"[Autocomplete] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/serp', methods=['POST'])
def seo_serp():
    """Fetch Google SERP results via Apify (async with polling)"""
    try:
        data = request.json
        keyword = data.get('keyword')
        max_results = data.get('max_results', 10)  # Default 10
        our_url = data.get('our_url', '')  # Our site URL to highlight
        
        # Validate max_results
        max_results = min(max(1, int(max_results)), 10)
        
        if not keyword:
            return jsonify({"success": False, "error": "Missing keyword"}), 400
        
        # Get Apify config
        apify_config = config.get('apify', {})
        token = apify_config.get('token')
        actor = apify_config.get('serp_actor', 'nFJndFXA5zjCTuudP')
        
        if not token:
            return jsonify({"success": False, "error": "Apify token not configured"}), 400
        
        # Common headers with User-Agent
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        
        # Step 1: Start the SERP scraper run - use token as query param
        start_url = f"https://api.apify.com/v2/acts/{actor}/runs?token={token}"
        payload = {
            "aiMode": "aiModeWithSearchResults",
            "countryCode": "il",
            "forceExactMatch": False,
            "includeIcons": False,
            "includeUnfilteredResults": True,
            "languageCode": "iw",
            "maxPagesPerQuery": 1,
            "mobileResults": False,
            "queries": keyword,  # Dynamic - based on keyword parameter
            "resultsPerPage": 10,
            "saveHtml": False,
            "saveHtmlToKeyValueStore": True
        }
        
        print(f"[SERP] Starting scrape for: {keyword}")
        start_response = requests.post(start_url, headers=headers, json=payload, timeout=30)
        
        print(f"[SERP] Start response status: {start_response.status_code}")
        
        if start_response.status_code not in [200, 201, 202]:
            print(f"[SERP] Start response text: {start_response.text[:500]}")
            return jsonify({
                "success": False, 
                "error": f"Apify start error: {start_response.status_code}"
            }), 400
        
        run_data = start_response.json()
        run_id = run_data.get('data', {}).get('id')
        
        if not run_id:
            return jsonify({"success": False, "error": "No run ID returned"}), 400
        
        # Step 2: Poll for completion - use token as query param
        poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}"
        max_polls = 30  # Max 60 seconds
        
        for i in range(max_polls):
            time.sleep(2)
            poll_response = requests.get(poll_url, headers=headers, timeout=10)
            poll_data = poll_response.json()
            status = poll_data.get('data', {}).get('status')
            
            print(f"[SERP] Poll {i+1}: {status}")
            
            if status == 'SUCCEEDED':
                dataset_id = poll_data.get('data', {}).get('defaultDatasetId')
                break
            elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                return jsonify({"success": False, "error": f"Run failed: {status}"}), 400
        else:
            return jsonify({"success": False, "error": "Timeout waiting for results"}), 400
        
        # Step 3: Fetch results - use token as query param
        results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"
        results_response = requests.get(results_url, headers=headers, timeout=30)
        results = results_response.json()
        
        # Extract organic results
        organic_results = []
        our_rank = None
        
        if isinstance(results, list) and len(results) > 0:
            serp_data = results[0]
            organic = serp_data.get('organicResults', [])
            
            for i, result in enumerate(organic[:max_results]):
                result_url = result.get('url', '')
                is_ours = False
                
                # Check if this is our URL
                if our_url and our_url in result_url:
                    is_ours = True
                    our_rank = i + 1
                
                organic_results.append({
                    "rank": i + 1,
                    "url": result_url,
                    "title": result.get('title', ''),
                    "description": result.get('description', ''),
                    "is_ours": is_ours
                })
        
        print(f"[SERP] Found {len(organic_results)} organic results" + (f", our site at rank {our_rank}" if our_rank else ""))
        
        return jsonify({
            "success": True,
            "keyword": keyword,
            "results": organic_results,
            "our_rank": our_rank,
            "total_results": len(organic_results)
        })
        
    except Exception as e:
        print(f"[SERP] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============ API Routes - Keyword Research ============

def get_autocomplete_suggestions(keyword, token):
    """Helper: Fetch autocomplete suggestions from Apify"""
    apify_config = config.get('apify', {})
    actor = apify_config.get('autocomplete_actor', 'afteru7~hshlmvt-gvgl')
    
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={token}"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    payload = {
        "country": "il",
        "language": "iw",
        "maxSuggestions": 20,
        "queries": [keyword],
        "url": "https://www.google.co.il/"
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    if response.status_code not in [200, 201]:
        return []
    
    results = response.json()
    suggestions = []
    if isinstance(results, list):
        for item in results:
            if 'suggestions' in item:
                suggestions.extend(item['suggestions'])
            elif 'query' in item:
                suggestions.append(item['query'])
    
    return suggestions[:20]


def save_rank_to_history(page_path, keyword, position, url_checked):
    """Save rank position to seo_history.json in the page folder"""
    try:
        from datetime import datetime
        
        page_folder = get_page_folder(page_path)
        history_path = BASE_DIR / page_folder / 'seo_history.json'
        
        # Ensure directory exists
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        history = {"rank_history": [], "wordpress_updates": []}
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # Get today's date (for deduplication)
        today = datetime.now().strftime('%Y-%m-%d')
        current_datetime = datetime.now().isoformat()
        
        # Check if we already have an entry for this keyword today
        rank_history = history.get('rank_history', [])
        entry_updated = False
        
        for entry in rank_history:
            entry_date = entry.get('date', '')[:10]  # Get YYYY-MM-DD part
            if entry_date == today and entry.get('keyword', '').lower() == keyword.lower():
                # Update existing entry for today
                entry['date'] = current_datetime
                entry['position'] = position
                entry['url_checked'] = url_checked
                entry_updated = True
                print(f"[Rank History] Updated existing entry for '{keyword}' on {today}: #{position}")
                break
        
        if not entry_updated:
            # Add new entry
            rank_history.append({
                "date": current_datetime,
                "keyword": keyword,
                "position": position,
                "url_checked": url_checked
            })
            print(f"[Rank History] Added new entry for '{keyword}': #{position}")
        
        history['rank_history'] = rank_history
        
        # Save back
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"[Rank History] Saved to {history_path}")
        
    except Exception as e:
        print(f"[Rank History] Error saving: {e}")
        import traceback
        traceback.print_exc()


def save_wordpress_update_to_history(page_path, update_type, changes, triggered_by='manual'):
    """Save WordPress update to seo_history.json for tracking changes"""
    try:
        from datetime import datetime
        
        page_folder = get_page_folder(page_path)
        history_path = BASE_DIR / page_folder / 'seo_history.json'
        
        # Ensure directory exists
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        history = {"rank_history": [], "wordpress_updates": []}
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        current_datetime = datetime.now().isoformat()
        
        # Get current version number
        wp_updates = history.get('wordpress_updates', [])
        version = len(wp_updates) + 1
        
        # Add new update entry
        wp_updates.append({
            "date": current_datetime,
            "version": version,
            "update_type": update_type,  # 'title', 'description', 'body', 'full'
            "changes": changes,
            "triggered_by": triggered_by
        })
        
        history['wordpress_updates'] = wp_updates
        
        # Save back
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print(f"[WP History] Saved update v{version} to {history_path}")
        
    except Exception as e:
        print(f"[WP History] Error saving: {e}")
        import traceback
        traceback.print_exc()


def get_serp_related_searches(keyword, token, our_url=None):
    """Helper: Fetch related searches from SERP API and check ranking position"""
    apify_config = config.get('apify', {})
    actor = apify_config.get('serp_actor', 'nFJndFXA5zjCTuudP')
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    # Start the SERP scraper run
    start_url = f"https://api.apify.com/v2/acts/{actor}/runs?token={token}"
    payload = {
        "aiMode": "aiModeWithSearchResults",
        "countryCode": "il",
        "forceExactMatch": False,
        "includeIcons": False,
        "includeUnfilteredResults": True,
        "languageCode": "iw",
        "maxPagesPerQuery": 1,
        "mobileResults": False,
        "queries": keyword,  # Dynamic - based on keyword parameter
        "resultsPerPage": 10,
        "saveHtml": False,
        "saveHtmlToKeyValueStore": True
    }
    
    print(f"[SERP] Starting scrape for '{keyword}' with resultsPerPage=10, aiMode=aiModeWithSearchResults")
    start_response = requests.post(start_url, headers=headers, json=payload, timeout=30)
    empty_result = {'related': [], 'rank_position': None, 'organic_results': [], 'ai_mode_results': [], 'ai_rank_position': None, 'competitor_data': []}
    if start_response.status_code not in [200, 201, 202]:
        return empty_result
    
    run_data = start_response.json()
    run_id = run_data.get('data', {}).get('id')
    if not run_id:
        return empty_result
    
    # Poll for completion
    poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}"
    dataset_id = None
    
    for i in range(30):
        time.sleep(2)
        poll_response = requests.get(poll_url, headers=headers, timeout=10)
        poll_data = poll_response.json()
        status = poll_data.get('data', {}).get('status')
        
        if status == 'SUCCEEDED':
            dataset_id = poll_data.get('data', {}).get('defaultDatasetId')
            break
        elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
            return empty_result
    
    if not dataset_id:
        return empty_result
    
    # Fetch results
    results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"
    results_response = requests.get(results_url, headers=headers, timeout=30)
    results = results_response.json()
    
    # Save full response to debug file
    try:
        import json as json_module
        debug_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apify_debug_response.json')
        with open(debug_file, 'w', encoding='utf-8') as f:
            json_module.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[SERP] Full response saved to: {debug_file}")
    except Exception as e:
        print(f"[SERP] Could not save debug file: {e}")
    
    # Log what we got - detailed debug
    if isinstance(results, list) and len(results) > 0:
        serp_data_debug = results[0]
        organic_count = len(serp_data_debug.get('organicResults', []))
        has_ai = 'aiModeResult' in serp_data_debug
        ai_results_count = len(serp_data_debug.get('aiModeResult', {}).get('results', [])) if has_ai else 0
        print(f"[SERP] ========== APIFY RESPONSE DEBUG ==========")
        print(f"[SERP] Results received: {organic_count} organic results")
        print(f"[SERP] Top-level keys: {list(serp_data_debug.keys())}")
        print(f"[SERP] AI Overview exists: {has_ai} ({ai_results_count} sources)")
        if has_ai:
            print(f"[SERP] AI Mode keys: {list(serp_data_debug.get('aiModeResult', {}).keys())}")
        # Check for alternative AI Overview field names
        for key in ['aiModeResult', 'aiOverview', 'ai_overview', 'aiResult', 'featuredSnippet']:
            if key in serp_data_debug:
                print(f"[SERP] Found field '{key}': {type(serp_data_debug[key])}")
        print(f"[SERP] ============================================")
    
    # Extract related searches, AI mode results, competitor data, and check ranking position
    related_searches = []
    rank_position = None
    ai_mode_results = []
    ai_rank_position = None
    organic_results = []
    competitor_data = []
    
    # Normalize URL for comparison - remove protocol, www, trailing slash, decode
    def normalize_url(url):
        from urllib.parse import unquote
        url = url.lower().strip()
        url = url.replace('https://', '').replace('http://', '')
        url = url.replace('www.', '')
        url = url.rstrip('/')
        # Decode URL encoding
        try:
            url = unquote(url)
        except:
            pass
        return url
    
    print(f"[SERP] ====================================================")
    print(f"[SERP] PARSING APIFY RESPONSE")
    print(f"[SERP] ====================================================")
    
    if isinstance(results, list) and len(results) > 0:
        serp_data = results[0]
        print(f"[SERP] Top-level keys: {list(serp_data.keys())}")
        
        # Get organic results
        organic = serp_data.get('organicResults', [])
        print(f"[SERP] Organic results count: {len(organic)}")
        
        # Check ranking position if our_url is provided
        if our_url:
            our_url_normalized = normalize_url(our_url)
            # Also get just the domain for partial matching
            our_domain = our_url_normalized.split('/')[0]
            
            print(f"[SERP Rank] ============================================")
            print(f"[SERP Rank] Checking for URL: {our_url}")
            print(f"[SERP Rank] Normalized URL: {our_url_normalized}")
            print(f"[SERP Rank] Domain: {our_domain}")
            print(f"[SERP Rank] Found {len(organic)} organic results")
            print(f"[SERP Rank] ============================================")
            
            for i, result in enumerate(organic[:20]):
                result_url_raw = result.get('url', '')
                result_url = normalize_url(result_url_raw)
                
                # Also try encoded version
                result_url_encoded = result_url_raw.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                
                # Check multiple matching strategies
                is_match = (
                    our_url_normalized == result_url or  # Exact match (decoded)
                    our_url_normalized == result_url_encoded or  # Exact match (encoded)
                    our_url_normalized in result_url or  # Our URL is part of result
                    result_url in our_url_normalized or  # Result is part of our URL
                    our_domain == result_url.split('/')[0]  # Same domain
                )
                
                # Always show all results for debugging
                print(f"[SERP Rank] #{i+1}: {result_url}")
                
                if is_match and rank_position is None:
                    rank_position = i + 1  # 1-based position
                    print(f"[SERP Rank] ✅ MATCH FOUND! '{keyword}' at position {rank_position}")
        
        # Extract AI Mode Results
        ai_mode_data = serp_data.get('aiModeResult', {})
        if ai_mode_data:
            print(f"[AI Mode] Found AI Mode data")
            print(f"[AI Mode] Keys in aiModeResult: {list(ai_mode_data.keys())}")
            
            # Get AI mode description (the summary) - Apify uses 'text' not 'description'
            ai_description = ai_mode_data.get('text', ai_mode_data.get('description', ''))
            
            # Get AI mode results array (sources) - Apify uses 'sources' not 'results'
            ai_results_raw = ai_mode_data.get('sources', ai_mode_data.get('results', []))
            print(f"[AI Mode] Found {len(ai_results_raw)} sources, description length: {len(ai_description)}")
            
            for i, ai_result in enumerate(ai_results_raw):
                ai_mode_results.append({
                    'position': i + 1,
                    'title': ai_result.get('title', ''),
                    'url': ai_result.get('url', ''),
                    'description': ai_result.get('description', '')
                })
                
                # Check if our URL is in AI results
                if our_url:
                    ai_result_url = normalize_url(ai_result.get('url', ''))
                    our_url_normalized = normalize_url(our_url)
                    our_domain = our_url_normalized.split('/')[0]
                    
                    ai_is_match = (
                        our_url_normalized == ai_result_url or
                        our_url_normalized in ai_result_url or
                        ai_result_url in our_url_normalized or
                        our_domain == ai_result_url.split('/')[0]
                    )
                    
                    if ai_is_match and ai_rank_position is None:
                        ai_rank_position = i + 1
                        print(f"[AI Mode] ✅ Found in AI results at position {ai_rank_position}")
            
            # Store the AI overview description
            if ai_description:
                ai_mode_results.insert(0, {
                    'position': 0,
                    'title': 'AI Overview Summary',
                    'url': '',
                    'description': ai_description,
                    'is_summary': True
                })
            
            print(f"[AI Mode] Extracted {len(ai_mode_results)} AI mode results, our position: {ai_rank_position}")
        
        # Try different possible field names for related searches
        related = serp_data.get('relatedSearches', 
                  serp_data.get('relatedQueries', 
                  serp_data.get('related_searches', [])))
        
        print(f"[SERP Related] Found {len(related)} related queries")
        if related and len(related) > 0:
            print(f"[SERP Related] First item type: {type(related[0])}, sample: {related[0] if isinstance(related[0], str) else related[0].get('title', 'no title')}")
        
        for item in related:
            if isinstance(item, dict):
                title = item.get('title', item.get('query', item.get('text', '')))
                if title:
                    related_searches.append(title)
            elif isinstance(item, str):
                related_searches.append(item)
        
        # Extract organic results for display (top 20) with descriptions for competitor data
        for i, result in enumerate(organic[:20]):
            result_data = {
                'position': i + 1,
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'displayedUrl': result.get('displayedUrl', result.get('url', '')),
                'description': result.get('description', result.get('snippet', ''))
            }
            organic_results.append(result_data)
            
            # Add to competitor data (with description for prompt injection)
            competitor_data.append({
                'position': i + 1,
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'description': result.get('description', result.get('snippet', ''))
            })
    
    print(f"[SERP] ====================================================")
    print(f"[SERP] FINAL EXTRACTION SUMMARY:")
    print(f"[SERP]   - Related searches: {len(related_searches)}")
    print(f"[SERP]   - Organic results: {len(organic_results)}")
    print(f"[SERP]   - AI mode results: {len(ai_mode_results)}")
    print(f"[SERP]   - Rank position: {rank_position}")
    print(f"[SERP]   - AI rank position: {ai_rank_position}")
    print(f"[SERP] ====================================================")
    
    return {
        'related': related_searches,
        'rank_position': rank_position,
        'organic_results': organic_results,
        'ai_mode_results': ai_mode_results,
        'ai_rank_position': ai_rank_position,
        'competitor_data': competitor_data
    }


@app.route('/api/rank/check', methods=['POST'])
def check_rank():
    """Check ranking position for a keyword and URL"""
    try:
        data = request.json
        keyword = data.get('keyword')
        page_url = data.get('page_url')
        
        if not keyword or not page_url:
            return jsonify({"success": False, "error": "Missing keyword or page_url"}), 400
        
        apify_config = config.get('apify', {})
        token = apify_config.get('token')
        
        if not token:
            return jsonify({"success": False, "error": "Apify token not configured"}), 400
        
        print(f"[Rank Check] Checking rank for '{keyword}' at URL: {page_url}")
        
        # Use the SERP function which now checks rank
        result = get_serp_related_searches(keyword, token, page_url)
        
        return jsonify({
            "success": True,
            "keyword": keyword,
            "page_url": page_url,
            "rank_position": result.get('rank_position'),
            "found": result.get('rank_position') is not None
        })
        
    except Exception as e:
        print(f"[Rank Check] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/fetch', methods=['POST'])
def fetch_keywords():
    """Fetch both autocomplete AND related searches in one call, with rank tracking"""
    try:
        data = request.json
        keyword = data.get('keyword')
        page_url = data.get('page_url', '')  # URL to check ranking for
        page_path = data.get('page_path', '')  # For saving rank history
        
        if not keyword:
            return jsonify({"success": False, "error": "Missing keyword"}), 400
        
        apify_config = config.get('apify', {})
        token = apify_config.get('token')
        
        if not token:
            return jsonify({"success": False, "error": "Apify token not configured"}), 400
        
        print(f"[Keywords] Fetching keywords for: {keyword}")
        if page_url:
            print(f"[Keywords] Checking rank for URL: {page_url}")
        
        # 1. Get autocomplete suggestions
        print(f"[Keywords] Step 1: Fetching autocomplete...")
        autocomplete = get_autocomplete_suggestions(keyword, token)
        print(f"[Keywords] Found {len(autocomplete)} autocomplete suggestions")
        
        # 2. Get related searches from SERP (with rank checking, AI mode, competitor data)
        print(f"[Keywords] Step 2: Fetching related searches and checking rank...")
        serp_result = get_serp_related_searches(keyword, token, page_url)
        related = serp_result.get('related', [])
        rank_position = serp_result.get('rank_position')
        organic_results = serp_result.get('organic_results', [])
        ai_mode_results = serp_result.get('ai_mode_results', [])
        ai_rank_position = serp_result.get('ai_rank_position')
        competitor_data = serp_result.get('competitor_data', [])
        
        print(f"[Keywords] Found {len(related)} related searches, {len(organic_results)} organic results")
        print(f"[Keywords] Found {len(ai_mode_results)} AI mode results")
        if rank_position:
            print(f"[Keywords] Rank position for main keyword: #{rank_position}")
        if ai_rank_position:
            print(f"[Keywords] AI Overview position: #{ai_rank_position}")
        
        # 3. Save rank to history if we have position and page_path
        if page_path and rank_position is not None:
            save_rank_to_history(page_path, keyword, rank_position, page_url)
        
        # 4. Combine and deduplicate (basic)
        all_keywords = []
        seen = set()
        for kw in autocomplete + related:
            kw_lower = kw.strip().lower()
            if kw_lower and kw_lower not in seen:
                seen.add(kw_lower)
                all_keywords.append(kw.strip())
        
        print(f"[Keywords] Total unique keywords: {len(all_keywords)}")
        
        return jsonify({
            "success": True,
            "keyword": keyword,
            "autocomplete": autocomplete,
            "related": related,
            "combined": all_keywords,
            "rank_position": rank_position,  # Position in Google (1-20) or None
            "organic_results": organic_results,  # Top 20 Google results with title & URL & description
            "ai_mode_results": ai_mode_results,  # AI Overview results with title, URL, description
            "ai_rank_position": ai_rank_position,  # Position in AI Overview or None
            "competitor_data": competitor_data  # Top 20 competitors with descriptions for prompt injection
        })
        
    except Exception as e:
        print(f"[Keywords] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/process', methods=['POST'])
def process_keywords():
    """
    Process and deduplicate keywords with Hebrew morphology awareness:
    1. Filter plural/singular duplicates
    2. Cluster semantic variants
    3. Return cleaned list with clusters
    """
    try:
        data = request.json
        # Support both old format (combined list) and new format (separate lists with sources)
        autocomplete_keywords = data.get('autocomplete', [])
        related_keywords = data.get('related', [])
        keywords = data.get('keywords', [])  # Fallback for old format
        main_keyword = data.get('main_keyword', '')
        
        # Build keyword list with source tracking
        keywords_with_source = []
        if autocomplete_keywords or related_keywords:
            # New format - track sources
            for kw in autocomplete_keywords:
                keywords_with_source.append({'keyword': kw, 'source': 'autocomplete'})
            for kw in related_keywords:
                keywords_with_source.append({'keyword': kw, 'source': 'related'})
        else:
            # Old format - no source info
            for kw in keywords:
                keywords_with_source.append({'keyword': kw, 'source': 'unknown'})
        
        if not keywords_with_source:
            return jsonify({"success": False, "error": "No keywords provided"}), 400
        
        # Hebrew plural/singular suffixes
        plural_suffixes = ['ות', 'ים', 'יות', 'אות']
        
        # Semantic synonym groups (common Hebrew variations)
        synonym_groups = [
            ['מיידית', 'מיידי', 'מהירה', 'מהיר', 'בזק', 'דחופה', 'דחוף', 'מידית'],
            ['זולה', 'זול', 'זולות', 'זולים', 'במחיר נמוך', 'משתלמת'],
            ['טובה', 'טוב', 'טובות', 'טובים', 'איכותית', 'מומלצת'],
            ['קלה', 'קל', 'פשוטה', 'פשוט', 'נוחה', 'נוח'],
            ['ללא', 'בלי', 'אין'],
            ['עם', 'כולל'],
        ]
        
        def get_base_form(word):
            """Remove common Hebrew plural suffixes"""
            for suffix in plural_suffixes:
                if word.endswith(suffix) and len(word) > len(suffix) + 2:
                    return word[:-len(suffix)]
            return word
        
        def find_synonym_group(word):
            """Find which synonym group a word belongs to"""
            word_lower = word.lower()
            for i, group in enumerate(synonym_groups):
                if word_lower in [s.lower() for s in group]:
                    return i
            return None
        
        def extract_keywords_from_phrase(phrase, main_kw):
            """Extract the unique part from a keyphrase (removing main keyword)"""
            main_words = set(main_kw.lower().split())
            phrase_words = phrase.lower().split()
            unique_words = [w for w in phrase_words if w not in main_words]
            return ' '.join(unique_words)
        
        # Process keywords
        clusters = []
        processed = set()
        unique_topics = []
        
        for kw_item in keywords_with_source:
            kw = kw_item['keyword']
            source = kw_item['source']
            kw_stripped = kw.strip()
            if not kw_stripped or kw_stripped.lower() in processed:
                continue
            
            # Extract unique part (without main keyword)
            unique_part = extract_keywords_from_phrase(kw_stripped, main_keyword)
            
            # Check if it's a plural variant of something we've seen
            base_form = get_base_form(unique_part)
            
            # Check if semantically similar to existing cluster
            found_cluster = False
            for cluster in clusters:
                cluster_base = get_base_form(cluster['primary'])
                
                # Check plural/singular match
                if base_form == cluster_base or unique_part == cluster_base:
                    cluster['variants'].append(kw_stripped)
                    cluster['type'] = 'plural'
                    found_cluster = True
                    break
                
                # Check synonym match
                kw_synonym_group = find_synonym_group(unique_part)
                cluster_synonym_group = find_synonym_group(cluster['primary'])
                if kw_synonym_group is not None and kw_synonym_group == cluster_synonym_group:
                    cluster['variants'].append(kw_stripped)
                    cluster['type'] = 'semantic'
                    found_cluster = True
                    break
            
            if not found_cluster:
                # New cluster - include source
                clusters.append({
                    'primary': kw_stripped,
                    'variants': [],
                    'type': 'unique',
                    'unique_part': unique_part,
                    'source': source  # Track if from autocomplete or related
                })
                if unique_part:
                    unique_topics.append(unique_part)
            
            processed.add(kw_stripped.lower())
        
        # Build final keyword list (primaries only)
        final_keywords = [c['primary'] for c in clusters]
        
        # Count by source
        autocomplete_count = len([c for c in clusters if c.get('source') == 'autocomplete'])
        related_count = len([c for c in clusters if c.get('source') == 'related'])
        
        print(f"[Keywords Process] Input: {len(keywords_with_source)}, Output: {len(final_keywords)} clusters ({autocomplete_count} autocomplete, {related_count} related)")
        
        return jsonify({
            "success": True,
            "clusters": clusters,
            "final_keywords": final_keywords,
            "unique_topics": unique_topics,
            "stats": {
                "input_count": len(keywords_with_source),
                "output_count": len(final_keywords),
                "plural_merged": len([c for c in clusters if c['type'] == 'plural']),
                "semantic_merged": len([c for c in clusters if c['type'] == 'semantic']),
                "from_autocomplete": autocomplete_count,
                "from_related": related_count
            }
        })
        
    except Exception as e:
        print(f"[Keywords Process] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/save', methods=['POST'])
def save_keywords():
    """Save fetched keywords to page_info.json"""
    try:
        data = request.json
        page_path = data.get('page_path')
        keywords_data = data.get('keywords_data')
        
        print(f"[Keywords Save] ========================================")
        print(f"[Keywords Save] Received request for: {page_path}")
        print(f"[Keywords Save] Keywords count: {len(keywords_data.get('final_keywords', [])) if keywords_data else 0}")
        
        if not page_path or not keywords_data:
            print(f"[Keywords Save] ❌ Missing data: page_path={bool(page_path)}, keywords_data={bool(keywords_data)}")
            return jsonify({"success": False, "error": "Missing page_path or keywords_data"}), 400
        
        # Use the same path calculation as other functions
        page_folder = get_page_folder(page_path)
        page_info_path = BASE_DIR / page_folder / 'page_info.json'
        
        print(f"[Keywords Save] page_folder: {page_folder}")
        print(f"[Keywords Save] Full path: {page_info_path}")
        print(f"[Keywords Save] Path exists: {page_info_path.parent.exists()}")
        
        # Load existing page_info or create new
        page_info = {}
        if page_info_path.exists():
            with open(page_info_path, 'r', encoding='utf-8') as f:
                page_info = json.load(f)
        
        # Add keywords data
        page_info['fetched_keywords'] = keywords_data
        
        # Ensure directory exists
        page_info_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save back
        with open(page_info_path, 'w', encoding='utf-8') as f:
            json.dump(page_info, f, ensure_ascii=False, indent=2)
        
        print(f"[Keywords Save] ✅ SUCCESS! Saved {len(keywords_data.get('final_keywords', []))} keywords for {page_path}")
        print(f"[Keywords Save] ========================================")
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"[Keywords Save] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/delete', methods=['POST'])
def delete_keyword():
    """Delete a specific keyword from page_info.json"""
    try:
        data = request.json
        page_path = data.get('page_path')
        keyword = data.get('keyword')
        
        if not page_path or not keyword:
            return jsonify({"success": False, "error": "Missing page_path or keyword"}), 400
        
        # Use the same path calculation as other functions
        page_folder = get_page_folder(page_path)
        page_info_path = BASE_DIR / page_folder / 'page_info.json'
        
        print(f"[Keywords Delete] Deleting '{keyword}' from: {page_info_path}")
        
        if not page_info_path.exists():
            return jsonify({"success": False, "error": "page_info.json not found"}), 404
        
        # Load page_info
        with open(page_info_path, 'r', encoding='utf-8') as f:
            page_info = json.load(f)
        
        if 'fetched_keywords' not in page_info:
            return jsonify({"success": False, "error": "No keywords found"}), 404
        
        kw_data = page_info['fetched_keywords']
        
        # Remove from final_keywords
        if 'final_keywords' in kw_data:
            kw_data['final_keywords'] = [k for k in kw_data['final_keywords'] if k != keyword]
        
        # Remove from clusters
        if 'clusters' in kw_data:
            kw_data['clusters'] = [c for c in kw_data['clusters'] if c.get('primary') != keyword]
        
        # Save back
        with open(page_info_path, 'w', encoding='utf-8') as f:
            json.dump(page_info, f, ensure_ascii=False, indent=2)
        
        print(f"[Keywords Delete] Deleted '{keyword}', remaining: {len(kw_data.get('final_keywords', []))} keywords")
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"[Keywords Delete] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/step/prompt', methods=['GET'])
def get_step_prompt():
    """Get the prompt that was sent to Claude for a specific step - full template with shortcodes replaced"""
    try:
        page_path = request.args.get('page_path')
        step = request.args.get('step')  # e.g., "step1", "step2"
        agent_type = request.args.get('agent_type', 'atomic')  # atomic or seo
        agent_id = request.args.get('agent_id')  # Optional: specific agent ID
        render_shortcodes = request.args.get('render', 'true').lower() == 'true'
        
        print(f"[Get Prompt] page_path={page_path}, step={step}, agent_type={agent_type}, agent_id={agent_id}")
        
        if not page_path or not step:
            return jsonify({"success": False, "error": "Missing page_path or step"}), 400
        
        page_folder = get_page_folder(page_path)
        print(f"[Get Prompt] page_folder={page_folder}")
        
        # Determine agent ID if not provided
        if not agent_id:
            # Try to find agent by folder name (agent_type might be folder name like "הלוואות לעסקים")
            agents_folder = BASE_DIR / config.get("paths", {}).get("agents_folder", "agents")
            for agent_file in agents_folder.glob("*.json"):
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        agent_data = json.load(f)
                    if agent_data.get("folder_name") == agent_type:
                        agent_id = agent_data.get("id")
                        print(f"[Get Prompt] Found agent by folder_name: {agent_id}")
                        break
                except:
                    pass
            
            # Fallback to legacy logic
            if not agent_id:
                if agent_type == "atomic" or agent_type == "שיווק אטומי":
                    agent_id = "atomic_marketing"
                else:
                    agent_id = "seo"
                print(f"[Get Prompt] Using fallback agent_id: {agent_id}")
        
        # Try to get full prompt template from agent configuration
        agent = get_agent_unified(agent_id)
        prompt_template = None
        step_num = int(step.replace('step', ''))
        
        if agent:
            # Check new format (steps array)
            if agent.get("steps") and len(agent.get("steps", [])) >= step_num:
                step_data = agent["steps"][step_num - 1]
                prompt_template = step_data.get("prompt_template")
            # Check old format (step1, step2, etc.)
            elif agent.get(step):
                step_data = agent.get(step, {})
                prompt_template = step_data.get("prompt_template")
        
        if prompt_template:
            # Render the template with shortcodes
            if render_shortcodes:
                # Get page info for keyword
                keyword = Path(page_path).stem
                html_path = BASE_DIR / page_folder / f"{keyword}.html"
                
                # Create shortcode engine - pass the HTML file path, not folder
                # because ShortcodeEngine.__init__ calls get_page_folder internally
                html_file_path = str(page_folder / f"{keyword}.html")
                print(f"[Get Prompt] Creating ShortcodeEngine with page_path={html_file_path}")
                engine = ShortcodeEngine(
                    page_path=html_file_path,
                    agent=agent,
                    step_num=step_num
                )
                print(f"[Get Prompt] Engine page_folder={engine.page_folder}")
                
                # Set context values
                step_prompt_file = agent.get(step, {}).get("agent") or agent.get(step, {}).get("prompt_file")
                if not step_prompt_file and agent.get("steps") and len(agent.get("steps", [])) >= step_num:
                    step_prompt_file = agent["steps"][step_num - 1].get("prompt_file", "")
                
                # Build full path for prompt file
                if step_prompt_file:
                    # Add .md extension if missing
                    if not step_prompt_file.endswith(".md"):
                        step_prompt_file_with_ext = step_prompt_file + ".md"
                    else:
                        step_prompt_file_with_ext = step_prompt_file
                    full_prompt_path = str(BASE_DIR / step_prompt_file_with_ext)
                else:
                    full_prompt_path = ""
                
                engine.context[f"STEP{step_num}_PROMPT_FILE"] = full_prompt_path
                engine.context["PROMPT_FILE_PATH"] = full_prompt_path  # Also set the generic one
                engine.context["PAGE_HTML_PATH"] = str(html_path)
                engine.context["PAGE_KEYWORD"] = keyword
                
                # Set output path
                agent_folder_name = agent.get("folder_name", "שיווק אטומי")
                output_name = "דוח שלב " + str(step_num) + ".md"
                if agent.get(step):
                    output_name = agent[step].get("output_name") or agent[step].get("output", {}).get("path", output_name)
                elif agent.get("steps") and len(agent.get("steps", [])) >= step_num:
                    output_name = agent["steps"][step_num - 1].get("output", {}).get("path", output_name)
                
                engine.context["OUTPUT_PATH"] = str(BASE_DIR / page_folder / agent_folder_name / output_name)
                
                # Set previous step report PATHS for step 2+ (not content - Claude will read the file)
                if step_num > 1:
                    agent_folder = BASE_DIR / page_folder / agent_folder_name
                    for prev_step in range(1, step_num):
                        # Get report name from agent config
                        prev_step_key = f"step{prev_step}"
                        prev_step_data = None
                        if agent.get("steps") and len(agent.get("steps", [])) >= prev_step:
                            prev_step_data = agent["steps"][prev_step - 1]
                        elif agent.get(prev_step_key):
                            prev_step_data = agent[prev_step_key]
                        
                        if prev_step_data:
                            prev_output = prev_step_data.get("output", {})
                            prev_report_name = prev_output.get("path") if isinstance(prev_output, dict) else None
                            if not prev_report_name:
                                prev_report_name = prev_step_data.get("output_name", f"דוח שלב {prev_step}.md")
                        else:
                            prev_report_name = f"דוח שלב {prev_step}.md"
                        
                        prev_report_path = agent_folder / prev_report_name
                        # Register the PATH (not content) - Claude will read the file
                        engine.step_reports[f"STEP{prev_step}_REPORT"] = str(prev_report_path)
                        print(f"[Get Prompt] Set STEP{prev_step}_REPORT path: {prev_report_path}")
                
                # Process the template
                rendered_prompt = engine.process(prompt_template)
            else:
                rendered_prompt = prompt_template
            
            return jsonify({
                "success": True,
                "prompt": rendered_prompt,
                "step": step,
                "agent_type": agent_type,
                "agent_id": agent_id,
                "source": "agent_template",
                "template_raw": prompt_template if not render_shortcodes else None
            })
        
        # Fallback to old prompt file - use agent folder_name dynamically
        agent_folder_name = agent.get("folder_name") if agent else agent_type
        if agent_folder_name == "atomic" or agent_folder_name == "atomic_marketing":
            agent_folder_name = "שיווק אטומי"
        elif agent_folder_name == "seo":
            agent_folder_name = "SEO"
        
        prompt_file = BASE_DIR / page_folder / agent_folder_name / f"prompt_{step}.txt"
        
        print(f"[Get Prompt] Looking for prompt_file={prompt_file}, exists={prompt_file.exists()}")
        
        if not prompt_file.exists():
            return jsonify({
                "success": False, 
                "error": f"לא נמצא פרומפט עבור {step}",
                "path": str(prompt_file)
            }), 404
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        return jsonify({
            "success": True,
            "prompt": prompt_content,
            "step": step,
            "agent_type": agent_type,
            "file_path": str(prompt_file),
            "source": "saved_file"
        })
        
    except Exception as e:
        print(f"[Get Prompt] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/scrape-competitors', methods=['POST'])
def seo_scrape_competitors():
    """Scrape competitor pages using Apify Web Scraper - ALL URLs in one batch"""
    try:
        data = request.json
        urls = data.get('urls', [])
        keyword = data.get('keyword', '')
        related_terms = data.get('related_terms', [])
        
        if not urls:
            return jsonify({"success": False, "error": "No URLs provided"}), 400
        
        # Get Apify config
        apify_config = config.get('apify', {})
        token = apify_config.get('token')
        
        if not token:
            return jsonify({"success": False, "error": "Apify token not configured"}), 400
        
        # Prepare all URLs for batch scraping
        urls_to_scrape = urls[:5]  # Max 5 competitors
        start_urls = [{"url": url, "method": "GET"} for url in urls_to_scrape]
        
        print(f"[Scrape] Batch scraping {len(start_urls)} URLs...")
        
        # Call Apify Web Scraper with all URLs at once
        scraper_url = f"https://api.apify.com/v2/acts/apify~web-scraper/run-sync-get-dataset-items?token={token}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        # Page function to extract content
        page_function = """async function pageFunction(context) {
            const $ = context.jQuery;
            
            // Get title
            const title = $('title').text().trim();
            
            // Get meta description
            const description = $('meta[name="description"]').attr('content') || '';
            
            // Get headings
            const headings = [];
            $('h1, h2, h3').each((i, el) => {
                const tag = el.tagName;
                const text = $(el).text().trim();
                if (text) headings.push(tag + ': ' + text);
            });
            
            // Get schemas
            const schemas = [];
            $('script[type="application/ld+json"]').each((i, el) => {
                try {
                    const data = JSON.parse($(el).text());
                    if (data['@type']) schemas.push(data['@type']);
                    if (Array.isArray(data)) {
                        data.forEach(item => { if (item['@type']) schemas.push(item['@type']); });
                    }
                } catch(e) {}
            });
            
            // Count media
            const imageCount = $('img').length;
            const imagesWithAlt = $('img[alt]').filter((i, el) => $(el).attr('alt').trim()).length;
            const videoCount = $('video, iframe[src*="youtube"], iframe[src*="vimeo"]').length;
            
            // Check for interactive elements
            const hasForm = $('form').length > 0;
            const hasCalculator = $('[class*="calculator"], [id*="calculator"]').length > 0;
            const hasSlider = $('input[type="range"]').length > 0;
            
            // Get body text (clean)
            $('script, style, nav, footer, header, aside').remove();
            const bodyText = $('body').text().trim().replace(/\\s+/g, ' ');
            
            // Author detection
            const author = $('[class*="author"], [rel="author"]').first().text().trim() || null;
            
            return {
                url: context.request.url,
                title: title,
                description: description,
                headings: headings.slice(0, 30),
                schemas: schemas,
                imageCount: imageCount,
                imagesWithAlt: imagesWithAlt,
                videoCount: videoCount,
                hasForm: hasForm,
                hasCalculator: hasCalculator,
                hasSlider: hasSlider,
                author: author,
                bodyText: bodyText.substring(0, 10000)
            };
        }"""
        
        payload = {
            "startUrls": start_urls,  # ALL URLs at once
            "proxyConfiguration": {"useApifyProxy": True},
            "renderJavaScript": True,
            "injectJQuery": True,
            "waitUntil": ["networkidle2"],
            "downloadCss": False,
            "downloadMedia": False,
            "respectRobotsTxtFile": True,
            "runMode": "DEVELOPMENT",
            "headless": True,
            "useChrome": False,
            "maxConcurrency": 5,  # Scrape all in parallel
            "pageFunction": page_function
        }
        
        print(f"[Scrape] Calling Apify Web Scraper for {len(start_urls)} URLs...")
        response = requests.post(scraper_url, headers=headers, json=payload, timeout=300)  # 5 min timeout for batch
        
        if response.status_code not in [200, 201]:
            print(f"[Scrape] Apify error {response.status_code}: {response.text[:500]}")
            return jsonify({
                "success": False, 
                "error": f"Apify error: {response.status_code}"
            }), 400
        
        results = response.json()
        print(f"[Scrape] Got {len(results)} results from Apify")
        
        # Map results back to original URL order
        results_by_url = {r.get('url', ''): r for r in results}
        
        competitors_data = []
        for i, url in enumerate(urls_to_scrape):
            page_data = results_by_url.get(url)
            
            if not page_data:
                competitors_data.append({
                    "rank": i + 1,
                    "url": url,
                    "error": "No data returned for this URL"
                })
                continue
            
            body_text = page_data.get('bodyText', '')
            title_text = page_data.get('title', '')
            
            # Word count
            words = body_text.split() if body_text else []
            word_count = len(words)
            
            # Check keyword presence
            text_lower = body_text.lower()
            keyword_in_h1 = any(keyword.lower() in h.lower() for h in page_data.get('headings', []) if h.startswith('H1:')) if keyword else False
            keyword_in_title = keyword.lower() in title_text.lower() if keyword else False
            
            # Semantic coverage
            related_found = [term for term in related_terms if term.lower() in text_lower]
            related_missing = [term for term in related_terms if term.lower() not in text_lower]
            
            # Interactive elements
            interactive = []
            if page_data.get('hasForm'): interactive.append('form_detected')
            if page_data.get('hasCalculator'): interactive.append('calculator_detected')
            if page_data.get('hasSlider'): interactive.append('slider_detected')
            
            # Image alt percentage
            img_count = page_data.get('imageCount', 0)
            img_with_alt = page_data.get('imagesWithAlt', 0)
            alt_percentage = round(img_with_alt / img_count * 100, 1) if img_count > 0 else 0
            
            competitors_data.append({
                "rank": i + 1,
                "url": url,
                "meta": {
                    "title": title_text,
                    "title_length": len(title_text),
                    "description": page_data.get('description', ''),
                    "schemas_found": list(set(page_data.get('schemas', [])))
                },
                "structure": {
                    "word_count": word_count,
                    "headings_structure": page_data.get('headings', []),
                    "has_table_of_contents": False,
                    "keyword_in_h1": keyword_in_h1,
                    "keyword_in_title": keyword_in_title
                },
                "media": {
                    "image_count": img_count,
                    "images_with_alt_percentage": alt_percentage,
                    "video_count": page_data.get('videoCount', 0)
                },
                "content_features": {
                    "interactive_elements": interactive,
                    "author_byline": page_data.get('author')
                },
                "semantic_coverage": {
                    "related_terms_found": related_found,
                    "related_terms_missing": related_missing
                },
                "cleaned_text_snippet": body_text[:5000] if body_text else ""
            })
            
            print(f"[Scrape] ✅ {i+1}. {url}: {word_count} words")
        
        print(f"[Scrape] Batch complete: {len(competitors_data)} competitors processed")
        
        return jsonify({
            "success": True,
            "competitors_data": competitors_data
        })
        
    except requests.exceptions.Timeout:
        print(f"[Scrape] Timeout after 300 seconds")
        return jsonify({"success": False, "error": "Timeout - הסריקה לקחה יותר מ-5 דקות"}), 400
    except Exception as e:
        print(f"[Scrape] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/scrape-single', methods=['POST'])
def seo_scrape_single():
    """Scrape a single URL and return full HTML content"""
    try:
        data = request.json
        url = data.get('url')
        keyword = data.get('keyword', '')
        
        if not url:
            return jsonify({"success": False, "error": "Missing URL"}), 400
        
        print(f"[ScrapeSingle] Scraping: {url}")
        
        # Use requests with a good user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Get the HTML content
        html_content = response.text
        
        # === VALIDATION: Detect blocked/captcha/empty pages ===
        blocked_indicators = [
            'לוודא שאינך רובוט',
            'verify you are human',
            'captcha',
            'recaptcha',
            'cloudflare',
            'please wait',
            'אנא המתן',
            'access denied',
            'גישה נדחתה',
            'bot detected',
            'security check',
            'בדיקת אבטחה',
            'just a moment',
            'checking your browser',
            'enable javascript',
            'הפעל javascript',
        ]
        
        html_lower = html_content.lower()
        for indicator in blocked_indicators:
            if indicator.lower() in html_lower:
                print(f"[ScrapeSingle] BLOCKED - detected indicator: '{indicator}' in {url}")
                return jsonify({
                    "success": False,
                    "error": f"האתר חסם את הסריקה (זוהה: {indicator})",
                    "blocked": True,
                    "url": url
                }), 200  # Return 200 so client can handle gracefully
        
        # Check for minimum meaningful content
        # Remove tags to check actual text content
        import re
        text_only = re.sub(r'<[^>]+>', ' ', html_content)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        word_count = len(text_only.split())
        
        if word_count < 50:
            print(f"[ScrapeSingle] TOO SHORT - only {word_count} words in {url}")
            return jsonify({
                "success": False,
                "error": f"התוכן קצר מדי ({word_count} מילים) - ייתכן שזה דף חסימה",
                "blocked": True,
                "url": url
            }), 200
        
        # Check if main content exists (basic heuristic)
        content_tags = ['<article', '<main', '<p>', '<div class="content', '<div class="entry']
        has_content_structure = any(tag in html_lower for tag in content_tags)
        
        if not has_content_structure and word_count < 200:
            print(f"[ScrapeSingle] NO CONTENT STRUCTURE - {url}")
            return jsonify({
                "success": False,
                "error": "לא נמצא מבנה תוכן תקין בעמוד",
                "blocked": True,
                "url": url
            }), 200
        
        print(f"[ScrapeSingle] Success: {len(html_content)} bytes, ~{word_count} words")
        
        return jsonify({
            "success": True,
            "url": url,
            "html": html_content,
            "content": html_content,  # Also return as 'content' for compatibility
            "status_code": response.status_code,
            "word_count_estimate": word_count
        })
        
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Timeout - העמוד לא הגיב תוך 30 שניות", "blocked": False}), 400
    except requests.exceptions.RequestException as e:
        print(f"[ScrapeSingle] Request error: {e}")
        return jsonify({"success": False, "error": str(e), "blocked": False}), 400
    except Exception as e:
        print(f"[ScrapeSingle] Error: {e}")
        return jsonify({"success": False, "error": str(e), "blocked": False}), 500


@app.route('/api/seo/analyze-gaps', methods=['POST'])
def seo_analyze_gaps():
    """Analyze gaps between my page and competitors using Claude Opus 4.5"""
    print("[AnalyzeGaps] Request received...")
    try:
        data = request.json
        keyword = data.get('keyword', '')
        page_path = data.get('pagePath', '')
        my_analysis = data.get('myAnalysis', {})
        competitor_analyses = data.get('competitorAnalyses', [])
        comparison_data = data.get('comparisonData', {})
        
        print(f"[AnalyzeGaps] Keyword: {keyword}, Competitors: {len(competitor_analyses)}")
        
        if not my_analysis or not competitor_analyses:
            return jsonify({"success": False, "error": "Missing analysis data"}), 400
        
        # Calculate averages and gaps
        def avg(values):
            return sum(values) / len(values) if values else 0
        
        def calc_gap(my_val, avg_val):
            if avg_val == 0:
                return "N/A"
            diff = my_val - avg_val
            percent = (diff / avg_val) * 100 if avg_val != 0 else 0
            if diff < 0:
                return f"{diff:.0f} ({percent:.0f}%)"
            return f"+{diff:.0f} ({percent:+.0f}%)"
        
        # Build structured comparison
        comp_summary = {
            "wordCount": {
                "mine": my_analysis.get('content', {}).get('wordCount', 0),
                "avg": avg([c.get('content', {}).get('wordCount', 0) for c in competitor_analyses]),
            },
            "keywordDensity": {
                "mine": my_analysis.get('content', {}).get('keywordDensity', 0),
                "avg": avg([c.get('content', {}).get('keywordDensity', 0) for c in competitor_analyses]),
            },
            "h2Count": {
                "mine": my_analysis.get('headings', {}).get('h2', {}).get('count', 0),
                "avg": avg([c.get('headings', {}).get('h2', {}).get('count', 0) for c in competitor_analyses]),
            },
            "h2SpamRatio": {
                "mine": my_analysis.get('headings', {}).get('h2', {}).get('spamRatio', 0),
                "avg": avg([c.get('headings', {}).get('h2', {}).get('spamRatio', 0) for c in competitor_analyses]),
            },
            "tables": {
                "mine": my_analysis.get('elements', {}).get('tables', 0),
                "avg": avg([c.get('elements', {}).get('tables', 0) for c in competitor_analyses]),
            },
            "images": {
                "mine": my_analysis.get('elements', {}).get('images', 0),
                "avg": avg([c.get('elements', {}).get('images', 0) for c in competitor_analyses]),
            },
            "lists": {
                "mine": my_analysis.get('elements', {}).get('ulLists', 0) + my_analysis.get('elements', {}).get('olLists', 0),
                "avg": avg([c.get('elements', {}).get('ulLists', 0) + c.get('elements', {}).get('olLists', 0) for c in competitor_analyses]),
            },
            "hasFaq": {
                "mine": my_analysis.get('sections', {}).get('hasFaq', False),
                "competitorsWithFaq": sum([1 for c in competitor_analyses if c.get('sections', {}).get('hasFaq', False)]),
            },
            "schemas": {
                "mine": len(my_analysis.get('meta', {}).get('schemas', [])),
                "avg": avg([len(c.get('meta', {}).get('schemas', [])) for c in competitor_analyses]),
            },
            "internalLinks": {
                "mine": my_analysis.get('links', {}).get('internal', 0),
                "avg": avg([c.get('links', {}).get('internal', 0) for c in competitor_analyses]),
            },
        }
        
        # Build the Claude Opus prompt
        prompt = f"""אתה מומחה SEO שמנתח פערים בין עמוד לקוח לבין מתחרים מובילים.

מילת מפתח: "{keyword}"

## נתוני השוואה מובנים:

### תוכן:
- מילים שלי: {comp_summary['wordCount']['mine']:,} | ממוצע מתחרים: {comp_summary['wordCount']['avg']:,.0f}
- צפיפות מילת מפתח שלי: {comp_summary['keywordDensity']['mine']:.2f}% | ממוצע: {comp_summary['keywordDensity']['avg']:.2f}%

### כותרות H2:
- כמות שלי: {comp_summary['h2Count']['mine']} | ממוצע: {comp_summary['h2Count']['avg']:.1f}
- אחוז H2 עם מילת מפתח שלי: {comp_summary['h2SpamRatio']['mine']}% | ממוצע: {comp_summary['h2SpamRatio']['avg']:.0f}%

### אלמנטים:
- טבלאות שלי: {comp_summary['tables']['mine']} | ממוצע: {comp_summary['tables']['avg']:.1f}
- תמונות שלי: {comp_summary['images']['mine']} | ממוצע: {comp_summary['images']['avg']:.1f}
- רשימות שלי: {comp_summary['lists']['mine']} | ממוצע: {comp_summary['lists']['avg']:.1f}

### סקשנים מיוחדים:
- FAQ אצלי: {'כן' if comp_summary['hasFaq']['mine'] else 'לא'} | מתחרים עם FAQ: {comp_summary['hasFaq']['competitorsWithFaq']}/{len(competitor_analyses)}
- סכמות Schema שלי: {comp_summary['schemas']['mine']} | ממוצע: {comp_summary['schemas']['avg']:.1f}

### קישורים:
- קישורים פנימיים שלי: {comp_summary['internalLinks']['mine']} | ממוצע: {comp_summary['internalLinks']['avg']:.1f}

## כותרות H2 שלי:
{chr(10).join(['- ' + h for h in my_analysis.get('headings', {}).get('h2', {}).get('texts', [])[:10]])}

## משימה:

כתוב דוח ממוקד בפורמט הבא. **אל תנתח את המתחרים - רק מה חסר אצלי ומה לתקן.**

## מה חסר בעמוד שלי

### 1. בעיות קריטיות (לתקן מיד)
רשימת בעיות עם checkbox לכל פריט, כולל:
- כמה לתקן/להוסיף (מספרים ספציפיים)
- למה זה קריטי

### 2. תוספות נדרשות (לשיפור דירוג)
רשימת דברים להוסיף עם כמויות מדויקות

### 3. שיפורים מומלצים (בונוס)
רשימת שיפורים אופציונליים

### 4. כותרות H2 מומלצות
אם יש ספאם בכותרות - תן 5-8 כותרות H2 חלופיות **ללא מילת המפתח** שרלוונטיות לנושא

הקפד על:
- עברית בלבד
- מספרים ספציפיים (לא "להוסיף עוד" אלא "להוסיף 3 טבלאות")
- פורמט checkbox: - [ ] תיאור הפעולה
- תעדוף ברור לפי השפעה על דירוג
"""

        # Call Claude Opus 4.5 API
        api_key = os.environ.get('ANTHROPIC_API_KEY', ANTHROPIC_API_KEY)
        
        if not api_key:
            return jsonify({"success": False, "error": "Anthropic API key not configured"}), 400
        
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        claude_payload = {
            "model": "claude-opus-4-20250514",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        print(f"[AnalyzeGaps] Calling Claude Opus 4.5 for: {keyword}")
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=claude_payload,
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"[AnalyzeGaps] Claude API error: {response.status_code} - {response.text}")
            return jsonify({"success": False, "error": f"Claude API error: {response.status_code}"}), 400
        
        result = response.json()
        analysis_text = result.get('content', [{}])[0].get('text', '')
        
        if not analysis_text:
            return jsonify({"success": False, "error": "Empty response from Claude"}), 400
        
        print(f"[AnalyzeGaps] Success: {len(analysis_text)} chars")
        
        # Save the report to file
        try:
            page_folder = Path(BASE_DIR) / Path(page_path).parent
            report_path = page_folder / "gap_analysis_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# ניתוח פערים - {keyword}\n\n")
                f.write(f"תאריך: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write(analysis_text)
            print(f"[AnalyzeGaps] Report saved to: {report_path}")
        except Exception as save_error:
            print(f"[AnalyzeGaps] Failed to save report: {save_error}")
        
        return jsonify({
            "success": True,
            "analysis": analysis_text,
            "comparison_summary": comp_summary
        })
        
    except Exception as e:
        print(f"[AnalyzeGaps] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/save-competitor-html', methods=['POST'])
def seo_save_competitor_html():
    """Save competitor HTML to page's competitors folder"""
    try:
        data = request.json
        page_path = data.get('page_path')
        competitor_url = data.get('url')
        competitor_html = data.get('html')
        competitor_index = data.get('index', 0)
        
        if not page_path or not competitor_html:
            return jsonify({"success": False, "error": "Missing page_path or html"}), 400
        
        # Get page folder
        page_folder = Path(BASE_DIR) / Path(page_path).parent
        competitors_folder = page_folder / "competitors" / "html"
        
        # Create folder if not exists
        competitors_folder.mkdir(parents=True, exist_ok=True)
        
        # Extract domain for filename
        from urllib.parse import urlparse
        domain = urlparse(competitor_url).netloc.replace('www.', '') if competitor_url else f"competitor_{competitor_index}"
        
        # Save HTML file
        html_file = competitors_folder / f"{domain}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(competitor_html)
        
        print(f"[SaveCompetitorHTML] Saved: {html_file}")
        
        return jsonify({
            "success": True,
            "saved_path": str(html_file),
            "domain": domain
        })
    except Exception as e:
        print(f"[SaveCompetitorHTML] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/load-competitor-html', methods=['GET'])
def seo_load_competitor_html():
    """Load saved competitor HTML files"""
    try:
        page_path = request.args.get('page_path')
        
        if not page_path:
            return jsonify({"success": False, "error": "Missing page_path"}), 400
        
        # Get page folder
        page_folder = Path(BASE_DIR) / Path(page_path).parent
        html_folder = page_folder / "competitors" / "html"
        
        if not html_folder.exists():
            return jsonify({"success": True, "exists": False, "competitors": []})
        
        # Load all HTML files
        competitors = []
        for html_file in html_folder.glob("*.html"):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            competitors.append({
                "domain": html_file.stem,
                "html": html_content,
                "file": str(html_file)
            })
        
        print(f"[LoadCompetitorHTML] Loaded {len(competitors)} HTML files")
        
        return jsonify({
            "success": True,
            "exists": len(competitors) > 0,
            "competitors": competitors
        })
    except Exception as e:
        print(f"[LoadCompetitorHTML] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/save-competitor-data', methods=['POST'])
def seo_save_competitor_data():
    """Save competitor analysis data to page's competitors folder"""
    try:
        data = request.json
        page_path = data.get('page_path')
        competitor_data = data.get('data', {})
        
        if not page_path:
            return jsonify({"success": False, "error": "Missing page_path"}), 400
        
        # Get page folder
        page_folder = Path(BASE_DIR) / Path(page_path).parent
        competitors_folder = page_folder / "competitors"
        
        # Create competitors folder if not exists
        competitors_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with date
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Save full analysis JSON
        analysis_file = competitors_folder / f"analysis_{date_str}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(competitor_data, f, ensure_ascii=False, indent=2)
        
        print(f"[SaveCompetitor] Saved analysis to: {analysis_file}")
        
        # Update page_info.json with keywords
        page_info_path = page_folder / "page_info.json"
        page_info = {}
        
        if page_info_path.exists():
            with open(page_info_path, 'r', encoding='utf-8') as f:
                page_info = json.load(f)
        
        # Add autocomplete and related keywords
        page_info['google_autocomplete'] = competitor_data.get('autocomplete_suggestions', [])
        page_info['related_keywords'] = competitor_data.get('related_keywords', [])
        page_info['last_competitor_scan'] = datetime.now().isoformat()
        
        with open(page_info_path, 'w', encoding='utf-8') as f:
            json.dump(page_info, f, ensure_ascii=False, indent=2)
        
        print(f"[SaveCompetitor] Updated page_info.json with keywords")
        
        return jsonify({
            "success": True,
            "saved_path": str(analysis_file),
            "page_info_updated": True
        })
        
    except Exception as e:
        print(f"[SaveCompetitor] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/analyze-competitors', methods=['POST'])
def seo_analyze_competitors():
    """Analyze competitors using Claude LLM"""
    try:
        data = request.json
        page_path = data.get('page_path')
        competitor_data = data.get('data', {})
        keyword = competitor_data.get('target_keyword', '')
        
        if not page_path or not competitor_data:
            return jsonify({"success": False, "error": "Missing page_path or data"}), 400
        
        # Build the Claude prompt
        prompt = f"""Role: You are an expert SEO Strategist specialized in competitive analysis for the Hebrew market.

Task: Analyze the search results for the keyword: "{keyword}".

I will provide you with a JSON containing technical data, semantic coverage analysis, and content snippets of the Top 5 competitors.

Your Goal: Create a strategic "Gap Analysis Report" that explains exactly how to outrank these competitors.

Competitor Data:
```json
{json.dumps(competitor_data, ensure_ascii=False, indent=2)}
```

Instructions:
1. **Full Context Analysis:** Analyze the content depth, structure, and coverage of each competitor.
2. **Semantic Gap:** Look at the 'semantic_coverage' field. Highlight which related terms are being used and which are missing.
3. **Information Gain:** What unique value does the #1 ranking site provide?
4. **Actionable Advice:** Provide specific advice on Structure, Content, and Media.

Output Format (in Hebrew):

## ניתוח אסטרטגי לביטוי: {keyword}

### 1. פיצוח ה-Intent והטון
* **מה המשתמש מחפש:** (Analyze user need based on search intent)
* **הטון המנצח:** (Recommended tone based on top results)

### 2. פערי תוכן וסמנטיקה (The Semantic Gap)
* **נושאים שחוזרים אצל כולם:** (Must-have topics found in all competitors)
* **הזדמנויות סמנטיות:** (Related terms and topics to include)
* **מה חסר אצל המתחרים:** (Gaps in competitor content we can exploit)

### 3. ה"אס" המנצח (Information Gain)
* **מה מייחד את מי שבמקום 1:** (What makes #1 unique)
* **איך לנצח אותו:** (How to beat #1)

### 4. המלצות מבנה וטכני
* **אורך מומלץ:** (Recommended word count based on analysis)
* **מבנה כותרות מומלץ:** (Suggested heading structure/outline)
* **סכמות נדרשות:** (Required Schema.org types)
* **אלמנטים אינטראקטיביים:** (Recommended interactive elements)

### 5. שורת המחץ (Action Plan)
3 Critical immediate actions to outrank competitors.
"""

        # Call Claude API
        api_key = os.environ.get('ANTHROPIC_API_KEY', ANTHROPIC_API_KEY)
        
        if not api_key:
            return jsonify({"success": False, "error": "Anthropic API key not configured"}), 400
        
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        claude_payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        print(f"[AnalyzeCompetitors] Calling Claude API for: {keyword}")
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=claude_payload,
            timeout=120
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False, 
                "error": f"Claude API error: {response.status_code}"
            }), 400
        
        result = response.json()
        analysis_text = result.get('content', [{}])[0].get('text', '')
        
        # Save the gap report
        page_folder = Path(BASE_DIR) / Path(page_path).parent
        competitors_folder = page_folder / "competitors"
        competitors_folder.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_file = competitors_folder / f"gap_report_{date_str}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(analysis_text)
        
        print(f"[AnalyzeCompetitors] Saved report to: {report_file}")
        
        return jsonify({
            "success": True,
            "analysis": analysis_text,
            "saved_path": str(report_file)
        })
        
    except Exception as e:
        print(f"[AnalyzeCompetitors] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/seo/load-competitor-data', methods=['GET'])
def seo_load_competitor_data():
    """Load existing competitor analysis data for a page"""
    try:
        page_path = request.args.get('page_path')
        
        if not page_path:
            return jsonify({"success": False, "error": "Missing page_path"}), 400
        
        page_folder = Path(BASE_DIR) / Path(page_path).parent
        competitors_folder = page_folder / "competitors"
        
        if not competitors_folder.exists():
            return jsonify({
                "success": True,
                "exists": False,
                "message": "No competitor data found"
            })
        
        # Find latest analysis file
        analysis_files = list(competitors_folder.glob("analysis_*.json"))
        report_files = list(competitors_folder.glob("gap_report_*.md"))
        
        latest_analysis = None
        latest_report = None
        
        if analysis_files:
            latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                latest_analysis = json.load(f)
        
        if report_files:
            latest_file = max(report_files, key=lambda x: x.stat().st_mtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                latest_report = f.read()
        
        return jsonify({
            "success": True,
            "exists": True,
            "analysis": latest_analysis,
            "report": latest_report
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ API Routes - File Save ============

@app.route('/api/file/save', methods=['POST'])
def save_file():
    """Save content to a file (for direct editing)"""
    try:
        data = request.json
        file_path = data.get('path')
        content = data.get('content')
        
        if not file_path or content is None:
            return jsonify({"success": False, "error": "Missing path or content"}), 400
        
        full_path = BASE_DIR / file_path
        
        if not full_path.exists():
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # Read original file to preserve structure
        with open(full_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Find body content boundaries and replace
        import re
        body_pattern = re.compile(r'(<body[^>]*>)(.*?)(</body>)', re.DOTALL | re.IGNORECASE)
        match = body_pattern.search(original_content)
        
        if match:
            # Replace only body content, preserve everything else
            new_content = original_content[:match.start(2)] + content + original_content[match.end(2):]
        else:
            # If no body tag found, replace entire content
            new_content = content
        
        # Backup original file
        backup_path = full_path.with_suffix('.html.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # Save new content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return jsonify({
            "success": True,
            "message": "File saved successfully",
            "backup": str(backup_path)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Run Annotation ============

@app.route('/api/workflow/run-annotation', methods=['POST'])
def run_annotation():
    """Run Claude Code with annotation prompt - uses same method as step1"""
    try:
        data = request.json
        page_path = data.get('page_path')
        prompt_path = data.get('prompt_path')
        prompt_content = data.get('prompt_content')
        
        if not page_path or not prompt_content:
            return jsonify({"success": False, "error": "Missing page_path or prompt_content"}), 400
        
        # Get page folder for log
        page_folder = Path(page_path).parent
        
        # Use the same log mechanism as agents
        page_log_file = get_log_file_for_page(page_path)
        clear_live_log(page_path)
        
        # Get Claude command and API key
        cmd = get_claude_command()
        api_key = ANTHROPIC_API_KEY
        
        # Build paths
        full_prompt_path = BASE_DIR / prompt_path
        html_path = BASE_DIR / page_path
        
        page_path_escaped = page_path.replace("\\", "/")
        prompt_path_escaped = prompt_path.replace("\\", "/")
        
        # Create the prompt for Claude
        user_prompt = f"קרא את קובץ ההוראות {full_prompt_path} ובצע את התיקונים על הקובץ {html_path}."
        user_prompt_escaped = user_prompt.replace("\\", "\\\\")
        
        # Create runner script (same pattern as step1)
        runner_script = TMP_FOLDER / "temp_run_annotation.py"
        
        runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🚀 ביצוע תיקונים מהעורך")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("📋 פרומפט: {prompt_path_escaped}")
log("")

prompt = """{user_prompt_escaped}"""

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output
claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10",
    prompt
]

process = subprocess.Popen(
    args,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)
'''

        with open(runner_script, 'w', encoding='utf-8') as f:
            f.write(runner_content)
        
        # Create batch file to run in visible terminal (same as other steps)
        batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
        batch_path = TMP_FOLDER / "temp_annotation_run.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Open in legacy CMD (visible terminal like other agents)
        global running_claude_process
        running_claude_process = subprocess.Popen(
            [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
            cwd=str(BASE_DIR)
        )
        
        # Mark page as running with PID
        set_page_running(page_path, "annotation", 1, running_claude_process.pid)
        
        return jsonify({
            "success": True,
            "message": "Started annotation execution",
            "log_path": str(page_log_file),
            "pid": running_claude_process.pid
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Run Agent (Title/Description) ============

@app.route('/api/prompt/run-agent', methods=['POST'])
def run_agent_prompt():
    """Run Claude Code with a dynamic agent prompt"""
    try:
        data = request.json
        page_path = data.get('page_path')
        prompt_content = data.get('prompt')
        agent_type = data.get('agent_type', 'title_description')
        output_path = data.get('output_path')
        
        if not page_path or not prompt_content:
            return jsonify({"success": False, "error": "Missing page_path or prompt"}), 400
        
        # Get page folder for log
        page_folder = Path(page_path).parent
        
        # Use the same log mechanism as agents
        page_log_file = get_log_file_for_page(page_path)
        clear_live_log(page_path)
        
        # Get Claude command and API key
        cmd = get_claude_command()
        api_key = ANTHROPIC_API_KEY
        
        # Save the prompt to a temp file
        prompt_file = TMP_FOLDER / "temp_agent_prompt.md"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        page_path_escaped = page_path.replace("\\", "/")
        
        # Create the prompt for Claude
        user_prompt = f"קרא את קובץ ההוראות {prompt_file} ובצע את המשימה."
        user_prompt_escaped = user_prompt.replace("\\", "\\\\")
        
        # Create runner script (same pattern as step1)
        runner_script = TMP_FOLDER / "temp_run_agent.py"
        
        runner_content = f'''# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "{api_key}"
os.chdir(r"{BASE_DIR}")

LIVE_LOG = r"{page_log_file}"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🏆 סוכן {agent_type}")
log("=" * 60)
log("")
log("📄 עמוד: {page_path_escaped}")
log("")

prompt = """{user_prompt_escaped}"""

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output
claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",
    "--verbose",
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10",
    prompt
]

process = subprocess.Popen(
    args,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"{BASE_DIR}"
)

try:
    for line in iter(process.stdout.readline, b''):
        try:
            decoded = line.decode('utf-8', errors='replace').strip()
            if not decoded:
                continue
            
            try:
                data = json.loads(decoded)
                msg_type = data.get("type", "")
                
                if msg_type == "assistant":
                    content = data.get("message", {{}}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {{text}}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {{tool_name}}")
                
                elif msg_type == "content_block_delta":
                    delta = data.get("delta", {{}})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {{text}}")
                
                elif msg_type == "result":
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {{e}}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)
'''

        with open(runner_script, 'w', encoding='utf-8') as f:
            f.write(runner_content)
        
        # Create batch file to run in visible terminal
        batch_content = f'''@echo off
chcp 65001 >nul
cd /d "{BASE_DIR}"
{PYTHON_CMD} "{runner_script}"
'''
        batch_path = TMP_FOLDER / "temp_agent_run.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Open in legacy CMD (visible terminal)
        global running_claude_process
        running_claude_process = subprocess.Popen(
            [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
            cwd=str(BASE_DIR)
        )
        
        # Mark page as running with PID
        set_page_running(page_path, agent_type, 1, running_claude_process.pid)
        
        return jsonify({
            "success": True,
            "message": f"Started {agent_type} agent",
            "log_path": str(page_log_file),
            "pid": running_claude_process.pid
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Prompt Save ============

@app.route('/api/prompt/save', methods=['POST'])
def save_prompt():
    """Save a generated prompt file"""
    try:
        data = request.json
        prompt_path = data.get('path')
        content = data.get('content')
        
        if not prompt_path or not content:
            return jsonify({"success": False, "error": "Missing path or content"}), 400
        
        full_path = BASE_DIR / prompt_path
        
        # Create directory if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "success": True,
            "path": str(full_path),
            "message": "Prompt saved successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ API Routes - Folders ============

@app.route('/api/folders', methods=['GET'])
def get_folders():
    """Get available folders for output selection"""
    try:
        folders = []
        
        # Add configured folders
        for key, path in config["paths"].items():
            if isinstance(path, str) and key not in ["csv_file"]:
                folder_path = BASE_DIR / path
                if folder_path.is_dir() or not folder_path.exists():
                    folders.append({"id": key, "path": path, "exists": folder_path.exists()})
            elif isinstance(path, list):
                for p in path:
                    folder_path = BASE_DIR / p
                    folders.append({"path": p, "exists": folder_path.exists()})
        
        return jsonify({"success": True, "folders": folders})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Static Files ============

@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML"""
    return send_from_directory(str(BASE_DIR), 'dashboard.html')

@app.route('/v2')
def serve_dashboard_v2():
    """Serve the v2 dashboard - uses original dashboard for full functionality"""
    # For now, serve the original dashboard.html which has all functionality
    # Once v2/dashboard is fully built, switch to: 
    # return send_from_directory(str(BASE_DIR / 'v2' / 'dashboard'), 'index.html')
    return send_from_directory(str(BASE_DIR), 'dashboard.html')

@app.route('/v2/<path:filename>')
def serve_v2_static(filename):
    """Serve static files from v2 dashboard folder"""
    return send_from_directory(str(BASE_DIR / 'v2' / 'dashboard'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files from js folder"""
    js_dir = BASE_DIR / 'js'
    return send_from_directory(str(js_dir), filename)

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(str(BASE_DIR), filename)

# ============ Git Integration ============

@app.route('/api/git/status', methods=['GET'])
def get_git_status():
    """Check if there are uncommitted changes and if behind remote"""
    try:
        # Fetch from remote to check for updates (silent)
        subprocess.run(['git', 'fetch'], capture_output=True, cwd=BASE_DIR)
        
        # Check local changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=BASE_DIR)
        has_changes = bool(result.stdout.strip())
        changed_files = len([l for l in result.stdout.strip().split('\n') if l]) if has_changes else 0
        
        # Get current branch
        branch = subprocess.run(['git', 'branch', '--show-current'],
                               capture_output=True, text=True, cwd=BASE_DIR)
        branch_name = branch.stdout.strip() or 'main'
        
        # Check if behind remote
        behind_check = subprocess.run(
            ['git', 'rev-list', '--count', f'HEAD..origin/{branch_name}'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        behind_count = int(behind_check.stdout.strip()) if behind_check.returncode == 0 else 0
        
        # Check if ahead of remote
        ahead_check = subprocess.run(
            ['git', 'rev-list', '--count', f'origin/{branch_name}..HEAD'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        ahead_count = int(ahead_check.stdout.strip()) if ahead_check.returncode == 0 else 0
        
        return jsonify({
            "success": True,
            "has_changes": has_changes,
            "branch": branch_name,
            "changed_files": changed_files,
            "behind": behind_count,
            "ahead": ahead_count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/git/pull', methods=['POST'])
def git_pull():
    """Pull latest changes from remote"""
    try:
        git_env = os.environ.copy()
        git_env['GIT_TERMINAL_PROMPT'] = '0'
        result = subprocess.run(['git', 'pull'], cwd=BASE_DIR, capture_output=True, text=True, env=git_env)
        success = result.returncode == 0
        return jsonify({
            "success": success,
            "output": result.stdout + result.stderr
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/git/push', methods=['POST'])
def git_push():
    """Add all, commit with auto message, and push"""
    try:
        git_env = os.environ.copy()
        git_env['GIT_TERMINAL_PROMPT'] = '0'
        
        message = (request.json or {}).get('message') or f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, check=True)
        subprocess.run(['git', 'commit', '-m', message], cwd=BASE_DIR)
        result = subprocess.run(['git', 'push'], cwd=BASE_DIR, capture_output=True, text=True, env=git_env)
        
        return jsonify({"success": result.returncode == 0, "output": result.stdout + result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/git/sync', methods=['POST'])
def git_sync():
    """Smart sync - pull first if behind, then push if has changes"""
    try:
        actions = []
        errors = []
        
        # Set environment to prevent Git from prompting for credentials
        git_env = os.environ.copy()
        git_env['GIT_TERMINAL_PROMPT'] = '0'
        git_env['GIT_ASKPASS'] = ''
        
        # First, fetch to check status
        subprocess.run(['git', 'fetch'], capture_output=True, cwd=BASE_DIR, env=git_env)
        
        # Check status
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                      capture_output=True, text=True, cwd=BASE_DIR)
        has_changes = bool(status_result.stdout.strip())
        
        # Get branch name
        branch = subprocess.run(['git', 'branch', '--show-current'],
                               capture_output=True, text=True, cwd=BASE_DIR)
        branch_name = branch.stdout.strip() or 'main'
        
        # Check if behind
        behind_check = subprocess.run(
            ['git', 'rev-list', '--count', f'HEAD..origin/{branch_name}'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        behind_count = int(behind_check.stdout.strip()) if behind_check.returncode == 0 else 0
        
        # Check if ahead
        ahead_check = subprocess.run(
            ['git', 'rev-list', '--count', f'origin/{branch_name}..HEAD'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        ahead_count = int(ahead_check.stdout.strip()) if ahead_check.returncode == 0 else 0
        
        # Step 1: Pull if behind
        if behind_count > 0:
            if has_changes:
                # Stash local changes first
                subprocess.run(['git', 'stash'], cwd=BASE_DIR, capture_output=True)
                actions.append(f"שמרתי {status_result.stdout.count(chr(10))} שינויים זמנית")
            
            pull_result = subprocess.run(['git', 'pull'], cwd=BASE_DIR, capture_output=True, text=True, env=git_env)
            if pull_result.returncode == 0:
                actions.append(f"משכתי {behind_count} עדכונים")
            else:
                errors.append(f"שגיאה במשיכה: {pull_result.stderr}")
            
            if has_changes:
                # Restore stashed changes
                stash_pop = subprocess.run(['git', 'stash', 'pop'], cwd=BASE_DIR, capture_output=True, text=True)
                if stash_pop.returncode == 0:
                    actions.append("שחזרתי שינויים מקומיים")
                elif "CONFLICT" in stash_pop.stdout or "CONFLICT" in stash_pop.stderr:
                    # There's a conflict - resolve by keeping the newer file
                    # Get list of conflicting files
                    conflict_result = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], 
                                                    cwd=BASE_DIR, capture_output=True, text=True)
                    conflict_files = conflict_result.stdout.strip().split('\n') if conflict_result.stdout.strip() else []
                    
                    for conflict_file in conflict_files:
                        if not conflict_file:
                            continue
                        file_path = BASE_DIR / conflict_file
                        
                        # Get local file modification time (from working directory before conflict)
                        try:
                            local_mtime = file_path.stat().st_mtime if file_path.exists() else 0
                        except:
                            local_mtime = 0
                        
                        # Get remote file time from git log
                        remote_time_result = subprocess.run(
                            ['git', 'log', '-1', '--format=%ct', f'origin/{branch_name}', '--', conflict_file],
                            cwd=BASE_DIR, capture_output=True, text=True
                        )
                        try:
                            remote_mtime = int(remote_time_result.stdout.strip()) if remote_time_result.stdout.strip() else 0
                        except:
                            remote_mtime = 0
                        
                        # Keep the newer version
                        if local_mtime > remote_mtime:
                            subprocess.run(['git', 'checkout', '--ours', conflict_file], cwd=BASE_DIR, capture_output=True)
                            actions.append(f"⚠️ קונפליקט ב-{conflict_file} - שמרתי גרסה מקומית (חדשה יותר)")
                        else:
                            subprocess.run(['git', 'checkout', '--theirs', conflict_file], cwd=BASE_DIR, capture_output=True)
                            actions.append(f"⚠️ קונפליקט ב-{conflict_file} - לקחתי גרסת שרת (חדשה יותר)")
                    
                    # Mark conflicts as resolved and commit
                    subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, capture_output=True)
                    subprocess.run(['git', 'stash', 'drop'], cwd=BASE_DIR, capture_output=True)
                else:
                    errors.append("קונפליקט בשחזור שינויים - צריך לפתור ידנית")
        
        # Recheck for changes after pull
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                      capture_output=True, text=True, cwd=BASE_DIR)
        has_changes = bool(status_result.stdout.strip())
        
        # Recheck ahead count
        ahead_check = subprocess.run(
            ['git', 'rev-list', '--count', f'origin/{branch_name}..HEAD'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        ahead_count = int(ahead_check.stdout.strip()) if ahead_check.returncode == 0 else 0
        
        # Step 2: Push if has changes or ahead
        if has_changes or ahead_count > 0:
            if has_changes:
                subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, check=True)
                message = f"Auto sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                subprocess.run(['git', 'commit', '-m', message], cwd=BASE_DIR)
                actions.append("שמרתי שינויים מקומיים")
            
            push_result = subprocess.run(['git', 'push'], cwd=BASE_DIR, capture_output=True, text=True, env=git_env)
            if push_result.returncode == 0:
                actions.append("דחפתי לשרת")
            else:
                errors.append(f"שגיאה בדחיפה: {push_result.stderr}")
        
        if not actions and not errors:
            actions.append("הכל מסונכרן!")
        
        return jsonify({
            "success": len(errors) == 0,
            "actions": actions,
            "errors": errors,
            "message": " → ".join(actions) if actions else "מסונכרן"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Server Control ============

@app.route('/api/server/restart', methods=['POST'])
def restart_server():
    """Restart by running start_dashboard.bat which does full cleanup"""
    import threading
    
    try:
        batch_file = BASE_DIR / "start_dashboard.bat"
        if batch_file.exists():
            # Start the batch file in a new console window
            subprocess.Popen(
                ['cmd', '/c', 'start', 'cmd', '/k', str(batch_file)],
                cwd=str(BASE_DIR),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        
        # Give time for response before shutdown
        def shutdown():
            time.sleep(1)
            os._exit(0)
        
        threading.Thread(target=shutdown).start()
        
        return jsonify({"success": True, "message": "Restarting..."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/server/reload-config', methods=['POST'])
def reload_config():
    """Reload configuration without full restart"""
    global config
    try:
        config = load_config()
        return jsonify({"success": True, "message": "Config reloaded"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Config API ============

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get public config values (UI settings, etc.)"""
    try:
        # Return only public/safe config values
        public_config = {
            "ui": config.get("ui", {}),
            "paths": {
                "editable_pages": config.get("paths", {}).get("editable_pages", {})
            }
        }
        return jsonify({"success": True, "config": public_config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Global Values API ============

@app.route('/api/global-values', methods=['GET'])
def get_global_values():
    """Get all global values from config"""
    try:
        global_values = config.get("global_values", {})
        return jsonify({"success": True, "values": global_values})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/global-values', methods=['POST'])
def save_global_value():
    """Save a global value to config"""
    global config
    try:
        data = request.json
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return jsonify({"success": False, "error": "Missing key"}), 400
        
        # Initialize global_values if not exists
        if "global_values" not in config:
            config["global_values"] = {}
        
        # Update or create the value
        if key in config["global_values"]:
            config["global_values"][key]["value"] = value
        else:
            config["global_values"][key] = {
                "name": key,
                "value": value,
                "description": ""
            }
        
        # Save to config.json
        config_path = BASE_DIR / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": f"Saved {key} = {value}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Main ============

if __name__ == '__main__':
    print("=" * 50)
    print("  Page Management Dashboard")
    print("=" * 50)
    
    # Kill existing process on port 5000 if needed
    import socket
    import subprocess
    import time
    
    def kill_port(port):
        """Find and kill process using port"""
        try:
            # Check if port is in use
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return False  # Port is free
            
            print(f"⚠️ Port {port} is in use. Killing process...")
            
            # Find PID using netstat
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True).decode()
            
            for line in output.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    print(f"  Found PID: {pid}")
                    # Kill process
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                    time.sleep(1) # Wait for release
                    return True
        except Exception as e:
            print(f"Error killing port {port}: {e}")
        return False

    kill_port(5000)
    
    print(f"  Server: http://localhost:5000")
    print(f"  Base Dir: {BASE_DIR}")
    print("=" * 50)
    
    # use_reloader=False prevents server restart when files change
    # This is critical for Full Auto mode - otherwise running_pages gets cleared!
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

