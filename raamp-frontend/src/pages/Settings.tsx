import { Link } from "react-router-dom";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  User,
  Building2,
  Palette,
  ChevronRight,
  Bell,
  Link2,
  Target,
  Settings as SettingsIcon,
  MessageSquare,
  CreditCard,
} from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

interface SettingsCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
}

const SettingsCard = ({ title, description, icon, href }: SettingsCardProps) => (
  <motion.div variants={fadeInUp}>
    <Link to={href}>
      <motion.div
        variants={hoverScale}
        initial="rest"
        whileHover="hover"
        whileTap="tap"
      >
        <Card className="p-5 bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all cursor-pointer group">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
              {icon}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold group-hover:text-primary transition-colors font-heading font-semibold text-lg">{title}</h3>
              <p className="text-sm text-muted-foreground truncate font-mono">{description}</p>
            </div>
            <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all flex-shrink-0" />
          </div>
        </Card>
      </motion.div>
    </Link>
  </motion.div>
);

const Settings = () => {
  const settingsModules = [
    {
      title: "Edit User Profile",
      description: "Personal details, contact info, and bio",
      icon: <User className="w-5 h-5 text-primary" />,
      href: "/profile/user",
    },
    {
      title: "Edit Business Details",
      description: "Business location and targeting parameters",
      icon: <Building2 className="w-5 h-5 text-primary" />,
      href: "/profile/business-setup",
    },
    {
      title: "Business Specialties",
      description: "Set keywords for enhanced trend detection",
      icon: <Target className="w-5 h-5 text-primary" />,
      href: "/settings/business-specialties",
    },
    {
      title: "Brand Settings",
      description: "Logo, colors, tagline, and tone of voice",
      icon: <Palette className="w-5 h-5 text-primary" />,
      href: "/profile/brand-settings",
    },
    {
      title: "Notification Preferences",
      description: "Email, push, and SMS notification settings",
      icon: <Bell className="w-5 h-5 text-primary" />,
      href: "/settings/notifications",
    },
    {
      title: "Auto Replies",
      description: "Enable review-only or hybrid auto replies (FB/IG)",
      icon: <MessageSquare className="w-5 h-5 text-primary" />,
      href: "/settings/auto-replies",
    },
    {
      title: "Integrations",
      description: "Meta, Google, and API connections",
      icon: <Link2 className="w-5 h-5 text-primary" />,
      href: "/settings/integrations",
    },
    {
      title: "Billing & Payments",
      description: "Subscription plan, credits, and payment history",
      icon: <CreditCard className="w-5 h-5 text-primary" />,
      href: "/billing",
    },
  ];

  return (
    <Layout breadcrumbItems={[{ label: "Settings" }]}>
      <motion.div
        className="space-y-6 max-w-3xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
              <SettingsIcon className="w-7 h-7 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold font-heading font-semibold">
                <BlurText text="Settings" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                Manage your account, connections, and preferences
              </p>
            </div>
          </div>
        </Reveal>

        {/* Settings Grid */}
        <motion.div
          className="grid gap-3"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {settingsModules.map((module) => (
            <SettingsCard key={module.title} {...module} />
          ))}
        </motion.div>
      </motion.div>
    </Layout>
  );
};

export default Settings;
