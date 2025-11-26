import { useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff, Check, X, Key } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";

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
      const response = await apiClient.post('/auth/reset-password', {
        email: '', // Backend will extract from token
        reset_token: resetToken,
        new_password: password,
        confirm_password: confirmPassword,
      });

      setIsSuccess(true);
      toast({
        title: "Password Reset Successful",
        description: response.message || "You can now sign in with your new password.",
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
        <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center">
                <Check className="w-10 h-10 text-success animate-scale-in" />
              </div>
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Password Reset Successful</h1>
              <p className="text-muted-foreground">
                Your password has been reset successfully. You can now sign in with your new password.
              </p>
            </div>
            <Button
              onClick={() => navigate("/login")}
              className="bg-gradient-to-r from-primary to-accent hover:opacity-90"
            >
              Go to Sign In
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4">
      <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
        <div className="space-y-6">
          <div className="text-center space-y-4">
            <div className="flex justify-center mb-4">
              <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
            </div>
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
              <Key className="w-8 h-8 text-primary" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Reset Your Password</h1>
              <p className="text-muted-foreground">
                Please enter your new password below
              </p>
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive flex items-center gap-2">
                <X className="w-4 h-4" />
                {error}
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* New Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password">New Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => setTouched({ ...touched, password: true })}
                  className="bg-background/50 pr-10"
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
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          passwordStrength().level === "weak"
                            ? "w-1/3 bg-destructive"
                            : passwordStrength().level === "medium"
                            ? "w-2/3 bg-warning"
                            : "w-full bg-success"
                        }`}
                      />
                    </div>
                    <span className={`text-xs font-medium ${passwordStrength().color}`}>
                      {passwordStrength().level}
                    </span>
                  </div>

                  {/* Password Requirements Checklist */}
                  <div className="space-y-1 text-xs">
                    {Object.entries({
                      "8+ characters": passwordChecks.length,
                      Uppercase: passwordChecks.uppercase,
                      Lowercase: passwordChecks.lowercase,
                      Number: passwordChecks.number,
                      "Special character": passwordChecks.special,
                    }).map(([label, checked]) => (
                      <div
                        key={label}
                        className={`flex items-center gap-2 ${
                          checked ? "text-success" : "text-muted-foreground"
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
                </div>
              )}
            </div>

            {/* Confirm Password Field */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
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
                  className={`bg-background/50 pr-10 ${
                    touched.confirmPassword
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
                <p className="text-sm text-destructive flex items-center gap-1">
                  <X className="w-3 h-3" />
                  Passwords do not match
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
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
          </form>
        </div>
      </Card>
    </div>
  );
};

export default ResetPassword;
