# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "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"
os.chdir(r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates")

LIVE_LOG = r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates\logs\הלוואות_למילואימניקים_log.txt"

def log(msg):
    """Write to live log file"""
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🚀 Claude Code Agent - שלב 1 (הפקת דוח)")
log("=" * 60)
log("")
log("📄 עמוד: דפים לשינוי/הלוואות למילואימניקים/הלוואות למילואימניקים.html")
log("📋 סוכן: סוכן טסט")
log("")

prompt = """אתה מנתח כותרות עמודים.

קרא את קובץ ה-HTML בנתיב: C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\דפים לשינוי\\הלוואות למילואימניקים\\הלוואות למילואימניקים.html

בדוק את הכותרת הראשית (H1) בעמוד.

החזר תשובה קצרה בפורמט:
- כותרת נוכחית: [הכותרת]
- כותרת מוצעת: [כותרת משופרת עם מילת מפתח "הלוואות"]
- סיבה: [הסבר קצר]

בסוף חובה לשמור את הדוח בנתיב המדויק: C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\דפים לשינוי\\הלוואות למילואימניקים\\סוכן טסט\\דוח שלב 1.md"""

# Save prompt to temp file to avoid command line length limits
prompt_file = r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates" + r"\temp_prompt.txt"
with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt)
log(f"📝 פרומפט: {len(prompt)} תווים")

log("🔄 מריץ Claude Code עם streaming...")
log("-" * 60)
log("")

# Run claude with streaming JSON output - use stdin for long prompts
claude_cmd = r"C:\Users\eyal\AppData\Roaming\npm\claude.cmd"
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
    cwd=r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates"
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
                    content = data.get("message", {}).get("content", [])
                    for block in content:
                        if block.get("type") == "text":
                            text = block.get("text", "")[:200]
                            if text:
                                log(f"💭 {text}")
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                            log(f"🔧 משתמש בכלי: {tool_name}")
                
                elif msg_type == "content_block_delta":
                    # Streaming text delta
                    delta = data.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")[:100]
                        if text.strip():
                            log(f"   {text}")
                
                elif msg_type == "result":
                    # Final result
                    log("")
                    log("✅ Claude סיים!")
                    
            except json.JSONDecodeError:
                # Not JSON, just log as-is
                if decoded:
                    log(decoded)
                    
        except Exception as e:
            log(f"⚠️ שגיאה בקריאה: {e}")

    process.wait()
    prompt_input.close()
    
except KeyboardInterrupt:
    process.terminate()
    prompt_input.close()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {stderr[:500]}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {process.returncode}")
log("=" * 60)

# Notify server that job is complete (legacy endpoint)
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({"page_path": "דפים לשינוי/הלוואות למילואימניקים/הלוואות למילואימניקים.html"}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/status/complete",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log("📡 השרת עודכן.")
except Exception as e:
    log(f"⚠️ לא ניתן לעדכן שרת: {e}")

# === STEP WEBHOOK - Notify step 1 completion for Full Auto ===
try:
    report_path = r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates\דפים לשינוי\הלוואות למילואימניקים\סוכן טסט\דוח שלב 1.md"
    report_exists = os.path.exists(report_path)
    webhook_data = json_lib.dumps({
        "page_path": "דפים לשינוי/הלוואות למילואימניקים/הלוואות למילואימניקים.html",
        "agent_id": "agent_mjwo0avx_4zda",
        "step": 1,
        "status": "success" if report_exists else "error"
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:5000/api/step/complete",
        data=webhook_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    log(f"📡 Step 1 webhook: {'success' if report_exists else 'error'}")
except Exception as e:
    log(f"⚠️ Step webhook failed: {e}")
