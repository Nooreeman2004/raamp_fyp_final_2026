import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Zap, MessageSquare, Lightbulb, AlertCircle, Play, Terminal, Cpu, ShieldCheck, Activity, RefreshCw, CheckCircle, XCircle, Mic, MicOff, Loader2 } from "lucide-react";
import { chatbotService, ChatMessage, ChatResponse, DiagnosticResult } from "@/services/chatbotService";
import { toast as sonner } from "sonner";
import { useLocation } from "react-router-dom";

// Animation Imports
import { motion, AnimatePresence } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, hoverLift } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

interface DiagnosticItem {
  id: string;
  name: string;
  status: "PENDING" | "RUNNING" | "SUCCESS" | "WARNING" | "FAILED";
  variant: "default" | "secondary" | "destructive" | "outline";
  color: string;
  border: string;
  message?: string;
}

const RAAMPAssistant = () => {
  const [message, setMessage] = useState("");
  const [session, setSession] = useState<string>("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const [diagnostics, setDiagnostics] = useState<DiagnosticItem[]>([
    { id: "ad_account_health", name: "AD ACCOUNT HEALTH CHECK", status: "PENDING", variant: "secondary" as const, color: "text-amber-400", border: "border-amber-400/50" },
    { id: "budget_discrepancy", name: "BUDGET ALLOCATION DISCREPANCIES", status: "PENDING", variant: "default" as const, color: "text-primary", border: "border-primary/50" },
    { id: "pixel_verification", name: "PIXEL IMPLEMENTATION VERIFICATION", status: "PENDING", variant: "secondary" as const, color: "text-muted-foreground/80", border: "border-border/80" },
    { id: "creative_compliance", name: "CREATIVE ASSET COMPLIANCE", status: "PENDING", variant: "destructive" as const, color: "text-red-500", border: "border-red-500/50" }
  ]);

  const [runningCheckId, setRunningCheckId] = useState<string | null>(null);

  // Initialize session
  useEffect(() => {
    const savedSession = localStorage.getItem("raamp_chat_session");
    if (savedSession) {
      setSession(savedSession);
      fetchHistory(savedSession);
    }
  }, []);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = Array.from(event.results as any[])
          .map((result: any) => result[0].transcript)
          .join('');
        setMessage(transcript);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history, isLoading]);


  const fetchHistory = async (sessionId: string) => {
    try {
      const msgs = await chatbotService.getHistory(sessionId);
      setHistory(msgs);
    } catch (err) {
      console.error("Failed to load history", err);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const currentMsg = message;
    setMessage("");
    setIsLoading(true);

    // Stop any current audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }

    // Optimistic UI update
    const tempUserMsg: ChatMessage = { role: "user", content: currentMsg, timestamp: new Date().toISOString() };
    setHistory(prev => [...prev, tempUserMsg]);

    try {
      const context = {
        current_page: location.pathname,
        timestamp: new Date().toISOString()
      };

      const response: ChatResponse = await chatbotService.sendMessage(currentMsg, session, context);

      // Update session if new
      if (!session) {
        setSession(response.session_id);
        localStorage.setItem("raamp_chat_session", response.session_id);
      }

      const botMsg: ChatMessage = { role: "assistant", content: response.answer, timestamp: response.timestamp };
      setHistory(prev => [...prev, botMsg]);

      // 🔊 Play audio if available
      if (response.audio_content) {
        playAudio(response.audio_content);
      }

    } catch (err: any) {
      sonner.error("Failed to send message", { description: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSpeechRecognition = () => {
    if (!recognitionRef.current) {
      sonner.error('Speech recognition is not supported in your browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Speech recognition error:', error);
        setIsListening(false);
      }
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
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleReset = async () => {
    if (!session) return;
    try {
      await chatbotService.resetSession(session);
      setHistory([]);
      setSession("");
      localStorage.removeItem("raamp_chat_session");
      sonner.success("Session Reset", { description: "Conversation history cleared." });
    } catch (err) {
      console.error("Reset failed", err);
    }
  };

  const handleRunDiagnostic = async (checkId: string) => {
    setRunningCheckId(checkId);

    // Update status to RUNNING
    setDiagnostics(prev => prev.map(d =>
      d.id === checkId ? { ...d, status: "RUNNING" } : d
    ));

    try {
      const result = await chatbotService.runDiagnostic(checkId);

      // Map backend status to UI status
      let uiStatus: DiagnosticItem["status"] = "PENDING";
      let variant: DiagnosticItem["variant"] = "secondary";

      if (result.status === "success") { uiStatus = "SUCCESS"; variant = "default"; }
      else if (result.status === "warning") { uiStatus = "WARNING"; variant = "secondary"; }
      else { uiStatus = "FAILED"; variant = "destructive"; }

      setDiagnostics(prev => prev.map(d =>
        d.id === checkId ? {
          ...d,
          status: uiStatus,
          variant: variant,
          message: result.message
        } : d
      ));

      if (result.status === 'success') {
        sonner.success(result.message, { description: result.details });
      } else if (result.status === 'warning') {
        sonner.warning(result.message, { description: result.details });
      } else {
        sonner.error(result.message, { description: result.details });
      }

    } catch (error) {
      setDiagnostics(prev => prev.map(d =>
        d.id === checkId ? { ...d, status: "FAILED", variant: "destructive" } : d
      ));
      sonner.error("Diagnostic Failed", { description: "Could not complete the system check." });
    } finally {
      setRunningCheckId(null);
    }
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-primary/10 rounded border border-primary/30">
              <Cpu className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-1 font-heading font-semibold text-foreground">
                <BlurText text="RAAMP ORACLE INTERFACE" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                  // AI MARKETING CO-PILOT // INSIGHTS // DIAGNOSTICS // TROUBLESHOOTING
              </p>
            </div>
          </div>
        </Reveal>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Interactive Chat Window - Terminal Style */}
          <Reveal variant="fadeInUp" delay={0.2} className="lg:col-span-2">
            <HolographicCard className="p-0 h-[600px] flex flex-col overflow-hidden border-primary/30">
              <div className="p-4 border-b border-border/50 bg-background/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-primary" />
                  <span className="text-xs font-mono text-primary tracking-widest">
                    {session ? `SESSION: ${session.slice(-8).toUpperCase()}` : 'TERMINAL_READY'}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground/80 hover:text-foreground" onClick={handleReset} title="Reset Session">
                    <RefreshCw className="w-3 h-3" />
                  </Button>
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-red-500/50" />
                    <div className="w-2 h-2 rounded-full bg-amber-500/50" />
                    <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
                  </div>
                </div>
              </div>

              <div ref={scrollRef} className="flex-1 bg-background/80 p-6 overflow-y-auto space-y-6 font-mono relative scroller-hide">
                {/* Scanline Overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,255,0,0.06))] z-0 pointer-events-none bg-[length:100%_4px,3px_100%]" />

                {/* Empty State */}
                {history.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-white/30 z-10 relative">
                    <Cpu className="w-12 h-12 mb-4 opacity-50" />
                    <p className="text-sm font-mono text-center max-w-sm">
                      INITIALIZING AI CORE...<br />
                      READY FOR QUERY.
                    </p>
                  </div>
                )}

                <AnimatePresence mode="popLayout">
                  {history.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: msg.role === 'assistant' ? -20 : 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`flex gap-4 relative z-10 ${msg.role === 'user' ? 'justify-end' : ''}`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="w-8 h-8 rounded bg-primary/10 border border-primary/30 flex items-center justify-center flex-shrink-0 mt-1">
                          <Zap className="w-4 h-4 text-primary" />
                        </div>
                      )}

                      <div className={`flex-1 max-w-[85%]`}>
                        <div className={`text-[10px] mb-1 opacity-70 ${msg.role === 'user' ? 'text-muted-foreground/80 text-right' : 'text-primary'}`}>
                          {msg.role === 'assistant' ? 'SYSTEM_AI' : 'USER_COMMAND'}
                        </div>
                        <div className={`p-4 text-sm shadow-[0_0_15px_rgba(0,224,208,0.05)] ${msg.role === 'assistant'
                          ? 'bg-primary/5 border border-primary/20 rounded-tr-lg rounded-br-lg rounded-bl-lg text-white/90'
                          : 'bg-foreground/10 border border-border/80 rounded-tl-lg rounded-bl-lg rounded-br-lg text-foreground'
                          }`}>
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex gap-4 relative z-10"
                  >
                    <div className="w-8 h-8 rounded bg-primary/10 border border-primary/30 flex items-center justify-center flex-shrink-0 mt-1">
                      <Zap className="w-4 h-4 text-primary animate-pulse" />
                    </div>
                    <div className="flex-1">
                      <div className="text-[10px] text-primary mb-1 opacity-70">SYSTEM_AI</div>
                      <div className="bg-primary/5 border border-primary/20 p-4 rounded-tr-lg rounded-br-lg rounded-bl-lg text-sm text-white/90 w-fit">
                        <div className="flex gap-1">
                          <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <span className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Speaking indicator */}
                {isPlaying && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex justify-start relative z-10"
                  >
                    <div className="bg-primary/10 border border-primary/30 rounded-full px-3 py-1 flex items-center gap-2">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                      </span>
                      <span className="text-[10px] font-mono text-primary uppercase tracking-widest animate-pulse">Oracle is speaking...</span>
                    </div>
                  </motion.div>
                )}
              </div>

              <div className="p-4 bg-background/60 border-t border-border/50 flex gap-2 relative z-20">
                <Button
                  onClick={toggleSpeechRecognition}
                  disabled={isLoading}
                  variant="ghost"
                  className={`h-10 w-10 p-0 rounded-full border border-border/50 ${isListening ? 'text-red-500 bg-red-500/10' : 'text-primary hover:bg-primary/10'}`}
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
                <div className="flex-1 relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-primary font-mono animate-pulse">{'>'}</span>
                  <Input
                    placeholder={isListening ? "LISTENING..." : "ENTER COMMAND..."}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyPress}
                    disabled={isLoading}
                    className="bg-card border-border/50 pl-8 font-mono text-sm focus:border-primary/50 focus:ring-primary/20 h-10"
                  />
                </div>
                <Button onClick={handleSendMessage} disabled={isLoading || !message.trim()} className="bg-primary text-primary-foreground hover:bg-primary/80 font-bold h-10 w-10 p-0">
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
                </Button>
              </div>
            </HolographicCard>
          </Reveal>
        </div>

        {/* Right Column - Guidance & Actions */}
        <div className="space-y-6">
          {/* Contextual Guidance */}
          <Reveal variant="fadeInUp" delay={0.3}>
            <HolographicCard className="p-6">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2 font-heading font-semibold text-foreground">
                <Lightbulb className="w-5 h-5 text-primary" />
                CONTEXTUAL GUIDANCE
              </h3>
              <p className="text-xs text-muted-foreground mb-4 font-mono">
                    // PROACTIVE INTELLIGENCE FEED
              </p>

              <motion.div
                className="space-y-3"
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
              >
                <motion.div variants={fadeInUp} className="p-3 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors">
                  <h4 className="font-bold text-xs mb-2 text-primary font-mono uppercase">Current Context: {location.pathname.split('/').pop()?.replace('-', ' ') || 'Dashboard'}</h4>
                  <p className="text-[10px] text-muted-foreground font-mono leading-relaxed">
                    SYSTEM ACTIVE. ANALYZING REAL-TIME DATA FROM THIS MODULE.
                  </p>
                </motion.div>

                <motion.div variants={fadeInUp} className="p-3 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors">
                  <h4 className="font-bold text-xs mb-2 flex items-center gap-2 text-amber-400 font-mono uppercase">
                    <Lightbulb className="w-3 h-3" />
                    AI Optimization Tip
                  </h4>
                  <p className="text-[10px] text-muted-foreground font-mono leading-relaxed">
                    ASK RAAMP ASSISTANT TO "ANALYZE PERFORMANCE" FOR DEEPER INSIGHTS INTO THIS MODULE.
                  </p>
                </motion.div>
              </motion.div>
            </HolographicCard>
          </Reveal>

          {/* Quick Actions */}
          <Reveal variant="fadeInUp" delay={0.4}>
            <HolographicCard className="p-6">
              <h3 className="text-lg font-bold mb-4 font-heading font-semibold text-foreground">QUICK ACTIONS</h3>
              <div className="space-y-2">
                {[
                  { icon: Activity, text: "CAMPAIGN HEALTH SUMMARY" },
                  { icon: AlertCircle, text: "RECENT ALERTS LOG" },
                  { icon: ShieldCheck, text: "BEST PRACTICES PROTOCOL" }
                ].map((action, idx) => (
                  <motion.div key={idx} variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button variant="outline" className="w-full justify-start border-border/50 hover:bg-primary/10 hover:text-primary hover:border-primary/30 font-mono text-xs h-9" size="sm">
                      <action.icon className="w-3 h-3 mr-2" />
                      {action.text}
                    </Button>
                  </motion.div>
                ))}
              </div>
            </HolographicCard>
          </Reveal>
        </div>
      </div>

      {/* Troubleshooting & Diagnostics */}
      <Reveal variant="fadeInUp" delay={0.5}>
        <HolographicCard className="p-6 mt-6">
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 font-heading font-semibold text-foreground">
            <AlertCircle className="w-6 h-6 text-primary" />
            SYSTEM DIAGNOSTICS & REPAIR
          </h2>
          <p className="text-xs text-muted-foreground mb-6 font-mono">
                // RUN HEALTH CHECKS // EXECUTE REPAIR PROTOCOLS
          </p>

          <motion.div
            className="grid md:grid-cols-2 gap-4"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {diagnostics.map((item, idx) => (
              <motion.div key={idx} variants={fadeInUp}>
                <motion.div
                  variants={hoverLift}
                  initial="rest"
                  whileHover="hover"
                  className={`p-4 bg-card rounded border ${item.border} hover:bg-foreground/5 transition-all group`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className={`font-bold text-xs font-mono uppercase ${item.color}`}>{item.name}</h3>
                    <Badge variant={item.variant} className="font-mono text-[10px]">
                      {item.status}
                    </Badge>
                  </div>
                  {item.message && (
                    <div className="mb-3 text-[10px] font-mono text-muted-foreground/80 bg-foreground/5 p-2 rounded">
                      {item.status === 'SUCCESS' && <CheckCircle className="w-3 h-3 inline mr-1 text-green-500" />}
                      {item.status === 'FAILED' && <XCircle className="w-3 h-3 inline mr-1 text-red-500" />}
                      {item.message}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <motion.div className="flex-1" variants={hoverScale} whileTap="tap">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={runningCheckId !== null}
                        onClick={() => handleRunDiagnostic(item.id)}
                        className="w-full border-border/50 text-[10px] font-mono h-8 hover:bg-foreground/10"
                      >
                        {runningCheckId === item.id ? (
                          <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                        ) : (
                          <Play className="w-3 h-3 mr-1" />
                        )}
                        {runningCheckId === item.id ? "SCANNING..." : "RUN CHECK"}
                      </Button>
                    </motion.div>
                    <motion.div className="flex-1" variants={hoverScale} whileTap="tap">
                      <Button size="sm" disabled={item.status !== "FAILED"} className="w-full bg-primary/10 text-primary border border-primary/50 hover:bg-primary hover:text-primary-foreground text-[10px] font-mono h-8">
                        INITIATE FIX
                      </Button>
                    </motion.div>
                  </div>
                </motion.div>
              </motion.div>
            ))}
          </motion.div>
        </HolographicCard>
      </Reveal>
    </Layout>
  );
};

export default RAAMPAssistant;
