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
import { toast as sonner } from "sonner";
import { authService } from "@/services/authService";
import { MESSAGES } from "@/constants/messages";
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
import { BlurText } from "@/components/ui/text-reveal";
import { PasswordVerificationDialog } from "@/components/PasswordVerificationDialog";

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
  // Account action states
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showPasswordGate, setShowPasswordGate] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [showDeleteOtpDialog, setShowDeleteOtpDialog] = useState(false);
  const [deleteOtp, setDeleteOtp] = useState("");
  const [deleteOtpError, setDeleteOtpError] = useState("");
  const [isSendingDeleteOtp, setIsSendingDeleteOtp] = useState(false);
  const [isResendingDeleteOtp, setIsResendingDeleteOtp] = useState(false);

  // Password change (keep it in Account & Security to avoid UX fragmentation)
  const [showPwdOtpDialog, setShowPwdOtpDialog] = useState(false);
  const [showPwdDialog, setShowPwdDialog] = useState(false);
  const [pwdOtp, setPwdOtp] = useState("");
  const [pwdOtpError, setPwdOtpError] = useState("");
  const [pwdCurrent, setPwdCurrent] = useState("");
  const [pwdNew, setPwdNew] = useState("");
  const [pwdConfirm, setPwdConfirm] = useState("");
  const [pwdSaving, setPwdSaving] = useState(false);

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

  const lastLoginLabel = () => {
    const last = userProfile?.last_login;
    if (last) return formatDate(last);
    // Legacy users may not have last_login; don't show "Never" (feels broken)
    return "First login";
  };

  const handleChangePassword = async () => {
    if (!userProfile?.email) {
      toast({
        title: "Error",
        description: "Missing email. Please refresh and try again.",
        variant: "destructive",
      });
      return;
    }

    try {
      await authService.sendChangePasswordOtp({ email: userProfile.email });
      setPwdOtp("");
      setPwdOtpError("");
      setShowPwdOtpDialog(true);
      sonner.success("Verification code sent", {
        description: `We emailed a 6-digit code to ${userProfile.email}.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to send verification code. Please try again.",
        variant: "destructive",
      });
    }
  };

  const verifyPwdOtp = () => {
    setPwdOtpError("");
    if (!pwdOtp || pwdOtp.trim().length !== 6) {
      setPwdOtpError("Please enter the 6-digit code.");
      return;
    }
    setShowPwdOtpDialog(false);
    setShowPwdDialog(true);
  };

  const saveNewPassword = async () => {
    if (!userProfile?.email) {
      sonner.error("Error", { description: "Missing email. Please refresh and try again." });
      return;
    }
    if (!pwdCurrent.trim()) {
      sonner.error("Error", { description: "Current password is required." });
      return;
    }
    if (pwdNew.length < 8) {
      sonner.error("Error", { description: "Password must be at least 8 characters." });
      return;
    }
    if (pwdNew !== pwdConfirm) {
      sonner.error("Error", { description: "Passwords do not match." });
      return;
    }

    setPwdSaving(true);
    try {
      const resp = await authService.changePassword({
        current_password: pwdCurrent,
        otp_code: pwdOtp.trim(),
        new_password: pwdNew,
        confirm_password: pwdConfirm,
      });
      sonner.success("Password Updated", {
        description: MESSAGES.AUTH.PASSWORD_UPDATED,
      });
      setShowPwdDialog(false);
      setPwdOtp("");
      setPwdCurrent("");
      setPwdNew("");
      setPwdConfirm("");
    } catch {
      sonner.error("Could Not Change Password", {
        description: MESSAGES.AUTH.PASSWORD_UPDATE_FAILED,
      });
    } finally {
      setPwdSaving(false);
    }
  };

  const handleDeleteAccountClick = () => {
    setShowDeleteConfirmation(true);
  };

  const handleConfirmDelete = () => {
    setShowDeleteConfirmation(false);
    void (async () => {
      if (!userProfile?.email) {
        toast({
          title: "Error",
          description: "Could not determine your email. Please refresh and try again.",
          variant: "destructive",
        });
        return;
      }

      setIsSendingDeleteOtp(true);
      try {
        await apiClient.post("/auth/account-deletion/send-otp", { email: userProfile.email });
        sonner.success("Verification code sent", {
          description: `We emailed a 6-digit code to ${userProfile.email}.`,
        });
        setDeleteOtp("");
        setDeleteOtpError("");
        setShowDeleteOtpDialog(true);
      } catch (error: any) {
        toast({
          title: "Error",
          description: "Failed to send verification code. Please try again.",
          variant: "destructive",
        });
      } finally {
        setIsSendingDeleteOtp(false);
      }
    })();
  };

  const handleResendDeleteOtp = async () => {
    if (!userProfile?.email) return;
    setIsResendingDeleteOtp(true);
    try {
      await apiClient.post("/auth/account-deletion/send-otp", { email: userProfile.email });
      sonner.success("Code resent", { description: `Sent to ${userProfile.email}` });
      setDeleteOtpError("");
    } catch (error: any) {
      toast({
        title: "Resend failed",
        description: "Could not resend the code. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsResendingDeleteOtp(false);
    }
  };

  const handleVerifyDeleteOtp = async () => {
    setDeleteOtpError("");
    if (!deleteOtp || deleteOtp.trim().length !== 6) {
      setDeleteOtpError("Please enter the 6-digit code.");
      return;
    }
    if (!userProfile?.email) {
      setDeleteOtpError("Missing email. Please refresh and try again.");
      return;
    }

    setShowDeleteOtpDialog(false);
    setIsDeleting(true);

    try {
      await apiClient.post("/auth/account-deletion/verify", {
        email: userProfile.email,
        code: deleteOtp.trim(),
      });

      localStorage.removeItem("user");
      localStorage.removeItem("token");
      try {
        // Best-effort cookie cleanup (if backend uses httpOnly cookie auth in any env)
        await authService.logout();
      } catch {
        // ignore
      }
      sonner.success("Account Deleted", {
        description: "Your account was permanently deleted.",
      });
      navigate("/");
    } catch (error) {
      toast({
        title: "Deletion Failed",
        description: "Invalid or expired code, or deletion failed. Please try again.",
        variant: "destructive",
      });
      setShowDeleteOtpDialog(true);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleUnlock = () => {
    setShowPasswordGate(true);
  };

  const handleVerified = () => {
    setShowPasswordGate(false);
    setIsUnlocked(true);
    sonner.success("Identity Verified", {
      description: "Sensitive actions are now available.",
    });
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
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                <Shield className="w-7 h-7 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold font-heading font-semibold">
                  <BlurText text="Account & Security" />
                </h1>
                <p className="text-muted-foreground font-mono text-sm">Manage your account security settings</p>
              </div>
            </div>
            {!isUnlocked && (
              <Button
                variant="outline"
                onClick={handleUnlock}
                className="font-mono text-xs gap-2 border-primary/30 hover:bg-primary/5"
              >
                <Shield className="w-4 h-4" />
                Unlock Settings
              </Button>
            )}
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 font-heading font-semibold">
              <Key className="w-5 h-5 text-primary" />
              Password
            </h2>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground font-mono">
                Keep your account secure with a strong password.
              </p>
              <Button
                variant="outline"
                onClick={handleChangePassword}
                className="font-mono text-xs"
                disabled={!isUnlocked}
              >
                Change Password
              </Button>
            </div>
          </Card>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.2}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 font-heading font-semibold">
              <Clock className="w-5 h-5 text-primary" />
              Last Login
            </h2>
            <div className="p-4 rounded-lg bg-muted/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium font-mono">Last Active Session</p>
                  <p className="text-lg text-foreground mt-1 font-mono">
                    {lastLoginLabel()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground font-mono">Account Created</p>
                  <p className="text-sm text-muted-foreground font-mono">
                    {formatDate(userProfile?.created_at)}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.3}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-destructive/20">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 font-heading font-semibold">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Danger Zone
            </h2>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground font-mono">
                Once you delete your account, there is no going back. All your data,
                business profiles, and settings will be permanently removed.
              </p>
              <Button
                variant="destructive"
                onClick={handleDeleteAccountClick}
                disabled={!isUnlocked || isDeleting || isSendingDeleteOtp}
                className="font-mono text-xs"
              >
                {isSendingDeleteOtp ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Sending code...
                  </>
                ) : isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Delete Account"
                )}
              </Button>
            </div>
          </Card>
        </Reveal>
      </motion.div>

      {/* Password OTP Dialog */}
      <Dialog open={showPwdOtpDialog} onOpenChange={setShowPwdOtpDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Password change verification</DialogTitle>
            <DialogDescription>Enter the 6-digit code we emailed you.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label htmlFor="pwdOtp">OTP code</Label>
            <Input
              id="pwdOtp"
              value={pwdOtp}
              onChange={(e) => setPwdOtp(e.target.value)}
              maxLength={6}
              placeholder="000000"
            />
            {pwdOtpError && <p className="text-xs text-destructive">{pwdOtpError}</p>}
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowPwdOtpDialog(false)}>
              Cancel
            </Button>
            <Button onClick={verifyPwdOtp}>Verify</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={showPwdDialog} onOpenChange={setShowPwdDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Change password</DialogTitle>
            <DialogDescription>Enter your current password and a new password.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1">
              <Label htmlFor="pwdCurrent">Current password</Label>
              <Input
                id="pwdCurrent"
                type="password"
                value={pwdCurrent}
                onChange={(e) => setPwdCurrent(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="pwdNew">New password</Label>
              <Input
                id="pwdNew"
                type="password"
                value={pwdNew}
                onChange={(e) => setPwdNew(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="pwdConfirm">Confirm new password</Label>
              <Input
                id="pwdConfirm"
                type="password"
                value={pwdConfirm}
                onChange={(e) => setPwdConfirm(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowPwdDialog(false)} disabled={pwdSaving}>
              Cancel
            </Button>
            <Button onClick={saveNewPassword} disabled={pwdSaving}>
              {pwdSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving…
                </>
              ) : (
                "Update password"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirmation} onOpenChange={setShowDeleteConfirmation}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive font-heading font-semibold">
              <AlertTriangle className="w-5 h-5" />
              Delete Account?
            </DialogTitle>
            <DialogDescription className="font-mono text-xs">
              This action cannot be undone. We will send a verification code to your email
              to confirm this action.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground font-mono">
              Your account <strong>{userProfile?.email}</strong> and all associated data
              will be permanently deleted.
            </p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowDeleteConfirmation(false)} className="font-mono text-xs">
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete} className="font-mono text-xs" disabled={isSendingDeleteOtp}>
              {isSendingDeleteOtp ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                "Send Verification Code"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete OTP Dialog */}
      <Dialog open={showDeleteOtpDialog} onOpenChange={setShowDeleteOtpDialog}>
        <DialogContent className="bg-background/90 border-primary/30 text-foreground backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="font-heading font-semibold text-2xl text-primary">CONFIRM ACCOUNT DELETION</DialogTitle>
            <DialogDescription className="font-mono text-xs text-muted-foreground">
              Enter the 6-digit verification code sent to your email. This action is irreversible.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="deleteOtp" className="text-xs font-mono text-primary">ONE-TIME CODE</Label>
              <Input
                id="deleteOtp"
                value={deleteOtp}
                onChange={(e) => setDeleteOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="bg-black/50 border-border/50 text-center text-2xl tracking-[0.5em] font-mono focus:border-primary/50 focus:ring-primary/20"
                maxLength={6}
                placeholder="000000"
              />
              {deleteOtpError && <p className="text-red-500 text-xs font-mono">{deleteOtpError}</p>}
              <button
                type="button"
                onClick={handleResendDeleteOtp}
                disabled={isResendingDeleteOtp || isDeleting || isSendingDeleteOtp}
                className="text-[11px] font-mono text-primary/80 hover:text-primary underline-offset-4 hover:underline disabled:opacity-50 disabled:no-underline"
              >
                {isResendingDeleteOtp ? "Resending…" : "Resend code"}
              </button>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => {
                setShowDeleteOtpDialog(false);
                setDeleteOtp("");
                setDeleteOtpError("");
              }}
              className="font-mono text-xs text-muted-foreground/80 hover:text-foreground"
            >
              Cancel
            </Button>
            <Button onClick={handleVerifyDeleteOtp} className="bg-red-600 text-white hover:bg-red-600/90 font-heading font-semibold" disabled={isDeleting}>
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Verify & Delete"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <PasswordVerificationDialog
        isOpen={showPasswordGate}
        onClose={() => setShowPasswordGate(false)}
        onVerified={handleVerified}
      />
    </Layout>
  );
};

export default AccountSecurity;
