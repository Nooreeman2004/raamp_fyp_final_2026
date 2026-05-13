import { PricingCard3D } from "@/components/ui/pricing-card-3d";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeIn } from "@/utils/animations";
import { MaskedTextReveal } from "@/components/ui/masked-text-reveal";

const Pricing = () => {
  return (
    <section id="pricing" className="relative py-24 overflow-hidden">
      {/* Background gradient */}
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

      {/* Animated gradient orbs */}
      <motion.div 
        className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px] -z-10"
        animate={{ 
          x: [0, 50, 0],
          y: [0, -30, 0],
          scale: [1, 1.2, 1]
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div 
        className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px] -z-10"
        animate={{ 
          x: [0, -50, 0],
          y: [0, 30, 0],
          scale: [1, 1.3, 1]
        }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="container relative z-10 mx-auto px-4">
        <div className="text-center mb-16 flex flex-col items-center">
          <Reveal variant="blurInUp">
            <h2 className="text-5xl md:text-6xl font-extrabold mb-6 text-foreground">
              Flexible Pricing for <span className="text-primary font-black">RAAMP</span>
            </h2>
          </Reveal>
          <Reveal variant="fadeIn" delay={0.2}>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto font-medium">
              Choose the plan that fits your business needs and <span className="text-primary font-semibold">scale infinitely</span>.
            </p>
          </Reveal>
        </div>

        {/* Staggered Grid — pt-6 gives room for the "Most Popular" badge */}
        <motion.div
          className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto pt-16 pb-12"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
        >
          {/* Free Plan */}
          <PricingCard3D
            title="Free"
            price="$0"
            features={[
              "Create up to 5 advertisements",
              "Access basic templates",
              "Basic AI generation",
              "Basic analytics",
              "Standard email support",
            ]}
          />

          {/* Pro Plan */}
          <PricingCard3D
            title="Pro"
            price="$10"
            isPopular={true}
            features={[
              "Up to 50 ads per month",
              "Premium templates",
              "Faster AI generation",
              "Advanced editing tools",
              "Campaign management",
              "Advanced analytics dashboard",
              "Priority email support",
            ]}
          />

          {/* Premium Plan */}
          <PricingCard3D
            title="Premium"
            price="$25"
            features={[
              "Unlimited advertisements",
              "Unlimited ad credits",
              "All templates",
              "Advanced AI generation",
              "Campaign performance insights",
              "Team collaboration",
              "API access",
              "24/7 priority support",
            ]}
          />
        </motion.div>
      </div>

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