import { useState, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  Menu,
  LayoutDashboard,
  MapPin,
  Sparkles,
  TrendingUp,
  FlaskConical,
  Settings,
  LogOut,
  Bell,
  Search,
  Calendar,
  CalendarDays,
  Images,
  ShieldCheck,
  MessageSquare,
  LifeBuoy,
  AlertTriangle,
  CreditCard,
  FileText,
  User,
  Info,
  BookOpen,
  Scale
} from "lucide-react";
import type { UserResponse } from "@/types";
import { authService } from "@/services/authService";
import { toast as sonner } from "sonner";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { BrandMark } from "@/components/BrandMark";
import { useNotifications } from "@/contexts/NotificationContext";
import { Separator } from "@/components/ui/separator";

interface AppDrawerProps {
  user: UserResponse | null;
}

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: MapPin, label: "Geo-Intent", href: "/dashboard/geo-intent" },
  { icon: Sparkles, label: "Creative Studio", href: "/dashboard/creative" },
  { icon: Images, label: "Asset Library", href: "/dashboard/assets" },
  { icon: Calendar, label: "Smart Scheduling", href: "/dashboard/smart-scheduling" },
  { icon: CalendarDays, label: "Campaign Planner", href: "/dashboard/campaign-planner" },
  { icon: TrendingUp, label: "Trend Arbitrage", href: "/dashboard/trends" },
  { icon: ShieldCheck, label: "Approvals", href: "/dashboard/approvals" },
  { icon: FileText, label: "My Drafts", href: "/dashboard/drafts" },
  { icon: MessageSquare, label: "Auto Replies", href: "/dashboard/auto-replies" },
  { icon: AlertTriangle, label: "Social Moderation", href: "/dashboard/escalations" },
  { icon: FlaskConical, label: "The Lab (A/B)", href: "/dashboard/ab-optimizer" },
  { icon: CreditCard, label: "Billing", href: "/billing" },
];

