
import axios from 'axios';

// Helper to get auth token from storage
const getAuthToken = (): string | null => {
    return localStorage.getItem('token');
};

const API_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
}

export interface ChatSource {
    id: string;
    question: string;
    category: string;
    relevance: number;
}

export interface ChatResponse {
    answer: string;
    session_id: string;
    sources?: ChatSource[];
    timestamp: string;
    audio_content?: string;
}

export interface DiagnosticResult {
    status: 'success' | 'warning' | 'failed' | 'error';
    message: string;
    details: string;
}

export const chatbotService = {
    /**
     * Send a message to the chatbot with optional context
     */
    async sendMessage(message: string, sessionId?: string, context?: Record<string, any>): Promise<ChatResponse> {
        try {
            const token = getAuthToken();
            const headers: any = {
                'Content-Type': 'application/json',
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await axios.post(`${API_URL}/chatbot/chat`, {
                message,
                session_id: sessionId,
                include_sources: true,
                context: context // Send context to backend
            }, { headers });

            return response.data;
        } catch (error: any) {
            throw new Error(error.response?.data?.detail || 'Failed to send message');
        }
    },

    /**
     * Get conversation history
     */
    async getHistory(sessionId: string): Promise<ChatMessage[]> {
        try {
            const token = getAuthToken();
            const headers: any = {
                'Content-Type': 'application/json',
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await axios.get(`${API_URL}/chatbot/history/${sessionId}`, { headers });
            return response.data.messages;
        } catch (error) {
            console.error("Failed to fetch history", error);
            return [];
        }
    },

    /**
     * Reset the chat session
     */
    async resetSession(sessionId: string): Promise<boolean> {
        try {
            const token = getAuthToken();
            const headers: any = {
                'Content-Type': 'application/json',
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            await axios.post(`${API_URL}/chatbot/reset`, { session_id: sessionId }, { headers });
            return true;
        } catch (error) {
            return false;
        }
    },

    /**
     * Run a diagnostic check
     */
    async runDiagnostic(checkId: string): Promise<DiagnosticResult> {
        try {
            const token = getAuthToken();
            const headers: any = {
                'Content-Type': 'application/json',
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await axios.post(`${API_URL}/chatbot/diagnostics/run`, {
                check_id: checkId
            }, { headers });

            return response.data;
        } catch (error: any) {
            return {
                status: 'error',
                message: 'Check Failed',
                details: error.response?.data?.detail || error.message
            };
        }
    }
};
