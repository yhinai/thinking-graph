import os
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configure Gemini API
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
genai.configure(api_key=gemini_api_key)


@dataclass
class ThoughtNode:
    """Represents a single thought or reasoning step"""
    id: str
    content: str
    type: str  # 'observation', 'analysis', 'decision', 'action', 'reflection'
    entities: List[str]
    tools_mentioned: List[str]
    confidence: float
    timestamp: datetime


@dataclass
class ReasoningEdge:
    """Represents a connection between thoughts"""
    source_id: str
    target_id: str
    relationship: str  # 'leads_to', 'depends_on', 'contradicts', 'supports'
    strength: float


class ThinkingAnalyzer:
    """Analyzes agent thinking text and extracts structured information"""

    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze_thinking_text(self, thinking_text: str) -> Dict[str, Any]:
        """Use Gemini to analyze the thinking text and extract structured data"""

        prompt = f"""
        Analyze this agent thinking process and extract structured information:

        Text: "{thinking_text}"

        Please provide a JSON response with the following structure:
        {{

            "thoughts": [
                {{
                    "content": "extracted thought content",
                    "type": "observation|analysis|decision|action|reflection",
                    "entities": ["entity1", "entity2"],
                    "tools_mentioned": ["tool1", "tool2"],
                    "confidence": 0.8
                }}
            ],
            "relationships": [
                {{
                    "source_thought": 0,
                    "target_thought": 1,
                    "relationship": "leads_to|depends_on|supports|contradicts",
                    "strength": 0.9
                }}
            ],
            "reasoning_strategy": "step_by_step|tool_selection|problem_decomposition|verification",
            "domain": "weather|api|general",
            "success_indicators": ["indicator1", "indicator2"]
        }}

        Guidelines:
        - Extract individual reasoning steps as separate thoughts
        - Identify entities (functions, parameters, cities, etc.)
        - Detect tools/APIs mentioned
        - Assess confidence based on certainty language
        - Map logical flow between thoughts
        - Classify the overall reasoning strategy
        """

        try:
            response = self.model.generate_content(prompt)
            # Clean the response to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            return json.loads(response_text)
        except Exception as e:
            print(f"Error analyzing with Gemini: {e}")
            return self._fallback_analysis(thinking_text)

    def _fallback_analysis(self, thinking_text: str) -> Dict[str, Any]:
        """Fallback analysis using regex patterns"""
        sentences = re.split(r'[.!?]+', thinking_text)

        thoughts = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                thought_type = self._classify_sentence(sentence)
                entities = self._extract_entities(sentence)
                tools = self._extract_tools(sentence)

                thoughts.append({
                    "content": sentence.strip(),
                    "type": thought_type,
                    "entities": entities,
                    "tools_mentioned": tools,
                    "confidence": 0.7
                })

        # Simple sequential relationships
        relationships = []
        for i in range(len(thoughts) - 1):
            relationships.append({
                "source_thought": i,
                "target_thought": i + 1,
                "relationship": "leads_to",
                "strength": 0.8
            })

        return {
            "thoughts": thoughts,
            "relationships": relationships,
            "reasoning_strategy": "sequential",
            "domain": "general",
            "success_indicators": [],
        }

    def _classify_sentence(self, sentence: str) -> str:
        """Simple classification of sentence type"""
        sentence_lower = sentence.lower()
        if any(word in sentence_lower for word in ['observe', 'see', 'notice', 'found']):
            return 'observation'
        elif any(word in sentence_lower for word in ['analyze', 'determine', 'identify']):
            return 'analysis'
        elif any(word in sentence_lower for word in ['decide', 'choose', 'will']):
            return 'decision'
        elif any(word in sentence_lower for word in ['call', 'execute', 'run', 'invoke']):
            return 'action'
        else:
            return 'reflection'

    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential entities from text"""
        # Look for function names, parameters, quoted strings
        entities = []

        # Function names (camelCase or snake_case)
        functions = re.findall(r'\b[a-z][a-zA-Z0-9_]*(?:[A-Z][a-z]*)*\b', text)
        entities.extend([f for f in functions if len(f) > 3])

        # Quoted strings
        quoted = re.findall(r"'([^']*)'|\"([^\"]*)\"", text)
        entities.extend([q[0] or q[1] for q in quoted])

        return list(set(entities))

    def _extract_tools(self, text: str) -> List[str]:
        """Extract tool/API mentions from text"""
        tools = []

        # Common API/tool patterns
        tool_patterns = [
            r'\w+API',
            r'\w+_api',
            r'default_api',
            r'\w+Tool',
            r'\w+Service'
        ]

        for pattern in tool_patterns:
            tools.extend(re.findall(pattern, text, re.IGNORECASE))

        return list(set(tools))


class KnowledgeGraphBuilder:
    """Builds and manages the Neo4j knowledge graph"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_constraints()

    def _create_constraints(self):
        """Create necessary constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT thought_id IF NOT EXISTS FOR (t:Thought) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE",
                "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
                "CREATE CONSTRAINT tool_name IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE"
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint creation note: {e}")

    def add_thinking_session(self, session_id: str, thinking_text: str,
                             analyzed_data: Dict[str, Any], overwrite: bool = True) -> str:
        """Add a complete thinking session to the knowledge graph"""

        with self.driver.session() as session:
            # Check if session already exists and handle accordingly
            existing_session = session.run("""
                MATCH (s:Session {id: $session_id})
                RETURN s.id as id
            """, session_id=session_id).single()

            if existing_session and not overwrite:
                print(f"Session {session_id} already exists. Use overwrite=True to replace it.")
                return session_id
            elif existing_session and overwrite:
                # Delete existing session and all related nodes
                print(f"Overwriting existing session: {session_id}")
                session.run("""
                    MATCH (s:Session {id: $session_id})
                    OPTIONAL MATCH (s)-[:CONTAINS]->(t:Thought)
                    OPTIONAL MATCH (t)-[r1:MENTIONS|USES_TOOL|REASONING_FLOW]-()
                    DELETE r1, t, s
                """, session_id=session_id)

            # Create session node
            session.run("""
                MERGE (s:Session {id: $session_id})
                SET s.raw_text = $thinking_text,
                    s.reasoning_strategy = $strategy,
                    s.domain = $domain,
                    s.timestamp = datetime(),
                    s.success_indicators = $success_indicators
            """, session_id=session_id, thinking_text=thinking_text,
                        strategy=analyzed_data.get('reasoning_strategy', 'unknown'),
                        domain=analyzed_data.get('domain', 'general'),
                        success_indicators=analyzed_data.get('success_indicators', []))

            # Create thought nodes
            thought_ids = []
            for i, thought in enumerate(analyzed_data['thoughts']):
                thought_id = f"{session_id}_thought_{i}"
                thought_ids.append(thought_id)

                session.run("""
                    MERGE (t:Thought {id: $thought_id})
                    SET t.content = $content,
                        t.type = $type,
                        t.confidence = $confidence,
                        t.session_id = $session_id,
                        t.sequence_order = $order,
                        t.timestamp = datetime()
                """, thought_id=thought_id, content=thought['content'],
                            type=thought['type'], confidence=thought['confidence'],
                            session_id=session_id, order=i)

                # Connect thought to session
                session.run("""
                    MATCH (s:Session {id: $session_id})
                    MATCH (t:Thought {id: $thought_id})
                    MERGE (s)-[:CONTAINS]->(t)
                """, session_id=session_id, thought_id=thought_id)

                # Create entity nodes and relationships
                for entity in thought['entities']:
                    session.run("""
                        MERGE (e:Entity {name: $entity})
                        WITH e
                        MATCH (t:Thought {id: $thought_id})
                        MERGE (t)-[:MENTIONS]->(e)
                    """, entity=entity, thought_id=thought_id)

                # Create tool nodes and relationships
                for tool in thought['tools_mentioned']:
                    session.run("""
                        MERGE (tool:Tool {name: $tool})
                        WITH tool
                        MATCH (t:Thought {id: $thought_id})
                        MERGE (t)-[:USES_TOOL]->(tool)
                    """, tool=tool, thought_id=thought_id)

            # Create relationships between thoughts
            for rel in analyzed_data.get('relationships', []):
                source_id = thought_ids[rel['source_thought']]
                target_id = thought_ids[rel['target_thought']]

                session.run("""
                    MATCH (source:Thought {id: $source_id})
                    MATCH (target:Thought {id: $target_id})
                    MERGE (source)-[r:REASONING_FLOW {type: $rel_type}]->(target)
                    SET r.strength = $strength
                """, source_id=source_id, target_id=target_id,
                            rel_type=rel['relationship'], strength=rel['strength'])

        return session_id

    def query_reasoning_patterns(self) -> List[Dict[str, Any]]:
        """Query for common reasoning patterns"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Session)
                RETURN s.reasoning_strategy as strategy, 
                       s.domain as domain,
                       count(s) as frequency
                ORDER BY frequency DESC
            """)
            return [record.data() for record in result]

    def find_successful_patterns(self) -> List[Dict[str, Any]]:
        """Find patterns that led to successful reasoning"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Session)-[:CONTAINS]->(t:Thought)
                WHERE size(s.success_indicators) > 0
                WITH s.reasoning_strategy as strategy, s.success_indicators as indicators,
                     collect(t.type) as thought_sequence
                RETURN strategy, thought_sequence, indicators, count(*) as frequency
                ORDER BY frequency DESC
            """)
            return [record.data() for record in result]

    def get_tool_usage_patterns(self) -> List[Dict[str, Any]]:
        """Analyze tool usage patterns in reasoning"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Thought)-[:USES_TOOL]->(tool:Tool)
                WITH tool.name as tool_name, 
                     collect(t.type) as thought_types,
                     count(t) as usage_count
                RETURN tool_name, thought_types, usage_count
                ORDER BY usage_count DESC
            """)
            return [record.data() for record in result]

    def close(self):
        """Close the database connection"""
        self.driver.close()


class AgentThinkingKG:
    """Main class that orchestrates the thinking-to-KG conversion"""

    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None,
                 neo4j_password: str = None):
        # Use provided credentials or environment variables
        self.neo4j_uri = neo4j_uri or os.getenv('NEO4J_URI')
        self.neo4j_user = neo4j_user or os.getenv('NEO4J_USER')
        self.neo4j_password = neo4j_password or os.getenv('NEO4J_PASSWORD')
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError("Neo4j credentials must be provided either through parameters or environment variables")

        self.analyzer = ThinkingAnalyzer()
        self.kg_builder = KnowledgeGraphBuilder(
            self.neo4j_uri, self.neo4j_user, self.neo4j_password
        )

    def process_thinking(self, thinking_text: str, session_id: str = None,
                         overwrite: bool = True) -> str:
        """Process agent thinking text and add to knowledge graph"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"Analyzing thinking text...")
        analyzed_data = self.analyzer.analyze_thinking_text(thinking_text)

        print(f"Adding to knowledge graph...")
        result_session_id = self.kg_builder.add_thinking_session(
            session_id, thinking_text, analyzed_data, overwrite
        )

        print(f"Successfully processed thinking session: {result_session_id}")
        return result_session_id

    def analyze_patterns(self, session_id: str = None) -> Dict[str, Any]:
        """Analyze reasoning patterns in the knowledge graph"""
        # Note: session_id parameter added for compatibility but not used in current implementation
        return {
            'reasoning_patterns': self.kg_builder.query_reasoning_patterns(),
            'successful_patterns': self.kg_builder.find_successful_patterns(),
            'tool_usage_patterns': self.kg_builder.get_tool_usage_patterns()
        }

    def clear_database(self):
        """Clear all data from the knowledge graph (use with caution!)"""
        with self.kg_builder.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared successfully!")

    def get_session_info(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Get information about sessions in the database"""
        with self.kg_builder.driver.session() as session:
            if session_id:
                result = session.run("""
                    MATCH (s:Session {id: $session_id})-[:CONTAINS]->(t:Thought)
                    RETURN s.id as session_id, s.reasoning_strategy as strategy,
                           collect(t.content) as thoughts
                """, session_id=session_id)
            else:
                result = session.run("""
                    MATCH (s:Session)
                    OPTIONAL MATCH (s)-[:CONTAINS]->(t:Thought)
                    WITH s, count(t) as thought_count
                    RETURN s.id as session_id, s.reasoning_strategy as strategy,
                           thought_count, toString(s.timestamp) as timestamp
                    ORDER BY s.timestamp DESC
                """)
            return [record.data() for record in result]

    def close(self):
        """Close database connections"""
        self.kg_builder.close()

    def get_full_graph_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all nodes and relationships for the knowledge graph visualization"""
        with self.kg_builder.driver.session() as session:
            # Fetch all nodes
            nodes_result = session.run("MATCH (n) RETURN n")
            nodes = []
            for record in nodes_result:
                node = record['n']
                nodes.append({
                    'id': node.element_id,
                    'label': node.get('name') or node.get('content') or node.element_id,
                    'type': list(node.labels)[0] if list(node.labels) else 'unknown'
                })

            # Fetch all relationships
            relationships_result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m")
            links = []
            for record in relationships_result:
                start_node = record['n']
                end_node = record['m']
                relationship = record['r']
                links.append({
                    'source': start_node.element_id,
                    'target': end_node.element_id,
                    'type': relationship.type,
                    'strength': relationship.get('strength', 1.0) # Default strength if not present
                })

        return {
            'nodes': nodes,
            'links': links
        }


# Example usage
def main():
    # Initialize the system
    kg_system = AgentThinkingKG()

    try:
        # Clear existing data (optional - comment out to keep existing data)
        print("Clearing existing data...")
        kg_system.clear_database()

        # Example thinking process
        thinking_example = input()

        # Process the thinking
        session_id = kg_system.process_thinking(thinking_example, "weather_example_1")

        # Show session information
        sessions = kg_system.get_session_info()
        print(f"\nSessions in database: {len(sessions)}")
        for session_info in sessions:
            print(
                f"- {session_info['session_id']}: {session_info.get('strategy', 'unknown')} ({session_info.get('thought_count', 0)} thoughts)")

        # Analyze patterns (after processing multiple sessions)
        patterns = kg_system.analyze_patterns()
        print("\nReasoning Patterns Analysis:")
        print(json.dumps(patterns, indent=2))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close connections
        kg_system.close()


if __name__ == "__main__":
    main()