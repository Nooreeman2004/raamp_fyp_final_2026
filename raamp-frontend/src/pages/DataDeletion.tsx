import { useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp } from "@/utils/animations";

export default function DataDeletion() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <Reveal variant="fadeIn" delay={0.1}>
            <Link
              to="/privacy"
              className="text-primary hover:text-primary/80 transition-colors mb-4 inline-block"
            >
              ← Back to Privacy Policy
            </Link>
          </Reveal>
          <Reveal variant="fadeInUp" delay={0.2}>
            <h1 className="text-4xl font-bold text-foreground mb-2">Data Deletion Instructions</h1>
          </Reveal>
          <Reveal variant="fadeInUp" delay={0.3}>
            <p className="text-gray-400">Effective Date: 21 April 2026</p>
          </Reveal>
        </div>

        <motion.div
          className="bg-foreground/5 backdrop-blur-lg rounded-2xl p-8 space-y-8 text-gray-200"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">How to request deletion</h2>
            <p className="leading-relaxed">
              You can request deletion of your RAAMP account and associated personal data by email.
            </p>
            <div className="mt-4 p-4 bg-foreground/5 rounded-lg space-y-2">
              <p className="text-foreground font-semibold">Email</p>
              <p className="text-primary">malik.noor.eman@gmail.com</p>
              <p className="text-foreground font-semibold mt-3">Subject (required)</p>
              <p className="text-primary">RAAMP Data Deletion Request</p>
              <p className="text-foreground font-semibold mt-3">Include (required)</p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Your RAAMP account email</li>
                <li>Your full name (as shown in RAAMP)</li>
                <li>A short request: “Please delete my RAAMP account and associated data.”</li>
              </ul>
            </div>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">What we delete</h2>
            <ul className="list-disc list-inside ml-4 space-y-2">
              <li>RAAMP account profile data</li>
              <li>Connected platform settings stored in RAAMP</li>
              <li>Stored webhook/audit records associated with your account (where feasible)</li>
            </ul>
            <p className="leading-relaxed mt-4">
              If you connected Instagram/Facebook via Meta, you can also remove RAAMP’s access from Meta’s settings and
              disconnect the integration inside RAAMP.
            </p>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">What we may retain</h2>
            <p className="leading-relaxed">
              We may retain limited information if required for security, fraud prevention, or legal compliance. Where
              possible, retained data is minimized and access-restricted.
            </p>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">Response timeline</h2>
            <p className="leading-relaxed">We aim to respond within 7–14 days after verifying the request.</p>
          </motion.section>
        </motion.div>
      </div>
    </div>
  );
}

