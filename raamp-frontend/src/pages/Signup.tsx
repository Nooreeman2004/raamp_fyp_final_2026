import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";
import { signInWithGoogle } from "@/services/googleAuth";
import { motion } from "framer-motion";
import { BlurText } from "@/components/ui/text-reveal";
import raampIcon from "@/assets/raamp-logo-v6-transparent.png";
import { Lock, Mail, ArrowRight, Eye, EyeOff, User, Check, X, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { BackgroundBeams } from "@/components/ui/background-beams";
import { Ultra3DCard } from "@/components/ui/ultra-3d-card";
import { LiquidLogo } from "@/components/ui/liquid-logo";

const PasswordRequirementItem = ({ label, isMet, showError }: { label: string, isMet: boolean, showError: boolean }) => (
  <motion.div
    initial={{ opacity: 0, x: -5 }}
    animate={{ opacity: 1, x: 0 }}
    className="flex items-center gap-2"
  >
    <div className={cn(
      "w-3.5 h-3.5 rounded-full border flex items-center justify-center transition-all duration-300",
      isMet
        ? "bg-emerald-500/20 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]"
        : (showError ? "bg-red-500/10 border-red-500/50" : "bg-foreground/5 border-border/50")
    )}>
      {isMet && <Check className="w-2.5 h-2.5 text-emerald-500" strokeWidth={3} />}
    </div>
    <span className={cn(
      "text-[10px] font-mono transition-colors duration-300",
      isMet ? "text-emerald-500" : (showError ? "text-red-400" : "text-muted-foreground/60")
    )}>
      {label}
    </span>
  </motion.div>
);

const Signup = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    agreed_to_terms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState({
    username: false,
    email: false,
    password: false,
    confirmPassword: false,
  });

  const { toast } = useToast();
  const navigate = useNavigate();

  // Validation State
  const [validations, setValidations] = useState({
    username: { isValid: false, message: "" },
    email: { isValid: false, message: "" },
    password: {
      isValid: false,
      strength: 0, // 0-100
      requirements: {
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false,
      }
    },
    confirmPassword: { isValid: false, message: "" }
  });

  // Real-time validation
  useEffect(() => {
    const { username, email, password, confirmPassword } = formData;

    // Username Validation
    const usernameRegex = /^[a-z0-9]+$/;
    const isUsernameValid =
      username.length >= 7 &&
      username.length <= 20 &&
      usernameRegex.test(username);

    // Email Validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isEmailValid = emailRegex.test(email);

    // Password Validation
    const hasLength = password.length >= 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    let strength = 0;
    if (hasLength) strength += 20;
    if (hasUpper) strength += 20;
    if (hasLower) strength += 20;
    if (hasNumber) strength += 20;
    if (hasSpecial) strength += 20;

    // Confirm Password Validation
    const isConfirmValid = confirmPassword === password && confirmPassword.length > 0;

    setValidations({
      username: {
        isValid: isUsernameValid,
        message: isUsernameValid ? "" : "7-20 chars, lowercase & numbers only"
      },
      email: {
        isValid: isEmailValid,
        message: isEmailValid ? "" : "Invalid email address"
      },
      password: {
        isValid: strength === 100,
        strength,
        requirements: {
          length: hasLength,
          uppercase: hasUpper,
          lowercase: hasLower,
          number: hasNumber,
          special: hasSpecial,
        }
      },
      confirmPassword: {
        isValid: isConfirmValid,
        message: isConfirmValid ? "" : "Passwords do not match"
      }
    });

  }, [formData]);

  const handleBlur = (field: keyof typeof touched) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all as touched to show errors
    setTouched({
      username: true,
      email: true,
      password: true,
      confirmPassword: true
    });

    if (!validations.username.isValid || !validations.email.isValid || !validations.password.isValid || !validations.confirmPassword.isValid) {
      toast({
        title: "Validation Error",
        description: "Please fix the errors in the form.",
        variant: "destructive",
      });
      return;
    }

    if (!formData.agreed_to_terms) {
      toast({
        title: "Terms Required",
        description: "You must agree to the Terms of Service and Privacy Policy.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      await authService.signup({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        agreed_to_terms: formData.agreed_to_terms,
      });
      toast({
        title: "Account Created",
        description: "Please check your email to verify your account.",
        className: "bg-primary/10 border-primary/20 text-primary",
      });
      // Redirect to email verification page with email state
      navigate("/verify-email", { state: { email: formData.email } });
    } catch (error: any) {
      console.error("Signup Error:", error);

      // Parse and categorize the error for user-friendly messaging
      let errorTitle = "Signup Failed";
      let errorDescription = "Something went wrong while creating your account. Please try again.";

      // Handle Server-Side Validation Errors
      if (error.errors && typeof error.errors === 'object') {
        const newValidations = { ...validations };
        let hasNewErrors = false;

        if (error.errors.username) {
          const usernameError = Array.isArray(error.errors.username) 
            ? error.errors.username.join(', ') 
            : error.errors.username;
          newValidations.username = { isValid: false, message: usernameError };
          hasNewErrors = true;
        }
        if (error.errors.email) {
          const emailError = Array.isArray(error.errors.email) 
            ? error.errors.email.join(', ') 
            : error.errors.email;
          newValidations.email = { isValid: false, message: emailError };
          hasNewErrors = true;
        }
        if (error.errors.password) {
          newValidations.password = {
            ...newValidations.password,
            isValid: false,
          };
          hasNewErrors = true;
        }

        if (hasNewErrors) {
          setValidations(newValidations);
          errorTitle = "Validation Error";
          errorDescription = "Please fix the highlighted fields and try again.";
        }
      }

      // Handle specific error cases with user-friendly messages
      if (error.message) {
        const errorMsg = error.message.toLowerCase();

        // Email-related errors
        if (errorMsg.includes('email') && (errorMsg.includes('exists') || errorMsg.includes('already') || errorMsg.includes('taken'))) {
          errorTitle = "Email Already Registered";
          errorDescription = "This email is already registered. Please login or use a different email.";
        }
        else if (errorMsg.includes('email') && (errorMsg.includes('invalid') || errorMsg.includes('format'))) {
          errorTitle = "Invalid Email";
          errorDescription = "Please enter a valid email address.";
        }
        // Username-related errors
        else if (errorMsg.includes('username') && (errorMsg.includes('exists') || errorMsg.includes('taken') || errorMsg.includes('already'))) {
          errorTitle = "Username Not Available";
          errorDescription = "This username is already taken. Please choose another.";
        }
        else if (errorMsg.includes('username') && errorMsg.includes('invalid')) {
          errorTitle = "Invalid Username";
          errorDescription = "Username must be 7-20 characters, lowercase letters and numbers only.";
        }
        // Password-related errors
        else if (errorMsg.includes('password') && (errorMsg.includes('weak') || errorMsg.includes('requirements') || errorMsg.includes('strong'))) {
          errorTitle = "Weak Password";
          errorDescription = "Password must contain at least 8 characters with uppercase, lowercase, number, and special character.";
        }
        else if (errorMsg.includes('password') && errorMsg.includes('match')) {
          errorTitle = "Passwords Don't Match";
          errorDescription = "The passwords you entered do not match. Please try again.";
        }
        // Network errors
        else if (errorMsg.includes('network') || errorMsg.includes('connection') || errorMsg.includes('fetch')) {
          errorTitle = "Connection Error";
          errorDescription = "Network error. Please check your internet connection and try again.";
        }
        else if (errorMsg.includes('timeout') || errorMsg.includes('timed out')) {
          errorTitle = "Request Timeout";
          errorDescription = "The request took too long. Please check your connection and try again.";
        }
        // Server errors
        else if (error.status >= 500 || errorMsg.includes('server error') || errorMsg.includes('internal error')) {
          errorTitle = "Server Error";
          errorDescription = "Something went wrong on our side. Please try again later.";
        }
        // Authentication/Authorization errors
        else if (error.status === 401 || error.status === 403) {
          errorTitle = "Access Denied";
          errorDescription = error.message || "You don't have permission to perform this action.";
          // Clear any stale token that may be causing this
          localStorage.removeItem("token");
        }
        // Rate limiting
        else if (error.status === 429 || errorMsg.includes('too many') || errorMsg.includes('rate limit')) {
          errorTitle = "Too Many Attempts";
          errorDescription = "Too many signup attempts. Please wait a few minutes and try again.";
        }
        // Generic validation errors
        else if (errorMsg.includes('validation') || errorMsg.includes('invalid')) {
          errorTitle = "Invalid Input";
          errorDescription = error.message;
        }
        // Use the backend message if it's user-friendly
        else if (error.message && !errorMsg.includes('error') && error.message.length < 100) {
          errorDescription = error.message;
        }
      }

      toast({
        title: errorTitle,
        description: errorDescription,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setLoading(true);
    try {
      const googleResult = await signInWithGoogle();
      const response = await authService.signinWithGoogle({
        id_token: googleResult.idToken,
        email: googleResult.email,
        display_name: googleResult.displayName,
        photo_url: googleResult.photoURL,
      });

      // Store the token in localStorage
      if (response.token) {
        localStorage.setItem('token', response.token);
      }

      toast({
        title: "Login Successful",
        description: "Identity verified via Google.",
        className: "bg-primary/10 border-primary/20 text-primary",
      });

      if (response.user && !response.user.profile_completed) {
        navigate("/profile/personal-details");
      } else {
        navigate("/dashboard");
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Identity verification failed.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-neutral-950 relative flex flex-col items-center justify-center antialiased">
      <BackgroundBeams className="opacity-40" />

      <div className="relative z-10 w-full max-w-lg p-4">
        <Ultra3DCard className="w-full backdrop-blur-3xl bg-card border-border/50 shadow-2xl" disableHoverEffects={true}>
          <div className="p-8">
            <div className="text-center mb-8">
              <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="inline-block mb-4 relative group"
              >
                <LiquidLogo
                  src={raampIcon}
                  className="h-20 w-20 border-none bg-transparent"
                  logoClassName="w-12 h-12"
                />
              </motion.div>
              <h1 className="text-4xl font-bold text-foreground font-heading font-semibold mb-2">
                <BlurText text="CREATE ACCOUNT" />
              </h1>
              <p className="text-muted-foreground text-sm font-mono">
                Create your secure account to continue
              </p>
            </div>

            <form onSubmit={handleSignup} className="space-y-4">
              {/* Username Field */}
              <div className="space-y-2">
                <Label htmlFor="username" className="text-xs font-mono uppercase text-muted-foreground">Username</Label>
                <div className="relative group">
                  <User className={cn(
                    "absolute left-3 top-3 h-4 w-4 transition-colors z-10",
                    touched.username && !validations.username.isValid ? "text-red-500" :
                      touched.username && validations.username.isValid ? "text-emerald-500" : "text-muted-foreground"
                  )} />
                  <Input
                    id="username"
                    placeholder="commander1"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value.toLowerCase() })}
                    onBlur={() => handleBlur('username')}
                    className={cn(
                      "pl-10 bg-foreground/5 backdrop-blur-sm border-border/50 font-mono focus:border-border/80 transition-colors",
                      touched.username && !validations.username.isValid ? "border-red-500/50" :
                        touched.username && validations.username.isValid ? "border-emerald-500/50" : ""
                    )}
                    required
                  />
                  {touched.username && validations.username.isValid && (
                    <Check className="absolute right-3 top-3 h-4 w-4 text-emerald-500 z-10" />
                  )}
                  {touched.username && !validations.username.isValid && (
                    <p className="text-[10px] text-red-500 mt-1 font-mono">{validations.username.message}</p>
                  )}
                </div>
              </div>

              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-xs font-mono uppercase text-muted-foreground">Email Address</Label>
                <div className="relative group">
                  <Mail className={cn(
                    "absolute left-3 top-3 h-4 w-4 transition-colors z-10",
                    touched.email && !validations.email.isValid ? "text-red-500" :
                      touched.email && validations.email.isValid ? "text-emerald-500" : "text-muted-foreground"
                  )} />
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@company.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value.toLowerCase() })}
                    onBlur={() => handleBlur('email')}
                    className={cn(
                      "pl-10 bg-foreground/5 backdrop-blur-sm border-border/50 font-mono focus:border-border/80 transition-colors",
                      touched.email && !validations.email.isValid ? "border-red-500/50" :
                        touched.email && validations.email.isValid ? "border-emerald-500/50" : ""
                    )}
                    required
                  />
                  {touched.email && !validations.email.isValid && (
                    <p className="text-[10px] text-red-500 mt-1 font-mono">{validations.email.message}</p>
                  )}
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-xs font-mono uppercase text-muted-foreground">Password</Label>
                <div className="relative group">
                  <Lock className={cn(
                    "absolute left-3 top-3 h-4 w-4 transition-colors z-10",
                    touched.password && !validations.password.isValid ? "text-red-500" :
                      touched.password && validations.password.isValid ? "text-emerald-500" : "text-muted-foreground"
                  )} />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    onBlur={() => handleBlur('password')}
                    className={cn(
                      "pl-10 pr-10 bg-foreground/5 backdrop-blur-sm border-border/50 font-mono focus:border-border/80 transition-colors",
                      touched.password && !validations.password.isValid ? "border-red-500/50" :
                        touched.password && validations.password.isValid ? "border-emerald-500/50" : ""
                    )}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-muted-foreground hover:text-white/80 transition-colors z-10"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Micro-Interaction Strength Meter & Checklist */}
                {formData.password && (
                  <div className="mt-3 space-y-3">
                    <div className="flex gap-1 h-1">
                      {[20, 40, 60, 80, 100].map((step) => (
                        <motion.div
                          key={step}
                          className={cn(
                            "h-full flex-1 rounded-full transition-colors duration-300",
                            validations.password.strength >= step
                              ? (validations.password.strength < 60 ? "bg-red-500" : validations.password.strength < 100 ? "bg-yellow-500" : "bg-emerald-500")
                              : "bg-foreground/5"
                          )}
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: 1 }}
                        />
                      ))}
                    </div>

                    <div className="grid grid-cols-2 gap-x-4 gap-y-2 px-1">
                      <PasswordRequirementItem
                        label="8+ Characters"
                        isMet={validations.password.requirements.length}
                        showError={touched.password}
                      />
                      <PasswordRequirementItem
                        label="Uppercase (A-Z)"
                        isMet={validations.password.requirements.uppercase}
                        showError={touched.password}
                      />
                      <PasswordRequirementItem
                        label="Lowercase (a-z)"
                        isMet={validations.password.requirements.lowercase}
                        showError={touched.password}
                      />
                      <PasswordRequirementItem
                        label="Number (0-9)"
                        isMet={validations.password.requirements.number}
                        showError={touched.password}
                      />
                      <PasswordRequirementItem
                        label="Special (!@#$)"
                        isMet={validations.password.requirements.special}
                        showError={touched.password}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-xs font-mono uppercase text-muted-foreground">Confirm Password</Label>
                <div className="relative group">
                  <Lock className={cn(
                    "absolute left-3 top-3 h-4 w-4 transition-colors z-10",
                    touched.confirmPassword && !validations.confirmPassword.isValid ? "text-red-500" :
                      touched.confirmPassword && validations.confirmPassword.isValid ? "text-emerald-500" : "text-muted-foreground"
                  )} />
                  <Input
                    id="confirmPassword"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    onBlur={() => handleBlur('confirmPassword')}
                    className={cn(
                      "pl-10 pr-10 bg-foreground/5 backdrop-blur-sm border-border/50 font-mono focus:border-border/80 transition-colors",
                      touched.confirmPassword && !validations.confirmPassword.isValid ? "border-red-500/50" :
                        touched.confirmPassword && validations.confirmPassword.isValid ? "border-emerald-500/50" : ""
                    )}
                    required
                  />
                  {touched.confirmPassword && !validations.confirmPassword.isValid && (
                    <p className="text-[10px] text-red-500 mt-1 font-mono">{validations.confirmPassword.message}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <Checkbox
                  id="terms"
                  className="border-border/80 data-[state=checked]:bg-primary data-[state=checked]:text-black"
                  required
                  checked={formData.agreed_to_terms}
                  onCheckedChange={(checked) => setFormData({ ...formData, agreed_to_terms: checked as boolean })}
                />
                <Label htmlFor="terms" className="text-xs font-normal text-muted-foreground">
                  I agree to the <Link to="/terms" className="text-primary hover:underline">Terms of Service</Link> and <Link to="/privacy" className="text-primary hover:underline">Privacy Policy</Link>
                </Label>
              </div>

              <MagneticButton
                type="submit"
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-semibold h-11 border border-primary/20 transition-all duration-300 mt-4"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    Creating Account...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    Create Account <ArrowRight className="w-4 h-4" />
                  </span>
                )}
              </MagneticButton>
            </form>

            <div className="relative py-6">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border/50" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-black/50 px-2 text-muted-foreground backdrop-blur-sm">Or continue with</span>
              </div>
            </div>

            <MagneticButton
              type="button"
              className="w-full border border-border/50 bg-foreground/5 hover:bg-foreground/10 text-foreground font-mono text-xs h-10"
              onClick={handleGoogleSignup}
              disabled={loading}
            >
              <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Google
            </MagneticButton>

            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link to="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
                  Login
                </Link>
              </p>
            </div>

            {/* Security Badge */}
            <div className="mt-8 flex justify-center gap-6 text-[10px] uppercase tracking-widest text-muted-foreground/40 font-mono">
              <div className="flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                <span>End-to-End Encrypted</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>Node Active</span>
              </div>
            </div>
          </div>
        </Ultra3DCard>
      </div>
    </div>
  );
};

export default Signup;