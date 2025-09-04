"""
Advanced Entity Extraction Service with Confidence Scoring

This service provides sophisticated entity extraction capabilities with:
- Confidence scoring for extracted entities
- Entity categorization into different types
- Duplicate detection and merging
- Semantic similarity for entity matching
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import logging

# Optional imports with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ADVANCED_NLP_AVAILABLE = True
except ImportError:
    ADVANCED_NLP_AVAILABLE = False

@dataclass
class ExtractedEntity:
    """Represents an extracted entity with metadata"""
    name: str
    category: str
    confidence: float
    context: str
    mentions: int = 1
    first_seen: datetime = None
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.now()


class AdvancedEntityExtractor:
    """Advanced entity extraction with confidence scoring and categorization"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.similarity_threshold = 0.85
        self.logger = logging.getLogger(__name__)
        
        # Initialize semantic model if available
        self.semantic_model = None
        global ADVANCED_NLP_AVAILABLE
        if ADVANCED_NLP_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("✅ Advanced NLP features loaded with sentence transformers")
            except Exception as e:
                self.logger.warning(f"Failed to load sentence transformer: {e}")
                ADVANCED_NLP_AVAILABLE = False
        
        # Entity patterns for different categories
        self.patterns = {
            'people': [
                r'\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?|Professor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b(?=\s+(?:said|wrote|thinks|believes|argues|suggests|explains|states|mentioned|told|asked))',
                r'\b([A-Z][a-z]+)\s+(?:is a|was a|works as|worked as|teaches|taught|studies)',
                r'(?:by|from|according to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            'concepts': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:theory|principle|concept|framework|model|approach|methodology|paradigm)',
                r'(?:concept of|theory of|principle of|idea of)\s+([a-z][a-z\s]+)',
                r'\b(artificial intelligence|machine learning|deep learning|neural networks|algorithms|programming|software|technology)\b',
                r'\b([a-z]+(?:\s+[a-z]+)*)\s+(?:is defined as|refers to|means)',
                r'(?:understanding|learning|studying|exploring)\s+([a-z][a-z\s]+(?:theory|concept|principle))'
            ],
            'tools': [
                r'\b(Python|JavaScript|Java|C\+\+|React|Vue|Angular|Flask|Django|Node\.js|TensorFlow|PyTorch|Git|Docker|Kubernetes)\b',
                r'\b([A-Z][a-zA-Z]*)\s+(?:library|framework|tool|software|application|platform|system)',
                r'using\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)',
                r'with\s+([A-Z][a-zA-Z]*(?:\.[a-zA-Z]+)*)'
            ],
            'locations': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s+(?:[A-Z]{2}|[A-Z][a-z]+)',
                r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+University)',
                r'\bat\s+(Stanford|MIT|Harvard|Berkeley|Google|Microsoft|Apple|Meta|OpenAI)'
            ],
            'temporal_events': [
                r'(?:in|during|since|before|after)\s+(\d{4}|\d{1,2}/\d{1,2}/\d{4}|January|February|March|April|May|June|July|August|September|October|November|December)\s*\d*',
                r'(?:recently|yesterday|today|tomorrow|next week|last week|this year|last year)',
                r'(?:when|while)\s+([^,\.]+(?:happened|occurred|started|began|ended))'
            ]
        }
        
        # Common stop words and noise patterns
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are', 
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
    def extract_entities_with_confidence(self, text: str) -> Dict[str, Any]:
        """Extract entities with confidence scoring and categorization"""
        if not text or not text.strip():
            return self._empty_result()
        
        self.logger.debug(f"Extracting entities from text of length: {len(text)}")
        
        entities = {
            'people': [],
            'concepts': [],
            'tools': [],
            'locations': [],
            'temporal_events': [],
            'definitions': {}
        }
        
        # Extract entities for each category
        for category, patterns in self.patterns.items():
            category_entities = self._extract_category_entities(text, category, patterns)
            entities[category] = category_entities
        
        # Extract definitions separately
        entities['definitions'] = self._extract_definitions(text)
        
        # Clean and deduplicate entities
        entities = self._clean_and_deduplicate(entities)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(entities)
        
        result = {
            'entities': entities,
            'overall_confidence': overall_confidence,
            'total_entities': self._count_total_entities(entities),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        self.logger.debug(f"Extracted {result['total_entities']} entities with confidence {overall_confidence:.3f}")
        return result
    
    def _extract_category_entities(self, text: str, category: str, patterns: List[str]) -> List[Dict[str, Any]]:
        """Extract entities for a specific category"""
        entities = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity_text = match.group(1) if match.groups() else match.group(0)
                entity_text = entity_text.strip()
                
                # Skip if too short or contains only stop words
                if len(entity_text) < 2 or self._is_noise(entity_text):
                    continue
                
                # Get context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Calculate confidence score
                confidence = self._calculate_confidence_score(entity_text, context, category)
                
                if confidence >= self.confidence_threshold:
                    entities.append({
                        'name': entity_text,
                        'confidence': confidence,
                        'context': context,
                        'pattern_matched': pattern,
                        'position': match.start()
                    })
        
        return entities
    
    def _extract_definitions(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Extract definitions from text"""
        definitions = {}
        
        # Pattern for explicit definitions
        definition_patterns = [
            r'([A-Za-z][a-zA-Z\s]+)\s+(?:is|are|refers to|means|defined as)\s+(.+?)(?:\.|;|,|$)',
            r'(?:The term|The concept of|The idea of)\s+([a-zA-Z\s]+)\s+(?:is|refers to|means)\s+(.+?)(?:\.|;|,|$)',
            r'([A-Za-z][a-zA-Z\s]+):\s+(.+?)(?:\.|;|$)'
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) > 2 and len(definition) > 10 and not self._is_noise(term):
                    confidence = self._calculate_definition_confidence(term, definition)
                    if confidence >= self.confidence_threshold:
                        definitions[term] = {
                            'definition': definition,
                            'confidence': confidence,
                            'context': match.group(0)
                        }
        
        return definitions
    
    def _calculate_confidence_score(self, entity: str, context: str, category: str) -> float:
        """Calculate confidence score for extracted entity"""
        score = 0.5  # Base score
        
        # Length penalty for very short entities
        if len(entity) < 3:
            score -= 0.2
        elif len(entity) > 20:
            score -= 0.1
        
        # Capitalization bonus
        if entity[0].isupper():
            score += 0.1
        if entity.istitle():
            score += 0.1
        
        # Context quality
        context_lower = context.lower()
        
        # Category-specific scoring
        if category == 'people':
            if any(word in context_lower for word in ['said', 'wrote', 'thinks', 'believes', 'researcher', 'professor', 'dr.']):
                score += 0.2
            if any(word in context_lower for word in ['university', 'published', 'study', 'research']):
                score += 0.1
                
        elif category == 'concepts':
            if any(word in context_lower for word in ['theory', 'concept', 'principle', 'framework', 'approach']):
                score += 0.2
            if any(word in context_lower for word in ['understanding', 'learning', 'study', 'analysis']):
                score += 0.1
                
        elif category == 'tools':
            if any(word in context_lower for word in ['using', 'with', 'library', 'framework', 'tool']):
                score += 0.2
            if any(word in context_lower for word in ['code', 'programming', 'software', 'development']):
                score += 0.1
        
        # Avoid noise patterns
        if entity.lower() in self.stop_words:
            score -= 0.5
        if len(entity.split()) > 5:  # Very long entities are often noise
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_definition_confidence(self, term: str, definition: str) -> float:
        """Calculate confidence for definition extraction"""
        score = 0.6  # Base score for definitions
        
        # Term quality
        if len(term.split()) <= 3:  # Reasonable term length
            score += 0.1
        if term.istitle():
            score += 0.1
        
        # Definition quality
        if len(definition) > 20:  # Substantial definition
            score += 0.1
        if len(definition) > 50:
            score += 0.1
        
        # Check for definition indicators
        if any(word in definition.lower() for word in ['refers to', 'means', 'defined as', 'is a type of']):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _is_noise(self, entity: str) -> bool:
        """Check if entity is likely noise"""
        entity_lower = entity.lower()
        
        # Common noise patterns
        if entity_lower in self.stop_words:
            return True
        if len(entity) < 2:
            return True
        if entity.isdigit():
            return True
        if re.match(r'^[^\w\s]+$', entity):  # Only punctuation
            return True
        
        return False
    
    def merge_similar_entities(self, existing_entities: List[str], new_entity: str) -> Optional[str]:
        """Check if new entity should be merged with existing ones"""
        if not existing_entities or not new_entity:
            return None
        
        new_entity_lower = new_entity.lower()
        
        # Exact match (case insensitive)
        for entity in existing_entities:
            if entity.lower() == new_entity_lower:
                return entity
        
        # Substring match
        for entity in existing_entities:
            if new_entity_lower in entity.lower() or entity.lower() in new_entity_lower:
                if len(new_entity) > len(entity):
                    return new_entity  # Keep longer version
                else:
                    return entity
        
        # Semantic similarity (if available)
        if ADVANCED_NLP_AVAILABLE and self.semantic_model:
            try:
                new_embedding = self.semantic_model.encode([new_entity])
                existing_embeddings = self.semantic_model.encode(existing_entities)
                
                similarities = cosine_similarity(new_embedding, existing_embeddings)[0]
                max_similarity = np.max(similarities)
                
                if max_similarity >= self.similarity_threshold:
                    best_match_idx = np.argmax(similarities)
                    return existing_entities[best_match_idx]
                    
            except Exception as e:
                self.logger.warning(f"Semantic similarity failed: {e}")
        
        return None  # No similar entity found
    
    def _clean_and_deduplicate(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and deduplicate entities within each category"""
        cleaned = {}
        
        for category, entity_list in entities.items():
            if category == 'definitions':
                cleaned[category] = entity_list  # Definitions are already deduplicated by key
                continue
            
            if not isinstance(entity_list, list):
                cleaned[category] = entity_list
                continue
            
            # Group similar entities
            unique_entities = []
            seen_names = set()
            
            for entity in entity_list:
                entity_name = entity['name']
                entity_lower = entity_name.lower()
                
                # Check for exact matches
                if entity_lower in seen_names:
                    continue
                
                # Check for merging with existing entities
                existing_names = [e['name'] for e in unique_entities]
                merged_name = self.merge_similar_entities(existing_names, entity_name)
                
                if merged_name:
                    # Update existing entity if we found a better version
                    if merged_name == entity_name:  # New entity is better
                        # Remove the old one and add the new one
                        unique_entities = [e for e in unique_entities if e['name'].lower() != merged_name.lower()]
                        unique_entities.append(entity)
                        seen_names.discard(merged_name.lower())
                        seen_names.add(entity_lower)
                    # If merged_name is existing entity, keep it as is
                else:
                    # Add as new entity
                    unique_entities.append(entity)
                    seen_names.add(entity_lower)
            
            # Sort by confidence
            unique_entities.sort(key=lambda x: x['confidence'], reverse=True)
            cleaned[category] = unique_entities
        
        return cleaned
    
    def _calculate_overall_confidence(self, entities: Dict[str, Any]) -> float:
        """Calculate overall extraction confidence"""
        total_entities = 0
        total_confidence = 0.0
        
        for category, entity_list in entities.items():
            if category == 'definitions':
                for term, definition_data in entity_list.items():
                    total_entities += 1
                    total_confidence += definition_data['confidence']
            elif isinstance(entity_list, list):
                for entity in entity_list:
                    total_entities += 1
                    total_confidence += entity['confidence']
        
        return total_confidence / total_entities if total_entities > 0 else 0.0
    
    def _count_total_entities(self, entities: Dict[str, Any]) -> int:
        """Count total entities extracted"""
        count = 0
        for category, entity_list in entities.items():
            if category == 'definitions':
                count += len(entity_list)
            elif isinstance(entity_list, list):
                count += len(entity_list)
        return count
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty extraction result"""
        return {
            'entities': {
                'people': [],
                'concepts': [],
                'tools': [],
                'locations': [],
                'temporal_events': [],
                'definitions': {}
            },
            'overall_confidence': 0.0,
            'total_entities': 0,
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def get_entity_statistics(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistical information about extracted entities"""
        stats = {
            'category_counts': {},
            'confidence_distribution': {},
            'top_entities': {}
        }
        
        for category, entity_list in entities['entities'].items():
            if category == 'definitions':
                count = len(entity_list)
                confidences = [data['confidence'] for data in entity_list.values()]
            elif isinstance(entity_list, list):
                count = len(entity_list)
                confidences = [entity['confidence'] for entity in entity_list]
            else:
                count = 0
                confidences = []
            
            stats['category_counts'][category] = count
            
            if confidences:
                stats['confidence_distribution'][category] = {
                    'mean': sum(confidences) / len(confidences),
                    'min': min(confidences),
                    'max': max(confidences)
                }
                
                # Top entities in category
                if category == 'definitions':
                    top = sorted(entity_list.items(), key=lambda x: x[1]['confidence'], reverse=True)[:3]
                    stats['top_entities'][category] = [(name, data['confidence']) for name, data in top]
                elif isinstance(entity_list, list):
                    top = sorted(entity_list, key=lambda x: x['confidence'], reverse=True)[:3]
                    stats['top_entities'][category] = [(entity['name'], entity['confidence']) for entity in top]
        
        return stats


# Global instance
entity_extractor = AdvancedEntityExtractor()