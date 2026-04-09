import { ContentSuggestion } from "@/services/trendService";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sparkles, Video, Hash, Target, Users, Lightbulb, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

interface ContentSuggestionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  suggestions: ContentSuggestion | null;
  isLoading: boolean;
}

export const ContentSuggestionsModal = ({ 
  isOpen, 
  onClose, 
  suggestions, 
  isLoading 
}: ContentSuggestionsModalProps) => {
  const navigate = useNavigate();

  const handleUsePrompt = () => {
    if (!suggestions?.campaign_angle) return;
    onClose();
    navigate("/dashboard/creative", {
      state: { prefillPrompt: suggestions.campaign_angle },
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-deep-teal-800 border-deep-teal-700 text-foreground max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-heading font-semibold flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-neon-teal animate-pulse" />
            AI Content Suggestions
          </DialogTitle>
          <DialogDescription className="text-muted-foreground/80 font-mono text-sm">
            {suggestions ? `for "${suggestions.keyword}"` : "Generating ideas..."}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="w-16 h-16 border-4 border-neon-teal border-t-transparent rounded-full animate-spin" />
            <p className="text-sm font-mono text-muted-foreground/80 animate-pulse">
              AI analyzing trend patterns...
            </p>
          </div>
        ) : suggestions ? (
          <div className="space-y-6 py-4">
            {/* Lifecycle & Profit Banner */}
            <div className="flex items-center gap-4 p-4 bg-deep-teal-900 rounded-lg border border-deep-teal-700">
              <div className="flex-1">
                <p className="text-xs text-muted-foreground font-mono uppercase mb-1">Lifecycle Stage</p>
                <Badge className={`
                  ${suggestions.lifecycle_stage === 'Emerging' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50' :
                    suggestions.lifecycle_stage === 'Breakout' ? 'bg-orange-500/20 text-orange-400 border-orange-500/50' :
                    suggestions.lifecycle_stage === 'Mainstream' ? 'bg-teal-500/20 text-teal-400 border-teal-500/50' :
                    suggestions.lifecycle_stage === 'Saturated' ? 'bg-amber-500/20 text-amber-400 border-amber-500/50' :
                    'bg-red-500/20 text-red-400 border-red-500/50'
                  } border font-mono text-xs`}>
                  {suggestions.lifecycle_stage}
                </Badge>
              </div>
              <div className="flex-1">
                <p className="text-xs text-muted-foreground font-mono uppercase mb-1">Profit Score</p>
                <p className={`text-2xl font-bold ${
                  suggestions.profit_score >= 80 ? 'text-emerald-400' :
                  suggestions.profit_score >= 60 ? 'text-teal-400' :
                  suggestions.profit_score >= 40 ? 'text-amber-400' :
                  'text-red-400'
                }`}>
                  {suggestions.profit_score.toFixed(0)}/100
                </p>
              </div>
            </div>

            {/* Video Ideas */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2">
                <Video className="w-5 h-5 text-neon-teal" />
                <h3 className="font-heading font-semibold text-lg tracking-wide">Video Content Ideas</h3>
              </div>
              <div className="grid gap-2">
                {suggestions.video_ideas.map((idea, idx) => (
                  <div 
                    key={idx}
                    className="p-3 bg-deep-teal-900 rounded-lg border border-deep-teal-700 hover:border-neon-teal/50 transition-colors"
                  >
                    <p className="text-sm font-mono text-white/80">{idea}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Hooks */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-400" />
                <h3 className="font-heading font-semibold text-lg tracking-wide">Attention Hooks</h3>
              </div>
              <div className="grid gap-2">
                {suggestions.hooks.map((hook, idx) => (
                  <div 
                    key={idx}
                    className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30 hover:border-amber-400 transition-colors"
                  >
                    <p className="text-sm font-mono text-amber-100 italic">"{hook}"</p>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Hashtags */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2">
                <Hash className="w-5 h-5 text-teal-400" />
                <h3 className="font-heading font-semibold text-lg tracking-wide">Hashtag Strategy</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {suggestions.hashtags.map((tag, idx) => (
                  <Badge 
                    key={idx}
                    variant="secondary"
                    className="bg-teal-500/20 text-teal-300 border-teal-500/30 font-mono text-xs"
                  >
                    #{tag}
                  </Badge>
                ))}
              </div>
            </motion.div>

            {/* Campaign Angle */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-400" />
                <h3 className="font-heading font-semibold text-lg tracking-wide">Campaign Angle</h3>
              </div>
              <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
                <p className="text-sm font-mono text-purple-100">{suggestions.campaign_angle}</p>
              </div>
            </motion.div>

            {/* Influencer Strategy */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-emerald-400" />
                <h3 className="font-heading font-semibold text-lg tracking-wide">Influencer Strategy</h3>
              </div>
              <div className="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
                <p className="text-sm font-mono text-emerald-100">{suggestions.influencer_strategy}</p>
              </div>
            </motion.div>

            {/* Use This Prompt CTA */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="pt-2 border-t border-deep-teal-700"
            >
              <Button
                onClick={handleUsePrompt}
                className="w-full bg-primary/20 hover:bg-primary text-primary hover:text-black border border-primary/50 font-mono text-sm py-5"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Use This Prompt in Creative Studio
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </motion.div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground/80 font-mono text-sm">
            No suggestions available
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
