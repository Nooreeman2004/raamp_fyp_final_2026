import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useThemeMode } from "@/hooks/useThemeMode"

export function ThemeToggle() {
  const { isDark, mounted, toggleTheme } = useThemeMode()

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <Button
        variant="outline"
        size="icon"
        disabled
        className="w-10 h-10"
      />
    )
  }

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={() => toggleTheme()}
      className="relative w-10 h-10 bg-background border border-border hover:bg-secondary/80 hover:border-primary/50 transition-all duration-300 rounded-lg shadow-sm"
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
    >
      <Sun 
        className="h-[1.2rem] w-[1.2rem] text-foreground rotate-0 scale-100 transition-all duration-300 dark:-rotate-90 dark:scale-0" 
        aria-hidden="true"
      />
      <Moon 
        className="absolute h-[1.2rem] w-[1.2rem] text-foreground rotate-90 scale-0 transition-all duration-300 dark:rotate-0 dark:scale-100" 
        aria-hidden="true"
      />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}

