import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Lock, Eye, EyeOff, Loader2 } from "lucide-react";
import { apiClient } from "@/services/api";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface PasswordVerificationDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onVerified: () => void;
    title?: string;
    description?: string;
}

export const PasswordVerificationDialog = ({
    isOpen,
    onClose,
    onVerified,
    title = "Verify Your Identity",
    description = "Please enter your password to authorize these changes.",
}: PasswordVerificationDialogProps) => {
    const { user } = useAuth();
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isVerifying, setIsVerifying] = useState(false);
    const [error, setError] = useState("");

    const handleVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!password) return;

        setError("");
        setIsVerifying(true);

        try {
            // Use sign-in endpoint to verify password
            await apiClient.post("/auth/signin", {
                email: user?.email,
                password: password,
            });

            toast.success("Identity verified successfully");
            setPassword("");
            onVerified();
        } catch (err: any) {
            setError(err?.message || "Incorrect password. Please try again.");
            toast.error("Verification failed");
        } finally {
            setIsVerifying(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="bg-background/90 border-primary/30 text-foreground backdrop-blur-xl sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="font-heading font-semibold text-2xl text-primary flex items-center gap-2">
                        <Lock className="w-5 h-5" />
                        {title}
                    </DialogTitle>
                    <DialogDescription className="font-mono text-xs text-muted-foreground">
                        {description.toUpperCase()}
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleVerify} className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="gate-password" className="text-xs font-mono text-primary">PASSWORD</Label>
                        <div className="relative">
                            <Input
                                id="gate-password"
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => {
                                    setPassword(e.target.value);
                                    setError("");
                                }}
                                className={cn(
                                    "bg-black/50 border-border/50 font-mono focus:border-primary/50 focus:ring-primary/20 pr-10",
                                    error && "border-destructive focus:border-destructive"
                                )}
                                placeholder="••••••••"
                                autoFocus
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-3 text-white/30 hover:text-primary transition-colors"
                                aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                        {error && (
                            <p className="text-destructive text-[10px] font-mono uppercase animate-in fade-in slide-in-from-top-1">
                                {error}
                            </p>
                        )}
                    </div>

                    <DialogFooter className="pt-2">
                        <Button
                            type="button"
                            variant="ghost"
                            onClick={onClose}
                            className="font-mono text-xs text-muted-foreground/80 hover:text-foreground"
                            disabled={isVerifying}
                        >
                            CANCEL
                        </Button>
                        <Button
                            type="submit"
                            className="bg-primary text-primary-foreground hover:bg-primary/90 font-heading font-semibold min-w-[120px]"
                            disabled={!password || isVerifying}
                        >
                            {isVerifying ? (
                                <div className="flex items-center gap-2">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    VERIFYING...
                                </div>
                            ) : (
                                "VERIFY IDENTITY"
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};
