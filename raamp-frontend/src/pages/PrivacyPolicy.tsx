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
            <h1 className="text-4xl font-bold text-white mb-2">Privacy Policy</h1>
          </Reveal>
          <Reveal variant="fadeIn" delay={0.3}>
            <p className="text-gray-400">Last Updated: November 25, 2025</p>
          </Reveal>
        </div>

        {/* Content Container - Staggers the sections inside */}
        <motion.div 
          className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 space-y-8 text-gray-200"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          
          {/* Section 1 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">1. Introduction</h2>
            <p className="leading-relaxed">
              This Privacy Policy explains how RAAMP (Revolutionary AI-Powered Autonomous Marketing Platform) collects, 
              uses, processes, stores, and protects your personal information and business data. We are committed to 
              transparency and protecting your privacy while delivering powerful AI-driven marketing automation.
            </p>
            <p className="leading-relaxed mt-4">
              RAAMP processes various types of data, including business information, customer insights, geolocation data, 
              and third-party integrations. This policy applies to all users of the RAAMP platform, including business 
              owners, marketing professionals, and team members.
            </p>
            <p className="leading-relaxed mt-4">
              By using RAAMP, you consent to the data practices described in this policy. If you do not agree with our 
              privacy practices, please do not use the platform.
            </p>
          </motion.section>

          {/* Section 2 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">2. Information We Collect</h2>
            
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">2.1 User-Provided Information</h3>
            <p className="leading-relaxed">
              When you create an account and use RAAMP, you directly provide us with the following information:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Account Information:</strong> Name, email address, phone number, and securely hashed password</li>
              <li><strong className="text-white">Business Details:</strong> Company name, industry, business type, physical location, target markets, and service areas</li>
              <li><strong className="text-white">Brand Settings:</strong> Logo files, brand colors, tone of voice preferences, messaging guidelines, and creative preferences</li>
              <li><strong className="text-white">Campaign Inputs:</strong> Marketing goals, target audiences, budget allocations, creative briefs, and campaign objectives</li>
              <li><strong className="text-white">Payment Information:</strong> Credit card details (partially stored, with full details tokenized through our payment processor), billing addresses, and transaction history</li>
              <li><strong className="text-white">Communication Preferences:</strong> Notification settings, email preferences, and contact preferences</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">2.2 Integration-Based & Automated Data</h3>
            <p className="leading-relaxed">
              RAAMP collects data through authorized third-party integrations and automated systems:
            </p>
            
            <div className="mt-4">
              <h4 className="font-semibold text-white mb-2">Third-Party API Data (via OAuth Authorization)</h4>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li><strong className="text-white">Instagram Integration:</strong> Profile data, engagement metrics, follower demographics, hashtag performance, post analytics, and story insights</li>
                <li><strong className="text-white">Google Maps Integration:</strong> Location data, business listings, customer reviews, foot traffic patterns, and geographic insights</li>
                <li><strong className="text-white">Other Marketing Platforms:</strong> Ad performance data, audience insights, and campaign metrics from connected advertising accounts</li>
              </ul>
            </div>

            <div className="mt-4">
              <h4 className="font-semibold text-white mb-2">AI-Generated & Analyzed Data</h4>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li><strong className="text-white">Trend Signals:</strong> Real-time trend analysis, viral content identification, hashtag momentum scoring, and emerging topic detection</li>
                <li><strong className="text-white">Location-Intent Signals:</strong> Hyperlocal demand patterns, geographic customer intent, neighborhood engagement scores, and proximity-based insights</li>
                <li><strong className="text-white">Hashtag Engagement:</strong> Performance metrics, reach analysis, and engagement prediction models</li>
                <li><strong className="text-white">Predictive Analytics:</strong> Customer behavior predictions, churn risk scoring, and conversion probability modeling</li>
              </ul>
            </div>

            <div className="mt-4">
              <h4 className="font-semibold text-white mb-2">Web-Scraped Public Data</h4>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>Publicly available business information from third-party websites and directories</li>
                <li>Competitive intelligence gathered from public sources</li>
                <li>Market trends and industry insights from public data sources</li>
                <li>Review aggregation from public review platforms</li>
              </ul>
              <p className="text-sm text-gray-400 mt-2">
                Note: We only collect publicly available data and comply with website terms of service and robots.txt directives.
              </p>
            </div>

            <div className="mt-4">
              <h4 className="font-semibold text-white mb-2">Campaign Performance & Attribution Data</h4>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li><strong className="text-white">Performance Metrics:</strong> Return on Ad Spend (ROAS), Click-Through Rate (CTR), Cost Per Click (CPC), Cost Per Acquisition (CPA), conversion rates, and revenue attribution</li>
                <li><strong className="text-white">A/B Testing Results:</strong> Variant performance data, statistical significance scores, and optimization recommendations</li>
                <li><strong className="text-white">Attribution Analytics:</strong> Multi-touch attribution models, customer journey mapping, and channel performance analysis</li>
                <li><strong className="text-white">Budget Allocation Data:</strong> Automated budget distribution patterns and optimization decisions made by the A/B Auto-Optimization Layer</li>
              </ul>
            </div>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">2.3 Automatically Collected Technical Data</h3>
            <p className="leading-relaxed">
              When you use RAAMP, we automatically collect certain technical information:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Device Information:</strong> Device type, operating system, browser type and version, screen resolution, and device identifiers</li>
              <li><strong className="text-white">Usage Data:</strong> Pages viewed, features accessed, time spent on platform, click patterns, and navigation paths</li>
              <li><strong className="text-white">Log Data:</strong> IP addresses, access times, error logs, and system diagnostics</li>
              <li><strong className="text-white">Cookies & Similar Technologies:</strong> Session cookies, authentication tokens, and analytics cookies (see Cookie Policy)</li>
            </ul>
          </motion.section>

          {/* Section 3 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">3. How We Use Your Data</h2>
            <p className="leading-relaxed">
              RAAMP uses collected data to provide, improve, and personalize our AI-powered marketing platform:
            </p>

            <div className="mt-4">
              <h3 className="text-xl font-semibold text-primary mb-3">3.1 Core Platform Operations</h3>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li><strong className="text-white">Account Management:</strong> Authentication, account access, user profiles, and team management</li>
                <li><strong className="text-white">Campaign Execution:</strong> Running campaigns, distributing ads, managing budgets, and tracking performance</li>
                <li><strong className="text-white">Hyperlocal Targeting:</strong> Analyzing geolocation data to identify high-intent areas, score neighborhoods, and optimize ad delivery based on location signals</li>
                <li><strong className="text-white">Payment Processing:</strong> Billing, invoicing, transaction processing, and financial reporting</li>
              </ul>
            </div>

            <div className="mt-4">
              <h3 className="text-xl font-semibold text-primary mb-3">3.2 AI-Powered Features</h3>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li><strong className="text-white">Generative Creatives:</strong> Using Stable Diffusion and BERT models to generate images, copy, and campaign content based on your brand guidelines and inputs</li>
                <li><strong className="text-white">A/B Auto-Optimization:</strong> Automatically testing campaign variants, analyzing performance, and reallocating budgets to maximize ROAS</li>
                <li><strong className="text-white">Predictive Analytics:</strong> Using TensorFlow models to forecast customer behavior, predict campaign outcomes, and recommend optimization strategies</li>
                <li><strong className="text-white">Attribution Insights:</strong> Mapping customer journeys, attributing conversions across channels, and providing multi-touch attribution analysis</li>
                <li><strong className="text-white">RAAMP Assistant:</strong> Providing conversational AI support, answering questions, and offering strategic recommendations</li>
                <li><strong className="text-white">Trend Arbitrage:</strong> Identifying emerging trends, analyzing hashtag momentum, and recommending timely content opportunities</li>
              </ul>
            </div>

            <div className="mt-4">
              <h3 className="text-xl font-semibold text-primary mb-3">3.3 Platform Improvement & AI Training</h3>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>Training and refining AI models to improve prediction accuracy and recommendation quality</li>
                <li>Enhancing algorithms for better targeting, optimization, and personalization</li>
                <li>Developing new features and capabilities based on usage patterns</li>
                <li>Conducting aggregate analysis to benchmark performance across industries</li>
              </ul>
              <p className="text-sm text-gray-400 mt-2">
                Note: Data used for AI training is anonymized and aggregated to protect individual user privacy.
              </p>
            </div>

            <div className="mt-4">
              <h3 className="text-xl font-semibold text-primary mb-3">3.4 Communication & Support</h3>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li><strong className="text-white">System Alerts:</strong> Critical notifications about campaign status, budget depletion, and system issues</li>
                <li><strong className="text-white">Performance Notifications:</strong> Campaign updates, optimization recommendations, and achievement milestones</li>
                <li><strong className="text-white">Customer Support:</strong> Responding to inquiries, troubleshooting issues, and providing technical assistance</li>
                <li><strong className="text-white">Marketing Communications:</strong> Product updates, feature announcements, educational content, and promotional offers (opt-out available)</li>
              </ul>
            </div>

            <div className="mt-4">
              <h3 className="text-xl font-semibold text-primary mb-3">3.5 Legal & Security</h3>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>Preventing fraud, unauthorized access, and security threats</li>
                <li>Enforcing our Terms & Conditions and platform policies</li>
                <li>Complying with legal obligations and responding to lawful requests</li>
                <li>Protecting the rights, property, and safety of RAAMP and our users</li>
              </ul>
            </div>
          </motion.section>

          {/* Section 4 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">4. Data Storage, Security & Retention</h2>
            
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.1 Where Your Data is Stored</h3>
            <p className="leading-relaxed">
              RAAMP data is stored securely on enterprise-grade cloud infrastructure:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Primary Storage:</strong> Amazon Web Services (AWS) and/or Google Cloud Platform in geographically distributed data centers</li>
              <li><strong className="text-white">Database Systems:</strong> Encrypted databases with automated backups and disaster recovery capabilities</li>
              <li><strong className="text-white">File Storage:</strong> Secure object storage for media assets, creatives, and documents</li>
              <li><strong className="text-white">Data Residency:</strong> Data may be processed and stored in multiple regions to ensure performance and availability</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.2 Security Measures</h3>
            <p className="leading-relaxed">
              We implement industry-standard security practices to protect your data:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Encryption in Transit:</strong> All data transmitted between your browser and RAAMP is encrypted using TLS 1.2+ (Transport Layer Security)</li>
              <li><strong className="text-white">Encryption at Rest:</strong> Sensitive data stored in databases is encrypted using AES-256 encryption</li>
              <li><strong className="text-white">Password Security:</strong> User passwords are hashed using bcrypt with secure salt and never stored in plain text</li>
              <li><strong className="text-white">Access Controls:</strong> Role-based access controls (RBAC) limit data access to authorized personnel only</li>
              <li><strong className="text-white">Session Management:</strong> Automatic session expiry after 30 minutes of inactivity to prevent unauthorized access</li>
              <li><strong className="text-white">Monitoring & Auditing:</strong> Continuous security monitoring, intrusion detection, and audit logging</li>
              <li><strong className="text-white">Vulnerability Management:</strong> Regular security assessments, penetration testing, and prompt patching of vulnerabilities</li>
              <li><strong className="text-white">Secure Development:</strong> Security-first development practices, code reviews, and security training for our team</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">4.3 Data Retention</h3>
            <p className="leading-relaxed">
              We retain your data for as long as necessary to provide our services and comply with legal obligations:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Active Accounts:</strong> Data is retained while your account is active and for reasonable periods after account closure</li>
              <li><strong className="text-white">Campaign Data:</strong> Performance metrics and analytics are retained for up to 7 years for reporting and compliance purposes</li>
              <li><strong className="text-white">Financial Records:</strong> Billing and transaction data is retained as required by tax and accounting regulations (typically 7-10 years)</li>
              <li><strong className="text-white">Legal Holds:</strong> Data may be retained longer if required by law, litigation, or regulatory investigation</li>
              <li><strong className="text-white">Anonymized Data:</strong> Aggregated and anonymized data may be retained indefinitely for analytics and AI training</li>
            </ul>
            <p className="leading-relaxed mt-4">
              You may request deletion of your data at any time (see Section 6: User Rights).
            </p>
          </motion.section>

          {/* Section 5 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">5. Data Sharing & Third Parties</h2>
            
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">5.1 When We Share Your Data</h3>
            <p className="leading-relaxed">
              RAAMP does not sell your personal or business data to third parties. We only share data in the following limited circumstances:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Service Providers:</strong> Third-party vendors who help us operate the platform (cloud hosting, payment processing, email delivery, analytics) under strict confidentiality agreements</li>
              <li><strong className="text-white">Advertising Platforms:</strong> Campaign data sent to Facebook, Instagram, Google Ads, etc. when you run campaigns through those platforms (subject to their privacy policies)</li>
              <li><strong className="text-white">Business Transfers:</strong> In the event of a merger, acquisition, or sale of assets, your data may be transferred to the acquiring entity</li>
              <li><strong className="text-white">Legal Compliance:</strong> When required by law, court order, or government request, or to protect our rights and safety</li>
              <li><strong className="text-white">With Your Consent:</strong> When you explicitly authorize us to share specific data with third parties</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">5.2 Third-Party Services & APIs</h3>
            <p className="leading-relaxed">
              RAAMP integrates with external services that have their own privacy policies:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Google Maps API (Google Privacy Policy applies)</li>
              <li>Instagram API (Meta/Facebook Privacy Policy applies)</li>
              <li>Payment processors (Stripe, PayPal, etc.)</li>
              <li>Cloud infrastructure providers (AWS, Google Cloud)</li>
            </ul>
            <p className="text-sm text-gray-400 mt-2">
              We recommend reviewing the privacy policies of these third-party services to understand their data practices.
            </p>
          </motion.section>

          {/* Section 6 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">6. Your Rights & Choices (GDPR & Privacy Regulations)</h2>
            
            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">6.1 Data Access & Portability</h3>
            <p className="leading-relaxed">
              You have the right to:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Access Your Data:</strong> Request a copy of all personal and business data we hold about you</li>
              <li><strong className="text-white">Data Portability:</strong> Receive your data in a structured, machine-readable format (CSV, JSON) for transfer to another service</li>
              <li><strong className="text-white">Update Information:</strong> Correct or update inaccurate account information through your profile settings</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">6.2 Data Deletion & Account Closure</h3>
            <p className="leading-relaxed">
              You have the right to:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Request Deletion:</strong> Ask us to delete your personal data, subject to legal retention requirements</li>
              <li><strong className="text-white">Close Your Account:</strong> Permanently delete your RAAMP account through account settings or by contacting support</li>
              <li><strong className="text-white">Withdraw Consent:</strong> Revoke consent for data processing where consent was the legal basis</li>
            </ul>
            <p className="text-sm text-gray-400 mt-2">
              Note: Some data may be retained as required by law (e.g., financial records) or in anonymized form for analytics.
            </p>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">6.3 Integration & Communication Controls</h3>
            <p className="leading-relaxed">
              You can manage your preferences at any time:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Revoke Integrations:</strong> Disconnect Instagram, Google Maps, or other third-party integrations through your account settings</li>
              <li><strong className="text-white">Communication Preferences:</strong> Opt out of marketing emails, adjust notification settings, and choose communication channels</li>
              <li><strong className="text-white">Cookie Settings:</strong> Manage cookie preferences through your browser settings (note: some cookies are essential for platform functionality)</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">6.4 GDPR-Specific Rights (EU/EEA Users)</h3>
            <p className="leading-relaxed">
              If you are located in the European Economic Area (EEA), you have additional rights under GDPR:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Right to Object:</strong> Object to processing of your data for direct marketing or legitimate interests</li>
              <li><strong className="text-white">Right to Restrict Processing:</strong> Request temporary restriction of data processing in certain circumstances</li>
              <li><strong className="text-white">Right to Lodge Complaint:</strong> File a complaint with your local data protection authority (DPA)</li>
              <li><strong className="text-white">Automated Decision-Making:</strong> Request human review of AI-driven decisions that significantly affect you</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">6.5 How to Exercise Your Rights</h3>
            <p className="leading-relaxed">
              To exercise any of these rights, please contact us at:
            </p>
            <div className="mt-3 p-4 bg-white/5 rounded-lg">
              <p className="text-primary">Email: privacy@raamp.ai</p>
              <p className="text-primary">Subject: Data Rights Request</p>
            </div>
            <p className="text-sm text-gray-400 mt-3">
              We will respond to verified requests within 30 days (or as required by applicable law).
            </p>
          </motion.section>

          {/* Section 7 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">7. GDPR Compliance & Data Protection</h2>
            <p className="leading-relaxed">
              RAAMP is designed with GDPR principles in mind and implements the following safeguards:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li><strong className="text-white">Lawful Basis:</strong> We process data based on consent, contractual necessity, legitimate interests, or legal obligations</li>
              <li><strong className="text-white">Data Minimization:</strong> We collect only data necessary for platform functionality and stated purposes</li>
              <li><strong className="text-white">Purpose Limitation:</strong> Data is used only for disclosed purposes and not for incompatible secondary uses</li>
              <li><strong className="text-white">Accuracy:</strong> We maintain accurate records and allow users to update their information</li>
              <li><strong className="text-white">Storage Limitation:</strong> Data is retained only as long as necessary and deleted when no longer needed</li>
              <li><strong className="text-white">Integrity & Confidentiality:</strong> Strong security measures protect data from unauthorized access, loss, or disclosure</li>
              <li><strong className="text-white">Accountability:</strong> We maintain records of processing activities and conduct data protection impact assessments (DPIAs) for high-risk processing</li>
            </ul>

            <h3 className="text-xl font-semibold text-primary mb-3 mt-6">7.1 Scraped Data & Third-Party Data Validation</h3>
            <p className="leading-relaxed">
              For web-scraped and third-party data, we implement additional safeguards:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>We only scrape publicly available data from websites that permit automated access</li>
              <li>We comply with robots.txt directives and website terms of service</li>
              <li>We validate data accuracy and freshness before using it for insights</li>
              <li>We do not scrape or process sensitive personal data (e.g., health, financial, biometric)</li>
              <li>Users can report inaccurate scraped data for correction or removal</li>
            </ul>
          </motion.section>

          {/* Section 8 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">8. Children's Privacy</h2>
            <p className="leading-relaxed">
              RAAMP is a B2B marketing platform intended for business use only. We do not knowingly collect personal 
              information from individuals under the age of 18. If we become aware that we have collected data from a 
              minor without parental consent, we will take steps to delete that information promptly.
            </p>
            <p className="leading-relaxed mt-4">
              If you believe we have inadvertently collected data from a minor, please contact us immediately at 
              privacy@raamp.ai.
            </p>
          </motion.section>

          {/* Section 9 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">9. International Data Transfers</h2>
            <p className="leading-relaxed">
              RAAMP operates globally and may transfer data across international borders. If you are located in the 
              European Economic Area (EEA), United Kingdom, or other regions with data transfer restrictions, please 
              be aware that:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Your data may be transferred to and processed in countries outside your jurisdiction</li>
              <li>We use Standard Contractual Clauses (SCCs) and other approved mechanisms to ensure adequate protection</li>
              <li>Third-party providers are required to implement appropriate safeguards</li>
              <li>You may contact us for more information about our data transfer practices</li>
            </ul>
          </motion.section>

          {/* Section 10 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">10. Changes to This Privacy Policy</h2>
            <p className="leading-relaxed">
              We may update this Privacy Policy from time to time to reflect changes in our practices, technology, 
              legal requirements, or other factors. When we make material changes, we will:
            </p>
            <ul className="list-disc list-inside ml-4 mt-3 space-y-2">
              <li>Update the "Last Updated" date at the top of this policy</li>
              <li>Notify you via email or platform notification</li>
              <li>Provide a summary of significant changes</li>
              <li>Give you an opportunity to review the updated policy</li>
            </ul>
            <p className="leading-relaxed mt-4">
              Your continued use of RAAMP after policy changes constitutes acceptance of the updated terms. We 
              encourage you to review this policy periodically.
            </p>
          </motion.section>

          {/* Section 11 */}
          <motion.section variants={fadeInUp}>
            <h2 className="text-2xl font-bold text-white mb-4">11. Contact Us</h2>
            <p className="leading-relaxed">
              If you have questions, concerns, or requests regarding this Privacy Policy or our data practices, 
              please contact us:
            </p>
            <div className="mt-4 p-6 bg-white/5 rounded-lg space-y-3">
              <div>
                <p className="font-semibold text-white">RAAMP Data Protection Officer</p>
                <p className="text-primary">Email: privacy@raamp.ai</p>
              </div>
              <div>
                <p className="font-semibold text-white">General Support</p>
                <p className="text-primary">Email: support@raamp.ai</p>
              </div>
              <div>
                <p className="font-semibold text-white">Legal Inquiries</p>
                <p className="text-primary">Email: legal@raamp.ai</p>
              </div>
              <div>
                <p className="font-semibold text-white">Website</p>
                <p className="text-primary">www.raamp.ai</p>
              </div>
            </div>
            <p className="text-sm text-gray-400 mt-4">
              We aim to respond to all privacy inquiries within 30 days (or as required by applicable law).
            </p>
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