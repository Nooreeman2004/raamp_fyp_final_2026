import { useState } from "react";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Utensils, Save, Clock, MapPin } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

const RestaurantProfile = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [formData, setFormData] = useState({
        cuisineType: "Italian",
        averagePrice: "$$",
        openingHours: "11:00 AM - 10:00 PM",
        deliveryRadius: "5 miles",
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        // Simulate API call
        setTimeout(() => {
            setIsLoading(false);
            toast({
                title: "Restaurant Profile Saved",
                description: "Your restaurant details have been updated successfully.",
            });
        }, 1500);
    };

    return (
        <Layout breadcrumbItems={[{ label: "Profile", href: "/profile/user" }, { label: "Restaurant Details" }]}>
            <motion.div
                className="space-y-6 max-w-3xl mx-auto"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Reveal variant="blurInUp">
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                            <Utensils className="w-7 h-7 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold font-heading font-semibold">
                                <BlurText text="Restaurant Profile" />
                            </h1>
                            <p className="text-muted-foreground font-mono text-sm">
                                Specific details for your restaurant business
                            </p>
                        </div>
                    </div>
                </Reveal>

                <Reveal variant="fadeInUp" delay={0.1}>
                    <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label htmlFor="cuisineType" className="font-mono text-xs">Cuisine Type</Label>
                                    <Input
                                        id="cuisineType"
                                        name="cuisineType"
                                        value={formData.cuisineType}
                                        onChange={handleChange}
                                        className="bg-background/50 font-mono"
                                        placeholder="e.g. Italian, Mexican, Sushi"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="averagePrice" className="font-mono text-xs">Price Range</Label>
                                    <Input
                                        id="averagePrice"
                                        name="averagePrice"
                                        value={formData.averagePrice}
                                        onChange={handleChange}
                                        className="bg-background/50 font-mono"
                                        placeholder="$, $$, $$$"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="openingHours" className="font-mono text-xs">Opening Hours</Label>
                                    <div className="relative">
                                        <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="openingHours"
                                            name="openingHours"
                                            value={formData.openingHours}
                                            onChange={handleChange}
                                            className="pl-9 bg-background/50 font-mono"
                                            placeholder="e.g. 9AM - 10PM"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="deliveryRadius" className="font-mono text-xs">Delivery Radius</Label>
                                    <div className="relative">
                                        <MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="deliveryRadius"
                                            name="deliveryRadius"
                                            value={formData.deliveryRadius}
                                            onChange={handleChange}
                                            className="pl-9 bg-background/50 font-mono"
                                            placeholder="e.g. 5 miles"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end pt-4">
                                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                    <Button type="submit" disabled={isLoading} className="font-heading font-semibold text-lg">
                                        {isLoading ? (
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                Saving...
                                            </div>
                                        ) : (
                                            <>
                                                <Save className="w-4 h-4 mr-2" />
                                                Save Details
                                            </>
                                        )}
                                    </Button>
                                </motion.div>
                            </div>
                        </form>
                    </Card>
                </Reveal>
            </motion.div>
        </Layout>
    );
};

export default RestaurantProfile;
