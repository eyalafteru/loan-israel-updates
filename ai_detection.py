# -*- coding: utf-8 -*-
"""
AI Content Detection Module - Python Port
Based on the N8N JavaScript algorithm for detecting AI-generated content in Hebrew text.
"""

import re
from html.parser import HTMLParser
from collections import Counter

# ============================================
# DICTIONARIES - Hebrew AI Detection Phrases
# ============================================

# Generic AI phrases that indicate machine-generated text
AI_PHRASES = [
    'חשוב לציין', 'ראוי לציין', 'יש לזכור', 'כדאי לדעת', 'ניתן לומר',
    'באופן כללי', 'בדרך כלל', 'ברוב המקרים', 'על פי רוב',
    'בסופו של דבר', 'בסופו של יום', 'בשורה התחתונה',
    'בנוסף לכך', 'יתרה מכך', 'כמו כן', 'במקביל לכך',
    'לאור זאת', 'בהתאם לכך', 'כתוצאה מכך', 'עקב כך',
    'משמעות הדבר', 'כלומר', 'דהיינו', 'רוצה לומר',
    'במידה רבה', 'במידה מסוימת', 'באופן משמעותי',
    'היבט נוסף', 'נקודה נוספת', 'פן נוסף', 'נדבך נוסף',
    'מחד גיסא', 'מאידך גיסא', 'אי לכך ובהתאם לזאת',
    'הלכה למעשה', 'בפועל', 'ברמה הפרקטית',
    'ראייה הוליסטית', 'תמונה רחבה', 'מבט על',
    'שילוב מנצח', 'פתרון אולטימטיבי', 'חווית משתמש',
    'עידן חדש', 'פורץ דרך', 'חסר תקדים', 'אבן דרך',
    'לסיכום', 'ניתן לומר כי', 'במאמר זה',
    'בפתח הדברים', 'חשוב להדגיש כי', 'כפי שניתן לראות',
    'מכאן עולה כי', 'בחינה מעמיקה מראה', 'לא ניתן להתעלם מהעובדה ש',
    'בהקשר זה ראוי לציין', 'נקודה חשובה נוספת היא', 'מוסכם על הכל כי',
    'הדעה הרווחת היא', 'מקובל לחשוב ש', 'אין ספק כי', 'ברור לחלוטין ש',
    'מחקרים מראים כי', 'הספרות המקצועית מצביעה על'
]

# Claude-specific fingerprints
CLAUDE_FINGERPRINTS = [
    'בואו נצא למסע', 'בואו נצלול', 'נצא למסע מרתק', 'יחד נגלה',
    'במאמר זה נחקור', 'במדריך זה נכסה', 'בשורות הבאות',
    'האומנות שב', 'בליבת העשייה', 'מעבר לאופק', 'שוזר בתוכו',
    'מרקם עדין', 'סימפוניה של', 'ריקוד עדין', 'הוליסטי',
    'רב-ממדי', 'פורץ דרך', 'מהפכני', 'עידן חדש',
    'לכל מטבע שני צדדים', 'חשוב לראות את התמונה המלאה',
    'ראוי לגשת לנושא', 'בשקלול כל הגורמים', 'מצד אחד... ומצד שני',
    'בסיכומו של מסע', 'לסיכום הדברים', 'המסר העיקרי הוא',
    'קחו את הזמן', 'זכרו תמיד', 'אל תשכחו ש'
]

# Formal to casual mapping (high register words)
FORMAL_TO_CASUAL = {
    'כיצד': 'איך',
    'מדוע': 'למה',
    'הינו': 'הוא',
    'הינה': 'היא',
    'הינם': 'הם',
    'הינן': 'הן',
    'אנו': 'אנחנו',
    'לבצע': 'לעשות',
    'ביצוע': 'עשייה',
    'לרכוש': 'לקנות',
    'להעניק': 'לתת',
    'לספק': 'לתת',
    'להוות': 'להיות',
    'מהווה': 'הוא',
    'מהווים': 'הם',
    'בטרם': 'לפני',
    'טרם': 'עוד לא',
    'עקב': 'בגלל',
    'בגין': 'בגלל',
    'אודות': 'על',
    'באמצעות': 'בעזרת',
    'על מנת': 'כדי',
    'במטרה': 'כדי',
    'לשם': 'כדי',
    'ברם': 'אבל',
    'אולם': 'אבל',
}

# Tautologies (redundant phrases)
TAUTOLOGIES = {
    'לעלות למעלה': 'לעלות',
    'לרדת למטה': 'לרדת',
    'לצאת החוצה': 'לצאת',
    'להיכנס פנימה': 'להיכנס',
    'לחזור שוב': 'לחזור',
    'לחזור חזרה': 'לחזור',
    'רוב רובו': 'רובו',
    'כמו למשל': 'למשל',
    'במידה ואם': 'אם',
    'בסופו של דבר': 'בסוף',
    'הפתעה לא צפויה': 'הפתעה',
    'מתנה חינם': 'מתנה',
}

