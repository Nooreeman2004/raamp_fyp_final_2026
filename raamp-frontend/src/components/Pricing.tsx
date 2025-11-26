import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Check } from "lucide-react";

const Pricing = () => {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-card via-background to-card">
        <div className="absolute inset-0 opacity-20" 
             style={{ backgroundImage: 'radial-gradient(circle at 30% 50%, hsl(var(--glow-primary) / 0.15), transparent 70%)' }} 
        />
      </div>

      <div className="container relative z-10 mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Flexible Pricing for RAAMP
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Choose the pricing model that best fits your business needs
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Pay-As-You-Go Card */}
          <Link to="/dashboard/billing">
            <Card className="p-8 card-shadow bg-card/70 backdrop-blur-sm border-primary/20 hover:border-primary/40 transition-all duration-300 group cursor-pointer h-full">
              <div className="space-y-6">
                <h3 className="text-3xl font-bold text-primary group-hover:text-primary/90 transition-colors">
                  Pay-As-You-Go
                </h3>
                
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground">
                      Fixed-rate pricing with no upfront costs.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground">
                      Cancel anytime with monthly billing.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground">
                      Perfect for small to medium businesses.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </Link>

          {/* Credits Model Card */}
          <Link to="/dashboard/billing">
            <Card className="p-8 card-shadow bg-card/70 backdrop-blur-sm border-primary/20 hover:border-primary/40 transition-all duration-300 group cursor-pointer h-full">
              <div className="space-y-6">
                <h3 className="text-3xl font-bold text-primary group-hover:text-primary/90 transition-colors">
                  Credits Model
                </h3>
                
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground">
                      Discounted tiered pricing with a $2,500 credit minimum.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground">
                      Credits are fully refundable and do not expire.
                    </p>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-4 h-4 text-primary" />
                    </div>
                    <p className="text-foreground">
                      Ideal for high-volume enterprise users.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Decorative bottom line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
    </section>
  );
};

export default Pricing;
