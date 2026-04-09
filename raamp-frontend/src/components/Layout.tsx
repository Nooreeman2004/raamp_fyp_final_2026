import { ReactNode, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Breadcrumbs from "@/components/Breadcrumbs";
import AppDrawer from "@/components/AppDrawer";
import RAMPFloatingWidget from "@/components/RAMPFloatingWidget";
import { Bell, RefreshCw } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { motion } from "framer-motion";
import { useNotifications } from "@/contexts/NotificationContext";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import { useThemeMode } from "@/hooks/useThemeMode";
import * as React from "react";
import { BrandMark } from "@/components/BrandMark";

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

  // 1. Authenticated Layout (Sidebar)
  if (user) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-x-hidden font-sans selection:bg-primary/30 selection:text-primary">
        <div className="fixed inset-0 bg-background -z-50" />
        <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 dark:bg-primary/5 blur-[120px] rounded-full pointer-events-none -z-40 animate-pulse" />
        <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-teal-500/10 dark:bg-teal-500/5 blur-[120px] rounded-full pointer-events-none -z-40 animate-pulse [animation-delay:2s]" />

        <Sidebar collapsed={sidebarCollapsed} setCollapsed={setSidebarCollapsed} />

        <motion.main
          animate={{ paddingLeft: sidebarCollapsed ? 80 : 240 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="min-h-screen relative z-10 hidden lg:block"
        >
          {/* Top Header for Dashboard */}
          <div className="h-20 flex items-center justify-between px-8 border-b border-border bg-background/50 backdrop-blur-xl sticky top-0 z-40">
            <div className="flex items-center gap-4">
              {showBreadcrumbs && (
                <Breadcrumbs items={breadcrumbOverride ? breadcrumbOverride.map(b => ({ label: b.label, href: b.path })) : breadcrumbItems} />
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/5 dark:bg-foreground/5 border border-primary/20 dark:border-border/50 text-xs text-primary dark:text-muted-foreground shadow-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_hsl(var(--primary))]" />
                <span className="font-mono uppercase text-[9px] font-black tracking-widest">Real-time Data Active</span>
              </div>
              <ThemeToggle />
              <Link to="/profile/user">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 dark:from-gray-800 dark:to-black flex items-center justify-center border border-primary/30 dark:border-border/50 hover:border-primary/50 transition-all cursor-pointer shadow-lg group">
                  <span className="text-xs font-bold text-foreground group-hover:scale-110 transition-transform">
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
          <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border py-3 px-4 flex justify-between items-center">
            <div className="flex items-center gap-4">
              <AppDrawer user={user} />
              <button
                onClick={() => window.location.reload()}
                className="text-muted-foreground/80 hover:text-primary transition-colors"
                aria-label="Refresh Page"
              >
                <RefreshCw size={18} />
              </button>
              <BrandMark variant="navbar" size={32} />
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Link to="/profile/user">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 dark:from-gray-800 dark:to-black flex items-center justify-center border border-primary/30 dark:border-border/50">
                  <span className="text-xs font-bold text-foreground">
                    {getUserInitials()}
                  </span>
                </div>
              </Link>
            </div>
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
      <div className="fixed inset-0 bg-background -z-50" />
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 dark:bg-primary/5 blur-[120px] rounded-full pointer-events-none -z-40 animate-pulse" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-teal-500/10 dark:bg-teal-500/5 blur-[120px] rounded-full pointer-events-none -z-40 animate-pulse [animation-delay:2s]" />

      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out transform ${scrolled ? "bg-background/80 backdrop-blur-xl border-b border-border py-3" : "bg-transparent py-5"
          }`}
      >
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-10">
            <div className="flex items-center gap-4">
              <AppDrawer user={user} />
              <Link to="/" className="flex items-center gap-3 group">
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 blur-md rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <BrandMark variant="navbar" size={32} className="relative z-10" />
                </div>
                <span className="text-lg font-bold tracking-wide text-foreground group-hover:text-primary transition-colors duration-300 hidden sm:inline font-heading font-semibold">RAAMP</span>
              </Link>
            </div>

            <div className="flex items-center gap-4">
              <Link to="/notifications">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-primary hover:bg-foreground/5 transition-all relative group"
                  aria-label="Notifications"
                >
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full shadow-[0_0_8px_hsl(var(--destructive))]" />
                  )}
                </Button>
              </Link>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </nav>

      <div className="h-20" />

      {showBreadcrumbs && (
        <div className="border-b border-border bg-background/50 backdrop-blur-sm relative z-40">
          <div className="container mx-auto px-4 sm:px-6 py-2">
            <Breadcrumbs items={breadcrumbOverride ? breadcrumbOverride.map(b => ({ label: b.label, href: b.path })) : breadcrumbItems} />
          </div>
        </div>
      )}

      <main className="container mx-auto px-4 sm:px-6 py-8 sm:py-10 relative z-10">
        {children}
      </main>
    </div>
  );
};

export default Layout;
