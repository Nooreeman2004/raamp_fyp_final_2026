/**
 * Restaurant-specific campaign templates for Creative Studio
 * Designed for restaurant owners without marketing expertise
 */

import type { LucideIcon } from "lucide-react";

export interface CampaignTemplate {
  id: string;
  title: string;
  category: string;
  prompt: string;
  icon: LucideIcon;
  emoji: string;
  description: string;
}

import { 
  Sparkles, Utensils, Leaf, ChefHat, PartyPopper, 
  Wine, Salad, Users, Heart, Star, Trophy, 
  UtensilsCrossed, UsersRound, Sprout, Gift, 
  CalendarDays, Mic, Truck, Package 
} from "lucide-react";

export const RESTAURANT_CAMPAIGN_TEMPLATES: CampaignTemplate[] = [
  // Menu & Food Promotions
  {
    id: "new-menu-item",
    title: "New Menu Item Launch",
    category: "Menu",
    icon: Sparkles,
    emoji: "✨",
    description: "Announce a new dish or drink",
    prompt: "We're launching a new [dish/drink name] on our menu. It features [key ingredients] and is perfect for [target customers]. Create an exciting post that makes people want to try it."
  },
  {
    id: "daily-special",
    title: "Daily Special",
    category: "Menu",
    icon: Utensils,
    emoji: "🍴",
    description: "Promote today's special dish",
    prompt: "Today's special is [dish name] - [brief description]. Available only today. Create a post that creates urgency and highlights what makes it special."
  },
  {
    id: "seasonal-menu",
    title: "Seasonal Menu Update",
    category: "Menu",
    icon: Leaf,
    emoji: "🔄",
    description: "Announce seasonal menu changes",
    prompt: "We've updated our menu for [season] with fresh, seasonal ingredients. New items include [list 2-3 items]. Create a post celebrating the new season and inviting customers to try our seasonal offerings."
  },
  {
    id: "chef-special",
    title: "Chef's Special",
    category: "Menu",
    icon: ChefHat,
    emoji: "👨‍🍳",
    description: "Highlight chef's recommendation",
    prompt: "Our chef recommends [dish name] - made with [special ingredients/technique]. Create a post that showcases the chef's expertise and makes this dish sound irresistible."
  },

  // Promotions & Offers
  {
    id: "weekend-special",
    title: "Weekend Special Promotion",
    category: "Promotions",
    icon: PartyPopper,
    emoji: "🎉",
    description: "Weekend deals and offers",
    prompt: "This weekend only: [offer details, e.g., '20% off all pasta dishes' or 'Buy 1 Get 1 on desserts']. Create an exciting post that drives weekend traffic to our restaurant."
  },
  {
    id: "happy-hour",
    title: "Happy Hour Announcement",
    category: "Promotions",
    icon: Wine,
    emoji: "🍷",
    description: "Promote happy hour deals",
    prompt: "Happy Hour from [time] to [time]! [Offer details, e.g., '50% off drinks' or 'Special appetizer prices']. Create a fun post that gets people excited to visit during happy hour."
  },
  {
    id: "lunch-deal",
    title: "Lunch Deal",
    category: "Promotions",
    icon: Salad,
    emoji: "🥗",
    description: "Promote lunch specials",
    prompt: "Lunch special: [deal details] available from [time] to [time]. Perfect for office workers and quick lunch breaks. Create a post targeting lunch crowd."
  },
  {
    id: "family-deal",
    title: "Family Meal Deal",
    category: "Promotions",
    icon: Users,
    emoji: "👨‍👩‍👧‍👦",
    description: "Family-sized meal offers",
    prompt: "Family meal deal: [package details] for [price]. Feeds [number] people. Create a post that appeals to families looking for convenient, delicious meals."
  },

  // Customer Engagement
  {
    id: "customer-appreciation",
    title: "Customer Appreciation Post",
    category: "Engagement",
    icon: Heart,
    emoji: "💖",
    description: "Thank your loyal customers",
    prompt: "Thank you to all our amazing customers for your continued support! We appreciate you choosing us for [occasions/meals]. Create a heartfelt post showing gratitude."
  },
  {
    id: "customer-testimonial",
    title: "Customer Testimonial",
    category: "Engagement",
    icon: Star,
    emoji: "⭐",
    description: "Share customer reviews",
    prompt: "Our customer [name/anonymous] said: '[testimonial quote]'. We're so happy to hear this! Create a post sharing this positive feedback and inviting others to visit."
  },
  {
    id: "milestone-celebration",
    title: "Milestone Celebration",
    category: "Engagement",
    icon: Trophy,
    emoji: "🏆",
    description: "Celebrate business milestones",
    prompt: "We're celebrating [milestone, e.g., '5 years in business', '10,000 customers served', 'opening our 2nd location']. Thank you for being part of our journey! Create a celebratory post."
  },

  // Behind the Scenes
  {
    id: "behind-scenes-kitchen",
    title: "Behind the Scenes - Kitchen",
    category: "Behind the Scenes",
    icon: UtensilsCrossed,
    emoji: "🎬",
    description: "Show kitchen preparation",
    prompt: "Take a peek behind the scenes! Our team is preparing [dish/ingredient] with care and attention. Create a post showing the hard work and passion that goes into every meal."
  },
  {
    id: "meet-the-team",
    title: "Meet the Team",
    category: "Behind the Scenes",
    icon: UsersRound,
    emoji: "👥",
    description: "Introduce staff members",
    prompt: "Meet [staff name], our [role]. They've been with us for [time] and love [something about their job]. Create a friendly post introducing our team member."
  },
  {
    id: "ingredient-spotlight",
    title: "Ingredient Spotlight",
    category: "Behind the Scenes",
    icon: Sprout,
    emoji: "🌱",
    description: "Highlight quality ingredients",
    prompt: "We source [ingredient] from [source/supplier]. It's [quality description, e.g., 'organic', 'locally grown', 'imported from Italy']. Create a post highlighting our commitment to quality ingredients."
  },

  // Events & Occasions
  {
    id: "holiday-special",
    title: "Holiday Special",
    category: "Events",
    icon: Gift,
    emoji: "🎁",
    description: "Holiday promotions",
    prompt: "Celebrate [holiday name] with us! [Special offer/menu/event details]. Create a festive post that captures the holiday spirit and invites customers to celebrate with us."
  },
  {
    id: "reservation-reminder",
    title: "Reservation Reminder",
    category: "Events",
    icon: CalendarDays,
    emoji: "📅",
    description: "Encourage reservations",
    prompt: "Planning to visit us [this weekend/for dinner/for a special occasion]? Book your table now! [Reservation details]. Create a post encouraging advance bookings."
  },
  {
    id: "event-announcement",
    title: "Special Event",
    category: "Events",
    icon: Mic,
    emoji: "🎤",
    description: "Announce special events",
    prompt: "Join us for [event name] on [date]! [Event details]. Create an exciting post that gets people interested in attending our special event."
  },

  // Delivery & Takeout
  {
    id: "delivery-promo",
    title: "Delivery Promotion",
    category: "Delivery",
    icon: Truck,
    emoji: "🚚",
    description: "Promote delivery service",
    prompt: "Order from home! [Delivery offer/details]. Available on [platforms/phone number]. Create a post promoting our delivery service and any special delivery offers."
  },
  {
    id: "takeout-special",
    title: "Takeout Special",
    category: "Delivery",
    icon: Package,
    emoji: "📦",
    description: "Takeout deals",
    prompt: "Takeout special: [offer details]. Call [phone] or order online. Create a post making takeout convenient and appealing."
  }
];

export const TEMPLATE_CATEGORIES = [
  "All",
  "Menu",
  "Promotions",
  "Engagement",
  "Behind the Scenes",
  "Events",
  "Delivery"
] as const;

export type TemplateCategory = typeof TEMPLATE_CATEGORIES[number];
