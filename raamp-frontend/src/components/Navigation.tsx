import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { Menu, Home, Info, BookOpen, Scale, LogIn, UserPlus } from "lucide-react";

const Navigation = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "How It Works", href: "/#how-it-works", icon: Home },
    { label: "Modules", href: "/#modules", icon: Home },
    { label: "About", href: "/about", icon: Info },
    { label: "Resources", href: "/resources", icon: BookOpen },
    { label: "Legal", href: "/legal", icon: Scale },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-md border-b border-primary/10">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
            <span className="text-xl font-bold">RAAMP</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link 
                key={link.href}
                to={link.href} 
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Desktop Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Login
              </Button>
            </Link>
            <Link to="/signup">
              <Button variant="hero" size="sm">
                Sign Up
              </Button>
            </Link>
          </div>

          {/* Mobile Menu */}
          <div className="flex md:hidden items-center gap-2">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Login
              </Button>
            </Link>
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="hover:bg-primary/10"
                  aria-label="Open menu"
                >
                  <Menu className="w-5 h-5" />
                </Button>
              </SheetTrigger>
              <SheetContent 
                side="right" 
                className="w-[280px] p-0 flex flex-col bg-gradient-to-b from-card via-card/95 to-card/90"
              >
                <SheetHeader className="p-6 pb-4 border-b border-primary/10">
                  <div className="flex items-center gap-3">
                    <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
                    <SheetTitle className="text-xl font-bold text-primary">RAAMP</SheetTitle>
                  </div>
                </SheetHeader>

                <div className="flex-1 overflow-y-auto py-4">
                  <nav className="space-y-1 px-3">
                    {navLinks.map((link) => {
                      const Icon = link.icon;
                      return (
                        <Link
                          key={link.href}
                          to={link.href}
                          onClick={() => setMobileMenuOpen(false)}
                          className="group flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-primary/5 text-foreground/80 hover:text-foreground transition-all"
                        >
                          <Icon className="w-5 h-5 text-muted-foreground group-hover:text-primary" />
                          <span className="text-sm">{link.label}</span>
                        </Link>
                      );
                    })}
                  </nav>

                  <Separator className="my-4 mx-6" />

                  <div className="px-3 space-y-2">
                    <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="hero" size="sm" className="w-full justify-start gap-3">
                        <UserPlus className="w-4 h-4" />
                        Sign Up
                      </Button>
                    </Link>
                    <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="outline" size="sm" className="w-full justify-start gap-3">
                        <LogIn className="w-4 h-4" />
                        Login
                      </Button>
                    </Link>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
