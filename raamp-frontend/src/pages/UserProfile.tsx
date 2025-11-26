import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { User, Eye, EyeOff, Upload, Lock, Shield, HelpCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";
import Breadcrumbs from "@/components/Breadcrumbs";
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges";
import ConfirmationDialog from "@/components/ConfirmationDialog";

const UserProfile = () => {
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [showOtpDialog, setShowOtpDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showPasswordOtpDialog, setShowPasswordOtpDialog] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState("");
  const [passwordOtp, setPasswordOtp] = useState("");
  const [passwordOtpError, setPasswordOtpError] = useState("");
  
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [userData, setUserData] = useState<any>({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    profilePicture: "",
    username: "",
  });

  const [initialUserData, setInitialUserData] = useState("");

  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  // Track unsaved changes
  const hasUnsavedChanges = isEditing && JSON.stringify({
    firstName: userData.firstName,
    lastName: userData.lastName,
    phone: userData.phone,
  }) !== initialUserData;

  useUnsavedChanges({
    hasUnsavedChanges: hasUnsavedChanges,
    message: "You have unsaved changes to your profile. Are you sure you want to leave?"
  });

  const handleEdit = async () => {
    // Trigger OTP via backend, then show OTP dialog. Only enable editing after verification.
    setOtp("");
    setOtpError("");
    try {
      await authService.sendProfileEditOtp({ email: userData.email });
      toast({ title: "OTP Sent", description: `A verification code was sent to ${userData.email}` });
      setShowOtpDialog(true);
    } catch (err: any) {
      // If server returned structured errors (like cooldown), show them clearly
      const cooldownMsg = err?.errors?.cooldown || err?.errors?.message || err?.message;
      if (cooldownMsg) {
        toast({ title: "Cooldown active", description: cooldownMsg, variant: 'destructive' });
      } else {
        toast({ title: "Error", description: err?.message || 'Failed to send OTP', variant: 'destructive' });
      }
    }
  };

  const handleVerifyOtp = async () => {
    setOtpError("");
    try {
      await authService.verifyProfileEditOtp({ email: userData.email, code: otp });
      setShowOtpDialog(false);
      setIsEditing(true);
      toast({ title: "Verified", description: "You can now edit your profile" });
    } catch (err: any) {
      setOtpError(err?.message || "Invalid OTP. Please try again.");
    }
  };

  const handleSave = async () => {
    // Map frontend fields to backend update fields
    const payload = {
      first_name: userData.firstName,
      last_name: userData.lastName,
      phone_number: userData.phone,
      // add other fields as needed (company, role, bio)
    };

    try {
      const resp = await authService.updateProfile(payload);
      setIsEditing(false);
      // Update local state and localStorage
      const updated = resp.user;
      const updatedData = {
        firstName: updated.first_name || userData.firstName,
        lastName: updated.last_name || userData.lastName,
        email: updated.email || userData.email,
        phone: updated.phone_number || userData.phone,
        profilePicture: updated.profile_picture || userData.profilePicture,
        username: updated.username || userData.username,
      };
      setUserData(updatedData);
      setInitialUserData(JSON.stringify({
        firstName: updatedData.firstName,
        lastName: updatedData.lastName,
        phone: updatedData.phone,
      }));
      try { localStorage.setItem('user', JSON.stringify(resp.user)); } catch {}
      toast({ 
        title: "Success", 
        description: "Profile updated successfully",
      });
    } catch (err: any) {
      toast({ title: "Error", description: err?.message || 'Failed to save profile', variant: 'destructive' });
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

    // OTP verified, show password change dialog
    setShowPasswordOtpDialog(false);
    setShowPasswordDialog(true);
  };

  const handleChangePassword = () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast({ title: "Error", description: "Passwords do not match", variant: "destructive" });
      return;
    }

    if (passwordData.newPassword.length < 8) {
      toast({ title: "Error", description: "Password must be at least 8 characters", variant: "destructive" });
      return;
    }

    (async () => {
      try {
        const resp = await authService.changePassword({
          otp_code: passwordOtp,
          new_password: passwordData.newPassword,
          confirm_password: passwordData.confirmPassword,
        });

        toast({ title: "Success", description: resp.message || "Password changed successfully" });
        setShowPasswordDialog(false);
        setShowPasswordOtpDialog(false);
        setPasswordData({ currentPassword: "", newPassword: "", confirmPassword: "" });
        setPasswordOtp("");
      } catch (err: any) {
        const msg = err?.message || (err?.errors ? JSON.stringify(err.errors) : 'Failed to change password');
        toast({ title: "Error", description: msg, variant: "destructive" });
      }
    })();
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "Error",
        description: "File must be less than 5MB",
        variant: "destructive",
      });
      return;
    }

    try {
      // Import storage service dynamically
      const { uploadProfilePicture } = await import('@/services/storageService');
      
      toast({
        title: "Uploading...",
        description: "Please wait while we upload your profile picture",
      });

      const downloadURL = await uploadProfilePicture(file, userData.email || userData.username);
      
      // Update profile with new picture URL via backend
      const resp = await authService.updateProfile({
        ...userData,
        profile_picture: downloadURL,
      } as any);
      
      setUserData({ ...userData, profilePicture: downloadURL });
      toast({
        title: "Success",
        description: "Profile picture updated successfully",
      });
    } catch (err: any) {
      toast({
        title: "Error",
        description: err?.message || "Failed to upload profile picture",
        variant: "destructive",
      });
    }
  };

  // Load real user profile on mount
  useEffect(() => {
    (async () => {
      try {
        const u = await authService.getProfile();
        if (u) {
          const data = {
            firstName: (u.first_name as string) || u.username || '',
            lastName: (u.last_name as string) || '',
            email: u.email || '',
            phone: (u.phone_number as string) || '',
            profilePicture: (u.profile_picture as string) || '',
            username: u.username || '',
          };
          setUserData(data);
          setInitialUserData(JSON.stringify({
            firstName: data.firstName,
            lastName: data.lastName,
            phone: data.phone,
          }));
        }
      } catch (err) {
        // ignore - user not authenticated or endpoint missing
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <nav className="border-b border-primary/10 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center gap-3">
              <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
              <span className="text-xl font-bold">RAAMP</span>
            </Link>
          </div>
        </div>
      </nav>

      {/* Breadcrumbs */}
      <div className="container mx-auto px-4 py-4">
        <Breadcrumbs items={[
          { label: 'Home', href: '/dashboard' },
          { label: 'Profile', href: '/profile' },
          { label: 'User Profile' },
        ]} />
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">User Profile</h1>
              <p className="text-muted-foreground">
                Manage your personal information and security settings
              </p>
            </div>
            {!isEditing && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button onClick={handleEdit} variant="hero">
                      <Shield className="w-4 h-4 mr-2" />
                      Edit Profile
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>You'll need to verify your identity with an OTP to edit your profile</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            {isEditing && hasUnsavedChanges && (
              <div className="text-sm text-amber-500 flex items-center gap-2">
                <HelpCircle className="w-4 h-4" />
                You have unsaved changes
              </div>
            )}
          </div>

          {/* Profile Card */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <div className="space-y-6">
              {/* Profile Picture */}
              <div className="flex items-center gap-6">
                <div className="relative group">
                  <Avatar className="w-24 h-24">
                    <AvatarImage src={userData.profilePicture} />
                    <AvatarFallback className="text-2xl">
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
                      className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    >
                      <Upload className="w-6 h-6 text-white" />
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
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <User className="w-6 h-6 text-primary" />
                    Personal Information
                  </h2>
                  {isEditing && (
                    <p className="text-sm text-muted-foreground mt-1">
                      Click avatar to change picture
                    </p>
                  )}
                </div>
              </div>

              {/* Form Fields */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    value={userData.firstName}
                    onChange={(e) => setUserData({ ...userData, firstName: e.target.value })}
                    disabled={!isEditing}
                    className="bg-background/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    value={userData.lastName}
                    onChange={(e) => setUserData({ ...userData, lastName: e.target.value })}
                    disabled={!isEditing}
                    className="bg-background/50"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={userData.email}
                  onChange={(e) => setUserData({ ...userData, email: e.target.value })}
                  disabled={!isEditing}
                  className="bg-background/50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  value={userData.phone}
                  onChange={(e) => setUserData({ ...userData, phone: e.target.value })}
                  disabled={!isEditing}
                  className="bg-background/50"
                />
              </div>

              {/* Action Buttons */}
              {isEditing && (
                <div className="flex gap-3 pt-4">
                  <Button onClick={handleSave} variant="hero" className="flex-1">
                    Save Changes
                  </Button>
                  <Button onClick={handleCancel} variant="outline" className="flex-1">
                    Cancel
                  </Button>
                </div>
              )}
            </div>
          </Card>

          {/* Security Section */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Lock className="w-6 h-6 text-primary" />
              Security Settings
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Manage your password and account security
            </p>
            <Button 
              onClick={async () => {
                try {
                  // Send OTP first
                  await authService.sendChangePasswordOtp({ email: userData.email });
                  toast({
                    title: "OTP Sent",
                    description: `A verification code was sent to ${userData.email}`,
                  });
                  setShowPasswordOtpDialog(true);
                  setPasswordOtp("");
                  setPasswordOtpError("");
                } catch (err: any) {
                  const cooldownMsg = err?.errors?.cooldown || err?.errors?.message || err?.message;
                  if (cooldownMsg) {
                    toast({ title: "Cooldown active", description: cooldownMsg, variant: 'destructive' });
                  } else {
                    toast({ title: "Error", description: err?.message || 'Failed to send OTP', variant: 'destructive' });
                  }
                }
              }}
              variant="outline"
              className="w-full md:w-auto"
            >
              <Lock className="w-4 h-4 mr-2" />
              Change Password
            </Button>
          </Card>
        </div>
      </main>

      {/* OTP Verification Dialog */}
      <Dialog open={showOtpDialog} onOpenChange={setShowOtpDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Verify Your Identity</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert>
              <AlertDescription>
                We've sent a verification code to {userData.email}
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Label htmlFor="otp">Enter OTP</Label>
              <Input
                id="otp"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="Enter 6-digit code"
                maxLength={6}
                className="bg-background/50"
              />
              {otpError && (
                <p className="text-sm text-destructive">{otpError}</p>
              )}
            </div>
            <div className="flex gap-3">
              <Button onClick={handleVerifyOtp} variant="hero" className="flex-1">
                Verify OTP
              </Button>
              <Button onClick={() => setShowOtpDialog(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Password Change OTP Dialog */}
      <Dialog open={showPasswordOtpDialog} onOpenChange={setShowPasswordOtpDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Verify Your Identity</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert>
              <AlertDescription>
                We've sent a verification code to {userData.email} to verify your identity before changing your password.
              </AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Label htmlFor="passwordOtp">Enter OTP</Label>
              <Input
                id="passwordOtp"
                value={passwordOtp}
                onChange={(e) => setPasswordOtp(e.target.value)}
                placeholder="Enter 6-digit code"
                maxLength={6}
                className="bg-background/50"
              />
              {passwordOtpError && (
                <p className="text-sm text-destructive">{passwordOtpError}</p>
              )}
            </div>
            <div className="flex gap-3">
              <Button onClick={handleVerifyPasswordOtp} variant="hero" className="flex-1">
                Verify OTP
              </Button>
              <Button onClick={() => setShowPasswordOtpDialog(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert>
              <AlertDescription className="text-xs">
                For security, we recommend using a strong password with at least 8 characters
              </AlertDescription>
            </Alert>


            <div className="space-y-2">
              <Label htmlFor="newPassword">New Password</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  className="bg-background/50 pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm New Password</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  className="bg-background/50 pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleChangePassword} variant="hero" className="flex-1">
                Update Password
              </Button>
              <Button onClick={() => setShowPasswordDialog(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserProfile;
