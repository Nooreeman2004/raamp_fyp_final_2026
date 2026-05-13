import { motion, useAnimationControls } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import Reveal from "@/components/ui/Reveal";
import {
  TrendingUp,
  Sparkles,
  MapPin,
  Images,
  Calendar,
  CalendarDays,
  ShieldCheck,
  FileText,
  MessageSquare,
  AlertTriangle,
  FlaskConical,
  LayoutDashboard
} from "lucide-react";

const modules = [
  {
    title: "Geo-Intent Mapping",
    description: "Identify hyper-local audience intent and target with precision based on geographic behavior patterns.",
    icon: MapPin,
  },
  {
    title: "Creative Studio",
    description: "Generate high-performing ad creatives at scale with AI-powered text and image generation.",
    icon: Sparkles,
  },
  {
    title: "Asset Library",
    description: "Centralized repository for all your marketing assets with smart organization and quick access.",
    icon: Images,
  },
  {
    title: "Smart Scheduling",
    description: "AI-optimized post scheduling that maximizes engagement across all your social channels.",
    icon: Calendar,
  },
  {
    title: "Campaign Planner",
    description: "Plan, organize, and execute multi-channel campaigns with intelligent automation.",
    icon: CalendarDays,
  },
  {
    title: "Trend Arbitrage",
    description: "Capitalize on emerging trends before your competition with real-time trend detection.",
    icon: TrendingUp,
  },
  {
    title: "Approvals Workflow",
    description: "Streamlined content approval process with team collaboration and version control.",
    icon: ShieldCheck,
  },
  {
    title: "Smart Drafts",
    description: "Never lose creative work with auto-saved drafts and intelligent content suggestions.",
    icon: FileText,
  },
  {
    title: "Auto Replies",
    description: "AI-powered automated responses that maintain your brand voice across all interactions.",
    icon: MessageSquare,
  },
  {
    title: "Social Moderation",
    description: "Automated comment filtering and threat detection to protect your brand reputation.",
    icon: AlertTriangle,
  },
  {
    title: "The Lab (A/B Testing)",
    description: "Experiment with creative variations and let AI identify winning combinations.",
    icon: FlaskConical,
  },
  {
    title: "Unified Dashboard",
    description: "All-in-one analytics dashboard with real-time insights and actionable intelligence.",
    icon: LayoutDashboard,
  }
];

const Modules = () => {
  const [isPaused, setIsPaused] = useState(false);

  // Duplicate modules for seamless loop
  const extendedModules = [...modules, ...modules];

  return (
    <section className="py-24 bg-card/30 relative overflow-hidden">
      {/* Background gradient orbs */}
      <div className="absolute inset-0 -z-10">
        <motion.div 
          className="absolute top-20 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl"
          animate={{ 
            x: [0, 100, 0],
            y: [0, -50, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div 
          className="absolute bottom-20 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl"
          animate={{ 
            x: [0, -100, 0],
            y: [0, 50, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <div className="container mx-auto px-4 mb-16 text-center">
        <Reveal variant="blurInUp">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Everything You Need to Market,{" "}
              <span className="text-primary">
                In One Autonomous Platform
              </span>
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              12 powerful AI-driven modules working together to transform your marketing workflow
            </p>
          </motion.div>
        </Reveal>
      </div>

      {/* Infinite Scroll Animation */}
      <div className="relative">
        {/* Row 1 - Scroll Left */}
        <motion.div
          className="flex gap-6 mb-6"
          animate={{
            x: isPaused ? undefined : [0, -1920]
          }}
          transition={{
            x: {
              duration: 40,
              repeat: Infinity,
              ease: "linear"
            }
          }}
          onHoverStart={() => setIsPaused(true)}
          onHoverEnd={() => setIsPaused(false)}
        >
          {extendedModules.slice(0, 8).map((module, index) => (
            <motion.div
              key={`row1-${index}`}
              className="min-w-[320px] bg-card/80 backdrop-blur-md border border-primary/20 rounded-2xl p-6 hover:border-primary hover:shadow-[0_0_40px_rgba(0,224,208,0.3)] transition-all duration-300"
              whileHover={{ y: -10, scale: 1.05 }}
            >
              <motion.div
                className="w-14 h-14 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center mb-4"
                whileHover={{ rotate: 360, scale: 1.1 }}
                transition={{ duration: 0.6 }}
              >
                <module.icon className="w-7 h-7 text-primary drop-shadow-[0_0_10px_rgba(0,224,208,0.5)]" />
              </motion.div>
              
              <h3 className="text-xl font-bold mb-2 text-primary">
                {module.title}
              </h3>
              
              <p className="text-sm text-muted-foreground leading-relaxed">
                {module.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* Row 2 - Scroll Right */}
        <motion.div
          className="flex gap-6"
          animate={{
            x: isPaused ? undefined : [-1920, 0]
          }}
          transition={{
            x: {
              duration: 40,
              repeat: Infinity,
              ease: "linear"
            }
          }}
          onHoverStart={() => setIsPaused(true)}
          onHoverEnd={() => setIsPaused(false)}
        >
          {extendedModules.slice(4, 12).map((module, index) => (
            <motion.div
              key={`row2-${index}`}
              className="min-w-[320px] bg-card/80 backdrop-blur-md border border-primary/20 rounded-2xl p-6 hover:border-primary hover:shadow-[0_0_40px_rgba(0,224,208,0.3)] transition-all duration-300"
              whileHover={{ y: -10, scale: 1.05 }}
            >
              <motion.div
                className="w-14 h-14 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center mb-4"
                whileHover={{ rotate: -360, scale: 1.1 }}
                transition={{ duration: 0.6 }}
              >
                <module.icon className="w-7 h-7 text-primary drop-shadow-[0_0_10px_rgba(0,224,208,0.5)]" />
              </motion.div>
              
              <h3 className="text-xl font-bold mb-2 text-primary">
                {module.title}
              </h3>
              
              <p className="text-sm text-muted-foreground leading-relaxed">
                {module.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default Modules;