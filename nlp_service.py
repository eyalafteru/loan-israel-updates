#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hebrew NLP Service for Keyword Density Analysis
Uses Trankit for morphology and DictaBERT for semantic analysis
"""

import json
import sys
import re
from typing import List, Dict, Tuple, Optional

# Try to import NLP libraries, provide fallback if not available
TRANKIT_AVAILABLE = False
DICTABERT_AVAILABLE = False

try:
    from trankit import Pipeline
    TRANKIT_AVAILABLE = True
except ImportError:
    pass

try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    DICTABERT_AVAILABLE = True
except ImportError:
    pass


class HebrewNLPService:
    """
    Hebrew NLP service providing:
    - Lemmatization (finding word base forms)
    - Morphological variations generation
    - Semantic similarity scoring with DictaBERT
    """
    
    def __init__(self, use_advanced_nlp: bool = True):
        self.use_advanced = use_advanced_nlp and TRANKIT_AVAILABLE
        self.use_semantic = use_advanced_nlp and DICTABERT_AVAILABLE
        
        self._trankit_pipeline = None
        self._dictabert_model = None
        self._dictabert_tokenizer = None
        
        # Common Hebrew prefixes
        self.prefixes = ['ה', 'ב', 'ל', 'מ', 'ו', 'כ', 'ש', 'וה', 'וב', 'ול', 'וכ', 'ומ', 'שה', 'שב', 'של', 'שמ']
        
        # Common suffixes for nouns
        self.noun_suffixes = {
            'singular_to_plural': [
                ('ה', 'ות'),  # הלוואה -> הלוואות
                ('', 'ים'),   # בנק -> בנקים
                ('', 'ות'),   # משכנתא -> משכנתאות
            ],
            'with_article': ['ה'],  # ההלוואה
            'possessive': ['י', 'ך', 'ו', 'נו', 'כם', 'הם'],  # הלוואתי
        }
    
    @property
    def trankit_pipeline(self):
        """Lazy load Trankit pipeline"""
        if self._trankit_pipeline is None and TRANKIT_AVAILABLE:
            try:
                self._trankit_pipeline = Pipeline('hebrew')
            except Exception as e:
                print(f"Warning: Could not load Trankit: {e}", file=sys.stderr)
        return self._trankit_pipeline
    
    @property
    def dictabert_model(self):
        """Lazy load DictaBERT model"""
        if self._dictabert_model is None and DICTABERT_AVAILABLE:
            try:
                self._dictabert_model = AutoModel.from_pretrained('dicta-il/dictabert')
                self._dictabert_tokenizer = AutoTokenizer.from_pretrained('dicta-il/dictabert')
            except Exception as e:
                print(f"Warning: Could not load DictaBERT: {e}", file=sys.stderr)
        return self._dictabert_model
    
    def normalize_hebrew(self, text: str) -> str:
        """
        Normalize Hebrew text:
        - Remove niqqud (vowel marks)
        - Normalize whitespace
        - Keep only Hebrew characters and spaces
        """
        # Remove niqqud
        text = re.sub(r'[\u0591-\u05C7]', '', text)
        # Remove non-Hebrew characters except spaces
        text = re.sub(r'[^\u0590-\u05FF\s]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_lemma(self, word: str) -> str:
        """Get the lemma (base form) of a Hebrew word using Trankit"""
        if not self.trankit_pipeline:
            return word
        
        try:
            result = self.trankit_pipeline.lemmatize(word)
            if result and 'tokens' in result:
                tokens = result['tokens']
                if tokens and len(tokens) > 0:
                    return tokens[0].get('lemma', word)
        except Exception:
            pass
        return word
    
    def generate_variations(self, keyword: str) -> List[str]:
        """
        Generate all morphological variations of a keyword.
        Includes prefixes, suffixes, and plural forms.
        """
        variations = set()
        words = keyword.split()
        
        # Original keyword
        variations.add(keyword)
        
        # Process each word in multi-word keywords
        if len(words) == 1:
            word = words[0]
            # Add prefixed versions
            for prefix in self.prefixes:
                variations.add(prefix + word)
            
            # Add plural forms
            for singular_end, plural_end in self.noun_suffixes['singular_to_plural']:
                if word.endswith(singular_end) and singular_end:
                    plural = word[:-len(singular_end)] + plural_end
                    variations.add(plural)
                    # Also add prefixed plurals
                    for prefix in self.prefixes[:7]:  # Basic prefixes
                        variations.add(prefix + plural)
                elif not singular_end:
                    variations.add(word + plural_end)
        else:
            # Multi-word keyword - add common prefixes to first word
            first_word = words[0]
            rest = ' '.join(words[1:])
            
            for prefix in self.prefixes[:7]:
                if not first_word.startswith(prefix):
                    variations.add(prefix + first_word + ' ' + rest)
        
        # If Trankit available, get lemma-based variations
        if self.trankit_pipeline:
            try:
                for word in words:
                    lemma = self.get_lemma(word)
                    if lemma != word:
                        # Add lemma
                        variations.add(lemma)
                        # Add prefixed lemmas
                        for prefix in self.prefixes[:7]:
                            variations.add(prefix + lemma)
            except Exception:
                pass
        
        return list(variations)
    
    def calculate_semantic_similarity(self, keyword: str, text: str) -> float:
        """
        Calculate semantic similarity between keyword and text using DictaBERT.
        Returns a score between 0 and 1.
        """
        if not self.dictabert_model or not self._dictabert_tokenizer:
            return 0.5  # Neutral fallback
        
        try:
            # Tokenize and embed keyword
            kw_tokens = self._dictabert_tokenizer(
                keyword, 
                return_tensors='pt', 
                truncation=True, 
                max_length=64
            )
            kw_embedding = self.dictabert_model(**kw_tokens).last_hidden_state.mean(dim=1)
            
            # Tokenize and embed text (truncated for performance)
            text_tokens = self._dictabert_tokenizer(
                text, 
                return_tensors='pt', 
                truncation=True, 
                max_length=512
            )
            text_embedding = self.dictabert_model(**text_tokens).last_hidden_state.mean(dim=1)
            
            # Calculate cosine similarity
            similarity = torch.cosine_similarity(kw_embedding, text_embedding)
            return max(0, min(1, similarity.item()))  # Clamp to 0-1
            
        except Exception as e:
            print(f"Semantic similarity error: {e}", file=sys.stderr)
            return 0.5
    
    def analyze_keyword_density(self, text: str, keyword: str) -> Dict:
        """
        Comprehensive keyword density analysis with:
        - Morphological variation matching
        - Semantic relevance scoring
        - Zone-aware analysis
        """
        normalized_text = self.normalize_hebrew(text)
        normalized_keyword = self.normalize_hebrew(keyword)
        
        # Generate all variations
        variations = self.generate_variations(normalized_keyword)
        
        # Count occurrences of each variation
        words = normalized_text.split()
        word_count = len(words)
        
        variation_counts = {}
        total_count = 0
        positions = []
        
        for variation in variations:
            pattern = re.compile(re.escape(variation), re.IGNORECASE)
            matches = list(pattern.finditer(normalized_text))
            count = len(matches)
            if count > 0:
                variation_counts[variation] = count
                total_count += count
                for match in matches:
                    positions.append({
                        'start': match.start(),
                        'end': match.end(),
                        'variation': variation
                    })
        
        # Calculate density
        density = (total_count / word_count * 100) if word_count > 0 else 0
        
        # Calculate semantic score if available
        semantic_score = 0.5
        if self.use_semantic:
            semantic_score = self.calculate_semantic_similarity(keyword, text)
        
        # Combined score (density + semantic)
        density_score = self._calculate_density_score(density)
        combined_score = (density_score * 0.4) + (semantic_score * 100 * 0.6)
        
        return {
            'keyword': keyword,
            'variations_found': variation_counts,
            'total_occurrences': total_count,
            'word_count': word_count,
            'density': round(density, 2),
            'density_score': round(density_score, 1),
            'semantic_score': round(semantic_score * 100, 1),
            'combined_score': round(combined_score, 1),
            'status': self._get_status(density),
            'positions': positions,
            'nlp_available': {
                'trankit': TRANKIT_AVAILABLE,
                'dictabert': DICTABERT_AVAILABLE
            }
        }
    
    def _calculate_density_score(self, density: float) -> float:
        """Convert density percentage to a 0-100 score"""
        if 1.5 <= density <= 2.5:
            return 100  # Ideal range
        elif 1.0 <= density < 1.5 or 2.5 < density <= 3.0:
            return 80  # Good
        elif 0.5 <= density < 1.0 or 3.0 < density <= 3.5:
            return 60  # Warning
        elif density < 0.5:
            return 40 - (0.5 - density) * 40  # Too thin
        else:  # > 3.5
            return max(0, 40 - (density - 3.5) * 20)  # Stuffing
    
    def _get_status(self, density: float) -> str:
        """Get status string based on density"""
        if 1.5 <= density <= 2.5:
            return 'ideal'
        elif 1.0 <= density <= 3.0:
            return 'good'
        elif 0.5 <= density < 1.0:
            return 'low'
        elif 3.0 < density <= 3.5:
            return 'high'
        elif density < 0.5:
            return 'too_thin'
        else:
            return 'stuffing'


def main():
    """CLI interface for the NLP service"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'error': 'Usage: python nlp_service.py <action> <json_params>',
            'actions': ['analyze', 'variations', 'lemma', 'semantic']
        }))
        sys.exit(1)
    
    action = sys.argv[1]
    try:
        params = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'Invalid JSON: {e}'}))
        sys.exit(1)
    
    service = HebrewNLPService()
    
    if action == 'analyze':
        text = params.get('text', '')
        keyword = params.get('keyword', '')
        result = service.analyze_keyword_density(text, keyword)
        print(json.dumps(result, ensure_ascii=False))
    
    elif action == 'variations':
        keyword = params.get('keyword', '')
        variations = service.generate_variations(keyword)
        print(json.dumps({'variations': variations}, ensure_ascii=False))
    
    elif action == 'lemma':
        word = params.get('word', '')
        lemma = service.get_lemma(word)
        print(json.dumps({'word': word, 'lemma': lemma}, ensure_ascii=False))
    
    elif action == 'semantic':
        keyword = params.get('keyword', '')
        text = params.get('text', '')
        score = service.calculate_semantic_similarity(keyword, text)
        print(json.dumps({'semantic_score': score}, ensure_ascii=False))
    
    else:
        print(json.dumps({'error': f'Unknown action: {action}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()

