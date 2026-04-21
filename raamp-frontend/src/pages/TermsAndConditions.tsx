import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, fadeIn } from "@/utils/animations";

export default function TermsAndConditions() {
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
              className="text-primary hover:text-primary transition-colors mb-4 inline-block"
            >
              ← Back to Signup
            </Link>
          </Reveal>
          <Reveal variant="fadeInUp" delay={0.2}>
            <h1 className="text-4xl font-bold text-foreground mb-2">Terms & Conditions</h1>
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

          {/* Section 1 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">1. Acceptance of Terms</h2>
            <p className="leading-relaxed">
              By creating an account, accessing, or using RAAMP (Revolutionary AI-Powered Autonomous Marketing Platform),
              you agree to be bound by these Terms & Conditions and our Privacy Policy. If you are using RAAMP on behalf
              of a business or other legal entity, you represent and warrant that you have the authority to bind that
              entity to these terms. In such cases, "you" and "your" refer to that entity.
            </p>
            <p className="leading-relaxed mt-4">
              If you do not agree to these terms, you must not access or use RAAMP. We reserve the right to update these
              terms at any time, and your continued use of the platform constitutes acceptance of any modifications.
            </p>
          </motion.section>

          {/* Section 2 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">2. Service Scope & Limitations</h2>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">2.1 AI-Driven Automation</h3>
            <p className="leading-relaxed">
              RAAMP includes AI-assisted features intended to help with marketing tasks and automation. Outputs may be
              inaccurate or incomplete and should be reviewed by you.
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>You are responsible for decisions you make using the Service.</li>
              <li>RAAMP does not guarantee results or outcomes.</li>
            </ul>
            <p className="leading-relaxed mt-4">
              <strong className="text-foreground">Important Disclaimer:</strong> All AI-generated outputs, predictions, and
              recommendations are automated and data-driven. RAAMP does not guarantee specific financial outcomes,
              performance metrics, or results including but not limited to: Return on Ad Spend (ROAS), lead volume,
              conversion rates, revenue growth, or campaign success. Users acknowledge that marketing outcomes depend
              on multiple factors beyond RAAMP's control, including market conditions, competition, product quality,
              and user implementation.
            </p>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">2.2 Third-Party API Dependencies</h3>
            <p className="leading-relaxed">
              Core RAAMP features rely on external APIs and third-party services, including but not limited to:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Google Maps API for location-based services and geolocation targeting</li>
              <li>Instagram API for social media integration and trend analysis</li>
              <li>Other marketing platform APIs and data sources</li>
            </ul>
            <p className="leading-relaxed mt-4">
              By using RAAMP, you agree to comply with the terms of service, usage policies, and guidelines of these
              third-party platforms. RAAMP is not responsible for:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Rate limits, usage restrictions, or policy changes imposed by external APIs</li>
              <li>Service outages, downtime, or performance issues of third-party providers</li>
              <li>Accuracy, completeness, or freshness of data provided by external APIs</li>
              <li>Changes to API availability, pricing, or functionality</li>
              <li>Compliance violations resulting from your use of third-party platforms</li>
            </ul>
          </motion.section>

          {/* Section 3 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">3. User Responsibilities</h2>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">3.1 Content Ownership & Compliance</h3>
            <p className="leading-relaxed">
              Users are solely responsible for all content created, uploaded, or generated through RAAMP, including:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Marketing creatives (images, videos, graphics)</li>
              <li>Campaign copy, captions, and messaging</li>
              <li>Offers, promotions, and pricing information</li>
              <li>AI-generated content based on user inputs and preferences</li>
              <li>Brand assets (logos, colors, tone guidelines)</li>
            </ul>
            <p className="leading-relaxed mt-4">
              You represent and warrant that you have all necessary rights, licenses, consents, and permissions for any
              content you provide to RAAMP. You are responsible for ensuring your content and campaigns comply with:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>All applicable laws and regulations (including GDPR, CCPA, and other data protection laws)</li>
              <li>Advertising platform policies (Facebook, Instagram, Google Ads, etc.)</li>
              <li>Intellectual property rights and trademark laws</li>
              <li>Industry-specific regulations (health, finance, legal, etc.)</li>
              <li>Truth in advertising and consumer protection standards</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">3.2 Ethical Data Use & Prohibited Activities</h3>
            <p className="leading-relaxed">
              Users must use RAAMP ethically and in accordance with these terms. The following activities are strictly prohibited:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Unauthorized scraping, data extraction, or reverse engineering of RAAMP</li>
              <li>Attempting to access, modify, or interfere with RAAMP's systems, databases, or infrastructure</li>
              <li>Using RAAMP to transmit spam, malware, or malicious content</li>
              <li>Violating third-party rights or terms of service</li>
              <li>Creating false or misleading campaigns</li>
              <li>Sharing account credentials with unauthorized parties</li>
              <li>Using RAAMP for illegal, fraudulent, or deceptive purposes</li>
            </ul>
            <p className="leading-relaxed mt-4">
              RAAMP reserves the right to suspend or terminate accounts that violate these terms or engage in prohibited activities.
            </p>
          </motion.section>

          {/* Section 4 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">4. Intellectual Property Rights</h2>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.1 RAAMP Intellectual Property</h3>
            <p className="leading-relaxed">
              All aspects of the RAAMP platform are proprietary and protected by intellectual property laws. This includes:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>AI algorithms, machine learning models, and neural network architectures</li>
              <li>TensorFlow models and Bayesian analytical methods</li>
              <li>Generative Creative Studio technology and AI image generation systems</li>
              <li>RAAMP Assistant conversational AI and natural language processing</li>
              <li>Hyperlocal targeting algorithms and geolocation scoring systems</li>
              <li>A/B Auto-Optimization Layer and budget allocation logic</li>
              <li>Attribution analytics and performance prediction models</li>
              <li>Platform design, user interface, and user experience elements</li>
              <li>Source code, databases, APIs, and technical infrastructure</li>
              <li>RAAMP brand, logos, trademarks, and trade names</li>
            </ul>
            <p className="leading-relaxed mt-4">
              Users are granted a limited, non-exclusive, non-transferable license to access and use RAAMP solely for
              their marketing purposes. This license does not grant any ownership rights to RAAMP's technology or intellectual property.
            </p>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.2 User Data License</h3>
            <p className="leading-relaxed">
              By using RAAMP, you grant RAAMP a non-exclusive, worldwide, royalty-free, perpetual license to use, process,
              analyze, and store your data for the following purposes:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Operating and providing RAAMP services to you</li>
              <li>Training, improving, and optimizing AI models and algorithms</li>
              <li>Enhancing platform features, predictions, and recommendations</li>
              <li>Conducting aggregate analytics and performance benchmarking</li>
              <li>Developing new features and capabilities</li>
            </ul>
            <p className="leading-relaxed mt-4">
              This license includes campaign data, performance metrics, tone descriptions, brand preferences, creative inputs,
              and engagement analytics. All data used for AI training is anonymized and aggregated to protect user privacy.
              RAAMP will not share your identifiable business data with third parties without your consent, except as required
              by law or specified in our Privacy Policy.
            </p>
          </motion.section>

          {/* Section 5 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">5. Payments</h2>
            <p className="leading-relaxed">
              RAAMP is provided as a final year project demonstration and does not include paid subscriptions or payment
              processing unless explicitly stated in the Service.
            </p>
          </motion.section>

          {/* Section 6 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">6. Limitation of Liability</h2>
            <p className="leading-relaxed">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, RAAMP SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
              CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOST PROFITS, LOST REVENUE, LOST DATA,
              OR BUSINESS INTERRUPTION, ARISING FROM YOUR USE OF OR INABILITY TO USE THE PLATFORM.
            </p>
            <p className="leading-relaxed mt-4">
              RAAMP's total liability for any claims arising from these terms or your use of the platform shall not exceed
              the amount you paid to RAAMP in the three (3) months preceding the claim.
            </p>
          </motion.section>

          {/* Section 7 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">7. Termination</h2>
            <p className="leading-relaxed">
              RAAMP reserves the right to suspend or terminate your account at any time for violations of these Terms,
              fraudulent activity, or any other reason at our sole discretion. Upon termination:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Your access to RAAMP will be immediately revoked</li>
              <li>Active campaigns will be paused or terminated</li>
              <li>You remain responsible for any outstanding fees or charges</li>
              <li>RAAMP may retain your data as required by law or our data retention policies</li>
            </ul>
            <p className="leading-relaxed mt-4">
              You may terminate your account at any time through your account settings or by contacting support.
              Termination does not relieve you of obligations incurred prior to termination.
            </p>
          </motion.section>

          {/* Section 8 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">8. Governing Law & Dispute Resolution</h2>
            <p className="leading-relaxed">
              These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict
              of law principles. Any disputes arising from these Terms or your use of RAAMP shall be resolved through binding
              arbitration, except where prohibited by law.
            </p>
          </motion.section>

          {/* Section 9 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-foreground mb-4">9. Contact Information</h2>
            <p className="leading-relaxed">
              If you have questions about these Terms & Conditions, please contact us at:
            </p>
            <div className="mt-4 p-4 bg-foreground/5 rounded-lg">
              <p className="font-semibold text-foreground">RAAMP Support</p>
              <p className="text-primary">Email: malik.noor.eman@gmail.com</p>
            </div>
          </motion.section>

          {/* Footer */}
          <motion.div variants={fadeInUp} className="border-t border-gray-700 pt-6 mt-8">
            <p className="text-sm text-gray-400">
              By using RAAMP, you acknowledge that you have read, understood, and agree to be bound by these Terms & Conditions.
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