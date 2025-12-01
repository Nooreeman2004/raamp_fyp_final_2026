import { useState, useRef, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { Palette, Upload, FileText, Type, Sparkles, Loader2, Check, X } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiClient } from "@/services/api";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, hoverLift } from "@/utils/animations";

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const BrandSettings = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Form state
  const [logoUrl, setLogoUrl] = useState("");
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [primaryColor, setPrimaryColor] = useState("#009999");
  const [secondaryColor, setSecondaryColor] = useState("#005377");
  const [toneOfVoice, setToneOfVoice] = useState("Professional, innovative, empowering, slightly futuristic, friendly.");
  const [tagline, setTagline] = useState("");
  const [theme, setTheme] = useState("");
  
  // Loading states
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingSettings, setLoadingSettings] = useState(true);

  // Load existing settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settings: any = await apiClient.get('/brand-alignment/settings');
        if (settings) {
          setLogoUrl(settings.brand_logo_url || "");
          setLogoPreview(settings.brand_logo_url || null);
          setPrimaryColor(settings.primary_color || "#009999");
          setSecondaryColor(settings.secondary_color || "#005377");
          setTagline(settings.tagline || "");
          setToneOfVoice(settings.tone_of_voice || "Professional, innovative, empowering, slightly futuristic, friendly.");
          setTheme(settings.restaurant_theme || "");
        }
      } catch (err: any) {
        // 404 is fine - no settings saved yet
        if (err?.status !== 404) {
          console.error('Failed to load brand settings:', err);
        }
      } finally {
        setLoadingSettings(false);
      }
    };
    loadSettings();
  }, []);

  // Handle logo file selection and upload
  const handleLogoUpload = useCallback(async (file: File) => {
    // Validate file type
    const allowedTypes = ['image/svg+xml', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      toast({ title: 'Invalid file type', description: 'Please upload SVG, PNG, or JPG', variant: 'destructive' });
      return;
    }
    // Validate file size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast({ title: 'File too large', description: 'Maximum file size is 2MB', variant: 'destructive' });
      return;
    }

    setUploadingLogo(true);
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('logo', file);

      const response = await fetch(`${API_BASE}/brand-alignment/upload-logo`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await response.json();
      setLogoUrl(data.logo_url);
      setLogoPreview(data.logo_url);
      toast({ title: 'Logo uploaded', description: 'Your brand logo has been uploaded successfully.' });
    } catch (err: any) {
      toast({ title: 'Upload failed', description: err.message || 'Failed to upload logo', variant: 'destructive' });
    } finally {
      setUploadingLogo(false);
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleLogoUpload(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleLogoUpload(file);
  };

  // Validate all fields before save
  const canSave = logoUrl && primaryColor && secondaryColor && tagline.trim() && toneOfVoice.trim() && theme.trim();

  // Save all settings
  const handleSave = async () => {
    if (!canSave) {
      toast({ title: 'Missing fields', description: 'Please fill in all required fields including logo, tagline, tone of voice, and theme.', variant: 'destructive' });
      return;
    }

    setSaving(true);
    try {
      await apiClient.post('/brand-alignment/save', {
        brand_logo_url: logoUrl,
        primary_color: primaryColor,
        secondary_color: secondaryColor,
        tagline: tagline.trim(),
        tone_of_voice: toneOfVoice.trim(),
        restaurant_theme: theme.trim(),
      });
      toast({ title: 'Saved', description: 'Brand alignment settings saved successfully!' });
      navigate("/dashboard");
    } catch (err: any) {
      toast({ title: 'Save failed', description: err.message || 'Failed to save settings', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    setPrimaryColor("#009999");
    setSecondaryColor("#005377");
    setToneOfVoice("Professional, innovative, empowering, slightly futuristic, friendly.");
    setTagline("");
    setTheme("");
    // Don't reset logo
  };

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b border-primary/10 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <Reveal variant="fadeInDown" duration={0.5} className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center gap-3">
              <motion.img 
                whileHover={{ rotate: 10, scale: 1.1 }}
                src={raampIcon} 
                alt="RAAMP" 
                className="h-10 w-10" 
              />
              <span className="text-xl font-bold">RAAMP</span>
            </Link>
          </div>
        </Reveal>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8 max-w-5xl mx-auto">
          {/* Header */}
          <Reveal variant="blurInUp">
            <div>
              <h1 className="text-4xl font-bold mb-2">Brand Alignment Settings</h1>
              <p className="text-muted-foreground">
                Define your brand identity for AI-generated content consistency
              </p>
            </div>
          </Reveal>

          {/* Staggered Grid */}
          <motion.div 
            className="grid md:grid-cols-2 gap-6"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            {/* Upload Brand Logo */}
            <motion.div variants={fadeInUp}>
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Upload className="w-5 h-5 text-primary" />
                    Upload Brand Logo
                  </h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    Ensure AI-generated visuals match your brand identity
                  </p>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".svg,.png,.jpg,.jpeg"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                  <motion.div 
                    whileHover={{ scale: 1.02, borderColor: "rgba(var(--primary), 0.5)" }}
                    whileTap={{ scale: 0.98 }}
                    className="border-2 border-dashed border-primary/20 rounded-lg p-8 text-center hover:border-primary/40 transition-colors cursor-pointer relative"
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                  >
                    {uploadingLogo ? (
                      <div className="flex flex-col items-center">
                        <Loader2 className="w-12 h-12 text-primary mx-auto mb-3 animate-spin" />
                        <p className="text-sm font-medium">Uploading...</p>
                      </div>
                    ) : logoPreview ? (
                      <div className="flex flex-col items-center">
                        <img src={logoPreview} alt="Brand Logo" className="w-24 h-24 object-contain mb-3 rounded" />
                        <p className="text-sm font-medium text-primary flex items-center gap-1"><Check className="w-4 h-4" /> Logo uploaded</p>
                        <p className="text-xs text-muted-foreground mt-1">Click to replace</p>
                      </div>
                    ) : (
                      <>
                        <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                        <p className="text-sm font-medium mb-1">Click to upload or drag and drop</p>
                        <p className="text-xs text-muted-foreground">SVG, PNG, JPG (max. 2MB)</p>
                      </>
                    )}
                  </motion.div>
                </Card>
              </motion.div>
            </motion.div>

            {/* Define Color Palette */}
            <motion.div variants={fadeInUp}>
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Palette className="w-5 h-5 text-primary" />
                    Define Color Palette
                  </h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    Specify primary and secondary colors for consistency
                  </p>
                  
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="primaryColor">Primary Color</Label>
                      <div className="flex gap-2">
                        <motion.div whileHover={{ scale: 1.1 }}>
                          <Input
                            id="primaryColor"
                            type="color"
                            value={primaryColor}
                            onChange={(e) => setPrimaryColor(e.target.value)}
                            className="w-16 h-10 p-1 bg-background/50 cursor-pointer"
                          />
                        </motion.div>
                        <Input
                          value={primaryColor}
                          onChange={(e) => setPrimaryColor(e.target.value)}
                          className="flex-1 bg-background/50"
                          placeholder="#009999"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="secondaryColor">Secondary Color</Label>
                      <div className="flex gap-2">
                        <motion.div whileHover={{ scale: 1.1 }}>
                          <Input
                            id="secondaryColor"
                            type="color"
                            value={secondaryColor}
                            onChange={(e) => setSecondaryColor(e.target.value)}
                            className="w-16 h-10 p-1 bg-background/50 cursor-pointer"
                          />
                        </motion.div>
                        <Input
                          value={secondaryColor}
                          onChange={(e) => setSecondaryColor(e.target.value)}
                          className="flex-1 bg-background/50"
                          placeholder="#005377"
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            </motion.div>

            {/* Restaurant Tagline */}
            <motion.div variants={fadeInUp}>
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Type className="w-5 h-5 text-primary" />
                    Restaurant Tagline
                  </h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    A memorable phrase that captures your restaurant's essence
                  </p>
                  
                  <div className="space-y-2">
                    <Label htmlFor="tagline">Tagline</Label>
                    <Input
                      id="tagline"
                      value={tagline}
                      onChange={(e) => setTagline(e.target.value)}
                      className="bg-background/50"
                      placeholder="e.g., Where flavor meets tradition"
                      maxLength={100}
                    />
                    <p className="text-xs text-muted-foreground">{tagline.length}/100 characters</p>
                  </div>
                </Card>
              </motion.div>
            </motion.div>

            {/* Set Tone of Voice */}
            <motion.div variants={fadeInUp}>
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    Set Tone of Voice
                  </h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    Guide AI to write copy that sounds like your brand
                  </p>
                  
                  <Textarea
                    value={toneOfVoice}
                    onChange={(e) => setToneOfVoice(e.target.value)}
                    className="min-h-32 bg-background/50"
                    placeholder="e.g., Professional, innovative, empowering, slightly futuristic, friendly."
                  />
                </Card>
              </motion.div>
            </motion.div>

            {/* Restaurant Theme */}
            <motion.div variants={fadeInUp} className="md:col-span-2">
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" />
                    Restaurant Theme
                  </h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    Describe the ambiance, style, and atmosphere of your restaurant
                  </p>
                  
                  <div className="space-y-2">
                    <Label htmlFor="theme">Theme</Label>
                    <Textarea
                      id="theme"
                      value={theme}
                      onChange={(e) => setTheme(e.target.value)}
                      className="min-h-24 bg-background/50"
                      placeholder="e.g., Modern rustic with warm lighting, cozy atmosphere, farm-to-table aesthetic"
                    />
                  </div>
                </Card>
              </motion.div>
            </motion.div>
          </motion.div>

          {/* Action Buttons */}
          <Reveal variant="fadeInUp" delay={0.6}>
            <div className="flex justify-between items-center gap-3">
              <p className="text-sm text-muted-foreground">
                {!canSave && <span className="text-destructive">* All fields are required including logo upload</span>}
              </p>
              <div className="flex gap-3">
                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Button variant="outline" onClick={resetToDefaults}>Reset to Defaults</Button>
                </motion.div>
                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Button 
                    variant="hero" 
                    size="lg"
                    onClick={handleSave}
                    disabled={!canSave || saving}
                  >
                    {saving ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Complete Setup & Go to Dashboard'
                    )}
                  </Button>
                </motion.div>
              </div>
            </div>
          </Reveal>
        </div>
      </main>
    </div>
  );
};

export default BrandSettings;