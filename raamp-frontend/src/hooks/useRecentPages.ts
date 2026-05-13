import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

interface RecentPage {
  path: string;
  label: string;
  timestamp: number;
}

const STORAGE_KEY = "raamp_recent_pages";
const MAX_RECENT_PAGES = 5;

export function useRecentPages(): { recentPages: RecentPage[]; clearRecentPages: () => void } {
  const location = useLocation();
  const [recentPages, setRecentPages] = useState<RecentPage[]>([]);

  // Page labels mapping
  const pageLabels: Record<string, string> = {
    "/dashboard": "Dashboard",
    "/dashboard/geo-intent": "Geo Intent",
    "/dashboard/creative": "Creative Studio",
    "/dashboard/trends": "Trend Arbitrage",
    "/dashboard/ab-testing": "A/B Testing",
    "/dashboard/assistant": "RAAMP Assistant",
    "/dashboard/billing": "Billing",
    "/profile/user": "User Profile",
    "/profile/restaurant": "Restaurant Profile",
    "/profile/onboarding": "Onboarding",
    "/profile/personal-details": "Personal Details",
  };

  // Load recent pages from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setRecentPages(JSON.parse(stored));
      }
    } catch (err) {
      console.error("Failed to load recent pages:", err);
    }
  }, []);

  // Track current page
  useEffect(() => {
    const currentPath = location.pathname;
    const label = pageLabels[currentPath] || currentPath;

    // Skip if it's the same as the last page
    if (recentPages.length > 0 && recentPages[0].path === currentPath) {
      return;
    }

    // Skip certain pages
    const skipPaths = ["/", "/login", "/signup", "/verify-email"];
    if (skipPaths.includes(currentPath)) {
      return;
    }

    setRecentPages((prev) => {
      // Remove if already exists
      const filtered = prev.filter((page) => page.path !== currentPath);
      
      // Add to beginning
      const updated = [
        { path: currentPath, label, timestamp: Date.now() },
        ...filtered,
      ].slice(0, MAX_RECENT_PAGES);

      // Save to localStorage
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (err) {
        console.error("Failed to save recent pages:", err);
      }

      return updated;
    });
  }, [location.pathname]);

  const clearRecentPages = (): void => {
    setRecentPages([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (err) {
      console.error("Failed to clear recent pages:", err);
    }
  };

  return { recentPages, clearRecentPages };
}

