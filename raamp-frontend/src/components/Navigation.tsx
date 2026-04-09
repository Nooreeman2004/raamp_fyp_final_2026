import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { Menu, Home, Info, BookOpen, Scale, LogIn, UserPlus } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { useThemeMode } from "@/hooks/useThemeMode";
import { BrandMark } from "@/components/BrandMark";


const Navigation = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { mounted } = useThemeMode();

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
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-md border-b border-border/60 transition-all duration-300">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <BrandMark variant="navbar" size={40} />
            <span className="text-2xl font-bold font-heading font-semiboldst text-foreground group-hover:text-primary transition-colors">RAAMP</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="text-sm font-bold font-mono text-muted-foreground hover:text-primary transition-colors tracking-wide"
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Desktop Auth Buttons with Theme Toggle */}
          <div className="hidden md:flex items-center gap-3">
            {mounted && <ThemeToggle />}
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-foreground hover:text-primary hover:bg-foreground/5 font-mono">
                LOGIN
              </Button>
            </Link>
            <Link to="/signup">
              <Button variant="default" size="sm" className="bg-primary text-white hover:bg-primary/90 font-bold font-heading font-semibold">
                SIGN UP
              </Button>
            </Link>
          </div>

          {/* Mobile Menu with Theme Toggle */}
          <div className="flex md:hidden items-center gap-2">
            {mounted && <ThemeToggle />}
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-foreground font-mono">
                LOGIN
              </Button>
            </Link>
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-foreground hover:bg-foreground/10 hover:text-primary transition-colors"
                  aria-label="Open menu"
                >
                  <Menu className="w-6 h-6" />
                </Button>
              </SheetTrigger>
              <SheetContent
                side="right"
                className="w-[280px] p-0 flex flex-col bg-background border-l border-border/50"
              >
                <SheetHeader className="p-6 pb-4 border-b border-border/50">
                  <div className="flex items-center gap-3">
                    <BrandMark variant="drawer" size={36} />
                    <SheetTitle className="text-2xl font-bold font-heading font-semiboldst text-foreground">RAAMP</SheetTitle>
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
                          className="group flex items-center gap-3 px-3 py-3 rounded hover:bg-foreground/5 text-muted-foreground hover:text-primary transition-all"
                        >
                          <Icon className="w-4 h-4 text-muted-foreground/80 group-hover:text-primary" />
                          <span className="text-sm font-mono font-bold tracking-wide">{link.label}</span>
                        </Link>
                      );
                    })}
                  </nav>

                  <Separator className="my-4 mx-6 bg-foreground/10" />

                  <div className="px-3 space-y-3">
                    <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="default" size="sm" className="w-full justify-start gap-3 bg-primary text-white hover:bg-primary/90 font-heading font-semibold">
                        <UserPlus className="w-4 h-4" />
                        SIGN UP
                      </Button>
                    </Link>
                    <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                      <Button variant="outline" size="sm" className="w-full justify-start gap-3 border-border/50 text-foreground hover:bg-foreground/5 font-mono">
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
