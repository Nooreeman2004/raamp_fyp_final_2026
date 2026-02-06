import { Skeleton } from "@/components/ui/skeleton";
import { HolographicCard } from "./holographic-card";

export function CardSkeleton() {
    return (
        <HolographicCard className="p-6">
            <div className="flex items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-4 rounded-full" />
            </div>
            <div className="flex items-baseline justify-between pt-2">
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-5 w-12 rounded-full" />
            </div>
        </HolographicCard>
    );
}

export function ChartSkeleton() {
    return (
        <HolographicCard className="p-6 h-[400px]">
            <div className="flex items-center justify-between mb-6">
                <div className="space-y-2">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-8 w-24" />
            </div>
            <div className="flex-1 flex flex-col gap-4">
                <Skeleton className="w-full h-full min-h-[250px] rounded-lg" />
            </div>
        </HolographicCard>
    );
}
