import { useLocation, Link, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Home, SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";
import Reveal from "@/components/ui/Reveal";
import { hoverScale, scaleUp } from "@/utils/animations";

const NotFound = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4 overflow-hidden relative">
      
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="relative z-10 text-center space-y-8 max-w-lg mx-auto">
        
        {/* Creative 404 Graphic */}
        <Reveal variant="scaleUp" duration={0.8} className="relative select-none">

          <h1 className="text-[180px] font-black leading-none text-foreground/5 scale-150 blur-sm absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 -z-10">
            404
          </h1>
          
          <div className="w-32 h-32 bg-card/50 backdrop-blur-md rounded-full border border-primary/20 flex items-center justify-center mx-auto shadow-2xl relative">
            <div className="absolute inset-0 rounded-full border border-primary/10 animate-ping opacity-20" />
            <SearchX className="w-16 h-16 text-primary" />
          </div>
        </Reveal>

        <div className="space-y-2">
          <Reveal variant="fadeInUp" delay={0.2}>
            <h2 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Page Not Found
            </h2>
          </Reveal>
          <Reveal variant="fadeIn" delay={0.4}>
            <p className="text-muted-foreground text-lg max-w-sm mx-auto leading-relaxed">
              We looked everywhere for this page. Are you sure the URL is correct?
            </p>
          </Reveal>
          <Reveal variant="fadeIn" delay={0.5}>
             <p className="text-xs font-mono text-muted-foreground/50 bg-muted/30 inline-block px-2 py-1 rounded">
                Route: {location.pathname}
             </p>
          </Reveal>
        </div>

        <Reveal variant="fadeInUp" delay={0.6}>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mt-4">
            
            {/* Return Home Button */}
            <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
              <Button asChild size="lg" className="gap-2 bg-gradient-to-r from-primary to-primary/80 shadow-lg shadow-primary/20">
                <Link to="/">
                  <Home className="w-4 h-4" />
                  Return Home
                </Link>
              </Button>
            </motion.div>
            
            {/* Go Back Button */}
            <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
              <Button 
                variant="outline" 
                size="lg" 
                className="gap-2 border-primary/20 hover:bg-primary/5"
                onClick={() => navigate(-1)}
              >
                <ArrowLeft className="w-4 h-4" />
                Go Back
              </Button>
            </motion.div>

          </div>
        </Reveal>

      </div>
    </div>
  );
};

export default NotFound;