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
    CreditCard,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    User,
    Bell,
    Search,
    Command,
    Info,
    BookOpen,
    Scale,
    Calendar
} from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { authService } from "@/services/authService";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";

const menuItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
    { icon: MapPin, label: "Geo-Intent", href: "/dashboard/geo-intent" },
    { icon: Sparkles, label: "Creative Studio", href: "/dashboard/creative" },
    { icon: Calendar, label: "Smart Scheduling", href: "/dashboard/smart-scheduling" },
    { icon: TrendingUp, label: "Trend Arbitrage", href: "/dashboard/trends" },
    { icon: FlaskConical, label: "A/B Testing", href: "/dashboard/ab-testing" },
    { icon: BarChart3, label: "Performance", href: "/dashboard/performance" },
    { icon: CreditCard, label: "Billing", href: "/billing" },
];

const bottomItems = [
    { icon: Bell, label: "Notifications", href: "/notifications" },
    { icon: Settings, label: "Settings", href: "/settings" },
];

const infoItems = [
    { icon: Info, label: "About Us", href: "/about" },
    { icon: BookOpen, label: "Resources", href: "/resources" },
    { icon: Scale, label: "Legal", href: "/legal" },
];

import { useNotifications } from "@/contexts/NotificationContext";

export const Sidebar = ({ collapsed, setCollapsed }: { collapsed: boolean; setCollapsed: (v: boolean) => void }) => {
    const location = useLocation();
    const navigate = useNavigate();
    const notificationContext = useNotifications();
    const unreadCount = notificationContext?.unreadCount || 0;

    const handleLogout = async () => {
        await authService.logout();
        navigate("/login");
    };

    return (
        <motion.div
            initial={{ width: 240 }}
            animate={{ width: collapsed ? 80 : 240 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className={cn(
                "fixed left-0 top-0 h-screen z-50 flex flex-col border-r border-white/10 bg-black/40 backdrop-blur-xl transition-all duration-300",
                "hidden lg:flex" // Hide on mobile
            )}
        >
            {/* Header */}
            <div className="h-20 flex items-center px-6 border-b border-white/5 relative">
                <Link to="/dashboard" className="flex items-center gap-3 overflow-hidden">
                    <div className="relative flex-shrink-0">
                        <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full opacity-50" />
                        <img src={raampIcon} alt="Logo" className="w-8 h-8 relative z-10" />
                    </div>
                    <motion.span
                        animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                        className="font-bebas text-xl tracking-wider text-white whitespace-nowrap overflow-hidden"
                    >
                        RAAMP
                    </motion.span>
                </Link>

                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-black border border-white/20 rounded-full flex items-center justify-center text-white/50 hover:text-white hover:border-primary/50 transition-all z-50"
                >
                    {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
                </button>
            </div>

            {/* Command Shortcut Hint */}
            {!collapsed && (
                <div className="px-4 py-4">
                    <button
                        onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/5 text-xs text-muted-foreground hover:bg-white/10 hover:border-white/10 transition-all group"
                    >
                        <Search size={14} />
                        <span className="flex-1 text-left">Search...</span>
                        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-white/10 bg-black px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100 group-hover:text-white">
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
                                        "flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                        isActive
                                            ? "bg-primary/10 text-primary shadow-[0_0_20px_rgba(0,224,208,0.1)]"
                                            : "text-muted-foreground hover:text-white hover:bg-white/5"
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
                                <TooltipContent side="right" className="bg-black/90 border-white/10 text-white">
                                    {item.label}
                                </TooltipContent>
                            )}
                        </Tooltip>
                    );
                })}
            </div>

            {/* Bottom Section */}
            <div className="p-3 border-t border-white/5 space-y-2 bg-black/20">
                {bottomItems.map((item) => (
                    <Tooltip key={item.href} delayDuration={0}>
                        <TooltipTrigger asChild>
                            <Link
                                to={item.href}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-muted-foreground hover:text-white hover:bg-white/5 relative",
                                    location.pathname === item.href && "text-white bg-white/5"
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
                                        "absolute bg-destructive text-white text-[10px] font-bold flex items-center justify-center rounded-full",
                                        collapsed ? "top-1 right-1 w-3 h-3 p-0" : "right-3 w-5 h-5"
                                    )}>
                                        {!collapsed && (unreadCount > 99 ? '99+' : unreadCount)}
                                    </div>
                                )}
                            </Link>
                        </TooltipTrigger>
                        {collapsed && (
                            <TooltipContent side="right" className="bg-black/90 border-white/10 text-white">
                                {item.label} {item.label === "Notifications" && unreadCount > 0 && `(${unreadCount})`}
                            </TooltipContent>
                        )}
                    </Tooltip>
                ))}

                <Separator className="bg-white/5 my-2" />

                {infoItems.map((item) => (
                    <Tooltip key={item.href} delayDuration={0}>
                        <TooltipTrigger asChild>
                            <Link
                                to={item.href}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group text-muted-foreground hover:text-white hover:bg-white/5",
                                    location.pathname === item.href && "text-white bg-white/5"
                                )}
                            >
                                <item.icon size={18} className="flex-shrink-0 opacity-50 group-hover:opacity-100 transition-opacity" />
                                <motion.span
                                    animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                                    className="font-medium text-[11px] whitespace-nowrap overflow-hidden uppercase tracking-wider opacity-60 group-hover:opacity-100 transition-opacity"
                                >
                                    {item.label}
                                </motion.span>
                            </Link>
                        </TooltipTrigger>
                        {collapsed && (
                            <TooltipContent side="right" className="bg-black/90 border-white/10 text-white">
                                {item.label}
                            </TooltipContent>
                        )}
                    </Tooltip>
                ))}

                <Separator className="bg-white/5 my-2" />

                <Tooltip delayDuration={0}>
                    <TooltipTrigger asChild>
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        >
                            <LogOut size={20} className="flex-shrink-0" />
                            <motion.span
                                animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                                className="font-medium text-sm whitespace-nowrap overflow-hidden"
                            >
                                Sign Out
                            </motion.span>
                        </button>
                    </TooltipTrigger>
                    {collapsed && (
                        <TooltipContent side="right" className="bg-red-900/90 border-red-500/20 text-white">
                            Sign Out
                        </TooltipContent>
                    )}
                </Tooltip>
            </div>
        </motion.div>
    );
};
