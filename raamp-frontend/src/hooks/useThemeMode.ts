import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

interface ThemeModeOptions {
  light: string;
  dark: string;
}

export function useThemeMode() {
  const { theme, setTheme, systemTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted && (resolvedTheme === "dark" || false);
  const isLight = mounted && (resolvedTheme === "light" || false);

  const toggleTheme = () => {
    if (mounted) {
      setTheme(isDark ? "light" : "dark");
    }
  };

  const setLightMode = () => setTheme("light");
  const setDarkMode = () => setTheme("dark");
  const setSystemMode = () => setTheme("system");

  const getThemeValue = (options: ThemeModeOptions): string => {
    return isDark ? options.dark : options.light;
  };

  return {
    theme,
    resolvedTheme,
    isDark,
    isLight,
    mounted,
    toggleTheme,
    setTheme,
    setLightMode,
    setDarkMode,
    setSystemMode,
    systemTheme,
    getThemeValue,
  };
}
