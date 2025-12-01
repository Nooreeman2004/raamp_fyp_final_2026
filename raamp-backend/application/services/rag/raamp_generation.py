"""
RAAMP Generation Module (LangChain Enhanced)
=============================================
Response generation component for the RAAMP Assistant RAG pipeline.
Uses LangChain's ChatOpenAI and prompt templates for optimized responses.
Implements strict guardrails to only answer based on FAQ knowledge.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .raamp_retriever import RAAMPRetriever

# Load environment variables
load_dotenv()


# Specialized system prompt for RAAMP Assistant
RAAMP_SYSTEM_PROMPT = """You are the **RAAMP Assistant**, a helpful and knowledgeable AI helper for the Revolutionary AI-Powered Autonomous Marketing Platform (RAAMP). Your primary goal is to provide concise, accurate, and relevant answers to user questions **based only on the information provided in the context below**.

Key instructions:
- **Strictly use the provided context.** Do not use any external knowledge about marketing, RAAMP, or general topics.
- **NEVER** answer questions that are not supported by the context. If the context does not contain the answer, state: "I am sorry, but I can only answer questions about the RAAMP platform based on the documentation I have. I do not have enough information to answer that."
- Maintain a highly professional, knowledgeable, and helpful tone, reflecting RAAMP's advanced AI capabilities.
- For feature explanations, focus on the **benefit to the business owner** (e.g., increased ROI, time savings).
- Use emojis where appropriate: 💡 for features/AI, 🔒 for security, 📈 for performance/metrics, ⚙️ for settings/troubleshooting.
- Keep responses concise but comprehensive.
- If the user greets you, respond warmly and offer to help with RAAMP-related questions.

