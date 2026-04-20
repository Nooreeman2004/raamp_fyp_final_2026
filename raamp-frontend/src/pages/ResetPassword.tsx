import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff, Check, X, Key } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, zoomIn, scaleUp, fadeIn } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

const ResetPassword = () => {
    const navigate = useNavigate();
    const { token } = useParams();
    const [searchParams] = useSearchParams();
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error, setError] = useState("");
    const [touched, setTouched] = useState({
        password: false,
        confirmPassword: false,
    });

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
    const isFormValid = allPasswordChecksPassed && passwordsMatch;

    const passwordStrength = () => {
        const checkedCount = Object.values(passwordChecks).filter(Boolean).length;
        if (checkedCount <= 2) return { level: "weak", color: "text-destructive" };
        if (checkedCount <= 4) return { level: "medium", color: "text-warning" };
        return { level: "strong", color: "text-success" };
    };

    // Password resets now use OTP (no reset links).
    // If a user lands here, redirect them to the OTP flow.
    useEffect(() => {
        const resetToken = token || searchParams.get('token');
        if (resetToken) {
            toast({
                title: "Reset links are no longer supported",
                description: "Please use the 6-digit code sent to your email to reset your password.",
                variant: "destructive",
            });
        }
        navigate("/forgot-password", { replace: true });
    }, [navigate, searchParams, token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        setTouched({
            password: true,
            confirmPassword: true,
        });

        if (!isFormValid) return;

        setIsLoading(true);

        try {
            const { apiClient } = await import('@/services/api');
            const resetToken = token || searchParams.get('token');

            if (!resetToken) {
                setError("Invalid reset link. Please request a new password reset.");
                setIsLoading(false);
                return;
            }

            // For link-based reset, we need email. In production, you might decode token or include email in URL
            // For now, we'll use a simplified approach - the backend can validate the token
            const response = await apiClient.post<{ message: string }>('/auth/reset-password', {
                email: '', // Backend will extract from token
                reset_token: resetToken,
                new_password: password,
                confirm_password: confirmPassword,
            });

            setIsSuccess(true);
            toast({
                title: "Password Reset Successful",
                description: response.message || "You can now login with your new password.",
            });

            setTimeout(() => {
                navigate("/login");
            }, 2000);
        } catch (err: any) {
            setError(err?.message || "Failed to reset password. Please try again.");
            toast({
                title: "Error",
                description: err?.message || "Failed to reset password. Please try again.",
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
                            <div className="flex justify-center">
                                <Reveal variant="scaleUp" delay={0.2}>
                                    <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center">
                                        <Check className="w-10 h-10 text-success animate-scale-in" />
                                    </div>
                                </Reveal>
                            </div>
                            <Reveal variant="fadeInUp" delay={0.3}>
                                <div className="space-y-2">
                                    <h1 className="text-3xl font-bold font-heading font-semibold">
                                        <BlurText text="Password Reset Successful" />
                                    </h1>
                                    <p className="text-muted-foreground font-mono text-sm">
                                        Your password has been reset successfully. You can now login with your new password.
                                    </p>
                                </div>
                            </Reveal>
                            <Reveal variant="fadeInUp" delay={0.4}>
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
                        <div className="text-center space-y-4">
                            <div className="flex justify-center mb-4">
                                <Reveal variant="scaleUp" delay={0.2}>
                                    <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
                                </Reveal>
                            </div>
                            <Reveal variant="fadeIn" delay={0.3}>
                                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
                                    <Key className="w-8 h-8 text-primary" />
                                </div>
                            </Reveal>
                            <Reveal variant="blurInUp" delay={0.4}>
                                <div className="space-y-2">
                                    <h1 className="text-3xl font-bold font-heading font-semibold">
                                        <BlurText text="Reset Your Password" />
                                    </h1>
                                    <p className="text-muted-foreground font-mono text-sm">
                                        Please enter your new password below
                                    </p>
                                </div>
                            </Reveal>
                        </div>

                        {error && (
                            <Reveal variant="fadeIn">
                                <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                                    <p className="text-sm text-destructive flex items-center gap-2 font-mono">
                                        <X className="w-4 h-4" />
                                        {error}
                                    </p>
                                </div>
                            </Reveal>
                        )}

                        <motion.form
                            onSubmit={handleSubmit}
                            className="space-y-4"
                            variants={staggerContainer}
                            initial="hidden"
                            animate="visible"
                        >
                            {/* New Password Field */}
                            <motion.div variants={fadeInUp} className="space-y-2">
                                <Label htmlFor="password" className="font-mono text-xs">New Password</Label>
                                <div className="relative">
                                    <Input
                                        id="password"
                                        type={showPassword ? "text" : "password"}
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        onBlur={() => setTouched({ ...touched, password: true })}
                                        className="bg-background/50 pr-10 font-mono"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                                    >
                                        {showPassword ? (
                                            <EyeOff className="w-4 h-4" />
                                        ) : (
                                            <Eye className="w-4 h-4" />
                                        )}
                                    </button>
                                </div>

                                {/* Password Strength Meter */}
                                {password && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        className="space-y-2"
                                    >
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full transition-all duration-300 ${passwordStrength().level === "weak"
                                                        ? "w-1/3 bg-destructive"
                                                        : passwordStrength().level === "medium"
                                                            ? "w-2/3 bg-warning"
                                                            : "w-full bg-success"
                                                        }`}
                                                />
                                            </div>
                                            <span className={`text-xs font-medium ${passwordStrength().color} font-mono`}>
                                                {passwordStrength().level}
                                            </span>
                                        </div>

                                        {/* Password Requirements Checklist */}
                                        <div className="space-y-1 text-xs font-mono">
                                            {Object.entries({
                                                "8+ characters": passwordChecks.length,
                                                Uppercase: passwordChecks.uppercase,
                                                Lowercase: passwordChecks.lowercase,
                                                Number: passwordChecks.number,
                                                "Special character": passwordChecks.special,
                                            }).map(([label, checked]) => (
                                                <div
                                                    key={label}
                                                    className={`flex items-center gap-2 ${checked ? "text-success" : "text-muted-foreground"
                                                        }`}
                                                >
                                                    {checked ? (
                                                        <Check className="w-3 h-3" />
                                                    ) : (
                                                        <X className="w-3 h-3" />
                                                    )}
                                                    <span>{label}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </motion.div>

                            {/* Confirm Password Field */}
                            <motion.div variants={fadeInUp} className="space-y-2">
                                <Label htmlFor="confirmPassword" className="font-mono text-xs">Confirm Password</Label>
                                <div className="relative">
                                    <Input
                                        id="confirmPassword"
                                        type={showConfirmPassword ? "text" : "password"}
                                        placeholder="••••••••"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        onBlur={() =>
                                            setTouched({ ...touched, confirmPassword: true })
                                        }
                                        className={`bg-background/50 pr-10 font-mono ${touched.confirmPassword
                                            ? passwordsMatch
                                                ? "border-success"
                                                : "border-destructive"
                                            : ""
                                            }`}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                                    >
                                        {showConfirmPassword ? (
                                            <EyeOff className="w-4 h-4" />
                                        ) : (
                                            <Eye className="w-4 h-4" />
                                        )}
                                    </button>
                                </div>
                                {touched.confirmPassword && !passwordsMatch && confirmPassword && (
                                    <p className="text-sm text-destructive flex items-center gap-1 font-mono">
                                        <X className="w-3 h-3" />
                                        Passwords do not match
                                    </p>
                                )}
                            </motion.div>

                            <motion.div variants={fadeInUp}>
                                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                    <Button
                                        type="submit"
                                        className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity font-heading font-semibold text-lg"
                                        disabled={!isFormValid || isLoading}
                                    >
                                        {isLoading ? (
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                Resetting Password...
                                            </div>
                                        ) : (
                                            "Reset Password"
                                        )}
                                    </Button>
                                </motion.div>
                            </motion.div>
                        </motion.form>
                    </div>
                </Card>
            </Reveal>
        </div>
    );
};

export default ResetPassword;