import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import Breadcrumbs from "@/components/Breadcrumbs";
import AppDrawer from "@/components/AppDrawer";
import RAMPFloatingWidget from "@/components/RAMPFloatingWidget";
import { Bell } from "lucide-react";
import { useState, useEffect } from "react";
import { authService } from "@/services/authService";
import type { UserResponse } from "@/types";

interface LayoutProps {
  children: ReactNode;
  showBreadcrumbs?: boolean;
  breadcrumbItems?: Array<{ label: string; href?: string }>;
  breadcrumbOverride?: Array<{ label: string; path: string }>;
}

const Layout = ({ children, showBreadcrumbs = true, breadcrumbItems, breadcrumbOverride }: LayoutProps) => {
  const [user, setUser] = useState<UserResponse | null>(null);

  useEffect(() => {
    // Load user from localStorage first
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch (error) {
        // Invalid stored user data, remove it
        localStorage.removeItem("user");
      }
    }

    // Fetch fresh user data
    (async () => {
      try {
        const u = await authService.getProfile();
        if (u) {
          setUser(u);
          try {
            localStorage.setItem("user", JSON.stringify(u));
          } catch (error) {
            // localStorage quota exceeded or unavailable
          }
        }
      } catch (err) {
        // Ignore - user will be handled by ProtectedRoute
      }
    })();
  }, []);

  const getUserInitials = () => {
    if (!user) return "U";
    const first = user.first_name?.[0] || "";
    const last = user.last_name?.[0] || user.first_name?.[1] || "";
    return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || "U";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-[#0f1c26] to-background">
      {/* Top Navigation with Hamburger Menu */}
      <nav className="sticky top-0 z-50 border-b border-primary/20 bg-card/95 backdrop-blur-md">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            {/* Left: Hamburger Menu */}
            <div className="flex items-center gap-3">
              <AppDrawer user={user} />
              <Link to="/" className="flex items-center gap-2 sm:gap-3">
                <img src={raampIcon} alt="RAAMP" className="h-8 w-8 sm:h-10 sm:w-10" />
                <span className="text-lg sm:text-xl font-bold text-primary hidden sm:inline">RAAMP</span>
              </Link>
            </div>

            {/* Right: Notifications and User Profile */}
            <div className="flex items-center gap-2">
              <Link to="/notifications">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="hover:bg-primary/10 transition-colors relative"
                  aria-label="Notifications"
                >
                  <Bell className="w-5 h-5" />
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full animate-pulse" />
                </Button>
              </Link>
              {user && (
                <Link to="/profile/user">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-2 hover:bg-primary/10 transition-colors"
                  >
                    <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                      <span className="text-xs font-semibold text-primary">
                        {getUserInitials()}
                      </span>
                    </div>
                    <span className="font-medium hidden sm:inline">Profile</span>
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Breadcrumbs */}
      {showBreadcrumbs && (
        <div className="border-b border-primary/10 bg-card/10 backdrop-blur-sm">
          <div className="container mx-auto px-4 sm:px-6 py-3">
            <Breadcrumbs items={breadcrumbOverride ? breadcrumbOverride.map(b => ({ label: b.label, href: b.path })) : breadcrumbItems} />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {children}
      </main>

      {/* Floating AI Widget - only for logged in users */}
      {user && <RAMPFloatingWidget userName={user.first_name || user.username} />}
    </div>
  );
};

export default Layout;
