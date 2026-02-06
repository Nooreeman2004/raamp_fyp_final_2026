"""
RAAMP Query Preprocessor Module
================================
Intelligent query preprocessing with fuzzy matching, partial word handling,
and marketing context awareness for improved RAG retrieval.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class ProcessedQuery:
    """Represents a preprocessed query with enhancements."""
    original: str
    cleaned: str
    expanded: str
    keywords: List[str]
    intent: str
    confidence: float
    corrections: List[Dict[str, str]]


class QueryPreprocessor:
    """
    Intelligent query preprocessing for the RAAMP Assistant.
    Handles partial words, typos, marketing context, and query expansion.
    """
    
    # Marketing-related synonyms and expansions
    MARKETING_SYNONYMS = {
        # Campaign terms
        "campaign": ["campaigns", "ad campaign", "marketing campaign", "advertising"],
        "ad": ["ads", "advertisement", "advertising", "promotional"],
        "roi": ["return on investment", "returns", "revenue", "profit"],
        "ctr": ["click through rate", "click rate", "clicks"],
        "cpc": ["cost per click", "click cost"],
        "cpm": ["cost per mille", "impressions cost"],
        
        # Platform terms
        "raamp": ["ramp", "platform", "system", "app", "application"],
        "dashboard": ["home", "main page", "overview", "control panel"],
        "analytics": ["reports", "metrics", "data", "statistics", "insights"],
        
        # Actions
        "login": ["log in", "sign in", "signin", "access", "enter"],
        "signup": ["sign up", "register", "create account", "join"],
        "logout": ["log out", "sign out", "signout", "exit"],
        "setup": ["set up", "configure", "setting up", "configuration"],
        
        # Features
        "geo": ["geolocation", "location", "geographic", "local"],
        "intent": ["geo-intent", "geointent", "targeting"],
        "ai": ["artificial intelligence", "machine learning", "smart", "automated"],
        
        # Business terms
        "business": ["company", "brand", "store", "restaurant", "shop"],
        "customer": ["customers", "clients", "users", "audience"],
        "engagement": ["interactions", "activity", "responses"],
        
        # Help terms
        "help": ["support", "assist", "guide", "how to", "tutorial"],
        "problem": ["issue", "error", "trouble", "not working", "broken"],
        "fix": ["solve", "resolve", "repair", "troubleshoot"],
    }
    
    # Common typos and corrections
    COMMON_TYPOS = {
        "campain": "campaign",
        "campaing": "campaign",
        "campgn": "campaign",
        "advertisment": "advertisement",
        "advertisng": "advertising",
        "analtics": "analytics",
        "anlytics": "analytics",
        "dashbord": "dashboard",
        "dashbaord": "dashboard",
        "loging": "login",
        "loggin": "login",
        "signp": "signup",
        "singup": "signup",
        "buisness": "business",
        "bussiness": "business",
        "custmer": "customer",
        "customar": "customer",
        "feture": "feature",
        "featurs": "features",
        "setings": "settings",
        "settigns": "settings",
        "accout": "account",
        "acount": "account",
        "pasword": "password",
        "passwrd": "password",
        "conect": "connect",
        "connetc": "connect",
        "instagarm": "instagram",
        "instagam": "instagram",
        "facebok": "facebook",
        "facbook": "facebook",
        "googel": "google",
        "gogle": "google",
        "targetting": "targeting",
        "targteing": "targeting",
    }
    
    # Intent patterns
    INTENT_PATTERNS = {
        "greeting": [r"^(hi|hello|hey|good\s*(morning|afternoon|evening))"],
        "how_to": [r"how\s+(do|can|to|should)", r"what.*steps", r"guide.*to"],
        "what_is": [r"what\s+(is|are)", r"explain", r"describe", r"tell.*about"],
        "troubleshoot": [r"(not|isn't|doesn't|won't)\s+work", r"error", r"problem", r"issue", r"fix", r"broken"],
        "feature": [r"feature", r"can.*do", r"does.*support", r"capability"],
        "pricing": [r"price", r"cost", r"subscription", r"plan", r"payment", r"billing"],
        "account": [r"account", r"profile", r"settings", r"login", r"signup", r"password"],
        "integration": [r"connect", r"integrate", r"link", r"instagram", r"facebook", r"google"],
    }
    
    def __init__(self, fuzzy_threshold: float = 0.75):
        """
        Initialize the query preprocessor.
        
        Args:
            fuzzy_threshold: Minimum similarity for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold
        
        # Build reverse lookup for synonyms
        self._synonym_lookup = {}
        for canonical, synonyms in self.MARKETING_SYNONYMS.items():
            for syn in synonyms:
                self._synonym_lookup[syn.lower()] = canonical
    
    def preprocess(self, query: str) -> ProcessedQuery:
        """
        Preprocess a user query with all enhancements.
        
        Args:
            query: Raw user query
            
        Returns:
            ProcessedQuery with cleaned and expanded query
        """
        original = query
        corrections = []
        
        # Step 1: Basic cleaning
        cleaned = self._clean_query(query)
        
        # Step 2: Correct typos
        cleaned, typo_corrections = self._correct_typos(cleaned)
        corrections.extend(typo_corrections)
        
        # Step 3: Handle partial words
        cleaned, partial_corrections = self._handle_partial_words(cleaned)
        corrections.extend(partial_corrections)
        
        # Step 4: Detect intent
        intent, confidence = self._detect_intent(cleaned)
        
        # Step 5: Extract keywords
        keywords = self._extract_keywords(cleaned)
        
        # Step 6: Expand query with synonyms
        expanded = self._expand_query(cleaned, intent)
        
        return ProcessedQuery(
            original=original,
            cleaned=cleaned,
            expanded=expanded,
            keywords=keywords,
            intent=intent,
            confidence=confidence,
            corrections=corrections
        )
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize a query."""
        # Convert to lowercase
        cleaned = query.lower().strip()
        
        # Remove excessive punctuation but keep ? for questions
        cleaned = re.sub(r'[!.,;:]+', ' ', cleaned)
        cleaned = re.sub(r'\?+', '?', cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Handle common abbreviations
        cleaned = re.sub(r'\bpls\b', 'please', cleaned)
        cleaned = re.sub(r'\bu\b', 'you', cleaned)
        cleaned = re.sub(r'\br\b', 'are', cleaned)
        cleaned = re.sub(r'\bur\b', 'your', cleaned)
        cleaned = re.sub(r'\bthx\b', 'thanks', cleaned)
        cleaned = re.sub(r'\bty\b', 'thank you', cleaned)
        
        return cleaned.strip()
    
    def _correct_typos(self, query: str) -> Tuple[str, List[Dict[str, str]]]:
        """Correct common typos in the query."""
        corrections = []
        words = query.split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word.lower() in self.COMMON_TYPOS:
                correct = self.COMMON_TYPOS[clean_word.lower()]
                corrections.append({
                    "type": "typo",
                    "original": word,
                    "corrected": correct
                })
                corrected_words.append(word.replace(clean_word, correct))
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _handle_partial_words(self, query: str) -> Tuple[str, List[Dict[str, str]]]:
        """Handle partial/incomplete words using fuzzy matching."""
        corrections = []
        words = query.split()
        corrected_words = []
        
        # All possible words to match against
        all_words = set(self.COMMON_TYPOS.values())
        for synonyms in self.MARKETING_SYNONYMS.values():
            all_words.update(synonyms)
        all_words.update(self.MARKETING_SYNONYMS.keys())
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) < 3:  # Skip very short words
                corrected_words.append(word)
                continue
            
            # Try fuzzy matching for words that might be partial
            best_match = None
            best_score = 0
            
            for candidate in all_words:
                # Check if word is a prefix
                if candidate.startswith(clean_word.lower()) and len(clean_word) >= 3:
                    score = len(clean_word) / len(candidate) + 0.2  # Bonus for prefix match
                    if score > best_score:
                        best_score = score
                        best_match = candidate
                else:
                    # Fuzzy match
                    score = SequenceMatcher(None, clean_word.lower(), candidate).ratio()
                    if score > best_score and score >= self.fuzzy_threshold:
                        best_score = score
                        best_match = candidate
            
            if best_match and best_match.lower() != clean_word.lower():
                corrections.append({
                    "type": "partial",
                    "original": word,
                    "corrected": best_match,
                    "confidence": round(best_score, 2)
                })
                corrected_words.append(word.replace(clean_word, best_match))
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    def _detect_intent(self, query: str) -> Tuple[str, float]:
        """Detect the intent of the query."""
        query_lower = query.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent, 0.85
        
        # Default to general query
        return "general", 0.5
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query."""
        # Remove stop words
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "just", "i", "me", "my", "myself",
            "we", "our", "you", "your", "he", "she", "it", "they", "them",
            "what", "which", "who", "this", "that", "these", "those",
            "am", "and", "but", "if", "or", "because", "until", "while"
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _expand_query(self, query: str, intent: str) -> str:
        """Expand query with relevant synonyms and context."""
        words = query.split()
        expanded_parts = [query]  # Start with original
        
        # Add synonym expansions
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word).lower()
            
            # Check if word is a canonical term
            if clean_word in self.MARKETING_SYNONYMS:
                # Add some synonyms
                synonyms = self.MARKETING_SYNONYMS[clean_word][:2]
                for syn in synonyms:
                    if syn not in query.lower():
                        expanded_parts.append(syn)
            
            # Check if word is a synonym
            if clean_word in self._synonym_lookup:
                canonical = self._synonym_lookup[clean_word]
                if canonical not in query.lower():
                    expanded_parts.append(canonical)
        
        # Add intent-specific context
        intent_context = {
            "how_to": "steps guide tutorial",
            "troubleshoot": "fix solve problem error solution",
            "feature": "capability function what can",
            "account": "profile settings user",
            "integration": "connect link setup",
        }
        
        if intent in intent_context:
            expanded_parts.append(intent_context[intent])
        
        return ' '.join(expanded_parts)
    
    def get_search_query(self, query: str) -> str:
        """
        Get the optimized search query for retrieval.
        
        Args:
            query: Raw user query
            
        Returns:
            Optimized query for vector search
        """
        processed = self.preprocess(query)
        return processed.expanded


