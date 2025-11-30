import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Zap, CreditCard, DollarSign, FileText } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, hoverLift } from "@/utils/animations";

const Billing = () => {
  const transactions = [
    { date: "2024-07-25", description: "RAAMP Monthly Subscription", amount: "-$499.00", type: "debit" },
    { date: "2024-07-20", description: "Geo-Intent Engine Data Pack (Premium)", amount: "-$120.00", type: "debit" },
    { date: "2024-07-18", description: "Creative Studio Asset Purchase", amount: "-$50.00", type: "debit" },
    { date: "2024-07-15", description: "Account Top-up via Credit Card", amount: "$500.00", type: "credit" },
    { date: "2024-07-10", description: "A/B Auto-Optimization Upgrade", amount: "-$99.00", type: "debit" },
    { date: "2024-07-05", description: "RAAMP Assistant Premium Access", amount: "-$75.00", type: "debit" },
    { date: "2024-07-01", description: "Initial Account Setup Fee", amount: "-$25.00", type: "debit" }
  ];

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
        <div className="space-y-8 max-w-6xl mx-auto">
          {/* Header */}
          <Reveal variant="blurInUp">
            <div>
              <h1 className="text-4xl font-bold mb-2">Billing & Payment Methods</h1>
              <p className="text-muted-foreground">
                Manage your payment methods, view transactions, and control your marketing budget
              </p>
            </div>
          </Reveal>

          <motion.div 
            className="grid lg:grid-cols-2 gap-6"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            {/* Current Payment Method */}
            <motion.div variants={fadeInUp}>
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-primary" />
                    Current Payment Method
                  </h2>
                  <p className="text-sm text-muted-foreground mb-6">
                    Your primary method for payments and subscriptions
                  </p>

                  <div className="p-4 bg-muted/50 rounded-lg mb-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <CreditCard className="w-6 h-6 text-primary" />
                        <div>
                          <p className="font-bold">Visa ending in 1234</p>
                          <p className="text-sm text-muted-foreground">Expires 12/26</p>
                        </div>
                      </div>
                      <Badge>Primary</Badge>
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      Manage
                    </Button>
                  </div>

                  <div className="space-y-3">
                    <Link to="/billing/add-funds">
                      <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="w-full">
                        <Button variant="hero" className="w-full justify-start">
                          <DollarSign className="w-4 h-4 mr-2" />
                          Add Funds / Set Budget
                        </Button>
                      </motion.div>
                    </Link>
                    <Link to="/billing/transactions">
                      <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="w-full">
                        <Button variant="outline" className="w-full justify-start">
                          <FileText className="w-4 h-4 mr-2" />
                          View Transaction History
                        </Button>
                      </motion.div>
                    </Link>
                  </div>
                </Card>
              </motion.div>
            </motion.div>

            {/* Add New Payment Method */}
            <motion.div variants={fadeInUp}>
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4">Add New Payment Method</h2>
                  <p className="text-sm text-muted-foreground mb-6">
                    Securely add a new credit or debit card to your account
                  </p>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="cardNumber">Card Number</Label>
                      <Input
                        id="cardNumber"
                        placeholder="**** **** **** ****"
                        className="bg-background/50"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="cardholderName">Cardholder Name</Label>
                      <Input
                        id="cardholderName"
                        placeholder="John Doe"
                        className="bg-background/50"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="expiryDate">Expiration Date</Label>
                        <Input
                          id="expiryDate"
                          placeholder="MM/YY"
                          className="bg-background/50"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="cvv">CVV</Label>
                        <Input
                          id="cvv"
                          placeholder="***"
                          type="password"
                          maxLength={3}
                          className="bg-background/50"
                        />
                      </div>
                    </div>

                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                      <Button variant="hero" className="w-full mt-4">
                        Save Payment Method
                      </Button>
                    </motion.div>
                  </div>
                </Card>
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Other Payment Options */}
          <Reveal variant="fadeInUp" delay={0.4}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-xl font-bold mb-4">Other Payment Options</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Manage your alternative payment sources
              </p>

              <div className="p-4 bg-muted/50 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">PayPal Account</p>
                    <p className="text-sm text-muted-foreground">verified@example.com</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  Disconnect
                </Button>
              </div>
            </Card>
          </Reveal>
        </div>
      </main>
    </div>
  );
};

export default Billing;