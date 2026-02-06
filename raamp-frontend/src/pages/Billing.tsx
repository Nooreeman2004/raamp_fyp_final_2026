import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { CreditCard, DollarSign, FileText, Wallet } from "lucide-react";
import Layout from "@/components/Layout";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

const Billing = () => {
  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Billing & Finance" }]}>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-primary/10 rounded border border-primary/30">
              <Wallet className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
                <BlurText text="BILLING & FINANCE" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                // MANAGE BUDGET // TRANSACTION HISTORY // PAYMENT METHODS
              </p>
            </div>
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
            <HolographicCard className="p-6 h-full border-primary/30">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-bebas tracking-wide text-white">
                <CreditCard className="w-5 h-5 text-primary" />
                CURRENT PAYMENT METHOD
              </h2>
              <p className="text-xs text-muted-foreground mb-6 font-mono">
                  // PRIMARY SOURCE FOR SUBSCRIPTIONS & AD SPEND
              </p>

              <div className="p-4 bg-white/5 rounded border border-white/10 mb-6 relative overflow-hidden group">
                {/* Card Shine Effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />

                <div className="flex items-center justify-between mb-3 relative z-10">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                      <CreditCard className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-bold text-white font-mono">VISA ENDING IN 1234</p>
                      <p className="text-xs text-muted-foreground font-mono">EXPIRES 12/26</p>
                    </div>
                  </div>
                  <Badge className="bg-primary text-primary-foreground hover:bg-primary/90 font-mono text-[10px]">PRIMARY</Badge>
                </div>
                <Button variant="outline" size="sm" className="w-full border-white/10 text-white hover:bg-white/10 font-mono text-xs h-8">
                  MANAGE CARD
                </Button>
              </div>

              <div className="space-y-3">
                <Link to="/billing/add-funds">
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="w-full">
                    <Button className="w-full justify-start bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-bebas tracking-wider h-10">
                      <DollarSign className="w-4 h-4 mr-2" />
                      ADD FUNDS / SET BUDGET
                    </Button>
                  </motion.div>
                </Link>
                <Link to="/billing/transactions">
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="w-full">
                    <Button variant="outline" className="w-full justify-start border-white/10 text-white hover:bg-white/10 hover:text-primary hover:border-primary/30 font-mono text-xs h-10">
                      <FileText className="w-4 h-4 mr-2" />
                      VIEW TRANSACTION HISTORY
                    </Button>
                  </motion.div>
                </Link>
              </div>
            </HolographicCard>
          </motion.div>

          {/* Add New Payment Method */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-6 h-full">
              <h2 className="text-xl font-bold mb-4 font-bebas tracking-wide text-white">ADD NEW PAYMENT METHOD</h2>
              <p className="text-xs text-muted-foreground mb-6 font-mono">
                  // SECURE ENCRYPTED CONNECTION
              </p>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="cardNumber" className="text-xs font-mono text-muted-foreground">CARD NUMBER</Label>
                  <Input
                    id="cardNumber"
                    placeholder="**** **** **** ****"
                    className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cardholderName" className="text-xs font-mono text-muted-foreground">CARDHOLDER NAME</Label>
                  <Input
                    id="cardholderName"
                    placeholder="JOHN DOE"
                    className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10 uppercase"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="expiryDate" className="text-xs font-mono text-muted-foreground">EXPIRATION DATE</Label>
                    <Input
                      id="expiryDate"
                      placeholder="MM/YY"
                      className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cvv" className="text-xs font-mono text-muted-foreground">CVV</Label>
                    <Input
                      id="cvv"
                      placeholder="***"
                      type="password"
                      maxLength={3}
                      className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                    />
                  </div>
                </div>

                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Button className="w-full mt-4 bg-white/10 hover:bg-primary hover:text-primary-foreground text-white border border-white/20 hover:border-primary transition-all font-mono font-bold text-xs h-10">
                    SAVE PAYMENT METHOD
                  </Button>
                </motion.div>
              </div>
            </HolographicCard>
          </motion.div>
        </motion.div>

        {/* Other Payment Options */}
        <Reveal variant="fadeInUp" delay={0.4}>
          <HolographicCard className="p-6">
            <h2 className="text-xl font-bold mb-4 font-bebas tracking-wide text-white">OTHER PAYMENT OPTIONS</h2>
            <p className="text-xs text-muted-foreground mb-6 font-mono">
                // ALTERNATIVE FUNDING SOURCES
            </p>

            <div className="p-4 bg-white/5 rounded border border-white/10 flex items-center justify-between hover:border-primary/30 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded bg-white/10 flex items-center justify-center">
                  <CreditCard className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-bold text-white font-mono text-sm">PAYPAL ACCOUNT</p>
                  <p className="text-xs text-muted-foreground font-mono">verified@example.com</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300 hover:bg-red-500/10 font-mono text-xs">
                DISCONNECT
              </Button>
            </div>
          </HolographicCard>
        </Reveal>
      </div>
    </Layout>
  );
};

export default Billing;