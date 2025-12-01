import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { motion, AnimatePresence } from "framer-motion";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { 
  Menu,
  LayoutDashboard, 
  MapPin, 
  Sparkles, 
  BarChart3,
  TrendingUp as TrendIcon,
  FlaskConical as Flask,
  User,
  Building2,
  Palette,
  Bell,
  Link2,
  Shield,
  CreditCard,
  LogOut,
  ChevronRight,
  type LucideIcon
} from "lucide-react";
import type { UserResponse } from "@/types";
import { useToast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { staggerContainer, fadeInUp } from "@/utils/animations";

interface AppDrawerProps {
  user: UserResponse | null;
}

interface NavItem {
  label: string;
  icon: LucideIcon;
  href: string;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const AppDrawer = ({ user }: AppDrawerProps) => {
  const [open, setOpen] = useState(false);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // MODULE STATUS & QUICK ACTIONS - Core dashboard modules
  const moduleItems: NavItem[] = [
    { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { label: "Geo-Intent", icon: MapPin, href: "/dashboard/geo-intent" },
    { label: "Creative Studio", icon: Sparkles, href: "/dashboard/creative" },
    { label: "Trend Arbitrage", icon: TrendIcon, href: "/dashboard/trends" },
    { label: "A/B Testing", icon: Flask, href: "/dashboard/ab-testing" },
    { label: "Performance", icon: BarChart3, href: "/dashboard/performance" },
    { label: "Billing & Finance", icon: CreditCard, href: "/billing" },
  ];

  // SETTINGS - All editable screens
  const settingsItems: NavItem[] = [
    { label: "Edit User Profile", icon: User, href: "/profile/user" },
    { label: "Edit Business Details", icon: Building2, href: "/profile/business-setup" },
    { label: "Brand Settings", icon: Palette, href: "/profile/brand-settings" },
    { label: "Notification Preferences", icon: Bell, href: "/settings/notifications" },
    { label: "Integrations", icon: Link2, href: "/profile/onboarding" },
    { label: "Account & Security", icon: Shield, href: "/settings/security" },
  ];

  // Build navigation sections for logged-in users only
  const navSections: NavSection[] = user ? [
    { title: "Module Status & Quick Actions", items: moduleItems },
    { title: "Settings", items: settingsItems },
  ] : [];

  const handleLogout = async () => {
    try {
      await authService.logout();
      localStorage.removeItem("user");
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out.",
      });
      setOpen(false);
      navigate("/login");
    } catch (e) {
      toast({
        title: "Error",
        description: "Failed to logout. Please try again.",
        variant: "destructive",
      });
    }
  };

  const getUserInitials = () => {
    if (!user) return "U";
    const first = user.first_name?.[0] || "";
    const last = user.last_name?.[0] || user.first_name?.[1] || "";
    return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || "U";
  };

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return location.pathname === href;
    }
    return location.pathname.startsWith(href);
  };

  return (
    <>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button 
            variant="ghost" 
            size="icon" 
            className="hover:bg-primary/10 transition-colors"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </Button>
        </SheetTrigger>
        <SheetContent 
          side="left" 
          className="w-[300px] sm:w-[340px] p-0 flex flex-col bg-gradient-to-b from-card via-card/95 to-card/90"
        >
          {/* Header */}
          <SheetHeader className="p-6 pb-4 border-b border-primary/10">
            <div className="flex items-center justify-between">
              <Link 
                to={user ? "/dashboard" : "/"} 
                className="flex items-center gap-3 group"
                onClick={() => setOpen(false)}
              >
                <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
                <SheetTitle className="text-xl font-bold text-primary">RAAMP</SheetTitle>
              </Link>
            </div>
          </SheetHeader>

          {/* User Profile Section - Only for logged in users */}
          {user && (
            <div className="px-6 py-4 bg-primary/5 border-b border-primary/10">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12 border-2 border-primary/20">
                  <AvatarImage src={user.profile_picture || undefined} alt={user.username} />
                  <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                    {getUserInitials()}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate">
                    {user.first_name && user.last_name 
                      ? `${user.first_name} ${user.last_name}`
                      : user.username || user.email}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Sections */}
          <div className="flex-1 overflow-y-auto py-4">
            <AnimatePresence>
              {user ? (
                // Logged in: Show modules and settings
                navSections.map((section, sectionIdx) => (
                  <motion.div 
                    key={section.title} 
                    className="mb-6"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: sectionIdx * 0.1, duration: 0.3 }}
                  >
                    <h3 className="px-6 mb-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {section.title}
                    </h3>
                    <motion.nav 
                      className="space-y-0.5 px-3"
                      variants={staggerContainer}
                      initial="hidden"
                      animate="visible"
                    >
                      {section.items.map((item, itemIdx) => {
                        const Icon = item.icon;
                        const active = isActive(item.href);
                        return (
                          <motion.div
                            key={item.href}
                            variants={fadeInUp}
                            custom={itemIdx}
                          >
                            <Link
                              to={item.href}
                              onClick={() => setOpen(false)}
                              className={`
                                group flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200
                                ${active 
                                  ? 'bg-primary/10 text-primary font-medium' 
                                  : 'hover:bg-primary/5 text-foreground/80 hover:text-foreground'
                                }
                              `}
                            >
                              <Icon className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110 ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
                              <span className="text-sm flex-1">{item.label}</span>
                              {item.badge && (
                                <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-primary/20 text-primary">
                                  {item.badge}
                                </span>
                              )}
                              <ChevronRight className={`w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-all group-hover:translate-x-0.5 ${active ? 'text-primary opacity-100' : 'text-muted-foreground'}`} />
                            </Link>
                          </motion.div>
                        );
                      })}
                    </motion.nav>
                    {sectionIdx < navSections.length - 1 && (
                      <Separator className="mt-4 mx-6" />
                    )}
                  </motion.div>
                ))
              ) : (
                // Not logged in: Show login/signup options
                <motion.div 
                  className="px-3 space-y-2"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-primary/5 text-foreground/80 hover:text-foreground transition-all"
                  >
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">Login</span>
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-all"
                  >
                    <User className="w-4 h-4" />
                    <span className="text-sm font-medium">Sign Up</span>
                  </Link>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer Actions */}
          {user && (
            <div className="p-4 border-t border-primary/10 bg-card/50">
              <Button
                variant="ghost"
                className="w-full justify-start gap-3 text-destructive hover:text-destructive hover:bg-destructive/10"
                onClick={() => {
                  setOpen(false);
                  setShowLogoutDialog(true);
                }}
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </Button>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Logout Confirmation Dialog */}
      <ConfirmationDialog
        open={showLogoutDialog}
        onOpenChange={setShowLogoutDialog}
        onConfirm={handleLogout}
        title="Confirm Logout"
        description="Are you sure you want to logout? You'll need to sign in again to access your account."
        confirmText="Logout"
        cancelText="Cancel"
        variant="default"
      />
    </>
  );
};

export default AppDrawer;
