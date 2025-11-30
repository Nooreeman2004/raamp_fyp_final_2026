import { Search, Sparkles, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverLift, zoomIn } from "@/utils/animations";

const steps = [
  {
    icon: Search,
    title: "Detect Geo-Intent",
    description: "Leverage advanced AI to identify and analyze real-time geo-intent signals, uncovering hyper-local market opportunities you're missing",
  },
  {
    icon: Sparkles,
    title: "Generate & Test",
    description: "Automatically create, test, and optimize campaign variations with predictive analytics, ensuring maximum impact for every ad dollar",
  },
  {
    icon: TrendingUp,
    title: "Explain & Iterate",
    description: "Receive clear, actionable insights into campaign performance, continuously refining strategies for sustained growth and superior ROI",
  },
];

const HowItWorks = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="container mx-auto px-4">
        
        {/* Header with Blur Effect */}
        <div className="text-center mb-16">
          <Reveal variant="blurInUp">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              How RAAMP Works: The{" "}
              <span className="text-primary">Autonomous Optimization Loop</span>
            </h2>
          </Reveal>
        </div>

        {/* Staggered Grid Container */}
        <motion.div 
          className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto relative"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
        >
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div 
                key={index} 
                className="relative"
                variants={fadeInUp} // Controlled by staggerContainer parent
              >
                <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                  <Card className="card-shadow bg-card/50 backdrop-blur-sm border-primary/20 p-8 h-full hover:border-primary/40 transition-all duration-300">
                    <div className="flex flex-col items-center text-center space-y-4">
                      
                      {/* Icon Zoom Entrance */}
                      <Reveal variant="zoomIn" delay={0.2 + (index * 0.1)}>
                        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center breathing-glow">
                          <Icon className="w-8 h-8 text-primary" />
                        </div>
                      </Reveal>

                      <h3 className="text-2xl font-bold">{step.title}</h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </Card>
                </motion.div>              
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
};

export default HowItWorks;