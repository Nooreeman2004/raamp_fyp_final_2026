import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { User, Lock, Smartphone, Shield } from "lucide-react";
import { toast } from "sonner";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, hoverLift } from "@/utils/animations";

const ProfileHub = () => {
  const [firstName, setFirstName] = useState("Jane");
  const [lastName, setLastName] = useState("Doe");
  const [email] = useState("jane.doe@raamp.com");
  const [phone, setPhone] = useState("+1 (555) 123-4567");
  const [company, setCompany] = useState("Acme Marketing Solutions");
  const [role, setRole] = useState("Head of Digital Marketing");
  const [bio, setBio] = useState("A dedicated digital marketing professional with over 10 years of experience, passionate about leveraging AI to optimize campaign performance and drive ROI.");

  return (
    <Layout>
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div>
            <h1 className="text-4xl font-bold mb-2">Profile Hub</h1>
            <p className="text-muted-foreground">
              Manage your personal details, security settings, and account preferences
            </p>
          </div>
        </Reveal>

        {/* Staggered Content Sections */}
        <motion.div
          className="space-y-8"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {/* Edit Profile */}
          <motion.div variants={fadeInUp}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <User className="w-6 h-6 text-primary" />
                Manage Profile
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Manage your personal details and account settings
              </p>

              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="bg-background/50"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    value={email}
                    disabled
                    className="bg-muted/50"
                  />
                  <p className="text-xs text-muted-foreground">Email address cannot be changed</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="bg-background/50"
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Role</Label>
                    <Input
                      id="role"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="bg-background/50"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea
                    id="bio"
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    className="bg-background/50 min-h-24"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <motion.div className="flex-1" variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button
                      variant="hero"
                      className="w-full"
                      onClick={() => toast.success("Profile updated successfully")}
                    >
                      Save Changes
                    </Button>
                  </motion.div>

                  <Dialog>
                    <DialogTrigger asChild>
                      <motion.div className="flex-1" variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                        <Button variant="outline" className="w-full">
                          <Lock className="w-4 h-4 mr-2" />
                          Change Password
                        </Button>
                      </motion.div>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Change Password</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="currentPassword">Current Password</Label>
                          <Input id="currentPassword" type="password" className="bg-background/50" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="newPassword">New Password</Label>
                          <Input id="newPassword" type="password" className="bg-background/50" />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="confirmPassword">Confirm New Password</Label>
                          <Input id="confirmPassword" type="password" className="bg-background/50" />
                        </div>
                        <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                          <Button
                            variant="hero"
                            className="w-full"
                            onClick={() => toast.success("Password updated successfully")}
                          >
                            Update Password
                          </Button>
                        </motion.div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Security Settings */}
          <motion.div variants={fadeInUp}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Shield className="w-6 h-6 text-primary" />
                Security Settings
              </h2>

              <div className="space-y-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold">Two-Factor Authentication</h3>
                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                      <Button variant="outline" size="sm">Enable</Button>
                    </motion.div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Add an extra layer of security to your account
                  </p>
                </div>

                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold">Password Strength</h3>
                    <span className="text-sm font-medium text-primary">Strong</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: '80%' }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className="h-full bg-primary"
                    />
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Managed Devices */}
          <motion.div variants={fadeInUp}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Smartphone className="w-6 h-6 text-primary" />
                Managed Devices
              </h2>

              <div className="space-y-3">
                {[
                  { device: "MacBook Pro", location: "San Francisco, CA", lastActive: "Active now" },
                  { device: "iPhone 14", location: "San Francisco, CA", lastActive: "2 hours ago" },
                  { device: "iPad Pro", location: "San Francisco, CA", lastActive: "1 day ago" }
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    whileHover={{ x: 5 }}
                    className="flex items-center justify-between p-4 bg-muted/50 rounded-lg transition-transform"
                  >
                    <div>
                      <p className="font-medium">{item.device}</p>
                      <p className="text-sm text-muted-foreground">{item.location} • {item.lastActive}</p>
                    </div>
                    <Button variant="ghost" size="sm" className="hover:text-destructive">Remove</Button>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Additional Profile Links */}
          <motion.div
            className="grid md:grid-cols-3 gap-4"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {[
              { link: "/profile/business-setup", title: "Hyperlocal Business Setup", desc: "Configure your business location and targeting" },
              { link: "/profile/brand-settings", title: "Brand Alignment Settings", desc: "Define your brand voice and visual identity" },
              { link: "/profile/onboarding", title: "Ecosystem Integration", desc: "Connect your marketing platforms" }
            ].map((item, idx) => (
              <motion.div key={idx} variants={fadeInUp}>
                <Link to={item.link}>
                  <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                    <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-colors cursor-pointer h-full">
                      <h3 className="font-bold mb-2">{item.title}</h3>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </Card>
                  </motion.div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </Layout>
  );
};

export default ProfileHub;