#!/usr/bin/env python3
"""
Minimal Thinking Graph Application
- Simple Flask server with Neo4j
- Core chat and knowledge extraction only
- No authentication, caching, or collaboration features
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from neo4j import GraphDatabase
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='minimal_static', static_url_path='')
CORS(app)

# Neo4j connection
class SimpleKnowledgeGraph:
    def __init__(self):
        self.driver = None
        self.connect()
    
    def connect(self):
        """Connect to Neo4j database"""
        try:
            uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
            user = os.getenv('NEO4J_USER', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', 'password')
            
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Connected to Neo4j")
            
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def add_thought(self, content: str, session_id: str = None):
        """Add a thought and extract entities"""
        if not self.driver:
            return {"error": "Database not connected"}
        
        session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            with self.driver.session() as session:
                # Create thought node
                result = session.run("""
                    MERGE (s:Session {id: $session_id})
                    CREATE (t:Thought {
                        content: $content,
                        timestamp: datetime(),
                        id: randomUUID()
                    })
                    CREATE (s)-[:CONTAINS]->(t)
                    RETURN t.id as thought_id
                """, content=content, session_id=session_id)
                
                thought_id = result.single()['thought_id']
                
                # Simple entity extraction
                entities = self.extract_simple_entities(content)
                
                # Add entities and relationships
                for entity in entities:
                    session.run("""
                        MATCH (t:Thought {id: $thought_id})
                        MERGE (e:Entity {name: $entity})
                        MERGE (t)-[:MENTIONS]->(e)
                    """, thought_id=thought_id, entity=entity)
                
                return {
                    "thought_id": thought_id,
                    "session_id": session_id,
                    "entities": entities
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def extract_simple_entities(self, text: str):
        """Simple entity extraction using patterns"""
        entities = set()
        
        # Capitalize words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.update(capitalized)
        
        # Technical terms (words with specific patterns)
        tech_terms = re.findall(r'\b(?:API|SDK|AI|ML|database|server|client|framework|library)\b', text, re.IGNORECASE)
        entities.update(tech_terms)
        
        # Simple noun phrases (adjective + noun)
        noun_phrases = re.findall(r'\b(?:machine learning|artificial intelligence|neural network|data science|web development)\b', text, re.IGNORECASE)
        entities.update(noun_phrases)
        
        return list(entities)[:10]  # Limit to 10 entities
    
    def get_graph_data(self):
        """Get simple graph data for visualization"""
        if not self.driver:
            return {"nodes": [], "links": []}
        
        try:
            with self.driver.session() as session:
                # Get nodes
                nodes_result = session.run("""
                    MATCH (n)
                    RETURN n.name as name, n.content as content, 
                           labels(n)[0] as type, elementId(n) as id
                    LIMIT 100
                """)
                
                nodes = []
                for record in nodes_result:
                    nodes.append({
                        "id": record["id"],
                        "name": record["name"] or record["content"][:50] if record["content"] else "Unknown",
                        "type": record["type"],
                        "size": 1
                    })
                
                # Get relationships
                links_result = session.run("""
                    MATCH (a)-[r]->(b)
                    RETURN elementId(a) as source, elementId(b) as target,
                           type(r) as type
                    LIMIT 200
                """)
                
                links = []
                for record in links_result:
                    links.append({
                        "source": record["source"],
                        "target": record["target"],
                        "type": record["type"]
                    })
                
                return {"nodes": nodes, "links": links}
                
        except Exception as e:
            print(f"Error getting graph data: {e}")
            return {"nodes": [], "links": []}

# Initialize knowledge graph
kg = SimpleKnowledgeGraph()

# Simple AI integration (using existing Galileo service if available)
def get_ai_response(user_input: str):
    """Get AI response - simplified version"""
    try:
        # Try to use Galileo if available
        from services.galileo_service import get_galileo_service
        galileo_service = get_galileo_service()
        if galileo_service:
            thoughts, response, metadata = galileo_service.get_reasoning_response_with_evaluation(user_input)
            return response
    except ImportError:
        pass
    
    # Fallback response
    return f"I understand you're thinking about: {user_input}. Let me help you explore this further."

# API Routes
@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "database": "connected" if kg.driver else "disconnected",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Simple chat endpoint"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        session_id = data.get('session_id')
        
        if not user_input.strip():
            return jsonify({"error": "Empty message"}), 400
        
        # Get AI response
        ai_response = get_ai_response(user_input)
        
        # Add to knowledge graph
        kg_result = kg.add_thought(user_input, session_id)
        kg.add_thought(ai_response, session_id)
        
        return jsonify({
            "response": ai_response,
            "session_id": kg_result.get("session_id"),
            "entities_extracted": kg_result.get("entities", [])
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph')
def get_graph():
    """Get graph data"""
    try:
        graph_data = kg.get_graph_data()
        return jsonify(graph_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_graph():
    """Clear all graph data"""
    try:
        if kg.driver:
            with kg.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Minimal Thinking Graph")
    print(f"📊 Database: {'Connected' if kg.driver else 'Disconnected'}")
    print("🌐 Open http://localhost:8080")
    
    app.run(host='0.0.0.0', port=8080, debug=True)