# Singleton instance
_preprocessor: QueryPreprocessor = None


def get_preprocessor() -> QueryPreprocessor:
    """Get the singleton preprocessor instance."""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = QueryPreprocessor()
    return _preprocessor


def preprocess_query(query: str) -> ProcessedQuery:
    """
    Convenience function to preprocess a query.
    
    Args:
        query: Raw user query
        
    Returns:
        ProcessedQuery object
    """
    return get_preprocessor().preprocess(query)


if __name__ == "__main__":
    # Test the preprocessor
    preprocessor = QueryPreprocessor()
    
    test_queries = [
        "how to login",
        "campain setup",  # typo
        "what is geo",  # partial word
        "instagarm connect",  # typo
        "my dashbord not working",  # typo + troubleshoot
        "roi reports",  # marketing term
        "hi there",  # greeting
        "fetures of raamp",  # typo + partial
    ]
    
    print("🧪 Testing Query Preprocessor")
    print("=" * 50)
    
    for query in test_queries:
        result = preprocessor.preprocess(query)
        print(f"\n📝 Original: '{result.original}'")
        print(f"   Cleaned:  '{result.cleaned}'")
        print(f"   Expanded: '{result.expanded[:80]}...'")
        print(f"   Intent:   {result.intent} ({result.confidence:.0%})")
        print(f"   Keywords: {result.keywords}")
        if result.corrections:
            print(f"   Corrections: {result.corrections}")
