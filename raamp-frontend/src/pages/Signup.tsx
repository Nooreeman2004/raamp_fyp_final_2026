import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Check, X, HelpCircle } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { authService, type ErrorResponse } from "@/services/authService";
import { signInWithGoogle } from "@/services/googleAuth";

const Signup = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [touched, setTouched] = useState({
    username: false,
    email: false,
    password: false,
    terms: false,
  });

  // Username validation
  const validateUsername = (value: string) => {
    if (!value) return { valid: false, message: "" };
    if (value.length < 7 || value.length > 20)
      return { valid: false, message: "Must be 7-20 characters" };
    if (!/^[a-z0-9]+$/.test(value))
      return { valid: false, message: "Lowercase letters and numbers only" };
    return { valid: true, message: "" };
  };

  // Email validation
  const validateEmail = (value: string) => {
    if (!value) return { valid: false, message: "" };
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value))
      return { valid: false, message: "Invalid email format" };
    return { valid: true, message: "" };
  };

  // Password validation
  const passwordChecks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  const passwordStrength = () => {
    const checkedCount = Object.values(passwordChecks).filter(Boolean).length;
    if (checkedCount <= 2) return { level: "weak", color: "text-destructive" };
    if (checkedCount <= 4)
      return { level: "medium", color: "text-warning" };
    return { level: "strong", color: "text-success" };
  };

  const usernameValidation = validateUsername(username);
  const emailValidation = validateEmail(email);
  const allPasswordChecksPassed = Object.values(passwordChecks).every(Boolean);
  const isFormValid =
    usernameValidation.valid &&
    emailValidation.valid &&
    allPasswordChecksPassed &&
    termsAccepted;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setTouched({
      username: true,
      email: true,
      password: true,
      terms: true,
    });

    if (!isFormValid) return;

    setIsLoading(true);

    try {
      // Call backend API
      const response = await authService.signup({
        username,
        email,
        password,
        agreed_to_terms: termsAccepted,
      });

      // Success
      toast({
        title: "Account created!",
        description: response.message || "Please verify your email to continue.",
      });
      
      // Navigate to email verification
      navigate("/verify-email", { state: { email } });
      
    } catch (error: unknown) {
      // Handle API errors
      console.error("Signup error:", error);
      const apiError = error as { errors?: Record<string, string | string[]>; message?: string };
      
      if (apiError.errors) {
        // Backend validation errors
        
        // Special handling for "verification already in progress" error
        if (apiError.errors.email && typeof apiError.errors.email === 'string' && 
            error.errors.email.includes("verification")) {
          toast({
            title: "Verification in progress",
            description: "Please check your email for the verification code or wait to resend.",
          });
          // Navigate to verification page
          navigate("/verify-email", { state: { email } });
          return;
        }
        
        const errorMessages = Object.entries(apiError.errors)
          .map(([field, msg]) => {
            const messages = Array.isArray(msg) ? msg.join(", ") : msg;
            return `${field}: ${messages}`;
          })
          .join("\n");
        
        toast({
          title: "Signup failed",
          description: errorMessages,
          variant: "destructive",
        });
      } else {
        // Network or other errors
        toast({
          title: "Error",
          description: apiError.message || "Failed to create account. Please try again.",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setIsLoading(true);
    
    try {
      // Sign in with Google (Firebase popup)
      const googleResult = await signInWithGoogle();
      
      // Send Google credentials to backend
      const response = await authService.signupWithGoogle({
        id_token: googleResult.idToken,
        email: googleResult.email,
        display_name: googleResult.displayName,
        photo_url: googleResult.photoURL,
      });
      
      // Success - Google account created, now require onboarding/profile
      toast({
        title: "Account created!",
        description: response.message || "Welcome to RAAMP! Let’s complete your profile.",
      });
      
      // Newly created Google users must complete profile before using the app
      navigate("/profile/personal-details");
      
    } catch (error: unknown) {
      console.error("Google signup error:", error);
      const apiError = error as { errors?: Record<string, string | string[]>; message?: string; detail?: string };
      
      if (apiError.errors) {
        // Backend validation errors
        const errorMessages = Object.entries(apiError.errors)
          .map(([field, msg]) => {
            const messages = Array.isArray(msg) ? msg.join(", ") : msg;
            return `${field}: ${messages}`;
          })
          .join("\n");
        
        toast({
          title: "Signup failed",
          description: errorMessages,
          variant: "destructive",
        });
      } else {
        // Network or other errors
        toast({
          title: "Google Sign-in Failed",
          description: apiError.message || apiError.detail || "Failed to sign in with Google. Please try again.",
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
              <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
            </div>
            <h1 className="text-3xl font-bold">Create Account</h1>
            <p className="text-muted-foreground">
              Join RAAMP and start your autonomous marketing journey
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
            {/* Username Field */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="username">Username</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-4 h-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>7-20 characters, lowercase and numbers only</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <div className="relative">
                <Input
                  id="username"
                  name="username"
                  type="text"
                  placeholder="johndoe123"
                  value={username}
                  onChange={(e) =>
                    setUsername(e.target.value.toLowerCase())
                  }
                  onBlur={() => setTouched({ ...touched, username: true })}
                  className={`bg-background/50 pr-10 ${
                    touched.username
                      ? usernameValidation.valid
                        ? "border-success"
                        : "border-destructive"
                      : ""
                  }`}
                  autoComplete="off"
                />
                {touched.username && usernameValidation.valid && (
                  <Check className="absolute right-3 top-3 w-4 h-4 text-success" />
                )}
              </div>
              {touched.username && !usernameValidation.valid && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <X className="w-3 h-3" />
                  {usernameValidation.message}
                </p>
              )}
            </div>

            {/* Email Field */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="email">Email Address</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-4 h-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>We'll send verification here</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <div className="relative">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => setTouched({ ...touched, email: true })}
                  className={`bg-background/50 pr-10 ${
                    touched.email
                      ? emailValidation.valid
                        ? "border-success"
                        : "border-destructive"
                      : ""
                  }`}
                  autoComplete="email"
                />
                {touched.email && emailValidation.valid && (
                  <Check className="absolute right-3 top-3 w-4 h-4 text-success" />
                )}
              </div>
              {touched.email && !emailValidation.valid && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <X className="w-3 h-3" />
                  {emailValidation.message}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="password">Password</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-4 h-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent className="w-64">
                      <div className="space-y-1">
                        <p className="font-semibold">Password must contain:</p>
                        <ul className="text-xs space-y-1">
                          <li>• At least 8 characters</li>
                          <li>• One uppercase letter</li>
                          <li>• One lowercase letter</li>
                          <li>• One number</li>
                          <li>• One special character</li>
                        </ul>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  name="new-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => setTouched({ ...touched, password: true })}
                  className="bg-background/50 pr-10"
                  autoComplete="new-password"
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
                    <span
                      className={`text-xs font-medium ${
                        passwordStrength().color
                      }`}
                    >
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

            {/* Terms & Conditions */}
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <Checkbox
                  id="terms"
                  checked={termsAccepted}
                  onCheckedChange={(checked) =>
                    setTermsAccepted(checked as boolean)
                  }
                  className="mt-1"
                />
                <label
                  htmlFor="terms"
                  className="text-sm text-muted-foreground leading-tight cursor-pointer"
                >
                  I agree to the{" "}
                  <Link
                    to="/terms"
                    className="text-primary hover:underline"
                  >
                    Terms & Conditions
                  </Link>{" "}
                  and{" "}
                  <Link
                    to="/privacy"
                    className="text-primary hover:underline"
                  >
                    Privacy Policy
                  </Link>
                </label>
              </div>
              {touched.terms && !termsAccepted && (
                <p className="text-sm text-destructive flex items-center gap-1">
                  <X className="w-3 h-3" />
                  You must accept the terms and conditions
                </p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
              disabled={!isFormValid || isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                  Creating Account...
                </div>
              ) : (
                "Create Account"
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
              onClick={handleGoogleSignup}
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

          {/* Sign In Link */}
          <div className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Sign In
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Signup;
