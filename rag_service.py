# -*- coding: utf-8 -*-
"""
RAG Service - Retrieval-Augmented Generation
מערכת RAG מלאה עם embeddings לוקאליים וחיפוש semantic
"""

import json
import os
from pathlib import Path
from datetime import datetime

import numpy as np

# Lazy load sentence-transformers to avoid slow startup
_embedding_model = None

def get_embedding_model():
    """Lazy load the embedding model"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print("[RAG] Loading embedding model: paraphrase-multilingual-mpnet-base-v2")
        _embedding_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
        print(f"[RAG] Model loaded, dimension: {_embedding_model.get_sentence_embedding_dimension()}")
    return _embedding_model


class EmbeddingService:
    """
    שירות embeddings לוקאלי עם sentence-transformers
    משתמש במודל רב-לשוני שתומך בעברית
    """
    
    def __init__(self):
        self.model = None
        self.dimension = 768  # Default for paraphrase-multilingual-mpnet-base-v2
    
    def _ensure_model(self):
        """Load model on first use"""
        if self.model is None:
            self.model = get_embedding_model()
            self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed(self, texts):
        """המרת טקסטים ל-vectors"""
        self._ensure_model()
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def embed_query(self, query):
        """המרת שאילתה ל-vector"""
        self._ensure_model()
        return self.model.encode(query, convert_to_numpy=True)


class ChunkingService:
    """
    פיצול טקסט ל-chunks עם חפיפה
    """
    
    def __init__(self, chunk_size=500, overlap=50):
        self.chunk_size = chunk_size  # מילים
        self.overlap = overlap  # חפיפה בין chunks
    
    def chunk_text(self, text, source_id):
        """פיצול טקסט ל-chunks עם חפיפה"""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        # If text is shorter than chunk_size, return as single chunk
        if len(words) <= self.chunk_size:
            return [{
                'chunk_id': f"{source_id}_0",
                'text': text,
                'start_word': 0,
                'end_word': len(words),
                'word_count': len(words)
            }]
        
        start = 0
        chunk_idx = 0
        
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'chunk_id': f"{source_id}_{chunk_idx}",
                'text': chunk_text,
                'start_word': start,
                'end_word': end,
                'word_count': len(chunk_words)
            })
            
            # Move start with overlap
            start = end - self.overlap
            if start >= len(words):
                break
            chunk_idx += 1
        
        return chunks


class RAGIndexManager:
    """
    ניהול אינדקס RAG מרכזי
    מאחסן chunks ו-embeddings לחיפוש semantic
    """
    
    def __init__(self, base_path="generated_data/scraped_sources"):
        self.base_path = Path(base_path)
        self.embeddings_path = self.base_path / "embeddings_index.npy"
        self.chunks_index_path = self.base_path / "chunks_index.json"
        
        self.embedding_service = EmbeddingService()
        self.chunking_service = ChunkingService()
        
        self.embeddings = None
        self.chunks_metadata = []
        
        self._ensure_structure()
        self._load_index()
    
    def _ensure_structure(self):
        """יצירת תיקיות אם לא קיימות"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        sources_path = self.base_path / "sources"
        sources_path.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """טעינת אינדקס קיים"""
        if self.embeddings_path.exists():
            try:
                self.embeddings = np.load(self.embeddings_path)
                print(f"[RAG] Loaded {len(self.embeddings)} embeddings from index")
            except Exception as e:
                print(f"[RAG] Error loading embeddings: {e}")
                self.embeddings = np.array([]).reshape(0, 768)
        else:
            self.embeddings = np.array([]).reshape(0, 768)
        
        if self.chunks_index_path.exists():
            try:
                with open(self.chunks_index_path, 'r', encoding='utf-8') as f:
                    self.chunks_metadata = json.load(f)
                print(f"[RAG] Loaded {len(self.chunks_metadata)} chunks from index")
            except Exception as e:
                print(f"[RAG] Error loading chunks index: {e}")
                self.chunks_metadata = []
        else:
            self.chunks_metadata = []
    
    def _save_index(self):
        """שמירת אינדקס"""
        try:
            np.save(self.embeddings_path, self.embeddings)
            with open(self.chunks_index_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunks_metadata, f, ensure_ascii=False, indent=2)
            print(f"[RAG] Saved index: {len(self.chunks_metadata)} chunks, {len(self.embeddings)} embeddings")
        except Exception as e:
            print(f"[RAG] Error saving index: {e}")
    
    def add_source(self, source_id, content, url, title):
        """הוספת מקור חדש לאינדקס"""
        print(f"[RAG] Adding source: {source_id} ({title})")
        
        # 1. Check if source already exists and remove old chunks
        self._remove_source_chunks(source_id)
        
        # 2. פיצול ל-chunks
        chunks = self.chunking_service.chunk_text(content, source_id)
        if not chunks:
            print(f"[RAG] No chunks created for source {source_id}")
            return []
        
        print(f"[RAG] Created {len(chunks)} chunks")
        
        # 3. יצירת embeddings
        chunk_texts = [c['text'] for c in chunks]
        new_embeddings = self.embedding_service.embed(chunk_texts)
        
        print(f"[RAG] Created embeddings with shape {new_embeddings.shape}")
        
        # 4. עדכון אינדקס
        start_idx = len(self.chunks_metadata)
        for i, chunk in enumerate(chunks):
            chunk['embedding_idx'] = start_idx + i
            chunk['source_id'] = source_id
            chunk['url'] = url
            chunk['title'] = title
            chunk['added_at'] = datetime.now().isoformat()
            self.chunks_metadata.append(chunk)
        
        # 5. הוספת vectors
        if len(self.embeddings) == 0 or self.embeddings.size == 0:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        # 6. שמירה
        self._save_index()
        
        print(f"[RAG] Source added successfully. Total chunks: {len(self.chunks_metadata)}")
        return chunks
    
    def _remove_source_chunks(self, source_id):
        """הסרת chunks של מקור קיים (לפני עדכון)"""
        # Find chunks to remove
        chunks_to_remove = [i for i, c in enumerate(self.chunks_metadata) if c.get('source_id') == source_id]
        
        if not chunks_to_remove:
            return
        
        print(f"[RAG] Removing {len(chunks_to_remove)} existing chunks for source {source_id}")
        
        # Keep chunks that are not from this source
        new_chunks = [c for i, c in enumerate(self.chunks_metadata) if i not in chunks_to_remove]
        
        # Keep corresponding embeddings
        keep_indices = [i for i in range(len(self.chunks_metadata)) if i not in chunks_to_remove]
        if keep_indices and len(self.embeddings) > 0:
            new_embeddings = self.embeddings[keep_indices]
        else:
            new_embeddings = np.array([]).reshape(0, 768)
        
        # Update embedding indices
        for i, chunk in enumerate(new_chunks):
            chunk['embedding_idx'] = i
        
        self.chunks_metadata = new_chunks
        self.embeddings = new_embeddings
    
    def search(self, query, top_k=5):
        """חיפוש semantic"""
        if len(self.embeddings) == 0 or self.embeddings.size == 0:
            print("[RAG] No embeddings in index")
            return []
        
        print(f"[RAG] Searching for: {query[:50]}...")
        
        # המרת שאילתה ל-vector
        query_embedding = self.embedding_service.embed_query(query)
        
        # חישוב cosine similarity
        embeddings_norm = np.linalg.norm(self.embeddings, axis=1)
        query_norm = np.linalg.norm(query_embedding)
        
        # Avoid division by zero
        valid_mask = embeddings_norm > 0
        similarities = np.zeros(len(self.embeddings))
        similarities[valid_mask] = np.dot(self.embeddings[valid_mask], query_embedding) / (
            embeddings_norm[valid_mask] * query_norm
        )
        
        # מציאת top_k
        top_k = min(top_k, len(similarities))
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx < len(self.chunks_metadata):
                chunk = self.chunks_metadata[idx].copy()
                chunk['score'] = float(similarities[idx])
                results.append(chunk)
        
        print(f"[RAG] Found {len(results)} results")
        return results
    
    def get_stats(self):
        """קבלת סטטיסטיקות על האינדקס"""
        unique_sources = set(c.get('source_id') for c in self.chunks_metadata)
        return {
            'total_chunks': len(self.chunks_metadata),
            'total_embeddings': len(self.embeddings) if self.embeddings is not None else 0,
            'unique_sources': len(unique_sources),
            'sources': list(unique_sources)
        }


