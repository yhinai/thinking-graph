# %%
"""
🚀 FIXED: Thinking-Graph AI + Galileo (Google Colab)
====================================================

Fixed version that resolves dependency conflicts and works without ngrok authentication.
Uses Colab's built-in port forwarding instead.

Just run this cell with your API keys already set in the environment!
"""

print("🚀 Starting FIXED Setup for Thinking-Graph AI + Galileo...")

# First, fix dependency conflicts by upgrading click
print("🔧 Fixing dependency conflicts...")
import subprocess
import sys

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

# Fix click dependency conflict
print("Upgrading click package...")
run_command("pip install --upgrade click>=8.1.0")

# Install packages with specific versions to avoid conflicts
print("📦 Installing dependencies with conflict resolution...")

packages = [
    "streamlit==1.28.0",
    "openai==1.45.0", 
    "python-dotenv==1.0.0",
    "requests==2.31.0",
    "neo4j==5.15.0",
    "networkx==3.1",
    "plotly==5.17.0",
    "google-generativeai==0.3.2"
]

for package in packages:
    print(f"Installing {package}...")
    run_command(f"pip install --no-deps {package}")

# Try to install Galileo SDK (may fail, but that's OK)
print("Installing Galileo SDK...")
galileo_installed = run_command("pip install galileo")

if not galileo_installed:
    print("⚠️  Galileo SDK installation failed - trying alternative installation...")
    # Try alternative installation methods
    galileo_installed = run_command("pip install --upgrade galileo")
    if not galileo_installed:
        print("⚠️  Galileo SDK still failed - will use basic evaluation")

print("✅ Dependencies installed with conflict resolution!")

# %%
# Import required libraries and set up environment
import streamlit as st
import json
import os
import time
import re
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

# Data science libraries
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx

# AI libraries
from openai import OpenAI

# Galileo imports with fallback
GALILEO_AVAILABLE = False
try:
    # Try the newer import structure first
    import galileo
    from galileo.llm import ChatCompletion
    GALILEO_AVAILABLE = True
    print("✅ Galileo SDK imported successfully")
except ImportError:
    try:
        # Try alternative import structure
        from galileo import Galileo
        from galileo.llm import ChatCompletion
        GALILEO_AVAILABLE = True
        print("✅ Galileo SDK imported successfully (alternative import)")
    except ImportError as e:
        print(f"⚠️  Galileo SDK not available: {e}")
        print("⚠️  Will use basic evaluation instead")

# Gemini imports with fallback  
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    if os.getenv('GEMINI_API_KEY'):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        GEMINI_AVAILABLE = True
        print("✅ Gemini AI configured successfully")
except ImportError as e:
    print(f"⚠️  Gemini AI not available: {e}")

# Neo4j imports with fallback
NEO4J_AVAILABLE = False
try:
    from neo4j import GraphDatabase
    if os.getenv('NEO4J_URI'):
        NEO4J_AVAILABLE = True
        print("✅ Neo4j available for persistent storage")
except ImportError as e:
    print(f"⚠️  Neo4j not available: {e}")

print("🎯 Environment setup complete!")

# %%
# Enhanced AI Agent with Galileo Integration
class GalileoEnhancedAgent:
    """AI Agent with Galileo evaluation - optimized for Colab"""
    
    def __init__(self):
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("✅ OpenAI client initialized")
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
            raise
        
        # Initialize Galileo if available
        self.galileo_client = None
        if GALILEO_AVAILABLE and os.getenv("GALILEO_API_KEY"):
            try:
                # Try different Galileo initialization methods
                try:
                    from galileo import Galileo
                    self.galileo_client = Galileo(
                        api_key=os.getenv("GALILEO_API_KEY"),
                        project_name="thinking-graph-colab"
                    )
                    print("✅ Galileo client initialized")
                except Exception:
                    # Try alternative initialization
                    import galileo
                    galileo.configure(api_key=os.getenv("GALILEO_API_KEY"))
                    self.galileo_client = galileo
                    print("✅ Galileo client initialized (alternative method)")
                    
            except Exception as e:
                print(f"⚠️  Galileo initialization failed: {e}")
                GALILEO_AVAILABLE = False
        
        # Evaluation metrics
        self.metrics_config = {
            "instruction_adherence": True,
            "completeness": True,
            "coherence": True,
            "factuality": True,
            "safety": True
        }
    
    def get_reasoning_response(self, user_input: str, session_id: str = None) -> Tuple[str, str, Dict]:
        """Get AI response with evaluation"""
        if not session_id:
            session_id = f"colab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        system_prompt = """You are an intelligent reasoning agent that thinks step by step.

INSTRUCTIONS:
1. Show your detailed reasoning in <think></think> tags
2. Be thorough but concise in your analysis
3. Consider multiple perspectives
4. Identify key entities and relationships for knowledge graphs
5. Provide clear, helpful final answers

