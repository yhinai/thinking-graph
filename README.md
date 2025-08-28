# Knowledge Graph Visualization with AI Chat

Application that creates interactive 3D knowledge graphs from AI conversations thinking LLM. Chat with AI and watch your ideas transform into visual knowledge networks stored in Neo4j.


## ✨ Features

- **Interactive AI Chat**: Natural conversations with OpenAI GPT models
- **3D Knowledge Graph**: Real-time visualization using force-directed graphs
- **Neo4j Integration**: Persistent graph storage in Neo4j AuraDB
- **Knowledge Discovery**: Extract entities, relationships, and reasoning patterns
- **Real-time Updates**: Watch graphs build as you chat
- **🎯 Galileo AI Monitoring**: Enterprise-grade AI evaluation and observability with quality scoring


## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn
- OpenAI API Key
- Google AI API Key (optional)
- Galileo API Key (optional)

### Automated Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd thinking-graph
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   This will automatically:
   - Install all frontend and backend dependencies
   - Create a `.env` file with default configuration
   - Verify all dependencies are working
   - Make scripts executable

3. **Update your API keys:**
   Edit the `.env` file and add your actual API keys:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   GOOGLE_API_KEY=your_google_key_here
   GALILEO_API_KEY=your_galileo_key_here
   ```

4. **Start the application:**
   ```bash
   ./start.sh
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Health Check: http://localhost:8000/health

### Manual Setup

If you prefer manual setup:
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
- **Galileo AI** (AI monitoring & evaluation)
- Neo4j Database
- Python-dotenv

**Frontend:**
- Next.js 15.2 + React 19
- TypeScript
- Tailwind CSS
- 3D-Force-Graph + Three.js
- Radix UI components

## 🎯 Galileo AI Integration

### Enterprise AI Monitoring
The application integrates with [Galileo AI](https://www.rungalileo.io/) to provide advanced AI observability:

- **Real-time Quality Scoring**: Every AI response is evaluated for coherence, completeness, and relevance
- **Performance Analytics**: Track conversation quality trends and system performance
- **Reasoning Evaluation**: Multi-dimensional assessment of AI reasoning capabilities
- **Interactive Dashboards**: Beautiful visualizations of AI performance metrics

### Setup Instructions
1. **Sign up** for Galileo AI at [rungalileo.io](https://www.rungalileo.io/)
2. **Get API Keys** from your Galileo dashboard
3. **Configure Environment**: Add Galileo credentials to your `.env` file
4. **Enable Monitoring**: Set `ENABLE_GALILEO_MONITORING=true`

### Features Available
- ✅ **Automatic Evaluation**: Every chat interaction is automatically assessed
- ✅ **Graceful Fallback**: Works with or without Galileo API keys
- ✅ **Health Monitoring**: Service status visible in `/health` endpoint
- ✅ **Quality Metrics**: Detailed scoring across multiple dimensions

📖 **Detailed Guide**: See [GALILEO_INTEGRATION.md](./GALILEO_INTEGRATION.md) for comprehensive setup and usage instructions.

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

### Common Issues Fixed

**"Module not found: Can't resolve '@/lib/api'" or similar module errors:**
- Run `./setup.sh` to automatically create missing modules
- Or manually create missing files in `frontend/lib/` directory

**"next: command not found":**
- Run `cd frontend && npm install` to install frontend dependencies
- Or use `./setup.sh` for automated installation

**Frontend gets 500 errors:**
- Ensure backend is running on port 8000
- Check that all required lib files exist (`frontend/lib/api.ts`, `frontend/lib/utils.ts`)
- Run `./setup.sh` to verify and fix missing dependencies

### General Troubleshooting

**Backend Issues:**
- Check API keys in `.env` file (OpenAI, Gemini, Galileo)
- Verify Neo4j connection credentials
- Ensure Python dependencies are installed: `pip3 install -r backend/requirements.txt`

**Galileo AI Integration Issues:**
- **Authentication Errors**: Verify `GALILEO_API_KEY` is correct in `.env`
- **Service Unavailable**: Check `/health` endpoint for Galileo service status
- **Missing Evaluations**: Ensure `ENABLE_GALILEO_MONITORING=true` is set
- **Fallback Mode**: Application continues with basic evaluation if Galileo is unavailable

**Frontend Issues:**
- Run `npm install` in frontend directory
- Check if backend is running on port 8000: `curl http://localhost:8000/health`
- Verify API endpoints are accessible

**Connection Issues:**
- Ensure ports 3000 and 8000 are available
- Check firewall settings
- Verify CORS configuration

**Quick Fix Commands:**
```bash
# Clean setup
./setup.sh

# Manual dependency installation
cd frontend && npm install
pip3 install -r backend/requirements.txt

# Start with verbose logging
./start.sh

# Check if services are running
curl http://localhost:8000/health
curl http://localhost:3000
```
