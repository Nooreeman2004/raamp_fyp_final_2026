import { ReactNode, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Breadcrumbs from "@/components/Breadcrumbs";
import AppDrawer from "@/components/AppDrawer";
import RAMPFloatingWidget from "@/components/RAMPFloatingWidget";
import { Bell, RefreshCw, AlertTriangle, Loader2 } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { motion } from "framer-motion";
import { useNotifications } from "@/contexts/NotificationContext";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import { useThemeMode } from "@/hooks/useThemeMode";
import * as React from "react";
import { BrandMark } from "@/components/BrandMark";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface LayoutProps {
  children: ReactNode;
  showBreadcrumbs?: boolean;
  breadcrumbItems?: Array<{ label: string; href?: string }>;
  breadcrumbOverride?: Array<{ label: string; path: string }>;
}

const Layout = ({ children, showBreadcrumbs = true, breadcrumbItems, breadcrumbOverride }: LayoutProps) => {
  const { user, sessionUncertain, dismissSessionWarning, refreshUser } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sessionRetrying, setSessionRetrying] = useState(false);

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

  const sessionBanner = sessionUncertain ? (
    <Alert className="mb-6 rounded-lg border-amber-500/40 bg-amber-500/10 text-foreground">
      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
      <AlertTitle className="text-amber-900 dark:text-amber-100">Can’t reach the server</AlertTitle>
      <AlertDescription className="flex flex-col gap-3 text-amber-950/90 dark:text-amber-50/90 sm:flex-row sm:items-center sm:justify-between">
        <span>
          We couldn’t verify your session. You may be seeing cached account data; some actions may fail until the connection is restored.
        </span>
        <div className="flex shrink-0 gap-2">
          <Button
            type="button"
            size="sm"
            variant="secondary"
            disabled={sessionRetrying}
            onClick={async () => {
              setSessionRetrying(true);
              try {
                await refreshUser();
              } finally {
                setSessionRetrying(false);
              }
            }}
          >
            {sessionRetrying ? (
              <>
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                Retrying…
              </>
            ) : (
              "Retry"
            )}
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={dismissSessionWarning}>
            Dismiss
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  ) : null;

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
          className="min-h-screen relative z-10 hidden lg:block w-full min-w-0 max-w-[100vw] overflow-x-clip box-border"
        >
          {/* Top Header for Dashboard — flex/grid hybrid: wrap + min-w-0 prevents breadcrumb overflow */}
          <div className="min-h-[4.5rem] sm:min-h-20 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 sm:px-6 xl:px-8 border-b border-border bg-background/50 backdrop-blur-xl sticky top-0 z-40">
            <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-4">
              {showBreadcrumbs && (
                <Breadcrumbs items={breadcrumbOverride ? breadcrumbOverride.map(b => ({ label: b.label, href: b.path })) : breadcrumbItems} />
              )}
            </div>
            <div className="flex shrink-0 items-center gap-2 sm:gap-4">
              {/* Hide status pill on narrow desktop columns to avoid crowding; unchanged on xl+ */}
              <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/5 dark:bg-foreground/5 border border-primary/20 dark:border-border/50 text-xs text-primary dark:text-muted-foreground shadow-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_hsl(var(--primary))]" />
                <span className="font-mono uppercase text-[9px] font-black tracking-widest">Real-time Data Active</span>
              </div>
              <ThemeToggle />
              <div className="flex items-center gap-2 rounded-full border border-border/50 bg-background/60 px-3 py-1.5">
                <div className="h-8 w-8 sm:h-8 sm:w-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 dark:from-gray-800 dark:to-black flex items-center justify-center border border-primary/30 dark:border-border/50 shadow-lg">
                  <span className="text-xs font-bold text-foreground">
                    {getUserInitials()}
                  </span>
                </div>
                <span className="hidden sm:inline text-xs font-mono text-muted-foreground max-w-[180px] truncate">
                  {user?.first_name || user?.username || "User"}
                </span>
              </div>
            </div>
          </div>

          <div className="p-4 sm:p-6 xl:p-8 w-full min-w-0 max-w-full">
            {sessionBanner}
            {children}
          </div>
        </motion.main>

        {/* Mobile Layout (Fallback to Drawer) */}
        <div className="lg:hidden w-full min-w-0 max-w-[100vw] overflow-x-clip">
          <nav
            className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border flex min-h-[3.25rem] items-center justify-between gap-2 px-3 sm:px-4 pt-[max(0.5rem,env(safe-area-inset-top))] pb-2"
            style={{ paddingLeft: "max(0.75rem, env(safe-area-inset-left))", paddingRight: "max(0.75rem, env(safe-area-inset-right))" }}
          >
            <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
              <AppDrawer user={user} />
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="touch-target inline-flex shrink-0 items-center justify-center rounded-md text-muted-foreground/80 hover:text-primary transition-colors sm:min-h-0 sm:min-w-0 sm:p-2"
                aria-label="Refresh Page"
              >
                <RefreshCw className="h-[1.125rem] w-[1.125rem] sm:h-[1.125rem] sm:w-[1.125rem]" />
              </button>
              <BrandMark variant="navbar" size={32} className="shrink-0" />
            </div>
            <div className="flex shrink-0 items-center gap-2 sm:gap-3">
              <ThemeToggle />
              <div className="flex items-center gap-2 rounded-full border border-border/50 bg-background/60 px-2 py-1">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 dark:from-gray-800 dark:to-black flex items-center justify-center border border-primary/30 dark:border-border/50">
                  <span className="text-xs font-bold text-foreground">
                    {getUserInitials()}
                  </span>
                </div>
              </div>
            </div>
          </nav>
          <div className="h-14 sm:h-16" />
          <main className="w-full min-w-0 max-w-[100vw] overflow-x-clip px-3 py-4 sm:px-4 md:px-6">
            {sessionBanner}
            {children}
          </main>
        </div>

        <RAMPFloatingWidget
          userName={user?.first_name || user?.username || "Commander"}
          userId={user?.id}
        />
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
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out transform max-w-[100vw] overflow-x-clip ${scrolled ? "bg-background/80 backdrop-blur-xl border-b border-border py-3" : "bg-transparent py-5"
          }`}
      >
        <div className="container mx-auto w-full min-w-0 max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-[2.75rem] flex-wrap items-center justify-between gap-y-2 sm:h-10">
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

      <main className="container relative z-10 mx-auto w-full min-w-0 max-w-full overflow-x-clip px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;