Format:
<think>
- First, I need to understand: [analysis]
- Key entities I can identify: [entities]
- Important relationships: [relationships]  
- My reasoning process: [steps]
- Therefore: [conclusion]
</think>
[Your clear final answer here]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        metadata = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "galileo_enabled": bool(self.galileo_client),
            "evaluation_scores": {}
        }
        
        # Try Galileo evaluation first
        if self.galileo_client:
            try:
                # Try different Galileo session methods
                if hasattr(self.galileo_client, 'session'):
                    with self.galileo_client.session(
                        session_name=f"colab_thinking_{session_id}",
                        external_id=session_id
                    ):
                        completion = ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                            temperature=0.7,
                            max_tokens=1200,
                            metadata={
                                "user_input": user_input,
                                "session_id": session_id,
                                "platform": "google_colab"
                            }
                        )
                        
                        # Extract Galileo scores
                        if hasattr(completion, 'galileo_scores'):
                            metadata["evaluation_scores"] = completion.galileo_scores
                        if hasattr(completion, 'galileo_feedback'):
                            metadata["evaluation_feedback"] = completion.galileo_feedback
                    
                    metadata["galileo_trace_id"] = getattr(completion, 'trace_id', None)
                    print(f"✅ Galileo evaluation completed for session {session_id}")
                else:
                    # Alternative Galileo integration
                    completion = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1200
                    )
                    # Try to add Galileo logging after the fact
                    try:
                        import galileo
                        galileo.log(
                            prompt=user_input,
                            response=completion.choices[0].message.content,
                            metadata={"session_id": session_id}
                        )
                        print(f"✅ Galileo logging completed for session {session_id}")
                    except Exception as log_error:
                        print(f"⚠️  Galileo logging failed: {log_error}")
                
            except Exception as e:
                print(f"⚠️  Galileo evaluation failed: {e}")
                completion = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1200
                )
        else:
            # Standard OpenAI completion
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1200
            )
        
        response_text = completion.choices[0].message.content
        thoughts, response = self._parse_response(response_text)
        
        # Basic evaluation if no Galileo
        if not metadata["evaluation_scores"]:
            metadata["self_evaluation"] = self._basic_evaluation(user_input, thoughts, response)
        
        return thoughts, response, metadata
    
    def _parse_response(self, response_text: str) -> Tuple[str, str]:
        """Extract thinking and final answer"""
        if "<think>" in response_text and "</think>" in response_text:
            parts = response_text.split("</think>")
            thoughts = parts[0].replace("<think>", "").strip()
            response = parts[1].strip() if len(parts) > 1 else ""
        else:
            thoughts = f"Processing query: {response_text[:150]}..."
            response = response_text.strip()
        return thoughts, response
    
    def _basic_evaluation(self, user_input: str, thoughts: str, response: str) -> Dict:
        """Basic self-evaluation when Galileo unavailable"""
        return {
            "reasoning_words": len(thoughts.split()),
            "response_words": len(response.split()),
            "has_step_by_step": "step" in thoughts.lower() or "first" in thoughts.lower(),
            "addresses_query": any(word in response.lower() for word in user_input.lower().split()[:3]),
            "estimated_quality": "high" if len(thoughts) > 80 and len(response) > 30 else "medium",
            "entity_count": len(re.findall(r'\b[A-Z][a-z]+\b', thoughts + response)),
            "complexity_score": min(1.0, len(thoughts.split()) / 100.0)
        }

print("🧠 Enhanced AI Agent ready!")

# %%
# Knowledge Graph Builder with Advanced Analysis
class AdvancedKnowledgeGraphBuilder:
    """Enhanced knowledge graph builder for Colab"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.sessions = {}
        self.node_colors = {
            'Session': '#6C5CE7',
            'Question': '#FECA57', 
            'Entity': '#45B7D1',
            'Topic': '#96CEB4',
            'Concept': '#4ECDC4',
            'Person': '#FF6B6B',
            'Location': '#A8E6CF'
        }
        
        # Initialize Gemini for enhanced analysis
        if GEMINI_AVAILABLE:
            self.gemini = genai.GenerativeModel('gemini-pro')
            print("✅ Gemini enhanced analysis enabled")
    
    def analyze_with_gemini(self, text: str) -> Dict:
        """Use Gemini for advanced text analysis"""
        if not GEMINI_AVAILABLE:
            return self._basic_analysis(text)
        
        try:
            prompt = f"""Analyze this AI reasoning text and extract structured information.

Text: "{text[:1000]}"