const bottomItems = [
  { icon: LifeBuoy, label: "Support", href: "/dashboard/complaints" },
  { icon: Bell, label: "Notifications", href: "/notifications" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

const infoItems = [
  { label: "About Us", icon: Info, href: "/about" },
  { label: "Resources", icon: BookOpen, href: "/resources" },
  { label: "Legal & Compliance", icon: Scale, href: "/legal" },
];

const AppDrawer = ({ user }: AppDrawerProps) => {
  const [open, setOpen] = useState(false);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const notificationContext = useNotifications();
  const unreadCount = notificationContext?.unreadCount || 0;

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setMousePosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch {
      // Don't block sign-out UX on network/server failures
      sonner.message("Signed out locally", {
        description: "We couldn’t reach the server, but this device has been signed out.",
      });
    } finally {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
      setOpen(false);
      navigate("/login");
    }
  };

  return (
    <>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="touch-target text-muted-foreground hover:text-primary hover:bg-foreground/5 transition-all sm:min-h-10 sm:min-w-10"
            aria-label="Open menu"
          >
            <Menu className="w-6 h-6" />
          </Button>
        </SheetTrigger>
        <SheetContent
          side="left"
          className="w-[min(100vw-1rem,21.25rem)] sm:w-[min(100vw-2rem,21.25rem)] p-0 flex flex-col bg-background/95 backdrop-blur-2xl border-r border-border/50 text-foreground max-w-[100vw]"
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
          <SheetHeader className="h-20 flex items-center justify-between px-6 border-b border-border/50 relative z-10 m-0">
            <Link
              to={user ? "/dashboard" : "/"}
              className="flex items-center gap-3 w-full h-full"
              onClick={() => setOpen(false)}
            >
              <div className="relative flex-shrink-0">
                <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full opacity-50" />
                <BrandMark variant="drawer" size={32} className="relative z-10" />
              </div>
              <SheetTitle className="font-heading font-semibold text-xl tracking-wider text-foreground whitespace-nowrap overflow-hidden">
                RAAMP
              </SheetTitle>
            </Link>
          </SheetHeader>

          {/* Command Shortcut Hint */}
          {user && (
            <div className="px-4 py-4 relative z-10">
              <button
                onClick={() => {
                  setOpen(false);
                  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-foreground/5 border border-border text-xs text-muted-foreground hover:bg-foreground/10 hover:border-border/50 transition-all group"
              >
                <Search size={14} />
                <span className="flex-1 text-left">Search...</span>
                <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-border/50 bg-background px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100 group-hover:text-foreground">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </button>
            </div>
          )}

          {/* Navigation Sections */}
          <div className="flex-1 overflow-y-auto py-2 px-3 space-y-2 relative z-10 scrollbar-none">
            <AnimatePresence>
              {user ? (
                // Logged in: Show exactly what Sidebar shows
                <>
                  {menuItems.map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                      <Link
                        key={item.href}
                        to={item.href}
                        onClick={() => setOpen(false)}
                        className={cn(
                          "flex min-h-[2.75rem] items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                          isActive
                            ? "bg-primary/10 text-primary shadow-[0_0_20px_rgba(0,224,208,0.1)]"
                            : "text-muted-foreground hover:text-foreground hover:bg-foreground/5"
                        )}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="mobileActiveTab"
                            className="absolute inset-0 border border-primary/20 rounded-xl"
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                          />
                        )}
                        <item.icon size={20} className={cn("flex-shrink-0 transition-transform duration-300", isActive && "scale-110")} />
                        <span className="font-medium text-sm whitespace-nowrap overflow-hidden relative z-10">
                          {item.label}
                        </span>

                        {/* Active Glow Dot */}
                        {isActive && (
                          <motion.div
                            layoutId="mobileActiveDot"
                            className="absolute right-3 w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_10px_#00E0D0] z-10"
                          />
                        )}
                      </Link>
                    );
                  })}
                </>
              ) : (
                // Not logged in: Show login/signup options
                <motion.div
                  className="space-y-2"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-foreground/5 text-foreground/80 hover:text-foreground transition-all"
                  >
                    <User className="w-4 h-4 text-muted-foreground/80" />
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

                  <Separator className="my-4 bg-foreground/10 mx-3" />

                  <div className="space-y-1">
                    {infoItems.map((item) => (
                      <Link
                        key={item.href}
                        to={item.href}
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-foreground/5 text-muted-foreground/80 hover:text-foreground transition-all"
                      >
                        <item.icon className="w-4 h-4 text-muted-foreground/60" />
                        <span className="text-sm">{item.label}</span>
                      </Link>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Bottom Section */}
          {user && (
            <div className="p-3 border-t border-border space-y-2 bg-card/50 relative z-10">
              {bottomItems.map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex min-h-[2.75rem] items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-muted-foreground hover:text-foreground hover:bg-foreground/5 relative",
                    location.pathname === item.href && "text-foreground bg-foreground/5"
                  )}
                >
                  <item.icon size={20} className="flex-shrink-0" />
                  <span className="font-medium text-sm whitespace-nowrap overflow-hidden">
                    {item.label}
                  </span>
                  {item.label === "Notifications" && unreadCount > 0 && (
                    <div className="absolute right-3 w-5 h-5 bg-destructive text-foreground text-[10px] font-bold flex items-center justify-center rounded-full">
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </div>
                  )}
                </Link>
              ))}

              <button
                type="button"
                className="w-full flex min-h-[2.75rem] items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-red-400 hover:text-red-300 hover:bg-red-500/10"
                onClick={() => {
                  setOpen(false);
                  setShowLogoutDialog(true);
                }}
              >
                <LogOut size={20} className="flex-shrink-0" />
                <span className="font-medium text-sm whitespace-nowrap overflow-hidden">
                  Sign Out
                </span>
              </button>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Logout Confirmation Dialog */}
      <ConfirmationDialog
        open={showLogoutDialog}
        onOpenChange={setShowLogoutDialog}
        onConfirm={handleLogout}
        title="Sign out of RAAMP?"
        description="You'll be returned to the login screen. You can sign back in anytime."
        confirmText="Sign out"
        cancelText="Cancel"
        variant="destructive"
      />
    </>
  );
};

export default AppDrawer;
