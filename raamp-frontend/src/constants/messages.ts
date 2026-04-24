/**
 * Centralized User-Facing Messages
 * 
 * Guidelines:
 * - Titles: Title Case, no period
 * - Descriptions: Sentence case, with period
 * - Short messages: Title Case, no period
 * - Use actionable language ("Try X" not "X failed")
 */

export const MESSAGES = {
  // Authentication & Session
  AUTH: {
    LOGOUT_SUCCESS: "You've been logged out successfully.",
    LOGIN_REQUIRED: "Please log in to continue.",
    SESSION_EXPIRED: "Your session has expired. Please log in again.",
    IDENTITY_VERIFIED: "Identity verified successfully.",
    PASSWORD_UPDATED: "Your password has been updated successfully.",
    PASSWORD_UPDATE_FAILED: "Could not update password. Please check your current password and try again.",
  },

  // Settings & Configuration
  SETTINGS: {
    SAVED: "Settings saved successfully.",
    SAVE_FAILED: "Could not save settings. Please try again.",
    AUTO_REPLY_UPDATED: "Auto-reply settings updated successfully.",
    AUTO_REPLY_UPDATE_FAILED: "Could not update settings. Please check your inputs and try again.",
  },

  // Assets & Media
  ASSETS: {
    UPLOADED: "Media uploaded successfully.",
    UPLOAD_FAILED: "Upload failed. Please check your file size and format.",
    SELECTED: "Asset selected from library.",
    REFRESH_FAILED: "Could not refresh assets. Check your connection and try again.",
    RESCAN_FAILED: "Could not rescan assets. Please try again.",
    LOAD_FAILED: "Could not load assets. Check your connection and try again.",
    COPY_SUCCESS: "Copied to clipboard.",
    COPY_FAILED: "Could not copy to clipboard. Try selecting and copying manually.",
    FAVORITE_UPDATED: "Favorite status updated successfully.",
    FAVORITE_UPDATE_FAILED: "Could not update favorite. Please try again.",
    DOWNLOAD_FAILED: "Download failed. Please try again.",
    DELETE_FAILED: "Could not delete asset. Please try again.",
  },

  // Captions & Content
  CAPTIONS: {
    LOAD_FAILED: "Could not load captions. Check your connection and try again.",
    COPY_SUCCESS: "Caption copied to clipboard.",
    PACKAGE_COPY_SUCCESS: "Package copied to clipboard.",
  },

  // Campaign Planning
  CAMPAIGN: {
    PLAN_GENERATED: "Campaign plan generated successfully.",
    PLAN_GENERATION_FAILED: "Could not generate campaign plan. Please try again.",
    DRAFT_CREATED: "Draft created successfully.",
    APPROVAL_REQUESTED: "Approval requested successfully.",
    LAUNCH_REQUEST_CREATED: "Launch request created successfully.",
  },

  // Scheduled Posts
  SCHEDULED: {
    POST_CANCELLED: "Scheduled post cancelled successfully.",
    CANCEL_FAILED: "Could not cancel post. Please try again.",
  },

  // Complaints & Support
  COMPLAINTS: {
    LOAD_FAILED: "Could not load complaints. Check your connection and try again.",
    NOT_FOUND: "Ticket not found. It may have been deleted.",
    LOADED: (ticketId: string) => `Ticket #${ticketId} loaded successfully.`,
    UPDATE_SUCCESS: "Ticket updated successfully.",
    UPDATE_FAILED: "Could not update ticket. Please try again.",
    RESOLVE_SUCCESS: "Ticket resolved successfully.",
    STATUS_UPDATE_SUCCESS: "Status updated successfully.",
  },

  // Auto Replies
  AUTO_REPLY: {
    LOAD_FAILED: "Could not load auto-replies. Please try again.",
    ESCALATION_LOAD_FAILED: "Could not load escalation ticket. Please try again.",
    ACKNOWLEDGE_FAILED: "Could not acknowledge. Please try again.",
    RESOLVE_FAILED: "Could not resolve. Please try again.",
    SEND_FAILED: "Could not send reply. Please try again.",
    SKIP_FAILED: "Could not skip. Please try again.",
    APPROVED: "Reply approved and sent successfully.",
  },

  // Notifications
  NOTIFICATIONS: {
    UPDATE_FAILED: "Could not update notification. Please try again.",
    MARK_ALL_READ_FAILED: "Could not mark all as read. Please try again.",
    DELETE_FAILED: "Could not delete notification. Please try again.",
  },

  // Posting & Deployment
  POSTING: {
    SUCCESS_POSTED: "Posted to Instagram successfully.",
    SUCCESS_SCHEDULED: "Scheduled to Instagram successfully.",
    DEPLOYMENT_SUCCESS: "Deployment successful.",
    DEPLOYMENT_FAILED: "Deployment failed. Please check your connection and try again.",
  },

  // Trends & Intelligence
  TRENDS: {
    SCAN_COMPLETED: "Scan completed successfully.",
    ASSETS_READY: "Ready to create assets.",
  },

  // Geo-Intent
  GEO: {
    FINDING_ZONES: "Finding best zones. This may take 1-2 minutes.",
    GENERATING_BRIEF: "Generating location brief.",
    PREPARING_META_DEPLOY: "Preparing Meta deployment brief.",
  },

  // Comments & Moderation
  COMMENTS: {
    DELETING: (count: number) => `Deleting ${count} comment${count !== 1 ? 's' : ''}...`,
    DELETED: (count: number) => `${count} comment${count !== 1 ? 's' : ''} deleted successfully.`,
    DELETE_FAILED: "Could not delete comments. Please try again.",
  },

  // Generic Messages
  GENERIC: {
    LOADING: "Loading...",
    SAVING: "Saving...",
    PROCESSING: "Processing...",
    UPLOADING: "Uploading...",
    SUCCESS: "Success.",
    ERROR: "An error occurred. Please try again.",
    CONNECTION_ERROR: "Connection error. Check your internet and try again.",
  },
} as const;

// Type-safe message keys
export type MessageCategory = keyof typeof MESSAGES;
export type MessageKey<T extends MessageCategory> = keyof typeof MESSAGES[T];
