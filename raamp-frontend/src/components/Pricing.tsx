import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Check } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, zoomIn, hoverScale, blurInUp, fadeIn } from "@/utils/animations";

const Pricing = () => {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background gradient - Fades in slowly */}
      <motion.div 
        variants={fadeIn}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        transition={{ duration: 1.5 }}
        className="absolute inset-0 bg-gradient-to-br from-card via-background to-card"
      >
        <div className="absolute inset-0 opacity-20" 
             style={{ backgroundImage: 'radial-gradient(circle at 30% 50%, hsl(var(--glow-primary) / 0.15), transparent 70%)' }} 
        />
      </motion.div>

      <div className="container relative z-10 mx-auto px-4">
        <div className="text-center mb-16">
          <Reveal variant="blurInUp">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Flexible Pricing for RAAMP
            </h2>
          </Reveal>
          <Reveal variant="fadeIn" delay={0.2}>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Choose the pricing model that best fits your business needs
            </p>
          </Reveal>
        </div>

        {/* Staggered Grid */}
        <motion.div 
          className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
        >
          {/* Pay-As-You-Go Card */}
          <motion.div variants={zoomIn} className="h-full">
            <Link to="/dashboard/billing" className="block h-full">
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="h-full">
                <Card className="p-8 card-shadow bg-card/70 backdrop-blur-sm border-primary/20 hover:border-primary/40 transition-colors duration-300 group cursor-pointer h-full">
                  <div className="space-y-6">
                    <h3 className="text-3xl font-bold text-primary group-hover:text-primary/90 transition-colors">
                      Pay-As-You-Go
                    </h3>
                    
                    <div className="space-y-4">
                      {[
                        "Fixed-rate pricing with no upfront costs.",
                        "Cancel anytime with monthly billing.",
                        "Perfect for small to medium businesses."
                      ].map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Check className="w-4 h-4 text-primary" />
                          </div>
                          <p className="text-foreground">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              </motion.div>
            </Link>
          </motion.div>

          {/* Credits Model Card */}
          <motion.div variants={zoomIn} className="h-full">
            <Link to="/dashboard/billing" className="block h-full">
               <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="h-full">
                <Card className="p-8 card-shadow bg-card/70 backdrop-blur-sm border-primary/20 hover:border-primary/40 transition-colors duration-300 group cursor-pointer h-full">
                  <div className="space-y-6">
                    <h3 className="text-3xl font-bold text-primary group-hover:text-primary/90 transition-colors">
                      Credits Model
                    </h3>
                    
                    <div className="space-y-4">
                      {[
                        "Discounted tiered pricing with a $2,500 credit minimum.",
                        "Credits are fully refundable and do not expire.",
                        "Ideal for high-volume enterprise users."
                      ].map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Check className="w-4 h-4 text-primary" />
                          </div>
                          <p className="text-foreground">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              </motion.div>
            </Link>
          </motion.div>

        </motion.div>
      </div>

      {/* Decorative bottom line - Expands horizontally */}
      <motion.div 
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: 1 }}
        transition={{ duration: 0.8, ease: "circOut" }}
        className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent origin-center" 
      />
    </section>
  );
};

export default Pricing;