# Knowledge Graph Visualization with AI Chat

Application that creates interactive 3D knowledge graphs from AI conversations thinking LLM. Chat with AI and watch your ideas transform into visual knowledge networks stored in Neo4j.


## ✨ Features

- **Interactive AI Chat**: Natural conversations with OpenAI GPT models
- **3D Knowledge Graph**: Real-time visualization using force-directed graphs
- **Neo4j Integration**: Persistent graph storage in Neo4j AuraDB
- **Knowledge Discovery**: Extract entities, relationships, and reasoning patterns
- **Real-time Updates**: Watch graphs build as you chat


## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API Key
- Google Gemini API Key  
- Neo4j AuraDB instance

### 1. Clone and Setup
```bash
git clone <repository-url>
```

### 2. Environment Configuration
Create `backend/.env` with:
```bash
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
NEO4J_URI=neo4j+s://your-auradb.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
PORT=8000
```

### 3. Run Application
```bash
./start.sh
```

The script will:
- Kill any existing processes on ports 3000 & 8000
- Start backend server (port 8000) with health checks
- Start frontend server (port 3000) with accessibility verification
- Test API connectivity
- Report full system status

### 4. Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **Health Check**: http://localhost:8000/health

## 🛠️ Manual Setup

### Backend
```bash
cd backend/
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend/
npm install
npm run dev
```

## 📁 Project Structure

### Backend (`/backend`)
- **Flask API server** with CORS enabled
- **Knowledge graph builder** using Google Gemini AI
- **Neo4j integration** for persistent storage
- **OpenAI chat integration** with reasoning extraction

### Frontend (`/frontend`)
- **Next.js application** with TypeScript
- **3D force graph visualization** using Three.js
- **Real-time chat interface** with backend API
- **Responsive UI components** with Tailwind CSS

## 🔌 API Endpoints

- `POST /api/chat` - Send chat messages and get AI responses
- `GET /api/graph-data` - Retrieve graph data for visualization
- `GET /api/sessions` - List all chat sessions
- `GET /health` - Backend health status
- `DELETE /api/clear-database` - Reset graph database

## 🎨 Technologies

**Backend:**
- Flask 3.0 + Flask-CORS
- OpenAI GPT API
- Google Gemini AI
- Neo4j Database
- Python-dotenv

**Frontend:**
- Next.js 15.2 + React 19
- TypeScript
- Tailwind CSS
- 3D-Force-Graph + Three.js
- Radix UI components

## 🔧 Development

### Adding New Features
1. Backend changes: Modify Flask routes in `backend/app.py`
2. Frontend changes: Update components in `frontend/components/`  
3. API changes: Update `frontend/lib/api.ts`

### Testing
The `start.sh` script includes built-in health checks:
- Backend health endpoint verification
- Frontend accessibility testing
- API connectivity validation

## 🐛 Troubleshooting

**Backend Issues:**
- Check API keys in `.env` file
- Verify Neo4j connection credentials
- Ensure Python dependencies are installed

**Frontend Issues:**
- Run `npm install` in frontend directory
- Check if backend is running on port 8000
- Verify API endpoints are accessible

**Connection Issues:**
- Ensure ports 3000 and 8000 are available
- Check firewall settings
- Verify CORS configuration
