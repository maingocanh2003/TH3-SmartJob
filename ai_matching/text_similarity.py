"""
Text Similarity using TF-IDF and Cosine Similarity
Optimized pure Python implementation for CV and Job Description semantic matching.
"""

import math
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into lowercase terms, stripping punctuation."""
    if not text:
        return []
    text = unicodedata.normalize('NFC', text.lower())
    # Keep words, hyphens, and plus signs (for c++, c#, .net)
    tokens = re.findall(r'[a-zà-ỹ0-9+#.-]+', text)
    # Filter very short meaningless tokens except special keywords like c, r, go, js, ts, py
    valid_tokens = []
    stopwords = {
        'và', 'các', 'của', 'cho', 'với', 'trong', 'được', 'có', 'là', 'những',
        'khi', 'về', 'này', 'đến', 'tại', 'theo', 'như', 'đã', 'sẽ', 'đang',
        'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
    }
    for t in tokens:
        cleaned = t.strip('.-')
        if len(cleaned) >= 2 or cleaned in {'c', 'r', 'go'}:
            if cleaned not in stopwords:
                valid_tokens.append(cleaned)
    return valid_tokens


class TFIDFSimilarity:
    """
    Computes TF-IDF vectors and Cosine Similarity between document pairs.
    """

    def __init__(self, corpus: Optional[List[str]] = None):
        self.doc_count = 0
        self.doc_freq: Dict[str, int] = Counter()
        self.idf: Dict[str, float] = {}
        if corpus:
            self.fit(corpus)

    def fit(self, corpus: List[str]):
        """Fit vocabulary and document frequencies over a collection."""
        self.doc_count = len(corpus)
        self.doc_freq = Counter()
        for doc in corpus:
            tokens = set(tokenize(doc))
            for token in tokens:
                self.doc_freq[token] += 1

        # Smooth IDF
        self.idf = {}
        for token, freq in self.doc_freq.items():
            self.idf[token] = math.log((self.doc_count + 1) / (freq + 1)) + 1.0

    def compute_tfidf_vector(self, text: str) -> Dict[str, float]:
        """Compute L2-normalized TF-IDF vector for given text."""
        tokens = tokenize(text)
        if not tokens:
            return {}

        tf = Counter(tokens)
        max_tf = max(tf.values())

        vector: Dict[str, float] = {}
        norm_sq = 0.0

        for token, count in tf.items():
            # Sublinear TF scaling
            tf_val = 0.5 + 0.5 * (count / max_tf)
            idf_val = self.idf.get(token, 1.0)
            score = tf_val * idf_val
            vector[token] = score
            norm_sq += score * score

        # L2 Normalization
        norm = math.sqrt(norm_sq)
        if norm > 0:
            for token in vector:
                vector[token] /= norm

        return vector

    def cosine_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts (0.0 to 1.0).
        """
        vec1 = self.compute_tfidf_vector(text1)
        vec2 = self.compute_tfidf_vector(text2)

        if not vec1 or not vec2:
            return 0.0

        # Dot product of normalized vectors
        dot_product = 0.0
        # Iterate over smaller dict
        if len(vec1) > len(vec2):
            vec1, vec2 = vec2, vec1

        for token, val1 in vec1.items():
            if token in vec2:
                dot_product += val1 * vec2[token]

        return max(0.0, min(1.0, dot_product))


_similarity_engine = TFIDFSimilarity()


def compute_semantic_similarity(text1: str, text2: str) -> float:
    return _similarity_engine.cosine_similarity(text1, text2)
