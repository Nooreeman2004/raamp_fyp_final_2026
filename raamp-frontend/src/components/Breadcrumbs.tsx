import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
}

// Route label mappings for better breadcrumb names
const routeLabels: Record<string, string> = {
  'dashboard': 'Dashboard',
  'geo-intent': 'Geo-Intent',
  'creative': 'Creative Studio',
  'trends': 'Trend Arbitrage',
  'ab-testing': 'A/B Testing',
  'performance': 'Performance',
  'assistant': 'RAAMP Assistant',
  'profile': 'Profile',
  'user': 'User Profile',
  'restaurant': 'Restaurant Profile',
  'personal-details': 'Personal Details',
  'onboarding': 'Onboarding',
  'business-setup': 'Business Setup',
  'brand-settings': 'Brand Settings',
  'billing': 'Billing',
  'add-funds': 'Add Funds',
  'transactions': 'Transactions',
  'about': 'About Us',
  'resources': 'Resources',
  'legal': 'Legal & Compliance',
};

export default function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  const location = useLocation();
  
  // Auto-generate breadcrumbs from path if not provided
  const breadcrumbs: BreadcrumbItem[] = items || (() => {
    const paths = location.pathname.split('/').filter(Boolean);
    const generated: BreadcrumbItem[] = [];
    
    // Always start with Home/Dashboard
    if (paths.length === 0 || paths[0] !== 'dashboard') {
      generated.push({ label: 'Home', href: '/dashboard' });
    }
    
    let currentPath = '';
    paths.forEach((path, index) => {
      currentPath += `/${path}`;
      // Use route label mapping or format the path nicely
      const label = routeLabels[path] || path
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      generated.push({
        label,
        href: index === paths.length - 1 ? undefined : currentPath,
      });
    });
    
    return generated;
  })();

  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center space-x-2 text-sm", className)}>
      <ol className="flex items-center space-x-2 flex-wrap">
        {breadcrumbs.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-muted-foreground mx-2 flex-shrink-0" />
            )}
            {item.href && index < breadcrumbs.length - 1 ? (
              <Link
                to={item.href}
                className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1.5 hover:underline"
              >
                {index === 0 && <Home className="w-4 h-4" />}
                <span>{item.label}</span>
              </Link>
            ) : (
              <span className={cn(
                "flex items-center gap-1.5",
                index === breadcrumbs.length - 1 
                  ? "text-foreground font-semibold" 
                  : "text-muted-foreground"
              )}>
                {index === 0 && <Home className="w-4 h-4" />}
                <span>{item.label}</span>
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

