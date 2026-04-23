import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    MapPin,
    Sparkles,
    BarChart3,
    TrendingUp,
    FlaskConical,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    Bell,
    Search,
    Calendar,
    CalendarDays,
    Images,
    ShieldCheck,
    MessageSquare,
    LifeBuoy,
    AlertTriangle
} from "lucide-react";
import { authService } from "@/services/authService";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { BrandMark } from "@/components/BrandMark";
import { toast } from "sonner";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const menuItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
    { icon: MapPin, label: "Geo-Intent", href: "/dashboard/geo-intent" },
    { icon: Sparkles, label: "Creative Studio", href: "/dashboard/creative" },
    { icon: Images, label: "Asset Library", href: "/dashboard/assets" },
    { icon: Calendar, label: "Smart Scheduling", href: "/dashboard/smart-scheduling" },
    { icon: CalendarDays, label: "Campaign Planner", href: "/dashboard/campaign-planner" },
    { icon: TrendingUp, label: "Trend Arbitrage", href: "/dashboard/trends" },
    { icon: ShieldCheck, label: "Approvals", href: "/dashboard/approvals" },
    { icon: MessageSquare, label: "Auto Replies", href: "/dashboard/auto-replies" },
    { icon: AlertTriangle, label: "Social Moderation", href: "/dashboard/escalations" },
    { icon: FlaskConical, label: "The Lab (A/B)", href: "/dashboard/ab-optimizer" },
];

const bottomItems = [
    { icon: LifeBuoy, label: "Support", href: "/dashboard/complaints" },
    { icon: Bell, label: "Notifications", href: "/notifications" },
    { icon: Settings, label: "Settings", href: "/settings" },
];

import { useNotifications } from "@/contexts/NotificationContext";

