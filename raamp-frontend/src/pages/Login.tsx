import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { InputSpotlight } from "@/components/ui/input-spotlight";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/useAuth";
import { authService } from "@/services/authService";
import { signInWithGoogle } from "@/services/googleAuth";
import { motion } from "framer-motion";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";
import raampIcon from "@/assets/raamp-logo-v6-transparent.png";
import { Lock, Mail, ArrowRight, ShieldCheck, Eye, EyeOff, Globe } from "lucide-react";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { VelocityScroll } from "@/components/ui/velocity-scroll";
import { LiquidLogo } from "@/components/ui/liquid-logo";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth(); // Use the new login method

  // Autofill email if provided (e.g. from Signup/Verify flow)
  useEffect(() => {
    if (location.state?.email) {
      setEmail(location.state.email);
    }
  }, [location.state]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Client-side validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim()) {
      toast({
        title: "Email Required",
        description: "Please enter your email address.",
        variant: "destructive",
      });
      return;
    }
    
    if (!emailRegex.test(email)) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid email address.",
        variant: "destructive",
      });
      return;
    }
    
    if (!password.trim()) {
      toast({
        title: "Password Required",
        description: "Please enter your password.",
        variant: "destructive",
      });
      return;
    }
    
    if (password.length < 8) {
      toast({
        title: "Password Too Short",
        description: "Password must be at least 8 characters long.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    // Get "Remember Me" state
    const rememberMe = (document.getElementById("remember") as HTMLInputElement)?.checked || false;

    try {
      const response = await authService.signin({ email, password });

      // Store the token in localStorage
      if (response.token) {
        localStorage.setItem('token', response.token);
      }

      // Update AuthContext with persistence preference
      if (response.user) {
        login(response.user, rememberMe);
      }

      toast({
        title: "Login Successful",
        description: "Welcome back to the command center.",
        className: "bg-primary/10 border-primary/20 text-primary",
      });

      if (response.user && !response.user.profile_completed) {
        navigate("/profile/personal-details");
      } else {
        navigate("/dashboard");
      }
    } catch (error: any) {
      // Use the enhanced error messages from the API
      let errorTitle = "Login Failed";
      let errorDescription = error.message || "An unexpected error occurred.";

      // Map specific error statuses to titles
      if (error.status === 0) {
        // Network error or timeout
        errorTitle = "Connection Error";
        // Use the message from API (already user-friendly)
      } else if (error.status === 401 || error.status === 422) {
        // Unauthorized - wrong credentials or unverified
        errorTitle = "Authentication Failed";
        // Message already set by API (e.g., "Incorrect email or password")
      } else if (error.status === 400) {
        // Bad request - validation error
        errorTitle = "Invalid Input";
        // Message already set by API (e.g., "Please enter a valid email address")
      } else if (error.status === 403) {
        // Forbidden - account locked
        errorTitle = "Account Locked";
        // Message already set by API
      } else if (error.status === 429) {
        // Too many requests
        errorTitle = "Too Many Attempts";
        // Message already set by API
      } else if (error.status >= 500) {
        // Server error
        errorTitle = "Server Error";
        errorDescription = error.message || "Server error. Please try again later.";
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

  const handleGoogleLogin = async () => {
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

      // Default to true (or session) for Google, but let's assume session for now unless we add a UI for it
      if (response.user) {
        login(response.user, true); // Defaulting to "remember" for OAuth for better UX
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
    <div className="min-h-screen flex bg-background relative overflow-hidden">

      {/* Left Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <div className="mb-8">
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
            <h1 className="text-4xl font-bold text-white font-bebas tracking-wide mb-2">
              <BlurText text="LOGIN" />
            </h1>
            <p className="text-muted-foreground text-sm">
              Enter your credentials to access the platform.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <InputSpotlight
                id="email"
                type="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <InputSpotlight
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-muted-foreground hover:text-primary transition-colors z-10"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox id="remember" className="border-white/20 data-[state=checked]:bg-primary data-[state=checked]:text-black" />
              <Label htmlFor="remember" className="text-sm font-normal text-muted-foreground">
                Keep me logged in
              </Label>
            </div>

            <MagneticButton
              type="submit"
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-semibold h-11 shadow-[0_0_20px_rgba(0,224,208,0.2)] hover:shadow-[0_0_30px_rgba(0,224,208,0.4)] transition-all duration-300"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Authenticating...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Login <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </MagneticButton>
          </form>

          <div className="relative py-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>

          <MagneticButton
            type="button"
            className="w-full border border-white/10 bg-white/5 hover:bg-white/10 text-white font-mono text-xs h-10"
            onClick={handleGoogleLogin}
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
              Don't have an account?{" "}
              <Link to="/signup" className="text-primary hover:text-primary/80 font-medium transition-colors">
                Sign Up
              </Link>
            </p>
          </div>
        </motion.div>
      </div>

      {/* Right Side - Visuals */}
      <div className="hidden lg:flex w-1/2 bg-black relative overflow-hidden items-center justify-center">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,224,208,0.1),transparent_70%)]" />
        <div className="absolute inset-0 opacity-20 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

        <div className="relative z-10 text-center p-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mb-8 relative"
          >
            <LiquidLogo
              src={raampIcon}
              className="w-64 h-64 mx-auto"
              logoClassName="w-32 h-32"
            />
          </motion.div>

          <h2 className="text-3xl font-bold text-white font-bebas tracking-wide mb-4">
            Global Intelligence Network
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Join thousands of marketers leveraging autonomous AI to dominate their local markets.
          </p>
        </div>

        {/* Velocity Scroll at bottom of right panel */}
        <div className="absolute bottom-10 left-0 w-full opacity-20">
          <VelocityScroll text="SECURE ACCESS // ENCRYPTED CONNECTION //" />
        </div>
      </div>

    </div>
  );
};

export default Login;