import { Link, useLocation } from "react-router-dom";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { User, Store } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProfileSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ProfileSidebar = ({ open, onOpenChange }: ProfileSidebarProps) => {
  const location = useLocation();

  const navItems = [
    {
      icon: User,
      label: "User Profile",
      href: "/profile/user",
      description: "Manage your personal information"
    },
    {
      icon: Store,
      label: "Restaurant Profile",
      href: "/profile/restaurant",
      description: "Manage your restaurant details"
    }
  ];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full min-w-0 max-w-[100vw] sm:max-w-md overflow-x-hidden">
        <SheetHeader>
          <SheetTitle className="text-2xl font-bold">
            Manage Profile
          </SheetTitle>
        </SheetHeader>

        <div className="space-y-4 py-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            
            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={() => onOpenChange(false)}
                className={cn(
                  "flex min-h-[3.25rem] items-start gap-4 p-4 rounded-lg border-2 transition-all cursor-pointer hover:border-primary/50 sm:min-h-0",
                  isActive 
                    ? "border-primary bg-primary/5" 
                    : "border-primary/10 bg-card/50"
                )}
              >
                <div className={cn(
                  "w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0",
                  isActive ? "bg-primary/20" : "bg-primary/10"
                )}>
                  <Icon className={cn(
                    "w-6 h-6",
                    isActive ? "text-primary" : "text-muted-foreground"
                  )} />
                </div>
                <div className="flex-1">
                  <h3 className={cn(
                    "font-bold text-lg mb-1",
                    isActive && "text-primary"
                  )}>
                    {item.label}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default ProfileSidebar;