# Superlatives (exaggerated language)
SUPERLATIVES = {
    'חסר תקדים': 'מרשים',
    'פורץ דרך': 'חדשני',
    'מהפכני': 'מתקדם',
    'יוצא דופן': 'מיוחד',
    'אולטימטיבי': 'מקיף',
    'מושלם': 'מצוין',
    'אידיאלי': 'מתאים מאוד',
    'הטוב ביותר': 'מעולה',
    'אין ספק': 'ברור',
    'ללא עוררין': 'בטוח',
}

# Double connectors (redundant linking)
DOUBLE_CONNECTORS = {
    'אולם יחד עם זאת': 'עם זאת',
    'אך למרות זאת': 'למרות זאת',
    'אבל יחד עם זאת': 'אבל',
    'בנוסף לכך גם': 'בנוסף',
    'כמו כן גם': 'כמו כן',
}


# ============================================
# TEXT EXTRACTION
# ============================================

class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML, ignoring scripts and styles."""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_tags = {'script', 'style', 'noscript'}
        self.current_ignore = False
        
    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.ignore_tags:
            self.current_ignore = True
            
    def handle_endtag(self, tag):
        if tag.lower() in self.ignore_tags:
            self.current_ignore = False
            
    def handle_data(self, data):
        if not self.current_ignore:
            self.text_parts.append(data)
            
    def get_text(self):
        return ' '.join(self.text_parts)


def extract_text_from_html(html_content):
    """Extract clean text from HTML content."""
    if not html_content:
        return ""
    
    # Remove JSON-LD schemas
    html_content = re.sub(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract text
    try:
        parser = HTMLTextExtractor()
        parser.feed(html_content)
        text = parser.get_text()
    except:
        # Fallback: simple tag removal
        text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Clean up
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&[#\w]+;', ' ', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


# ============================================
# ANALYSIS FUNCTIONS
# ============================================

def check_ai_phrases(text):
    """Find AI-typical phrases in text."""
    found = []
    for phrase in AI_PHRASES:
        if phrase in text:
            # Find position for context
            pos = text.find(phrase)
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(phrase) + 30)
            context = text[context_start:context_end]
            
            found.append({
                'phrase': phrase,
                'position': pos,
                'context': f"...{context}...",
                'category': 'ai_phrase',
                'suggestion': 'שקול להסיר או לנסח מחדש בשפה טבעית יותר'
            })
    
    return found


def check_claude_fingerprints(text):
    """Find Claude-specific language patterns."""
    found = []
    for fingerprint in CLAUDE_FINGERPRINTS:
        if fingerprint in text:
            pos = text.find(fingerprint)
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(fingerprint) + 30)
            context = text[context_start:context_end]
            
            found.append({
                'phrase': fingerprint,
                'position': pos,
                'context': f"...{context}...",
                'category': 'claude_fingerprint',
                'suggestion': 'ביטוי אופייני ל-Claude - שקול ניסוח אחר'
            })
    
    return found


def check_formal_language(text):
    """Find overly formal language."""
    found = []
    for formal, casual in FORMAL_TO_CASUAL.items():
        pattern = rf'\b{re.escape(formal)}\b'
        matches = list(re.finditer(pattern, text))
        for match in matches:
            pos = match.start()
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(formal) + 30)
            context = text[context_start:context_end]
            
            found.append({
                'phrase': formal,
                'position': pos,
                'context': f"...{context}...",
                'category': 'formal_language',
                'suggestion': f'שפה גבוהה מדי - שקול "{casual}" במקום "{formal}"',
                'replacement': casual
            })
    
    return found


def check_tautologies(text):
    """Find redundant phrases."""
    found = []
    for tautology, fix in TAUTOLOGIES.items():
        if tautology in text:
            pos = text.find(tautology)
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(tautology) + 30)
            context = text[context_start:context_end]
            
            found.append({
                'phrase': tautology,
                'position': pos,
                'context': f"...{context}...",
                'category': 'tautology',
                'suggestion': f'כפילות מיותרת - שקול "{fix}" במקום "{tautology}"',
                'replacement': fix
            })
    
    return found


def check_superlatives(text):
    """Find exaggerated language."""
    found = []
    for superlative, alternative in SUPERLATIVES.items():
        if superlative in text:
            pos = text.find(superlative)
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(superlative) + 30)
            context = text[context_start:context_end]
            
            found.append({
                'phrase': superlative,
                'position': pos,
                'context': f"...{context}...",
                'category': 'superlative',
                'suggestion': f'שפה מוגזמת - שקול "{alternative}" במקום "{superlative}"',
                'replacement': alternative
            })
    
    return found


def check_structure_issues(text):
    """Check for structural AI patterns."""
    issues = []
    
    # Check for generic conclusion at end
    last_part = text[-500:] if len(text) > 500 else text
    conclusion_patterns = ['לסיכום', 'סיכומו של דבר', 'בסיכום', 'לסיום', 'כסיכום', 'השורה התחתונה']
    for pattern in conclusion_patterns:
        if pattern in last_part:
            issues.append({
                'phrase': pattern,
                'position': len(text) - 500 + last_part.find(pattern) if len(text) > 500 else last_part.find(pattern),
                'context': f"...{last_part[max(0, last_part.find(pattern)-20):last_part.find(pattern)+len(pattern)+20]}...",
                'category': 'generic_conclusion',
                'suggestion': 'סיום גנרי אופייני ל-AI - שקול סיום ספציפי יותר או הסרה'
            })
            break
    
    # Check for didactic Q&A pattern
    didactic_pattern = re.compile(r'\?\s+(כי|מכיוון ש|בגלל ש|הסיבה היא)')
    matches = list(didactic_pattern.finditer(text))
    if matches:
        for match in matches[:3]:  # Limit to first 3
            issues.append({
                'phrase': match.group(0),
                'position': match.start(),
                'context': f"...{text[max(0, match.start()-20):match.end()+20]}...",
                'category': 'didactic_pattern',
                'suggestion': 'תבנית שאלה-תשובה דידקטית - שקול ניסוח רהוט יותר'
            })
    
    # Check for impersonal text (no first person in long text)
    if len(text) > 1000:
        personal_pronouns = ['אני', 'שלי', 'לדעתי', 'בעיני', 'מניסיוני', 'אצלנו', 'אנחנו']
        has_personal = any(f' {p} ' in text for p in personal_pronouns)
        if not has_personal:
            issues.append({
                'phrase': '(הטקסט כולו)',
                'position': 0,
                'context': 'טקסט ארוך ללא שימוש בגוף ראשון',
                'category': 'impersonal',
                'suggestion': 'הטקסט לא אישי - שקול להוסיף "אני", "לדעתי", "מניסיוננו" וכד\''
            })
    
    return issues


def calculate_score(issues_by_category):
    """Calculate overall AI score based on found issues."""
    score = 0
    
    weights = {
        'ai_phrase': 3,
        'claude_fingerprint': 5,
        'formal_language': 2,
        'tautology': 3,
        'superlative': 4,
        'generic_conclusion': 8,
        'didactic_pattern': 5,
        'impersonal': 10,
        'double_connector': 3,
    }
    
    for category, issues in issues_by_category.items():
        weight = weights.get(category, 2)
        score += len(issues) * weight
    
    # Cap at 100
    return min(100, score)


def get_confidence_level(score):
    """Get confidence description based on score."""
    if score < 15:
        return 'נמוכה - הטקסט נראה אנושי'
    elif score < 30:
        return 'בינונית - יש כמה סימני AI'
    elif score < 50:
        return 'גבוהה - סביר שזה תוכן AI'
    else:
        return 'גבוהה מאוד - כמעט בוודאות תוכן AI'


# ============================================
# MAIN ANALYSIS FUNCTION
# ============================================

def analyze(html_content):
    """
    Main analysis function.
    
    Args:
        html_content: HTML string to analyze
        
    Returns:
        dict with analysis results
    """
    # Extract text
    text = extract_text_from_html(html_content)
    
    if len(text) < 200:
        return {
            'success': True,
            'score': 0,
            'confidence': 'נמוכה',
            'message': 'הטקסט קצר מדי לניתוח מהימן (פחות מ-200 תווים)',
            'issues': [],
            'categories': {},
            'text_length': len(text),
            'word_count': len(text.split())
        }
    
    # Run all checks
    issues_by_category = {
        'ai_phrase': check_ai_phrases(text),
        'claude_fingerprint': check_claude_fingerprints(text),
        'formal_language': check_formal_language(text),
        'tautology': check_tautologies(text),
        'superlative': check_superlatives(text),
    }
    
    # Add structure issues
    structure_issues = check_structure_issues(text)
    for issue in structure_issues:
        cat = issue['category']
        if cat not in issues_by_category:
            issues_by_category[cat] = []
        issues_by_category[cat].append(issue)
    
    # Flatten all issues
    all_issues = []
    for category, issues in issues_by_category.items():
        for issue in issues:
            issue['id'] = f"{category}_{issue['position']}"
            all_issues.append(issue)
    
    # Sort by position
    all_issues.sort(key=lambda x: x['position'])
    
    # Calculate score
    score = calculate_score(issues_by_category)
    confidence = get_confidence_level(score)
    
    # Create summary by category
    category_summary = {}
    for cat, issues in issues_by_category.items():
        if issues:
            category_names = {
                'ai_phrase': 'ביטויי AI גנריים',
                'claude_fingerprint': 'טביעות אצבע של Claude',
                'formal_language': 'שפה רשמית מדי',
                'tautology': 'כפילויות מיותרות',
                'superlative': 'שפה מוגזמת',
                'generic_conclusion': 'סיום גנרי',
                'didactic_pattern': 'תבנית דידקטית',
                'impersonal': 'העדר אישיות',
            }
            category_summary[cat] = {
                'name': category_names.get(cat, cat),
                'count': len(issues),
                'examples': [i['phrase'] for i in issues[:5]]
            }
    
    return {
        'success': True,
        'score': score,
        'confidence': confidence,
        'issues': all_issues,
        'categories': category_summary,
        'text_length': len(text),
        'word_count': len(text.split()),
        'total_issues': len(all_issues)
    }




