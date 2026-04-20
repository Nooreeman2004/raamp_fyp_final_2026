import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { 
  LayoutDashboard, 
  MapPin, 
  Sparkles, 
  MessageSquare,
  FlaskConical,
  TrendingUp,
  User,
  Store,
  Settings,
  FileText,
  Zap
} from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  keywords: string[];
  category: string;
}

const navigationItems: NavigationItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
    keywords: ["dashboard", "home", "main", "overview"],
    category: "Main"
  },
  {
    id: "geo-intent",
    label: "Geo Intent",
    path: "/dashboard/geo-intent",
    icon: MapPin,
    keywords: ["geo", "location", "map", "intent", "geographic"],
    category: "Analytics"
  },
  {
    id: "creative",
    label: "Creative Studio",
    path: "/dashboard/creative",
    icon: Sparkles,
    keywords: ["creative", "studio", "design", "assets", "content"],
    category: "Tools"
  },
  {
    id: "trends",
    label: "Trend Arbitrage",
    path: "/dashboard/trends",
    icon: TrendingUp,
    keywords: ["trend", "arbitrage", "trending", "opportunities"],
    category: "Analytics"
  },
  {
    id: "ab-testing",
    label: "A/B Testing",
    path: "/dashboard/ab-testing",
    icon: FlaskConical,
    keywords: ["ab", "testing", "experiments", "variants", "optimization"],
    category: "Analytics"
  },
  {
    id: "assistant",
    label: "RAAMP Assistant",
    path: "/dashboard/assistant",
    icon: MessageSquare,
    keywords: ["assistant", "ai", "help", "chat", "support"],
    category: "Tools"
  },
  {
    id: "user-profile",
    label: "User Profile",
    path: "/profile/user",
    icon: User,
    keywords: ["profile", "user", "account", "settings", "personal"],
    category: "Profile"
  },
  {
    id: "restaurant-profile",
    label: "Restaurant Profile",
    path: "/profile/restaurant",
    icon: Store,
    keywords: ["restaurant", "business", "profile", "location"],
    category: "Profile"
  },
  {
    id: "settings",
    label: "Settings",
    path: "/dashboard",
    icon: Settings,
    keywords: ["settings", "preferences", "config"],
    category: "Settings"
  },
];

export default function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [search, setSearch] = useState("");

  // Filter items based on search
  const filteredItems = navigationItems.filter((item) => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      item.label.toLowerCase().includes(searchLower) ||
      item.keywords.some((keyword) => keyword.toLowerCase().includes(searchLower)) ||
      item.category.toLowerCase().includes(searchLower)
    );
  });

  // Group items by category
  const groupedItems = filteredItems.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, NavigationItem[]>);

  const handleSelect = (path: string) => {
    navigate(path);
    onOpenChange(false);
    setSearch("");
  };

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === "Escape") {
        onOpenChange(false);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, onOpenChange]);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput 
        placeholder="Type a command or search..." 
        value={search}
        onValueChange={setSearch}
      />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        {Object.entries(groupedItems).map(([category, items]) => (
          <CommandGroup key={category} heading={category}>
            {items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <CommandItem
                  key={item.id}
                  onSelect={() => handleSelect(item.path)}
                  className={isActive ? "bg-primary/10" : ""}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  <span>{item.label}</span>
                  {isActive && (
                    <span className="ml-auto text-xs text-muted-foreground">Current</span>
                  )}
                </CommandItem>
              );
            })}
          </CommandGroup>
        ))}
      </CommandList>
    </CommandDialog>
  );
}

