import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";
import { signInWithGoogle } from "@/services/googleAuth";

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      const googleResult = await signInWithGoogle();
      const response = await authService.signinWithGoogle({
        id_token: googleResult.idToken,
        email: googleResult.email,
        display_name: googleResult.displayName,
        photo_url: googleResult.photoURL,
      });

      toast({
        title: "Welcome!",
        description: response.message || "Signed in with Google.",
      });

      if (response.user && !response.user.profile_completed) {
        navigate("/profile/personal-details");
      } else {
        navigate("/dashboard");
      }
    } catch (error: unknown) {
      console.error("Google sign-in error:", error);
      const apiError = error as { message?: string; detail?: string };
      const description =
        apiError?.message ||
        apiError?.detail ||
        "Unable to sign in with Google. Please try again or use email/password.";
      toast({
        title: "Google Sign-in Failed",
        description,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast({
        title: "Missing Information",
        description: "Please enter both email and password.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await authService.signin({
        email,
        password,
      });

      toast({
        title: "Welcome back!",
        description: response.message || "You've successfully signed in.",
      });
      
      // Check if profile is completed
      if (response.user && !response.user.profile_completed) {
        // New user - redirect to profile setup
        navigate("/profile/personal-details");
      } else {
        // Existing user with completed profile - redirect to dashboard
        navigate("/dashboard");
      }
    } catch (error: unknown) {
      console.error("Sign in error:", error);
      const apiError = error as { errors?: Record<string, string | string[]>; message?: string };
      
      // Handle different error scenarios
      if (apiError.errors) {
          // Special case: Email not verified
          if (apiError.errors.email && typeof apiError.errors.email === 'string' && 
              apiError.errors.email.toLowerCase().includes("verify")) {
            // Before navigating to verify, double-check verification status to avoid duplicate emails
            try {
              const status = await authService.getVerificationStatus(email);
              if (status && status.is_verified) {
                toast({
                  title: "Already Verified",
                  description: "This email appears to be already verified. Try signing in or contact support.",
                  variant: "default",
                });
                return;
              }
            } catch (err) {
              // If the check fails, fall back to original behavior
              console.warn('Verification status check failed:', err);
            }

            toast({
              title: "Email Not Verified",
              description: "Please check your email and enter the verification code.",
              variant: "destructive",
            });
            // Redirect to verification page
            setTimeout(() => {
              navigate("/verify-email", { state: { email } });
            }, 2000);
            return;
          }
        
        // Backend validation errors
        const errorMessages = Object.values(apiError.errors).flat().join(", ");
        toast({
          title: "Sign In Failed",
          description: errorMessages,
          variant: "destructive",
        });
      } else {
        // Generic error
        toast({
          title: "Sign In Failed",
          description: apiError.message || "Unable to sign in. Please check your credentials.",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4">
      <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
        <div className="space-y-6">
          <div className="text-center space-y-2">
            <div className="flex justify-center mb-4">
              <img src={raampIcon} alt="RAAMP" className="h-24 w-24" />
            </div>
            <h1 className="text-3xl font-bold">Login to RAAMP</h1>
            <p className="text-muted-foreground">
              Autonomous marketing, powered by AI.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-background/50"
                autoComplete="email"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-primary hover:underline"
                >
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-background/50 pr-10"
                  autoComplete="current-password"
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
            </div>

            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                  Signing In...
                </div>
              ) : (
                "Sign In"
              )}
            </Button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or</span>
              </div>
            </div>

            {/* Google OAuth */}
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleGoogleLogin}
              disabled={isLoading}
            >
              <svg
                className="w-5 h-5 mr-2"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google
            </Button>
          </form>

          <div className="text-center text-sm text-muted-foreground space-y-2">
            <div>
              Don't have an account?{" "}
              <Link to="/signup" className="text-primary hover:underline font-medium">
                Sign Up
              </Link>
            </div>
            <div>
              Need to verify your email?{" "}
              <button
                type="button"
                onClick={async () => {
                  // If the user has entered an email in the form, check verification status first
                  if (email) {
                    try {
                      const status = await authService.getVerificationStatus(email);
                      if (status && status.is_verified) {
                        toast({
                          title: "Already Verified",
                          description: "This email is already verified. Please sign in instead.",
                        });
                        return;
                      }
                      
                      // Not verified -> send OTP first
                      toast({
                        title: "Sending verification code...",
                        description: "Please wait while we send the code to your email.",
                      });
                      
                      try {
                        await authService.resendVerification({ email });
                        toast({
                          title: "Verification Code Sent",
                          description: `A verification code has been sent to ${email}`,
                        });
                        // Navigate to verification page with email prefilled
                        navigate('/verify-email', { state: { email } });
                      } catch (resendErr: unknown) {
                        console.error('Failed to send verification code', resendErr);
                        
                        // Parse error to show helpful message
                        let errorMessage = "Failed to send verification code. Please try again.";
                        
                        if (resendErr && typeof resendErr === 'object') {
                          if ('response' in resendErr) {
                            const response = (resendErr as { response?: { data?: { errors?: Record<string, string> } } }).response;
                            const errors = response?.data?.errors;
                            
                            if (errors?.email?.includes('No pending verification found')) {
                              errorMessage = "No pending verification found. Please sign up first or sign in if you're already registered.";
                            } else if (errors?.email?.includes('already verified')) {
                              errorMessage = "This email is already verified. Please sign in instead.";
                            } else if (errors?.cooldown) {
                              errorMessage = errors.cooldown;
                            } else if ('message' in resendErr) {
                              errorMessage = String(resendErr.message);
                            }
                          } else if ('message' in resendErr) {
                            errorMessage = String(resendErr.message);
                          }
                        }
                        
                        toast({
                          title: "Cannot Send Verification Code",
                          description: errorMessage,
                          variant: "destructive",
                        });
                      }
                    } catch (err) {
                      console.error('Failed to check verification status', err);
                      // Fallback: try to send OTP anyway
                      try {
                        await authService.resendVerification({ email });
                        toast({
                          title: "Verification Code Sent",
                          description: `A verification code has been sent to ${email}`,
                        });
                        navigate('/verify-email', { state: { email } });
                      } catch (resendErr: unknown) {
                        let errorMessage = "Failed to send verification code.";
                        
                        if (resendErr && typeof resendErr === 'object') {
                          if ('response' in resendErr) {
                            const response = (resendErr as { response?: { data?: { errors?: Record<string, string> } } }).response;
                            const errors = response?.data?.errors;
                            
                            if (errors?.email?.includes('No pending verification found')) {
                              errorMessage = "No pending verification found. Please sign up first or sign in if you're already registered.";
                            } else if (errors?.email?.includes('already verified')) {
                              errorMessage = "This email is already verified. Please sign in instead.";
                            }
                          } else if ('message' in resendErr) {
                            errorMessage = String(resendErr.message);
                          }
                        }
                        
                        toast({
                          title: "Cannot Send Verification Code",
                          description: errorMessage,
                          variant: "destructive",
                        });
                      }
                    }
                  } else {
                    // No email typed — show error
                    toast({
                      title: "Email Required",
                      description: "Please enter your email address first.",
                      variant: "destructive",
                    });
                  }
                }}
                className="text-primary hover:underline font-medium"
              >
                Verify Email
              </button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Login;
