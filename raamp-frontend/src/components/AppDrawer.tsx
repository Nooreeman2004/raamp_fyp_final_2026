import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { 
  Menu,
  LayoutDashboard, 
  MapPin, 
  Sparkles, 
  BarChart3,
  MessageSquare,
  TrendingUp as TrendIcon,
  FlaskConical as Flask,
  User,
  Building2,
  Settings,
  CreditCard,
  LogOut,
  X,
  ChevronRight,
  Home,
  BookOpen,
  Info,
  Scale,
  type LucideIcon
} from "lucide-react";
import type { UserResponse } from "@/types";
import { useToast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";
import ConfirmationDialog from "@/components/ConfirmationDialog";

interface AppDrawerProps {
  user: UserResponse | null;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface NavItem {
  label: string;
  icon: LucideIcon;
  href: string;
  badge?: string;
  description?: string;
}

const AppDrawer = ({ user }: AppDrawerProps) => {
  const [open, setOpen] = useState(false);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  const dashboardItems: NavItem[] = [
    { 
      label: "Dashboard", 
      icon: LayoutDashboard, 
      href: "/dashboard",
      description: "Overview & Analytics"
    },
    { 
      label: "Geo-Intent", 
      icon: MapPin, 
      href: "/dashboard/geo-intent",
      description: "Location-based targeting"
    },
    { 
      label: "Creative Studio", 
      icon: Sparkles, 
      href: "/dashboard/creative",
      description: "AI content generation"
    },
    { 
      label: "Trend Arbitrage", 
      icon: TrendIcon, 
      href: "/dashboard/trends",
      description: "Real-time trend detection"
    },
    { 
      label: "A/B Testing", 
      icon: Flask, 
      href: "/dashboard/ab-testing",
      description: "Campaign optimization"
    },
    { 
      label: "Performance", 
      icon: BarChart3, 
      href: "/dashboard/performance",
      description: "Metrics & insights"
    },
    { 
      label: "RAAMP Assistant", 
      icon: MessageSquare, 
      href: "/dashboard/assistant",
      badge: "AI",
      description: "Chat-based help"
    },
  ];

  const profileItems: NavItem[] = [
    { label: "User Profile", icon: User, href: "/profile/user" },
    { label: "Personal Details", icon: User, href: "/profile/personal-details" },
    { label: "Business Setup", icon: Building2, href: "/profile/business-setup" },
    { label: "Brand Settings", icon: Settings, href: "/profile/brand-settings" },
    { label: "Onboarding", icon: Settings, href: "/profile/onboarding" },
  ];

  const billingItems: NavItem[] = [
    { label: "Billing Overview", icon: CreditCard, href: "/billing" },
    { label: "Add Funds", icon: CreditCard, href: "/billing/add-funds" },
    { label: "Transactions", icon: CreditCard, href: "/billing/transactions" },
  ];

  const publicItems: NavItem[] = [
    { label: "Home", icon: Home, href: "/" },
    { label: "About", icon: Info, href: "/about" },
    { label: "Resources", icon: BookOpen, href: "/resources" },
    { label: "Legal", icon: Scale, href: "/legal" },
  ];

  const navSections: NavSection[] = [
    { title: "Dashboard", items: dashboardItems },
    { title: "Profile", items: profileItems },
    { title: "Billing", items: billingItems },
    { title: "Information", items: publicItems },
  ];

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
          className="w-[300px] sm:w-[380px] p-0 flex flex-col bg-gradient-to-b from-card via-card/95 to-card/90"
        >
          {/* Header */}
          <SheetHeader className="p-6 pb-4 border-b border-primary/10">
            <div className="flex items-center justify-between">
              <Link 
                to="/" 
                className="flex items-center gap-3 group"
                onClick={() => setOpen(false)}
              >
                <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
                <SheetTitle className="text-xl font-bold text-primary">RAAMP</SheetTitle>
              </Link>
            </div>
          </SheetHeader>

          {/* User Profile Section */}
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
            {navSections.map((section, sectionIdx) => (
              <div key={section.title} className="mb-6">
                <h3 className="px-6 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {section.title}
                </h3>
                <nav className="space-y-1 px-3">
                  {section.items.map((item) => {
                    const Icon = item.icon;
                    const active = isActive(item.href);
                    return (
                      <Link
                        key={item.href}
                        to={item.href}
                        onClick={() => setOpen(false)}
                        className={`
                          group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                          ${active 
                            ? 'bg-primary/10 text-primary font-medium shadow-sm' 
                            : 'hover:bg-primary/5 text-foreground/80 hover:text-foreground'
                          }
                        `}
                      >
                        <Icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm truncate">{item.label}</span>
                            {item.badge && (
                              <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-primary/20 text-primary">
                                {item.badge}
                              </span>
                            )}
                          </div>
                          {item.description && !active && (
                            <p className="text-xs text-muted-foreground truncate mt-0.5">
                              {item.description}
                            </p>
                          )}
                        </div>
                        <ChevronRight className={`w-4 h-4 transition-transform ${active ? 'text-primary' : 'text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-0.5'}`} />
                      </Link>
                    );
                  })}
                </nav>
                {sectionIdx < navSections.length - 1 && (
                  <Separator className="mt-4 mx-6" />
                )}
              </div>
            ))}
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
                <LogOut className="w-5 h-5" />
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
