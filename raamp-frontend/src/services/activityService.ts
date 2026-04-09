import { apiClient } from './api';

export interface ActivityEvent {
    id: string;
    business_id: string;
    event_type: 'post_published' | 'heat_spike' | 'scan_completed' | 'insight_updated' | 'trend_detected';
    title: string;
    subtitle: string;
    created_at: string;
}

class ActivityService {
    /**
     * Get activity feed for a business
     * @param businessId business ID (or user identifier)
     * @param limit maximum items to return
     */
    async getActivityFeed(businessId: string, limit: number = 10): Promise<ActivityEvent[]> {
        return apiClient.get<ActivityEvent[]>(`/activity/${businessId}?limit=${limit}`);
    }
}

export const activityService = new ActivityService();
