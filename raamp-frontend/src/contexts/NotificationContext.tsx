import { createContext, useContext, useEffect, useState, ReactNode, useRef } from 'react';
import { toast } from 'sonner';
import { MESSAGES } from '@/constants/messages';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/services/api';
import { API_BASE_URL } from '@/config/apiBase';
import { isAuthError } from '@/utils/errorHandler';

export interface Notification {
    id: string;
    type: string;
    title: string;
    message: string;
    read: boolean;
    priority?: number;
    created_at: string;
    metadata?: any;
}

interface NotificationContextType {
    notifications: Notification[];
    unreadCount: number;
    loading: boolean;
    loadingMore: boolean;
    hasMore: boolean;
    unreadOnly: boolean;
    setUnreadOnly: (v: boolean) => void;
    markAsRead: (id: string) => Promise<void>;
    markAllAsRead: () => Promise<void>;
    deleteNotification: (id: string) => Promise<void>;
    clearAllNotifications: () => Promise<void>;
    fetchNotifications: (opts?: { limit?: number; offset?: number; append?: boolean; unread_only?: boolean }) => Promise<void>;
    loadMore: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider = ({ children }: { children: ReactNode }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [unreadOnly, setUnreadOnly] = useState(false);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
    const wsRef = useRef<WebSocket | null>(null);
    const pingIntervalRef = useRef<number | null>(null);
    const shouldReconnectRef = useRef(true);
    const intentionalCloseRef = useRef(false);
    const wsWarnedAtRef = useRef<number>(0);
    const wsConnectedOnceRef = useRef(false);
    const pageSizeRef = useRef<number>(20);

    // Fetch initial notifications
    const fetchNotifications = async (opts?: { limit?: number; offset?: number; append?: boolean; unread_only?: boolean }) => {
        // Don't fetch if user is not logged in
        if (!user) {
            console.log('[NotificationContext] Skipping fetch - no user');
            return;
        }
        
        try {
            const limit = Math.max(1, Math.min(Number(opts?.limit ?? pageSizeRef.current), 100));
            const offset = Math.max(0, Number(opts?.offset ?? 0));
            const append = Boolean(opts?.append);
            const unread_only = (opts?.unread_only ?? unreadOnly) ? "true" : "false";
            if (append) setLoadingMore(true);
            else setLoading(true);

            const qs = new URLSearchParams();
            qs.set("limit", String(limit));
            qs.set("offset", String(offset));
            qs.set("unread_only", unread_only);
            const data = await apiClient.get<{ notifications: Notification[]; unread_count: number }>(`/notifications?${qs.toString()}`);
            const list = Array.isArray(data?.notifications) ? data.notifications : [];
            setNotifications(prev => append ? [...prev, ...list] : list);
            setUnreadCount(data.unread_count || 0);
            setHasMore(list.length >= limit);
        } catch (error: any) {
            console.error('Failed to fetch notifications:', error);
            // Only show toast if it's not an auth error (401) and user is still logged in
            const isAuthError = error?.status === 401 || error?.message?.toLowerCase().includes('authentication');
            if (user && !isAuthError) {
                toast.message("Notifications unavailable", {
                    description: "We couldn't load your notifications right now. Retrying in the background.",
                    duration: 4000,
                });
            }
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    // Connect WebSocket
    const connectWebSocket = () => {
        if (!user) {
            console.log('[NotificationContext] Skipping WebSocket - no user');
            return;
        }

        // Close existing connection if any
        if (wsRef.current) {
            intentionalCloseRef.current = true;
            wsRef.current.close();
        }
        if (pingIntervalRef.current) {
            window.clearInterval(pingIntervalRef.current);
            pingIntervalRef.current = null;
        }
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = undefined;
        }

        // Attempt to get token (from cookie usually, but here we depend on auth context or browser handling cookies)
        // Since our backend router expects ?token=..., we might need to extract it or assume standard cookie auth if WS supports it.
        // However, the standard WebSocket API doesn't allow setting custom headers easily. 
        // We will rely on the cookie if the backend reads it from the Upgrade request.
        // BUT the backend implementation I wrote checks `token` query param specifically.
        // Let's assume for now we might fail auth if we don't pass the token. 
        // Ideally useAuth exposes `token`. If not, we might need to fetch it.

        // For this implementation, I will attempt to connect WITHOUT token param first, 
        // relying on the browser sending the `access_token` cookie automatically. 
        // If backend logic fails, I will need to update backend to parse cookie.

        // UPDATE: Backend implementation DOES rely on token param.
        // I need to get the token. 
        // `useAuth` usually stores it? If not, we are in trouble.
        // Let's assume we can get it from a cookie utility or localStorage if saved there.

        const token = localStorage.getItem('token') || sessionStorage.getItem('token');

        // Use API_BASE_URL and convert http(s) protocol to ws(s)
        const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/notifications/ws' + (token ? `?token=${token}` : '');

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('Notification WebSocket connected');
            intentionalCloseRef.current = false;
            wsConnectedOnceRef.current = true;
            // Keepalive: backend waits on receive_text(); this prevents idle proxy timeouts.
            pingIntervalRef.current = window.setInterval(() => {
                try {
                    if (ws.readyState === WebSocket.OPEN) ws.send("ping");
                } catch {
                    // ignore
                }
            }, 25000);
        };

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.event === 'new_notification' && msg.data) {
                    const newNotif = msg.data;
                    setNotifications(prev => {
                        const merged = [newNotif, ...prev];
                        // Keep UI ordering stable: priority desc, then created_at desc.
                        return merged.sort((a: any, b: any) => {
                            const ap = Number(a?.priority ?? 0);
                            const bp = Number(b?.priority ?? 0);
                            if (bp !== ap) return bp - ap;
                            const at = new Date(a?.created_at ?? 0).getTime();
                            const bt = new Date(b?.created_at ?? 0).getTime();
                            return bt - at;
                        });
                    });
                    setUnreadCount(prev => prev + 1);

                    // Show toast - hide 'View' for trends as requested
                    const subType = newNotif.metadata?.sub_type;
                    const isTrend = subType === 'trend' || subType === 'trend_discovered';

                    toast(newNotif.title, {
                        description: newNotif.message,
                        duration: 5000,
                        action: isTrend ? undefined : {
                            label: 'View',
                            onClick: () => window.location.href = '/notifications'
                        }
                    });
                }
            } catch (err) {
                console.error('WS Message parsing error', err);
            }
        };

        ws.onerror = (err) => {
            console.warn('Notification WebSocket error', err);
        };

        ws.onclose = (ev) => {
            console.log('Notification WebSocket disconnected. Reconnecting in 5s...', {
                code: ev.code,
                reason: ev.reason,
                wasClean: ev.wasClean,
            });
            wsRef.current = null;
            if (pingIntervalRef.current) {
                window.clearInterval(pingIntervalRef.current);
                pingIntervalRef.current = null;
            }
            // In React 18 dev StrictMode, effects mount->cleanup->mount, which can
            // intentionally close the socket once right after connecting.
            // Also avoid reconnecting when we explicitly closed the socket (switch user, unmount, etc.).
            if (!shouldReconnectRef.current || intentionalCloseRef.current) return;

            // User-facing notice (rate-limited) when realtime disconnects
            const now = Date.now();
            const shouldToast = wsConnectedOnceRef.current && (now - wsWarnedAtRef.current) > 60_000;
            if (shouldToast) {
                wsWarnedAtRef.current = now;
                toast.message("Realtime notifications disconnected", {
                    description: "We're reconnecting in the background.",
                    duration: 4000,
                });
            }
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        };

        wsRef.current = ws;
    };

    useEffect(() => {
        if (user) {
            shouldReconnectRef.current = true;
            fetchNotifications({ limit: pageSizeRef.current, offset: 0, append: false, unread_only: unreadOnly });
            connectWebSocket();
        }
        return () => {
            shouldReconnectRef.current = false;
            if (wsRef.current) wsRef.current.close();
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (pingIntervalRef.current) window.clearInterval(pingIntervalRef.current);
        };
    }, [user]);

    // When unreadOnly changes, refetch from start.
    useEffect(() => {
        if (!user) return;
        void fetchNotifications({ limit: pageSizeRef.current, offset: 0, append: false, unread_only: unreadOnly });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [unreadOnly]);

    const markAsRead = async (id: string) => {
        try {
            // Optimistic update
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
            // Re-calc unread count locally for speed
            setUnreadCount(prev => Math.max(0, prev - 1));

            await apiClient.patch(`/notifications/${id}/read`, {});
        } catch (error) {
            console.error('Failed to mark read:', error);
            toast.error("Update Failed", { description: MESSAGES.NOTIFICATIONS.UPDATE_FAILED, duration: 4000 });
            fetchNotifications(); // Revert on error
        }
    };

    const markAllAsRead = async () => {
        try {
            setNotifications(prev => prev.map(n => ({ ...n, read: true })));
            setUnreadCount(0);
            await apiClient.post('/notifications/read-all', {});
        } catch (error) {
            toast.error("Mark All Read Failed", { description: MESSAGES.NOTIFICATIONS.MARK_ALL_READ_FAILED, duration: 4000 });
            fetchNotifications();
        }
    };

    const deleteNotification = async (id: string) => {
        try {
            const target = notifications.find(n => n.id === id);
            setNotifications(prev => prev.filter(n => n.id !== id));
            if (target && !target.read) setUnreadCount(prev => Math.max(0, prev - 1));

            await apiClient.delete(`/notifications/${id}`);
        } catch (error) {
            toast.error("Delete Failed", { description: MESSAGES.NOTIFICATIONS.DELETE_FAILED, duration: 4000 });
            fetchNotifications();
        }
    };

    const clearAllNotifications = async () => {
        try {
            setNotifications([]);
            setUnreadCount(0);
            await apiClient.delete<{ success: boolean; deleted: number }>('/notifications/all');
        } catch (error) {
            console.error('Failed to clear notifications:', error);
            await fetchNotifications();
            throw error;
        }
    };

    const loadMore = async () => {
        if (loading || loadingMore) return;
        if (!hasMore) return;
        await fetchNotifications({ limit: pageSizeRef.current, offset: notifications.length, append: true, unread_only: unreadOnly });
    };

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            loading,
            loadingMore,
            hasMore,
            unreadOnly,
            setUnreadOnly,
            markAsRead,
            markAllAsRead,
            deleteNotification,
            clearAllNotifications,
            fetchNotifications,
            loadMore,
        }}>
            {children}
        </NotificationContext.Provider>
    );
};

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (context === undefined) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};
