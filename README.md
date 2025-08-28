# Thinking Graph - AI Knowledge Visualization

Interactive 3D knowledge graph application that visualizes AI conversations and reasoning patterns in real-time.

## ✨ Features

- **AI Chat Interface**: Natural conversations with AI models
- **3D Knowledge Graph**: Real-time visualization with Three.js
- **Neo4j Integration**: Persistent graph storage  
- **Knowledge Discovery**: Extract entities and relationships from conversations
- **Galileo AI Integration**: Optional AI evaluation and monitoring


## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API Key
- Neo4j Database (optional - for persistence)

### Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd thinking-graph
   ./setup.sh
   ```

2. **Configure API keys:**
   Edit `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   NEO4J_URI=your_neo4j_uri (optional)
   GALILEO_API_KEY=your_galileo_key (optional)
   ```

3. **Start application:**
   ```bash
   ./start.sh
   ```

4. **Access:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

### Manual Setup (Alternative)

**Backend:**
```bash
cd backend && pip install -r requirements.txt && python app.py
```

**Frontend:**
```bash
cd frontend && npm install && npm run dev
```

## 🏗️ Architecture

**Backend:** Flask + OpenAI + Neo4j + Galileo AI  
**Frontend:** Next.js + React + TypeScript + Three.js  
**Database:** Neo4j (optional)  
**Monitoring:** Galileo AI (optional)

## 🔌 API Endpoints

- `POST /api/chat` - Chat with AI
- `GET /api/graph-data` - Get visualization data  
- `GET /api/sessions` - List sessions
- `GET /health` - Health check

## 🎯 Galileo AI (Optional)

Enterprise-grade AI monitoring and evaluation:
- Real-time quality scoring
- Performance analytics  
- Reasoning evaluation

Setup: Add `GALILEO_API_KEY` to `.env` file.  
Details: See [GALILEO_INTEGRATION.md](./GALILEO_INTEGRATION.md)

## 🐛 Troubleshooting

**Common Issues:**
- Missing modules: Run `./setup.sh`
- API key errors: Check `.env` file
- Port conflicts: Ensure ports 3000/8000 are free
- Dependencies: Run `npm install` and `pip install -r requirements.txt`

**Health Check:** `curl http://localhost:8000/health`
