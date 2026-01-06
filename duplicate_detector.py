# -*- coding: utf-8 -*-
"""
Duplicate Content Detector
מנוע זיהוי כפילויות תוכן בשיטת Google (TF-IDF + Cosine Similarity)
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

from bs4 import BeautifulSoup

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[Warning] scikit-learn not installed. Duplicate detection disabled.")

# ============ Constants ============

BASE_DIR = Path(__file__).parent
IGNORE_PATTERNS_FILE = BASE_DIR / "ignore_patterns.json"
CACHE_DIR = BASE_DIR / "cache"

# Content weights for similarity calculation
CONTENT_WEIGHTS = {
    'body': 0.60,
    'headings': 0.25,
    'meta': 0.15
}

# SEO Impact thresholds
SEO_THRESHOLDS = {
    'critical': 0.85,
    'high': 0.70,
    'medium': 0.50
}


# ============ Utility Functions ============

def load_ignore_patterns() -> Dict:
    """Load ignore patterns from JSON file"""
    if IGNORE_PATTERNS_FILE.exists():
        try:
            with open(IGNORE_PATTERNS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Loading ignore patterns: {e}")
    return {'patterns': [], 'html_classes_to_ignore': [], 'html_ids_to_ignore': []}


def should_ignore_text(text: str, patterns: List[Dict]) -> bool:
    """Check if text should be ignored based on patterns"""
    for pattern in patterns:
        pattern_type = pattern.get('type', 'exact')
        pattern_text = pattern.get('text', '')
        
        if pattern_type == 'exact':
            if pattern_text == text.strip():
                return True
        elif pattern_type == 'contains':
            if pattern_text in text:
                return True
        elif pattern_type == 'regex':
            try:
                if re.search(pattern_text, text):
                    return True
            except re.error:
                pass
    return False


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove numbers (dates, prices, etc.)
    text = re.sub(r'\d+', '', text)
    # Strip
    return text.strip()


# ============ Content Extraction ============

def extract_content_parts(html_path: Path, page_info_path: Optional[Path] = None) -> Dict:
    """
    Extract all content parts from HTML file
    Returns: {body_text, headings, title, description, keyword}
    """
    content_parts = {
        'body_text': '',
        'headings': {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'title': '',
        'description': '',
        'keyword': '',
        'url': ''
    }
    
    # Load ignore patterns
    ignore_data = load_ignore_patterns()
    ignore_patterns = ignore_data.get('patterns', [])
    ignore_classes = set(ignore_data.get('html_classes_to_ignore', []))
    ignore_ids = set(ignore_data.get('html_ids_to_ignore', []))
    
    try:
        with open(html_path, 'r', encoding='utf-8-sig') as f:
            html_content = f.read()
    except Exception as e:
        print(f"[Error] Reading HTML {html_path}: {e}")
        return content_parts
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts, styles, and ignored elements
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    # Remove elements with ignored classes/ids
    for element in soup.find_all(class_=lambda c: c and any(ic in c for ic in ignore_classes)):
        element.decompose()
    for element in soup.find_all(id=lambda i: i and i in ignore_ids):
        element.decompose()
    
    # Extract headings
    for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        headings = []
        for h in soup.find_all(level):
            heading_text = h.get_text(strip=True)
            if heading_text and not should_ignore_text(heading_text, ignore_patterns):
                headings.append(heading_text)
        content_parts['headings'][level] = headings
    
    # Extract body text
    body_text = soup.get_text(separator=' ', strip=True)
    
    # Filter out ignored patterns from body
    for pattern in ignore_patterns:
        pattern_text = pattern.get('text', '')
        if pattern.get('type') == 'contains' and pattern_text:
            # Remove lines containing the pattern
            lines = body_text.split('\n')
            lines = [line for line in lines if pattern_text not in line]
            body_text = '\n'.join(lines)
    
    content_parts['body_text'] = normalize_text(body_text)
    
    # Load page_info.json if exists
    if page_info_path and page_info_path.exists():
        try:
            with open(page_info_path, 'r', encoding='utf-8-sig') as f:
                page_info = json.load(f)
                content_parts['title'] = page_info.get('title', '')
                content_parts['description'] = page_info.get('description', '')
                content_parts['keyword'] = page_info.get('keyword', '')
                content_parts['url'] = page_info.get('url', '')
        except Exception as e:
            print(f"[Error] Reading page_info {page_info_path}: {e}")
    
    return content_parts


def get_page_files(directory: Path) -> List[Tuple[Path, Path]]:
    """
    Get all page HTML files with their page_info.json
    Returns: [(html_path, page_info_path), ...]
    """
    pages = []
    
    for folder in directory.iterdir():
        if not folder.is_dir():
            continue
        if folder.name.startswith('.'):
            continue
            
        # Find main HTML file (not backup)
        html_files = [f for f in folder.glob('*.html') if '_backup' not in f.name.lower()]
        if not html_files:
            continue
            
        html_file = html_files[0]
        page_info_file = folder / 'page_info.json'
        
        pages.append((html_file, page_info_file if page_info_file.exists() else None))
    
    return pages


# ============ Similarity Calculation ============

def calculate_text_similarity(texts: List[str]) -> np.ndarray:
    """
    Calculate similarity matrix using TF-IDF + Cosine Similarity
    """
    if not SKLEARN_AVAILABLE:
        return np.zeros((len(texts), len(texts)))
    
    if len(texts) < 2:
        return np.zeros((len(texts), len(texts)))
    
    # Filter empty texts
    valid_indices = [i for i, t in enumerate(texts) if t.strip()]
    valid_texts = [texts[i] for i in valid_indices]
    
    if len(valid_texts) < 2:
        return np.zeros((len(texts), len(texts)))
    
    try:
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 3),
            analyzer='word'
        )
        
        tfidf_matrix = vectorizer.fit_transform(valid_texts)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix)
        
        # Map back to full matrix
        full_matrix = np.zeros((len(texts), len(texts)))
        for i, idx_i in enumerate(valid_indices):
            for j, idx_j in enumerate(valid_indices):
                full_matrix[idx_i][idx_j] = similarity[i][j]
        
        return full_matrix
        
    except Exception as e:
        print(f"[Error] Calculating similarity: {e}")
        return np.zeros((len(texts), len(texts)))


def find_duplicate_snippets(text1: str, text2: str, min_length: int = 100) -> List[Dict]:
    """
    Find common text snippets between two texts
    """
    snippets = []
    
    # Split into sentences
    sentences1 = re.split(r'[.!?]', text1)
    sentences2 = re.split(r'[.!?]', text2)
    
    # Find common sentences/paragraphs
    for s1 in sentences1:
        s1_clean = s1.strip()
        if len(s1_clean) < min_length:
            continue
            
        for s2 in sentences2:
            s2_clean = s2.strip()
            if s1_clean == s2_clean:
                snippets.append({
                    'text': s1_clean,
                    'type': 'body',
                    'length': len(s1_clean)
                })
                break
    
    return snippets


# ============ SEO Impact Calculation ============

def calculate_seo_impact(similarity: float, pages: List[Dict]) -> Dict:
    """
    Calculate SEO impact score for a duplicate group
    """
    # Base score from similarity
    if similarity >= SEO_THRESHOLDS['critical']:
        level = 'critical'
        base_score = 90
    elif similarity >= SEO_THRESHOLDS['high']:
        level = 'high'
        base_score = 70
    else:
        level = 'medium'
        base_score = 50
    
    # Adjust based on number of pages
    page_count = len(pages)
    score = base_score + (page_count - 2) * 2
    score = min(100, score)
    
    # Generate reason
    reasons = []
    reasons.append(f"{page_count} עמודים עם {int(similarity * 100)}% דמיון")
    
    if similarity >= 0.85:
        reasons.append("כפילות גבוהה מאוד - Google עלול להעניש")
    
    return {
        'level': level,
        'score': score,
        'reason': ' | '.join(reasons)
    }


# ============ Main Report Generation ============

def generate_duplicate_report(
    pages_dir: str,
    threshold: float = 0.5,
    include_meta: bool = True,
    include_headings: bool = True
) -> Dict:
    """
    Generate comprehensive duplicate content report
    """
    pages_path = BASE_DIR / pages_dir
    
    if not pages_path.exists():
        return {
            'success': False,
            'error': f'Directory not found: {pages_dir}',
            'total_pages': 0,
            'groups': []
        }
    
    # Get all pages
    page_files = get_page_files(pages_path)
    
    if len(page_files) < 2:
        return {
            'success': True,
            'total_pages': len(page_files),
            'duplicates_found': 0,
            'groups': [],
            'statistics': {
                'pages_with_duplicates': 0,
                'total_duplicate_snippets': 0,
                'avg_similarity': 0,
                'severity_breakdown': {'critical': 0, 'high': 0, 'medium': 0}
            },
            'scan_time': datetime.now().isoformat()
        }
    
    # Extract content from all pages
    pages_content = []
    for html_path, info_path in page_files:
        content = extract_content_parts(html_path, info_path)
        content['path'] = str(html_path.relative_to(BASE_DIR))
        content['folder'] = html_path.parent.name
        pages_content.append(content)
    
    # Build combined texts for similarity
    combined_texts = []
    for page in pages_content:
        parts = []
        
        # Body text (main weight)
        if page['body_text']:
            parts.append(page['body_text'])
        
        # Headings
        if include_headings:
            for level in ['h1', 'h2', 'h3']:
                parts.extend(page['headings'].get(level, []))
        
        # Meta
        if include_meta:
            if page['title']:
                parts.append(page['title'])
            if page['description']:
                parts.append(page['description'])
        
        combined_texts.append(' '.join(parts))
    
    # Calculate similarity matrix
    similarity_matrix = calculate_text_similarity(combined_texts)
    
    # Find duplicate groups
    groups = []
    processed_pairs = set()
    pages_with_duplicates = set()
    total_snippets = 0
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0}
    
    for i in range(len(pages_content)):
        for j in range(i + 1, len(pages_content)):
            similarity = similarity_matrix[i][j]
            
            if similarity >= threshold:
                pair_key = tuple(sorted([i, j]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                pages_with_duplicates.add(i)
                pages_with_duplicates.add(j)
                
                page1 = pages_content[i]
                page2 = pages_content[j]
                
                # Find duplicate snippets
                snippets = find_duplicate_snippets(page1['body_text'], page2['body_text'])
                
                # Find duplicate headings
                headings_duplicates = {}
                if include_headings:
                    for level in ['h1', 'h2', 'h3']:
                        h1_set = set(page1['headings'].get(level, []))
                        h2_set = set(page2['headings'].get(level, []))
                        common = list(h1_set & h2_set)
                        if common:
                            headings_duplicates[level] = common
                            for h in common:
                                snippets.append({
                                    'text': h,
                                    'type': level,
                                    'length': len(h)
                                })
                
                total_snippets += len(snippets)
                
                # Calculate SEO impact
                seo_impact = calculate_seo_impact(similarity, [page1, page2])
                severity_counts[seo_impact['level']] += 1
                
                # Add pages to snippets
                for snippet in snippets:
                    snippet['pages'] = [page1['path'], page2['path']]
                
                groups.append({
                    'id': f'group_{len(groups) + 1}',
                    'similarity': float(similarity),
                    'seo_impact': seo_impact,
                    'pages': [
                        {
                            'path': page1['path'],
                            'keyword': page1['keyword'] or page1['folder'],
                            'url': page1['url'],
                            'title': page1['title'],
                            'description': page1['description']
                        },
                        {
                            'path': page2['path'],
                            'keyword': page2['keyword'] or page2['folder'],
                            'url': page2['url'],
                            'title': page2['title'],
                            'description': page2['description']
                        }
                    ],
                    'duplicate_snippets': snippets,
                    'headings_duplicates': headings_duplicates
                })
    
    # Sort groups by similarity (descending)
    groups.sort(key=lambda g: g['similarity'], reverse=True)
    
    # Calculate average similarity
    similarities = [g['similarity'] for g in groups]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    # Build similarity matrix for heatmap (simplified - top 20 pages)
    heatmap_size = min(20, len(pages_content))
    heatmap_matrix = similarity_matrix[:heatmap_size, :heatmap_size].tolist()
    heatmap_labels = [p['keyword'] or p['folder'] for p in pages_content[:heatmap_size]]
    
    return {
        'success': True,
        'total_pages': len(pages_content),
        'duplicates_found': len(groups),
        'statistics': {
            'pages_with_duplicates': len(pages_with_duplicates),
            'total_duplicate_snippets': total_snippets,
            'avg_similarity': avg_similarity,
            'severity_breakdown': severity_counts
        },
        'similarity_matrix': heatmap_matrix,
        'heatmap_labels': heatmap_labels,
        'groups': groups,
        'scan_time': datetime.now().isoformat()
    }


def scan_cross_directories(
    directories: List[str],
    threshold: float = 0.5,
    include_meta: bool = True,
    include_headings: bool = True
) -> Dict:
    """
    Scan for duplicates across multiple directories
    """
    all_pages_content = []
    
    for dir_name in directories:
        pages_path = BASE_DIR / "דפים לשינוי" / dir_name
        
        if not pages_path.exists():
            continue
        
        page_files = get_page_files(pages_path)
        
        for html_path, info_path in page_files:
            content = extract_content_parts(html_path, info_path)
            content['path'] = str(html_path.relative_to(BASE_DIR))
            content['folder'] = html_path.parent.name
            content['directory'] = dir_name
            all_pages_content.append(content)
    
    if len(all_pages_content) < 2:
        return {
            'success': True,
            'total_pages': len(all_pages_content),
            'duplicates_found': 0,
            'groups': [],
            'statistics': {
                'pages_with_duplicates': 0,
                'total_duplicate_snippets': 0,
                'avg_similarity': 0,
                'severity_breakdown': {'critical': 0, 'high': 0, 'medium': 0}
            },
            'scan_time': datetime.now().isoformat()
        }
    
    # Build combined texts
    combined_texts = []
    for page in all_pages_content:
        parts = []
        if page['body_text']:
            parts.append(page['body_text'])
        if include_headings:
            for level in ['h1', 'h2', 'h3']:
                parts.extend(page['headings'].get(level, []))
        if include_meta:
            if page['title']:
                parts.append(page['title'])
            if page['description']:
                parts.append(page['description'])
        combined_texts.append(' '.join(parts))
    
    # Calculate similarity
    similarity_matrix = calculate_text_similarity(combined_texts)
    
    # Find cross-directory duplicates
    groups = []
    processed_pairs = set()
    pages_with_duplicates = set()
    total_snippets = 0
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0}
    
    for i in range(len(all_pages_content)):
        for j in range(i + 1, len(all_pages_content)):
            # Only consider cross-directory pairs
            if all_pages_content[i]['directory'] == all_pages_content[j]['directory']:
                continue
            
            similarity = similarity_matrix[i][j]
            
            if similarity >= threshold:
                pair_key = tuple(sorted([i, j]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                pages_with_duplicates.add(i)
                pages_with_duplicates.add(j)
                
                page1 = all_pages_content[i]
                page2 = all_pages_content[j]
                
                snippets = find_duplicate_snippets(page1['body_text'], page2['body_text'])
                
                headings_duplicates = {}
                if include_headings:
                    for level in ['h1', 'h2', 'h3']:
                        h1_set = set(page1['headings'].get(level, []))
                        h2_set = set(page2['headings'].get(level, []))
                        common = list(h1_set & h2_set)
                        if common:
                            headings_duplicates[level] = common
                
                total_snippets += len(snippets)
                
                seo_impact = calculate_seo_impact(similarity, [page1, page2])
                severity_counts[seo_impact['level']] += 1
                
                for snippet in snippets:
                    snippet['pages'] = [page1['path'], page2['path']]
                
                groups.append({
                    'id': f'cross_group_{len(groups) + 1}',
                    'similarity': float(similarity),
                    'seo_impact': seo_impact,
                    'cross_directory': True,
                    'pages': [
                        {
                            'path': page1['path'],
                            'keyword': page1['keyword'] or page1['folder'],
                            'url': page1['url'],
                            'title': page1['title'],
                            'description': page1['description'],
                            'directory': page1['directory']
                        },
                        {
                            'path': page2['path'],
                            'keyword': page2['keyword'] or page2['folder'],
                            'url': page2['url'],
                            'title': page2['title'],
                            'description': page2['description'],
                            'directory': page2['directory']
                        }
                    ],
                    'duplicate_snippets': snippets,
                    'headings_duplicates': headings_duplicates
                })
    
    groups.sort(key=lambda g: g['similarity'], reverse=True)
    
    similarities = [g['similarity'] for g in groups]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    return {
        'success': True,
        'total_pages': len(all_pages_content),
        'duplicates_found': len(groups),
        'cross_directory': True,
        'statistics': {
            'pages_with_duplicates': len(pages_with_duplicates),
            'total_duplicate_snippets': total_snippets,
            'avg_similarity': avg_similarity,
            'severity_breakdown': severity_counts
        },
        'groups': groups,
        'scan_time': datetime.now().isoformat()
    }


def merge_reports(reports: Dict[str, Dict]) -> Dict:
    """
    Merge multiple directory reports into one
    """
    all_groups = []
    total_pages = 0
    pages_with_duplicates = 0
    total_snippets = 0
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0}
    
    for dir_name, report in reports.items():
        if not report.get('success'):
            continue
        
        total_pages += report.get('total_pages', 0)
        
        stats = report.get('statistics', {})
        pages_with_duplicates += stats.get('pages_with_duplicates', 0)
        total_snippets += stats.get('total_duplicate_snippets', 0)
        
        breakdown = stats.get('severity_breakdown', {})
        for level in ['critical', 'high', 'medium']:
            severity_counts[level] += breakdown.get(level, 0)
        
        for group in report.get('groups', []):
            group['source_directory'] = dir_name
            all_groups.append(group)
    
    all_groups.sort(key=lambda g: g['similarity'], reverse=True)
    
    similarities = [g['similarity'] for g in all_groups]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    return {
        'success': True,
        'total_pages': total_pages,
        'duplicates_found': len(all_groups),
        'statistics': {
            'pages_with_duplicates': pages_with_duplicates,
            'total_duplicate_snippets': total_snippets,
            'avg_similarity': avg_similarity,
            'severity_breakdown': severity_counts
        },
        'groups': all_groups,
        'scan_time': datetime.now().isoformat()
    }


def compare_two_pages(page1_path: str, page2_path: str) -> Dict:
    """
    Compare two specific pages for detailed diff view
    """
    page1_full = BASE_DIR / page1_path
    page2_full = BASE_DIR / page2_path
    
    page1_info = page1_full.parent / 'page_info.json'
    page2_info = page2_full.parent / 'page_info.json'
    
    content1 = extract_content_parts(page1_full, page1_info if page1_info.exists() else None)
    content2 = extract_content_parts(page2_full, page2_info if page2_info.exists() else None)
    
    # Calculate similarity
    texts = [content1['body_text'], content2['body_text']]
    similarity_matrix = calculate_text_similarity(texts)
    similarity = similarity_matrix[0][1] if len(similarity_matrix) > 1 else 0
    
    # Find matching sections
    snippets = find_duplicate_snippets(content1['body_text'], content2['body_text'], min_length=50)
    
    # Get matching phrases for highlighting
    matches = [s['text'] for s in snippets]
    
    return {
        'success': True,
        'similarity': float(similarity),
        'page1': {
            'path': page1_path,
            'keyword': content1['keyword'] or page1_full.parent.name,
            'content': content1['body_text'][:5000],  # Limit for display
            'title': content1['title'],
            'headings': content1['headings']
        },
        'page2': {
            'path': page2_path,
            'keyword': content2['keyword'] or page2_full.parent.name,
            'content': content2['body_text'][:5000],
            'title': content2['title'],
            'headings': content2['headings']
        },
        'matches': matches,
        'snippets': snippets
    }


# ============ CLI Testing ============

if __name__ == '__main__':
    print("Testing Duplicate Detector...")
    
    if not SKLEARN_AVAILABLE:
        print("ERROR: scikit-learn not installed!")
        exit(1)
    
    # Test with main directory
    report = generate_duplicate_report("דפים לשינוי/main", threshold=0.5)
    
    print(f"\nResults:")
    print(f"  Total pages: {report['total_pages']}")
    print(f"  Duplicates found: {report['duplicates_found']}")
    
    if report['groups']:
        print(f"\nTop 3 duplicate groups:")
        for group in report['groups'][:3]:
            print(f"  - {group['similarity']*100:.1f}% similarity")
            print(f"    Pages: {[p['keyword'] for p in group['pages']]}")
            print(f"    SEO Impact: {group['seo_impact']['level']}")
