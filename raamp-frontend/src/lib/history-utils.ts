import { format, formatDistanceToNow } from "date-fns";

/**
 * Maps raw backend error messages to user-friendly UI messages
 */
export const mapBackendErrorToUI = (error: string | undefined | null): string => {
    if (!error) return "Unknown error occurred";

    const errorLower = error.toLowerCase();

    if (errorLower.includes("session has been invalidated") ||
        errorLower.includes("validating access token") ||
        errorLower.includes("changed their password") ||
        errorLower.includes("error code: 190")) {
        return "Instagram session expired. Please reconnect your account in Integrations → Instagram.";
    }

    if (errorLower.includes("instagramconnectionmodel") && errorLower.includes("page_access_token")) {
        return "Instagram session expired. Please reconnect in Onboarding.";
    }

    if (errorLower.includes("not connected")) {
        return "Account not connected. Please connect first.";
    }

    if (errorLower.includes("token") || errorLower.includes("authentication") || errorLower.includes("unauthorized")) {
        return "Session expired. Please reconnect your account.";
    }

    if (errorLower.includes("permission") || errorLower.includes("scope")) {
        return "Missing permissions. Please re-authorize the app.";
    }

    if (errorLower.includes("rate limit") || errorLower.includes("too many requests")) {
        return "Instagram rate limit reached. Try again later.";
    }

    if (errorLower.includes("media") || errorLower.includes("url") || errorLower.includes("file")) {
        return "Invalid media file or URL. Please check your content.";
    }

    if (errorLower.includes("api") || errorLower.includes("meta") || errorLower.includes("facebook")) {
        return "Platform API error. Meta services might be down.";
    }

    if (errorLower.includes("validation") || errorLower.includes("invalid")) {
        return "Input validation failed. Please check your data.";
    }

    // Suppress Python stack traces or raw technical strings
    if (error.includes("Traceback") || error.includes("object at") || error.includes("\n  File")) {
        return "An unexpected error occurred. Our team has been notified.";
    }

    return error; // Return original if it seems readable enough or not matched
};

/**
 * Formats a timestamp into Absolute (Relative) format
 * Example: Feb 5, 7:41 PM (5 min ago)
 */
export const formatHistoryTimestamp = (dateStr: string): string => {
    try {
        // Defensive parsing: If no Z or +/- offset is present, treat as UTC
        let normalizedStr = dateStr;
        if (!dateStr.includes('Z') && !/[+-]\d{2}(:?\d{2})?$/.test(dateStr)) {
            normalizedStr = dateStr + 'Z';
        }

        const date = new Date(normalizedStr);
        const absolute = format(date, "MMM dd, h:mm a");
        const relative = formatDistanceToNow(date, { addSuffix: true });
        return `${absolute} (${relative})`;
    } catch (e) {
        return dateStr;
    }
};

/**
 * Gets the timezone string
 */
export const getTimezone = () => {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
};
