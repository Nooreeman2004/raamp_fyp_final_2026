import { Link } from "react-router-dom";
import raampIcon from "@/assets/raamp-logo-v6.png";

const Footer = () => {
  return (
    <footer className="border-t border-primary/10 py-12 bg-card/50 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <img src={raampIcon} alt="RAAMP" className="h-8 w-auto mix-blend-screen" />
            <p className="text-sm text-muted-foreground font-mono">
              © 2025 RAAMP. All rights reserved.
            </p>
          </div>
          <div className="flex gap-6">
            <Link to="/about" className="text-sm text-muted-foreground hover:text-primary transition-colors font-mono">
              About
            </Link>
            <Link to="/resources" className="text-sm text-muted-foreground hover:text-primary transition-colors font-mono">
              Resources
            </Link>
            <Link to="/legal" className="text-sm text-muted-foreground hover:text-primary transition-colors font-mono">
              Legal
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
