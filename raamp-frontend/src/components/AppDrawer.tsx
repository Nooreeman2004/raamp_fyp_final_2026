import { useState, useRef } from "react";
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
  Info,
  BookOpen,
  Scale,
  Images,
  type LucideIcon
} from "lucide-react";
import type { UserResponse } from "@/types";
import { authService } from "@/services/authService";
import { toast as sonner } from "sonner";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { staggerContainer } from "@/utils/animations";
import { springSlide } from "@/utils/motion";

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
  const containerRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setMousePosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  // MODULE STATUS & QUICK ACTIONS - Core dashboard modules
  const moduleItems: NavItem[] = [
    { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { label: "Geo-Intent", icon: MapPin, href: "/dashboard/geo-intent" },
    { label: "Creative Studio", icon: Sparkles, href: "/dashboard/creative" },
    { label: "Asset Library", icon: Images, href: "/dashboard/assets" },
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

  // Information items - only shown to non-logged-in users
  const infoItems: NavItem[] = [
    { label: "About Us", icon: Info, href: "/about" },
    { label: "Resources", icon: BookOpen, href: "/resources" },
    { label: "Legal & Compliance", icon: Scale, href: "/legal" },
  ];

  // Build navigation sections for logged-in users
  // Marketing pages (About, Resources, Legal) are intentionally excluded for logged-in users
  const navSections: NavSection[] = user ? [
    { title: "Module Status & Quick Actions", items: moduleItems },
    { title: "Settings", items: settingsItems },
  ] : [];

  const handleLogout = async () => {
    try {
      await authService.logout();
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      sonner.success("Logged Out", {
        description: "You have been successfully logged out.",
      });
      setOpen(false);
      navigate("/login");
    } catch (e) {
      sonner.error("Error", {
        description: "Failed to logout. Please try again.",
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
            className="text-white/70 hover:text-primary hover:bg-white/5 transition-all"
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </Button>
        </SheetTrigger>
        <SheetContent
          side="left"
          className="w-[300px] sm:w-[340px] p-0 flex flex-col bg-background/95 backdrop-blur-2xl border-r border-white/10 text-white"
        >
          {/* Glow Slide Effect Container */}
          <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            className="absolute inset-0 pointer-events-none z-0 opacity-30"
            style={{
              background: `radial-gradient(600px circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(0, 224, 208, 0.15), transparent 40%)`
            }}
          />

          {/* Header */}
          <SheetHeader className="p-6 pb-4 border-b border-white/10 relative z-10">
            <div className="flex items-center justify-between">
              <Link
                to={user ? "/dashboard" : "/"}
                className="flex items-center gap-3 group"
                onClick={() => setOpen(false)}
              >
                <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
                <SheetTitle className="text-2xl font-bold text-white tracking-wider font-bebas group-hover:text-primary transition-colors">RAAMP</SheetTitle>
              </Link>
            </div>
          </SheetHeader>

          {/* User Profile Section - Only for logged in users */}
          {user && (
            <div className="px-6 py-4 bg-white/5 border-b border-white/10 relative z-10">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12 border border-white/20 ring-2 ring-transparent group-hover:ring-primary/50 transition-all">
                  <AvatarImage src={user.profile_picture || undefined} alt={user.username} />
                  <AvatarFallback className="bg-card text-primary font-bold border border-white/10">
                    {getUserInitials()}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate text-white">
                    {user.first_name && user.last_name
                      ? `${user.first_name} ${user.last_name}`
                      : user.username || user.email}
                  </p>
                  <p className="text-xs text-white/50 truncate">{user.email}</p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Sections */}
          <div className="flex-1 overflow-y-auto py-4 relative z-10 scrollbar-thin scrollbar-thumb-white/10 hover:scrollbar-thumb-primary/50">
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
                    <h3 className="px-6 mb-3 text-[10px] font-bold text-primary/80 uppercase tracking-[0.2em]">
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
                            variants={springSlide}
                            custom={itemIdx}
                          >
                            <Link
                              to={item.href}
                              onClick={() => setOpen(false)}
                              className={`
                                group flex items-center gap-3 px-3 py-2.5 rounded-r-lg transition-all duration-300 relative overflow-hidden
                                ${active
                                  ? 'bg-primary/10 text-primary border-l-2 border-primary'
                                  : 'text-white/60 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                                }
                              `}
                            >
                              <Icon className={`w-4 h-4 flex-shrink-0 transition-transform duration-300 group-hover:scale-110 ${active ? 'text-primary' : 'text-white/40 group-hover:text-primary'}`} />
                              <span className="text-sm flex-1 font-medium tracking-wide">{item.label}</span>
                              {item.badge && (
                                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-primary/20 text-primary border border-primary/30">
                                  {item.badge}
                                </span>
                              )}
                              <ChevronRight className={`w-3.5 h-3.5 transition-all duration-300 ${active ? 'opacity-100 translate-x-0 text-primary' : 'opacity-0 -translate-x-2 group-hover:opacity-50 group-hover:translate-x-0'}`} />

                              {/* Active Glow Background */}
                              {active && (
                                <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-50 -z-10" />
                              )}
                            </Link>
                          </motion.div>
                        );
                      })}
                    </motion.nav>
                    {sectionIdx < navSections.length - 1 && (
                      <Separator className="mt-4 mx-6 bg-white/10" />
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
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-white/80 hover:text-white transition-all"
                  >
                    <User className="w-4 h-4 text-white/50" />
                    <span className="text-sm">Login</span>
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-all border border-primary/20"
                  >
                    <User className="w-4 h-4" />
                    <span className="text-sm font-medium">Create Account</span>
                  </Link>

                  <Separator className="my-4 bg-white/10" />

                  <div className="space-y-1">
                    {infoItems.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.href}
                          to={item.href}
                          onClick={() => setOpen(false)}
                          className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5 text-white/60 hover:text-white transition-all"
                        >
                          <Icon className="w-4 h-4 text-white/30" />
                          <span className="text-sm">{item.label}</span>
                        </Link>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer Actions */}
          {user && (
            <div className="p-4 border-t border-white/10 bg-black/20 relative z-10">
              <Button
                variant="ghost"
                className="w-full justify-start gap-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
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
        description="Are you sure you want to logout? You'll need to login again to access your account."
        confirmText="Logout"
        cancelText="Cancel"
        variant="destructive"
      />
    </>
  );
};

export default AppDrawer;