Context from RAAMP Knowledge Base:
{context}
"""


@dataclass
class RAGResponse:
    """Represents a response from the RAG pipeline."""
    query: str
    answer: str
    context_used: str
    sources: List[Dict[str, Any]]
    model: str
    created_at: str
    tokens_used: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "context_used": self.context_used,
            "sources": self.sources,
            "model": self.model,
            "created_at": self.created_at,
            "tokens_used": self.tokens_used
        }


class RAAMPGenerator:
    """
    LangChain-enhanced response generator for the RAAMP Assistant.
    Combines retrieval with LLM generation for RAG-based responses.
    Supports conversation memory for multi-turn dialogues.
    """
    
    def __init__(self, retriever: RAAMPRetriever = None):
        """
        Initialize the generator with LangChain components.
        
        Args:
            retriever: RAAMPRetriever instance. Creates new one if not provided.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.model_name = os.getenv("OPENAI_GENERATION_MODEL", "gpt-3.5-turbo")
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.7,
            max_tokens=500,
            openai_api_key=self.api_key
        )
        
        # Initialize retriever
        self.retriever = retriever or RAAMPRetriever()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", RAAMP_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # Create output parser
        self.output_parser = StrOutputParser()
        
        print("✅ LangChain Generator initialized")
        print(f"   Model: {self.model_name}")
    
    def _get_context(self, query: str, n_results: int = None) -> str:
        """Get formatted context from retriever."""
        return self.retriever.retrieve_with_context(query, n_results)
    
    def _get_sources(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """Get source documents for a query."""
        docs = self.retriever.retrieve(query, n_results)
        return [
            {
                "id": doc.id,
                "question": doc.question,
                "category": doc.category,
                "relevance": doc.relevance_score
            }
            for doc in docs
        ]
    
    def generate_response(self, 
                          query: str, 
                          n_context: int = None,
                          chat_history: List = None) -> RAGResponse:
        """
        Generate a response for a user query using RAG.
        
        Args:
            query: User's question
            n_context: Number of context documents to retrieve
            chat_history: Previous messages in conversation
            
        Returns:
            RAGResponse object containing the answer and metadata
        """
        # Retrieve context
        context_text = self._get_context(query, n_context)
        sources = self._get_sources(query, n_context)
        
        # Convert chat history to LangChain message format
        lc_history = []
        if chat_history:
            for msg in chat_history[-10:]:  # Keep last 10 messages for context
                if msg.get("role") == "user":
                    lc_history.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    lc_history.append(AIMessage(content=msg["content"]))
        
        # Build and invoke chain
        try:
            chain = self.prompt | self.llm | self.output_parser
            
            answer = chain.invoke({
                "context": context_text,
                "chat_history": lc_history,
                "question": query
            })
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            answer = "I apologize, but I encountered an error processing your request. Please try again."
        
        # Build response object
        return RAGResponse(
            query=query,
            answer=answer,
            context_used=context_text,
            sources=sources,
            model=self.model_name,
            created_at=datetime.utcnow().isoformat(),
            tokens_used=None  # LangChain handles this internally
        )
    
    def generate_simple(self, query: str) -> str:
        """
        Simple interface for generating a response.
        Returns just the answer text.
        
        Args:
            query: User's question
            
        Returns:
            Answer string
        """
        response = self.generate_response(query)
        return response.answer
    
    def chat(self, 
             query: str, 
             conversation_history: List[Dict[str, str]] = None,
             n_context: int = None) -> Dict[str, Any]:
        """
        Chat interface with conversation history support.
        Maintains context across multiple turns.
        
        Args:
            query: User's current question
            conversation_history: Previous messages in the conversation
            n_context: Number of context documents to retrieve
            
        Returns:
            Dictionary with response and updated history
        """
        response = self.generate_response(
            query=query,
            n_context=n_context,
            chat_history=conversation_history
        )
        
        # Update conversation history
        new_history = list(conversation_history) if conversation_history else []
        new_history.append({"role": "user", "content": query})
        new_history.append({"role": "assistant", "content": response.answer})
        
        return {
            "answer": response.answer,
            "sources": response.sources,
            "conversation_history": new_history
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the generator."""
        try:
            # Check retriever
            retriever_health = self.retriever.health_check()
            
            # Test LLM with a simple prompt
            test_result = self.llm.invoke([HumanMessage(content="Say 'OK'")])
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "retriever": retriever_health,
                "llm_test": "passed"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class RAMPAssistant:
    """
    High-level interface for the RAAMP Assistant chatbot.
    Provides a simple API for the frontend widget with session management.
    Thread-safe for multi-user support.
    """
    
    # Singleton generator instance (shared across sessions)
    _generator: RAAMPGenerator = None
    
    @classmethod
    def get_generator(cls) -> RAAMPGenerator:
        """Get or create the shared generator instance."""
        if cls._generator is None:
            cls._generator = RAAMPGenerator()
        return cls._generator
    
    def __init__(self, session_id: str = None):
        """
        Initialize the RAAMP Assistant for a session.
        
        Args:
            session_id: Unique session identifier for conversation tracking
        """
        self.session_id = session_id or "default"
        self.generator = self.get_generator()
        self.conversation_history: List[Dict[str, str]] = []
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question and get a response with sources.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        result = self.generator.chat(question, self.conversation_history)
        self.conversation_history = result["conversation_history"]
        
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "session_id": self.session_id
        }
    
    def ask_simple(self, question: str) -> str:
        """
        Ask a question and get just the answer text.
        
        Args:
            question: User's question
            
        Returns:
            Answer string
        """
        return self.ask(question)["answer"]
    
    def reset_conversation(self):
        """Reset the conversation history for this session."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history
    
    def get_conversation_length(self) -> int:
        """Get the number of messages in conversation."""
        return len(self.conversation_history)


def main():
    """Test the LangChain generation functionality."""
    print("🚀 Testing RAAMP Generator (LangChain)...")
    print("=" * 50)
    
    generator = RAAMPGenerator()
    
    # Health check
    health = generator.health_check()
    print(f"\n📊 Health Check: {health['status']}")
    
    # Test queries
    test_queries = [
        "What is RAAMP?",
        "How do I sign up?",
        "What is the capital of France?"  # Should trigger guardrail
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"🔍 Query: '{query}'")
        print("-" * 50)
        
        response = generator.generate_response(query)
        print(f"📝 Answer: {response.answer[:300]}...")
        print(f"📚 Sources: {len(response.sources)} documents used")
    
    # Test conversation
    print("\n" + "=" * 50)
    print("💬 Testing Conversation Mode...")
    
    assistant = RAMPAssistant(session_id="test-session")
    
    conversation = [
        "Hi there!",
        "What features does RAAMP have?",
        "Tell me more about the first one"
    ]
    
    for msg in conversation:
        print(f"\n👤 User: {msg}")
        response = assistant.ask(msg)
        print(f"🤖 Assistant: {response['answer'][:200]}...")
    
    print(f"\n📊 Conversation length: {assistant.get_conversation_length()} messages")
    print("\n✅ LangChain Generator test complete!")


if __name__ == "__main__":
    main()
