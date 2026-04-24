/**
 * Standardized Loading Toast Patterns
 * 
 * Usage Guidelines:
 * - Quick operations (<5s): Use quick()
 * - Multi-step operations: Use multiStep()
 * - Long operations with progress: Use withProgress()
 * - Always dismiss loading toasts when operation completes
 */

import { toast } from 'sonner';

export const loadingPatterns = {
  /**
   * For quick operations (< 5 seconds)
   * Automatically dismissed when operation completes
   * 
   * @example
   * const toastId = loadingPatterns.quick("Saving settings");
   * await saveSettings();
   * toast.dismiss(toastId);
   * toast.success("Settings saved successfully.");
   */
  quick: (action: string): string | number => {
    return toast.loading(`${action}...`);
  },

  /**
   * For multi-step operations
   * Shows current step and total steps
   * Must be manually dismissed
   * 
   * @example
   * const toastId = loadingPatterns.multiStep(1, 2, "Creating video script");
   * await createScript();
   * toast.dismiss(toastId);
   * 
   * const toastId2 = loadingPatterns.multiStep(2, 2, "Generating video");
   * await generateVideo();
   * toast.dismiss(toastId2);
   */
  multiStep: (
    step: number,
    total: number,
    description: string
  ): string | number => {
    return toast.loading(`Step ${step}/${total}: ${description}...`, {
      duration: Infinity, // Keep until manually dismissed
    });
  },

  /**
   * For long operations with progress percentage
   * Shows percentage completion
   * Must be manually dismissed and updated
   * 
   * @example
   * const toastId = loadingPatterns.withProgress("Uploading file", 0);
   * // Update progress
   * toast.loading("Uploading file (50%)...", { id: toastId });
   * toast.loading("Uploading file (100%)...", { id: toastId });
   * toast.dismiss(toastId);
   */
  withProgress: (message: string, progress: number): string | number => {
    return toast.loading(`${message} (${progress}%)...`, {
      duration: Infinity,
    });
  },

  /**
   * For time-consuming operations with estimated duration
   * Useful for setting user expectations
   * 
   * @example
   * const toastId = loadingPatterns.withDuration(
   *   "Generating video",
   *   "2-5 minutes"
   * );
   * await generateVideo();
   * toast.dismiss(toastId);
   */
  withDuration: (message: string, duration: string): string | number => {
    return toast.loading(`${message}. This may take ${duration}.`, {
      duration: Infinity,
    });
  },

  /**
   * For operations that might take a while
   * Sets user expectations without specific time
   * 
   * @example
   * const toastId = loadingPatterns.longRunning("Scanning for trends");
   * await scanTrends();
   * toast.dismiss(toastId);
   */
  longRunning: (message: string): string | number => {
    return toast.loading(`${message}. This may take a moment...`, {
      duration: Infinity,
    });
  },
} as const;

/**
 * Helper to update an existing loading toast
 * Useful for progress updates
 * 
 * @example
 * const toastId = loadingPatterns.quick("Processing");
 * updateLoadingToast(toastId, "Processing (50%)");
 * updateLoadingToast(toastId, "Processing (100%)");
 */
export const updateLoadingToast = (
  toastId: string | number,
  message: string
): void => {
  toast.loading(message, { id: toastId });
};

/**
 * Helper to replace loading toast with success
 * 
 * @example
 * const toastId = loadingPatterns.quick("Saving");
 * await save();
 * completeLoadingToast(toastId, "Saved successfully");
 */
export const completeLoadingToast = (
  toastId: string | number,
  successMessage: string
): void => {
  toast.dismiss(toastId);
  toast.success(successMessage);
};

/**
 * Helper to replace loading toast with error
 * 
 * @example
 * const toastId = loadingPatterns.quick("Saving");
 * try {
 *   await save();
 *   completeLoadingToast(toastId, "Saved successfully");
 * } catch (error) {
 *   failLoadingToast(toastId, "Save failed", "Please try again");
 * }
 */
export const failLoadingToast = (
  toastId: string | number,
  errorTitle: string,
  errorDescription?: string
): void => {
  toast.dismiss(toastId);
  toast.error(errorTitle, {
    description: errorDescription,
  });
};
