import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Minimize2,
  Loader2,
  Mic,
  MicOff,
  Volume2,
  VolumeX
} from "lucide-react";

const MarkdownText = ({ content }: { content: string }) => {
  const MD = ReactMarkdown as any;
  return (
    <MD
      remarkPlugins={[[remarkMath, { singleDollarTextMath: false }]]}
      rehypePlugins={[rehypeKatex]}
      components={{
        p: ({ children }: { children: React.ReactNode }) => <p className="text-[0.85rem] leading-relaxed mb-1">{children}</p>,
        h1: ({ children }: { children: React.ReactNode }) => <h1 className="font-bold text-sm mt-2 mb-0.5 text-foreground">{children}</h1>,
        h2: ({ children }: { children: React.ReactNode }) => <h2 className="font-bold text-sm mt-2 mb-0.5 text-foreground">{children}</h2>,
        h3: ({ children }: { children: React.ReactNode }) => <h3 className="font-semibold text-sm mt-1.5 mb-0.5 text-foreground">{children}</h3>,
        ul: ({ children }: { children: React.ReactNode }) => <ul className="list-disc ml-4 my-1 space-y-0.5 text-[0.85rem]">{children}</ul>,
        ol: ({ children }: { children: React.ReactNode }) => <ol className="list-decimal ml-4 my-1 space-y-0.5 text-[0.85rem]">{children}</ol>,
        li: ({ children }: { children: React.ReactNode }) => <li className="leading-relaxed">{children}</li>,
        strong: ({ children }: { children: React.ReactNode }) => <strong className="font-semibold text-foreground">{children}</strong>,
        code: ({ children }: { children: React.ReactNode }) => <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
        pre: ({ children }: { children: React.ReactNode }) => <pre className="bg-muted p-2 rounded text-xs font-mono overflow-x-auto my-1">{children}</pre>,
      }}
    >
      {content}
    </MD>
  );
};
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface RAMPFloatingWidgetProps {
  userName?: string;
  /** Backend uses this for business/RAG context (optional header). */
  userId?: string;
}

// Same base strategy as api.ts / chatbotService: relative `/api` (Vite proxy) or absolute API URL in production.
const API_PREFIX = import.meta.env.VITE_API_BASE_URL || "/api";

const CHAT_STREAM_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT) || 60000;

function buildChatbotHeaders(userId?: string): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = localStorage.getItem("token");
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (userId) {
    headers["X-User-ID"] = userId;
  }
  return headers;
}

// Detect WebSocket URL from environment or current window host
const getWsUrl = (token: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host; // e.g. localhost:8080 or tunnel.loca.lt
  // If we're using the Vite proxy at /api/v1/..., the actual websocket is at the backend port (8000)
  // But since we want to be port-agnostic, we can try to use a relative path if the proxy supports it,
  // or use the backend port directly if we can detect it.
  
  // Check if VITE_API_BASE_URL is set (e.g. /api)
  const apiPrefix = import.meta.env.VITE_API_BASE_URL || '/api';
  
  // For local dev, we typically proxy /api to 8000. 
  // Standard RAMP backend WebSocket path is usually /api/v1/notifications/ws or similar
  return `${protocol}//${host}${apiPrefix}/v1/dashboard-analytics/ws?token=${token}`;
};

