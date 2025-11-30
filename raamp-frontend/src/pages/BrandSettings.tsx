import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { Palette, Upload, FileText, Type, Sparkles } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, hoverLift } from "@/utils/animations";

const BrandSettings = () => {
  const navigate = useNavigate();
  const [toneOfVoice, setToneOfVoice] = useState("Professional, innovative, empowering, slightly futuristic, friendly.");
  const [tagline, setTagline] = useState("");
  const [theme, setTheme] = useState("");

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
                  
                  <motion.div 
                    whileHover={{ scale: 1.02, borderColor: "rgba(var(--primary), 0.5)" }}
                    whileTap={{ scale: 0.98 }}
                    className="border-2 border-dashed border-primary/20 rounded-lg p-8 text-center hover:border-primary/40 transition-colors cursor-pointer"
                  >
                    <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-sm font-medium mb-1">Click to upload or drag and drop</p>
                    <p className="text-xs text-muted-foreground">SVG, PNG, JPG (max. 2MB)</p>
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
                            defaultValue="#009999"
                            className="w-16 h-10 p-1 bg-background/50 cursor-pointer"
                          />
                        </motion.div>
                        <Input
                          value="#009999"
                          className="flex-1 bg-background/50"
                          readOnly
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
                            defaultValue="#005377"
                            className="w-16 h-10 p-1 bg-background/50 cursor-pointer"
                          />
                        </motion.div>
                        <Input
                          value="#005377"
                          className="flex-1 bg-background/50"
                          readOnly
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
            <div className="flex justify-end gap-3">
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button variant="outline">Reset to Defaults</Button>
              </motion.div>
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button 
                  variant="hero" 
                  size="lg"
                  onClick={() => navigate("/dashboard")}
                >
                  Complete Setup & Go to Dashboard
                </Button>
              </motion.div>
            </div>
          </Reveal>
        </div>
      </main>
    </div>
  );
};

export default BrandSettings;