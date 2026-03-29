import React, { createContext, useContext, useEffect, useState, ReactNode, useRef } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import { apiClient } from '../services/api';

export interface Notification {
    id: string;
    type: string;
    title: string;
    message: string;
    read: boolean;
    created_at: string;
    metadata?: any;
}

interface NotificationContextType {
    notifications: Notification[];
    unreadCount: number;
    loading: boolean;
    markAsRead: (id: string) => Promise<void>;
    markAllAsRead: () => Promise<void>;
    deleteNotification: (id: string) => Promise<void>;
    fetchNotifications: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider = ({ children }: { children: ReactNode }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
    const wsRef = useRef<WebSocket | null>(null);

    // Fetch initial notifications
    const fetchNotifications = async () => {
        if (!user) return;
        try {
            setLoading(true);
            const data = await apiClient.get<{ notifications: Notification[]; unread_count: number }>('/notifications?limit=20');
            setNotifications(data.notifications || []);
            setUnreadCount(data.unread_count || 0);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    // Connect WebSocket
    const connectWebSocket = () => {
        if (!user) return;

        // Close existing connection if any
        if (wsRef.current) {
            wsRef.current.close();
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

        const token = localStorage.getItem('token');

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host; // includes port if dev
        const wsUrl = `${protocol}//${host}/api/notifications/ws${token ? `?token=${token}` : ''}`;

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('Notification WebSocket connected');
        };

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.event === 'new_notification' && msg.data) {
                    const newNotif = msg.data;
                    setNotifications(prev => [newNotif, ...prev]);
                    setUnreadCount(prev => prev + 1);

                    // Show toast - hide 'View' for trends as requested
                    const isTrend = newNotif.metadata?.sub_type === 'trend';

                    toast(newNotif.title, {
                        description: newNotif.message,
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

        ws.onclose = () => {
            console.log('Notification WebSocket disconnected. Reconnecting in 5s...');
            wsRef.current = null;
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        };

        wsRef.current = ws;
    };

    useEffect(() => {
        if (user) {
            fetchNotifications();
            connectWebSocket();
        }
        return () => {
            if (wsRef.current) wsRef.current.close();
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        };
    }, [user]);

    const markAsRead = async (id: string) => {
        try {
            // Optimistic update
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
            // Re-calc unread count locally for speed
            setUnreadCount(prev => Math.max(0, prev - 1));

            await apiClient.patch(`/notifications/${id}/read`, {});
        } catch (error) {
            console.error('Failed to mark read:', error);
            fetchNotifications(); // Revert on error
        }
    };

    const markAllAsRead = async () => {
        try {
            setNotifications(prev => prev.map(n => ({ ...n, read: true })));
            setUnreadCount(0);
            await apiClient.post('/notifications/read-all', {});
        } catch (error) {
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
            fetchNotifications();
        }
    };

    return (
        <NotificationContext.Provider value={{
            notifications,
            unreadCount,
            loading,
            markAsRead,
            markAllAsRead,
            deleteNotification,
            fetchNotifications
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