const RAMPFloatingWidget = ({ userName, userId }: RAMPFloatingWidgetProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isListeningRef = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Generate session ID on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('raamp_chat_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      localStorage.setItem('raamp_chat_session_id', newSessionId);
    }
  }, []);

  // Initialize welcome message with username
  useEffect(() => {
    const greeting = userName
      ? `Hi ${userName}! I'm your RAAMP Assistant. I can help you with campaign optimization, trend analysis, creative suggestions, and more. How can I assist you today?`
      : "Hi! I'm your RAAMP Assistant. I can help you with campaign optimization, trend analysis, creative suggestions, and more. How can I assist you today?";

    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: greeting,
        timestamp: new Date(),
      },
    ]);
  }, [userName]);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInput(transcript);
      };

      recognitionRef.current.onend = () => {
        // If user hasn't stopped mic manually, restart to keep it running (continuous mode)
        if (isListeningRef.current && recognitionRef.current) {
          try { recognitionRef.current.start(); } catch { /* already started */ }
        } else {
          setIsListening(false);
        }
      };

      recognitionRef.current.onerror = (event: Event) => {
        const err = (event as SpeechRecognitionErrorEvent).error;
        // Don't stop on transient no-speech errors in continuous mode
        if (err === 'no-speech') return;
        isListeningRef.current = false;
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const toggleSpeechRecognition = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }

    if (isListening) {
      isListeningRef.current = false;
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        isListeningRef.current = true;
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Speech recognition error:', error);
        isListeningRef.current = false;
        setIsListening(false);
      }
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    // Stop and clear any current audio / TTS
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    }

    // Stop listening if sending
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = input.trim();
    setInput("");
    setIsTyping(true);

    // Create placeholder assistant message for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    const streamController = new AbortController();
    const streamTimeout = window.setTimeout(() => streamController.abort(), CHAT_STREAM_TIMEOUT_MS);

    try {
      // Aligned with chatbotService: same API prefix, Bearer + X-User-ID, credentials for cookies.
      const response = await fetch(`${API_PREFIX}/chatbot/chat/stream`, {
        method: "POST",
        headers: buildChatbotHeaders(userId),
        credentials: "include",
        signal: streamController.signal,
        body: JSON.stringify({
          message: userInput,
          session_id: sessionId,
          include_sources: false,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      // Read the streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let accumulatedContent = "";

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.slice(6));

              if (jsonData.type === 'token') {
                // Accumulate tokens and update the message
                accumulatedContent += jsonData.content;
                
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                );
              } else if (jsonData.type === 'done') {
                // Stream completed
                if (jsonData.session_id && jsonData.session_id !== sessionId) {
                  setSessionId(jsonData.session_id);
                  localStorage.setItem('raamp_chat_session_id', jsonData.session_id);
                }
                setIsTyping(false);
                // TTS: speak the completed response using Web Speech API
                if (ttsEnabled && accumulatedContent && 'speechSynthesis' in window) {
                  window.speechSynthesis.cancel();
                  const plainText = accumulatedContent.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1').replace(/#{1,3}\s/g, '').replace(/\n/g, ' ');
                  const utterance = new SpeechSynthesisUtterance(plainText);
                  utterance.rate = 0.95;
                  utterance.pitch = 1.0;
                  utterance.volume = 1.0;
                  utterance.onstart = () => setIsPlaying(true);
                  utterance.onend = () => setIsPlaying(false);
                  utterance.onerror = () => setIsPlaying(false);
                  utteranceRef.current = utterance;

                  // Select the best available natural-sounding English voice
                  const selectVoiceAndSpeak = () => {
                    const voices = window.speechSynthesis.getVoices();
                    if (voices.length > 0) {
                      // Preference order: high-quality online voices → local en-US voices → any English
                      const preferred = [
                        'Google US English',
                        'Microsoft Aria Online (Natural) - English (United States)',
                        'Microsoft Jenny Online (Natural) - English (United States)',
                        'Microsoft Guy Online (Natural) - English (United States)',
                        'Microsoft Zira - English (United States)',
                        'Samantha', // macOS
                      ];
                      let chosen = preferred
                        .map(name => voices.find(v => v.name === name))
                        .find(Boolean);

                      if (!chosen) {
                        // Fallback: any en-US voice, then any English voice
                        chosen = voices.find(v => v.lang === 'en-US')
                          ?? voices.find(v => v.lang.startsWith('en'))
                          ?? undefined;
                      }

                      if (chosen) utterance.voice = chosen;
                    }
                    window.speechSynthesis.speak(utterance);
                  };

                  const voices = window.speechSynthesis.getVoices();
                  if (voices.length > 0) {
                    selectVoiceAndSpeak();
                  } else {
                    // Voices may not be loaded yet on first call — wait for the event
                    window.speechSynthesis.onvoiceschanged = () => {
                      window.speechSynthesis.onvoiceschanged = null;
                      selectVoiceAndSpeak();
                    };
                  }
                }
              } else if (jsonData.type === 'error') {
                // Handle error from stream
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: jsonData.content }
                      : msg
                  )
                );
                setIsTyping(false);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chatbot error:', error);

      const isAbort =
        error instanceof DOMException && error.name === "AbortError";
      const fallback = isAbort
        ? "The assistant took too long to respond. Please try a shorter question or try again."
        : "I apologize, but I'm having trouble connecting right now. Please try again in a moment.";

      // Fallback response on error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: fallback,
              }
            : msg
        )
      );
    } finally {
      clearTimeout(streamTimeout);
      setIsTyping(false);
    }
  };

  const playAudio = (base64Audio: string) => {
    try {
      const audioBlob = b64toBlob(base64Audio, 'audio/mpeg');
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = () => setIsPlaying(false);

      audio.play().catch(e => console.error("Audio play failed:", e));
    } catch (e) {
      console.error("Audio preparation failed:", e);
    }
  };

  // Helper to convert base64 to Blob
  const b64toBlob = (b64Data: string, contentType = '', sliceSize = 512) => {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
      const slice = byteCharacters.slice(offset, offset + sliceSize);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }

    return new Blob(byteArrays, { type: contentType });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Reset conversation
  const handleReset = async () => {
    try {
      await fetch(`${API_PREFIX}/chatbot/reset`, {
        method: "POST",
        headers: buildChatbotHeaders(userId),
        credentials: "include",
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch (error) {
      console.error('Reset error:', error);
      toast.warning("Reset partially failed", {
        description: "History cleared locally, but server sync failed."
      });
    }

    // Reset local state
    const greeting = userName
      ? `Hi ${userName}! I'm your RAAMP Assistant. I can help you with campaign optimization, trend analysis, creative suggestions, and more. How can I assist you today?`
      : "Hi! I'm your RAAMP Assistant. I can help you with campaign optimization, trend analysis, creative suggestions, and more. How can I assist you today?";

    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: greeting,
        timestamp: new Date(),
      },
    ]);
  };

  const suggestions = [
    "What is RAAMP?",
    "How do I get started?",
    "Campaign optimization",
    "Geo-intent targeting",
  ];

  return (
    <>
      {/* Floating Button */}
      <motion.div
        className="fixed bottom-6 right-6 z-50 md:bottom-8 md:right-8"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: "spring", stiffness: 260, damping: 20 }}
      >
        <Button
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "w-14 h-14 md:w-14 md:h-14 rounded-full shadow-lg transition-all duration-300",
            "bg-gradient-to-br from-primary to-accent hover:from-primary/90 hover:to-accent/90",
            "flex items-center justify-center",
            isOpen ? "scale-0 opacity-0" : "scale-100 opacity-100"
          )}
          style={{
            boxShadow: "0 0 20px rgba(0, 153, 153, 0.4), 0 4px 12px rgba(0, 0, 0, 0.3)",
          }}
        >
          <MessageSquare className="w-6 h-6 text-foreground" />
          {/* Pulse animation */}
          <span className="absolute inset-0 rounded-full bg-primary/30 animate-ping" />
        </Button>
      </motion.div>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 100, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className={cn(
              "fixed z-50",
              // Mobile: full screen modal
              "inset-0 md:inset-auto",
              // Desktop: bottom-right panel
              "md:bottom-6 md:right-6 md:w-[520px] md:h-[75vh] md:max-h-[740px] md:min-h-[520px]"
            )}
          >
            <Card
              className={cn(
                "flex flex-col h-full",
                "bg-gradient-to-b from-card/98 via-card/95 to-card/90 backdrop-blur-xl",
                "border-primary/20 shadow-2xl",
                "md:rounded-2xl rounded-none"
              )}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-primary/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-foreground" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">RAAMP Assistant</h3>
                    <p className="text-xs text-muted-foreground">Always here to help</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 hover:bg-primary/10"
                    onClick={() => {
                      if (isPlaying) { window.speechSynthesis.cancel(); setIsPlaying(false); }
                      setTtsEnabled(v => !v);
                    }}
                    title={ttsEnabled ? 'Disable text-to-speech' : 'Enable text-to-speech'}
                  >
                    {ttsEnabled ? <Volume2 className="w-4 h-4 text-primary" /> : <VolumeX className="w-4 h-4 text-muted-foreground" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 hover:bg-primary/10"
                    onClick={() => setIsOpen(false)}
                  >
                    <Minimize2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => setIsOpen(false)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                <div className="space-y-4">
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        "flex",
                        message.role === "user" ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[85%] rounded-2xl px-4 py-2.5 text-[0.85rem]",
                          message.role === "user"
                            ? "bg-primary text-primary-foreground rounded-br-md"
                            : "bg-muted/50 border border-primary/10 rounded-bl-md"
                        )}
                      >
                        {message.role === "assistant" ? (
                          <MarkdownText content={message.content} />
                        ) : (
                          message.content
                        )}
                      </div>
                    </motion.div>
                  ))}

                  {/* Typing indicator */}
                  {isTyping && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-start"
                    >
                      <div className="bg-muted/50 border border-primary/10 rounded-2xl rounded-bl-md px-4 py-3">
                        <div className="flex items-center gap-1">
                          <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <span className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Speaking indicator */}
                  {isPlaying && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="flex justify-start"
                    >
                      <div className="bg-primary/10 border border-primary/30 rounded-full px-3 py-1 flex items-center gap-2">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                        </span>
                        <span className="text-[10px] font-mono text-primary uppercase tracking-widest animate-pulse">Assistant is speaking...</span>
                      </div>
                    </motion.div>
                  )}
                </div>
              </ScrollArea>

              {/* Suggestions */}
              {messages.length <= 2 && !isTyping && (
                <div className="px-4 pb-2">
                  <div className="flex flex-wrap gap-2">
                    {suggestions.map((suggestion) => (
                      <Button
                        key={suggestion}
                        variant="outline"
                        size="sm"
                        className="text-xs h-7 bg-primary/5 border-primary/20 hover:bg-primary/10"
                        onClick={() => {
                          setInput(suggestion);
                          inputRef.current?.focus();
                        }}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Input */}
              <div className="p-4 border-t border-primary/10">
                <div className="flex items-center gap-2">
                  <Button
                    onClick={toggleSpeechRecognition}
                    disabled={isTyping}
                    variant="ghost"
                    className={cn(
                      "w-11 h-11 rounded-full transition-all flex-shrink-0",
                      isListening
                        ? "bg-destructive/20 text-destructive hover:bg-destructive/30 animate-pulse ring-2 ring-destructive/50"
                        : "bg-primary/10 text-primary hover:bg-primary/20 ring-1 ring-primary/30"
                    )}
                    title={isListening ? "Stop listening" : "Start voice input"}
                  >
                    {isListening ? (
                      <MicOff className="w-5 h-5" />
                    ) : (
                      <Mic className="w-5 h-5" />
                    )}
                  </Button>
                  <Input
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={isListening ? "Listening..." : "Ask RAAMP anything..."}
                    className={cn(
                      "flex-1 bg-muted/30 border-primary/20 focus-visible:ring-primary/30",
                      isListening && "border-destructive/50"
                    )}
                    disabled={isTyping}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || isTyping}
                    className="w-10 h-10 rounded-full bg-primary hover:bg-primary/90"
                  >
                    {isTyping ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default RAMPFloatingWidget;
