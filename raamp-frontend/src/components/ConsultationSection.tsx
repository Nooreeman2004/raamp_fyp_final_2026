import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const ConsultationSection = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    company: "",
  });
  const [errors, setErrors] = useState({
    firstName: false,
    lastName: false,
    email: false,
    company: false,
  });

  const validateForm = () => {
    const newErrors = {
      firstName: !formData.firstName.trim(),
      lastName: !formData.lastName.trim(),
      email: !formData.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email),
      company: !formData.company.trim(),
    };
    setErrors(newErrors);
    return !Object.values(newErrors).some(error => error);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // TODO: Integrate with backend email service
    console.log("Form submitted:", formData);
    
    toast({
      title: "Consultation Booked!",
      description: "We'll contact you shortly to schedule your free consultation.",
    });

    // Reset form
    setFormData({ firstName: "", lastName: "", email: "", company: "" });
    setErrors({ firstName: false, lastName: false, email: false, company: false });
  };

  return (
    <section id="consultation" className="relative py-24 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-card to-background">
        <div className="absolute inset-0 opacity-20" 
             style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, hsl(var(--glow-primary) / 0.15), transparent 70%)' }} 
        />
      </div>

      <div className="container relative z-10 mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <Card className="p-8 md:p-12 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
            <div className="text-center mb-8">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                Book Your Free Consultation
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Ready to revolutionize your marketing? Get in touch with our team and discover how RAAMP can transform your business.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="firstName" className="text-foreground">First Name*</Label>
                  <Input
                    id="firstName"
                    placeholder="First Name*"
                    value={formData.firstName}
                    onChange={(e) => {
                      setFormData({ ...formData, firstName: e.target.value });
                      setErrors({ ...errors, firstName: false });
                    }}
                    className={`bg-background/50 ${errors.firstName ? 'border-destructive' : ''}`}
                  />
                  {errors.firstName && (
                    <p className="text-destructive text-sm">Please complete this required field.</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lastName" className="text-foreground">Last Name*</Label>
                  <Input
                    id="lastName"
                    placeholder="Last Name*"
                    value={formData.lastName}
                    onChange={(e) => {
                      setFormData({ ...formData, lastName: e.target.value });
                      setErrors({ ...errors, lastName: false });
                    }}
                    className={`bg-background/50 ${errors.lastName ? 'border-destructive' : ''}`}
                  />
                  {errors.lastName && (
                    <p className="text-destructive text-sm">Please complete this required field.</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-foreground">Business Email*</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Business Email*"
                  value={formData.email}
                  onChange={(e) => {
                    setFormData({ ...formData, email: e.target.value });
                    setErrors({ ...errors, email: false });
                  }}
                  className={`bg-background/50 ${errors.email ? 'border-destructive' : ''}`}
                />
                {errors.email && (
                  <p className="text-destructive text-sm">Please complete this required field.</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="company" className="text-foreground">Company Name*</Label>
                <Input
                  id="company"
                  placeholder="Company Name*"
                  value={formData.company}
                  onChange={(e) => {
                    setFormData({ ...formData, company: e.target.value });
                    setErrors({ ...errors, company: false });
                  }}
                  className={`bg-background/50 ${errors.company ? 'border-destructive' : ''}`}
                />
                {errors.company && (
                  <p className="text-destructive text-sm">Please complete this required field.</p>
                )}
              </div>

              <div className="flex justify-center pt-4">
                <Button type="submit" variant="heroCta" size="lg" className="min-w-[200px]">
                  Submit
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>

      {/* Decorative bottom line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
    </section>
  );
};

export default ConsultationSection;
