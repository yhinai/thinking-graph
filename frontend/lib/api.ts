// API service for communicating with the backend

export interface EvaluationData {
  galileo_enabled: boolean;
  evaluation_scores: Record<string, any>;
  evaluation_feedback: Record<string, any>;
  self_evaluation: Record<string, any>;
  galileo_trace_id?: string;
  service_version: string;
}

export interface ChatResponse {
  success: boolean;
  session_id: string;
  thoughts: string;
  response: string;
  message: string;
  kg_enabled: boolean;
  evaluation: EvaluationData;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  val: number;
  color: string;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string;
  value: number;
}

export interface GraphData {
  nodes: Array<GraphNode>;
  links: Array<GraphLink>;
}

export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  kg_system_initialized: boolean;
  galileo_service: any;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  async sendChatMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getGraphData(): Promise<GraphData> {
    const response = await fetch(`${this.baseUrl}/api/graph-data`);
    if (!response.ok) {
      throw new Error(`Graph data request failed: ${response.statusText}`);
    }
    return response.json();
  }

  async clearDatabase(): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/clear-database`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`Clear database request failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getSessions(): Promise<{ sessions: any[] }> {
    const response = await fetch(`${this.baseUrl}/api/sessions`);
    if (!response.ok) {
      throw new Error(`Get sessions request failed: ${response.statusText}`);
    }
    return response.json();
  }

  async getSessionDetails(sessionId: string): Promise<{ session: any }> {
    const response = await fetch(`${this.baseUrl}/api/session/${sessionId}`);
    if (!response.ok) {
      throw new Error(`Get session details request failed: ${response.statusText}`);
    }
    return response.json();
  }

  async getPatterns(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/patterns`);
    if (!response.ok) {
      throw new Error(`Get patterns request failed: ${response.statusText}`);
    }
    return response.json();
  }
}

export const apiService = new ApiService();