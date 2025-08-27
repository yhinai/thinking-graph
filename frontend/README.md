# Thinking-graph Chatbot Frontend

## Overview

A Next.js-based frontend application that provides an interactive chat interface integrated with a 3D knowledge graph visualization. Users can have conversations that automatically build and update a visual knowledge graph showing relationships between concepts, entities, and reasoning patterns.

## Features

- **Interactive Chat Interface**: Real-time messaging with AI assistant
- **3D Knowledge Graph**: Visual representation of conversation data using force-directed graphs
- **Backend Integration**: Seamless connection with Thinking-graph backend API
- **Real-time Updates**: Knowledge graph updates automatically as conversations progress
- **Responsive Design**: Modern UI with Tailwind CSS and essential components
- **Optimized Bundle**: Streamlined dependencies for fast loading

## Prerequisites

- Node.js 18+
- npm or pnpm
- Running Thinking-graph backend server

## Setup

1. **Install Dependencies**:
   ```bash
   npm install
   ```
   
   Note: Dependencies have been optimized and streamlined. Only essential packages are included.

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Build for Production**:
   ```bash
   npm run build
   npm start
   ```

## Project Structure (Optimized)

```
├── app/
│   ├── page.tsx                    # Main application page
│   ├── layout.tsx                  # App layout
│   └── globals.css                 # Global styles
├── components/
│   ├── enhanced-chat-interface.tsx # Chat with backend integration
│   ├── enhanced-knowledge-graph-view.tsx # Graph with backend
│   ├── force-graph-3d.tsx         # 3D graph component
│   └── ui/                         # Essential UI components (6 files)
│       ├── button.tsx              # Button component
│       ├── input.tsx               # Input component
│       ├── card.tsx                # Card component
│       ├── badge.tsx               # Badge component
│       ├── avatar.tsx              # Avatar component
│       └── scroll-area.tsx         # Scroll area component
├── lib/
│   ├── api.ts                      # Backend API service
│   └── utils.ts                    # Utility functions
```

**Note**: This structure has been optimized by removing 54+ unused files, reducing complexity by ~70%.

## Features

### Chat Interface
- Real-time messaging with typing indicators
- Message history with timestamps
- Backend connection status indicator
- Error handling and offline mode

### Knowledge Graph Visualization
- 3D force-directed graph using Three.js
- Node types: Sessions, Thoughts, Entities, Tools
- Interactive nodes with click handlers
- Real-time updates when new conversations are processed
- Fallback 2D visualization when 3D libraries aren't available

### Backend Integration
- RESTful API communication
- Health check monitoring
- Automatic reconnection handling
- Graph data synchronization

## Usage

1. **Start the Backend**: Ensure the Thinking-graph backend server is running on `http://localhost:5000`

2. **Open the Application**: Navigate to `http://localhost:3000`

3. **Start Chatting**: Type messages in the chat interface. Each message will:
   - Be processed by the backend AI
   - Generate knowledge graph nodes and relationships
   - Update the 3D visualization in real-time

4. **Explore the Graph**: 
   - Nodes represent different entities (sessions, thoughts, concepts)
   - Links show relationships between entities
   - Colors indicate different node types
   - Click nodes for more information (when implemented)

## Configuration

### API Endpoint
Update the API base URL in `lib/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:5000';
```

### Graph Visualization
Customize the 3D graph in `components/force-graph-3d.tsx`:
- Node colors and sizes
- Link appearance
- Physics simulation parameters
- Interaction behaviors

## Development

### Adding New Features
1. **New API Endpoints**: Add to `lib/api.ts`
2. **UI Components**: Create in `components/`
3. **Graph Customization**: Modify `force-graph-3d.tsx`
4. **Styling**: Update Tailwind classes

### Testing Integration
1. Start both backend and frontend servers
2. Send test messages through the chat
3. Verify graph updates in real-time
4. Check browser console for any errors

## Troubleshooting

### Backend Connection Issues
- Verify backend server is running on port 5000
- Check CORS configuration in backend
- Ensure API endpoints are accessible

### Graph Visualization Problems
- Install required 3D graph dependencies
- Check browser console for Three.js errors
- Verify graph data format from API

### Build Issues
- Clear node_modules and reinstall dependencies
- Update Next.js and React versions if needed
- Check for TypeScript errors

## Future Enhancements

- [ ] Full 3D force graph integration
- [ ] Node detail panels
- [ ] Graph filtering and search
- [ ] Export functionality
- [ ] Real-time collaboration
- [ ] Graph analytics dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request