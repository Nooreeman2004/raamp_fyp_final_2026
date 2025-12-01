import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Bell, Mail, MessageSquare, Pencil, Save } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { hoverScale } from "@/utils/animations";

const NotificationPreferences = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isEditMode, setIsEditMode] = useState(false);
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    marketingEmails: false,
    campaignAlerts: true,
    performanceReports: true,
    trendAlerts: true,
    billingAlerts: true,
  });

  const handleToggle = (key: keyof typeof settings) => {
    if (!isEditMode) return;
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    // TODO: Save to backend
    toast({
      title: "Preferences Saved",
      description: "Your notification preferences have been updated.",
    });
    setIsEditMode(false);
    navigate("/settings");
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
                <h1 className="text-3xl font-bold">Notification Preferences</h1>
                <p className="text-muted-foreground">Choose how you want to be notified</p>
              </div>
            </div>
            {!isEditMode && (
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button variant="outline" onClick={() => setIsEditMode(true)}>
                  <Pencil className="w-4 h-4 mr-2" />
                  Edit
                </Button>
              </motion.div>
            )}
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Mail className="w-5 h-5 text-primary" />
              Communication Channels
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="email">Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive updates via email</p>
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
                  <Label htmlFor="push">Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">Browser push notifications</p>
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
                  <Label htmlFor="sms">SMS Notifications</Label>
                  <p className="text-sm text-muted-foreground">Text message alerts</p>
                </div>
                <Switch
                  id="sms"
                  checked={settings.smsNotifications}
                  onCheckedChange={() => handleToggle("smsNotifications")}
                  disabled={!isEditMode}
                />
              </div>
            </div>
          </Card>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.2}>
          <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary" />
              Alert Types
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="campaign">Campaign Alerts</Label>
                  <p className="text-sm text-muted-foreground">Updates on campaign performance</p>
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
                  <Label htmlFor="performance">Performance Reports</Label>
                  <p className="text-sm text-muted-foreground">Weekly and monthly summaries</p>
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
                  <Label htmlFor="trends">Trend Alerts</Label>
                  <p className="text-sm text-muted-foreground">New trending topics in your area</p>
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
                  <Label htmlFor="billing">Billing Alerts</Label>
                  <p className="text-sm text-muted-foreground">Payment and subscription updates</p>
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

        {isEditMode && (
          <Reveal variant="fadeInUp" delay={0.3}>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setIsEditMode(false)}>Cancel</Button>
              <Button onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                Save Preferences
              </Button>
            </div>
          </Reveal>
        )}
      </motion.div>
    </Layout>
  );
};

export default NotificationPreferences;
