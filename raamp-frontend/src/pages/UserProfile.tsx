import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { authService } from "@/services/authService";
import { toast as sonner } from "sonner";
import { User, Shield, Lock, Upload, Cpu, HelpCircle } from "lucide-react";
import Layout from "@/components/Layout";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Animation Imports
import Reveal from "@/components/ui/Reveal";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

const UserProfile = () => {
  // Override breadcrumb to remove "Profile" and show just "User Profile"
  const customBreadcrumbOverride = [
    { label: "Home", path: "/dashboard" },
    { label: "User Profile", path: "/profile/user" }
  ];

  const [isEditing, setIsEditing] = useState(false);
  const [userData, setUserData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    company: "",
    bio: "",
    role: "",
    profilePicture: "",
    username: "",
    address: "",
    website: "",
  });

  // Track initial data to detect changes
  const [initialUserData, setInitialUserData] = useState("");

  const hasUnsavedChanges = JSON.stringify({
    firstName: userData.firstName,
    lastName: userData.lastName,
    phone: userData.phone,
    company: userData.company,
    bio: userData.bio,
    role: userData.role,
  }) !== initialUserData;


  // OTP Dialog State
  const [showOtpDialog, setShowOtpDialog] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState("");

  // Password Change State
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showPasswordOtpDialog, setShowPasswordOtpDialog] = useState(false);
  const [passwordOtp, setPasswordOtp] = useState("");
  const [passwordOtpError, setPasswordOtpError] = useState("");
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleEdit = async () => {
    if (isEditing) return;

    try {
      // Send OTP to email
      await authService.sendProfileEditOtp({ email: userData.email });
      sonner.info("Verification Required", {
        description: `A security code has been sent to ${userData.email}`,
      });
      setShowOtpDialog(true);
    } catch (err: any) {
      const cooldownMsg = err?.errors?.cooldown || err?.errors?.message || err?.message;
      if (cooldownMsg) {
        sonner.error("Cooldown active", { description: cooldownMsg });
      } else {
        sonner.error("Error", { description: err?.message || 'Failed to send OTP' });
      }
    }
  };

  const handleVerifyOtp = async () => {
    setOtpError("");
    try {
      await authService.verifyProfileEditOtp({ email: userData.email, code: otp });
      setShowOtpDialog(false);
      setIsEditing(true);
      sonner.success("Verified", {
        description: "You can now edit your profile",
      });
    } catch (err: any) {
      setOtpError(err?.message || "Invalid OTP. Please try again.");
    }
  };

  // Load real user profile and business data on mount
  useEffect(() => {
    (async () => {
      try {
        const [u, b] = await Promise.all([
          authService.getProfile(),
          import('@/services/businessService').then(m => m.businessService.getHyperlocalSetup().catch(() => null))
        ]);

        if (u) {
          let businessName = (u.company as string) || '';
          let businessAddress = '';
          let businessWebsite = '';
          let businessDescription = (u.bio as string) || '';
          let businessPhone = (u.phone_number as string) || '';

          // If business data exists, it takes precedence or fills gaps
          if (b && b.has_setup !== false) {
            businessName = b.business_name || businessName;
            businessAddress = b.formatted_address || '';
            businessWebsite = b.website || '';
            businessDescription = b.description || businessDescription;
            businessPhone = b.phone || businessPhone;
          } else if (b && b.latitude) {
            // Partial location data
            businessName = b.business_name || businessName;
            businessAddress = b.formatted_address || '';
          }

          const data = {
            firstName: (u.first_name as string) || u.username || '',
            lastName: (u.last_name as string) || '',
            email: u.email || '',
            phone: businessPhone,
            company: businessName,
            address: businessAddress,
            website: businessWebsite,
            bio: businessDescription,
            role: (u.role as string) || '',
            profilePicture: (u.profile_picture as string) || '',
            username: u.username || '',
          };
          setUserData(data);
          setInitialUserData(JSON.stringify({
            firstName: data.firstName,
            lastName: data.lastName,
            phone: data.phone,
            company: data.company,
            address: data.address,
            website: data.website,
            bio: data.bio,
            role: data.role,
          }));
        }
      } catch (err) {
        // ignore
      }
    })();
  }, []);

  const handleSave = async () => {
    // Map frontend fields to backend update fields
    // We update both User profile and Business profile

    // 1. Update User Profile
    const userPayload = {
      first_name: userData.firstName,
      last_name: userData.lastName,
      phone_number: userData.phone,
      company: userData.company,
      bio: userData.bio,
      role: userData.role,
    };

    // 2. Update Business Profile (if address/website present or if company/bio changed)
    // We need to fetch the current business setup to get lat/long/type if we are updating
    // Since we don't store lat/long in the form, we assume they haven't changed or we can't update them here.
    // However, saveHyperlocalSetup requires them.
    // Strategy: We will only update business text fields if business data exists.

    try {
      setIsEditing(false); // Optimistic close

      // Parallel save
      const promises: Promise<any>[] = [
        authService.updateProfile(userPayload)
      ];

      // Only try to save business details if we have them. 
      // We'd ideally need the full object or patch support.
      // For now, let's try to fetch current, merge, and save.
      const { businessService } = await import('@/services/businessService');
      const currentBusiness = await businessService.getHyperlocalSetup().catch(() => null);

      if (currentBusiness) {
        promises.push(businessService.saveHyperlocalSetup({
          business_name: userData.company,
          business_type: currentBusiness.business_type || "General",
          latitude: currentBusiness.latitude || 0,
          longitude: currentBusiness.longitude || 0,
          place_id: currentBusiness.place_id,
          formatted_address: userData.address || currentBusiness.formatted_address,
          website: userData.website || currentBusiness.website,
          phone: userData.phone,
          description: userData.bio
        }));
      }

      const [userResp] = await Promise.all(promises);

      // Update local state and localStorage
      const updated = userResp.user;
      const updatedData = {
        ...userData, // keep address/website from state
        firstName: updated.first_name || userData.firstName,
        lastName: updated.last_name || userData.lastName,
        email: updated.email || userData.email,
        phone: updated.phone_number || userData.phone,
        company: updated.company || userData.company,
        bio: updated.bio || userData.bio,
        role: updated.role || userData.role,
        profilePicture: updated.profile_picture || userData.profilePicture,
        username: updated.username || userData.username,
      };
      setUserData(updatedData);
      setInitialUserData(JSON.stringify({
        firstName: updatedData.firstName,
        lastName: updatedData.lastName,
        phone: updatedData.phone,
        company: updatedData.company,
        address: updatedData.address,
        website: updatedData.website,
        bio: updatedData.bio,
        role: updatedData.role,
      }));
      try { localStorage.setItem('user', JSON.stringify(userResp.user)); } catch { }
      sonner.success("Profile Updated", {
        description: "Your changes have been saved successfully.",
      });
    } catch (err: any) {
      sonner.error("Update Failed", {
        description: err?.message || 'Failed to save profile',
      });
      setIsEditing(true); // Revert edit mode on error
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const handleVerifyPasswordOtp = async () => {
    setPasswordOtpError("");
    if (!passwordOtp || passwordOtp.length !== 6) {
      setPasswordOtpError("Please enter a valid 6-digit OTP");
      return;
    }

    setShowPasswordOtpDialog(false);
    setShowPasswordDialog(true);
  };

  const handleChangePassword = () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      sonner.error("Error", { description: "Passwords do not match" });
      return;
    }

    if (passwordData.newPassword.length < 8) {
      sonner.error("Error", { description: "Password must be at least 8 characters" });
      return;
    }

    (async () => {
      try {
        const resp = await authService.changePassword({
          otp_code: passwordOtp,
          new_password: passwordData.newPassword,
          confirm_password: passwordData.confirmPassword,
        });

        sonner.success("Password Updated", {
          description: resp.message || "Password changed successfully",
        });
        setShowPasswordDialog(false);
        setShowPasswordOtpDialog(false);
        setPasswordData({ currentPassword: "", newPassword: "", confirmPassword: "" });
        setPasswordOtp("");
      } catch (err: any) {
        const msg = err?.message || (err?.errors ? JSON.stringify(err.errors) : 'Failed to change password');
        sonner.error("Error", { description: msg });
      }
    })();
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      sonner.error("Upload Error", {
        description: "File size must be less than 5MB",
      });
      return;
    }

    try {
      const { uploadProfilePicture } = await import('@/services/storageService');

      sonner.info("Uploading...", {
        description: "Please wait while we upload your profile picture",
      });

      const downloadURL = await uploadProfilePicture(file, userData.email || userData.username);

      await authService.updateProfile({
        ...userData,
        profile_picture: downloadURL,
      } as any);

      setUserData({ ...userData, profilePicture: downloadURL });
      sonner.success("Success", {
        description: "Profile picture updated successfully",
      });
    } catch (err: any) {
      sonner.error("Error", {
        description: err?.message || "Failed to upload profile picture",
      });
    }
  };

  return (
    <Layout breadcrumbOverride={customBreadcrumbOverride}>
      <div className="max-w-3xl mx-auto space-y-6">
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded border border-primary/30">
                <User className="w-8 h-8 text-primary animate-pulse" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
                  <BlurText text="USER PROFILE" />
                </h1>
                <p className="text-muted-foreground font-mono text-sm">
                    // MANAGE IDENTITY // SECURITY PROTOCOLS
                </p>
              </div>
            </div>
            {!isEditing && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button onClick={handleEdit} className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-bebas tracking-wider border border-primary/50 shadow-[0_0_15px_rgba(0,224,208,0.3)]">
                      <Shield className="w-4 h-4 mr-2" />
                      EDIT PROFILE
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent className="bg-black border border-white/10 text-white font-mono text-xs">
                    <p>VERIFICATION REQUIRED FOR EDIT ACCESS</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            {isEditing && hasUnsavedChanges && (
              <div className="text-xs text-amber-500 flex items-center gap-2 font-mono border border-amber-500/30 px-3 py-1 rounded bg-amber-500/10">
                <HelpCircle className="w-3 h-3" />
                UNSAVED CHANGES DETECTED
              </div>
            )}
          </div>
        </Reveal>

        {/* Profile Card */}
        <Reveal variant="fadeInUp" delay={0.2}>
          <HolographicCard className="p-6 border-primary/30">
            <div className="space-y-6">
              {/* Profile Picture */}
              <div className="flex items-center gap-6">
                <div className="relative group">
                  <Avatar className="w-24 h-24 border-2 border-primary/50 ring-4 ring-primary/10 shadow-[0_0_20px_rgba(0,224,208,0.2)]">
                    <AvatarImage src={userData.profilePicture} />
                    <AvatarFallback className="text-2xl bg-black text-primary font-bebas tracking-widest">
                      {userData.firstName && userData.lastName
                        ? (userData.firstName.charAt(0) + userData.lastName.charAt(0)).toUpperCase()
                        : userData.firstName
                          ? userData.firstName.substring(0, 2).toUpperCase()
                          : userData.username
                            ? userData.username.substring(0, 2).toUpperCase()
                            : userData.email
                              ? userData.email.substring(0, 2).toUpperCase()
                              : "JD"}
                    </AvatarFallback>
                  </Avatar>
                  {isEditing && (
                    <label
                      htmlFor="profile-upload"
                      className="absolute inset-0 flex items-center justify-center bg-black/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer border-2 border-primary"
                    >
                      <Upload className="w-6 h-6 text-primary" />
                    </label>
                  )}
                  <input
                    id="profile-upload"
                    type="file"
                    accept="image/jpeg,image/png,image/gif"
                    className="hidden"
                    onChange={handleImageUpload}
                    disabled={!isEditing}
                  />
                </div>
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2 font-bebas tracking-wide text-white">
                    <Cpu className="w-5 h-5 text-primary" />
                    PERSONAL INFORMATION
                  </h2>
                  {isEditing && (
                    <p className="text-xs text-primary/70 mt-1 font-mono">
                        // CLICK AVATAR TO UPDATE BIOMETRIC ID
                    </p>
                  )}
                </div>
              </div>

              {/* Form Fields */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName" className="text-xs font-mono text-muted-foreground">FIRST NAME</Label>
                  <Input
                    id="firstName"
                    value={userData.firstName}
                    onChange={(e) => setUserData({ ...userData, firstName: e.target.value })}
                    disabled={!isEditing}
                    className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName" className="text-xs font-mono text-muted-foreground">LAST NAME</Label>
                  <Input
                    id="lastName"
                    value={userData.lastName}
                    onChange={(e) => setUserData({ ...userData, lastName: e.target.value })}
                    disabled={!isEditing}
                    className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-xs font-mono text-muted-foreground">EMAIL ADDRESS</Label>
                <Input
                  id="email"
                  type="email"
                  value={userData.email}
                  onChange={(e) => setUserData({ ...userData, email: e.target.value })}
                  disabled={!isEditing}
                  className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone" className="text-xs font-mono text-muted-foreground">PHONE NUMBER</Label>
                <Input
                  id="phone"
                  value={userData.phone}
                  onChange={(e) => setUserData({ ...userData, phone: e.target.value })}
                  disabled={!isEditing}
                  className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                  placeholder="+1 (555) 000-0000"
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company" className="text-xs font-mono text-muted-foreground">COMPANY</Label>
                  <Input
                    id="company"
                    value={userData.company}
                    onChange={(e) => setUserData({ ...userData, company: e.target.value })}
                    disabled={!isEditing}
                    className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                    placeholder="Your company name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role" className="text-xs font-mono text-muted-foreground">ROLE</Label>
                  <Input
                    id="role"
                    value={userData.role}
                    onChange={(e) => setUserData({ ...userData, role: e.target.value })}
                    disabled={!isEditing}
                    className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                    placeholder="Your job title"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio" className="text-xs font-mono text-muted-foreground">BIO</Label>
                <Input
                  id="bio"
                  value={userData.bio}
                  onChange={(e) => setUserData({ ...userData, bio: e.target.value })}
                  disabled={!isEditing}
                  className="bg-black/40 border-white/10 text-white focus:border-primary/50 focus:ring-primary/20 font-mono h-10"
                  placeholder="Tell us about yourself"
                />
              </div>

              {/* Action Buttons */}
              {isEditing && (
                <div className="flex gap-3 pt-4">
                  <Button onClick={handleSave} className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-bebas tracking-wider">
                    SAVE CHANGES
                  </Button>
                  <Button onClick={handleCancel} variant="outline" className="flex-1 border-white/10 text-white hover:bg-white/10 font-mono">
                    CANCEL
                  </Button>
                </div>
              )}
            </div>
          </HolographicCard>
        </Reveal>

        {/* Security Section */}
        <Reveal variant="fadeInUp" delay={0.3}>
          <HolographicCard className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-bebas tracking-wide text-white">
              <Lock className="w-5 h-5 text-primary" />
              SECURITY SETTINGS
            </h2>
            <p className="text-xs text-muted-foreground mb-6 font-mono">
                // MANAGE ENCRYPTION KEYS // PASSWORD PROTOCOLS
            </p>
            <Button
              onClick={async () => {
                try {
                  // Send OTP first
                  await authService.sendChangePasswordOtp({ email: userData.email });
                  sonner.info("OTP Sent", {
                    description: `A verification code was sent to ${userData.email}`,
                  });
                  setShowPasswordOtpDialog(true);
                  setPasswordOtp("");
                  setPasswordOtpError("");
                } catch (err: any) {
                  const cooldownMsg = err?.errors?.cooldown || err?.errors?.message || err?.message;
                  if (cooldownMsg) {
                    sonner.error("Cooldown active", { description: cooldownMsg });
                  } else {
                    sonner.error("Error", { description: err?.message || 'Failed to send OTP' });
                  }
                }
              }}
              variant="outline"
              className="w-full border-white/10 text-white hover:bg-white/10 hover:text-primary hover:border-primary/50 transition-all font-mono"
            >
              CHANGE PASSWORD
            </Button>
          </HolographicCard>
        </Reveal>
      </div>

      {/* OTP Dialog for Profile Edit */}
      <Dialog open={showOtpDialog} onOpenChange={setShowOtpDialog}>
        <DialogContent className="bg-black/90 border-primary/30 text-white backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="font-bebas tracking-wider text-2xl text-primary">SECURITY VERIFICATION</DialogTitle>
            <DialogDescription className="font-mono text-xs text-white/70">
              ENTER THE 6-DIGIT CODE SENT TO YOUR EMAIL TO AUTHORIZE PROFILE CHANGES.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="otp" className="text-xs font-mono text-primary">ONE-TIME PASSWORD</Label>
              <Input
                id="otp"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="bg-black/50 border-white/10 text-center text-2xl tracking-[0.5em] font-mono focus:border-primary/50 focus:ring-primary/20"
                maxLength={6}
                placeholder="000000"
              />
              {otpError && <p className="text-red-500 text-xs font-mono">{otpError}</p>}
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowOtpDialog(false)} className="font-mono text-xs text-white/50 hover:text-white">CANCEL</Button>
            <Button onClick={handleVerifyOtp} className="bg-primary text-primary-foreground hover:bg-primary/90 font-bebas tracking-wider">VERIFY IDENTITY</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* OTP Dialog for Password Change */}
      <Dialog open={showPasswordOtpDialog} onOpenChange={setShowPasswordOtpDialog}>
        <DialogContent className="bg-black/90 border-primary/30 text-white backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="font-bebas tracking-wider text-2xl text-primary">PASSWORD RESET AUTHORIZATION</DialogTitle>
            <DialogDescription className="font-mono text-xs text-white/70">
              ENTER THE 6-DIGIT CODE SENT TO YOUR EMAIL TO PROCEED WITH PASSWORD CHANGE.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="passwordOtp" className="text-xs font-mono text-primary">ONE-TIME PASSWORD</Label>
              <Input
                id="passwordOtp"
                value={passwordOtp}
                onChange={(e) => setPasswordOtp(e.target.value)}
                className="bg-black/50 border-white/10 text-center text-2xl tracking-[0.5em] font-mono focus:border-primary/50 focus:ring-primary/20"
                maxLength={6}
                placeholder="000000"
              />
              {passwordOtpError && <p className="text-red-500 text-xs font-mono">{passwordOtpError}</p>}
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowPasswordOtpDialog(false)} className="font-mono text-xs text-white/50 hover:text-white">CANCEL</Button>
            <Button onClick={handleVerifyPasswordOtp} className="bg-primary text-primary-foreground hover:bg-primary/90 font-bebas tracking-wider">VERIFY & PROCEED</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent className="bg-black/90 border-primary/30 text-white backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="font-bebas tracking-wider text-2xl text-primary">UPDATE CREDENTIALS</DialogTitle>
            <DialogDescription className="font-mono text-xs text-white/70">
              ESTABLISH NEW SECURITY PROTOCOLS.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="newPassword" className="text-xs font-mono text-primary">NEW PASSWORD</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  className="bg-black/50 border-white/10 font-mono focus:border-primary/50 focus:ring-primary/20 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-3 text-white/30 hover:text-primary transition-colors"
                >
                  {showNewPassword ? "HIDE" : "SHOW"}
                </button>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-xs font-mono text-primary">CONFIRM PASSWORD</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  className="bg-black/50 border-white/10 font-mono focus:border-primary/50 focus:ring-primary/20 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-3 text-white/30 hover:text-primary transition-colors"
                >
                  {showConfirmPassword ? "HIDE" : "SHOW"}
                </button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowPasswordDialog(false)} className="font-mono text-xs text-white/50 hover:text-white">CANCEL</Button>
            <Button onClick={handleChangePassword} className="bg-primary text-primary-foreground hover:bg-primary/90 font-bebas tracking-wider">UPDATE PASSWORD</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default UserProfile;
