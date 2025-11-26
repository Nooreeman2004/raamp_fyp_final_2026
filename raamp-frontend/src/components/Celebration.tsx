import { useEffect, useState } from "react";
import { CheckCircle, Sparkles, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";

interface CelebrationProps {
  message: string;
  type?: "success" | "milestone" | "achievement";
  onComplete?: () => void;
  duration?: number;
}

export default function Celebration({ 
  message, 
  type = "success",
  onComplete,
  duration = 3000 
}: CelebrationProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => onComplete?.(), 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onComplete]);

  const icons = {
    success: CheckCircle,
    milestone: Sparkles,
    achievement: Trophy,
  };

  const Icon = icons[type];

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
      <div
        className={cn(
          "bg-card border-2 rounded-lg shadow-2xl p-8 max-w-md mx-4 transform transition-all duration-300",
          isVisible ? "scale-100 opacity-100" : "scale-95 opacity-0",
          type === "milestone" && "border-primary",
          type === "achievement" && "border-amber-500"
        )}
      >
        <div className="flex flex-col items-center text-center space-y-4">
          <div
            className={cn(
              "w-20 h-20 rounded-full flex items-center justify-center animate-bounce",
              type === "success" && "bg-emerald-500/20 text-emerald-500",
              type === "milestone" && "bg-primary/20 text-primary",
              type === "achievement" && "bg-amber-500/20 text-amber-500"
            )}
          >
            <Icon className="w-10 h-10" />
          </div>
          <div className="space-y-2">
            <h3 className="text-2xl font-bold">{message}</h3>
            {type === "milestone" && (
              <p className="text-sm text-muted-foreground">Keep up the great work!</p>
            )}
            {type === "achievement" && (
              <p className="text-sm text-muted-foreground">You've unlocked a new achievement!</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

