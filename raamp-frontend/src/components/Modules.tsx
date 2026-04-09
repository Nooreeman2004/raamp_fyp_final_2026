import StickyScrollReveal from "@/components/ui/sticky-scroll-reveal";
import { Ultra3DCard } from "@/components/ui/ultra-3d-card";
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

const modules = [
  {
    title: "Predictive Analytics",
    description: "Leverage advanced AI to foresee market trends and consumer behavior, optimizing campaigns before launch.",
    content: (
      <Ultra3DCard
        title="Predictive Analytics"
        description="Foresee market trends."
        icon={TrendingUp}
        className="h-full w-full"
      >
        <div />
      </Ultra3DCard>
    )
  },
  {
    title: "Ad Creative Automation",
    description: "Generate high-performing ad creatives at scale, personalized for diverse audiences and platforms.",
    content: (
      <Ultra3DCard
        title="Ad Creative Automation"
        description="Generate high-performing ads."
        icon={Sparkles}
        className="h-full w-full"
      >
        <div />
      </Ultra3DCard>
    )
  },
  {
    title: "Audience Segmentation",
    description: "Automatically identify and target niche audiences with unparalleled precision based on real-time data.",
    content: (
      <Ultra3DCard
        title="Audience Segmentation"
        description="Target niche audiences."
        icon={Users}
        className="h-full w-full"
      >
        <div />
      </Ultra3DCard>
    )
  },
  {
    title: "Performance Forecasting",
    description: "Forecast campaign outcomes and ROI, allowing for proactive adjustments and strategic planning.",
    content: (
      <Ultra3DCard
        title="Performance Forecasting"
        description="Forecast outcomes and ROI."
        icon={BarChart3}
        className="h-full w-full"
      >
        <div />
      </Ultra3DCard>
    )
  },
];

const Modules = () => {
  return (
    <section className="py-24 bg-card/30">
      <div className="container mx-auto px-4 mb-16 text-center">
        <Reveal variant="blurInUp">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 font-heading font-semibold">
            Everything You Need to Market,{" "}
            <span className="text-primary">In One Autonomous Platform</span>
          </h2>
        </Reveal>
      </div>

      <StickyScrollReveal content={modules} />
    </section>
  );
};

export default Modules;