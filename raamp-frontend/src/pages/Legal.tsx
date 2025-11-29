import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card } from "@/components/ui/card";
import { Scale, Shield, FileText } from "lucide-react";

const Legal = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background">
      <Navigation />
      
      {/* Breadcrumbs */}
      <div className="container mx-auto px-4 pt-20">
        <Breadcrumbs items={[
          { label: 'Home', href: '/' },
          { label: 'Legal' },
        ]} />
      </div>
      
      {/* Header Section */}
      <section className="pt-8 pb-12 px-4">
        <div className="container mx-auto max-w-4xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
              <Scale className="w-10 h-10 text-primary" />
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Legal & Compliance
          </h1>
          <p className="text-lg text-muted-foreground">
            Our commitment to transparency, privacy, and security
          </p>
        </div>
      </section>

      {/* Privacy Policy Section */}
      <section className="py-8 px-4">
        <div className="container mx-auto max-w-4xl">
          <Card className="p-8 md:p-10 bg-card/50 backdrop-blur-sm border-primary/10">
            <div className="flex items-center gap-3 mb-6">
              <Shield className="w-6 h-6 text-primary" />
              <h2 className="text-3xl font-bold">Privacy Policy</h2>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold mb-3 text-primary">Data Protection (GDPR)</h3>
                <p className="text-muted-foreground leading-relaxed">
                  RAAMP is committed to protecting your privacy. We comply with regulations such as the General 
                  Data Protection Regulation (GDPR) to ensure all user information is handled securely and ethically.
                </p>
              </div>

              <div className="border-t border-primary/10 pt-6">
                <h3 className="text-xl font-bold mb-3 text-primary">Data Usage</h3>
                <p className="text-muted-foreground leading-relaxed">
                  We collect location-based data and social engagement metrics solely to optimize your marketing 
                  campaigns. We do not sell your personal data to third parties.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Terms of Service Section */}
      <section className="py-8 px-4 pb-20">
        <div className="container mx-auto max-w-4xl">
          <Card className="p-8 md:p-10 bg-card/50 backdrop-blur-sm border-primary/10">
            <div className="flex items-center gap-3 mb-6">
              <FileText className="w-6 h-6 text-primary" />
              <h2 className="text-3xl font-bold">Terms of Service</h2>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold mb-3 text-primary">Third-Party Integrations</h3>
                <p className="text-muted-foreground leading-relaxed">
                  RAAMP relies on external APIs, including Google Maps and Instagram. While we strive for 98% 
                  operational availability, service disruptions from these providers may temporarily affect 
                  real-time data collection.
                </p>
              </div>

              <div className="border-t border-primary/10 pt-6">
                <h3 className="text-xl font-bold mb-3 text-primary">Account Security</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Users are responsible for maintaining the confidentiality of their login credentials. Sessions 
                  automatically expire after 30 minutes of inactivity to prevent unauthorized access.
                </p>
              </div>

              <div className="border-t border-primary/10 pt-6">
                <h3 className="text-xl font-bold mb-3 text-primary">Declaration</h3>
                <p className="text-muted-foreground leading-relaxed">
                  This software is the result of independent development efforts and utilizes authorized API 
                  connections for all external data processing.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Legal;
