import { Search, Sparkles, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";

const steps = [
  {
    icon: Search,
    title: "Detect Geo-Intent",
    description: "Leverage advanced AI to identify and analyze real-time geo-intent signals, uncovering hyper-local market opportunities you're missing",
  },
  {
    icon: Sparkles,
    title: "Generate & Test",
    description: "Automatically create, test, and optimize campaign variations with predictive analytics, ensuring maximum impact for every ad dollar",
  },
  {
    icon: TrendingUp,
    title: "Explain & Iterate",
    description: "Receive clear, actionable insights into campaign performance, continuously refining strategies for sustained growth and superior ROI",
  },
];

const HowItWorks = () => {
  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            How RAAMP Works: The{" "}
            <span className="text-primary">Autonomous Optimization Loop</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto relative">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative">
                <Card className="card-shadow bg-card/50 backdrop-blur-sm border-primary/20 p-8 h-full hover:border-primary/40 transition-all duration-300">
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center breathing-glow">
                      <Icon className="w-8 h-8 text-primary" />
                    </div>
                    <h3 className="text-2xl font-bold">{step.title}</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </Card>
                
                {/* Connection line */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-px bg-gradient-to-r from-primary/50 to-transparent z-10" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
