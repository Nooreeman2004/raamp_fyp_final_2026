import React, { useState, useEffect, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import {
    Loader2,
    Upload,
    Image as ImageIcon,
    Video,
    CheckCircle2,
    AlertCircle,
    X,
    Sparkles,
    Instagram,
    Facebook,
    Zap,
    Clock,
    Smartphone,
    Calendar as CalendarIcon
} from "lucide-react";
import { PostMode } from "@/types/instagram.types";
import { instagramService } from "@/services/instagramService";
import { facebookService } from "@/services/facebookService";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { format, addHours, startOfHour } from "date-fns";
import { SocialConnectionStatus } from "@/types/instagram.types";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const postFormSchema = z.object({
    mode: z.enum([PostMode.POST_NOW, PostMode.SCHEDULE_POST, PostMode.POST_STORY]),
    platform: z.enum(["instagram", "facebook", "both"]), // Added facebook only option
    media_url: z.string().url("Please provide a valid media URL").min(1, "Media is required"),
    caption: z.string().max(2200, "Caption must be less than 2200 characters").optional(),
    scheduled_date: z.date().optional(),
    scheduled_time: z.string().optional(),
}).refine((data) => {
    if (data.mode === PostMode.SCHEDULE_POST) {
        return !!data.scheduled_date && !!data.scheduled_time;
    }
    return true;
}, {
    message: "Date and time are required for scheduling",
    path: ["scheduled_date"],
});

type PostFormValues = z.infer<typeof postFormSchema>;

interface EnhancedPostCreatorPanelProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
}

