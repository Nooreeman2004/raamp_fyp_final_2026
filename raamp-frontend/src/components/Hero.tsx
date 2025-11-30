import { Button } from "@/components/ui/button";
import { ArrowRight, Play } from "lucide-react";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { hoverScale } from "@/utils/animations";

const Hero = () => {
  const scrollToConsultation = () => {
    const consultationSection = document.getElementById('consultation');
    if (consultationSection) {
      consultationSection.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-24">
      
      {/* Animated background gradient - Fades in slowly */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5 }}
        className="absolute inset-0 bg-gradient-to-br from-background via-card to-background"
      >
        <div className="absolute inset-0 opacity-30" 
             style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, hsl(var(--glow-primary) / 0.15), transparent 50%), radial-gradient(circle at 80% 50%, hsl(var(--glow-secondary) / 0.1), transparent 50%)' }} 
        />
      </motion.div>

      <div className="container relative z-10 mx-auto px-4 text-center">
        <div className="max-w-4xl mx-auto space-y-8">
          
          {/* Title - Premium Blur Effect */}
          <Reveal variant="blurInUp" duration={0.8}>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-tight">
              Revolutionize Local Marketing with{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-primary animate-pulse">
                Autonomous Intelligence
              </span>
            </h1>
          </Reveal>
          
          {/* Subtitle - Fades in slightly later */}
          <Reveal variant="fadeInUp" delay={0.2}>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              RAAMP uses AI to hyper-localize campaigns, optimize spending, and accelerate creative production, 
              delivering unparalleled results for businesses of all sizes
            </p>
          </Reveal>

          {/* Buttons - Interactive Physics */}
          <Reveal variant="fadeInUp" delay={0.4}>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
              
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button 
                  variant="heroCta" 
                  size="lg" 
                  className="group"
                  onClick={scrollToConsultation}
                >
                  Get Started
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </motion.div>

              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button variant="outline" size="lg" className="group border-primary/50 hover:border-primary">
                  <Play className="mr-2 h-5 w-5" />
                  Watch Demo
                </Button>
              </motion.div>
              
            </div>
          </Reveal>

        </div>
      </div>

      {/* Decorative elements */}
      <motion.div 
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1, delay: 0.5 }}
        className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" 
      />
    </section>
  );
};

export default Hero;