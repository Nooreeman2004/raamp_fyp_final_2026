import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Target, Plus, X, Loader2, Sparkles, Save, Info, Shield, Lock } from "lucide-react";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { trendService } from "@/services/trendService";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { BlurText } from "@/components/ui/text-reveal";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PasswordVerificationDialog } from "@/components/PasswordVerificationDialog";
import { cn } from "@/lib/utils";

const BusinessSpecialties = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [specialties, setSpecialties] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordGate, setShowPasswordGate] = useState(false);

  // Curated suggestions (can be enhanced later with niche-specific suggestions)
  const suggestions = [
    "bubble tea", "matcha", "vegan", "sushi", "pizza",
    "streetwear", "vintage", "sustainable", "yoga", "crossfit"
  ];

  useEffect(() => {
    fetchSpecialties();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchSpecialties = async () => {
    try {
      setLoading(true);
      const res = await trendService.getBusinessSpecialties();
      if (res.success) {
        setSpecialties(res.specialties || []);
      }
    } catch (error: unknown) {
      console.error("Failed to fetch specialties", error);
      const axiosError = error as { response?: { status?: number } };
      if (axiosError?.response?.status !== 404) {
        toast({
          title: "Error",
          description: "Failed to load business specialties. Using defaults.",
          variant: "destructive",
        });
      }
      // If 404, it just means no specialties set yet (which is fine)
    } finally {
      setLoading(false);
    }
  };

  const handleAddSpecialty = () => {
    const trimmed = inputValue.trim().toLowerCase();

    // Validation
    if (!trimmed) return;

    if (trimmed.length > 50) {
      setError("Specialty must be 50 characters or less");
      return;
    }

    if (specialties.includes(trimmed)) {
      setError("Specialty already added");
      return;
    }

    if (specialties.length >= 10) {
      setError("Maximum 10 specialties allowed");
      return;
    }

    setSpecialties([...specialties, trimmed]);
    setInputValue("");
    setError(null);
  };

  const handleRemoveSpecialty = (specialty: string) => {
    setSpecialties(specialties.filter(s => s !== specialty));
  };

  const handleAddSuggestion = (suggestion: string) => {
    if (specialties.includes(suggestion)) {
      toast({
        title: "Already Added",
        description: `"${suggestion}" is already in your specialties.`,
      });
      return;
    }

    if (specialties.length >= 10) {
      setError("Maximum 10 specialties allowed");
      return;
    }

    setSpecialties([...specialties, suggestion]);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = specialties;
      const res = await trendService.updateBusinessSpecialties(payload);

      if (res.success) {
        toast({
          title: "Specialties Saved",
          description: "Your business specialties have been updated. Trend detection will now focus on these keywords.",
        });
      }
    } catch (error: unknown) {
      console.error("Failed to save specialties", error);
      const axiosError = error as { response?: { data?: { detail?: string } } };
      toast({
        title: "Error",
        description: axiosError?.response?.data?.detail || "Failed to save specialties. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSpecialty();
    }
  };

  if (loading) {
    return (
      <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Business Specialties" }]}>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Business Specialties" }]}>
      <motion.div
        className="space-y-6 max-w-3xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                <Target className="w-7 h-7 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold font-bebas tracking-wide">
                  <BlurText text="Business Specialties" />
                </h1>
                <p className="text-muted-foreground font-mono text-sm">
                  Add keywords to enhance trend detection for your business
                </p>
              </div>
            </div>
            {!isEditing && (
              <Button
                variant="outline"
                onClick={() => setShowPasswordGate(true)}
                className="font-mono text-xs gap-2 border-primary/30 hover:bg-primary/5"
              >
                <Shield className="w-4 h-4" />
                Unlock to Edit
              </Button>
            )}
          </div>
        </Reveal>

        {/* Info Alert */}
        <Reveal variant="fadeInUp" delay={0.1}>
          <Alert className="border-primary/20 bg-primary/5">
            <Info className="h-4 w-4 text-primary" />
            <AlertDescription className="text-sm font-mono">
              <strong className="text-primary">What are specialties?</strong> Keywords that help RAAMP find more relevant trends.
              For example, a restaurant might add "bubble tea", "matcha", or "vegan" to get specialty-specific trend detection
              instead of generic "all" trends.
            </AlertDescription>
          </Alert>
        </Reveal>

        {/* Main Card */}
        <Reveal variant="fadeInUp" delay={0.2}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <div className="space-y-6">
              {/* Current Specialties */}
              <div>
                <label className="text-sm font-semibold font-bebas tracking-wide flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-primary" />
                  Your Specialties ({specialties.length}/10)
                </label>

                {specialties.length > 0 ? (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {specialties.map((specialty) => (
                      <Badge
                        key={specialty}
                        variant="secondary"
                        className="px-3 py-1.5 text-sm font-mono bg-primary/10 text-primary border-primary/20 hover:bg-primary/20 transition-colors"
                      >
                        {specialty}
                        {isEditing && (
                          <button
                            onClick={() => handleRemoveSpecialty(specialty)}
                            className="ml-2 hover:text-red-400 transition-colors"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        )}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground font-mono italic mb-4 p-4 bg-muted/30 rounded-lg border border-dashed">
                    No specialties added yet. Add keywords below to get started.
                  </div>
                )}
              </div>

              {/* Add New Specialty */}
              <div>
                <label className="text-sm font-semibold font-bebas tracking-wide mb-2 block">
                  Add New Specialty
                </label>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    placeholder="e.g., bubble tea, vegan, yoga..."
                    value={inputValue}
                    onChange={(e) => {
                      setInputValue(e.target.value);
                      setError(null);
                    }}
                    onKeyPress={handleKeyPress}
                    maxLength={50}
                    className="font-mono"
                    disabled={specialties.length >= 10}
                  />
                  <Button
                    onClick={handleAddSpecialty}
                    disabled={!inputValue.trim() || specialties.length >= 10 || !isEditing}
                    variant="outline"
                    className="px-4"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                {error && (
                  <p className="text-xs text-red-400 font-mono mt-2">{error}</p>
                )}
                <p className="text-xs text-muted-foreground font-mono mt-2">
                  Max 50 characters per specialty. Automatically converted to lowercase.
                </p>
              </div>

              {/* Suggestions */}
              <div>
                <label className="text-sm font-semibold font-bebas tracking-wide mb-2 block">
                  Quick Suggestions
                </label>
                <div className="flex flex-wrap gap-2">
                  {suggestions
                    .filter(s => !specialties.includes(s))
                    .map((suggestion) => (
                      <Badge
                        key={suggestion}
                        variant="outline"
                        className={cn(
                          "px-3 py-1.5 text-xs font-mono transition-colors",
                          isEditing ? "cursor-pointer hover:bg-primary/10 hover:text-primary hover:border-primary/30" : "opacity-50 cursor-not-allowed"
                        )}
                        onClick={() => isEditing && handleAddSuggestion(suggestion)}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        {suggestion}
                      </Badge>
                    ))}
                </div>
              </div>
            </div>
          </Card>
        </Reveal>

        {/* Save Button */}
        <Reveal variant="fadeInUp" delay={0.3}>
          <div className="flex gap-3 justify-end">
            <Button
              variant="outline"
              onClick={() => window.history.back()}
              className="font-mono"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !isEditing}
              className={cn(
                "bg-primary text-black hover:opacity-90 font-bebas text-lg px-8",
                (!isEditing || saving) && "opacity-50 grayscale cursor-not-allowed"
              )}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  SAVING...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  SAVE CHANGES
                </>
              )}
            </Button>
          </div>
        </Reveal>

        {/* Help Section */}
        <Reveal variant="fadeInUp" delay={0.4}>
          <Card className="p-6 bg-muted/30 border-dashed">
            <h3 className="font-semibold mb-3 font-bebas tracking-wide">Examples by Niche</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-mono">
              <div>
                <p className="text-primary font-bold mb-1">Restaurant:</p>
                <p className="text-muted-foreground">bubble tea, matcha, vegan, sushi, pizza</p>
              </div>
              <div>
                <p className="text-primary font-bold mb-1">Fashion:</p>
                <p className="text-muted-foreground">streetwear, vintage, sustainable, denim</p>
              </div>
              <div>
                <p className="text-primary font-bold mb-1">Fitness:</p>
                <p className="text-muted-foreground">yoga, crossfit, pilates, hiit, strength</p>
              </div>
              <div>
                <p className="text-primary font-bold mb-1">Beauty:</p>
                <p className="text-muted-foreground">skincare, makeup, organic, cruelty-free</p>
              </div>
            </div>
          </Card>
        </Reveal>
        {/* Password Gate Dialog */}
        <PasswordVerificationDialog
          isOpen={showPasswordGate}
          onClose={() => setShowPasswordGate(false)}
          onVerified={() => {
            setShowPasswordGate(false);
            setIsEditing(true);
            toast({
              title: "Verified",
              description: "You can now edit your business specialties.",
            });
          }}
        />
      </motion.div>
    </Layout>
  );
};

export default BusinessSpecialties;
