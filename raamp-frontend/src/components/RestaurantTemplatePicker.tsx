import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Sparkles, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { RESTAURANT_CAMPAIGN_TEMPLATES, TEMPLATE_CATEGORIES, type CampaignTemplate, type TemplateCategory } from "@/constants/restaurantTemplates";

interface RestaurantTemplatePickerProps {
  onSelectTemplate: (prompt: string) => void;
}

export const RestaurantTemplatePicker = ({ onSelectTemplate }: RestaurantTemplatePickerProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory>("All");

  const filteredTemplates = selectedCategory === "All"
    ? RESTAURANT_CAMPAIGN_TEMPLATES
    : RESTAURANT_CAMPAIGN_TEMPLATES.filter(t => t.category === selectedCategory);

  const handleSelectTemplate = (template: CampaignTemplate) => {
    onSelectTemplate(template.prompt);
    setIsOpen(false);
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="gap-2"
      >
        <Sparkles className="h-4 w-4" />
        Use Template
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Restaurant Campaign Templates
            </DialogTitle>
            <DialogDescription>
              Choose a template to get started quickly. You can customize it after selecting.
            </DialogDescription>
          </DialogHeader>

          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap pb-4 border-b">
            {TEMPLATE_CATEGORIES.map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </Button>
            ))}
          </div>

          {/* Templates Grid */}
          <div className="overflow-y-auto flex-1 pr-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <AnimatePresence mode="popLayout">
                {filteredTemplates.map((template) => (
                  <motion.div
                    key={template.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Card
                      className="p-4 cursor-pointer hover:border-primary transition-all hover:shadow-md"
                      onClick={() => handleSelectTemplate(template)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="text-3xl">
                          {template.emoji}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h4 className="font-semibold text-sm">{template.title}</h4>
                            <Badge variant="secondary" className="text-xs shrink-0">
                              {template.category}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">
                            {template.description}
                          </p>
                          <p className="text-xs text-muted-foreground italic line-clamp-2">
                            "{template.prompt.substring(0, 100)}..."
                          </p>
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {filteredTemplates.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No templates found in this category
              </div>
            )}
          </div>

          {/* Helper Text */}
          <div className="pt-4 border-t text-xs text-muted-foreground">
            💡 Tip: After selecting a template, customize it with your specific details (dish names, prices, dates, etc.)
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
