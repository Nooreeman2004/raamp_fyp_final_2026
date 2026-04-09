import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { User } from "lucide-react";
import { Card } from "@/components/ui/card";
import Reveal from "@/components/ui/Reveal";
import { cn } from "@/lib/utils";

// Import team member photos
import abdullahImg from "@/assets/team/Abdullah_aamir.jpeg";
import noorImg from "@/assets/team/Noor_e_eman.jpeg";
import tamimiImg from "@/assets/team/tamimi.jpeg";
import rashidImg from "@/assets/team/rashid_mehmood.jpeg";

const team = [
    {
        name: "Abdullah Aamir",
        role: "Co-Founder & Developer",
        type: "developer",
        image: abdullahImg,
        direction: { x: -200, y: -100, rotate: -10 } // Comes from top-left
    },
    {
        name: "Noor E Eman Malik",
        role: "Co-Founder & Developer",
        type: "developer",
        image: noorImg,
        imageScale: "scale-[1.5]",
        objectPosition: "object-bottom",
        direction: { x: 200, y: -100, rotate: 10 } // Comes from top-right
    },
    {
        name: "Dr. Manzoor Ilahi Tamimi",
        role: "Project Supervisor",
        type: "advisor",
        image: tamimiImg,
        objectPosition: "object-top",
        direction: { x: -200, y: 100, rotate: -5 } // Comes from bottom-left
    },
    {
        name: "Mr. Rashid Mehmood",
        role: "Co-Supervisor",
        type: "advisor",
        image: rashidImg,
        direction: { x: 200, y: 100, rotate: 5 } // Comes from bottom-right
    }
];

const FloatingTeam = () => {
    const containerRef = useRef<HTMLDivElement>(null);

    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "center center"]
    });

    // Opacity fade in
    const opacity = useTransform(scrollYProgress, [0, 0.8], [0, 1]);
    const scale = useTransform(scrollYProgress, [0, 0.8], [0.8, 1]);

    return (
        <section ref={containerRef} className="py-24 relative overflow-hidden min-h-[80vh] flex flex-col justify-center">
            <div className="container mx-auto px-4 max-w-6xl">

                {/* Header */}
                <div className="text-center mb-20">
                    <Reveal variant="blurInUp">
                        <h2 className="text-4xl md:text-5xl font-bold mb-4 font-heading font-semibold">
                            Visionaries & <span className="text-primary">Builders</span>
                        </h2>
                    </Reveal>
                    <Reveal variant="fadeIn" delay={0.2}>
                        <p className="text-muted-foreground font-mono">The minds behind RAAMP's innovation</p>
                    </Reveal>
                </div>

                {/* Team Grid */}
                <div className="grid md:grid-cols-2 gap-8 md:gap-12 max-w-4xl mx-auto">
                    {team.map((member, index) => {
                        // Create individual transforms for each card based on its direction vector
                        const x = useTransform(scrollYProgress, [0, 1], [member.direction.x, 0]);
                        const y = useTransform(scrollYProgress, [0, 1], [member.direction.y, 0]);
                        const rotate = useTransform(scrollYProgress, [0, 1], [member.direction.rotate, 0]);

                        return (
                            <motion.div
                                key={index}
                                style={{
                                    x,
                                    y,
                                    rotate,
                                    opacity,
                                    scale
                                }}
                                className="relative"
                            >
                                {/* Section Divider for Advisors (Visual separation if needed, but grid handles it) */}
                                {index === 2 && (
                                    <div className="absolute -top-10 left-1/2 -translate-x-1/2 text-primary font-heading font-semiboldst text-xl opacity-80 md:hidden">
                                        ADVISORS
                                    </div>
                                )}

                                <Card className="p-8 text-center card-shadow bg-card/40 backdrop-blur-md border-primary/10 hover:border-primary/30 transition-all h-full group hover:bg-card/60">
                                    <div className="flex flex-col items-center space-y-6">
                                        {/* Avatar with Glow */}
                                        <div className="relative">
                                            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                            <div className="w-32 h-32 rounded-full overflow-hidden flex items-center justify-center border-2 border-primary/20 relative z-10 group-hover:scale-110 group-hover:border-primary transition-all duration-500 shadow-[0_0_20px_rgba(0,224,208,0.2)]">
                                                {member.image ? (
                                                    <img
                                                        src={member.image}
                                                        alt={member.name}
                                                        className={cn("w-full h-full object-cover", (member as any).objectPosition || "object-center", (member as any).imageScale || "")}
                                                    />
                                                ) : (
                                                    <User className="w-12 h-12 text-primary/80 group-hover:text-primary transition-colors" />
                                                )}
                                            </div>
                                        </div>

                                        {/* Text Content */}
                                        <div>
                                            <h4 className="text-2xl font-bold font-heading font-semibold text-foreground group-hover:text-primary transition-colors">
                                                {member.name.toUpperCase()}
                                            </h4>
                                            <p className="text-primary/80 text-sm mt-2 font-mono tracking-tight">
                                                {member.role}
                                            </p>
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Central "Advisors" Label for Desktop Layout */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 hidden md:block pointer-events-none opacity-0 md:opacity-100">
                    {/* This is just a visual anchor, maybe a faint glow or text behind */}
                </div>

            </div>
        </section>
    );
};

export default FloatingTeam;
