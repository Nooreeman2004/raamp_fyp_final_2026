import React from "react";
import { AlertCircle, ArrowRight, Instagram, Facebook } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

interface GlobalConnectionBannerProps {
    instagramConnected?: boolean;
    facebookConnected?: boolean;
    className?: string;
}

export const GlobalConnectionBanner: React.FC<GlobalConnectionBannerProps> = ({
    instagramConnected = true,
    facebookConnected = true,
    className
}) => {
    if (instagramConnected && facebookConnected) return null;

    return (
        <div className={cn(
            "relative overflow-hidden rounded-xl border p-4 shadow-sm transition-all",
            "bg-destructive/5 border-destructive/20",
            className
        )}>
            {/* Background decoration */}
            <div className="absolute -right-4 -top-4 w-24 h-24 bg-destructive/5 rounded-full blur-2xl" />

            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
                <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
                        <AlertCircle className="w-5 h-5 text-destructive" />
                    </div>
                    <div>
                        <h4 className="font-bold text-white/90 tracking-tight">Accounts Disconnected</h4>
                        <p className="text-sm text-muted-foreground/80 mt-0.5 max-w-lg">
                            Some of your social accounts are not connected or their session has expired.
                            This will prevent automated posting and scheduling.
                        </p>

                        <div className="flex items-center gap-3 mt-3">
                            <div className={cn(
                                "flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest border",
                                instagramConnected ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : "bg-red-500/10 border-red-500/20 text-red-400"
                            )}>
                                <Instagram className="w-3 h-3" />
                                Instagram: {instagramConnected ? "Active" : "Disconnected"}
                            </div>
                            <div className={cn(
                                "flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest border",
                                facebookConnected ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : "bg-red-500/10 border-red-500/20 text-red-400"
                            )}>
                                <Facebook className="w-3 h-3" />
                                Facebook: {facebookConnected ? "Active" : "Disconnected"}
                            </div>
                        </div>
                    </div>
                </div>

                <Button asChild variant="destructive" className="h-10 px-6 gap-2 shadow-lg shadow-destructive/20">
                    <Link to="/dashboard/onboarding">
                        Reconnect Now
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </Button>
            </div>
        </div>
    );
};
