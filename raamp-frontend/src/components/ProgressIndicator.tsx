import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Step {
  id: string;
  label: string;
  description?: string;
}

interface ProgressIndicatorProps {
  steps: Step[];
  currentStep: number;
  completedSteps?: number[];
  className?: string;
}

export default function ProgressIndicator({ 
  steps, 
  currentStep, 
  completedSteps = [],
  className 
}: ProgressIndicatorProps) {
  const isStepCompleted = (index: number) => completedSteps.includes(index) || index < currentStep;
  const isStepActive = (index: number) => index === currentStep;

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-muted-foreground">
          Step {currentStep + 1} of {steps.length}
        </div>
        <div className="text-sm font-medium">
          {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
        </div>
      </div>
      
      <div className="relative">
        {/* Progress bar background */}
        <div className="absolute top-5 left-0 right-0 h-1 bg-muted rounded-full" />
        
        {/* Progress bar fill */}
        <div 
          className="absolute top-5 left-0 h-1 bg-primary rounded-full transition-all duration-300"
          style={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
        />
        
        {/* Steps */}
        <div className="relative flex justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex flex-col items-center" style={{ flex: 1 }}>
              <div
                className={cn(
                  "relative z-10 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all",
                  isStepCompleted(index)
                    ? "bg-primary border-primary text-primary-foreground"
                    : isStepActive(index)
                    ? "bg-primary/20 border-primary text-primary"
                    : "bg-background border-muted text-muted-foreground"
                )}
              >
                {isStepCompleted(index) ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              <div className="mt-2 text-center max-w-[120px]">
                <div
                  className={cn(
                    "text-xs font-medium",
                    isStepActive(index) || isStepCompleted(index)
                      ? "text-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {step.label}
                </div>
                {step.description && (
                  <div className="text-xs text-muted-foreground mt-1 hidden sm:block">
                    {step.description}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

