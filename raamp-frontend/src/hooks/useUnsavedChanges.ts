import { useEffect } from "react";

interface UseUnsavedChangesOptions {
  hasUnsavedChanges: boolean;
  message?: string;
}

export function useUnsavedChanges({ 
  hasUnsavedChanges, 
  message = "You have unsaved changes. Are you sure you want to leave?" 
}: UseUnsavedChangesOptions): null {
  // Fallback implementation: modern react-router data routers expose
  // `useBlocker`, but the app may use a plain BrowserRouter. To avoid
  // crashing the app we don't call `useBlocker` here. Instead we
  // install a `beforeunload` handler to warn the user when they try
  // to close/refresh the page. This does not block internal SPA
  // navigation, but avoids runtime errors and covers the most common
  // cause of lost work (reload/close).

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!hasUnsavedChanges) return undefined;
      e.preventDefault();
      e.returnValue = message; // Chrome requires returnValue to be set
      return message;
    };

    if (hasUnsavedChanges) {
      window.addEventListener('beforeunload', handler);
    }

    return () => {
      window.removeEventListener('beforeunload', handler);
    };
  }, [hasUnsavedChanges, message]);

  // No blocker object to return in this simplified implementation
  return null as any;
}

