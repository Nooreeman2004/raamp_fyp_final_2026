import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Mail, Check } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";

const EmailVerification = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || "";
  
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [resendTimer, setResendTimer] = useState(60);
  const [codeExpiry, setCodeExpiry] = useState(86400); // 24 hours in seconds
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Countdown for resend button
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  useEffect(() => {
    // Countdown for code expiry
    if (codeExpiry > 0) {
      const timer = setTimeout(() => setCodeExpiry(codeExpiry - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [codeExpiry]);

  const handleChange = (index: number, value: string) => {
    // Only allow numbers
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    // Auto-advance to next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all fields are filled
    if (newCode.every((digit) => digit !== "") && !isLoading) {
      handleVerify(newCode.join(""));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").slice(0, 6);
    
    if (!/^\d+$/.test(pastedData)) return;

    const newCode = [...code];
    for (let i = 0; i < pastedData.length; i++) {
      newCode[i] = pastedData[i];
    }
    setCode(newCode);

    // Focus the next empty input or last input
    const nextIndex = Math.min(pastedData.length, 5);
    inputRefs.current[nextIndex]?.focus();

    // Auto-submit if complete
    if (pastedData.length === 6) {
      handleVerify(pastedData);
    }
  };

  const handleVerify = async (verificationCode: string) => {
    if (!email) {
      toast({
        title: "Error",
        description: "Email address is missing. Please sign up again.",
        variant: "destructive",
      });
      navigate("/signup");
      return;
    }

    if (codeExpiry <= 0) {
      toast({
        title: "Code Expired",
        description: "Please request a new verification code.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await authService.verifyEmail({
        email,
        code: verificationCode,
      });

      setIsSuccess(true);
      toast({
        title: "Email Verified!",
        description: response.message || "Your account has been successfully created.",
      });

      // Redirect to login page after verification
      setTimeout(() => {
        navigate("/login", { state: { email, verified: true } });
      }, 1500);
    } catch (error: any) {
      console.error("Verification error:", error);
      
      // Special case: User already exists (verification already completed)
      if (error.errors?.email && typeof error.errors.email === 'string' && 
          error.errors.email.includes("already exists")) {
        toast({
          title: "Already Verified!",
          description: "Your account is ready. Please sign in.",
        });
        setTimeout(() => {
          navigate("/login");
        }, 1500);
        return;
      }
      
      toast({
        title: "Verification Failed",
        description: error.errors?.code || error.message || "Invalid or expired code.",
        variant: "destructive",
      });
      
      // Clear the code inputs on error
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      toast({
        title: "Error",
        description: "Email address is missing.",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await authService.resendVerification({ email });
      
      toast({
        title: "Verification Code Sent",
        description: response.message || "A new verification code has been sent to your email.",
      });
      
      setResendTimer(60);
      setCodeExpiry(86400); // Reset to 24 hours
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } catch (error: any) {
      console.error("Resend error:", error);
      
      toast({
        title: "Resend Failed",
        description: error.errors?.cooldown || error.message || "Failed to resend code.",
        variant: "destructive",
      });
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${mins}m ${secs}s`;
    } else if (mins > 0) {
      return `${mins}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4">
        <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center">
                <Check className="w-10 h-10 text-success" />
              </div>
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Email Verified!</h1>
              <p className="text-muted-foreground">
                Your account has been successfully verified. Redirecting...
              </p>
            </div>
            <div className="w-16 h-1 bg-primary mx-auto rounded-full animate-pulse" />
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
              <Mail className="w-8 h-8 text-primary" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Verify Your Email</h1>
              <p className="text-muted-foreground">
                We've sent a 6-digit verification code to
              </p>
              <p className="text-foreground font-medium">{email}</p>
            </div>
          </div>

          {/* OTP Input */}
          <div className="space-y-4">
            <div className="flex gap-2 justify-center" onPaste={handlePaste}>
              {code.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => (inputRefs.current[index] = el)}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className={`w-12 h-12 text-center text-lg font-bold rounded-md border-2 bg-background/50 transition-all
                    ${digit ? "border-primary" : "border-input"}
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    disabled:opacity-50 disabled:cursor-not-allowed`}
                  disabled={isLoading || codeExpiry <= 0}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            {/* Code Expiry Timer */}
            <div className="text-center text-sm">
              {codeExpiry > 0 ? (
                <p className="text-muted-foreground">
                  Code expires in:{" "}
                  <span className="font-medium text-foreground">
                    {formatTime(codeExpiry)}
                  </span>
                </p>
              ) : (
                <p className="text-destructive font-medium">
                  Verification code has expired
                </p>
              )}
            </div>
          </div>

          {/* Verify Button (shown when all digits entered) */}
          {code.every((digit) => digit !== "") && (
            <Button
              onClick={() => handleVerify(code.join(""))}
              className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
              disabled={isLoading || codeExpiry <= 0}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                  Verifying...
                </div>
              ) : (
                "Verify Email"
              )}
            </Button>
          )}

          {/* Resend Code */}
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-2">
              Didn't receive the code?
            </p>
            {resendTimer > 0 ? (
              <p className="text-sm text-muted-foreground">
                Resend available in{" "}
                <span className="font-medium text-foreground">{resendTimer}s</span>
              </p>
            ) : (
              <Button
                variant="outline"
                onClick={handleResend}
                className="text-primary hover:text-primary"
              >
                Resend Code
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default EmailVerification;
