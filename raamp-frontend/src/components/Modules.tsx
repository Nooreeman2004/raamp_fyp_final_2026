import { Card } from "@/components/ui/card";
import { 
  TrendingUp, 
  Sparkles, 
  Users, 
  BarChart3, 
  Network, 
  MapPin, 
  Wand2, 
  DollarSign 
} from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverLift } from "@/utils/animations";

const modules = [
  {
    icon: TrendingUp,
    title: "Predictive Analytics",
    description: "Leverage advanced AI to foresee market trends and consumer behavior, optimizing campaigns before launch.",
  },
  {
    icon: Sparkles,
    title: "Ad Creative Automation",
    description: "Generate high-performing ad creatives at scale, personalized for diverse audiences and platforms.",
  },
  {
    icon: Users,
    title: "Audience Segmentation",
    description: "Automatically identify and target niche audiences with unparalleled precision based on real-time data.",
  },
  {
    icon: BarChart3,
    title: "Performance Forecasting",
    description: "Forecast campaign outcomes and ROI, allowing for proactive adjustments and strategic planning.",
  },
  {
    icon: Network,
    title: "Multi-Channel Orchestration",
    description: "Seamlessly manage and synchronize campaigns across all digital channels from a single intelligent platform.",
  },
  {
    icon: MapPin,
    title: "Geo-Targeting Engine",
    description: "Pinpoint and engage local audiences with hyper-localized ads driven by real-time geo-intent signals.",
  },
  {
    icon: Wand2,
    title: "AI Content Generation",
    description: "Automate the creation of compelling marketing copy and visuals tailored to your brand voice and objectives.",
  },
  {
    icon: DollarSign,
    title: "Automated Budget Allocation",
    description: "Optimize ad spend dynamically across campaigns and channels to maximize efficiency and returns.",
  },
];

const Modules = () => {
  return (
    <section className="py-24 bg-card/30">
      <div className="container mx-auto px-4">
        
        {/* Header with Blur Effect */}
        <div className="text-center mb-16">
          <Reveal variant="blurInUp">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Everything You Need to Market,{" "}
              <span className="text-primary">In One Autonomous Platform</span>
            </h2>
          </Reveal>
        </div>

        {/* Staggered Grid Container */}
        <motion.div 
          className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
        >
          {modules.map((module, index) => {
            const Icon = module.icon;
            return (
              <motion.div 
                key={index} 
                variants={fadeInUp} // Controlled by parent stagger
              >
                <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                  <Card 
                    className="card-shadow bg-card/70 backdrop-blur-sm border-primary/10 p-6 hover:border-primary/30 transition-all duration-300 group cursor-pointer h-full"
                  >
                    <div className="space-y-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                        <Icon className="w-6 h-6 text-primary" />
                      </div>
                      <h3 className="text-xl font-bold group-hover:text-primary transition-colors">
                        {module.title}
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {module.description}
                      </p>
                    </div>
                  </Card>
                </motion.div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
};

export default Modules;