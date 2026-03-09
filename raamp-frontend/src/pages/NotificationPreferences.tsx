import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Bell, Mail, MessageSquare, Pencil, Save, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { authService } from "@/services/authService";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { PasswordVerificationDialog } from "@/components/PasswordVerificationDialog";
import { Shield } from "lucide-react";

interface NotificationSettings {
  emailNotifications: boolean;
  pushNotifications: boolean;
  smsNotifications: boolean;
  marketingEmails: boolean;
  campaignAlerts: boolean;
  performanceReports: boolean;
  trendAlerts: boolean;
  billingAlerts: boolean;
}

const NotificationPreferences = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isEditMode, setIsEditMode] = useState(false);
  const [showPasswordGate, setShowPasswordGate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<NotificationSettings>({
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    marketingEmails: false,
    campaignAlerts: true,
    performanceReports: true,
    trendAlerts: true,
    billingAlerts: true,
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await authService.getNotificationSettings();
      if (res) {
        setSettings({
          emailNotifications: res.email_alerts,
          pushNotifications: res.push_notifications,
          smsNotifications: res.sms_alerts,
          marketingEmails: res.marketing_alerts,
          campaignAlerts: res.campaign_alerts ?? true,
          performanceReports: res.performance_alerts ?? true,
          trendAlerts: res.trend_alerts ?? true,
          billingAlerts: res.billing_alerts ?? true,
        });
      }
    } catch (error) {
      console.error("Failed to fetch settings", error);
      // Fallback to defaults or show error
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (key: keyof NotificationSettings) => {
    if (!isEditMode) return;
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        email_alerts: settings.emailNotifications,
        push_notifications: settings.pushNotifications,
        sms_alerts: settings.smsNotifications,
        marketing_alerts: settings.marketingEmails,
        campaign_alerts: settings.campaignAlerts,
        performance_alerts: settings.performanceReports,
        trend_alerts: settings.trendAlerts,
        billing_alerts: settings.billingAlerts,
      };

      await authService.updateNotificationSettings(payload);

      toast({
        title: "Preferences Saved",
        description: "Your notification preferences have been updated.",
      });
      setIsEditMode(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save preferences. Please try again.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Notification Preferences" }]}>
      <motion.div
        className="space-y-6 max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                <Bell className="w-7 h-7 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold font-bebas tracking-wide">
                  <BlurText text="Notification Preferences" />
                </h1>
                <p className="text-muted-foreground font-mono text-sm">Choose how you want to be notified</p>
              </div>
            </div>
            {!isEditMode && !loading && (
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordGate(true)}
                  className="font-mono text-xs gap-2 border-primary/30 hover:bg-primary/5"
                >
                  <Shield className="w-4 h-4" />
                  Unlock to Edit
                </Button>
              </motion.div>
            )}
          </div>
        </Reveal>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <Reveal variant="fadeInUp" delay={0.1}>
              <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 font-bebas tracking-wide">
                  <Mail className="w-5 h-5 text-primary" />
                  Communication Channels
                </h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="email" className="font-mono text-sm">Email Notifications</Label>
                      <p className="text-sm text-muted-foreground font-mono">Receive updates via email</p>
                    </div>
                    <Switch
                      id="email"
                      checked={settings.emailNotifications}
                      onCheckedChange={() => handleToggle("emailNotifications")}
                      disabled={!isEditMode}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="push" className="font-mono text-sm">Push Notifications</Label>
                      <p className="text-sm text-muted-foreground font-mono">Browser push notifications</p>
                    </div>
                    <Switch
                      id="push"
                      checked={settings.pushNotifications}
                      onCheckedChange={() => handleToggle("pushNotifications")}
                      disabled={!isEditMode}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="sms" className="font-mono text-sm">SMS Notifications</Label>
                      <p className="text-sm text-muted-foreground font-mono">Text message alerts</p>
                    </div>
                    <Switch
                      id="sms"
                      checked={settings.smsNotifications}
                      onCheckedChange={() => handleToggle("smsNotifications")}
                      disabled={!isEditMode}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="marketing" className="font-mono text-sm">Marketing Emails</Label>
                      <p className="text-sm text-muted-foreground font-mono">Function update and promo emails</p>
                    </div>
                    <Switch
                      id="marketing"
                      checked={settings.marketingEmails}
                      onCheckedChange={() => handleToggle("marketingEmails")}
                      disabled={!isEditMode}
                    />
                  </div>
                </div>
              </Card>
            </Reveal>

            <Reveal variant="fadeInUp" delay={0.2}>
              <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 font-bebas tracking-wide">
                  <MessageSquare className="w-5 h-5 text-primary" />
                  Alert Types
                </h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="campaign" className="font-mono text-sm">Campaign Alerts</Label>
                      <p className="text-sm text-muted-foreground font-mono">Updates on campaign performance</p>
                    </div>
                    <Switch
                      id="campaign"
                      checked={settings.campaignAlerts}
                      onCheckedChange={() => handleToggle("campaignAlerts")}
                      disabled={!isEditMode}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="performance" className="font-mono text-sm">Performance Reports</Label>
                      <p className="text-sm text-muted-foreground font-mono">Weekly and monthly summaries</p>
                    </div>
                    <Switch
                      id="performance"
                      checked={settings.performanceReports}
                      onCheckedChange={() => handleToggle("performanceReports")}
                      disabled={!isEditMode}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="trends" className="font-mono text-sm">Trend Alerts</Label>
                      <p className="text-sm text-muted-foreground font-mono">New trending topics in your area</p>
                    </div>
                    <Switch
                      id="trends"
                      checked={settings.trendAlerts}
                      onCheckedChange={() => handleToggle("trendAlerts")}
                      disabled={!isEditMode}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="billing" className="font-mono text-sm">Billing Alerts</Label>
                      <p className="text-sm text-muted-foreground font-mono">Payment and subscription updates</p>
                    </div>
                    <Switch
                      id="billing"
                      checked={settings.billingAlerts}
                      onCheckedChange={() => handleToggle("billingAlerts")}
                      disabled={!isEditMode}
                    />
                  </div>
                </div>
              </Card>
            </Reveal>
          </>
        )}

        {isEditMode && (
          <Reveal variant="fadeInUp" delay={0.3}>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setIsEditMode(false)} className="font-mono text-xs" disabled={saving}>Cancel</Button>
              <Button onClick={handleSave} className="font-mono text-xs" disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Preferences
                  </>
                )}
              </Button>
            </div>
          </Reveal>
        )}
        {/* Password Gate Dialog */}
        <PasswordVerificationDialog
          isOpen={showPasswordGate}
          onClose={() => setShowPasswordGate(false)}
          onVerified={() => {
            setShowPasswordGate(false);
            setIsEditMode(true);
            toast({
              title: "Verified",
              description: "You can now edit your notification preferences.",
            });
          }}
        />
      </motion.div>
    </Layout>
  );
};

export default NotificationPreferences;
