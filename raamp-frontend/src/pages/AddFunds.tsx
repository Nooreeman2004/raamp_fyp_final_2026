import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Zap, DollarSign, TrendingUp, Loader2 } from "lucide-react";
import { apiClient } from "@/services/api";
import { toast } from "sonner";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { fadeInUp, hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

const AddFunds = () => {
    const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
    const [customAmount, setCustomAmount] = useState<number[]>([1000]);
    const [walletBalance, setWalletBalance] = useState<number>(0);
    const [loadingWallet, setLoadingWallet] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [searchParams] = useSearchParams();

    const presetAmounts = [100, 500, 1000, 2500, 5000];

    useEffect(() => {
        if (searchParams.get("canceled") === "true") {
            toast.error("Payment was canceled");
        }
    }, [searchParams]);

    useEffect(() => {
        const fetchWallet = async () => {
            try {
                const res = await apiClient.get<{ balance: number }>("/api/billing/wallet");
                setWalletBalance(res.balance);
            } catch {
                // Wallet may not exist yet
                setWalletBalance(0);
            } finally {
                setLoadingWallet(false);
            }
        };
        fetchWallet();
    }, []);

    const handleProcessPayment = async () => {
        const amount = selectedAmount || customAmount[0];
        if (amount <= 0) {
            toast.error("Please select an amount");
            return;
        }
        setProcessing(true);
        try {
            const res = await apiClient.post<{ url: string }>("/stripe/create-addfunds-session", { amount });
            if (res.url) {
                window.location.href = res.url;
            } else {
                toast.error("Could not start checkout. Please try again.");
            }
        } catch {
            toast.error("Failed to start payment. Please try again.");
        } finally {
            setProcessing(false);
        }
    };

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
                            <span className="text-xl font-bold font-bebas tracking-wide">RAAMP</span>
                        </Link>
                    </div>
                </Reveal>
            </nav>

            <main className="container mx-auto px-4 py-8">
                <div className="space-y-8 max-w-4xl mx-auto">
                    {/* Header */}
                    <Reveal variant="blurInUp">
                        <div>
                            <h1 className="text-4xl font-bold mb-2 font-bebas tracking-wide">
                                <BlurText text="Add Funds to Wallet" />
                            </h1>
                            <p className="text-muted-foreground font-mono text-sm">
                                Securely add funds via Stripe — your wallet is updated automatically
                            </p>
                        </div>
                    </Reveal>

                    {/* Current Wallet Balance */}
                    <Reveal variant="fadeInUp" delay={0.2}>
                        <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-bebas tracking-wide">
                                <TrendingUp className="w-5 h-5 text-primary" />
                                Current Wallet Balance
                            </h2>
                            <div className="flex items-center gap-4">
                                {loadingWallet ? (
                                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                                ) : (
                                    <span className="text-3xl font-bold font-mono">${walletBalance.toFixed(2)}</span>
                                )}
                                <span className="text-muted-foreground font-mono text-sm">USD</span>
                            </div>
                        </Card>
                    </Reveal>

                    {/* Select or Enter Amount */}
                    <Reveal variant="fadeInUp" delay={0.3}>
                        <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-bebas tracking-wide">
                                <DollarSign className="w-5 h-5 text-primary" />
                                Select or Enter Amount
                            </h2>
                            <p className="text-sm text-muted-foreground mb-6 font-mono">
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
                                            className="h-16 text-lg w-full font-mono"
                                        >
                                            ${amount.toLocaleString()}
                                        </Button>
                                    </motion.div>
                                ))}
                            </div>

                            <div className="text-center text-sm text-muted-foreground mb-4 font-mono">Or</div>

                            {/* Custom Amount */}
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium font-mono">Custom Amount: ${customAmount[0].toLocaleString()}</label>
                                    <Input
                                        type="number"
                                        value={customAmount[0]}
                                        onChange={(e) => {
                                            const value = parseInt(e.target.value) || 0;
                                            setCustomAmount([Math.min(Math.max(value, 0), 10000)]);
                                            setSelectedAmount(null);
                                        }}
                                        className="bg-background/50 font-mono"
                                        placeholder="Enter custom amount"
                                        min={1}
                                        max={10000}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium font-mono">Adjust Amount</label>
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
                                    <p className="text-xs text-muted-foreground font-mono">Amount: ${customAmount[0].toLocaleString()}</p>
                                </div>
                            </div>
                        </Card>
                    </Reveal>

                    {/* Checkout */}
                    <Reveal variant="fadeInUp" delay={0.4}>
                        <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                            <h2 className="text-xl font-bold mb-4 font-bebas tracking-wide">Proceed to Payment</h2>
                            <p className="text-sm text-muted-foreground mb-6 font-mono">
                                You'll be redirected to Stripe's secure checkout to complete the payment
                            </p>

                            <div className="p-6 bg-primary/5 rounded-lg border border-primary/20 mb-6">
                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-lg font-medium font-mono">Amount to Add:</span>
                                    <span className="text-3xl font-bold text-primary font-mono">
                                        ${(selectedAmount || customAmount[0]).toLocaleString()}.00
                                    </span>
                                </div>
                                {!loadingWallet && (
                                    <div className="flex items-center justify-between text-sm text-muted-foreground font-mono">
                                        <span>Estimated New Balance:</span>
                                        <span className="font-medium">
                                            ${(walletBalance + (selectedAmount || customAmount[0])).toLocaleString()}.00
                                        </span>
                                    </div>
                                )}
                            </div>

                            <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                <Button
                                    variant="hero"
                                    size="lg"
                                    className="w-full font-bebas tracking-wide text-lg"
                                    onClick={handleProcessPayment}
                                    disabled={processing || (selectedAmount || customAmount[0]) <= 0}
                                >
                                    {processing ? (
                                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                    ) : (
                                        <DollarSign className="w-5 h-5 mr-2" />
                                    )}
                                    {processing ? "Redirecting to Stripe..." : `Pay $${(selectedAmount || customAmount[0]).toLocaleString()}.00`}
                                </Button>
                            </motion.div>

                            <p className="text-xs text-center text-muted-foreground mt-4 font-mono">
                                Payments are processed securely by Stripe. Your wallet will be credited once payment is confirmed.
                            </p>
                        </Card>
                    </Reveal>
                </div>
            </main>
        </div>
    );
};

export default AddFunds;