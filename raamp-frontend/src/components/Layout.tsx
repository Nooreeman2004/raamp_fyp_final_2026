import { ReactNode, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import Breadcrumbs from "@/components/Breadcrumbs";
import AppDrawer from "@/components/AppDrawer";
import RAMPFloatingWidget from "@/components/RAMPFloatingWidget";
import { Bell } from "lucide-react";
import { authService } from "@/services/authService";
import type { UserResponse } from "@/types";
import { Sidebar } from "@/components/Sidebar";
import { motion } from "framer-motion";
import { useNotifications } from "@/contexts/NotificationContext";

import { useAuth } from "@/hooks/useAuth";

interface LayoutProps {
  children: ReactNode;
  showBreadcrumbs?: boolean;
  breadcrumbItems?: Array<{ label: string; href?: string }>;
  breadcrumbOverride?: Array<{ label: string; path: string }>;
}

const Layout = ({ children, showBreadcrumbs = true, breadcrumbItems, breadcrumbOverride }: LayoutProps) => {
  const { user } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // ... try-catch for context safety
  const notificationContext = useNotifications();
  const unreadCount = notificationContext?.unreadCount || 0;

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const getUserInitials = () => {
    if (!user) return "U";
    const first = user.first_name?.[0] || "";
    const last = user.last_name?.[0] || user.first_name?.[1] || "";
    return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || "U";
  };

  // --- RENDERING ---

  // 1. Authenticated Layout (Sidebar)
  if (user) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-x-hidden font-sans selection:bg-primary/30 selection:text-primary">
        <div className="fixed inset-0 bg-background -z-50" />
        <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full pointer-events-none -z-40" />
        <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-500/5 blur-[120px] rounded-full pointer-events-none -z-40" />

        <Sidebar collapsed={sidebarCollapsed} setCollapsed={setSidebarCollapsed} />

        <motion.main
          animate={{ paddingLeft: sidebarCollapsed ? 80 : 240 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="min-h-screen relative z-10 hidden lg:block"
        >
          {/* Top Header for Dashboard */}
          <div className="h-20 flex items-center justify-between px-8 border-b border-white/5 bg-background/50 backdrop-blur-sm sticky top-0 z-40">
            <div className="flex items-center gap-4">
              {showBreadcrumbs && (
                <Breadcrumbs items={breadcrumbOverride ? breadcrumbOverride.map(b => ({ label: b.label, href: b.path })) : breadcrumbItems} />
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Real-time Data Active
              </div>
              <Link to="/profile/user">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-800 to-black flex items-center justify-center border border-white/10 hover:border-primary/50 transition-colors cursor-pointer">
                  <span className="text-xs font-bold text-white">
                    {getUserInitials()}
                  </span>
                </div>
              </Link>
            </div>
          </div>

          <div className="p-8">
            {children}
          </div>
        </motion.main>

        {/* Mobile Layout (Fallback to Drawer) */}
        <div className="lg:hidden">
          <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-white/5 py-3 px-4 flex justify-between items-center">
            <div className="flex items-center gap-4">
              <AppDrawer user={user} />
              <img src={raampIcon} alt="RAAMP" className="h-8 w-8" />
            </div>
            <Link to="/profile/user">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-800 to-black flex items-center justify-center border border-white/10">
                <span className="text-xs font-bold text-white">
                  {getUserInitials()}
                </span>
              </div>
            </Link>
          </nav>
          <div className="h-16" />
          <main className="p-4">
            {children}
          </main>
        </div>

        <RAMPFloatingWidget userName={user?.first_name || user?.username || "Commander"} />
      </div>
    );
  }

  // 2. Public Layout (Top Nav)
  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-x-hidden font-sans selection:bg-primary/30 selection:text-primary">

      {/* BACKGROUND LAYER - Deep Teal Theme */}
      <div className="fixed inset-0 bg-background -z-50" />

      {/* Subtle Gradient Spotlights (Apple-style) */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full pointer-events-none -z-40" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-500/5 blur-[120px] rounded-full pointer-events-none -z-40" />

      {/* Top Navigation (HUD Mode) */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out transform ${scrolled ? "bg-background/80 backdrop-blur-xl border-b border-white/5 py-3" : "bg-transparent py-5"
          }`}
      >
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-10">
            {/* Left: Hamburger Menu */}
            <div className="flex items-center gap-4">
              <AppDrawer user={user} />
              <Link to="/" className="flex items-center gap-3 group">
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 blur-md rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <img src={raampIcon} alt="RAAMP" className="h-8 w-8 relative z-10" />
                </div>
                <span className="text-lg font-bold tracking-wide text-white group-hover:text-primary transition-colors duration-300 hidden sm:inline font-bebas">RAAMP</span>
              </Link>
            </div>

            {/* Right: Notifications and User Profile */}
            <div className="flex items-center gap-4">
              <Link to="/notifications">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-white/70 hover:text-primary hover:bg-white/5 transition-all relative group"
                  aria-label="Notifications"
                >
                  <Bell className="w-5 h-5" />
                  {/* Real-time Badge */}
                  {unreadCount > 0 && (
                    <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full" />
                  )}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Spacer for fixed navbar */}
      <div className="h-20" />

      {/* Breadcrumbs */}
      {showBreadcrumbs && (
        <div className="border-b border-white/5 bg-background/50 backdrop-blur-sm relative z-40">
          <div className="container mx-auto px-4 sm:px-6 py-2">
            <Breadcrumbs items={breadcrumbOverride ? breadcrumbOverride.map(b => ({ label: b.label, href: b.path })) : breadcrumbItems} />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10 relative z-10">
        {children}
      </main>
    </div>
  );
};

export default Layout;
