import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { CheckCircle2, Clock, AlertCircle, Loader2 } from "lucide-react";

const statusBadgeVariants = cva(
    "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                success: "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20",
                pending: "bg-amber-500/10 text-amber-500 border border-amber-500/20",
                failed: "bg-red-500/10 text-red-500 border border-red-500/20",
                processing: "bg-teal-500/10 text-teal-500 border border-teal-500/20",
                neutral: "bg-gray-500/10 text-gray-500 border border-gray-500/20",
            },
        },
        defaultVariants: {
            variant: "neutral",
        },
    }
);

export interface StatusBadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof statusBadgeVariants> {
    status: string;
}

const StatusBadge = React.forwardRef<HTMLDivElement, StatusBadgeProps>(
    ({ className, status, ...props }, ref) => {
        const s = status.toLowerCase();

        // Map various backend statuses to primary UI variants
        let variant: "success" | "pending" | "failed" | "processing" | "neutral" = "neutral";
        let Icon = null;

        if (s === "published" || s === "posted" || s === "success") {
            variant = "success";
            Icon = CheckCircle2;
        } else if (s === "pending" || s === "queued" || s === "scheduled") {
            variant = "pending";
            Icon = Clock;
        } else if (s === "failed" || s === "error") {
            variant = "failed";
            Icon = AlertCircle;
        } else if (s === "processing" || s === "uploading") {
            variant = "processing";
            Icon = Loader2;
        }

        return (
            <div
                ref={ref}
                className={cn(statusBadgeVariants({ variant }), "gap-1.5 px-3 py-1", className)}
                {...props}
            >
                {Icon && <Icon className={cn("w-3.5 h-3.5", variant === "processing" && "animate-spin")} />}
                <span className="text-[11px] font-bold tracking-tight">{status.toUpperCase()}</span>
            </div>
        );
    }
);

StatusBadge.displayName = "StatusBadge";

export { StatusBadge, statusBadgeVariants };
