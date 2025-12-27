# -*- coding: utf-8 -*-
"""
Page Management Dashboard - Flask Server
מערכת ניהול עמודים עם תמיכה בסוכנים חד/דו/תלת-שלביים
"""

import os
import json
import csv
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path

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

# Load environment variables from multiple sources
load_dotenv()  # Load .env if exists
load_dotenv(Path(__file__).parent / "api_config.env")  # Load api_config.env

# Get Anthropic API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

app = Flask(__name__)
CORS(app)

# Track running Claude process
running_claude_process = None

# ============ Configuration ============

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """Save configuration to config.json"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# Global config
config = load_config()

# JWT tokens cache
jwt_tokens = {
    "main": None,
    "business": None
}

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
    agent = config["agents"].get(agent_id, {})
    agent_folder_name = agent.get("folder_name", agent.get("name", agent_id))
    return BASE_DIR / page_folder / agent_folder_name

def get_wordpress_site(url):
    """Determine which WordPress site to use based on URL"""
    if "/Business/" in url:
        return "business", config["wordpress"]["sites"]["business"]
    return "main", config["wordpress"]["sites"]["main"]

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
    
    for folder in config["paths"]["editable_pages"]:
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

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all configured agents"""
    try:
        return jsonify({
            "success": True, 
            "agents": config["agents"],
            "agent_files": get_agent_files()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/create', methods=['POST'])
def create_agent():
    """Create a new agent configuration"""
    try:
        data = request.json
        agent_id = data.get("id")
        agent_config = data.get("config")
        create_file = data.get("create_file", False)
        
        if not agent_id or not agent_config:
            return jsonify({"success": False, "error": "Missing agent id or config"}), 400
        
        # Add to config
        config["agents"][agent_id] = agent_config
        save_config(config)
        
        # Create agent file if requested
        if create_file:
            agent_type = agent_config.get("type", "single-step")
            template = generate_agent_template(agent_config.get("name", agent_id), agent_type)
            
            if agent_type == "two-step":
                # Create both files
                step1_path = BASE_DIR / agent_config["step1"]["agent"]
                step2_path = BASE_DIR / agent_config["step2"]["agent"]
                
                if not step1_path.exists():
                    step1_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(step1_path, 'w', encoding='utf-8') as f:
                        f.write(template["step1"])
                
                if not step2_path.exists():
                    step2_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(step2_path, 'w', encoding='utf-8') as f:
                        f.write(template["step2"])
            else:
                # Single step
                agent_path = BASE_DIR / agent_config["agent"]
                if not agent_path.exists():
                    agent_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(agent_path, 'w', encoding='utf-8') as f:
                        f.write(template)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update an existing agent configuration"""
    try:
        data = request.json
        if agent_id not in config["agents"]:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        config["agents"][agent_id] = data
        save_config(config)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/agents/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent configuration (keeps files)"""
    try:
        if agent_id not in config["agents"]:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        del config["agents"][agent_id]
        save_config(config)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
    """Get the log file path for a specific page"""
    # Create a safe filename from page path
    safe_name = Path(page_path).stem  # Get filename without extension
    # Remove any problematic characters
    safe_name = safe_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return LIVE_LOGS_FOLDER / f"{safe_name}_log.txt"

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
        
        cmd = config["claude_code"]["command"]
        
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
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        if agent["type"] not in ["two-step", "three-step", "four-step", "six-step"]:
            return jsonify({"success": False, "error": "Agent is not two/three/four/six-step"}), 400
        
        step1 = agent["step1"]
        agent_file = step1["agent"]
        agent_folder_name = agent.get("folder_name", "שיווק אטומי")
        output_name = step1.get("output_name", "דוח שלב 1.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
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
            cmd = config["claude_code"]["command"]
            
            # Get API key and paths
            api_key = ANTHROPIC_API_KEY
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            
            # Simple prompt - let Claude read the files itself
            # Create agent folder if needed
            output_folder.mkdir(parents=True, exist_ok=True)
            report_full_path = output_folder / output_name
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ובצע את ההוראות על הקובץ {page_full_path}. מילת מפתח: {keyword}. בסוף חובה לשמור את הדוח בנתיב המדויק: {report_full_path}"
            # Escape backslashes for the generated Python script
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            agent_file_escaped = agent_file.replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script that captures streaming JSON and writes to log
            runner_script = BASE_DIR / "temp_run_claude.py"
            
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

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output
claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",  # Print mode (non-interactive)
    "--verbose",  # Required for stream-json
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
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server that job is complete
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
python "{runner_script}"
'''
            batch_path = BASE_DIR / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Open in legacy CMD (bypass Windows Terminal)
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/k', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            # Mark page as running with PID
            set_page_running(page_path, agent_id, 1, running_claude_process.pid)
            
            print(f"[Step1] Running Claude Code with streaming for {page_path}")
            
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
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        # Check if this is a four-step or six-step agent
        if agent.get("type") not in ["four-step", "six-step"]:
            # For non-four/six-step agents, call the old step2 logic (now step3)
            return run_step3_fixes()
        
        step2 = agent.get("step2")
        if not step2:
            return jsonify({"success": False, "error": "Agent has no step2"}), 400
        
        agent_file = step2["agent"]
        agent_folder_name = agent.get("folder_name", "שיווק אטומי")
        output_name = step2.get("output_name", "דוח שלב 1 מורחב.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
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
            cmd = config["claude_code"]["command"]
            api_key = ANTHROPIC_API_KEY
            
            # Build paths
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            report1_full = BASE_DIR / report1_path
            
            # Build prompt for QA agent
            report_full_path = output_folder / output_name
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת דוח שלב 1: {report1_full} ואת קובץ ה-HTML: {page_full_path}. בדוק את הדוח, הרחב אותו והוסף הצעות טקסט מלאות. בסוף חובה לשמור את הדוח המורחב בנתיב המדויק: {report_full_path}"
            
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script
            runner_script = BASE_DIR / "temp_run_claude.py"
            
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
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

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
python "{runner_script}"
'''
            batch_path = BASE_DIR / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            subprocess.Popen(
                ['C:\\Windows\\System32\\conhost.exe', 'cmd.exe', '/c', str(batch_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            set_page_running(page_path, "step2", 2)
            
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
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        # For four-step/six-step agents, look at step3; for three-step, look at step2
        step_config = agent.get("step3") if agent.get("type") in ["four-step", "six-step"] else agent.get("step2")
        if not step_config:
            return jsonify({"success": False, "error": "Agent has no fixes step"}), 400
        
        agent_file = step_config["agent"]
        agent_folder_name = agent.get("folder_name", "שיווק אטומי")
        report_output_name = step_config.get("report_name", "דוח שלב 3.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Validate that input report exists (step 2 expanded report)
        if report_path:
            report_full = BASE_DIR / report_path
            if not report_full.exists():
                return jsonify({"success": False, "error": f"דוח מורחב לא נמצא: {report_path}. הרץ שלב 2 קודם!"}), 400
        
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
            cmd = config["claude_code"]["command"]
            api_key = ANTHROPIC_API_KEY
            
            # Build paths
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            report_full_path = BASE_DIR / report_path
            
            # Simple prompt - edit file in place, don't create new file
            report_save_path = output_folder / report_output_name
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת הדוח {report_full_path}. ערוך את הקובץ {page_full_path} ישירות עם כלי Edit (לא Write!) - אל תיצור קובץ חדש! בסוף חובה לשמור דוח סיכום בנתיב המדויק: {report_save_path}"
            # Escape backslashes for the generated Python script
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            report_path_escaped = report_path.replace("\\", "/")
            agent_file_escaped = agent_file.replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script that captures streaming JSON and writes to log
            runner_script = BASE_DIR / "temp_run_claude.py"
            
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
log("")

prompt = """{user_prompt_escaped}"""

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output
claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",  # Print mode (non-interactive)
    "--verbose",  # Required for stream-json
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
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server that job is complete
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
python "{runner_script}"
'''
            batch_path = BASE_DIR / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Open in legacy CMD (bypass Windows Terminal)
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/k', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            # Mark page as running with PID
            set_page_running(page_path, agent_id, 3, running_claude_process.pid)
            
            print(f"[Step3] Running Claude Code with streaming for {page_path}")
            
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
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
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
        agent_folder_name = agent.get("folder_name", "שיווק אטומי")
        report_output_name = step_config.get("report_name", "דוח דיבאג.md")
        
        # Calculate output folder based on new structure
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
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
            cmd = config["claude_code"]["command"]
            api_key = ANTHROPIC_API_KEY
            
            # Build paths
            agent_file_path = BASE_DIR / agent_file
            report1_full = BASE_DIR / report1_path
            report2_full = BASE_DIR / report2_path
            page_full_path = BASE_DIR / page_path
            # For 4-step: report1 is "דוח שלב 1 מורחב" (from QA), report2 is "דוח שלב 3" (from fixes)
            report_save_path = output_folder / report_output_name
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת הדוח המורחב: {report1_full} ודוח התיקונים: {report2_full}. בדוק את הקובץ {page_full_path} ומצא מה לא בוצע מהדוחות. ערוך את הקובץ ישירות עם כלי Edit (לא Write!) - אל תיצור קובץ חדש! בסוף חובה לשמור דוח דיבאג בנתיב המדויק: {report_save_path}"
            
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            # Clear live log
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            # Create runner script
            runner_script = BASE_DIR / "temp_run_claude.py"
            
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
log("")

prompt = """{user_prompt_escaped}"""

claude_cmd = r"{cmd}"
args = [
    claude_cmd,
    "-p",  # Print mode (non-interactive)
    "--verbose",  # Required for stream-json
    "--output-format", "stream-json",
    "--include-partial-messages",
    "--dangerously-skip-permissions",
    "--model", "opus",
    "--max-budget-usd", "10",
    prompt
]

log("🚀 מפעיל Claude Code...")
log("-" * 60)
log("")

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
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

# Notify server that job is complete
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
            
            # Create batch file
            batch_content = f'''@echo off
chcp 65001 >nul
echo ============================================================
echo   Running Claude Code - Step 3 Debug
echo ============================================================
python "{runner_script}"
echo.
echo ============================================================
echo   Step 3 finished!
echo ============================================================
'''
            batch_path = BASE_DIR / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Open in legacy CMD
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/k', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            # Mark page as running
            set_page_running(page_path, agent_id, 4, running_claude_process.pid)
            
            print(f"[Step4] Running Claude Code debug for {page_path}")
            
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
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        if agent.get("type") != "six-step":
            return jsonify({"success": False, "error": "Agent is not six-step"}), 400
        
        step5 = agent.get("step5")
        if not step5:
            return jsonify({"success": False, "error": "Agent has no step5"}), 400
        
        agent_file = step5["agent"]
        agent_folder_name = agent.get("folder_name", "SEO")
        report_output_name = step5.get("report_name", "דוח שלב 5.md")
        
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Validate that step 4 report exists
        step4_report_name = agent.get("step4", {}).get("report_name", "דוח שלב 4.md")
        step4_report_path = output_folder / step4_report_name
        if not step4_report_path.exists():
            return jsonify({"success": False, "error": f"דוח שלב 4 לא נמצא. הרץ שלב 4 קודם!"}), 400
        
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
            cmd = config["claude_code"]["command"]
            api_key = ANTHROPIC_API_KEY
            
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            
            report_full_path = output_folder / report_output_name
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path}. סרוק את הקובץ {page_full_path} והסר עקבות AI. ערוך את הקובץ ישירות עם כלי Edit (לא Write!). בסוף חובה לשמור דוח בנתיב המדויק: {report_full_path}"
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            runner_script = BASE_DIR / "temp_run_claude.py"
            
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
log("")

prompt = """{user_prompt_escaped}"""

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

log("🚀 מפעיל Claude Code...")
log("-" * 60)
log("")

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
            log(f"⚠️ שגיאה: {{e}}")

    process.wait()
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

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
python "{runner_script}"
'''
            batch_path = BASE_DIR / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/k', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            set_page_running(page_path, agent_id, 5, running_claude_process.pid)
            
            print(f"[Step5] Running Claude Code AI removal for {page_path}")
            
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
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        if agent.get("type") != "six-step":
            return jsonify({"success": False, "error": "Agent is not six-step"}), 400
        
        step6 = agent.get("step6")
        if not step6:
            return jsonify({"success": False, "error": "Agent has no step6"}), 400
        
        agent_file = step6["agent"]
        agent_folder_name = agent.get("folder_name", "SEO")
        report_output_name = step6.get("report_name", "דוח דיבאג AI.md")
        
        page_folder = get_page_folder(page_path)
        output_folder = BASE_DIR / page_folder / agent_folder_name
        
        # Validate that step 5 report exists
        if step5_report_path:
            step5_full = BASE_DIR / step5_report_path
            if not step5_full.exists():
                return jsonify({"success": False, "error": f"דוח שלב 5 לא נמצא. הרץ שלב 5 קודם!"}), 400
        
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
            cmd = config["claude_code"]["command"]
            api_key = ANTHROPIC_API_KEY
            
            agent_file_path = BASE_DIR / agent_file
            page_full_path = BASE_DIR / page_path
            step5_report_full = BASE_DIR / step5_report_path
            
            report_full_path = output_folder / report_output_name
            user_prompt = f"קרא את קובץ ההוראות {agent_file_path} ואת דוח שלב 5: {step5_report_full}. בדוק את הקובץ {page_full_path} שכל עקבות ה-AI הוסרו. ערוך את הקובץ ישירות עם כלי Edit אם צריך. בסוף חובה לשמור דוח בנתיב המדויק: {report_full_path}"
            user_prompt_escaped = user_prompt.replace("\\", "\\\\")
            page_path_escaped = page_path.replace("\\", "/")
            
            page_log_file = get_log_file_for_page(page_path)
            clear_live_log(page_path)
            
            runner_script = BASE_DIR / "temp_run_claude.py"
            
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
log("")

prompt = """{user_prompt_escaped}"""

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

log("🚀 מפעיל Claude Code...")
log("-" * 60)
log("")

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
            log(f"⚠️ שגיאה: {{e}}")

    process.wait()
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {{stderr[:500]}}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {{process.returncode}}")
log("=" * 60)

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
python "{runner_script}"
'''
            batch_path = BASE_DIR / "temp_claude_run.bat"
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            running_claude_process = subprocess.Popen(
                [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/k', str(batch_path)],
                cwd=str(BASE_DIR)
            )
            
            set_page_running(page_path, agent_id, 6, running_claude_process.pid)
            
            print(f"[Step6] Running Claude Code AI debug for {page_path}")
            
            return jsonify({
                "success": True,
                "mode": "claude",
                "page_path": page_path,
                "message": "Claude Code Step 6 running!"
            })
    except Exception as e:
        print(f"[Step6] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/workflow/single', methods=['POST'])
def run_single_step():
    """Run a single-step agent"""
    try:
        data = request.json
        agent_id = data.get("agent_id")
        page_path = data.get("page_path")
        mode = data.get("mode", "cursor")
        
        agent = config["agents"].get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
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
                [config["claude_code"]["command"], "-p", command],
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
        
        cmd = config["claude_code"]["command"]
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
        runner_script = BASE_DIR / "temp_run_claude.py"
        
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
    
except KeyboardInterrupt:
    process.terminate()
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
python "{runner_script}"
'''
        batch_path = BASE_DIR / "temp_claude_run.bat"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Open in legacy CMD
        running_claude_process = subprocess.Popen(
            [r'C:\Windows\System32\conhost.exe', 'cmd.exe', '/k', str(batch_path)],
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
    """Stop running Claude Code process"""
    global running_claude_process
    try:
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
        
        print("[Stop] Claude Code process stopped")
        return jsonify({
            "success": True,
            "message": "Claude Code stopped"
        })
    except Exception as e:
        print(f"[Stop] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/worklog', methods=['GET'])
def get_work_log():
    """Get the current work log content for a specific page"""
    try:
        page_path = request.args.get('page', '')
        
        if page_path:
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
        
        if log_file.exists():
            # Read last N lines
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Parse and format the content for display
            lines = content.split('\n')
            # Keep last 200 lines for performance
            if len(lines) > 200:
                lines = lines[-200:]
            
            return jsonify({
                "success": True,
                "content": '\n'.join(lines),
                "line_count": len(lines),
                "log_file": log_file.name
            })
        else:
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

# Active jobs tracking - key is page path, value is job info
active_jobs = {}
running_pages = {}  # Track which pages are currently running

def set_page_running(page_path, agent_id, step, pid=None):
    """Mark a page as running"""
    running_pages[page_path] = {
        "agent_id": agent_id,
        "step": step,
        "started": datetime.now().isoformat(),
        "pid": pid  # Store process ID for checking if still alive
    }
    # Save to file for persistence
    with open(BASE_DIR / "running_jobs.json", 'w', encoding='utf-8') as f:
        json.dump(running_pages, f, ensure_ascii=False)
    print(f"[Status] Page marked as running: {page_path} (step {step}, pid={pid})")
    print(f"[Status] Running pages: {list(running_pages.keys())}")

def set_page_complete(page_path):
    """Mark a page as complete"""
    if page_path in running_pages:
        del running_pages[page_path]
        with open(BASE_DIR / "running_jobs.json", 'w', encoding='utf-8') as f:
            json.dump(running_pages, f, ensure_ascii=False)

def clear_page_running(page_path):
    """Remove a page from running status (alias for set_page_complete)"""
    set_page_complete(page_path)

def load_running_pages():
    """Load running pages from file and verify processes are still running"""
    global running_pages
    jobs_file = BASE_DIR / "running_jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                loaded_pages = json.load(f)
            
            # Check each loaded page - only keep if not completed
            running_pages = {}
            for page_path, info in loaded_pages.items():
                log_file = get_log_file_for_page(page_path)
                should_keep = False
                
                if log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        
                        # If no completion marker, check if recent
                        if '🏁 סיום!' not in content and '✅ Claude סיים!' not in content:
                            mtime = log_file.stat().st_mtime
                            age = time.time() - mtime
                            if age < 300:  # 5 minutes
                                should_keep = True
                                print(f"[Startup] Process for {page_path} might still be running (log age: {age:.0f}s)")
                        else:
                            print(f"[Startup] Process for {page_path} already completed")
                    except:
                        pass
                
                if should_keep:
                    running_pages[page_path] = info
                else:
                    print(f"[Startup] Removing stale status for {page_path}")
            
            # Save the cleaned up list
            if running_pages != loaded_pages:
                with open(jobs_file, 'w', encoding='utf-8') as f:
                    json.dump(running_pages, f, ensure_ascii=False)
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

def is_process_running(pid, page_path=None):
    """Check if a process is still running by checking log file activity"""
    # First check: is the log file being updated recently?
    if page_path:
        log_file = get_log_file_for_page(page_path)
        print(f"[Check] Checking log file: {log_file}, exists: {log_file.exists()}")
        if log_file.exists():
            try:
                # Check if log was modified in the last 60 seconds (increased from 30)
                mtime = log_file.stat().st_mtime
                age = time.time() - mtime
                print(f"[Check] Log age: {age:.1f} seconds")
                if age < 60:  # Active in last 60 seconds
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
    """Get status of all running pages, check if processes completed"""
    global running_pages
    
    # Check each running page - only remove if log shows completion
    dead_pages = []
    for page_path, info in running_pages.items():
        log_file = get_log_file_for_page(page_path)
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Check if completed (has completion marker)
                if '🏁 סיום!' in content or '✅ Claude סיים!' in content:
                    dead_pages.append(page_path)
                    print(f"[Status] Process for {page_path} COMPLETED (found completion marker)")
                else:
                    # Check last modification time - if no update for 2 minutes, consider dead
                    mtime = log_file.stat().st_mtime
                    age = time.time() - mtime
                    if age > 120:  # 2 minutes with no update
                        dead_pages.append(page_path)
                        print(f"[Status] Process for {page_path} TIMEOUT (no update for {age:.0f}s)")
            except Exception as e:
                print(f"[Status] Error reading log for {page_path}: {e}")
    
    # Remove completed/dead pages from running_pages
    for page_path in dead_pages:
        clear_page_running(page_path)
    
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
    
    # Get agent config
    agent = config["agents"].get(agent_id, {})
    agent_type = agent.get("type", "")
    agent_folder_name = agent.get("folder_name", "שיווק אטומי")
    
    # Determine file names based on agent config
    if agent_type == "six-step":
        report_name = agent.get("step1", {}).get("output_name", "דוח שלב 1.md")
        step2_report_name = agent.get("step2", {}).get("output_name", "דוח שלב 1 מורחב.md")  # QA report
        step3_report_name = agent.get("step3", {}).get("report_name", "דוח שלב 3.md")  # Fixes report
        step4_report_name = agent.get("step4", {}).get("report_name", "דוח שלב 4.md")  # QA fixes report
        step5_report_name = agent.get("step5", {}).get("report_name", "דוח שלב 5.md")  # AI removal report
        step6_report_name = agent.get("step6", {}).get("report_name", "דוח דיבאג AI.md")  # AI debug report
    elif agent_type == "four-step":
        report_name = agent.get("step1", {}).get("output_name", "דוח שלב 1.md")
        step2_report_name = agent.get("step2", {}).get("output_name", "דוח שלב 1 מורחב.md")  # QA report
        step3_report_name = agent.get("step3", {}).get("report_name", "דוח שלב 3.md")  # Fixes report
        step4_report_name = agent.get("step4", {}).get("report_name", "דוח דיבאג.md")  # Debug report
        step5_report_name = None
        step6_report_name = None
    elif agent_type in ["two-step", "three-step"]:
        report_name = agent.get("step1", {}).get("output_name", "דוח שלב 1.md")
        step2_report_name = agent.get("step2", {}).get("report_name", "דוח שלב 2.md")
        step3_report_name = agent.get("step3", {}).get("report_name", "דוח דיבאג.md") if agent_type == "three-step" else None
        step4_report_name = None
        step5_report_name = None
        step6_report_name = None
    else:
        # Default for atomic marketing (now four-step)
        report_name = "דוח שלב 1.md"
        step2_report_name = "דוח שלב 1 מורחב.md"
        step3_report_name = "דוח שלב 3.md"
        step4_report_name = "דוח דיבאג.md"
        step5_report_name = None
        step6_report_name = None
    
    # Check each page using the new folder structure
    for folder in config["paths"]["editable_pages"]:
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
                    
                    # Check files in agent folder
                    has_report = (agent_folder / report_name).exists() if report_name else False
                    has_step2_report = (agent_folder / step2_report_name).exists() if step2_report_name else False
                    has_step3_report = (agent_folder / step3_report_name).exists() if step3_report_name else False
                    has_step4_report = (agent_folder / step4_report_name).exists() if step4_report_name else False
                    has_step5_report = (agent_folder / step5_report_name).exists() if step5_report_name else False
                    has_step6_report = (agent_folder / step6_report_name).exists() if step6_report_name else False
                    
                    if has_report or has_step2_report or has_step3_report or has_step4_report or has_step5_report or has_step6_report:
                        status[page_path] = {
                            "hasReport": has_report,
                            "hasStep2Report": has_step2_report,
                            "hasStep3Report": has_step3_report,
                            "hasStep4Report": has_step4_report,
                            "hasStep5Report": has_step5_report,
                            "hasStep6Report": has_step6_report
                        }
    
    return jsonify({"success": True, "status": status})

@app.route('/api/status/multi-agent', methods=['GET'])
def get_multi_agent_status():
    """Get status for ALL agents for each page (for multi-agent sidebar display)"""
    status = {}
    
    # Define the two main agents to track
    agents_to_check = {
        "atomic_marketing": config["agents"].get("atomic_marketing", {}),
        "seo": config["agents"].get("seo", {})
    }
    
    # Check each page using the new folder structure
    for folder in config["paths"]["editable_pages"]:
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
                    
                    # Check status for each agent
                    for agent_id, agent in agents_to_check.items():
                        agent_folder_name = agent.get("folder_name", "שיווק אטומי" if agent_id == "atomic_marketing" else "SEO")
                        agent_type = agent.get("type", "")
                        agent_folder = page_folder / agent_folder_name
                        
                        # Determine max steps based on agent type
                        if agent_type == "six-step":
                            max_steps = 6
                            report_names = [
                                agent.get("step1", {}).get("output_name", "דוח שלב 1.md"),
                                agent.get("step2", {}).get("output_name", "דוח שלב 1 מורחב.md"),
                                agent.get("step3", {}).get("report_name", "דוח שלב 3.md"),
                                agent.get("step4", {}).get("report_name", "דוח שלב 4.md"),
                                agent.get("step5", {}).get("report_name", "דוח שלב 5.md"),
                                agent.get("step6", {}).get("report_name", "דוח דיבאג AI.md")
                            ]
                        elif agent_type == "four-step":
                            max_steps = 4
                            report_names = [
                                agent.get("step1", {}).get("output_name", "דוח שלב 1.md"),
                                agent.get("step2", {}).get("output_name", "דוח שלב 1 מורחב.md"),
                                agent.get("step3", {}).get("report_name", "דוח שלב 3.md"),
                                agent.get("step4", {}).get("report_name", "דוח דיבאג.md")
                            ]
                        else:
                            max_steps = 3
                            report_names = [
                                agent.get("step1", {}).get("output_name", "דוח שלב 1.md"),
                                agent.get("step2", {}).get("report_name", "דוח שלב 2.md"),
                                agent.get("step3", {}).get("report_name", "דוח דיבאג.md")
                            ]
                        
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
                    for folder in config["paths"]["editable_pages"]:
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

@app.route('/api/status/page/<path:page_path>', methods=['GET'])
def get_page_status(page_path):
    """Get running status of a specific page"""
    if page_path in running_pages:
        return jsonify({"success": True, "running": True, "info": running_pages[page_path]})
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

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(str(BASE_DIR), filename)

# ============ Server Control ============

@app.route('/api/server/restart', methods=['POST'])
def restart_server():
    """Restart the server"""
    import sys
    import threading
    
    def do_restart():
        import time
        time.sleep(1)
        os.execv(sys.executable, ['python'] + sys.argv)
    
    threading.Thread(target=do_restart).start()
    return jsonify({"success": True, "message": "Server restarting..."})

@app.route('/api/server/reload-config', methods=['POST'])
def reload_config():
    """Reload configuration without full restart"""
    global config
    try:
        config = load_config()
        return jsonify({"success": True, "message": "Config reloaded"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ Main ============

if __name__ == '__main__':
    print("=" * 50)
    print("  Page Management Dashboard")
    print("=" * 50)
    print(f"  Server: http://localhost:5000")
    print(f"  Base Dir: {BASE_DIR}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

