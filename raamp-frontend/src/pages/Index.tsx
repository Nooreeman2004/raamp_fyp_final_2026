import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import Modules from "@/components/Modules";
import IglooInspiredFeatures from "@/components/IglooInspiredFeatures";
import Pricing from "@/components/Pricing";
import FloatingTeam from "@/components/FloatingTeam";
import ConsultationSection from "@/components/ConsultationSection";
import Footer from "@/components/Footer";
import { CursorTrail } from "@/components/ui/cursor-trail";

const Index = () => {
  const location = useLocation();

  useEffect(() => {
    console.log("Index mounted, path:", location.pathname, "hash:", location.hash);
    // Handle hash navigation
    if (location.hash) {
      const id = location.hash.replace('#', '');
      const element = document.getElementById(id);
      if (element) {
        setTimeout(() => {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    }
  }, [location]);

  return (
    <div className="min-h-screen">
      {/* Cursor Trail Effect */}
      <CursorTrail />

      <Navigation />
      <Hero />
      <div id="how-it-works">
        <HowItWorks />
      </div>

      {/* New Igloo-Inspired Features Section */}
      <IglooInspiredFeatures />

      <div id="modules">
        <Modules />
      </div>
      <Pricing />
      <FloatingTeam />
      <ConsultationSection />
      <Footer />
    </div>
  );
};

export default Index;
