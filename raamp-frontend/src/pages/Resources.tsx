import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card } from "@/components/ui/card";
import { BookOpen, HelpCircle, Lightbulb } from "lucide-react";

const Resources = () => {
  const faqs = [
    {
      question: "Why isn't my ad showing?",
      answer: "Check your 'Performance Dashboard' for alerts. Common issues include budget caps or disconnected social accounts. The RAAMP Assistant can run a diagnostic check to pinpoint the issue."
    },
    {
      question: "How does the Trend Arbitrage Detector work?",
      answer: "We monitor emerging trends and viral events in your local area. When a relevant trend is detected, RAAMP suggests a campaign launch within minutes to help you capture the moment."
    },
    {
      question: "Is my data secure?",
      answer: "Yes. All user credentials and business data are encrypted. We strictly follow privacy standards to ensure your information is protected."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background">
      <Navigation />
      
      {/* Breadcrumbs */}
      <div className="container mx-auto px-4 pt-20">
        <Breadcrumbs items={[
          { label: 'Home', href: '/' },
          { label: 'Resources' },
        ]} />
      </div>
      
      {/* Header Section */}
      <section className="pt-8 pb-12 px-4">
        <div className="container mx-auto max-w-5xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
              <BookOpen className="w-10 h-10 text-primary" />
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            RAAMP Knowledge Base
          </h1>
          <p className="text-lg text-muted-foreground">
            Everything you need to get started and make the most of RAAMP
          </p>
        </div>
      </section>

      {/* Getting Started Section */}
      <section className="py-12 px-4">
        <div className="container mx-auto max-w-5xl">
          <Card className="p-8 md:p-10 bg-card/50 backdrop-blur-sm border-primary/10">
            <div className="flex items-center gap-3 mb-6">
              <Lightbulb className="w-6 h-6 text-primary" />
              <h2 className="text-3xl font-bold">Getting Started</h2>
            </div>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold mb-3 text-primary">How RAAMP Works</h3>
                <p className="text-muted-foreground leading-relaxed">
                  RAAMP integrates real-time data from Google Maps, Instagram, and web events to identify 
                  high-demand areas. Our Intelligent Geo-Intent Marketing Engine helps you target the right 
                  audience at the right time.
                </p>
              </div>

              <div className="border-t border-primary/10 pt-6">
                <h3 className="text-xl font-bold mb-3 text-primary">Setting Up</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Simply register with your email and business details. Once logged in, connect your Instagram 
                  handle via our secure OAuth integration to start generating hyper-personalized campaigns.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* FAQs Section */}
      <section className="py-12 px-4 pb-20">
        <div className="container mx-auto max-w-5xl">
          <div className="flex items-center gap-3 mb-8">
            <HelpCircle className="w-6 h-6 text-primary" />
            <h2 className="text-3xl font-bold">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <Card key={index} className="p-6 bg-card/50 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all">
                <h3 className="text-lg font-bold mb-3 text-foreground">
                  Q: {faq.question}
                </h3>
                <p className="text-muted-foreground leading-relaxed pl-4 border-l-2 border-primary/30">
                  A: {faq.answer}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Resources;
