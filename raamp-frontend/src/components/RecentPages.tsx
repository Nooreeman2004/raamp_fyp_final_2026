import { useNavigate } from "react-router-dom";
import { useRecentPages } from "@/hooks/useRecentPages";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Clock, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface RecentPagesProps {
  className?: string;
  maxItems?: number;
}

export default function RecentPages({ className, maxItems = 5 }: RecentPagesProps) {
  const navigate = useNavigate();
  const { recentPages, clearRecentPages } = useRecentPages();

  if (recentPages.length === 0) {
    return null;
  }

  const displayPages = recentPages.slice(0, maxItems);

  return (
    <Card className={cn("p-4 bg-card/50 backdrop-blur-sm border-primary/10", className)}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Recent Pages</h3>
        </div>
        {recentPages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearRecentPages}
            className="h-6 px-2 text-xs"
          >
            <X className="w-3 h-3 mr-1" />
            Clear
          </Button>
        )}
      </div>
      <div className="space-y-1">
        {displayPages.map((page) => (
          <Button
            key={page.path}
            variant="ghost"
            size="sm"
            onClick={() => navigate(page.path)}
            className="w-full justify-start text-xs h-8 text-muted-foreground hover:text-foreground"
          >
            {page.label}
          </Button>
        ))}
      </div>
    </Card>
  );
}

