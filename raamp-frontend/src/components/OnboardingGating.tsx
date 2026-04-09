import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, ArrowRight, CheckCircle2, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { BlurText } from "@/components/ui/text-reveal";
import { OnboardingStep } from "@/hooks/useOnboardingStatus";
import Layout from "@/components/Layout";

interface OnboardingGatingProps {
    steps: OnboardingStep[];
    nextStep: OnboardingStep | undefined;
}

const OnboardingGating = ({ steps, nextStep }: OnboardingGatingProps) => {
    const navigate = useNavigate();

    return (
        <Layout breadcrumbItems={[{ label: "Access Restricted" }]}>
            <div className="min-h-[70vh] flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className="max-w-xl w-full"
                >
                    <Card className="relative overflow-hidden border-primary/20 bg-card/80 backdrop-blur-xl p-8 md:p-12 shadow-2xl">
                        {/* Background Decor */}
                        <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />
                        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl" />

                        <div className="relative z-10 flex flex-col items-center text-center space-y-6">
                            <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center mb-2">
                                <Lock className="w-10 h-10 text-primary" />
                            </div>

                            <div className="space-y-2">
                                <h1 className="text-4xl font-bold font-heading font-semibold text-foreground">
                                    <BlurText text="Almost there!" />
                                </h1>
                                <p className="text-muted-foreground font-mono text-sm max-w-sm mx-auto">
                                    Complete your profile setup to unlock full access to the RAAMP AI marketing engine.
                                </p>
                            </div>

                            {/* Progress Checklist */}
                            <div className="w-full bg-background/40 rounded-xl p-6 border border-primary/5 space-y-4">
                                <h3 className="text-xs font-mono font-bold text-primary uppercase tracking-widest text-left">
                                    Your Progress
                                </h3>
                                <div className="space-y-3">
                                    {steps.map((step) => (
                                        <div key={step.id} className="flex items-center justify-between group">
                                            <div className="flex items-center gap-3">
                                                {step.isCompleted ? (
                                                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                                ) : (
                                                    <Circle className="w-5 h-5 text-muted-foreground/30" />
                                                )}
                                                <span className={`text-sm font-mono ${step.isCompleted ? 'text-foreground/70' : 'text-muted-foreground'}`}>
                                                    {step.label}
                                                </span>
                                            </div>
                                            {step.isCompleted && (
                                                <span className="text-[10px] font-mono text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                                                    Done
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-4 w-full">
                                <Button
                                    asChild
                                    size="lg"
                                    className="w-full py-7 text-xl font-heading font-semiboldst group relative overflow-hidden"
                                >
                                    <Link to={nextStep?.route || "#"} replace>
                                        <span className="relative z-10 flex items-center justify-center gap-2">
                                            {nextStep?.id === 'personal_details' ? 'Finish Onboarding' : 'Complete Setup'}
                                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                        </span>
                                        <div className="absolute inset-0 bg-gradient-to-r from-primary to-teal-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </Link>
                                </Button>
                            </div>
                        </div>
                    </Card>
                </motion.div>
            </div>
        </Layout>
    );
};

export default OnboardingGating;
