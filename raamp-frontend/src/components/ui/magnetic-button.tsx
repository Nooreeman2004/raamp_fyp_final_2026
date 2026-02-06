import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MagneticButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    className?: string;
    strength?: number; // How strong the magnetic pull is (default: 30)
}

export const MagneticButton = ({
    children,
    className,
    strength = 30,
    ...props
}: MagneticButtonProps) => {
    return (
        <button
            className={cn(
                "relative inline-flex items-center justify-center overflow-hidden rounded-lg transition-colors",
                className
            )}
            {...props}
        >
            {children}
        </button>
    );
};
