import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Bell, Check, Trash2, TrendingUp, DollarSign, AlertTriangle, Sparkles, CheckCheck, Search } from "lucide-react";
import { useState, useMemo } from "react";
import { toast as sonner } from "sonner";
import { useNotifications } from "@/contexts/NotificationContext";
import { LaunchCampaignDialog, LaunchCampaignPrefill } from "@/components/LaunchCampaignDialog";

// Animation Imports
import { motion, AnimatePresence } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { fadeInUp } from "@/utils/animations";

const Notifications = () => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, deleteNotification, clearAllNotifications, loading } = useNotifications();
  const [searchQuery, setSearchQuery] = useState("");
  const [launchOpen, setLaunchOpen] = useState(false);
  const [launchPrefill, setLaunchPrefill] = useState<LaunchCampaignPrefill | undefined>(undefined);

  // Filter notifications based on search query
  const filteredNotifications = useMemo(() => {
    if (!searchQuery.trim()) return notifications;
    
    const query = searchQuery.toLowerCase();
    return notifications.filter(
      (notification) =>
        notification.title.toLowerCase().includes(query) ||
        notification.message.toLowerCase().includes(query) ||
        notification.type.toLowerCase().includes(query)
    );
  }, [notifications, searchQuery]);

  const getIcon = (type: string) => {
    switch (type) {
      case "trend":
      case "trend_spike":
      case "trend_discovered":
        return <TrendingUp className="w-5 h-5" />;
      case "billing":
        return <DollarSign className="w-5 h-5" />;
      case "alert":
        return <AlertTriangle className="w-5 h-5" />;
      case "campaign":
        return <Sparkles className="w-5 h-5" />;
      case "system":
        return <CheckCheck className="w-5 h-5" />;
      default:
        return <Bell className="w-5 h-5" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "trend":
      case "trend_spike":
      case "trend_discovered":
        return "text-teal-500 bg-teal-500/10";
      case "billing":
        return "text-green-500 bg-green-500/10";
      case "alert":
        return "text-amber-500 bg-amber-500/10";
      case "campaign":
        return "text-purple-500 bg-purple-500/10";
      case "system":
        return "text-gray-500 bg-gray-500/10";
      default:
        return "text-primary bg-primary/10";
    }
  };

  const [clearingAll, setClearingAll] = useState(false);

  const handleClearAll = async () => {
    setClearingAll(true);
    try {
      await clearAllNotifications();
      sonner.success("All notifications cleared");
    } catch {
      sonner.error("Could not clear notifications");
    } finally {
      setClearingAll(false);
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Notifications" }]}>
      <motion.div
        className="space-y-6 max-w-3xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center relative">
                <Bell className="w-7 h-7 text-primary" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </div>
              <div>
                <h1 className="text-3xl font-bold">Notifications</h1>
                <p className="text-muted-foreground">
                  {unreadCount > 0
                    ? `You have ${unreadCount} unread notification${unreadCount > 1 ? "s" : ""}`
                    : "All caught up!"}
                </p>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap justify-end">
              {unreadCount > 0 && (
                <Button variant="outline" size="sm" onClick={() => markAllAsRead()}>
                  <CheckCheck className="w-4 h-4 mr-2" />
                  Mark All Read
                </Button>
              )}
              {notifications.length > 0 && (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm" disabled={clearingAll || loading}>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Clear All
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Clear all notifications?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This permanently removes every notification in your inbox. This cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        onClick={handleClearAll}
                      >
                        Clear all
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              )}
            </div>
          </div>
        </Reveal>

        {/* Search Bar */}
        <Reveal variant="fadeInUp">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search notifications by title, message, or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-foreground/5 border-border/50"
            />
          </div>
        </Reveal>

        <div className="space-y-3">
          <AnimatePresence>
            {loading && filteredNotifications.length === 0 ? (
              <div className="text-center py-10">Loading notifications...</div>
            ) : filteredNotifications.length === 0 ? (
              <Reveal variant="fadeInUp">
                <Card className="p-12 bg-card/70 backdrop-blur-sm border-primary/10 text-center">
                  <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">
                    {searchQuery ? "No Matching Notifications" : "No Notifications"}
                  </h3>
                  <p className="text-muted-foreground">
                    {searchQuery
                      ? "No notifications match your search criteria."
                      : "You're all caught up! New notifications will appear here."}
                  </p>
                </Card>
              </Reveal>
            ) : (
              filteredNotifications.map((notification, index) => (
                <motion.div
                  key={notification.id}
                  variants={fadeInUp}
                  initial="hidden"
                  animate="visible"
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={`p-4 bg-card/70 backdrop-blur-sm border-primary/10 transition-all ${!notification.read ? "border-l-4 border-l-primary" : ""
                      }`}
                  >
                    <div className="flex items-start gap-4">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${getTypeColor(
                          notification.type
                        )}`}
                      >
                        {getIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h3 className={`font-semibold ${!notification.read ? "text-foreground" : "text-muted-foreground"}`}>
                              {notification.title}
                            </h3>
                            <p className="text-sm text-muted-foreground mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-muted-foreground mt-2">
                              {new Date(notification.created_at).toLocaleString()}
                            </p>

                            {(notification.type === "trend_spike" || notification.metadata?.action === "launch_campaign") && (
                              <div className="mt-3">
                                <Button
                                  size="sm"
                                  className="bg-primary/20 hover:bg-primary text-primary hover:text-black border border-primary/50"
                                  onClick={() => {
                                    const md = notification.metadata || {};
                                    const pre = (md.campaign_prefill || {}) as any;
                                    setLaunchPrefill({
                                      trend_id: md.trend_id ?? md.related_entity_id ?? md.trend_signal_id ?? null,
                                      keyword: pre.keyword ?? md.keyword ?? null,
                                      niche: pre.niche ?? md.niche ?? null,
                                      location: pre.location ?? md.location ?? null,
                                      suggested_platforms: pre.suggested_platforms ?? [],
                                      hashtags: pre.hashtags ?? md.hashtags ?? [],
                                      lifecycle_stage: pre.lifecycle_stage ?? md.lifecycle_stage ?? null,
                                    });
                                    setLaunchOpen(true);
                                  }}
                                >
                                  Launch Campaign
                                </Button>
                              </div>
                            )}
                          </div>
                          <div className="flex gap-1 flex-shrink-0">
                            {!notification.read && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => markAsRead(notification.id)}
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                              onClick={() => deleteNotification(notification.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      <LaunchCampaignDialog open={launchOpen} onOpenChange={setLaunchOpen} prefill={launchPrefill} />
    </Layout>
  );
};

export default Notifications;
