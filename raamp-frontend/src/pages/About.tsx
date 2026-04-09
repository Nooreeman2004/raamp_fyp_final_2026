import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card } from "@/components/ui/card";
import { User } from "lucide-react";
import { cn } from "@/lib/utils";

// Animations Import
import Reveal from "@/components/ui/Reveal";
import { motion } from "framer-motion";
import { hoverLift, staggerContainer } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

// Import team member photos
import abdullahImg from "@/assets/team/Abdullah_aamir.jpeg";
import noorImg from "@/assets/team/Noor_e_eman.jpeg";
import tamimiImg from "@/assets/team/tamimi.jpeg";
import rashidImg from "@/assets/team/rashid_mehmood.jpeg";

const About = () => {
  const team = [
    {
      name: "Abdullah Aamir",
      role: "Co-Founder & Developer",
      type: "developer",
      image: abdullahImg
    },
    {
      name: "Noor E Eman Malik",
      role: "Co-Founder & Developer",
      type: "developer",
      image: noorImg
    },
    {
      name: "Dr. Manzoor Ilahi Tamimi",
      role: "Project Supervisor",
      type: "advisor",
      image: tamimiImg,
      objectPosition: "object-top"
    },
    {
      name: "Mr. Rashid Mehmood",
      role: "Co-Supervisor",
      type: "advisor",
      image: rashidImg
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background overflow-x-hidden">
      <Navigation />

      {/* Breadcrumbs - Simple Fade In */}
      <Reveal variant="fadeIn" delay={0.1} className="container mx-auto px-4 pt-20">
        <Breadcrumbs items={[
          { label: 'Home', href: '/' },
          { label: 'About' },
        ]} />
      </Reveal>

      {/* Hero Section */}
      <section className="pt-8 pb-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center space-y-6">
            {/* Title uses Blur Effect*/}
            <Reveal variant="blurInUp">
              <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent font-heading font-semibold">
                <BlurText text="Revolutionizing Local Business Marketing" />
              </h1>
            </Reveal>

            {/* Paragraph fades in slightly later */}
            <Reveal variant="fadeInUp" delay={0.2}>
              <p className="text-lg md:text-xl text-muted-foreground max-w-4xl mx-auto leading-relaxed font-mono">
                The Revolutionary AI-Powered Autonomous Marketing Platform (RAAMP) transforms digital marketing
                for small businesses by making it smarter, faster, and more accessible. We bridge the gap between
                technology and creativity to deliver campaigns that truly connect with local audiences.
              </p>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Vision Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          {/* The whole card fades up when scrolled into view */}
          <Reveal variant="fadeInUp" duration={0.8}>
            <Card className="p-8 md:p-12 bg-card/50 backdrop-blur-sm border-primary/10">
              <h2 className="text-3xl font-bold mb-6 text-center font-heading font-semibold">Our Vision</h2>
              <p className="text-lg text-muted-foreground leading-relaxed text-center max-w-4xl mx-auto font-mono">
                For local businesses such as restaurants and fashion boutiques that struggle with costly, complex tools,
                RAAMP offers an intelligent, fully automated solution. We utilize Bayesian analytics and generative
                intelligence to predict customer intent and optimize return on ad spend (ROAS) in real time.
              </p>
            </Card>
          </Reveal>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <Reveal variant="fadeInUp" className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 font-heading font-semibold">Meet the Team</h2>
            <p className="text-muted-foreground font-mono">The people behind RAAMP's innovation</p>
          </Reveal>

          {/* Developers */}
          <div className="mb-16">
            <Reveal variant="fadeInLeft">
              <h3 className="text-2xl font-bold mb-8 text-center text-primary font-heading font-semibold">Developers</h3>
            </Reveal>

            {/* We use motion.div here for the Stagger Effect */}
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto"
            >
              {team.filter(member => member.type === "developer").map((member, index) => (
                // Individual Card Animation
                <motion.div key={index} variants={hoverLift} initial="rest" whileHover="hover">
                  {/* We wrap the card in motion to animate entrance (fadeInUp) */}
                  <Reveal variant="fadeInUp">
                    <Card className="p-6 text-center card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all h-full cursor-pointer group">
                      <div className="flex flex-col items-center space-y-4">
                        <div className="w-32 h-32 rounded-full overflow-hidden flex items-center justify-center border-2 border-primary/20 group-hover:border-primary transition-all duration-300">
                          {member.image ? (
                            <img
                              src={member.image}
                              alt={member.name}
                              className={cn("w-full h-full object-cover", (member as any).objectPosition || "object-center")}
                            />
                          ) : (
                            <User className="w-16 h-16 text-primary" />
                          )}
                        </div>
                        <div>
                          <h4 className="text-xl font-bold font-heading font-semibold">{member.name}</h4>
                          <p className="text-primary text-sm mt-1 font-mono">{member.role}</p>
                        </div>
                      </div>
                    </Card>
                  </Reveal>
                </motion.div>
              ))}
            </motion.div>
          </div>

          {/* Advisors */}
          <div>
            <Reveal variant="fadeInLeft">
              <h3 className="text-2xl font-bold mb-8 text-center text-primary font-heading font-semibold">Advisors</h3>
            </Reveal>

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto"
            >
              {team.filter(member => member.type === "advisor").map((member, index) => (
                <motion.div key={index} variants={hoverLift} initial="rest" whileHover="hover">
                  <Reveal variant="fadeInUp">
                    <Card className="p-6 text-center card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all h-full cursor-pointer group">
                      <div className="flex flex-col items-center space-y-4">
                        <div className="w-32 h-32 rounded-full overflow-hidden flex items-center justify-center border-2 border-primary/20 group-hover:border-primary transition-all duration-300">
                          {member.image ? (
                            <img
                              src={member.image}
                              alt={member.name}
                              className={cn("w-full h-full object-cover", (member as any).objectPosition || "object-center")}
                            />
                          ) : (
                            <User className="w-16 h-16 text-primary" />
                          )}
                        </div>
                        <div>
                          <h4 className="text-xl font-bold font-heading font-semibold">{member.name}</h4>
                          <p className="text-primary text-sm mt-1 font-mono">{member.role}</p>
                        </div>
                      </div>
                    </Card>
                  </Reveal>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default About;