export const Sidebar = ({ collapsed, setCollapsed }: { collapsed: boolean; setCollapsed: (v: boolean) => void }) => {
    const location = useLocation();
    const navigate = useNavigate();
    const notificationContext = useNotifications();
    const unreadCount = notificationContext?.unreadCount || 0;

    const handleLogout = async () => {
        try {
            await authService.logout();
        } catch {
            // Don't block sign-out UX on network/server failures
            toast.message("Signed out locally", {
                description: "We couldn’t reach the server, but this device has been signed out.",
            });
        } finally {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            sessionStorage.removeItem("token");
            sessionStorage.removeItem("user");
            navigate("/login");
        }
    };

    return (
        <motion.div
            initial={{ width: 240 }}
            animate={{ width: collapsed ? 80 : 240 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className={cn(
                "fixed left-0 top-0 h-screen z-50 flex flex-col border-r border-border/50 bg-card backdrop-blur-xl transition-all duration-300",
                "hidden lg:flex" // Hide on mobile
            )}
        >
            {/* Header */}
            <div className="h-20 flex items-center px-6 border-b border-border relative">
                <Link to="/dashboard" className="flex items-center gap-3 overflow-hidden">
                    <div className="relative flex-shrink-0">
                        <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full opacity-50" />
                        <BrandMark variant="sidebar" size={32} className="relative z-10" />
                    </div>
                    <motion.span
                        animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                        className="font-heading font-semibold text-xl tracking-wider text-foreground whitespace-nowrap overflow-hidden"
                    >
                        RAAMP
                    </motion.span>
                </Link>

                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-background border border-border/80 rounded-full flex items-center justify-center text-muted-foreground/80 hover:text-foreground hover:border-primary/50 transition-all z-50"
                >
                    {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
                </button>
            </div>

            {/* Command Shortcut Hint */}
            {!collapsed && (
                <div className="px-4 py-4">
                    <button
                        onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
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

            {/* Main Menu */}
            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-2 scrollbar-none">
                {menuItems.map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                        <Tooltip key={item.href} delayDuration={0}>
                            <TooltipTrigger asChild>
                                <Link
                                    to={item.href}
                                    className={cn(
                                        "flex min-h-[2.75rem] items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                        isActive
                                            ? "bg-primary/10 text-primary shadow-[0_0_20px_rgba(0,224,208,0.1)]"
                                            : "text-muted-foreground hover:text-foreground hover:bg-foreground/5"
                                    )}
                                >
                                    {isActive && (
                                        <motion.div
                                            layoutId="activeTab"
                                            className="absolute inset-0 border border-primary/20 rounded-xl"
                                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                        />
                                    )}
                                    <item.icon size={20} className={cn("flex-shrink-0 transition-transform duration-300", isActive && "scale-110")} />
                                    <motion.span
                                        animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                                        className="font-medium text-sm whitespace-nowrap overflow-hidden"
                                    >
                                        {item.label}
                                    </motion.span>

                                    {/* Active Glow Dot */}
                                    {isActive && !collapsed && (
                                        <motion.div
                                            layoutId="activeDot"
                                            className="absolute right-3 w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_10px_#00E0D0]"
                                        />
                                    )}
                                </Link>
                            </TooltipTrigger>
                            {collapsed && (
                                <TooltipContent side="right" className="bg-background/90 border-border/50 text-foreground">
                                    {item.label}
                                </TooltipContent>
                            )}
                        </Tooltip>
                    );
                })}
            </div>

            {/* Bottom Section */}
            <div className="p-3 border-t border-border space-y-2 bg-card/50">
                {bottomItems.map((item) => (
                    <Tooltip key={item.href} delayDuration={0}>
                        <TooltipTrigger asChild>
                            <Link
                                to={item.href}
                                className={cn(
                                    "flex min-h-[2.75rem] items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-muted-foreground hover:text-foreground hover:bg-foreground/5 relative",
                                    location.pathname === item.href && "text-foreground bg-foreground/5"
                                )}
                            >
                                <item.icon size={20} className="flex-shrink-0" />
                                <motion.span
                                    animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                                    className="font-medium text-sm whitespace-nowrap overflow-hidden"
                                >
                                    {item.label}
                                </motion.span>
                                {item.label === "Notifications" && unreadCount > 0 && (
                                    <div className={cn(
                                        "absolute bg-destructive text-foreground text-[10px] font-bold flex items-center justify-center rounded-full",
                                        collapsed ? "top-1 right-1 w-3 h-3 p-0" : "right-3 w-5 h-5"
                                    )}>
                                        {!collapsed && (unreadCount > 99 ? '99+' : unreadCount)}
                                    </div>
                                )}
                            </Link>
                        </TooltipTrigger>
                        {collapsed && (
                            <TooltipContent side="right" className="bg-background/90 border-border/50 text-foreground">
                                {item.label} {item.label === "Notifications" && unreadCount > 0 && `(${unreadCount})`}
                            </TooltipContent>
                        )}
                    </Tooltip>
                ))}

                <AlertDialog>
                    <Tooltip delayDuration={0}>
                        <TooltipTrigger asChild>
                            <AlertDialogTrigger asChild>
                                <button
                                    type="button"
                                    className="w-full flex min-h-[2.75rem] items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                >
                                    <LogOut size={20} className="flex-shrink-0" />
                                    <motion.span
                                        animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                                        className="font-medium text-sm whitespace-nowrap overflow-hidden"
                                    >
                                        Sign Out
                                    </motion.span>
                                </button>
                            </AlertDialogTrigger>
                        </TooltipTrigger>
                        {collapsed && (
                            <TooltipContent side="right" className="bg-red-900/90 border-red-500/20 text-foreground">
                                Sign Out
                            </TooltipContent>
                        )}
                    </Tooltip>

                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Sign out of RAAMP?</AlertDialogTitle>
                            <AlertDialogDescription>
                                You’ll be returned to the login screen. You can sign back in anytime.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                onClick={handleLogout}
                            >
                                Sign out
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </div>
        </motion.div>
    );
};
