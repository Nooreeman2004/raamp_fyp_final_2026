import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Lock, Check } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, zoomIn, scaleUp, fadeIn } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

const ForgotPassword = () => {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!email) {
            toast({
                title: "Email Required",
                description: "Please enter your email address.",
                variant: "destructive",
            });
            return;
        }

        setIsLoading(true);

        try {
            const { apiClient } = await import('@/services/api');
            const response = await apiClient.post<{ message: string }>('/auth/forgot-password', {
                email: email,
                method: 'link', // or 'otp' for OTP-based reset
            });

            setIsSuccess(true);
            toast({
                title: "Reset Link Sent",
                description: response.message || "Check your email for password reset instructions.",
            });
        } catch (err: any) {
            toast({
                title: "Error",
                description: err?.message || "Failed to send reset link. Please try again.",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    if (isSuccess) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4">
                <Reveal variant="zoomIn" duration={0.5} className="w-full max-w-md">
                    <Card className="w-full p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
                        <div className="text-center space-y-6">
                            <div className="flex justify-center mb-4">
                                <Reveal variant="scaleUp" delay={0.2}>
                                    <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
                                </Reveal>
                            </div>
                            <div className="flex justify-center">
                                <Reveal variant="scaleUp" delay={0.3}>
                                    <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center">
                                        <Check className="w-10 h-10 text-success" />
                                    </div>
                                </Reveal>
                            </div>
                            <Reveal variant="fadeInUp" delay={0.4}>
                                <div className="space-y-2">
                                    <h1 className="text-3xl font-bold font-bebas tracking-wide">
                                        <BlurText text="Check Your Email" />
                                    </h1>
                                    <p className="text-muted-foreground font-mono text-sm">
                                        We've sent password reset instructions to
                                    </p>
                                    <p className="text-foreground font-medium font-mono">{email}</p>
                                    <p className="text-sm text-muted-foreground mt-4 font-mono">
                                        If you don't see the email, check your spam folder.
                                    </p>
                                </div>
                            </Reveal>
                            <Reveal variant="fadeInUp" delay={0.5}>
                                <Link to="/login">
                                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                        <Button className="bg-gradient-to-r from-primary to-accent hover:opacity-90 w-full font-bebas tracking-wide text-lg">
                                            Back to Login
                                        </Button>
                                    </motion.div>
                                </Link>
                            </Reveal>
                        </div>
                    </Card>
                </Reveal>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4 overflow-hidden">
            <Reveal variant="zoomIn" duration={0.5} className="w-full max-w-md">
                <Card className="w-full p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
                    <div className="space-y-6">
                        <div className="text-center space-y-4">
                            <div className="flex justify-center mb-4">
                                <Reveal variant="scaleUp" delay={0.2}>
                                    <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
                                </Reveal>
                            </div>
                            <Reveal variant="fadeIn" delay={0.3}>
                                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
                                    <Lock className="w-8 h-8 text-primary" />
                                </div>
                            </Reveal>
                            <Reveal variant="blurInUp" delay={0.4}>
                                <div className="space-y-2">
                                    <h1 className="text-3xl font-bold font-bebas tracking-wide">
                                        <BlurText text="Forgot Your Password?" />
                                    </h1>
                                    <p className="text-muted-foreground font-mono text-sm">
                                        Enter the email address associated with your account, and we'll send you a secure link to reset your password.
                                    </p>
                                </div>
                            </Reveal>
                        </div>

                        <motion.form
                            onSubmit={handleSubmit}
                            className="space-y-4"
                            variants={staggerContainer}
                            initial="hidden"
                            animate="visible"
                        >
                            <motion.div variants={fadeInUp} className="space-y-2">
                                <Label htmlFor="email" className="font-mono text-xs">Email Address</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="you@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="bg-background/50 font-mono"
                                />
                            </motion.div>

                            <motion.div variants={fadeInUp}>
                                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                    <Button
                                        type="submit"
                                        className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity font-bebas tracking-wide text-lg"
                                        disabled={isLoading}
                                    >
                                        {isLoading ? (
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                Sending...
                                            </div>
                                        ) : (
                                            "Send Reset Link"
                                        )}
                                    </Button>
                                </motion.div>
                            </motion.div>
                        </motion.form>

                        <Reveal variant="fadeIn" delay={0.6}>
                            <div className="text-center">
                                <Link
                                    to="/login"
                                    className="text-sm text-primary hover:underline inline-flex items-center gap-1 font-mono"
                                >
                                    <ArrowLeft className="w-4 h-4" />
                                    Back to Login
                                </Link>
                            </div>
                        </Reveal>
                    </div>
                </Card>
            </Reveal>
        </div>
    );
};

export default ForgotPassword;