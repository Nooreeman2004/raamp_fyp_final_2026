import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Key, Clock, AlertTriangle, Loader2 } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { apiClient } from "@/services/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";

interface UserProfile {
  email: string;
  last_login?: string;
  created_at?: string;
}

const AccountSecurity = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  
  // Delete account dialog states
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showOtpDialog, setShowOtpDialog] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);

  const fetchUserProfile = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get("/auth/me") as { email: string; last_login?: string; created_at?: string };
      setUserProfile({
        email: response.email,
        last_login: response.last_login,
        created_at: response.created_at,
      });
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      toast({
        title: "Error",
        description: "Failed to load profile data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleChangePassword = () => {
    navigate("/profile/user");
    toast({
      title: "Change Password",
      description: "You can change your password from the Edit Profile page.",
    });
  };

  const handleDeleteAccountClick = () => {
    setShowDeleteConfirmation(true);
  };

  const handleConfirmDelete = async () => {
    setShowDeleteConfirmation(false);
    setIsSendingOtp(true);
    
    try {
      await apiClient.post("/auth/account-deletion/send-otp", {
        email: userProfile?.email,
      });
      setShowOtpDialog(true);
      toast({
        title: "Verification Code Sent",
        description: "Please check your email for the verification code.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: (error instanceof Error ? error.message : null) || "Failed to send verification code",
        variant: "destructive",
      });
    } finally {
      setIsSendingOtp(false);
    }
  };

  const handleVerifyAndDelete = async () => {
    if (otpCode.length !== 6) {
      toast({
        title: "Invalid Code",
        description: "Please enter a 6-digit verification code",
        variant: "destructive",
      });
      return;
    }

    setIsVerifyingOtp(true);
    
    try {
      await apiClient.post("/auth/account-deletion/verify", {
        email: userProfile?.email,
        code: otpCode,
      });
      
      // Clear local storage and redirect
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      
      toast({
        title: "Account Deleted",
        description: "Your account has been permanently deleted. We're sorry to see you go.",
      });
      
      // Redirect to home
      navigate("/");
    } catch (error) {
      toast({
        title: "Verification Failed",
        description: (error instanceof Error ? error.message : null) || "Invalid or expired verification code",
        variant: "destructive",
      });
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  if (isLoading) {
    return (
      <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Account & Security" }]}>
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Account & Security" }]}>
      <motion.div
        className="space-y-6 max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
              <Shield className="w-7 h-7 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Account & Security</h1>
              <p className="text-muted-foreground">Manage your account security settings</p>
            </div>
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Key className="w-5 h-5 text-primary" />
              Password
            </h2>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Keep your account secure with a strong password.
              </p>
              <Button variant="outline" onClick={handleChangePassword}>
                Change Password
              </Button>
            </div>
          </Card>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.2}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Last Login
            </h2>
            <div className="p-4 rounded-lg bg-muted/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Last Active Session</p>
                  <p className="text-lg text-foreground mt-1">
                    {formatDate(userProfile?.last_login)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">Account Created</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(userProfile?.created_at)}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.3}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-destructive/20">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Danger Zone
            </h2>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Once you delete your account, there is no going back. All your data, 
                business profiles, and settings will be permanently removed.
              </p>
              <Button 
                variant="destructive" 
                onClick={handleDeleteAccountClick}
                disabled={isSendingOtp}
              >
                {isSendingOtp ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Sending Code...
                  </>
                ) : (
                  "Delete Account"
                )}
              </Button>
            </div>
          </Card>
        </Reveal>
      </motion.div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirmation} onOpenChange={setShowDeleteConfirmation}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              Delete Account?
            </DialogTitle>
            <DialogDescription>
              This action cannot be undone. We will send a verification code to your email 
              to confirm this action.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground">
              Your account <strong>{userProfile?.email}</strong> and all associated data 
              will be permanently deleted.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowDeleteConfirmation(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Send Verification Code
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* OTP Verification Dialog */}
      <Dialog open={showOtpDialog} onOpenChange={setShowOtpDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <Shield className="w-5 h-5" />
              Verify Account Deletion
            </DialogTitle>
            <DialogDescription>
              Enter the 6-digit verification code sent to your email.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="otp">Verification Code</Label>
              <Input
                id="otp"
                placeholder="Enter 6-digit code"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                maxLength={6}
                className="text-center text-2xl tracking-widest font-mono"
              />
            </div>
            <p className="text-xs text-muted-foreground text-center">
              This code expires in 10 minutes.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => {
              setShowOtpDialog(false);
              setOtpCode("");
            }}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleVerifyAndDelete}
              disabled={isVerifyingOtp || otpCode.length !== 6}
            >
              {isVerifyingOtp ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete My Account"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default AccountSecurity;
