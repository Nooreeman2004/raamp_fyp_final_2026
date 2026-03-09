import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import raampIcon from "@/assets/raamp-logo-v6-transparent.png";
import { Menu, Home, Info, BookOpen, Scale, LogIn, UserPlus } from "lucide-react";

const Navigation = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "HOW IT WORKS", href: "/#how-it-works", icon: Home },
    { label: "MODULES", href: "/#modules", icon: Home },
    { label: "PRICING", href: "/#pricing", icon: BookOpen },
    { label: "ABOUT", href: "/about", icon: Info },
    { label: "RESOURCES", href: "/resources", icon: BookOpen },
    { label: "LEGAL", href: "/legal", icon: Scale },
    { label: "CONTACT US", href: "/#consultation", icon: Info },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-md border-b border-white/10">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <img src={raampIcon} alt="RAAMP" className="h-10 w-auto" />
            <span className="text-2xl font-bold font-bebas tracking-widest text-white group-hover:text-neon-teal transition-colors">RAAMP</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="text-sm font-bold font-mono text-white/70 hover:text-neon-teal transition-colors tracking-wide"
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Desktop Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-white hover:text-neon-teal hover:bg-white/5 font-mono">
                LOGIN
              </Button>
            </Link>
            <Link to="/signup">
              <Button variant="default" size="sm" className="bg-neon-teal text-black hover:bg-neon-teal/80 font-bold font-bebas tracking-wider">
                SIGN UP
              </Button>
            </Link>
          </div>

          {/* Mobile Menu */}
          <div className="flex md:hidden items-center gap-2">
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-white font-mono">
                LOGIN
              </Button>
            </Link>
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-white hover:bg-white/10 hover:text-neon-teal"
                  aria-label="Open menu"
                >
                  <Menu className="w-6 h-6" />
                </Button>
              </SheetTrigger>
              <SheetContent
                side="right"
                className="w-[280px] p-0 flex flex-col bg-black/95 border-l border-white/10"
              >
                <SheetHeader className="p-6 pb-4 border-b border-white/10">
                  <div className="flex items-center gap-3">
                    <img src={raampIcon} alt="RAAMP" className="h-8 w-auto" />
                    <SheetTitle className="text-2xl font-bold font-bebas tracking-widest text-white">RAAMP</SheetTitle>
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
                          className="group flex items-center gap-3 px-3 py-3 rounded hover:bg-white/5 text-white/70 hover:text-neon-teal transition-all"
                        >
                          <Icon className="w-4 h-4 text-white/50 group-hover:text-neon-teal" />
                          <span className="text-sm font-mono font-bold tracking-wide">{link.label}</span>
                        </Link>
                      );
                    })}
                  </nav>

                  <Separator className="my-4 mx-6 bg-white/10" />

                  <div className="px-3 space-y-3">
                    <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="default" size="sm" className="w-full justify-start gap-3 bg-neon-teal text-black hover:bg-neon-teal/80 font-bebas tracking-wider">
                        <UserPlus className="w-4 h-4" />
                        SIGN UP
                      </Button>
                    </Link>
                    <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="outline" size="sm" className="w-full justify-start gap-3 border-white/10 text-white hover:bg-white/5 font-mono">
                        <LogIn className="w-4 h-4" />
                        LOGIN
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
