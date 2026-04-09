import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import { toast as sonner } from "sonner";
import { consultationService } from "@/services/consultationService";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, zoomIn, fadeIn } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

const ConsultationSection = () => {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      sonner.info("Submitting...", {
        description: "Please wait while we process your request.",
      });

      await consultationService.submitConsultation({
        first_name: formData.firstName,
        last_name: formData.lastName,
        business_email: formData.email,
        company_name: formData.company,
      });

      sonner.success("Consultation Booked!", {
        description: "Check your email for confirmation. Our team will contact you within 24-48 hours.",
      });

      // Reset form
      setFormData({ firstName: "", lastName: "", email: "", company: "" });
      setErrors({ firstName: false, lastName: false, email: false, company: false });
    } catch (error: any) {
      // Check if it's a duplicate email error (409 status)
      if (error?.status === 409 || error?.detail?.includes("already been used")) {
        sonner.success("Already Registered! ✓", {
          description: error?.detail || "This email has already been used to book a consultation.",
        });
      } else {
        sonner.error("Error", {
          description: error?.detail || error?.message || "Failed to submit consultation request.",
        });
      }
    }
  };

  return (
    <section id="consultation" className="relative py-24 overflow-hidden">
      {/* Background gradient - Fades in */}
      <motion.div
        variants={fadeIn}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        transition={{ duration: 1.5 }}
        className="absolute inset-0 bg-gradient-to-br from-background via-card to-background"
      >
        <div className="absolute inset-0 opacity-20"
          style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, hsl(var(--glow-primary) / 0.15), transparent 70%)' }}
        />
      </motion.div>

      <div className="container relative z-10 mx-auto px-4">
        <div className="max-w-4xl mx-auto">

          {/* Main Card Entrance: Zoom In */}
          <Reveal variant="zoomIn" duration={0.6}>
            <Card className="p-8 md:p-12 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
              <div className="text-center mb-8">
                <Reveal variant="blurInUp" delay={0.2}>
                  <h2 className="text-4xl md:text-5xl font-bold mb-4 font-heading font-semibold">
                    <BlurText text="Book Your Free Consultation" />
                  </h2>
                </Reveal>
                <Reveal variant="fadeIn" delay={0.3}>
                  <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-mono">
                    Ready to revolutionize your marketing? Get in touch with our team and discover how RAAMP can transform your business.
                  </p>
                </Reveal>
              </div>

              {/* Form with Staggered Inputs */}
              <motion.form
                onSubmit={handleSubmit}
                className="space-y-6"
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {/* Row 1: Names */}
                <motion.div variants={fadeInUp} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="firstName" className="text-foreground font-mono text-sm">First Name*</Label>
                    <Input
                      id="firstName"
                      placeholder="First Name*"
                      value={formData.firstName}
                      onChange={(e) => {
                        setFormData({ ...formData, firstName: e.target.value });
                        setErrors({ ...errors, firstName: false });
                      }}
                      className={`bg-background/50 font-mono ${errors.firstName ? 'border-destructive' : ''}`}
                    />
                    {errors.firstName && (
                      <p className="text-destructive text-sm font-mono">Please complete this required field.</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="lastName" className="text-foreground font-mono text-sm">Last Name*</Label>
                    <Input
                      id="lastName"
                      placeholder="Last Name*"
                      value={formData.lastName}
                      onChange={(e) => {
                        setFormData({ ...formData, lastName: e.target.value });
                        setErrors({ ...errors, lastName: false });
                      }}
                      className={`bg-background/50 font-mono ${errors.lastName ? 'border-destructive' : ''}`}
                    />
                    {errors.lastName && (
                      <p className="text-destructive text-sm font-mono">Please complete this required field.</p>
                    )}
                  </div>
                </motion.div>

                {/* Row 2: Email */}
                <motion.div variants={fadeInUp} className="space-y-2">
                  <Label htmlFor="email" className="text-foreground font-mono text-sm">Business Email*</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Business Email*"
                    value={formData.email}
                    onChange={(e) => {
                      setFormData({ ...formData, email: e.target.value });
                      setErrors({ ...errors, email: false });
                    }}
                    className={`bg-background/50 font-mono ${errors.email ? 'border-destructive' : ''}`}
                  />
                  {errors.email && (
                    <p className="text-destructive text-sm font-mono">Please complete this required field.</p>
                  )}
                </motion.div>

                {/* Row 3: Company */}
                <motion.div variants={fadeInUp} className="space-y-2">
                  <Label htmlFor="company" className="text-foreground font-mono text-sm">Company Name*</Label>
                  <Input
                    id="company"
                    placeholder="Company Name*"
                    value={formData.company}
                    onChange={(e) => {
                      setFormData({ ...formData, company: e.target.value });
                      setErrors({ ...errors, company: false });
                    }}
                    className={`bg-background/50 font-mono ${errors.company ? 'border-destructive' : ''}`}
                  />
                  {errors.company && (
                    <p className="text-destructive text-sm font-mono">Please complete this required field.</p>
                  )}
                </motion.div>

                {/* Row 4: Submit Button */}
                <motion.div variants={fadeInUp} className="flex justify-center pt-4">
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button type="submit" variant="heroCta" size="lg" className="min-w-[200px] font-heading font-semibold">
                      Submit
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  </motion.div>
                </motion.div>
              </motion.form>
            </Card>
          </Reveal>
        </div>
      </div>

      {/* Decorative bottom line - Expands horizontally */}
      <motion.div
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: 1 }}
        transition={{ duration: 0.8, ease: "circOut" }}
        className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent origin-center"
      />
    </section>
  );
};

export default ConsultationSection;