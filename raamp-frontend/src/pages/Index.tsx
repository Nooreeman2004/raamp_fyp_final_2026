import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import Modules from "@/components/Modules";
import Pricing from "@/components/Pricing";
import ConsultationSection from "@/components/ConsultationSection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      <Hero />
      <div id="how-it-works">
        <HowItWorks />
      </div>
      <div id="modules">
        <Modules />
      </div>
      <Pricing />
      <ConsultationSection />
      <Footer />
    </div>
  );
};

export default Index;
