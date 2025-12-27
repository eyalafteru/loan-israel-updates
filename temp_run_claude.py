# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import json
import time

os.environ["ANTHROPIC_API_KEY"] = "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"
os.chdir(r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates")

LIVE_LOG = r"C:\Users\eyal\loan-israel-updaets\loan-israel-updates\logs\הלוואה_חוץ_בנקאית_log.txt"

def log(msg):
    with open(LIVE_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)
    sys.stdout.flush()

log("=" * 60)
log("🔍 Claude Code Agent - שלב 4 (דיבאג)")
log("=" * 60)
log("")
log("📄 עמוד: דפים לשינוי/הלוואה חוץ בנקאית/הלוואה חוץ בנקאית.html")
log("")

prompt = """קרא את קובץ ההוראות C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\פרומטים\\סוכן QA לתיקוני SEO.md ואת הדוח המורחב: C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\דפים לשינוי\\הלוואה חוץ בנקאית\\SEO\\דוח שלב 2.md ודוח התיקונים: C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\דפים לשינוי\\הלוואה חוץ בנקאית\\SEO\\דוח שלב 3.md. בדוק את הקובץ C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\דפים לשינוי\\הלוואה חוץ בנקאית\\הלוואה חוץ בנקאית.html ומצא מה לא בוצע מהדוחות. ערוך את הקובץ ישירות עם כלי Edit (לא Write!) - אל תיצור קובץ חדש! בסוף חובה לשמור דוח דיבאג בנתיב המדויק: C:\\Users\\eyal\\loan-israel-updaets\\loan-israel-updates\\דפים לשינוי\\הלוואה חוץ בנקאית\\SEO\\דוח שלב 4.md"""

claude_cmd = r"C:\Users\eyal\AppData\Roaming\npm\claude.cmd"
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
    
except KeyboardInterrupt:
    process.terminate()
    log("❌ הופסק על ידי המשתמש")

# Read stderr
stderr = process.stderr.read().decode('utf-8', errors='replace')
if stderr:
    log(f"⚠️ שגיאות: {stderr[:500]}")

log("")
log("-" * 60)
log(f"🏁 סיום! קוד יציאה: {process.returncode}")
log("=" * 60)

# Notify server that job is complete
try:
    import urllib.request
    import json as json_lib
    data = json_lib.dumps({"page_path": "דפים לשינוי/הלוואה חוץ בנקאית/הלוואה חוץ בנקאית.html"}).encode("utf-8")
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
