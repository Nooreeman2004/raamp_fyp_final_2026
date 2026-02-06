import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
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
import { MediaUploadZone } from "@/components/ui/media-upload-zone";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { CalendarIcon, Zap, Clock, Smartphone, Loader2 } from "lucide-react";
import { PostMode } from "@/types/instagram.types";
import { instagramService } from "@/services/instagramService";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

const postFormSchema = z.object({
    mode: z.enum([PostMode.POST_NOW, PostMode.SCHEDULE_POST, PostMode.POST_STORY]),
    media_url: z.string().url("Please provide a valid media URL").min(1, "Media is required"),
    caption: z.string().max(2200, "Caption must be less than 2200 characters").optional(),
    scheduled_date: z.date().optional(),
    scheduled_time: z.string().optional(),
}).refine((data) => {
    if (data.mode === PostMode.SCHEDULE_POST) {
        return data.scheduled_date !== undefined && data.scheduled_time !== undefined;
    }
    return true;
}, {
    message: "Scheduled date and time are required for scheduled posts",
    path: ["scheduled_date"],
});

type PostFormValues = z.infer<typeof postFormSchema>;

interface PostCreatorPanelProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
}

export const PostCreatorPanel: React.FC<PostCreatorPanelProps> = ({
    open,
    onOpenChange,
    onSuccess,
}) => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const form = useForm<PostFormValues>({
        resolver: zodResolver(postFormSchema),
        defaultValues: {
            mode: PostMode.POST_NOW,
            media_url: "",
            caption: "",
            scheduled_date: undefined,
            scheduled_time: undefined,
        },
    });

    const selectedMode = form.watch("mode");
    const caption = form.watch("caption");

    const handleMediaSelect = (file: File | null, url: string | null) => {
        setSelectedFile(file);
        if (url) {
            form.setValue("media_url", url, { shouldValidate: true });
        } else if (file) {
            // For file uploads, we would need to upload to a CDN/storage first
            // For now, we'll show a message that URL is required
            form.setValue("media_url", "", { shouldValidate: false });
        } else {
            form.setValue("media_url", "", { shouldValidate: false });
        }
    };

    const onSubmit = async (values: PostFormValues) => {
        try {
            setIsSubmitting(true);

            // If a file was selected but no URL, we need to upload it first
            if (selectedFile && !values.media_url) {
                toast.error("Please use the Media URL tab to provide a publicly accessible URL");
                return;
            }

            // Construct scheduled_time in ISO format if scheduling
            let scheduled_time: string | undefined;
            if (values.mode === PostMode.SCHEDULE_POST && values.scheduled_date && values.scheduled_time) {
                const [hours, minutes] = values.scheduled_time.split(":");
                const scheduledDateTime = new Date(values.scheduled_date);
                scheduledDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);

                // Check if scheduled time is in the future
                if (scheduledDateTime <= new Date()) {
                    toast.error("Scheduled time must be in the future");
                    return;
                }

                scheduled_time = scheduledDateTime.toISOString();
            }

            const request = {
                mode: values.mode,
                media_url: values.media_url,
                caption: values.caption || undefined,
                scheduled_time,
            };

            const response = await instagramService.createPost(request);

            if (response.status === "published" || response.status === "scheduled") {
                const modeLabel = values.mode === PostMode.POST_NOW ? "posted" :
                    values.mode === PostMode.SCHEDULE_POST ? "scheduled" :
                        "story posted";
                toast.success(`Successfully ${modeLabel}!`);
                form.reset();
                setSelectedFile(null);
                onOpenChange(false);
                onSuccess?.();
            } else if (response.status === "failed") {
                toast.error(response.error || "Failed to create post");
            }
        } catch (error: any) {
            console.error("Error creating post:", error);
            toast.error(error.message || "Failed to create post. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const getModeIcon = (mode: PostMode) => {
        switch (mode) {
            case PostMode.POST_NOW:
                return <Zap className="w-4 h-4" />;
            case PostMode.SCHEDULE_POST:
                return <Clock className="w-4 h-4" />;
            case PostMode.POST_STORY:
                return <Smartphone className="w-4 h-4" />;
        }
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
                <SheetHeader>
                    <SheetTitle>Create Instagram Post</SheetTitle>
                    <SheetDescription>
                        Post immediately, schedule for later, or share as a story
                    </SheetDescription>
                </SheetHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 mt-6">
                        {/* Mode Selector */}
                        <FormField
                            control={form.control}
                            name="mode"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Posting Mode</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select posting mode" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value={PostMode.POST_NOW}>
                                                <div className="flex items-center gap-2">
                                                    <Zap className="w-4 h-4 text-yellow-500" />
                                                    Post Now
                                                </div>
                                            </SelectItem>
                                            <SelectItem value={PostMode.SCHEDULE_POST}>
                                                <div className="flex items-center gap-2">
                                                    <Clock className="w-4 h-4 text-blue-500" />
                                                    Schedule
                                                </div>
                                            </SelectItem>
                                            <SelectItem value={PostMode.POST_STORY}>
                                                <div className="flex items-center gap-2">
                                                    <Smartphone className="w-4 h-4 text-purple-500" />
                                                    Story
                                                </div>
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* Media Upload */}
                        <FormField
                            control={form.control}
                            name="media_url"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Media</FormLabel>
                                    <FormControl>
                                        <MediaUploadZone
                                            onMediaSelect={handleMediaSelect}
                                            accept="image/*,video/*"
                                            maxSizeMB={100}
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        Upload an image or video, or provide a publicly accessible URL
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {/* Caption (not for stories) */}
                        {selectedMode !== PostMode.POST_STORY && (
                            <FormField
                                control={form.control}
                                name="caption"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Caption</FormLabel>
                                        <FormControl>
                                            <Textarea
                                                placeholder="Write your caption here..."
                                                className="min-h-[100px] resize-none bg-white/5 border-white/10"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            {caption?.length || 0} / 2200 characters
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        )}

                        {/* Scheduled Date & Time (only for schedule mode) */}
                        {selectedMode === PostMode.SCHEDULE_POST && (
                            <div className="space-y-4 p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                                <FormField
                                    control={form.control}
                                    name="scheduled_date"
                                    render={({ field }) => (
                                        <FormItem className="flex flex-col">
                                            <FormLabel>Scheduled Date</FormLabel>
                                            <Popover>
                                                <PopoverTrigger asChild>
                                                    <FormControl>
                                                        <Button
                                                            variant="outline"
                                                            className={cn(
                                                                "w-full pl-3 text-left font-normal bg-white/5 border-white/10",
                                                                !field.value && "text-muted-foreground"
                                                            )}
                                                        >
                                                            {field.value ? (
                                                                format(field.value, "PPP")
                                                            ) : (
                                                                <span>Pick a date</span>
                                                            )}
                                                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                                        </Button>
                                                    </FormControl>
                                                </PopoverTrigger>
                                                <PopoverContent className="w-auto p-0" align="start">
                                                    <Calendar
                                                        mode="single"
                                                        selected={field.value}
                                                        onSelect={field.onChange}
                                                        disabled={(date) => date < new Date()}
                                                        initialFocus
                                                    />
                                                </PopoverContent>
                                            </Popover>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                <FormField
                                    control={form.control}
                                    name="scheduled_time"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Scheduled Time</FormLabel>
                                            <FormControl>
                                                <Input
                                                    type="time"
                                                    className="bg-white/5 border-white/10"
                                                    {...field}
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                        )}

                        {/* Submit Button */}
                        <div className="flex gap-3 pt-4">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                                className="flex-1"
                                disabled={isSubmitting}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                className="flex-1"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        {selectedMode === PostMode.SCHEDULE_POST ? "Scheduling..." : "Posting..."}
                                    </>
                                ) : (
                                    <>
                                        {getModeIcon(selectedMode)}
                                        <span className="ml-2">
                                            {selectedMode === PostMode.POST_NOW && "Post Now"}
                                            {selectedMode === PostMode.SCHEDULE_POST && "Schedule Post"}
                                            {selectedMode === PostMode.POST_STORY && "Post Story"}
                                        </span>
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                </Form>
            </SheetContent>
        </Sheet>
    );
};
