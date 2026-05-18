# -*- coding: utf-8 -*-
"""
AI Summarizer Service - Ollama Multi-Model Integration
שירות סיכום AI עם מודלים מקומיים דרך Ollama (Gemma 2 9B, Qwen 2.5 14B)
"""

import json
import requests
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any


# Supported AI models with display names
SUPPORTED_MODELS = {
    'gemma2:9b': {
        'name': 'Gemma 2 9B',
        'description': 'מהיר ויעיל',
        'size': '9B'
    },
    'qwen2.5:14b': {
        'name': 'Qwen 2.5 14B', 
        'description': 'איכותי יותר, איטי יותר',
        'size': '14B'
    },
    'qwen2.5:7b': {
        'name': 'Qwen 2.5 7B',
        'description': 'מאוזן - מהירות ואיכות',
        'size': '7B'
    },
    'qwen3:8b': {
        'name': 'Qwen 3 8B',
        'description': 'הדור החדש של Qwen - חכם ומהיר',
        'size': '8B'
    },
    'llama3.1:8b': {
        'name': 'Llama 3.1 8B',
        'description': 'Meta AI - מודל חזק',
        'size': '8B'
    }
}

DEFAULT_MODEL = 'gemma2:9b'


def get_available_models(base_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
    """
    מחזיר רשימת מודלים זמינים ב-Ollama
    בודק אילו מהמודלים הנתמכים מותקנים בפועל
    """
    available = []
    
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            installed_models = response.json().get('models', [])
            installed_names = [m.get('name', '') for m in installed_models]
            
            # Check each supported model
            for model_id, model_info in SUPPORTED_MODELS.items():
                model_base = model_id.split(':')[0]
                is_installed = any(model_base in name for name in installed_names)
                
                available.append({
                    'id': model_id,
                    'name': model_info['name'],
                    'description': model_info['description'],
                    'size': model_info['size'],
                    'installed': is_installed
                })
            
            # Also add any other installed models not in our list
            for installed in installed_models:
                name = installed.get('name', '')
                if name and not any(name.startswith(m.split(':')[0]) for m in SUPPORTED_MODELS.keys()):
                    available.append({
                        'id': name,
                        'name': name,
                        'description': 'מודל מותקן',
                        'size': 'unknown',
                        'installed': True
                    })
                    
    except Exception as e:
        print(f"[AI] Error getting models: {e}")
    
    return available


class OllamaSummarizer:
    """
    שירות סיכום עם מודלים מקומיים דרך Ollama
    תומך ב-Gemma 2, Qwen 2.5, Llama ועוד
    מותאם לתוכן פיננסי בעברית
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = 120  # 2 minutes timeout for AI responses
    
    def is_available(self) -> bool:
        """בדיקה אם Ollama זמין"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                # Check if our model is available
                return any(self.model.split(':')[0] in name for name in model_names)
            return False
        except Exception as e:
            print(f"[AI] Ollama not available: {e}")
            return False
    
    def _generate(self, prompt: str, json_mode: bool = True) -> Optional[str]:
        """שליחת prompt ל-Ollama וקבלת תשובה"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent outputs
                    "num_predict": 2048
                }
            }
            
            if json_mode:
                payload["format"] = "json"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                print(f"[AI] Error from Ollama: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("[AI] Request timed out")
            return None
        except Exception as e:
            print(f"[AI] Error generating response: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """פענוח תשובת JSON מה-AI"""
        if not response:
            return None
        
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                # Find JSON object in response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
        
        return None
    
    def summarize(self, content: str, url: str = "") -> Dict[str, Any]:
        """
        יצירת סיכום מובנה של תוכן פיננסי
        מחלץ את כל הפרטים החשובים לשימוש ביצירת תוכן
        
        Returns:
            {
                "success": bool,
                "summary": {
                    "lender": {...},
                    "product": {...},
                    "rates": {...},
                    "amounts": {...},
                    "periods": {...},
                    "monthly_payments": {...},
                    "eligibility": [...],
                    "requirements": [...],
                    "benefits": [...],
                    "fees": [...],
                    "process": [...],
                    "warnings": [...],
                    "contact": {...},
                    "key_points": [...]
                },
                "model": str,
                "timestamp": str
            }
        """
        if not content:
            return {"success": False, "error": "No content provided"}
        
        # Truncate content if too long (keep first 12000 chars for more context)
        # Also try to keep complete sentences
        max_chars = 12000
        if len(content) > max_chars:
            # Try to cut at a sentence boundary
            truncated = content[:max_chars]
            last_period = truncated.rfind('.')
            if last_period > max_chars - 500:  # If period is near the end
                truncated = truncated[:last_period + 1]
        else:
            truncated = content
        
        prompt = f"""אתה מנתח תוכן פיננסי מקצועי. חלץ את כל המידע הרלוונטי מהטקסט הבא.
המטרה: ליצור מאגר מידע מדויק שישמש ליצירת תוכן שיווקי.

הטקסט:
{truncated}

חלץ את כל המידע הבא וכתוב "לא צוין" אם המידע לא מופיע:

החזר JSON במבנה הבא בלבד:
{{
    "lender": {{
        "name": "שם הגוף המלווה (בנק/חברה/קרן)",
        "type": "בנק / חברת אשראי / קרן ממשלתית / גוף פרטי",
        "license": "רגולציה/רישיון אם מוזכר"
    }},
    "product": {{
        "name": "שם המוצר/ההלוואה",
        "type": "הלוואה אישית / עסקית / משכנתא / קרן השתלמות / אחר",
        "purpose": "מטרת ההלוואה (רכב/שיפוץ/עסק/כל מטרה וכו')",
        "description": "תיאור קצר במשפט אחד"
    }},
    "rates": {{
        "interest_rate": "אחוז ריבית נקוב (לדוגמה: 5.9%)",
        "interest_type": "קבועה / משתנה / צמודה למדד / צמודה לפריים",
        "prime_plus": "פריים + X אם רלוונטי",
        "effective_rate": "ריבית אפקטיבית שנתית",
        "range": "טווח ריביות אם יש (מ-X% עד Y%)",
        "funding_percentage": "אחוז מימון / LTV (לדוגמה: עד 75% מימון)",
        "down_payment": "הון עצמי נדרש (לדוגמה: 25% הון עצמי)"
    }},
    "amounts": {{
        "min_amount": "סכום מינימלי (עם מטבע)",
        "max_amount": "סכום מקסימלי (עם מטבע)",
        "typical_amount": "סכום טיפוסי/דוגמה אם מוזכר"
    }},
    "periods": {{
        "min_period": "תקופה מינימלית (חודשים/שנים)",
        "max_period": "תקופה מקסימלית (חודשים/שנים)",
        "grace_period": "תקופת גרייס אם יש"
    }},
    "monthly_payments": {{
        "example_payment": "דוגמה להחזר חודשי אם מוזכר",
        "calculation_example": "דוגמת חישוב: סכום X לתקופה Y = החזר Z",
        "payment_method": "שיטת החזר (שפיצר/בלון/קרן שווה)"
    }},
    "eligibility": [
        "תנאי זכאות 1 (מי יכול לקבל)",
        "תנאי זכאות 2",
        "גיל מינימלי/מקסימלי אם מוזכר"
    ],
    "requirements": [
        "מסמך/דרישה 1 (תלוש/דוחות/ערבות)",
        "מסמך/דרישה 2"
    ],
    "collateral": {{
        "type": "סוג בטוחה (ערבות/שעבוד/ללא)",
        "details": "פירוט הבטוחה"
    }},
    "benefits": [
        "יתרון 1",
        "יתרון 2"
    ],
    "fees": [
        {{
            "name": "שם העמלה",
            "amount": "סכום/אחוז",
            "notes": "הערות"
        }}
    ],
    "process": [
        "שלב 1 בתהליך",
        "שלב 2 בתהליך"
    ],
    "timing": {{
        "approval_time": "זמן אישור",
        "funding_time": "זמן העברת הכסף"
    }},
    "warnings": [
        "אזהרה/הסתייגות חשובה"
    ],
    "special_offers": [
        "מבצע/הטבה מיוחדת אם יש"
    ],
    "contact": {{
        "phone": "טלפון",
        "website": "אתר",
        "branches": "מידע על סניפים"
    }},
    "key_points": [
        "נקודה עיקרית 1 לסיכום",
        "נקודה עיקרית 2 לסיכום",
        "נקודה עיקרית 3 לסיכום"
    ],
    "last_updated": "תאריך עדכון אם מוזכר בדף"
}}

כללים חשובים:
1. חלץ רק מידע שמופיע בטקסט - אל תמציא נתונים
2. אם מידע לא מופיע, כתוב "לא צוין"
3. שמור על דיוק מספרי - העתק מספרים בדיוק כפי שמופיעים
4. כלול הקשר למספרים (לדוגמה: "עד 500,000 ש"ח לעסק קטן")
5. חפש במיוחד אחר: אחוזי מימון (LTV), הון עצמי, ריביות, עמלות, תקופות
6. אם יש טבלאות או רשימות עם נתונים - חלץ את כל המידע מהן

החזר רק את ה-JSON, ללא טקסט נוסף."""

        response = self._generate(prompt, json_mode=True)
        parsed = self._parse_json_response(response)
        
        if parsed:
            return {
                "success": True,
                "summary": parsed,
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]
            }
        else:
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "raw_response": response[:500] if response else None
            }
    
    def compare_versions(self, old_content: str, new_content: str, 
                         old_summary: Optional[Dict] = None) -> Dict[str, Any]:
        """
        השוואת שתי גרסאות של תוכן וזיהוי שינויים
        
        Returns:
            {
                "success": bool,
                "has_changes": bool,
                "changes": [...],
                "importance": "high" | "medium" | "low",
                "summary": str
            }
        """
        if not old_content or not new_content:
            return {"success": False, "error": "Missing content for comparison"}
        
        # Quick hash check - if identical, no changes
        old_hash = hashlib.sha256(old_content.encode()).hexdigest()
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()
        
        if old_hash == new_hash:
            return {
                "success": True,
                "has_changes": False,
                "changes": [],
                "importance": "none",
                "summary": "אין שינויים"
            }
        
        # Truncate contents for comparison
        old_truncated = old_content[:3000] if len(old_content) > 3000 else old_content
        new_truncated = new_content[:3000] if len(new_content) > 3000 else new_content
        
        prompt = f"""השווה בין שני הטקסטים הבאים מאותו מקור מידע פיננסי וזהה שינויים.

טקסט קודם:
{old_truncated}

טקסט חדש:
{new_truncated}

החזר JSON במבנה הבא:
{{
    "has_changes": true או false,
    "changes": [
        {{
            "type": "rate_change" או "term_change" או "requirement_change" או "new_info" או "removed_info",
            "description": "תיאור השינוי בעברית",
            "previous_value": "ערך קודם אם רלוונטי",
            "new_value": "ערך חדש אם רלוונטי",
            "importance": "high" או "medium" או "low"
        }}
    ],
    "overall_importance": "high" או "medium" או "low",
    "summary": "סיכום קצר של השינויים בעברית"
}}

שינויים בריבית או תנאים פיננסיים הם בחשיבות high.
שינויים בדרישות או תנאי זכאות הם בחשיבות medium.
שינויי ניסוח או עיצוב הם בחשיבות low.

החזר רק את ה-JSON."""

        response = self._generate(prompt, json_mode=True)
        parsed = self._parse_json_response(response)
        
        if parsed:
            return {
                "success": True,
                "has_changes": parsed.get("has_changes", True),
                "changes": parsed.get("changes", []),
                "importance": parsed.get("overall_importance", "medium"),
                "summary": parsed.get("summary", "זוהו שינויים"),
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Fallback - we know there are changes based on hash
            return {
                "success": True,
                "has_changes": True,
                "changes": [{"type": "content_updated", "description": "התוכן השתנה", "importance": "medium"}],
                "importance": "medium",
                "summary": "התוכן השתנה (ניתוח AI לא זמין)",
                "fallback": True
            }
    
    def suggest_updates(self, changes: List[Dict], page_content: str, 
                        page_title: str = "") -> Dict[str, Any]:
        """
        יצירת הצעות לעדכון עמוד בהתבסס על שינויים שזוהו
        
        Returns:
            {
                "success": bool,
                "suggestions": [...],
                "priority": "high" | "medium" | "low"
            }
        """
        if not changes:
            return {"success": True, "suggestions": [], "priority": "none"}
        
        changes_text = "\n".join([
            f"- {c.get('description', 'שינוי')} (חשיבות: {c.get('importance', 'medium')})"
            for c in changes
        ])
        
        page_truncated = page_content[:4000] if len(page_content) > 4000 else page_content
        
        prompt = f"""אתה עורך תוכן. בהתבסס על השינויים שזוהו במקור המידע, הצע עדכונים לעמוד.

כותרת העמוד: {page_title}

שינויים שזוהו במקור:
{changes_text}

תוכן העמוד הנוכחי:
{page_truncated}

החזר JSON במבנה הבא:
{{
    "suggestions": [
        {{
            "action": "update" או "add" או "remove" או "verify",
            "section": "באיזה חלק בעמוד",
            "description": "מה לעשות",
            "reason": "למה זה חשוב",
            "priority": "high" או "medium" או "low"
        }}
    ],
    "overall_priority": "high" או "medium" או "low",
    "summary": "סיכום קצר של העדכונים הנדרשים"
}}

החזר רק את ה-JSON."""

        response = self._generate(prompt, json_mode=True)
        parsed = self._parse_json_response(response)
        
        if parsed:
            return {
                "success": True,
                "suggestions": parsed.get("suggestions", []),
                "priority": parsed.get("overall_priority", "medium"),
                "summary": parsed.get("summary", ""),
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate suggestions",
                "suggestions": []
            }
    
    def extract_financial_data(self, content: str) -> Dict[str, Any]:
        """
        חילוץ נתונים פיננסיים ספציפיים מתוכן
        משלים את ContentSummarizer עם ניתוח AI
        """
        if not content:
            return {"success": False, "error": "No content"}
        
        truncated = content[:5000] if len(content) > 5000 else content
        
        prompt = f"""חלץ את כל הנתונים הפיננסיים מהטקסט הבא.

הטקסט:
{truncated}

החזר JSON במבנה הבא:
{{
    "interest_rates": [
        {{"value": "X%", "type": "שם סוג הריבית", "context": "הקשר קצר"}}
    ],
    "amounts": [
        {{"value": "XXX ש\"ח", "type": "מינימום/מקסימום/דוגמה", "context": "הקשר"}}
    ],
    "periods": [
        {{"value": "X חודשים/שנים", "type": "מינימום/מקסימום", "context": "הקשר"}}
    ],
    "fees": [
        {{"value": "XXX", "description": "תיאור העמלה"}}
    ],
    "conditions": [
        "תנאי 1",
        "תנאי 2"
    ],
    "last_updated": "תאריך עדכון אם מוזכר"
}}

החזר רק את ה-JSON."""

        response = self._generate(prompt, json_mode=True)
        parsed = self._parse_json_response(response)
        
        if parsed:
            return {
                "success": True,
                "data": parsed,
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "Failed to extract data"}


# Cache for summarizer instances by model
_summarizers: Dict[str, OllamaSummarizer] = {}

def get_summarizer(model: str = None) -> OllamaSummarizer:
    """
    Get summarizer instance for a specific model
    Creates new instance if model changes
    """
    global _summarizers
    
    # Use default if not specified
    if model is None:
        model = DEFAULT_MODEL
    
    # Create new instance if not cached
    if model not in _summarizers:
        _summarizers[model] = OllamaSummarizer(model=model)
    
    return _summarizers[model]


def check_ollama_status(model: str = None) -> Dict[str, Any]:
    """בדיקת סטטוס Ollama ומודל נבחר"""
    summarizer = get_summarizer(model)
    available = summarizer.is_available()
    
    # Get all available models
    models = get_available_models()
    installed_models = [m for m in models if m.get('installed')]
    
    return {
        "ollama_available": available,
        "model": summarizer.model,
        "base_url": summarizer.base_url,
        "available_models": models,
        "installed_count": len(installed_models),
        "message": f"Ollama ready with {summarizer.model}" if available else "Ollama not available. Run: ollama serve"
    }


# Quick test
if __name__ == "__main__":
    print("Testing AI Summarizer...")
    status = check_ollama_status()
    print(f"Status: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    if status["ollama_available"]:
        summarizer = get_summarizer()
        
        # Test summarization
        test_content = """
        הלוואה לעסקים קטנים
        ריבית: פריים + 2.5%
        סכום: 50,000 - 500,000 ש"ח
        תקופה: עד 60 חודשים
        דרישות: ערבות אישית, דוחות כספיים
        """
        
        result = summarizer.summarize(test_content)
        print(f"\nSummary result: {json.dumps(result, ensure_ascii=False, indent=2)}")