export const EnhancedPostCreatorPanel: React.FC<EnhancedPostCreatorPanelProps> = ({
    open,
    onOpenChange,
    onSuccess,
}) => {
    const [showDiscardConfirm, setShowDiscardConfirm] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [localPreview, setLocalPreview] = useState<string | null>(null);
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [optimizationBadge, setOptimizationBadge] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<SocialConnectionStatus | null>(null);

    const form = useForm<PostFormValues>({
        resolver: zodResolver(postFormSchema),
        defaultValues: {
            mode: PostMode.POST_NOW,
            platform: "instagram",
            media_url: "",
            caption: "",
            scheduled_time: "12:00",
        },
    });

    const selectedFile = React.useRef<File | null>(null);
    const caption = form.watch("caption");
    const mode = form.watch("mode");
    const scheduledDate = form.watch("scheduled_date");
    const scheduledTime = form.watch("scheduled_time");
    const mediaUrl = form.watch("media_url");
    const platform = form.watch("platform");

    // Calculate if the scheduled time is in the future
    const isFutureTime = React.useMemo(() => {
        if (mode !== PostMode.SCHEDULE_POST || !scheduledDate || !scheduledTime) return true;

        try {
            const [hours, minutes] = scheduledTime.split(':').map(Number);
            const date = new Date(scheduledDate);
            date.setHours(hours, minutes, 0, 0);
            return date > new Date();
        } catch (e) {
            return false;
        }
    }, [mode, scheduledDate, scheduledTime]);

    // Get formatted timezone string (e.g., GMT+5)
    const timezoneOffset = React.useMemo(() => {
        const offset = new Date().getTimezoneOffset();
        const absOffset = Math.abs(offset);
        const hours = Math.floor(absOffset / 60);
        const sign = offset <= 0 ? "+" : "-";
        return `GMT${sign}${hours}`;
    }, []);

    // Fetch connection status on mount
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const status = await instagramService.getSocialConnectionStatus();
                setConnectionStatus(status);
            } catch (error) {
                console.error("Failed to fetch social connection status:", error);
            }
        };
        if (open) {
            fetchStatus();
        }
    }, [open]);

    // Reset platform if mode is story (as FB stories aren't supported)
    useEffect(() => {
        if (mode === PostMode.POST_STORY && (platform === "both" || platform === "facebook")) {
            form.setValue("platform", "instagram");
        }
    }, [mode, platform, form]);

    // Reset state when modal closes
    useEffect(() => {
        if (!open) {
            form.reset({
                mode: PostMode.POST_NOW,
                platform: "instagram",
                media_url: "",
                caption: "",
                scheduled_time: "12:00",
            });
            setLocalPreview(null);
            setUploadStatus('idle');
            setOptimizationBadge(false);
            setErrorMessage(null);
            selectedFile.current = null;
        }
    }, [open, form]);

    const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploadStatus('idle');
        setOptimizationBadge(false);
        setErrorMessage(null);
        form.setValue("media_url", "");

        if (file.size > 10 * 1024 * 1024) {
            toast.error("File size must be less than 10MB");
            return;
        }

        selectedFile.current = file;

        const reader = new FileReader();
        reader.onload = (event) => {
            setLocalPreview(event.target?.result as string);
        };
        reader.readAsDataURL(file);

        try {
            setIsUploading(true);
            setUploadStatus('uploading');

            const response = await instagramService.uploadMedia(file);

            if (response.cloudinary_url || response.public_url) {
                form.setValue("media_url", response.cloudinary_url || response.public_url, { shouldValidate: true });
                setUploadStatus('success');

                if (response.is_auto_cropped || (response.transformed_dims && response.transformed_dims.target === 'instagram')) {
                    setOptimizationBadge(true);
                }

                toast.success("Media uploaded successfully");
            } else {
                throw new Error("Invalid response from server");
            }
        } catch (error: any) {
            setUploadStatus('error');
            setErrorMessage(error.message || "Upload failed. Please try again.");
            toast.error(error.message || "Failed to upload media");
        } finally {
            setIsUploading(false);
        }
    }, [form]);

    const onSubmit = async (values: PostFormValues) => {
        // Double-click prevention logic
        if (isSubmitting) {
            toast.info("Post is in progress...", {
                icon: <Loader2 className="w-4 h-4 animate-spin" />,
                duration: 2000
            });
            return;
        }

        try {
            setIsSubmitting(true);

            // Append optimization note if applicable
            const finalCaption = optimizationBadge
                ? `${values.caption || ""}\n\n(Automatic Optimization)`.trim()
                : values.caption;

            // Handle scheduling time format
            let finalizedScheduledTime = undefined;
            if (values.mode === PostMode.SCHEDULE_POST && values.scheduled_date && values.scheduled_time) {
                const [hours, minutes] = values.scheduled_time.split(':').map(Number);
                const date = new Date(values.scheduled_date);
                date.setHours(hours, minutes, 0, 0);

                if (date <= new Date()) {
                    toast.error("Scheduled time must be in the future");
                    setIsSubmitting(false);
                    return;
                }

                finalizedScheduledTime = date.toISOString();
            }

            // Perform Unified Submission
            const response = await instagramService.unifiedPost({
                platform: values.platform as any,
                mode: values.mode,
                media_url: values.media_url,
                caption: finalCaption,
                scheduled_time: finalizedScheduledTime,
                facebook_page_id: connectionStatus?.facebook_details?.page_id
            });

            if (response.success) {
                toast.success(`Success! Post ${values.mode === PostMode.SCHEDULE_POST ? "scheduled" : "published"}.`, {
                    description: response.message,
                });
                onOpenChange(false);
                onSuccess?.();
            } else {
                const errors = response.results.filter(r => r.status === "failed").map(r => `${r.platform}: ${r.error}`);
                setUploadStatus('error');
                setErrorMessage(errors.join(" | "));
                toast.error("Submission failed", {
                    description: errors.join(", "),
                });
            }
        } catch (error: any) {
            setUploadStatus('error');
            setErrorMessage(error.message || "An error occurred while processing your request");
            toast.error(error.message || "Failed to create post. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const isReadyToSubmit = !!mediaUrl && uploadStatus === 'success' &&
        (mode !== PostMode.SCHEDULE_POST || (!!scheduledDate && !!scheduledTime && isFutureTime));

    const isDirty = !!mediaUrl || !!caption || mode !== PostMode.POST_NOW;

    const handleDiscardClick = () => {
        if (isDirty) {
            setShowDiscardConfirm(true);
        } else {
            onOpenChange(false);
        }
    };

    const confirmDiscard = () => {
        form.reset({
            platform: "instagram",
            mode: PostMode.POST_NOW,
            media_url: "",
            caption: "",
            scheduled_date: new Date(),
            scheduled_time: format(addHours(startOfHour(new Date()), 1), "HH:mm")
        });
        setLocalPreview(null);
        setUploadStatus('idle');
        setOptimizationBadge(null);
        selectedFile.current = null;
        setShowDiscardConfirm(false);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={(val) => {
            // Only allow closing via states, not via outside interaction if submitting
            if (!val && !isSubmitting) {
                // If it's a close request (val is false), we check if we should block it
                // and instead show discard confirm if dirty? 
                // BUT the requirements say "dont do it until user discards".
                // Let's just block the Dialog's native onOpenChange from closing it directly
                // and rely on our Discard button.
            }
        }}>
            <DialogContent
                onInteractOutside={(e) => e.preventDefault()}
                onEscapeKeyDown={(e) => e.preventDefault()}
                className="sm:max-w-[600px] bg-[#0A0A0B]/95 border-[#00E0D0]/30 backdrop-blur-xl text-white p-0 overflow-hidden shadow-[0_0_40px_rgba(0,224,208,0.15)]"
            >
                <div className="absolute top-0 right-0 w-32 h-32 bg-[#00E0D0]/5 blur-[80px] -z-10" />
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-blue-500/5 blur-[80px] -z-10" />
                <div className="p-6">
                    <DialogHeader className="mb-6">
                        <DialogTitle className="text-xl font-bold flex items-center gap-2">
                            {mode === PostMode.POST_STORY ? <Smartphone className="w-5 h-5 text-purple-500" /> : <ImageIcon className="w-5 h-5 text-primary" />}
                            Create Social Media Post
                        </DialogTitle>
                        <DialogDescription className="text-gray-400">
                            Build, optimize, and schedule your content across platforms.
                        </DialogDescription>
                    </DialogHeader>

                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                            {/* Platform and Mode Row */}
                            <div className="grid grid-cols-2 gap-4">
                                <FormField
                                    control={form.control}
                                    name="platform"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-xs font-bold uppercase tracking-widest text-gray-500">Platform</FormLabel>
                                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                <FormControl>
                                                    <SelectTrigger className="bg-[#141416] border-white/10 h-10">
                                                        <SelectValue placeholder="Platform" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent className="bg-[#141416] border-white/10 text-white">
                                                    <SelectItem value="instagram">
                                                        <div className="flex items-center gap-2">
                                                            <Instagram className="w-3.5 h-3.5 text-pink-400" />
                                                            Instagram
                                                        </div>
                                                    </SelectItem>
                                                    <SelectItem value="facebook" disabled={mode === PostMode.POST_STORY}>
                                                        <div className="flex items-center gap-2">
                                                            <Facebook className="w-3.5 h-3.5 text-blue-500" />
                                                            Facebook
                                                        </div>
                                                    </SelectItem>
                                                    <SelectItem value="both" disabled={mode === PostMode.POST_STORY}>
                                                        <div className="flex items-center gap-2">
                                                            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                                                            IG + Facebook
                                                            {mode === PostMode.POST_STORY && <span className="text-[10px] opacity-40 ml-1 uppercase">(IG Only)</span>}
                                                        </div>
                                                    </SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                <FormField
                                    control={form.control}
                                    name="mode"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-xs font-bold uppercase tracking-widest text-gray-500">Post Type</FormLabel>
                                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                <FormControl>
                                                    <SelectTrigger className="bg-[#141416] border-white/10 h-10">
                                                        <SelectValue placeholder="Mode" />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent className="bg-[#141416] border-white/10 text-white">
                                                    <SelectItem value={PostMode.POST_NOW}>
                                                        <div className="flex items-center gap-2">
                                                            <Zap className="w-3.5 h-3.5 text-yellow-500" />
                                                            Post Now
                                                        </div>
                                                    </SelectItem>
                                                    <SelectItem value={PostMode.SCHEDULE_POST}>
                                                        <div className="flex items-center gap-2">
                                                            <Clock className="w-3.5 h-3.5 text-blue-500" />
                                                            Schedule
                                                        </div>
                                                    </SelectItem>
                                                    <SelectItem value={PostMode.POST_STORY}>
                                                        <div className="flex items-center gap-2">
                                                            <Smartphone className="w-3.5 h-3.5 text-purple-500" />
                                                            Story
                                                        </div>
                                                    </SelectItem>
                                                </SelectContent>
                                            </Select>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            {/* Multimedia Area */}
                            <div className="space-y-3">
                                <FormLabel className="text-xs font-bold uppercase tracking-widest text-gray-500">Media Content</FormLabel>
                                <div
                                    className={cn(
                                        "relative border-2 border-dashed rounded-xl transition-all h-56 flex flex-col items-center justify-center gap-3 overflow-hidden",
                                        uploadStatus === 'error' ? "border-red-500/30 bg-red-500/5" :
                                            uploadStatus === 'success' ? "border-[#00E0D0]/30 bg-[#00E0D0]/5" :
                                                "border-white/5 bg-[#141416] hover:bg-[#1A1A1C]"
                                    )}
                                >
                                    {localPreview ? (
                                        <>
                                            <div className="absolute inset-0 z-0">
                                                {selectedFile.current?.type.startsWith('video/') ? (
                                                    <video src={localPreview} className="w-full h-full object-contain" />
                                                ) : (
                                                    <img src={localPreview} className="w-full h-full object-contain" alt="Preview" />
                                                )}
                                            </div>

                                            {isUploading && (
                                                <div className="absolute inset-0 bg-black/60 z-10 flex flex-col items-center justify-center gap-3 backdrop-blur-sm">
                                                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                                                    <div className="text-sm font-medium animate-pulse text-white/80 tracking-tight">Automatic Optimization...</div>
                                                </div>
                                            )}

                                            {!isSubmitting && (
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setLocalPreview(null);
                                                        setUploadStatus('idle');
                                                        form.setValue("media_url", "");
                                                        selectedFile.current = null;
                                                    }}
                                                    className="absolute top-3 right-3 z-20 p-1.5 bg-black/50 backdrop-blur-md rounded-full hover:bg-red-500/80 transition-all border border-white/10"
                                                >
                                                    <X className="w-3.5 h-3.5" />
                                                </button>
                                            )}
                                        </>
                                    ) : (
                                        <>
                                            <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10">
                                                <Upload className="w-7 h-7 text-primary" />
                                            </div>
                                            <div className="text-center px-4">
                                                <div className="font-bold text-sm tracking-tight text-white/90">Click or Drag to Upload</div>
                                                <div className="text-[10px] text-gray-500 mt-1 uppercase font-black">
                                                    HQ Image/Video • Max 10MB
                                                </div>
                                            </div>
                                            <input
                                                type="file"
                                                className="absolute inset-0 opacity-0 cursor-pointer"
                                                accept="image/*,video/*"
                                                onChange={handleFileChange}
                                            />
                                        </>
                                    )}
                                </div>

                                {/* Status Indicators */}
                                <div className="flex flex-wrap gap-2 min-h-[28px]">
                                    {uploadStatus === 'success' && (
                                        <Badge variant="outline" className="bg-[#00E0D0]/5 text-[#00E0D0] border-[#00E0D0]/20 gap-1.5 px-2.5 py-1 text-[10px] uppercase font-black tracking-widest">
                                            <CheckCircle2 className="w-3 h-3" />
                                            Media uploaded & ready
                                        </Badge>
                                    )}
                                    {optimizationBadge && (
                                        <Badge variant="outline" className="bg-[#00E0D0]/5 text-[#00E0D0] border-[#00E0D0]/20 gap-1.5 px-2.5 py-1 text-[10px] uppercase font-black tracking-widest">
                                            <Sparkles className="w-3 h-3" />
                                            Optimized for Instagram
                                        </Badge>
                                    )}
                                    {uploadStatus === 'error' && (
                                        <Badge variant="destructive" className="gap-1.5 px-2.5 py-1 text-[10px] uppercase font-black tracking-widest bg-red-500/10 text-red-500 border-red-500/20">
                                            <AlertCircle className="w-3 h-3" />
                                            {errorMessage || "Internal Request Error"}
                                        </Badge>
                                    )}
                                </div>
                            </div>

                            {/* Scheduling Section */}
                            {mode === PostMode.SCHEDULE_POST && (
                                <div className="grid grid-cols-12 gap-4 p-4 rounded-xl bg-[#00E0D0]/5 border border-[#00E0D0]/10 items-end">
                                    <div className="col-span-7">
                                        <FormField
                                            control={form.control}
                                            name="scheduled_date"
                                            render={({ field }) => (
                                                <FormItem className="flex flex-col gap-1.5">
                                                    <FormLabel className="text-[10px] font-black uppercase tracking-widest text-[#00E0D0]/70 py-0.5">Pick Date</FormLabel>
                                                    <Popover>
                                                        <PopoverTrigger asChild>
                                                            <FormControl>
                                                                <Button
                                                                    variant={"outline"}
                                                                    className={cn(
                                                                        "w-full h-11 bg-[#141416] border-white/5 pl-3 text-left font-normal",
                                                                        !field.value && "text-muted-foreground"
                                                                    )}
                                                                >
                                                                    {field.value ? (
                                                                        format(field.value, "PPP")
                                                                    ) : (
                                                                        <span className="text-xs italic opacity-40">Choose Date</span>
                                                                    )}
                                                                    <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                                                </Button>
                                                            </FormControl>
                                                        </PopoverTrigger>
                                                        <PopoverContent className="w-auto p-0 bg-[#0A0A0B] border-white/10" align="start">
                                                            <Calendar
                                                                mode="single"
                                                                selected={field.value}
                                                                onSelect={field.onChange}
                                                                disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
                                                                initialFocus
                                                            />
                                                        </PopoverContent>
                                                    </Popover>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>

                                    <div className="col-span-12 md:col-span-5">
                                        <FormField
                                            control={form.control}
                                            name="scheduled_time"
                                            render={({ field }) => (
                                                <FormItem className="flex flex-col gap-1.5">
                                                    <div className="flex justify-between items-center">
                                                        <FormLabel className="text-[10px] font-black uppercase tracking-widest text-[#00E0D0]/70 py-0.5">Set Time</FormLabel>
                                                        <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">{timezoneOffset}</span>
                                                    </div>
                                                    <FormControl>
                                                        <input
                                                            type="time"
                                                            className={cn(
                                                                "w-full h-11 bg-[#141416] border border-white/5 rounded-md px-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#00E0D0]/50 transition-all text-white/90",
                                                                !isFutureTime && mode === PostMode.SCHEDULE_POST && "border-red-500/50 text-red-400"
                                                            )}
                                                            {...field}
                                                        />
                                                    </FormControl>
                                                    {!isFutureTime && mode === PostMode.SCHEDULE_POST && (
                                                        <p className="text-[9px] text-red-500 font-bold uppercase tracking-widest">Time must be in future</p>
                                                    )}
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Caption Section */}
                            <FormField
                                control={form.control}
                                name="caption"
                                render={({ field }) => (
                                    <FormItem>
                                        <div className="flex items-center justify-between mb-2">
                                            <FormLabel className="text-xs font-bold uppercase tracking-widest text-gray-500">Caption / Strategy</FormLabel>
                                            <span className="text-[9px] font-black uppercase tracking-tighter text-gray-600">
                                                {caption?.length || 0} / 2200 Chars
                                            </span>
                                        </div>
                                        <FormControl>
                                            <Textarea
                                                placeholder="What's the story behind this post? Use hashtags for better reach..."
                                                className="min-h-[100px] bg-[#141416] border-white/5 border-b-2 focus:border-b-primary transition-all resize-none shadow-inner"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            {/* Final Actions */}
                            <div className="flex gap-4 pt-4 border-t border-white/5">
                                <Button
                                    type="button"
                                    variant="ghost"
                                    onClick={handleDiscardClick}
                                    className="flex-1 h-12 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-white"
                                    disabled={isSubmitting}
                                >
                                    Discard
                                </Button>
                                <Button
                                    type="submit"
                                    onClick={() => {
                                        if (isSubmitting) {
                                            toast.info("Post is in progress...", {
                                                icon: <Loader2 className="w-4 h-4 animate-spin" />,
                                                duration: 2000
                                            });
                                        }
                                    }}
                                    className={cn(
                                        "flex-1 h-12 text-xs font-black uppercase tracking-widest transition-all shadow-xl",
                                        mode === PostMode.SCHEDULE_POST ? "bg-[#00E0D0] hover:bg-[#00E0D0]/90 text-black" : "bg-primary hover:bg-primary/90 text-black"
                                    )}
                                    disabled={!isReadyToSubmit}
                                >
                                    {isSubmitting ? (
                                        <div className="flex items-center gap-2">
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span>Processing...</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center justify-center gap-2">
                                            {mode === PostMode.SCHEDULE_POST ? <Clock className="w-4 h-4" /> : <Zap className="w-4 h-4 fill-current" />}
                                            {mode === PostMode.SCHEDULE_POST ? "Schedule Content" : "Post Content Now"}
                                        </div>
                                    )}
                                </Button>
                            </div>
                        </form>
                    </Form>
                </div>
            </DialogContent>

            <AlertDialog open={showDiscardConfirm} onOpenChange={setShowDiscardConfirm}>
                <AlertDialogContent className="bg-[#0A0A0B] border-white/10 text-white">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Discard changes?</AlertDialogTitle>
                        <AlertDialogDescription className="text-gray-400">
                            You have unsaved changes. Are you sure you want to discard this post? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel className="bg-white/5 border-white/10 hover:bg-white/10 text-white">Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={confirmDiscard}
                            className="bg-red-500 hover:bg-red-600 text-white border-none"
                        >
                            Discard Post
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </Dialog>
    );
};
