"""
Context Service for Knowledge Graph

Provides context-aware conversation capabilities by extracting relevant
information from the knowledge graph based on user input and conversation history.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from services.enhanced_entity_extractor import entity_extractor

logger = logging.getLogger(__name__)

class ContextService:
    """Context-aware conversation service using knowledge graph"""
    
    def __init__(self, kg_builder):
        self.kg_builder = kg_builder
        self.context_window = 5  # Number of recent interactions to consider
        self.max_context_entities = 10  # Maximum entities to include in context
        self.max_related_thoughts = 5  # Maximum related thoughts to include
        self.entity_extractor = entity_extractor
        
    def get_conversation_context(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Extract relevant context from knowledge graph for conversation"""
        try:
            # Extract entities from user input
            mentioned_entities = self._extract_entities_from_input(user_input)
            logger.debug(f"Extracted entities from input: {mentioned_entities}")
            
            if not mentioned_entities:
                return {'related_entities': [], 'related_thoughts': [], 'context_summary': ''}
            
            # Get context from knowledge graph
            with self.kg_builder.driver.session() as session:
                context_data = self._query_context_from_graph(session, mentioned_entities, session_id)
                
            # Format and rank context
            formatted_context = self._format_and_rank_context(context_data, mentioned_entities)
            
            logger.debug(f"Retrieved context with {len(formatted_context['related_entities'])} entities and {len(formatted_context['related_thoughts'])} thoughts")
            return formatted_context
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {'related_entities': [], 'related_thoughts': [], 'context_summary': 'Context extraction failed'}
    
    def _extract_entities_from_input(self, text: str) -> List[str]:
        """Extract entities from user input using multiple methods"""
        entities = []
        
        # Method 1: Use advanced entity extractor
        try:
            extracted = self.entity_extractor.extract_entities_with_confidence(text)
            for category, entity_list in extracted.get('entities', {}).items():
                entities.extend([entity['text'] for entity in entity_list])
        except Exception as e:
            logger.warning(f"Advanced entity extraction failed: {e}")
        
        # Method 2: Extract capitalized words (potential proper nouns)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized_words)
        
        # Method 3: Extract quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', text)
        entities.extend(quoted_terms)
        
        # Method 4: Extract technical terms (words with specific patterns)
        technical_terms = re.findall(r'\b(?:AI|ML|API|GPU|CPU|HTTP|JSON|XML|SQL|NoSQL)\b', text, re.IGNORECASE)
        entities.extend(technical_terms)
        
        # Clean and deduplicate
        cleaned_entities = []
        seen = set()
        for entity in entities:
            entity_clean = entity.strip().lower()
            if len(entity_clean) > 2 and entity_clean not in seen:
                cleaned_entities.append(entity.strip())
                seen.add(entity_clean)
        
        return cleaned_entities[:self.max_context_entities]
    
    def _query_context_from_graph(self, session, mentioned_entities: List[str], session_id: str) -> Dict[str, Any]:
        """Query the knowledge graph for relevant context"""
        
        # Query 1: Find entities mentioned in the input
        entity_context_query = """
            MATCH (e:Entity) 
            WHERE toLower(e.name) IN [entity IN $entities | toLower(entity)]
            OPTIONAL MATCH (e)<-[:MENTIONS]-(t:Thought)-[:PART_OF]->(s:Session)
            OPTIONAL MATCH (e)-[r]-(related:Entity)
            WITH e, 
                 collect(DISTINCT {
                     content: t.content,
                     type: t.type,
                     confidence: t.confidence,
                     timestamp: t.timestamp,
                     session_id: s.id
                 }) as related_thoughts,
                 collect(DISTINCT {
                     name: related.name,
                     type: labels(related)[0],
                     relationship: type(r)
                 }) as related_entities
            RETURN e.name as entity_name,
                   labels(e) as entity_types,
                   e.definition as definition,
                   related_thoughts,
                   related_entities
            ORDER BY size(related_thoughts) DESC
            LIMIT $max_entities
        """
        
        entity_results = session.run(
            entity_context_query, 
            entities=mentioned_entities, 
            max_entities=self.max_context_entities
        )
        
        # Query 2: Get recent session context
        session_context_query = """
            MATCH (s:Session {id: $session_id})-[:CONTAINS]->(t:Thought)
            OPTIONAL MATCH (t)-[:MENTIONS]->(e:Entity)
            WITH t, collect(DISTINCT e.name) as mentioned_entities
            RETURN t.content as content,
                   t.type as type,
                   t.confidence as confidence,
                   t.timestamp as timestamp,
                   mentioned_entities
            ORDER BY t.timestamp DESC
            LIMIT $context_window
        """
        
        session_results = session.run(
            session_context_query,
            session_id=session_id,
            context_window=self.context_window
        )
        
        # Query 3: Find similar conversations
        similarity_query = """
            MATCH (e:Entity) 
            WHERE toLower(e.name) IN [entity IN $entities | toLower(entity)]
            MATCH (e)<-[:MENTIONS]-(t:Thought)-[:PART_OF]->(s:Session)
            WHERE s.id <> $session_id
            WITH s, count(DISTINCT e) as entity_overlap,
                 collect(DISTINCT t.content) as thoughts
            ORDER BY entity_overlap DESC
            RETURN s.id as session_id,
                   s.reasoning_strategy as strategy,
                   s.domain as domain,
                   s.timestamp as timestamp,
                   entity_overlap,
                   thoughts[0..2] as sample_thoughts
            LIMIT 3
        """
        
        similarity_results = session.run(
            similarity_query,
            entities=mentioned_entities,
            session_id=session_id
        )
        
        return {
            'entity_context': list(entity_results),
            'session_context': list(session_results),
            'similar_sessions': list(similarity_results)
        }
    
    def _format_and_rank_context(self, context_data: Dict[str, Any], mentioned_entities: List[str]) -> Dict[str, Any]:
        """Format and rank context information for use in prompts"""
        
        related_entities = []
        related_thoughts = []
        
        # Process entity context
        for record in context_data['entity_context']:
            entity_info = {
                'name': record['entity_name'],
                'types': record['entity_types'],
                'definition': record.get('definition'),
                'mention_count': len(record.get('related_thoughts', [])),
                'related_concepts': [rel['name'] for rel in record.get('related_entities', [])[:3]]
            }
            related_entities.append(entity_info)
            
            # Add thoughts related to this entity
            for thought in record.get('related_thoughts', [])[:2]:
                if thought['content'] and len(thought['content'].strip()) > 10:
                    thought_info = {
                        'content': thought['content'][:200] + '...' if len(thought['content']) > 200 else thought['content'],
                        'type': thought.get('type', 'unknown'),
                        'confidence': thought.get('confidence', 0.5),
                        'timestamp': thought.get('timestamp'),
                        'session_id': thought.get('session_id'),
                        'relevance_score': self._calculate_thought_relevance(thought['content'], mentioned_entities)
                    }
                    related_thoughts.append(thought_info)
        
        # Process session context
        for record in context_data['session_context']:
            if record['content'] and len(record['content'].strip()) > 10:
                thought_info = {
                    'content': record['content'][:200] + '...' if len(record['content']) > 200 else record['content'],
                    'type': record.get('type', 'session'),
                    'confidence': record.get('confidence', 0.5),
                    'timestamp': record.get('timestamp'),
                    'mentioned_entities': record.get('mentioned_entities', []),
                    'relevance_score': self._calculate_thought_relevance(record['content'], mentioned_entities)
                }
                related_thoughts.append(thought_info)
        
        # Sort thoughts by relevance and recency
        related_thoughts.sort(key=lambda x: (x['relevance_score'], x.get('timestamp', datetime.min)), reverse=True)
        
        # Generate context summary
        context_summary = self._generate_context_summary(related_entities, related_thoughts, context_data['similar_sessions'])
        
        return {
            'related_entities': related_entities[:self.max_context_entities],
            'related_thoughts': related_thoughts[:self.max_related_thoughts],
            'similar_sessions': list(context_data['similar_sessions'])[:3],
            'context_summary': context_summary,
            'extracted_entities': mentioned_entities
        }
    
    def _calculate_thought_relevance(self, thought_content: str, mentioned_entities: List[str]) -> float:
        """Calculate relevance score for a thought based on entity mentions"""
        if not thought_content or not mentioned_entities:
            return 0.0
        
        content_lower = thought_content.lower()
        matches = sum(1 for entity in mentioned_entities if entity.lower() in content_lower)
        
        # Base score from entity matches
        relevance = matches / len(mentioned_entities) if mentioned_entities else 0
        
        # Boost for exact matches
        exact_matches = sum(1 for entity in mentioned_entities if entity in thought_content)
        relevance += exact_matches * 0.2
        
        return min(relevance, 1.0)
    
    def _generate_context_summary(self, entities: List[Dict], thoughts: List[Dict], similar_sessions: List[Any]) -> str:
        """Generate a brief context summary"""
        if not entities and not thoughts:
            return "No relevant context found from previous conversations."
        
        summary_parts = []
        
        if entities:
            entity_names = [e['name'] for e in entities[:3]]
            summary_parts.append(f"Previously discussed: {', '.join(entity_names)}")
        
        if thoughts:
            thought_count = len(thoughts)
            summary_parts.append(f"{thought_count} related insights found")
        
        if similar_sessions:
            summary_parts.append(f"{len(similar_sessions)} related conversations")
        
        return ". ".join(summary_parts) + "."
    
    def build_enhanced_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Build prompt with graph context for better AI responses"""
        
        base_prompt = """You are a knowledgeable AI assistant with access to conversation history and related concepts from previous discussions."""
        
        if context.get('context_summary'):
            base_prompt += f"\n\nContext: {context['context_summary']}"
        
        # Add entity context
        if context.get('related_entities'):
            entities_section = "\n\nRelevant concepts from our knowledge base:"
            for entity in context['related_entities'][:3]:
                entities_section += f"\n- {entity['name']}"
                if entity.get('definition'):
                    entities_section += f": {entity['definition'][:100]}..."
                if entity.get('related_concepts'):
                    entities_section += f" (Related: {', '.join(entity['related_concepts'][:2])})"
            base_prompt += entities_section
        
        # Add thought context
        if context.get('related_thoughts'):
            thoughts_section = "\n\nRelevant insights from previous conversations:"
            for thought in context['related_thoughts'][:3]:
                confidence_indicator = "🔴" if thought['confidence'] < 0.5 else "🟡" if thought['confidence'] < 0.8 else "🟢"
                thoughts_section += f"\n- {confidence_indicator} {thought['content']}"
            base_prompt += thoughts_section
        
        # Add similar sessions
        if context.get('similar_sessions'):
            sessions_section = "\n\nRelated conversation topics:"
            for session in context['similar_sessions']:
                sessions_section += f"\n- {session.get('strategy', 'General discussion')} about {session.get('domain', 'various topics')}"
            base_prompt += sessions_section
        
        # Instructions for using context
        base_prompt += """

When responding:
1. Reference relevant previous discussions when helpful
2. Build upon established knowledge and definitions
3. Point out interesting connections between topics
4. Avoid repeating information unnecessarily
5. Use the context to provide more insightful and personalized responses"""
        
        base_prompt += f"\n\nCurrent question: {user_input}"
        
        return base_prompt
    
    def get_context_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get metadata about the context for response tracking"""
        return {
            'context_entities_count': len(context.get('related_entities', [])),
            'context_thoughts_count': len(context.get('related_thoughts', [])),
            'similar_sessions_count': len(context.get('similar_sessions', [])),
            'extracted_entities': context.get('extracted_entities', []),
            'context_summary': context.get('context_summary', ''),
            'used_context': bool(context.get('related_entities') or context.get('related_thoughts'))
        }


# Export
__all__ = ['ContextService']