# Singleton instance for efficiency
_rag_manager = None

def get_rag_manager():
    """Get singleton RAG manager instance"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGIndexManager()
    return _rag_manager


def reset_rag_manager():
    """Reset RAG manager (for testing/reloading)"""
    global _rag_manager
    _rag_manager = None


# ============ Content Summarizer ============

import re

class ContentSummarizer:
    """
    חילוץ נתונים חשובים מטקסט
    מזהה מספרים, אחוזים, סכומי כסף, תאריכים ומונחים חשובים
    """
    
    @staticmethod
    def extract_summary(content, max_items=10):
        """חילוץ מספרים, אחוזים, ומונחים חשובים"""
        if not content:
            return {
                'percentages': [],
                'money': [],
                'numbers': [],
                'dates': [],
                'key_terms': [],
                'preview': ''
            }
        
        summary = {
            'percentages': [],
            'money': [],
            'numbers': [],
            'dates': [],
            'key_terms': []
        }
        
        # חילוץ אחוזים (ריביות)
        percent_pattern = r'(\d+(?:[.,]\d+)?)\s*%'
        for match in re.finditer(percent_pattern, content):
            start = max(0, match.start() - 40)
            end = min(len(content), match.end() + 40)
            context = content[start:end].strip()
            # Clean up context
            context = re.sub(r'\s+', ' ', context)
            summary['percentages'].append({
                'value': match.group(1) + '%',
                'context': '...' + context + '...'
            })
            if len(summary['percentages']) >= max_items:
                break
        
        # חילוץ סכומי כסף - ש"ח, שקל, ₪
        money_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:ש"ח|שקל|שקלים|₪)',
            r'₪\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:אלף|מיליון|מיליארד)\s*(?:ש"ח|שקל|₪)?'
        ]
        
        for pattern in money_patterns:
            for match in re.finditer(pattern, content):
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end].strip()
                context = re.sub(r'\s+', ' ', context)
                summary['money'].append({
                    'value': match.group(0),
                    'context': '...' + context + '...'
                })
                if len(summary['money']) >= max_items:
                    break
        
        # חילוץ מספרים עם הקשר (כמו "עד 60 חודשים", "מינימום 10,000")
        number_context_pattern = r'(?:עד|מינימום|מקסימום|בין|לתקופה של|למשך)\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:חודשים?|שנים?|ימים?)?'
        for match in re.finditer(number_context_pattern, content, re.IGNORECASE):
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 20)
            context = content[start:end].strip()
            context = re.sub(r'\s+', ' ', context)
            summary['numbers'].append({
                'value': match.group(0),
                'context': '...' + context + '...'
            })
            if len(summary['numbers']) >= max_items:
                break
        
        # חילוץ תאריכים
        date_patterns = [
            r'\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}',
            r'(?:ינואר|פברואר|מרץ|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)\s+\d{4}',
            r'\d{4}'  # שנה בודדת
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, content):
                # רק שנים מ-2020 ומעלה
                if len(match.group(0)) == 4:
                    try:
                        year = int(match.group(0))
                        if year < 2020 or year > 2030:
                            continue
                    except:
                        continue
                
                start = max(0, match.start() - 20)
                end = min(len(content), match.end() + 20)
                context = content[start:end].strip()
                context = re.sub(r'\s+', ' ', context)
                summary['dates'].append({
                    'value': match.group(0),
                    'context': '...' + context + '...'
                })
                if len(summary['dates']) >= max_items:
                    break
        
        # מונחים חשובים (לפי מילות מפתח ספציפיות)
        key_term_patterns = [
            r'(?:ריבית|פריים|הלוואה|אשראי|משכנתא|מימון)[^.]{10,60}',
            r'(?:תנאי הזכאות|דרישות|קריטריונים)[^.]{10,80}'
        ]
        
        for pattern in key_term_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                term = match.group(0).strip()
                term = re.sub(r'\s+', ' ', term)
                if len(term) > 20:  # רק ביטויים משמעותיים
                    summary['key_terms'].append(term)
                    if len(summary['key_terms']) >= max_items:
                        break
        
        # הסרת כפילויות
        summary['key_terms'] = list(set(summary['key_terms']))[:max_items]
        
        # הוספת תצוגה מקדימה - יותר תוכן
        preview_length = 1000
        if len(content) > preview_length:
            # Try to cut at a sentence or paragraph break
            cut_point = content[:preview_length].rfind('.')
            if cut_point > preview_length // 2:
                summary['preview'] = content[:cut_point + 1] + '\n\n...'
            else:
                summary['preview'] = content[:preview_length] + '...'
        else:
            summary['preview'] = content
        
        return summary
