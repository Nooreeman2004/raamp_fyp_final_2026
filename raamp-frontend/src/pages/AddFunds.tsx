import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Zap, DollarSign, TrendingUp } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, zoomIn, fadeIn } from "@/utils/animations";

const AddFunds = () => {
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmount, setCustomAmount] = useState<number[]>([1000]);

  const presetAmounts = [100, 500, 1000, 2500, 5000];

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b border-primary/10 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <Reveal variant="fadeInDown" duration={0.5} className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center gap-2">
              <motion.div 
                whileHover={{ rotate: 15, scale: 1.1 }}
                className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center"
              >
                <Zap className="w-5 h-5 text-primary" />
              </motion.div>
              <span className="text-xl font-bold">RAAMP</span>
            </Link>
          </div>
        </Reveal>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8 max-w-4xl mx-auto">
          {/* Header */}
          <Reveal variant="blurInUp">
            <div>
              <h1 className="text-4xl font-bold mb-2">Add Funds & Set Budget</h1>
              <p className="text-muted-foreground">
                Efficiently manage your marketing budget with precision
              </p>
            </div>
          </Reveal>

          {/* Current Budget Overview - Fade In Up */}
          <Reveal variant="fadeInUp" delay={0.2}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                Current Budget Overview
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Visualize your available funds at a glance
              </p>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold">$7,500</span>
                  <span className="text-muted-foreground">of $20,000 Budget</span>
                </div>
                <div className="h-4 bg-muted rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    whileInView={{ width: '37.5%' }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-primary breathing-glow" 
                  />
                </div>
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Available Budget</span>
                  <span>37.5% remaining</span>
                </div>
              </div>
            </Card>
          </Reveal>

          {/* Select or Enter Amount - Fade In Up */}
          <Reveal variant="fadeInUp" delay={0.3}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-primary" />
                Select or Enter Amount
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Choose a predefined amount or enter a custom value
              </p>

              {/* Predefined Amounts */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                {presetAmounts.map((amount) => (
                  <motion.div key={amount} variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button
                      variant={selectedAmount === amount ? "hero" : "outline"}
                      onClick={() => {
                        setSelectedAmount(amount);
                        setCustomAmount([amount]);
                      }}
                      className="h-16 text-lg w-full"
                    >
                      ${amount.toLocaleString()}
                    </Button>
                  </motion.div>
                ))}
              </div>

              <div className="text-center text-sm text-muted-foreground mb-4">Or</div>

              {/* Custom Amount */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Custom Amount: ${customAmount[0].toLocaleString()}</label>
                  <Input
                    type="number"
                    value={customAmount[0]}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 0;
                      setCustomAmount([value]);
                      setSelectedAmount(null);
                    }}
                    className="bg-background/50"
                    placeholder="Enter custom amount"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Adjust Budget Range</label>
                  <Slider
                    value={customAmount}
                    onValueChange={(value) => {
                      setCustomAmount(value);
                      setSelectedAmount(null);
                    }}
                    max={10000}
                    min={100}
                    step={100}
                    className="mb-2"
                  />
                  <p className="text-xs text-muted-foreground">Adjusting to: ${customAmount[0].toLocaleString()}</p>
                </div>
              </div>
            </Card>
          </Reveal>

          {/* Finalize Payment - Fade In Up */}
          <Reveal variant="fadeInUp" delay={0.4}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-xl font-bold mb-4">Finalize Payment</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Confirm the amount and process your payment securely
              </p>

              <div className="p-6 bg-primary/5 rounded-lg border border-primary/20 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-lg font-medium">Amount to Add:</span>
                  <span className="text-3xl font-bold text-primary">
                    ${(selectedAmount || customAmount[0]).toLocaleString()}.00
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>New Total Budget:</span>
                  <span className="font-medium">
                    ${(7500 + (selectedAmount || customAmount[0])).toLocaleString()}.00
                  </span>
                </div>
              </div>

              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button variant="hero" size="lg" className="w-full">
                  <DollarSign className="w-5 h-5 mr-2" />
                  Process Payment: ${(selectedAmount || customAmount[0]).toLocaleString()}.00
                </Button>
              </motion.div>

              <p className="text-xs text-center text-muted-foreground mt-4">
                Your payment will be processed securely using your saved payment method
              </p>
            </Card>
          </Reveal>
        </div>
      </main>
    </div>
  );
};

export default AddFunds;