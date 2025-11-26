import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Lock, Check } from "lucide-react";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { toast } from "@/hooks/use-toast";

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
      const response = await apiClient.post('/auth/forgot-password', {
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
        <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="text-center space-y-6">
            <div className="flex justify-center mb-4">
              <img src={raampIcon} alt="RAAMP" className="h-20 w-20" />
            </div>
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center">
                <Check className="w-10 h-10 text-success" />
              </div>
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Check Your Email</h1>
              <p className="text-muted-foreground">
                We've sent password reset instructions to
              </p>
              <p className="text-foreground font-medium">{email}</p>
              <p className="text-sm text-muted-foreground mt-4">
                If you don't see the email, check your spam folder.
              </p>
            </div>
            <Link to="/login">
              <Button className="bg-gradient-to-r from-primary to-accent hover:opacity-90">
                Back to Sign In
              </Button>
            </Link>
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
              <Lock className="w-8 h-8 text-primary" />
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">Forgot Your Password?</h1>
              <p className="text-muted-foreground">
                Enter the email address associated with your account, and we'll send you a secure link to reset your password.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-background/50"
              />
            </div>

            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-primary to-accent hover:opacity-90 transition-opacity"
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
          </form>

          <div className="text-center">
            <Link
              to="/login"
              className="text-sm text-primary hover:underline inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Sign In
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ForgotPassword;
