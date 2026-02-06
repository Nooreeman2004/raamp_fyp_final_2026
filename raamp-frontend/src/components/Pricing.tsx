import { Link } from "react-router-dom";
import { PricingCard3D } from "@/components/ui/pricing-card-3d";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeIn } from "@/utils/animations";
import { MaskedTextReveal } from "@/components/ui/masked-text-reveal";

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
        <div className="text-center mb-16 flex flex-col items-center">
          <Reveal variant="blurInUp">
            <MaskedTextReveal
              text="Flexible Pricing for RAAMP"
              className="text-4xl md:text-5xl font-bold mb-4 font-bebas tracking-wide justify-center"
              tag="h2"
            />
          </Reveal>
          <Reveal variant="fadeIn" delay={0.2}>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-mono">
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
          <Link to="/dashboard/billing" className="block h-full">
            <PricingCard3D
              title="Pay-As-You-Go"
              features={[
                "Fixed-rate pricing with no upfront costs.",
                "Cancel anytime with monthly billing.",
                "Perfect for small to medium businesses."
              ]}
            />
          </Link>

          {/* Credits Model Card */}
          <Link to="/dashboard/billing" className="block h-full">
            <PricingCard3D
              title="Credits Model"
              features={[
                "Discounted tiered pricing with a $2,500 credit minimum.",
                "Credits are fully refundable and do not expire.",
                "Ideal for high-volume enterprise users."
              ]}
            />
          </Link>

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