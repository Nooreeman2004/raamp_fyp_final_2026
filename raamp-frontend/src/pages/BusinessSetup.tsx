import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { MapPin, Building2 } from "lucide-react";

const BusinessSetup = () => {
  const navigate = useNavigate();
  const [businessName, setBusinessName] = useState("Artisan Coffee House");
  const [businessType, setBusinessType] = useState("Restaurant");

  const [categories, setCategories] = useState<string[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [categoriesError, setCategoriesError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetchCategories = async () => {
      setLoadingCategories(true);
      setCategoriesError(null);
      try {
        // Try fetching from API; if not present, this will fail and we fallback
        const res = await fetch('/api/categories');
        if (!mounted) return;
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!Array.isArray(data)) throw new Error('Invalid categories response');
        if (mounted) {
          setCategories(data);
          // If current selection not in the returned list, set to first
          if (data.length > 0 && !data.includes(businessType)) {
            setBusinessType(data[0]);
          }
        }
      } catch (err: any) {
        // Fallback: keep defaults already in UI and show a small error
        if (mounted) setCategoriesError('Could not load categories — using defaults');
      } finally {
        if (mounted) setLoadingCategories(false);
      }
    };

    fetchCategories();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-background">
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

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8 max-w-4xl mx-auto">
          <div>
            <h1 className="text-4xl font-bold mb-2">Hyperlocal Business Setup</h1>
            <p className="text-muted-foreground">
              Define your business location and targeting parameters for hyper-local campaigns
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-primary" />
                Pin Your Location
              </h2>
              
              <div className="aspect-square bg-muted rounded-lg mb-4 relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <MapPin className="w-12 h-12 text-primary mx-auto mb-2 breathing-glow" />
                    <p className="text-sm text-muted-foreground">Interactive Map</p>
                    <p className="text-xs text-muted-foreground mt-1">Click to set your business location</p>
                  </div>
                </div>
                <div className="absolute inset-0 bg-primary/5 animate-pulse"></div>
              </div>

              <p className="text-sm text-muted-foreground">
                Click on the map to set your exact business location. This will be used for geo-targeting campaigns.
              </p>
            </Card>

            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-primary" />
                Business Details
              </h2>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="businessName">Business Name</Label>
                  <Input
                    id="businessName"
                    value={businessName}
                    onChange={(e) => setBusinessName(e.target.value)}
                    className="bg-background/50"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="businessType">Business Type</Label>
                  <Select value={businessType} onValueChange={setBusinessType}>
                    <SelectTrigger className="bg-background/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {loadingCategories ? (
                        <SelectItem value="" disabled>
                          Loading categories...
                        </SelectItem>
                      ) : categories.length > 0 ? (
                        categories.map((c) => (
                          <SelectItem key={c} value={c}>
                            {c}
                          </SelectItem>
                        ))
                      ) : (
                        // Fallback list if no categories returned / fetch failed
                        <>
                          <SelectItem value="Restaurant">Restaurant</SelectItem>
                          <SelectItem value="Retail">Retail Store</SelectItem>
                          <SelectItem value="Services">Professional Services</SelectItem>
                          <SelectItem value="Healthcare">Healthcare</SelectItem>
                          <SelectItem value="Fitness">Fitness & Wellness</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </>
                      )}
                    </SelectContent>
                  </Select>

                  {categoriesError && <p className="text-xs text-destructive mt-1">{categoriesError}</p>}
                </div>

                <Button
                  variant="hero" 
                  className="w-full mt-4"
                  onClick={() => navigate("/profile/brand-settings")}
                >
                  Continue to Brand Alignment
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BusinessSetup;
