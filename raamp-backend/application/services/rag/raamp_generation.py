"""
RAAMP Generation Module (LangChain Enhanced)
=============================================
Response generation component for the RAAMP Assistant RAG pipeline.
Uses OpenAI API through LangChain for optimized responses.
Implements strict guardrails to only answer based on FAQ knowledge.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import logging

from .raamp_retriever import RAAMPRetriever

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)


# Specialized system prompt for RAAMP Assistant with marketing context
RAAMP_SYSTEM_PROMPT = """You are the **RAAMP Assistant**, a highly knowledgeable AI marketing advisor for the Revolutionary AI-Powered Autonomous Marketing Platform (RAAMP). You combine deep marketing expertise with RAAMP platform knowledge to provide exceptional support.

## Core Capabilities:
1. **Platform Expertise**: Deep knowledge of RAAMP features, setup, and troubleshooting
2. **Marketing Intelligence**: Understanding of digital marketing concepts (ROI, CTR, CPC, engagement)
3. **Geo-Intent Marketing**: Expertise in hyperlocal and location-based marketing strategies
4. **Campaign Optimization**: Knowledge of ad performance, targeting, and optimization

## Response Guidelines:
- **Strictly use the provided context** for RAAMP-specific questions
- For marketing concepts mentioned in context, explain them in a business-friendly way
- If asked about general marketing without RAAMP context, relate it back to how RAAMP can help
- For questions outside RAAMP scope, politely redirect: "I'm specialized in RAAMP platform support. For that question, I'd recommend [brief suggestion]. Is there anything about RAAMP I can help with?"

## Tone & Style:
- Professional yet approachable
- Use clear, jargon-free explanations when possible
- Include relevant emojis: 💡 features, 🔒 security, 📈 analytics, ⚙️ settings, 🎯 targeting, 📍 location
- For troubleshooting, be reassuring and provide step-by-step guidance
- Keep responses concise but comprehensive (2-4 paragraphs max)

## Special Handling:
- **Greetings**: Respond warmly and offer to help with RAAMP or marketing questions
- **Technical Issues/Complaints**: If a user has a technical issue, complaint, or needs formal support, sympathetically guide them to the Support Center: [link to complaints page](/dashboard/complaints).
- **Typos/Partial queries**: Understand intent even with imperfect spelling
- **Multi-part questions**: Address each part systematically

Context from RAAMP Knowledge Base:
{context}

{business_context}

{trend_context}
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
        Initialize the generator with OpenAI through LangChain.
        
        Args:
            retriever: RAAMPRetriever instance. Creates new one if not provided.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.model_name = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o-mini")
        
        # Initialize OpenAI LLM through LangChain
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=0.7,
                max_tokens=500,
                openai_api_key=self.api_key
            )
            logger.info(f"✅ OpenAI Generator initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        
        # Initialize retriever
        self.retriever = retriever or RAAMPRetriever()
        
        print("✅ OpenAI Generator initialized")
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
                          chat_history: List = None,
                          business_context: str = "",
                          trend_context: str = "") -> RAGResponse:
        """
        Generate a response for a user query using RAG.
        
        Args:
            query: User's question
            n_context: Number of context documents to retrieve
            chat_history: Previous messages in conversation
            business_context: Dynamically injected business details
            trend_context: Dynamically injected trend analysis details
            
        Returns:
            RAGResponse object containing the answer and metadata
        """
        # Retrieve context
        context_text = self._get_context(query, n_context)
        sources = self._get_sources(query, n_context)
        
        # Build messages for LangChain
        messages = []
        
        # System message with context
        system_content = RAAMP_SYSTEM_PROMPT.format(
            context=context_text,
            business_context=business_context,
            trend_context=trend_context
        )
        messages.append(SystemMessage(content=system_content))
        
        # Add conversation history if provided
        if chat_history:
            for msg in chat_history[-10:]:  # Keep last 10 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        # Add current user query
        messages.append(HumanMessage(content=query))
        
        # Generate response with OpenAI using LangChain
        try:
            response = self.llm.invoke(messages)
            answer = response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # User-friendly error message
            answer = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
        
        # Build response object
        return RAGResponse(
            query=query,
            answer=answer,
            context_used=context_text,
            sources=sources,
            model=self.model_name,
            created_at=datetime.utcnow().isoformat(),
            tokens_used=None  # Could be extracted from response metadata if needed
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
    
    def generate_response_stream(self,
                                 query: str,
                                 n_context: int = None,
                                 chat_history: List = None,
                                 business_context: str = "",
                                 trend_context: str = ""):
        """
        Generate a streaming response for a user query using RAG.
        Yields tokens as they arrive from OpenAI.
        
        Args:
            query: User's question
            n_context: Number of context documents to retrieve
            chat_history: Previous messages in conversation
            business_context: Dynamically injected business details
            trend_context: Dynamically injected trend analysis details
            
        Yields:
            Token strings as they arrive from the LLM
        """
        # Retrieve context
        context_text = self._get_context(query, n_context)
        
        # Build messages for LangChain
        messages = []
        
        # System message with context
        system_content = RAAMP_SYSTEM_PROMPT.format(
            context=context_text,
            business_context=business_context,
            trend_context=trend_context
        )
        messages.append(SystemMessage(content=system_content))
        
        # Add conversation history if provided
        if chat_history:
            for msg in chat_history[-10:]:  # Keep last 10 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        # Add current user query
        messages.append(HumanMessage(content=query))
        
        # Stream response with OpenAI using LangChain
        try:
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            # User-friendly error message
            yield "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    def get_sources(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """
        Public method to get sources for a query.
        Wrapper around _get_sources for external access.
        
        Args:
            query: User's question
            n_results: Number of results to retrieve
            
        Returns:
            List of source dictionaries
        """
        return self._get_sources(query, n_results)
    
    def chat(self, 
             query: str, 
             conversation_history: List[Dict[str, str]] = None,
             n_context: int = None,
             business_context: str = "",
             trend_context: str = "") -> Dict[str, Any]:
        """
        Chat interface with conversation history support.
        Maintains context across multiple turns.
        
        Args:
            query: User's current question
            conversation_history: Previous messages in the conversation
            n_context: Number of context documents to retrieve
            business_context: Business context string
            trend_context: Trend context string
            
        Returns:
            Dictionary with response and updated history
        """
        response = self.generate_response(
            query=query,
            n_context=n_context,
            chat_history=conversation_history,
            business_context=business_context,
            trend_context=trend_context
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
    
    def chat_stream(self,
                    query: str,
                    conversation_history: List[Dict[str, str]] = None,
                    n_context: int = None,
                    business_context: str = "",
                    trend_context: str = ""):
        """
        Streaming chat interface with conversation history support.
        Yields tokens as they arrive.
        
        Args:
            query: User's current question
            conversation_history: Previous messages in the conversation
            n_context: Number of context documents to retrieve
            business_context: Business context string
            trend_context: Trend context string
            
        Yields:
            Tokens as they arrive
        """
        # Stream the response
        for token in self.generate_response_stream(query, n_context, conversation_history, business_context, trend_context):
            yield token
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the generator."""
        try:
            # Check retriever
            retriever_health = self.retriever.health_check()
            
            # Test LLM with a simple prompt
            test_response = self.llm.invoke([HumanMessage(content="Say 'OK'")])
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "retriever": retriever_health,
                "llm_test": "passed"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": "Service temporarily unavailable"
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
    print("🚀 Testing RAAMP Generator (OpenAI + LangChain)...")
    print("=" * 50)
    
    try:
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
        print("\n✅ OpenAI Generator test complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
