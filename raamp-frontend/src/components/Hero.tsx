import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, Zap, Globe, BarChart3, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { BlurText, StaggerText } from "@/components/ui/text-reveal";
import { MaskedTextReveal } from "@/components/ui/masked-text-reveal";
import { HolographicCard } from "@/components/ui/holographic-card";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { ParallaxSection } from "@/components/ui/parallax-section";
import { VelocityScroll } from "@/components/ui/velocity-scroll";

const Hero = () => {
  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 overflow-hidden pt-20">

      {/* Background Elements */}
      <div className="absolute inset-0 -z-10 bg-background/50" />

      {/* Velocity Scroll Background Text */}
      <div className="absolute top-1/2 left-0 w-full -translate-y-1/2 opacity-5 pointer-events-none select-none z-0">
        <VelocityScroll text="AUTONOMOUS MARKETING INTELLIGENCE" />
      </div>

      <div className="max-w-5xl mx-auto text-center space-y-8 relative z-10">

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 backdrop-blur-md"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
          </span>
          <span className="text-xs font-mono font-medium text-primary tracking-wider uppercase">
            All Systems Active
          </span>
        </motion.div>

        {/* Main Heading */}
        <div className="space-y-4">
          <div className="flex flex-col items-center justify-center">
            <MaskedTextReveal
              text="Revolutionary AI-Powered"
              className="text-5xl md:text-7xl font-bold tracking-tight text-primary leading-[1.1] justify-center"
              tag="h1"
            />
            <MaskedTextReveal
              text="Autonomous"
              className="text-5xl md:text-7xl font-bold tracking-tight text-white leading-[1.1] justify-center"
              tag="h1"
              delay={0.3}
            />
            <MaskedTextReveal
              text="Marketing Platform"
              className="text-5xl md:text-7xl font-bold tracking-tight text-primary leading-[1.1] justify-center"
              tag="h1"
              delay={0.5}
            />
          </div>

          <div className="max-w-2xl mx-auto pt-4">
            <StaggerText
              text="Leverage advanced AI to foresee market trends, automate creative assets, and optimize campaigns across all channels in real-time."
              className="text-lg md:text-xl text-muted-foreground justify-center"
              delay={0.6}
            />
          </div>
        </div>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
        >
          <Link to="/signup">
            <MagneticButton className="min-w-[200px] h-14 text-lg font-semibold bg-primary text-primary-foreground shadow-[0_0_30px_rgba(0,224,208,0.4)] hover:shadow-[0_0_50px_rgba(0,224,208,0.6)]">
              <Zap className="w-5 h-5 mr-2" />
              Start Free Trial
            </MagneticButton>
          </Link>
          <Link to="/demo">
            <MagneticButton className="px-8 h-14 text-lg font-medium border border-white/10 bg-white/5 text-white hover:bg-white/10 backdrop-blur-sm whitespace-nowrap">
              View Interactive Demo
              <ArrowRight className="w-4 h-4 ml-2 flex-shrink-0" />
            </MagneticButton>
          </Link>
        </motion.div>

        {/* Feature Cards Grid (Reference Style) */}
        <div className="grid md:grid-cols-3 gap-6 pt-16 text-left">
          <ParallaxSection speed={0.05}>
            <HolographicCard className="p-5 h-55">
              <div className="w-12 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">AI Optimization</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Autonomous algorithms that adjust bids and targeting in real-time to maximize ROAS.
              </p>
            </HolographicCard>
          </ParallaxSection>

          <ParallaxSection speed={0.1}>
            <HolographicCard className="p-5 h-55">
              <div className="w-12 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <Globe className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Geo-Targeting</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Pinpoint audiences with hyper-local precision using our proprietary intent mapping.
              </p>
            </HolographicCard>
          </ParallaxSection>

          <ParallaxSection speed={0.15}>
            <HolographicCard className="p-5 h-55">
              <div className="w-12 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <BarChart3 className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Instant Scale</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Launch campaigns across 5+ platforms simultaneously with a single click.
              </p>
            </HolographicCard>
          </ParallaxSection>
        </div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, y: [0, 10, 0] }}
        transition={{ delay: 2, duration: 2, repeat: Infinity }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 text-white/50"
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