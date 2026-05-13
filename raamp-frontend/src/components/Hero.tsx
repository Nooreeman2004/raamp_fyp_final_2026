import { ArrowRight, Sparkles, Zap, Globe, BarChart3, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { HolographicCard } from "@/components/ui/holographic-card";
import { MagneticButton } from "@/components/ui/magnetic-button";

const Hero = () => {
  return (
    <section className="relative min-h-[100vh] flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 overflow-x-hidden pt-20 pb-32">

      {/* Background Elements */}
      <div className="absolute inset-0 -z-10 bg-background/50" />
      
      {/* Animated Gradient Orbs */}
      <motion.div 
        className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-gradient-to-r from-primary/20 to-cyan-400/20 blur-[100px] -z-10"
        animate={{ 
          x: [0, 100, 0],
          y: [0, 50, 0],
          scale: [1, 1.2, 1]
        }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div 
        className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-gradient-to-l from-teal-400/20 to-primary/20 blur-[100px] -z-10"
        animate={{ 
          x: [0, -80, 0],
          y: [0, -40, 0],
          scale: [1, 1.3, 1]
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Background Ticker Letters */}
      <div className="absolute inset-0 -z-20 overflow-hidden pointer-events-none select-none">
        <motion.div 
          className="absolute top-[10%] left-0 right-0 text-[clamp(8rem,20vw,16rem)] font-black tracking-tighter leading-none opacity-[0.08] whitespace-nowrap"
          animate={{ x: [0, -1000] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
          <div className="flex gap-8">
            <span className="text-foreground">AUTONOMOUS</span>
            <span className="text-foreground">MARKETING</span>
            <span className="text-foreground">AUTONOMOUS</span>
            <span className="text-foreground">MARKETING</span>
          </div>
        </motion.div>
        <motion.div 
          className="absolute top-[35%] left-0 right-0 text-[clamp(8rem,20vw,16rem)] font-black tracking-tighter leading-none opacity-[0.08] whitespace-nowrap"
          animate={{ x: [-1000, 0] }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        >
          <div className="flex gap-8">
            <span className="text-foreground">INTELLIGENCE</span>
            <span className="text-foreground">AUTOMATION</span>
            <span className="text-foreground">INTELLIGENCE</span>
            <span className="text-foreground">AUTOMATION</span>
          </div>
        </motion.div>
        <motion.div 
          className="absolute top-[60%] left-0 right-0 text-[clamp(8rem,20vw,16rem)] font-black tracking-tighter leading-none opacity-[0.08] whitespace-nowrap"
          animate={{ x: [0, -1200] }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        >
          <div className="flex gap-8">
            <span className="text-foreground">AUTOMATION</span>
            <span className="text-foreground">OPTIMIZATION</span>
            <span className="text-foreground">AUTOMATION</span>
            <span className="text-foreground">OPTIMIZATION</span>
          </div>
        </motion.div>
      </div>

      <div className="max-w-5xl mx-auto text-center space-y-8 relative z-10">

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 backdrop-blur-md shadow-[0_0_20px_rgba(0,224,208,0.3)]"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary shadow-[0_0_10px_rgba(0,224,208,0.8)]"></span>
          </span>
          <span className="text-xs font-mono font-medium bg-gradient-to-r from-primary via-cyan-400 to-primary bg-clip-text text-transparent tracking-wider uppercase animate-pulse">
            All Systems Active
          </span>
        </motion.div>

        {/* Main Heading */}
        <motion.div 
          className="space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="flex flex-col items-center justify-center gap-1">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] text-primary">
              Revolutionary AI-Powered
            </h1>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] text-primary/90 font-extrabold">
              Autonomous
            </h1>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] text-primary">
              Marketing Platform
            </h1>
          </div>

          <div className="max-w-2xl mx-auto pt-4">
            <p className="text-lg md:text-xl text-muted-foreground/90 font-medium">
              Leverage advanced <span className="text-primary font-semibold">AI</span> to foresee market trends, automate creative assets, and optimize campaigns across all channels in <span className="text-primary font-semibold">real-time</span>.
            </p>
          </div>
        </motion.div>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
        >
          <Link to="/signup">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              <MagneticButton className="min-w-[200px] h-14 text-lg font-semibold bg-primary text-primary-foreground shadow-[0_0_40px_rgba(0,224,208,0.4),0_8px_16px_rgba(0,0,0,0.3)] hover:shadow-[0_0_60px_rgba(0,224,208,0.6),0_12px_24px_rgba(0,0,0,0.4)] border border-primary/50 hover:border-primary transition-all duration-300">
                <Zap className="w-5 h-5 mr-2" />
                Start Free Trial
              </MagneticButton>
            </motion.div>
          </Link>
          <Link to="/demo">
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              <MagneticButton className="px-8 h-14 text-lg font-medium border-2 border-primary/40 bg-background/80 text-foreground hover:bg-primary/10 hover:border-primary/60 backdrop-blur-md whitespace-nowrap transition-all duration-300 shadow-[0_4px_12px_rgba(0,0,0,0.2)] hover:shadow-[0_0_30px_rgba(0,224,208,0.3),0_8px_16px_rgba(0,0,0,0.3)]">
                View Interactive Demo
                <ArrowRight className="w-4 h-4 ml-2 flex-shrink-0" />
              </MagneticButton>
            </motion.div>
          </Link>
        </motion.div>

        {/* Feature Cards Grid (Reference Style) */}
        <div className="grid md:grid-cols-3 gap-6 pt-16 pb-12 text-left">
          <HolographicCard className="p-6 min-h-[18rem] h-auto group hover:shadow-[0_0_30px_rgba(0,224,208,0.2)] transition-all duration-300">
            <motion.div 
              className="w-12 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-cyan-400/20 flex items-center justify-center mb-4 text-primary"
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <Sparkles className="w-6 h-6 drop-shadow-[0_0_8px_rgba(0,224,208,0.6)]" />
            </motion.div>
            <h3 className="text-xl font-semibold bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent mb-2">AI Optimization</h3>
            <p className="text-foreground/70 text-sm leading-relaxed group-hover:text-foreground/90 transition-colors">
              Autonomous algorithms that adjust bids and targeting in real-time to maximize ROAS.
            </p>
          </HolographicCard>

          <HolographicCard className="p-6 min-h-[18rem] h-auto group hover:shadow-[0_0_30px_rgba(0,224,208,0.2)] transition-all duration-300">
            <motion.div 
              className="w-12 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-cyan-400/20 flex items-center justify-center mb-4 text-primary"
              whileHover={{ scale: 1.1, rotate: -5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <Globe className="w-6 h-6 drop-shadow-[0_0_8px_rgba(0,224,208,0.6)]" />
            </motion.div>
            <h3 className="text-xl font-semibold bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent mb-2">Geo-Targeting</h3>
            <p className="text-foreground/70 text-sm leading-relaxed group-hover:text-foreground/90 transition-colors">
              Pinpoint audiences with hyper-local precision using our proprietary intent mapping.
            </p>
          </HolographicCard>

          <HolographicCard className="p-6 min-h-[18rem] h-auto group hover:shadow-[0_0_30px_rgba(0,224,208,0.2)] transition-all duration-300">
            <motion.div 
              className="w-12 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-cyan-400/20 flex items-center justify-center mb-4 text-primary"
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <BarChart3 className="w-6 h-6 drop-shadow-[0_0_8px_rgba(0,224,208,0.6)]" />
            </motion.div>
            <h3 className="text-xl font-semibold bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent mb-2">Instant Scale</h3>
            <p className="text-foreground/70 text-sm leading-relaxed group-hover:text-foreground/90 transition-colors">
              Launch campaigns across 5+ platforms simultaneously with a single click.
            </p>
          </HolographicCard>
        </div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, y: [0, 10, 0] }}
        transition={{ delay: 2, duration: 2, repeat: Infinity }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 text-muted-foreground/80"
      >
        <div className="flex flex-col items-center gap-2">
          <span className="text-[10px] uppercase tracking-[0.2em]">Scroll</span>
          <ChevronDown className="w-4 h-4" />
        </div>
      </motion.div>

      {/* Grid Floor Effect (Subtle) */}
      <div className="absolute bottom-0 left-0 right-0 h-[40vh] pointer-events-none -z-20 opacity-20">
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,#020B14_100%)]" />
        <div className="w-full h-full bg-[linear-gradient(to_right,#112233_1px,transparent_1px),linear-gradient(to_bottom,#112233_1px,transparent_1px)] bg-[size:4rem_4rem] [transform:perspective(1000px)_rotateX(60deg)] origin-bottom" />
      </div>
    </section>
  );
};

export default Hero;