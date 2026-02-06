import * as React from "react";
import { Command } from "cmdk";
import { Search, Home, User, Settings, LogOut, LayoutDashboard, Briefcase, CreditCard } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

export function CommandMenu() {
    const [open, setOpen] = React.useState(false);
    const navigate = useNavigate();

    React.useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    const runCommand = React.useCallback((command: () => unknown) => {
        setOpen(false);
        command();
    }, []);

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogContent className="p-0 overflow-hidden bg-black/80 backdrop-blur-xl border-white/10 shadow-2xl max-w-2xl">
                <Command className="bg-transparent text-white">
                    <div className="flex items-center border-b border-white/10 px-4" cmdk-input-wrapper="">
                        <Search className="mr-2 h-5 w-5 shrink-0 opacity-50" />
                        <Command.Input
                            placeholder="Type a command or search..."
                            className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                        />
                    </div>
                    <Command.List className="max-h-[300px] overflow-y-auto overflow-x-hidden py-2 px-2">
                        <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
                            No results found.
                        </Command.Empty>

                        <Command.Group heading="Navigation" className="text-xs font-medium text-muted-foreground px-2 py-1.5">
                            <Command.Item
                                onSelect={() => runCommand(() => navigate("/dashboard"))}
                                className="flex items-center px-2 py-2 rounded-md hover:bg-white/10 cursor-pointer transition-colors text-sm text-white"
                            >
                                <LayoutDashboard className="mr-2 h-4 w-4" />
                                <span>Dashboard</span>
                            </Command.Item>
                            <Command.Item
                                onSelect={() => runCommand(() => navigate("/profile/user"))}
                                className="flex items-center px-2 py-2 rounded-md hover:bg-white/10 cursor-pointer transition-colors text-sm text-white"
                            >
                                <User className="mr-2 h-4 w-4" />
                                <span>Profile</span>
                            </Command.Item>
                            <Command.Item
                                onSelect={() => runCommand(() => navigate("/brand-settings"))}
                                className="flex items-center px-2 py-2 rounded-md hover:bg-white/10 cursor-pointer transition-colors text-sm text-white"
                            >
                                <Briefcase className="mr-2 h-4 w-4" />
                                <span>Brand Settings</span>
                            </Command.Item>
                            <Command.Item
                                onSelect={() => runCommand(() => navigate("/pricing"))}
                                className="flex items-center px-2 py-2 rounded-md hover:bg-white/10 cursor-pointer transition-colors text-sm text-white"
                            >
                                <CreditCard className="mr-2 h-4 w-4" />
                                <span>Pricing</span>
                            </Command.Item>
                        </Command.Group>

                        <Command.Separator className="my-1 h-px bg-white/10" />

                        <Command.Group heading="System" className="text-xs font-medium text-muted-foreground px-2 py-1.5">
                            <Command.Item
                                onSelect={() => runCommand(() => navigate("/settings"))}
                                className="flex items-center px-2 py-2 rounded-md hover:bg-white/10 cursor-pointer transition-colors text-sm text-white"
                            >
                                <Settings className="mr-2 h-4 w-4" />
                                <span>Settings</span>
                            </Command.Item>
                            <Command.Item
                                onSelect={() => runCommand(() => console.log("Logout"))}
                                className="flex items-center px-2 py-2 rounded-md hover:bg-white/10 cursor-pointer transition-colors text-sm text-white"
                            >
                                <LogOut className="mr-2 h-4 w-4" />
                                <span>Sign Out</span>
                            </Command.Item>
                        </Command.Group>
                    </Command.List>

                    <div className="border-t border-white/10 px-4 py-2 text-xs text-muted-foreground flex justify-between items-center bg-white/5">
                        <span>Search for anything...</span>
                        <div className="flex gap-2">
                            <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                                <span className="text-xs">↑</span>
                                <span className="text-xs">↓</span>
                            </kbd>
                            <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                                <span className="text-xs">↵</span>
                            </kbd>
                        </div>
                    </div>
                </Command>
            </DialogContent>
        </Dialog>
    );
}
