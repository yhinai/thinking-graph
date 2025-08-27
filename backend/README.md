# Thinking-graph Backend

## Overview

The Thinking-graph backend is a Flask-based API server that processes thinking text and builds a knowledge graph using Neo4j. It integrates with Google's Gemini AI for natural language processing and provides REST endpoints for the frontend to interact with the knowledge graph data.

## Features

- **Knowledge Graph Builder**: Converts agent thinking text into structured knowledge graphs
- **Neo4j Integration**: Stores and manages graph data with nodes and relationships
- **Gemini AI Analysis**: Uses Google's Gemini model for advanced text analysis
- **REST API**: Provides endpoints for frontend integration
- **Real-time Processing**: Processes chat messages and updates the knowledge graph in real-time

## Prerequisites

- Python 3.8+
- Neo4j AuraDB or local Neo4j Database
- Google Gemini API Key
- OpenAI API Key (for DeepSeek reasoning)

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file with:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   NEO4J_URI=neo4j+s://your-auradb-instance.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_auradb_password
   
   # For local Neo4j (alternative to AuraDB):
   # NEO4J_URI=bolt://localhost:7687
   # NEO4J_USER=neo4j
   # NEO4J_PASSWORD=your_local_password
   ```

3. **Database Setup**:
   
   **Option A: Neo4j AuraDB (Recommended)**
   - Create a free AuraDB instance at https://neo4j.com/cloud/aura/
   - Use the `neo4j+s://` URI format in your `.env` file
   - No local installation required
   
   **Option B: Local Neo4j**
   - Install Neo4j Desktop or use Docker
   - Create a new database with authentication
   - Use `bolt://localhost:7687` format in `.env`

4. **Run the Server**:
   ```bash
   python app.py
   ```

## API Endpoints

### Health Check
- `GET /health` - Check server health and system status

### Thinking Processing
- `POST /api/process-thinking` - Process thinking text and update knowledge graph
  ```json
  {
    "thinking_text": "Your thinking process text here",
    "session_id": "optional_session_id"
  }
  ```

### Graph Data
- `GET /api/graph-data` - Get formatted graph data for 3D visualization
- `GET /api/sessions` - Get all sessions
- `GET /api/session/<session_id>` - Get specific session details
- `GET /api/patterns` - Get reasoning patterns analysis

### Database Management
- `DELETE /api/clear-database` - Clear all graph data (use with caution)

## Knowledge Graph Structure

### Node Types
- **Session**: Represents a thinking session
- **Thought**: Individual thoughts within a session
- **Entity**: Extracted entities (functions, parameters, concepts)
- **Tool**: Tools and APIs mentioned

### Relationship Types
- **CONTAINS**: Session contains thoughts
- **MENTIONS**: Thought mentions entity
- **USES_TOOL**: Thought uses tool
- **REASONING_FLOW**: Logical flow between thoughts

## Usage with Frontend

The backend is designed to work with the Thinking-graph chatbot frontend. When users send messages through the chat interface:

1. Message is sent to `/api/process-thinking`
2. Gemini AI analyzes the text structure
3. Knowledge graph is updated with new nodes and relationships
4. Frontend fetches updated graph data from `/api/graph-data`
5. 3D visualization is updated with new information

## Error Handling

The API includes comprehensive error handling:
- Invalid requests return appropriate HTTP status codes
- Database connection issues are logged and reported
- Gemini API failures fall back to regex-based processing

## Development

To extend the functionality:
1. Add new analysis patterns in `kgbuilder.py`
2. Extend API endpoints in `app.py`
3. Update the graph schema as needed
4. Test with various thinking text formats

## Troubleshooting

- **Neo4j Connection Issues**: Check database is running and credentials are correct
- **Gemini API Errors**: Verify API key and quota
- **CORS Issues**: Ensure Flask-CORS is properly configured for your frontend domain