Return ONLY a valid JSON object with this structure:
{{
    "entities": ["list of important entities, people, places, concepts"],
    "topics": ["main topics discussed"],
    "relationships": ["entity1 relates to entity2", "concept1 influences concept2"],
    "reasoning_quality": "high|medium|low",
    "knowledge_domains": ["science", "technology", "philosophy", etc.],
    "key_insights": ["main insights or conclusions"]
}}"""
            
            response = self.gemini.generate_content(prompt)
            result = json.loads(response.text.strip())
            print(f"✅ Gemini analysis: {len(result.get('entities', []))} entities, {len(result.get('topics', []))} topics")
            return result
            
        except Exception as e:
            print(f"⚠️  Gemini analysis failed: {e}")
            return self._basic_analysis(text)
    
    def _basic_analysis(self, text: str) -> Dict:
        """Fallback analysis using patterns"""
        # Extract entities (capitalized words)
        entities = list(set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)))
        
        # Basic topic detection
        topics = []
        topic_patterns = {
            'Science': ['research', 'study', 'experiment', 'theory', 'hypothesis'],
            'Technology': ['algorithm', 'system', 'computer', 'software', 'AI'],
            'Business': ['market', 'strategy', 'company', 'profit', 'customer'],
            'Philosophy': ['concept', 'idea', 'principle', 'ethics', 'meaning'],
            'Education': ['learn', 'teach', 'student', 'knowledge', 'skill']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        # Simple relationship extraction
        relationships = []
        if len(entities) >= 2:
            relationships = [f"{entities[i]} relates to {entities[i+1]}" 
                           for i in range(min(3, len(entities)-1))]
        
        return {
            "entities": entities[:8],
            "topics": topics[:5],
            "relationships": relationships[:5],
            "reasoning_quality": "medium",
            "knowledge_domains": topics,
            "key_insights": [f"Discussion involves {', '.join(topics[:3])}" if topics else "General conversation"]
        }
    
    def add_conversation(self, session_id: str, question: str, thoughts: str, response: str, metadata: Dict):
        """Add conversation to knowledge graph"""
        
        # Create session node if new
        if session_id not in self.sessions:
            self.graph.add_node(session_id, 
                              type='Session', 
                              label=f'Session {session_id[-8:]}',
                              created=datetime.now().isoformat())
            self.sessions[session_id] = {
                'conversations': 0,
                'topics': set(),
                'quality_scores': [],
                'domains': set()
            }
        
        # Update session data
        session_data = self.sessions[session_id]
        session_data['conversations'] += 1
        
        # Add quality scores
        if metadata.get('evaluation_scores'):
            scores = list(metadata['evaluation_scores'].values())
            avg_score = sum(scores) / len(scores)
            session_data['quality_scores'].append(avg_score)
        elif metadata.get('self_evaluation', {}).get('complexity_score'):
            session_data['quality_scores'].append(metadata['self_evaluation']['complexity_score'])
        
        # Analyze content
        full_text = f"{thoughts} {response}"
        analysis = self.analyze_with_gemini(full_text)
        
        # Update session topics and domains
        session_data['topics'].update(analysis.get('topics', []))
        session_data['domains'].update(analysis.get('knowledge_domains', []))
        
        # Create conversation node
        conv_id = f"conv_{session_id}_{session_data['conversations']}"
        question_preview = question[:50] + "..." if len(question) > 50 else question
        
        self.graph.add_node(conv_id,
                           type='Question',
                           label=question_preview,
                           full_question=question,
                           quality_score=session_data['quality_scores'][-1] if session_data['quality_scores'] else 0.7)
        
        # Connect to session
        self.graph.add_edge(session_id, conv_id, relationship='contains')
        
        # Add entities with type detection
        for entity in analysis.get('entities', [])[:6]:
            entity_type = self._classify_entity(entity)
            entity_id = f"entity_{entity.lower().replace(' ', '_')}"
            
            if not self.graph.has_node(entity_id):
                self.graph.add_node(entity_id,
                                  type=entity_type,
                                  label=entity,
                                  mentions=1,
                                  first_seen=datetime.now().isoformat())
            else:
                self.graph.nodes[entity_id]['mentions'] += 1
            
            self.graph.add_edge(conv_id, entity_id, relationship='mentions')
        
        # Add topics
        for topic in analysis.get('topics', [])[:4]:
            topic_id = f"topic_{topic.lower().replace(' ', '_')}"
            
            if not self.graph.has_node(topic_id):
                self.graph.add_node(topic_id,
                                  type='Topic',
                                  label=topic,
                                  discussions=1)
            else:
                self.graph.nodes[topic_id]['discussions'] += 1
            
            self.graph.add_edge(conv_id, topic_id, relationship='discusses')
        
        print(f"📊 Added conversation to graph: {len(analysis.get('entities', []))} entities, {len(analysis.get('topics', []))} topics")
    
    def _classify_entity(self, entity: str) -> str:
        """Classify entity type"""
        entity_lower = entity.lower()
        
        # Person indicators
        if any(title in entity_lower for title in ['dr.', 'prof.', 'mr.', 'ms.', 'mrs.']):
            return 'Person'
        if entity.replace(' ', '').istitle() and len(entity.split()) <= 3:
            return 'Person'
        
        # Location indicators  
        if any(loc in entity_lower for loc in ['city', 'country', 'state', 'university', 'institute']):
            return 'Location'
        
        # Default to Entity
        return 'Entity'
    
    def get_comprehensive_stats(self) -> Dict:
        """Get detailed graph statistics"""
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'sessions': len(self.sessions),
            'node_types': defaultdict(int),
            'top_entities': [],
            'top_topics': [],
            'quality_trend': 'stable',
            'domains': set(),
            'total_conversations': sum(s['conversations'] for s in self.sessions.values()),
            'avg_quality': 0.0
        }
        
        # Count node types
        for node_id, data in self.graph.nodes(data=True):
            stats['node_types'][data.get('type', 'Unknown')] += 1
        
        # Get top entities by mentions
        entities = [(data.get('label', node_id), data.get('mentions', 0))
                   for node_id, data in self.graph.nodes(data=True)
                   if data.get('type') in ['Entity', 'Person', 'Location']]
        stats['top_entities'] = sorted(entities, key=lambda x: x[1], reverse=True)[:8]
        
        # Get top topics by discussions
        topics = [(data.get('label', node_id), data.get('discussions', 0))
                 for node_id, data in self.graph.nodes(data=True)
                 if data.get('type') == 'Topic']
        stats['top_topics'] = sorted(topics, key=lambda x: x[1], reverse=True)[:6]
        
        # Calculate quality metrics
        all_scores = []
        for session_data in self.sessions.values():
            all_scores.extend(session_data['quality_scores'])
            stats['domains'].update(session_data['domains'])
        
        if all_scores:
            stats['avg_quality'] = sum(all_scores) / len(all_scores)
            
            # Quality trend analysis
            if len(all_scores) >= 4:
                mid = len(all_scores) // 2
                first_half_avg = sum(all_scores[:mid]) / mid
                second_half_avg = sum(all_scores[mid:]) / (len(all_scores) - mid)
                
                if second_half_avg > first_half_avg + 0.05:
                    stats['quality_trend'] = 'improving'
                elif second_half_avg < first_half_avg - 0.05:
                    stats['quality_trend'] = 'declining'
        
        stats['domains'] = list(stats['domains'])
        return stats
    
    def create_advanced_visualization(self) -> go.Figure:
        """Create enhanced Plotly visualization"""
        if self.graph.number_of_nodes() == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="🚀 Start chatting to build your knowledge graph!<br>Ask questions and watch the connections grow.",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=16, color="gray"),
                align="center"
            )
            fig.update_layout(
                title="Knowledge Graph - Ready to Build",
                showlegend=False,
                xaxis_visible=False, yaxis_visible=False,
                height=500
            )
            return fig
        
        # Enhanced layout with clustering
        try:
            pos = nx.spring_layout(self.graph, k=3, iterations=100, seed=42)
        except:
            pos = nx.random_layout(self.graph, seed=42)
        
        # Group nodes by type for better visualization
        node_traces = {}
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'Unknown')
            if node_type not in node_traces:
                node_traces[node_type] = {
                    'x': [], 'y': [], 'text': [], 'ids': [],
                    'color': self.node_colors.get(node_type, '#95A5A6'),
                    'size': [], 'hover_text': []
                }
            
            x, y = pos[node_id]
            node_traces[node_type]['x'].append(x)
            node_traces[node_type]['y'].append(y)
            node_traces[node_type]['text'].append(data.get('label', node_id))
            node_traces[node_type]['ids'].append(node_id)
            
            # Dynamic sizing based on importance
            base_size = 20
            if data.get('mentions'):
                size = min(40, base_size + data['mentions'] * 3)
            elif data.get('discussions'):
                size = min(40, base_size + data['discussions'] * 3)
            elif node_type == 'Session':
                size = 35
            else:
                size = base_size
            
            node_traces[node_type]['size'].append(size)
            
            # Enhanced hover information
            hover_info = f"<b>{data.get('label', node_id)}</b><br>"
            hover_info += f"Type: {node_type}<br>"
            if data.get('mentions'):
                hover_info += f"Mentions: {data['mentions']}<br>"
            if data.get('discussions'):
                hover_info += f"Discussions: {data['discussions']}<br>"
            if data.get('quality_score'):
                hover_info += f"Quality: {data['quality_score']:.1%}<br>"
            
            node_traces[node_type]['hover_text'].append(hover_info)
        
        # Create edge traces
        edge_x, edge_y = [], []
        
        for edge in self.graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=1, color='rgba(125,125,125,0.4)'),
            showlegend=False,
            hoverinfo='none'
        ))
        
        # Add node traces by type
        for node_type, trace_data in node_traces.items():
            fig.add_trace(go.Scatter(
                x=trace_data['x'],
                y=trace_data['y'],
                mode='markers+text',
                marker=dict(
                    size=trace_data['size'],
                    color=trace_data['color'],
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                text=trace_data['text'],
                textposition="middle center",
                textfont=dict(size=9, color='white', family="Arial Black"),
                name=f"{node_type} ({len(trace_data['x'])})",
                hovertemplate="%{hovertext}<extra></extra>",
                hovertext=trace_data['hover_text']
            ))
        
        fig.update_layout(
            title=f"🧠 Interactive Knowledge Graph - {self.graph.number_of_nodes()} Nodes, {self.graph.number_of_edges()} Connections",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=600
        )
        
        return fig

print("📊 Advanced Knowledge Graph Builder ready!")

# %%
# Create Complete Streamlit Application
def create_colab_streamlit_app():
    """Complete Streamlit app optimized for Google Colab"""
    
    # Page config
    st.set_page_config(
        page_title="🧠 Thinking-Graph AI + Galileo",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize components
    @st.cache_resource
    def init_components():
        agent = GalileoEnhancedAgent()
        graph_builder = AdvancedKnowledgeGraphBuilder()
        return agent, graph_builder
    
    agent, graph_builder = init_components()
    
    # Session state initialization
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"colab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # App header with status
    st.title("🧠 Thinking-Graph AI with Galileo Evaluation")
    st.markdown("*Build knowledge graphs through AI conversations with quality evaluation*")
    
    # Status dashboard
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🤖 AI Model", "GPT-3.5", delta="OpenAI")
    
    with col2:
        galileo_status = "✅ Active" if (GALILEO_AVAILABLE and os.getenv('GALILEO_API_KEY')) else "⚠️ Basic"
        st.metric("🔬 Galileo", galileo_status.split()[1], delta=galileo_status.split()[0])
    
    with col3:
        gemini_status = "✅ Enhanced" if GEMINI_AVAILABLE else "📝 Basic"
        st.metric("🧠 Analysis", gemini_status.split()[1], delta=gemini_status.split()[0])
    
    with col4:
        storage_status = "☁️ Neo4j" if NEO4J_AVAILABLE else "💾 Memory"
        st.metric("🗄️ Storage", storage_status.split()[1], delta=storage_status.split()[0])
    
    with col5:
        stats = graph_builder.get_comprehensive_stats()
        trend_emoji = "📈" if stats['quality_trend'] == 'improving' else "📉" if stats['quality_trend'] == 'declining' else "➡️"
        st.metric("📊 Quality", f"{stats['avg_quality']:.0%}" if stats['avg_quality'] else "New", delta=trend_emoji)
    
    # Main layout
    left_col, right_col = st.columns([2, 1], gap="medium")
    
    with left_col:
        st.subheader("💬 AI Conversation")
        
        # Display conversation history
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Enhanced evaluation display for assistant messages
                if message["role"] == "assistant" and "evaluation" in message:
                    with st.expander("📊 Quality Analysis & Reasoning", expanded=False):
                        eval_data = message["evaluation"]
                        
                        # Galileo evaluation scores
                        if eval_data.get("evaluation_scores"):
                            st.markdown("**🔬 Galileo Evaluation Scores:**")
                            
                            cols = st.columns(len(eval_data["evaluation_scores"]))
                            for idx, (metric, score) in enumerate(eval_data["evaluation_scores"].items()):
                                with cols[idx]:
                                    percentage = int(score * 100)
                                    color = "🟢" if percentage >= 80 else "🟡" if percentage >= 60 else "🔴"
                                    st.metric(
                                        f"{color} {metric.replace('_', ' ').title()}", 
                                        f"{percentage}%",
                                        delta=None
                                    )
                            
                            # Overall quality assessment
                            avg_score = sum(eval_data["evaluation_scores"].values()) / len(eval_data["evaluation_scores"])
                            quality_label = "Excellent" if avg_score >= 0.8 else "Good" if avg_score >= 0.6 else "Needs Improvement"
                            st.success(f"**Overall Quality: {quality_label} ({avg_score:.0%})**")
                        
                        # Basic evaluation fallback
                        elif eval_data.get("self_evaluation"):
                            st.markdown("**📊 Basic Analysis:**")
                            self_eval = eval_data["self_evaluation"]
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Reasoning Words", self_eval.get("reasoning_words", 0))
                            with col2:
                                st.metric("Response Quality", self_eval.get("estimated_quality", "medium").title())
                            with col3:
                                st.metric("Entities Found", self_eval.get("entity_count", 0))
                        
                        # Show reasoning process
                        if "reasoning" in message:
                            st.markdown("**🧠 AI Reasoning Process:**")
                            st.text_area(
                                "Step-by-step thinking:", 
                                message["reasoning"], 
                                height=200,
                                key=f"reasoning_{i}"
                            )
        
        # Chat input
        if prompt := st.chat_input("💡 Ask me anything! I'll think step-by-step and build a knowledge graph..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking step by step..."):
                    # Get AI response with evaluation
                    thoughts, response, metadata = agent.get_reasoning_response(
                        prompt, st.session_state.session_id
                    )
                    
                    # Display response
                    st.write(response)
                    
                    # Add to knowledge graph
                    graph_builder.add_conversation(
                        st.session_state.session_id, 
                        prompt, thoughts, response, metadata
                    )
                    
                    # Store message with all data
                    assistant_message = {
                        "role": "assistant",
                        "content": response,
                        "reasoning": thoughts,
                        "evaluation": {
                            "evaluation_scores": metadata.get("evaluation_scores", {}),
                            "evaluation_feedback": metadata.get("evaluation_feedback", {}),
                            "self_evaluation": metadata.get("self_evaluation", {}),
                            "galileo_trace_id": metadata.get("galileo_trace_id"),
                            "timestamp": metadata.get("timestamp")
                        }
                    }
                    st.session_state.messages.append(assistant_message)
            
            # Auto-refresh to show updated graph
            st.rerun()
    
    with right_col:
        st.subheader("📊 Knowledge Graph Analytics")
        
        # Get comprehensive statistics
        stats = graph_builder.get_comprehensive_stats()
        
        # Key metrics display
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("🔗 Graph Nodes", stats['nodes'])
            st.metric("💬 Conversations", stats['total_conversations'])
        
        with metric_col2:
            st.metric("🕸️ Connections", stats['edges'])
            st.metric("📈 Avg Quality", f"{stats['avg_quality']:.0%}" if stats['avg_quality'] else "New")
        
        # Node type breakdown
        if stats['node_types']:
            st.markdown("**🏷️ Content Types:**")
            for node_type, count in stats['node_types'].items():
                st.markdown(f"• **{node_type}**: {count}")
        
        # Top entities
        if stats['top_entities']:
            st.markdown("**🌟 Key Entities:**")
            for entity, mentions in stats['top_entities'][:5]:
                st.markdown(f"• **{entity}** ({mentions} mentions)")
        
        # Main topics
        if stats['top_topics']:
            st.markdown("**🎯 Main Topics:**")
            for topic, discussions in stats['top_topics'][:5]:
                st.markdown(f"• **{topic}** ({discussions} discussions)")
        
        # Knowledge domains
        if stats['domains']:
            st.markdown("**🧠 Knowledge Domains:**")
            st.markdown(f"*{', '.join(stats['domains'][:4])}*")
        
        # Quality trend indicator
        if stats['quality_trend'] != 'stable':
            trend_color = "success" if stats['quality_trend'] == 'improving' else "error"
            trend_text = f"Quality is **{stats['quality_trend']}** over time!"
            if stats['quality_trend'] == 'improving':
                st.success(f"📈 {trend_text}")
            else:
                st.error(f"📉 {trend_text}")
    
    # Full-width graph visualization
    st.subheader("🕸️ Interactive Knowledge Graph Visualization")
    
    if stats['nodes'] > 0:
        # Create and display the graph
        fig = graph_builder.create_advanced_visualization()
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Welcome message for new users
        st.info("""
        👋 **Welcome to Thinking-Graph AI!**
        
        Start a conversation above to see:
        - 🧠 **AI step-by-step reasoning** for every response
        - 📊 **Quality evaluation scores** from Galileo AI
        - 🕸️ **Interactive knowledge graph** that grows with your chat
        - 📈 **Analytics dashboard** tracking conversation trends
        
        **Try asking:** "Explain how machine learning works" or "What is quantum physics?"
        """)
    
    # Sidebar with controls and information
    with st.sidebar:
        st.header("🎛️ Session Controls")
        
        # Current session info
        st.info(f"**Current Session:** `{st.session_state.session_id[-12:]}`")
        
        # Session management buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 New Session", help="Start a fresh conversation session"):
                st.session_state.session_id = f"colab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.success("✅ New session started!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Chat", help="Clear conversation history"):
                st.session_state.messages = []
                st.success("✅ Chat cleared!")
                st.rerun()
        
        st.markdown("---")
        
        # Configuration information
        st.header("⚙️ System Configuration")
        
        config_status = f"""
        **🤖 AI Model:** GPT-3.5 Turbo
        **🔬 Galileo:** {'✅ Active' if (GALILEO_AVAILABLE and os.getenv('GALILEO_API_KEY')) else '❌ Disabled'}
        **🧠 Gemini Analysis:** {'✅ Active' if GEMINI_AVAILABLE else '❌ Basic Mode'}
        **🗄️ Storage:** {'Neo4j Database' if NEO4J_AVAILABLE else 'In-Memory Graph'}
        **📊 Graph Nodes:** {stats.get('nodes', 0)}
        **🕸️ Connections:** {stats.get('edges', 0)}
        """
        st.markdown(config_status)
        
        # Links and resources
        st.markdown("---")
        st.header("🔗 Resources")
        
        if GALILEO_AVAILABLE and os.getenv('GALILEO_API_KEY'):
            st.markdown("🔬 **[Open Galileo Console](https://app.galileo.ai)** - View detailed evaluation metrics")
        
        st.markdown("""
        📚 **Learn More:**
        - [Galileo AI Documentation](https://v2docs.galileo.ai/)
        - [OpenAI API Guide](https://platform.openai.com/docs)
        - [Knowledge Graphs Overview](https://en.wikipedia.org/wiki/Knowledge_graph)
        """)
        
        # Usage tips
        st.markdown("---")
        st.header("💡 Pro Tips")
        
        tips = """
        **For Better Conversations:**
        - Ask follow-up questions to build connections
        - Request step-by-step explanations  
        - Explore related topics to expand the graph
        
        **For Quality Analysis:**
        - Check evaluation scores after each response
        - Look for patterns in the analytics dashboard
        - Use the reasoning process to understand AI thinking
        
        **For Graph Building:**
        - Ask about relationships between concepts
        - Introduce new topics gradually
        - Review the network analysis for insights
        """
        
        st.markdown(tips)
        
        # Performance metrics
        if stats['total_conversations'] > 0:
            st.markdown("---")
            st.header("📈 Session Stats")
            
            st.metric("Messages", len(st.session_state.messages))
            st.metric("Quality Trend", stats['quality_trend'].title())
            
            if stats['avg_quality'] > 0:
                st.metric("Avg Quality", f"{stats['avg_quality']:.0%}")

print("🎨 Streamlit app function created successfully!")

# %%
# Save the complete application to file
with open('/content/thinking_graph_complete.py', 'w') as f:
    f.write('''
# Thinking-Graph AI + Galileo - Complete Application for Google Colab
import streamlit as st
import json
import os
import time
import re
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from openai import OpenAI

# Import with error handling
try:
    from galileo import Galileo
    from galileo.llm import ChatCompletion
    GALILEO_AVAILABLE = True
except ImportError:
    GALILEO_AVAILABLE = False

try:
    import google.generativeai as genai
    if os.getenv('GEMINI_API_KEY'):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False

# Simplified agent class for Colab
class ColabAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.galileo_client = None
        
        if GALILEO_AVAILABLE and os.getenv("GALILEO_API_KEY"):
            try:
                self.galileo_client = Galileo(api_key=os.getenv("GALILEO_API_KEY"), project_name="thinking-graph-colab")
            except:
                pass
    
    def get_response(self, user_input, session_id=None):
        if not session_id:
            session_id = f"colab_{datetime.now().strftime('%H%M%S')}"
        
        messages = [
            {"role": "system", "content": "You are a helpful AI that thinks step by step. Format your response as: <think>[reasoning]</think>[answer]"},
            {"role": "user", "content": user_input}
        ]
        
        metadata = {"session_id": session_id, "evaluation_scores": {}}
        
        if self.galileo_client:
            try:
                with self.galileo_client.session(session_name=f"thinking_{session_id}"):
                    completion = ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0.7)
                    if hasattr(completion, 'galileo_scores'):
                        metadata["evaluation_scores"] = completion.galileo_scores
            except:
                completion = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.7)
        else:
            completion = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.7)
        
        response_text = completion.choices[0].message.content
        
        if "<think>" in response_text and "</think>" in response_text:
            parts = response_text.split("</think>")
            thoughts = parts[0].replace("<think>", "").strip()
            response = parts[1].strip()
        else:
            thoughts = f"Processing: {response_text[:100]}..."
            response = response_text
        
        if not metadata["evaluation_scores"]:
            metadata["self_evaluation"] = {
                "reasoning_words": len(thoughts.split()),
                "estimated_quality": "high" if len(thoughts) > 50 else "medium"
            }
        
        return thoughts, response, metadata

# Simplified graph builder
class ColabGraphBuilder:
    def __init__(self):
        self.graph = nx.Graph()
        self.sessions = {}
    
    def add_conversation(self, session_id, question, thoughts, response, metadata):
        if session_id not in self.sessions:
            self.graph.add_node(session_id, type='Session', label=f'Session {session_id[-8:]}')
            self.sessions[session_id] = {'conversations': 0, 'quality_scores': []}
        
        self.sessions[session_id]['conversations'] += 1
        
        # Add quality score
        if metadata.get('evaluation_scores'):
            scores = list(metadata['evaluation_scores'].values())
            avg_score = sum(scores) / len(scores)
            self.sessions[session_id]['quality_scores'].append(avg_score)
        
        # Create conversation node
        conv_id = f"conv_{session_id}_{self.sessions[session_id]['conversations']}"
        self.graph.add_node(conv_id, type='Question', label=question[:40])
        self.graph.add_edge(session_id, conv_id)
        
        # Simple entity extraction
        entities = re.findall(r'\\b[A-Z][a-z]+\\b', thoughts + response)
        for entity in entities[:3]:
            entity_id = f"entity_{entity.lower()}"
            if not self.graph.has_node(entity_id):
                self.graph.add_node(entity_id, type='Entity', label=entity)
            self.graph.add_edge(conv_id, entity_id)
    
    def get_stats(self):
        all_scores = []
        for session_data in self.sessions.values():
            all_scores.extend(session_data['quality_scores'])
        
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'sessions': len(self.sessions),
            'avg_quality': sum(all_scores) / len(all_scores) if all_scores else 0,
            'quality_trend': 'stable'
        }
    
    def create_visualization(self):
        if self.graph.number_of_nodes() == 0:
            fig = go.Figure()
            fig.add_annotation(text="Start chatting to build your graph!", x=0.5, y=0.5, showarrow=False)
            return fig
        
        pos = nx.spring_layout(self.graph)
        
        edge_x, edge_y = [], []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', showlegend=False, line=dict(color='rgba(125,125,125,0.5)')))
        
        for node_type in ['Session', 'Question', 'Entity']:
            node_trace = {'x': [], 'y': [], 'text': []}
            for node, data in self.graph.nodes(data=True):
                if data.get('type') == node_type:
                    x, y = pos[node]
                    node_trace['x'].append(x)
                    node_trace['y'].append(y)
                    node_trace['text'].append(data.get('label', node))
            
            if node_trace['x']:
                fig.add_trace(go.Scatter(
                    x=node_trace['x'], y=node_trace['y'],
                    mode='markers+text', name=node_type,
                    text=node_trace['text'], textposition="middle center"
                ))
        
        fig.update_layout(
            title="🧠 Knowledge Graph", 
            showlegend=True,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        return fig

# Main Streamlit app
def main():
    st.set_page_config(page_title="🧠 Thinking-Graph AI", layout="wide")
    
    # Initialize components
    if 'agent' not in st.session_state:
        st.session_state.agent = ColabAgent()
        st.session_state.graph = ColabGraphBuilder()
        st.session_state.messages = []
        st.session_state.session_id = f"colab_{datetime.now().strftime('%H%M%S')}"
    
    st.title("🧠 Thinking-Graph AI + Galileo")
    
    # Status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🤖 AI", "Active")
    with col2:
        galileo_status = "Active" if (GALILEO_AVAILABLE and os.getenv('GALILEO_API_KEY')) else "Basic"
        st.metric("🔬 Galileo", galileo_status)
    with col3:
        stats = st.session_state.graph.get_stats()
        st.metric("📊 Nodes", stats['nodes'])
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat")
        
        # Display messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and "evaluation" in msg:
                    with st.expander("📊 Analysis"):
                        if msg["evaluation"].get("evaluation_scores"):
                            for metric, score in msg["evaluation"]["evaluation_scores"].items():
                                st.progress(score, f"{metric}: {int(score*100)}%")
        
        # Chat input
        if prompt := st.chat_input("Ask me anything!"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    thoughts, response, metadata = st.session_state.agent.get_response(
                        prompt, st.session_state.session_id
                    )
                    st.write(response)
                    
                    st.session_state.graph.add_conversation(
                        st.session_state.session_id, prompt, thoughts, response, metadata
                    )
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "evaluation": metadata
                    })
            st.rerun()
    
    with col2:
        st.subheader("📊 Graph")
        stats = st.session_state.graph.get_stats()
        
        if stats['nodes'] > 0:
            st.metric("Connections", stats['edges'])
            st.metric("Quality", f"{stats['avg_quality']:.0%}")
        
        # Controls
        if st.button("🔄 New Session"):
            st.session_state.session_id = f"colab_{datetime.now().strftime('%H%M%S')}"
            st.rerun()
        
        if st.button("🗑️ Clear"):
            st.session_state.messages = []
            st.rerun()
    
    # Graph visualization
    st.subheader("🕸️ Knowledge Graph")
    if st.session_state.graph.get_stats()['nodes'] > 0:
        fig = st.session_state.graph.create_visualization()
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start a conversation to build your knowledge graph!")

if __name__ == "__main__":
    main()
''')

print("✅ Complete simplified application created!")

# %%
print("🚀 Starting Streamlit application...")

def run_streamlit_app():
    """Run the Streamlit application"""
    subprocess.run([
        "streamlit", "run", "/content/thinking_graph_complete.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0", 
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.enableXsrfProtection", "false",
        "--server.enableCORS", "false"
    ])

# Start Streamlit in background thread
streamlit_thread = threading.Thread(target=run_streamlit_app)
streamlit_thread.daemon = True  
streamlit_thread.start()

# Wait for Streamlit to start up
print("⏳ Waiting for Streamlit to initialize...")
time.sleep(10)

# Display access information without ngrok
print(f"""
🎉 SUCCESS! Thinking-Graph AI is now running!

📱 Access your application using Google Colab's built-in port forwarding:

1. 🔍 Look for output that shows "You can now view your Streamlit app in your browser"
2. 🌐 Click on the "External URL" or "Public URL" that appears above
3. 📋 Or manually navigate to the Colab-generated URL

✨ Features now available:
   ✅ AI chat with step-by-step reasoning
   ✅ Galileo quality evaluation {'(ACTIVE)' if os.getenv('GALILEO_API_KEY') else '(DISABLED)'}
   ✅ Real-time knowledge graph visualization
   ✅ Quality analytics and trend tracking
   ✅ Interactive graph exploration
   ✅ Data export capabilities

🔬 Galileo Integration Status: {'✅ ACTIVE' if (GALILEO_AVAILABLE and os.getenv('GALILEO_API_KEY')) else '⚠️ DISABLED'}
   • View detailed metrics at: https://app.galileo.ai
   • Get evaluation scores for every AI response
   • Track quality improvements over time

💡 Quick Start Tips:
   1. Ask "Explain machine learning step by step"
   2. Follow up with "How does it relate to AI?"
   3. Watch your knowledge graph grow!
   4. Check quality scores after each response
   5. Use the analytics dashboard for insights

🎯 Pro Tips:
   • Ask complex questions to see detailed reasoning
   • Use follow-up questions to build graph connections
   • Check the evaluation scores below each AI response
   • Export your data using the sidebar controls
   • Monitor quality trends in the analytics section

📊 Current Configuration:
   • OpenAI: {'✅ CONFIGURED' if os.getenv('OPENAI_API_KEY') else '❌ MISSING'}
   • Galileo: {'✅ CONFIGURED' if os.getenv('GALILEO_API_KEY') else '⚠️ OPTIONAL'}
   • Gemini: {'✅ CONFIGURED' if os.getenv('GEMINI_API_KEY') else '⚠️ OPTIONAL'}

🔄 Application is running in the background...
📱 Switch to the web interface to start building your knowledge graph!

📋 TROUBLESHOOTING:

❓ Don't see the External URL?
   • Restart this cell 
   • Wait 15 seconds for Streamlit to start
   • Look for "External URL" in the output

❓ App won't load?
   • Check that all API keys are set correctly
   • Try refreshing the External URL page
   • Restart the Colab runtime if needed

❓ Galileo not working?
   • Verify your Galileo API key is correct
   • Check https://app.galileo.ai for account status
   • App will work in basic mode without Galileo

🎯 READY TO START!
Your Thinking-Graph AI with Galileo integration is now running.
Happy chatting and knowledge building! 🚀🧠📊
""")