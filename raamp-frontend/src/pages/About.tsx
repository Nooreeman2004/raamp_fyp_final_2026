import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card } from "@/components/ui/card";
import { User } from "lucide-react";

const About = () => {
  const team = [
    {
      name: "Abdullah Aamir",
      role: "Co-Founder & Developer",
      type: "developer"
    },
    {
      name: "Noor E Eman Malik",
      role: "Co-Founder & Developer",
      type: "developer"
    },
    {
      name: "Dr. Manzoor Ilahi Tamimi",
      role: "Project Supervisor",
      type: "advisor"
    },
    {
      name: "Mr. Mohsin Ahmed",
      role: "Co-Supervisor",
      type: "advisor"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background">
      <Navigation />
      
      {/* Breadcrumbs */}
      <div className="container mx-auto px-4 pt-20">
        <Breadcrumbs items={[
          { label: 'Home', href: '/' },
          { label: 'About' },
        ]} />
      </div>
      
      {/* Hero Section */}
      <section className="pt-8 pb-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center space-y-6">
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Revolutionizing Local Business Marketing
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-4xl mx-auto leading-relaxed">
              The Revolutionary AI-Powered Autonomous Marketing Platform (RAAMP) transforms digital marketing 
              for small businesses by making it smarter, faster, and more accessible. We bridge the gap between 
              technology and creativity to deliver campaigns that truly connect with local audiences.
            </p>
          </div>
        </div>
      </section>

      {/* Vision Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto max-w-6xl">
          <Card className="p-8 md:p-12 bg-card/50 backdrop-blur-sm border-primary/10">
            <h2 className="text-3xl font-bold mb-6 text-center">Our Vision</h2>
            <p className="text-lg text-muted-foreground leading-relaxed text-center max-w-4xl mx-auto">
              For local businesses such as restaurants and fashion boutiques that struggle with costly, complex tools, 
              RAAMP offers an intelligent, fully automated solution. We utilize Bayesian analytics and generative 
              intelligence to predict customer intent and optimize return on ad spend (ROAS) in real time.
            </p>
          </Card>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Meet the Team</h2>
            <p className="text-muted-foreground">The people behind RAAMP's innovation</p>
          </div>

          {/* Developers */}
          <div className="mb-16">
            <h3 className="text-2xl font-bold mb-8 text-center text-primary">Developers</h3>
            <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
              {team.filter(member => member.type === "developer").map((member, index) => (
                <Card key={index} className="p-6 text-center card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all">
                  <div className="flex flex-col items-center space-y-4">
                    <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border-2 border-primary/20">
                      <User className="w-16 h-16 text-primary" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold">{member.name}</h4>
                      <p className="text-primary text-sm mt-1">{member.role}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Advisors */}
          <div>
            <h3 className="text-2xl font-bold mb-8 text-center text-primary">Advisors</h3>
            <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
              {team.filter(member => member.type === "advisor").map((member, index) => (
                <Card key={index} className="p-6 text-center card-shadow bg-card/70 backdrop-blur-sm border-primary/10 hover:border-primary/30 transition-all">
                  <div className="flex flex-col items-center space-y-4">
                    <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border-2 border-primary/20">
                      <User className="w-16 h-16 text-primary" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold">{member.name}</h4>
                      <p className="text-primary text-sm mt-1">{member.role}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default About;
