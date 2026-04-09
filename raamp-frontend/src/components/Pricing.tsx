import { PricingCard3D } from "@/components/ui/pricing-card-3d";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeIn } from "@/utils/animations";
import { MaskedTextReveal } from "@/components/ui/masked-text-reveal";

const Pricing = () => {
  return (
    <section id="pricing" className="relative py-24">
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

      <div className="container relative z-10 mx-auto px-4">
        <div className="text-center mb-16 flex flex-col items-center">
          <Reveal variant="blurInUp">
            <MaskedTextReveal
              text="Flexible Pricing for RAAMP"
              className="text-4xl md:text-5xl font-bold mb-4 font-heading font-semibold justify-center"
              tag="h2"
            />
          </Reveal>
          <Reveal variant="fadeIn" delay={0.2}>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-mono">
              Choose the plan that fits your business needs and scale infinitely.
            </p>
          </Reveal>
        </div>

        {/* Staggered Grid — pt-6 gives room for the "Most Popular" badge */}
        <motion.div
          className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto pt-12 pb-12"
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