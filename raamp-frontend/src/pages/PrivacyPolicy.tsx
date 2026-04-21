import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, fadeIn } from "@/utils/animations";

export default function PrivacyPolicy() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background">
      <div className="max-w-4xl mx-auto px-6 py-12">

        {/* Header */}
        <div className="mb-8">
          <Reveal variant="fadeIn" delay={0.1}>
            <Link
              to="/signup"
              className="text-primary hover:text-primary/80 transition-colors mb-4 inline-block"
            >
              ← Back to Signup
            </Link>
          </Reveal>
          <Reveal variant="fadeInUp" delay={0.2}>
            <h1 className="text-4xl font-bold text-foreground mb-2">Privacy Policy</h1>
          </Reveal>
          <Reveal variant="fadeIn" delay={0.3}>
            <p className="text-gray-400">Effective Date: 21 April 2026</p>
          </Reveal>
        </div>

        {/* Content Container - Staggers the sections inside */}
        <motion.div
          className="bg-foreground/5 backdrop-blur-lg rounded-2xl p-8 space-y-8 text-gray-200"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">1. Introduction</h2>
            <p className="leading-relaxed">
              This Privacy Policy explains how RAAMP (“we”, “our”, “us”) collects, uses, and protects information when
              you use the RAAMP application (the “Service”).
            </p>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">2. Information We Collect</h2>
            <p className="leading-relaxed">We collect information in the following categories.</p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-foreground">Account data:</strong> Name and email address you provide, and a securely stored password hash.</li>
              <li><strong className="text-foreground">App usage data:</strong> Basic logs about actions in the Service (e.g., feature usage, timestamps, error diagnostics).</li>
              <li><strong className="text-foreground">Connected platform data (optional):</strong> If you connect Instagram/Facebook, we store identifiers and tokens required to provide the integration.</li>
            </ul>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">3. How We Use Your Data</h2>
            <p className="leading-relaxed">
              We use data to operate the Service, keep it secure, and provide connected-platform features you enable.
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-foreground">Account & authentication:</strong> sign-in, account security, and access control.</li>
              <li><strong className="text-foreground">Integrations (optional):</strong> receiving Instagram/Facebook comment events via webhooks and sending replies when you enable auto-replies.</li>
              <li><strong className="text-foreground">Reliability & security:</strong> monitoring, debugging, and abuse prevention.</li>
            </ul>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">4. Data Storage, Security & Retention</h2>
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.1 Security</h3>
            <p className="leading-relaxed">
              We use reasonable safeguards such as access controls and secure storage practices. No system is completely
              secure, and we cannot guarantee absolute security.
            </p>
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.2 Retention</h3>
            <p className="leading-relaxed">Where possible, we use specific retention periods:</p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-foreground">Account data:</strong> retained while your account is active; deleted within 30 days after verified deletion request.</li>
              <li><strong className="text-foreground">Integration tokens:</strong> retained while the integration is connected; deleted when you disconnect or request deletion.</li>
              <li><strong className="text-foreground">Webhook/audit records (e.g., auto-reply drafts/logs):</strong> retained up to 90 days for troubleshooting and accountability.</li>
              <li><strong className="text-foreground">Operational logs:</strong> retained up to 30 days for reliability and security monitoring.</li>
            </ul>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">5. Data Sharing & Third Parties</h2>
            <p className="leading-relaxed">
              We do not sell your personal data. We may share data with service providers only to operate the Service, or
              when required by law.
            </p>
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">Third-party providers used</h3>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-foreground">Meta Platforms, Inc. (Facebook/Instagram APIs & Webhooks):</strong> integrations for comment events and replies.</li>
              <li><strong className="text-foreground">OpenAI:</strong> AI text generation/analysis (when enabled in your RAAMP features).</li>
              <li><strong className="text-foreground">Pinecone:</strong> vector database used for retrieval features (when enabled).</li>
              <li><strong className="text-foreground">Cloudinary:</strong> media storage/processing (when enabled).</li>
              <li><strong className="text-foreground">MongoDB:</strong> database storage.</li>
              <li><strong className="text-foreground">ngrok (development/testing only):</strong> webhook testing tunnel.</li>
            </ul>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">6. Data access & deletion requests</h2>
            <p className="leading-relaxed">
              You can request access to your data or request deletion. See our dedicated page:
              <span className="ml-2">
                <Link to="/data-deletion" className="text-primary hover:text-primary/80 transition-colors">
                  Data Deletion Instructions
                </Link>
              </span>
              .
            </p>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">7. Changes to this policy</h2>
            <p className="leading-relaxed">
              We may update this policy. We will update the effective date on this page when changes are made.
            </p>
          </motion.section>

          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">8. Contact</h2>
            <p className="leading-relaxed">
              For privacy questions, contact:
            </p>
            <div className="mt-4 p-4 bg-foreground/5 rounded-lg">
              <p className="text-primary">Email: malik.noor.eman@gmail.com</p>
            </div>
          </motion.section>

          {/* Footer */}
          <motion.div variants={fadeInUp} className="border-t border-gray-700 pt-6 mt-8">
            <p className="text-sm text-gray-400">
              By using RAAMP, you acknowledge that you have read, understood, and agree to this Privacy Policy and
              our data processing practices.
            </p>
          </motion.div>
        </motion.div>

        {/* Back to Top */}
        <Reveal variant="fadeIn" delay={0.5} className="mt-8 text-center">
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="text-primary hover:text-primary transition-colors"
          >
            ↑ Back to Top
          </button>
        </Reveal>
      </div>
    </div>
  );
}