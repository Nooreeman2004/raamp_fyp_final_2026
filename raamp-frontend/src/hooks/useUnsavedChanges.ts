import { useEffect, useRef } from "react";
import { useBlocker } from "react-router-dom";

interface UseUnsavedChangesOptions {
  hasUnsavedChanges: boolean;
  message?: string;
}

export function useUnsavedChanges({ 
  hasUnsavedChanges, 
  message = "You have unsaved changes. Are you sure you want to leave?" 
}: UseUnsavedChangesOptions) {
  const blocker = useBlocker(hasUnsavedChanges);

  useEffect(() => {
    if (blocker.state === "blocked") {
      const shouldLeave = window.confirm(message);
      if (shouldLeave) {
        blocker.proceed();
      } else {
        blocker.reset();
      }
    }
  }, [blocker, message]);

  return blocker;
}

