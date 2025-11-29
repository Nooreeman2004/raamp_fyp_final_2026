import { useState } from "react";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { User, Lock, Smartphone, Shield } from "lucide-react";

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
          <div>
            <h1 className="text-4xl font-bold mb-2">Profile Hub</h1>
            <p className="text-muted-foreground">
              Manage your personal details, security settings, and account preferences
            </p>
          </div>

          {/* Edit Profile */}
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
                <Button variant="hero" className="flex-1">
                  Save Changes
                </Button>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="flex-1">
                      <Lock className="w-4 h-4 mr-2" />
                      Change Password
                    </Button>
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
                      <Button variant="hero" className="w-full">Update Password</Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </Card>

          {/* Security Settings */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Shield className="w-6 h-6 text-primary" />
              Security Settings
            </h2>

            <div className="space-y-4">
              <div className="p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold">Two-Factor Authentication</h3>
                  <Button variant="outline" size="sm">Enable</Button>
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
                  <div className="h-full bg-primary" style={{ width: '80%' }}></div>
                </div>
              </div>
            </div>
          </Card>

          {/* Managed Devices */}
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
                <div key={idx} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                  <div>
                    <p className="font-medium">{item.device}</p>
                    <p className="text-sm text-muted-foreground">{item.location} • {item.lastActive}</p>
                  </div>
                  <Button variant="ghost" size="sm">Remove</Button>
                </div>
              ))}
            </div>
          </Card>

          {/* Additional Profile Links */}
          <div className="grid md:grid-cols-3 gap-4">
            <Link to="/profile/business-setup">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all cursor-pointer h-full">
                <h3 className="font-bold mb-2">Hyperlocal Business Setup</h3>
                <p className="text-sm text-muted-foreground">Configure your business location and targeting</p>
              </Card>
            </Link>
            <Link to="/profile/brand-settings">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all cursor-pointer h-full">
                <h3 className="font-bold mb-2">Brand Alignment Settings</h3>
                <p className="text-sm text-muted-foreground">Define your brand voice and visual identity</p>
              </Card>
            </Link>
            <Link to="/profile/onboarding">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all cursor-pointer h-full">
                <h3 className="font-bold mb-2">Ecosystem Integration</h3>
                <p className="text-sm text-muted-foreground">Connect your marketing platforms</p>
              </Card>
            </Link>
          </div>
      </div>
    </Layout>
  );
};

export default ProfileHub;
