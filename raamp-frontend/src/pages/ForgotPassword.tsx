import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Lock, Eye, EyeOff, Check, X, ShieldCheck } from "lucide-react";
import raampIcon from "@/assets/raamp-logo-v6-transparent.png";
import { toast } from "@/hooks/use-toast";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, zoomIn, scaleUp } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { getErrorMessage } from "@/utils/errorHandler";

type Step = "email" | "otp" | "password" | "done";

const ForgotPassword = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState<Step>("email");
    const [email, setEmail] = useState("");
    const [otp, setOtp] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [touched, setTouched] = useState({ password: false, confirmPassword: false });

    // Password validation
    const passwordChecks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };
    const allPasswordChecksPassed = Object.values(passwordChecks).every(Boolean);
    const passwordsMatch = password === confirmPassword && confirmPassword !== "";
    const isPasswordFormValid = allPasswordChecksPassed && passwordsMatch;

    const passwordStrength = () => {
        const count = Object.values(passwordChecks).filter(Boolean).length;
        if (count <= 2) return { level: "weak", color: "text-destructive" };
        if (count <= 4) return { level: "medium", color: "text-warning" };
        return { level: "strong", color: "text-success" };
    };

    // ─── Step 1: Send OTP ──────────────────────────────────────────────
    const handleSendOtp = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) {
            toast({ title: "Email Required", description: "Please enter your email address.", variant: "destructive" });
            return;
        }
        setIsLoading(true);
        try {
            const { apiClient } = await import("@/services/api");
            await apiClient.post<{ message: string }>("/auth/forgot-password", { email, method: "otp" });
            toast({ title: "OTP Sent", description: "Check your email for a 6-digit reset code." });
            setStep("otp");
        } catch (err: any) {
            toast({ title: "Error", description: getErrorMessage(err), variant: "destructive" });
        } finally {
            setIsLoading(false);
        }
    };

    // ─── Step 2: Verify OTP ────────────────────────────────────────────
    const handleVerifyOtp = (e: React.FormEvent) => {
        e.preventDefault();
        if (!otp || otp.length !== 6) {
            toast({ title: "Invalid OTP", description: "Please enter the 6-digit code.", variant: "destructive" });
            return;
        }
        // We don't hit the backend here — we verify OTP when submitting the new password
        setStep("password");
    };

    // ─── Step 3: Reset Password ────────────────────────────────────────
    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setTouched({ password: true, confirmPassword: true });
        if (!isPasswordFormValid) return;

        setIsLoading(true);
        try {
            const { apiClient } = await import("@/services/api");
            await apiClient.post<{ message: string }>("/auth/reset-password", {
                email,
                otp_code: otp,
                new_password: password,
                confirm_password: confirmPassword,
            });
            setStep("done");
            toast({ title: "Password Reset", description: "Your password has been reset successfully." });
        } catch (err: any) {
            toast({ title: "Error", description: getErrorMessage(err), variant: "destructive" });
        } finally {
            setIsLoading(false);
        }
    };

    // ─── Done Screen ───────────────────────────────────────────────────
    if (step === "done") {
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
                            <Reveal variant="scaleUp" delay={0.3}>
                                <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center mx-auto">
                                    <Check className="w-10 h-10 text-success" />
                                </div>
                            </Reveal>
                            <Reveal variant="fadeInUp" delay={0.4}>
                                <div className="space-y-2">
                                    <h1 className="text-3xl font-bold font-heading font-semibold">
                                        <BlurText text="Password Reset!" />
                                    </h1>
                                    <p className="text-muted-foreground font-mono text-sm">
                                        Your password has been updated. You can now sign in with your new password.
                                    </p>
                                </div>
                            </Reveal>
                            <Reveal variant="fadeInUp" delay={0.5}>
                                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                    <Button
                                        onClick={() => navigate("/login")}
                                        className="bg-gradient-to-r from-primary to-accent hover:opacity-90 w-full font-heading font-semibold text-lg"
                                    >
                                        Go to Login
                                    </Button>
                                </motion.div>
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

                        {/* Header */}
                        <div className="text-center space-y-4">
                            <div className="flex justify-center mb-4">
                                <Reveal variant="scaleUp" delay={0.2}>
                                    <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
                                </Reveal>
                            </div>
                            <Reveal variant="fadeIn" delay={0.3}>
                                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
                                    {step === "email" && <Lock className="w-8 h-8 text-primary" />}
                                    {step === "otp" && <ShieldCheck className="w-8 h-8 text-primary" />}
                                    {step === "password" && <Lock className="w-8 h-8 text-primary" />}
                                </div>
                            </Reveal>

                            {/* Step indicators */}
                            <Reveal variant="fadeIn" delay={0.35}>
                                <div className="flex items-center justify-center gap-2 mt-2">
                                    {(["email", "otp", "password"] as Step[]).map((s, i) => (
                                        <div key={s} className="flex items-center gap-2">
                                            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono transition-all
                                                ${step === s ? "bg-primary text-primary-foreground" :
                                                    (["email", "otp", "password"].indexOf(step) > i) ? "bg-success/20 text-success" : "bg-muted text-muted-foreground"}`}>
                                                {(["email", "otp", "password"].indexOf(step) > i) ? <Check className="w-3 h-3" /> : i + 1}
                                            </div>
                                            {i < 2 && <div className={`w-6 h-px ${(["email", "otp", "password"].indexOf(step) > i) ? "bg-success" : "bg-muted"}`} />}
                                        </div>
                                    ))}
                                </div>
                            </Reveal>

                            <Reveal variant="blurInUp" delay={0.4}>
                                <div className="space-y-1">
                                    <h1 className="text-3xl font-bold font-heading font-semibold">
                                        <BlurText text={
                                            step === "email" ? "Forgot Password?" :
                                                step === "otp" ? "Enter Your OTP" :
                                                    "Set New Password"
                                        } />
                                    </h1>
                                    <p className="text-muted-foreground font-mono text-sm">
                                        {step === "email" && "Enter your email and we'll send you a reset code."}
                                        {step === "otp" && `We sent a 6-digit code to ${email}`}
                                        {step === "password" && "Choose a strong new password for your account."}
                                    </p>
                                </div>
                            </Reveal>
                        </div>

                        {/* ── Step 1: Email ── */}
                        {step === "email" && (
                            <motion.form onSubmit={handleSendOtp} className="space-y-4" variants={staggerContainer} initial="hidden" animate="visible">
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
                                        <Button type="submit" disabled={isLoading}
                                            className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 font-heading font-semibold text-lg">
                                            {isLoading ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                    Sending OTP...
                                                </div>
                                            ) : "Send OTP"}
                                        </Button>
                                    </motion.div>
                                </motion.div>
                            </motion.form>
                        )}

                        {/* ── Step 2: OTP ── */}
                        {step === "otp" && (
                            <motion.form onSubmit={handleVerifyOtp} className="space-y-4" variants={staggerContainer} initial="hidden" animate="visible">
                                <motion.div variants={fadeInUp} className="space-y-2">
                                    <Label htmlFor="otp" className="font-mono text-xs">6-Digit Code</Label>
                                    <Input
                                        id="otp"
                                        type="text"
                                        inputMode="numeric"
                                        placeholder="123456"
                                        maxLength={6}
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                                        className="bg-background/50 font-mono tracking-widest text-center text-xl"
                                    />
                                </motion.div>
                                <motion.div variants={fadeInUp} className="flex gap-3">
                                    <Button type="button" variant="outline" onClick={() => setStep("email")}
                                        className="flex-1 font-mono text-xs">
                                        <ArrowLeft className="w-4 h-4 mr-1" /> Back
                                    </Button>
                                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="flex-1">
                                        <Button type="submit"
                                            className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 font-heading font-semibold text-lg">
                                            Verify Code
                                        </Button>
                                    </motion.div>
                                </motion.div>
                                <motion.div variants={fadeInUp} className="text-center">
                                    <button type="button" onClick={handleSendOtp}
                                        className="text-xs text-primary hover:underline font-mono">
                                        Didn't receive it? Resend OTP
                                    </button>
                                </motion.div>
                            </motion.form>
                        )}

                        {/* ── Step 3: New Password ── */}
                        {step === "password" && (
                            <motion.form onSubmit={handleResetPassword} className="space-y-4" variants={staggerContainer} initial="hidden" animate="visible">
                                {/* New Password */}
                                <motion.div variants={fadeInUp} className="space-y-2">
                                    <Label htmlFor="password" className="font-mono text-xs">New Password</Label>
                                    <div className="relative">
                                        <Input id="password" type={showPassword ? "text" : "password"}
                                            placeholder="••••••••" value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            onBlur={() => setTouched({ ...touched, password: true })}
                                            className="bg-background/50 pr-10 font-mono" />
                                        <button type="button" onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-3 text-muted-foreground hover:text-foreground">
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                    {password && (
                                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="space-y-2">
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                                                    <div className={`h-full transition-all duration-300 ${passwordStrength().level === "weak" ? "w-1/3 bg-destructive" :
                                                            passwordStrength().level === "medium" ? "w-2/3 bg-warning" : "w-full bg-success"}`} />
                                                </div>
                                                <span className={`text-xs font-mono ${passwordStrength().color}`}>{passwordStrength().level}</span>
                                            </div>
                                            <div className="space-y-1 text-xs font-mono">
                                                {Object.entries({
                                                    "8+ characters": passwordChecks.length,
                                                    Uppercase: passwordChecks.uppercase,
                                                    Lowercase: passwordChecks.lowercase,
                                                    Number: passwordChecks.number,
                                                    "Special character": passwordChecks.special,
                                                }).map(([label, ok]) => (
                                                    <div key={label} className={`flex items-center gap-2 ${ok ? "text-success" : "text-muted-foreground"}`}>
                                                        {ok ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                                                        <span>{label}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}
                                </motion.div>

                                {/* Confirm Password */}
                                <motion.div variants={fadeInUp} className="space-y-2">
                                    <Label htmlFor="confirmPassword" className="font-mono text-xs">Confirm Password</Label>
                                    <div className="relative">
                                        <Input id="confirmPassword" type={showConfirmPassword ? "text" : "password"}
                                            placeholder="••••••••" value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            onBlur={() => setTouched({ ...touched, confirmPassword: true })}
                                            className={`bg-background/50 pr-10 font-mono ${touched.confirmPassword ? passwordsMatch ? "border-success" : "border-destructive" : ""}`} />
                                        <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            className="absolute right-3 top-3 text-muted-foreground hover:text-foreground">
                                            {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                    {touched.confirmPassword && !passwordsMatch && confirmPassword && (
                                        <p className="text-sm text-destructive flex items-center gap-1 font-mono">
                                            <X className="w-3 h-3" /> Passwords do not match
                                        </p>
                                    )}
                                </motion.div>

                                <motion.div variants={fadeInUp} className="flex gap-3">
                                    <Button type="button" variant="outline" onClick={() => setStep("otp")}
                                        className="flex-1 font-mono text-xs">
                                        <ArrowLeft className="w-4 h-4 mr-1" /> Back
                                    </Button>
                                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="flex-1">
                                        <Button type="submit" disabled={!isPasswordFormValid || isLoading}
                                            className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 font-heading font-semibold text-lg">
                                            {isLoading ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                    Resetting...
                                                </div>
                                            ) : "Reset Password"}
                                        </Button>
                                    </motion.div>
                                </motion.div>
                            </motion.form>
                        )}

                        {/* Back to Login */}
                        <Reveal variant="fadeIn" delay={0.6}>
                            <div className="text-center">
                                <Link to="/login" className="text-sm text-primary hover:underline inline-flex items-center gap-1 font-mono">
                                    <ArrowLeft className="w-4 h-4" /> Back to Login
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