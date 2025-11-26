import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { Store, MapPin, Shield, Upload, Palette, FileText, HelpCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import GoogleMap from "@/components/GoogleMap";
import { apiClient } from "@/services/api";
import { authService } from "@/services/authService";
import Breadcrumbs from "@/components/Breadcrumbs";
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges";

const RestaurantProfile = () => {
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [showOtpDialog, setShowOtpDialog] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState("");
  const [loading, setLoading] = useState(true);

  const [restaurantData, setRestaurantData] = useState({
    businessName: "",
    businessType: "",
    location: "",
    theme: "",
    vision: "",
    tagline: "",
    toneOfVoice: "",
    logo: "",
    primaryColor: "#0EA5E9",
    secondaryColor: "#14B8A6",
    latitude: null as number | null,
    longitude: null as number | null,
  });

  const [initialRestaurantData, setInitialRestaurantData] = useState("");

  // Track unsaved changes
  const hasUnsavedChanges = isEditing && JSON.stringify(restaurantData) !== initialRestaurantData;

  useUnsavedChanges({
    hasUnsavedChanges: hasUnsavedChanges,
    message: "You have unsaved changes to your restaurant profile. Are you sure you want to leave?"
  });

  // Load restaurant data from onboarding/backend
  useEffect(() => {
    const loadRestaurantData = async () => {
      try {
        setLoading(true);
        // Fetch onboarding data which includes restaurant info
        const onboardingData: any = await apiClient.get('/profile/onboarding');
        
        if (onboardingData?.connections?.google_business) {
          const googleBusiness = onboardingData.connections.google_business;
          setRestaurantData(prev => ({
            ...prev,
            businessName: googleBusiness.business_name || prev.businessName,
            location: googleBusiness.address || prev.location,
            latitude: googleBusiness.latitude || prev.latitude,
            longitude: googleBusiness.longitude || prev.longitude,
          }));
        }

        // Also check user profile for additional restaurant data
        try {
          const userProfile = await authService.getProfile();
          if (userProfile) {
            setRestaurantData(prev => ({
              ...prev,
              businessName: prev.businessName || userProfile.company || "",
              location: prev.location || "",
            }));
          }
        } catch (e) {
          // Ignore
        }

        // Set initial data for unsaved changes tracking
        setInitialRestaurantData(JSON.stringify(restaurantData));
      } catch (err: any) {
        console.error('Failed to load restaurant data:', err);
        toast({
          title: "Warning",
          description: "Could not load restaurant data. Please complete onboarding first.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    loadRestaurantData();
  }, [toast]);

  const handleEdit = async () => {
    try {
      // Get user email for OTP
      const userProfile = await authService.getProfile();
      if (!userProfile?.email) {
        toast({
          title: "Error",
          description: "Could not find user email",
          variant: "destructive",
        });
        return;
      }

      // Send OTP
      await authService.sendProfileEditOtp({ email: userProfile.email });
      toast({
        title: "OTP Sent",
        description: `A verification code was sent to ${userProfile.email}`,
      });
      setShowOtpDialog(true);
      setOtp("");
      setOtpError("");
    } catch (err: any) {
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
      const userProfile = await authService.getProfile();
      if (!userProfile?.email) {
        setOtpError("Could not find user email");
        return;
      }

      await authService.verifyProfileEditOtp({ email: userProfile.email, code: otp });
      setShowOtpDialog(false);
      setIsEditing(true);
      toast({
        title: "Verified",
        description: "You can now edit your restaurant profile",
      });
    } catch (err: any) {
      setOtpError(err?.message || "Invalid OTP. Please try again.");
    }
  };

  const handleSave = async () => {
    // Validate required fields
    if (!restaurantData.businessName || !restaurantData.businessType || !restaurantData.location || 
        !restaurantData.theme || !restaurantData.vision) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields (marked with *)",
        variant: "destructive",
      });
      return;
    }

    try {
      // TODO: Implement backend endpoint to save restaurant profile
      // For now, just show success
      setInitialRestaurantData(JSON.stringify(restaurantData));
      setIsEditing(false);
      toast({
        title: "Success",
        description: "Restaurant profile updated successfully",
      });
    } catch (err: any) {
      toast({
        title: "Error",
        description: err?.message || "Failed to save restaurant profile",
        variant: "destructive",
      });
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      toast({
        title: "Error",
        description: "File must be less than 2MB",
        variant: "destructive",
      });
      return;
    }

    const url = URL.createObjectURL(file);
    setRestaurantData({ ...restaurantData, logo: url });
    toast({
      title: "Success",
      description: "Logo updated",
    });
  };

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
          { label: 'Restaurant Profile' },
        ]} />
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">Restaurant Profile</h1>
              <p className="text-muted-foreground">
                Manage your restaurant information and brand identity
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
                    <p>You'll need to verify your identity with an OTP to edit your restaurant profile</p>
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

          {/* Business Information */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Store className="w-6 h-6 text-primary" />
              Business Information
            </h2>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="businessName">Business Name <span className="text-destructive">*</span></Label>
                <Input
                  id="businessName"
                  value={restaurantData.businessName}
                  onChange={(e) => setRestaurantData({ ...restaurantData, businessName: e.target.value })}
                  disabled={!isEditing}
                  required
                  className="bg-background/50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="businessType">Business Type <span className="text-destructive">*</span></Label>
                <Input
                  id="businessType"
                  value={restaurantData.businessType}
                  onChange={(e) => setRestaurantData({ ...restaurantData, businessType: e.target.value })}
                  disabled={!isEditing}
                  required
                  className="bg-background/50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location" className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Location <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="location"
                  value={restaurantData.location}
                  onChange={(e) => setRestaurantData({ ...restaurantData, location: e.target.value })}
                  disabled={!isEditing}
                  required
                  className="bg-background/50"
                />
              </div>

              {/* Google Map Display */}
              {restaurantData.latitude && restaurantData.longitude && (
                <div className="space-y-2">
                  <Label>Restaurant Location on Map</Label>
                  <GoogleMap
                    locations={[{
                      lat: restaurantData.latitude,
                      lng: restaurantData.longitude,
                      name: restaurantData.businessName,
                      address: restaurantData.location,
                    }]}
                    center={{ lat: restaurantData.latitude, lng: restaurantData.longitude }}
                    zoom={15}
                    height="300px"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="theme">Restaurant Theme <span className="text-destructive">*</span></Label>
                <Textarea
                  id="theme"
                  value={restaurantData.theme}
                  onChange={(e) => setRestaurantData({ ...restaurantData, theme: e.target.value })}
                  disabled={!isEditing}
                  required
                  className="bg-background/50 min-h-20"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="vision">Restaurant Vision <span className="text-destructive">*</span></Label>
                <Textarea
                  id="vision"
                  value={restaurantData.vision}
                  onChange={(e) => setRestaurantData({ ...restaurantData, vision: e.target.value })}
                  disabled={!isEditing}
                  required
                  className="bg-background/50 min-h-20"
                />
              </div>
            </div>
          </Card>

          {/* Brand Identity */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Palette className="w-6 h-6 text-primary" />
              Brand Identity
            </h2>

            <div className="space-y-6">
              {/* Logo Upload */}
              <div className="space-y-2">
                <Label>Restaurant Logo</Label>
                <div className="flex items-center gap-4">
                  {restaurantData.logo ? (
                    <div className="w-24 h-24 rounded-lg border-2 border-primary/20 overflow-hidden">
                      <img src={restaurantData.logo} alt="Logo" className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div className="w-24 h-24 rounded-lg border-2 border-dashed border-primary/20 flex items-center justify-center bg-muted/50">
                      <Upload className="w-6 h-6 text-muted-foreground" />
                    </div>
                  )}
                  {isEditing && (
                    <div>
                      <input
                        id="logo-upload"
                        type="file"
                        accept="image/jpeg,image/png,image/svg+xml"
                        className="hidden"
                        onChange={handleLogoUpload}
                      />
                      <Button 
                        variant="outline" 
                        onClick={() => document.getElementById('logo-upload')?.click()}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Logo
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              {/* Color Palette */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="primaryColor">Primary Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="primaryColor"
                      type="color"
                      value={restaurantData.primaryColor}
                      onChange={(e) => setRestaurantData({ ...restaurantData, primaryColor: e.target.value })}
                      disabled={!isEditing}
                      className="w-20 h-10 p-1 cursor-pointer"
                    />
                    <Input
                      value={restaurantData.primaryColor}
                      disabled={!isEditing}
                      className="bg-background/50"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secondaryColor">Secondary Color</Label>
                  <div className="flex gap-2">
                    <Input
                      id="secondaryColor"
                      type="color"
                      value={restaurantData.secondaryColor}
                      onChange={(e) => setRestaurantData({ ...restaurantData, secondaryColor: e.target.value })}
                      disabled={!isEditing}
                      className="w-20 h-10 p-1 cursor-pointer"
                    />
                    <Input
                      value={restaurantData.secondaryColor}
                      disabled={!isEditing}
                      className="bg-background/50"
                    />
                  </div>
                </div>
              </div>

              {/* Tagline and Tone */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tagline">Restaurant Tagline</Label>
                  <Input
                    id="tagline"
                    value={restaurantData.tagline}
                    onChange={(e) => setRestaurantData({ ...restaurantData, tagline: e.target.value })}
                    disabled={!isEditing}
                    className="bg-background/50"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="toneOfVoice" className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Tone of Voice
                  </Label>
                  <Input
                    id="toneOfVoice"
                    value={restaurantData.toneOfVoice}
                    onChange={(e) => setRestaurantData({ ...restaurantData, toneOfVoice: e.target.value })}
                    disabled={!isEditing}
                    className="bg-background/50"
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Action Buttons */}
          {isEditing && (
            <div className="flex gap-3">
              <Button onClick={handleSave} variant="hero" className="flex-1">
                Save Changes
              </Button>
              <Button onClick={handleCancel} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          )}
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
                We've sent a verification code to your registered email
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
    </div>
  );
};

export default RestaurantProfile;
