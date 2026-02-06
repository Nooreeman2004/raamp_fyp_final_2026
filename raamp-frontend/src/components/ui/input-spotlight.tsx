import React, { useState } from "react";
import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export interface InputSpotlightProps
    extends React.InputHTMLAttributes<HTMLInputElement> {
    containerClassName?: string;
}

export const InputSpotlight = React.forwardRef<HTMLInputElement, InputSpotlightProps>(
    ({ className, containerClassName, ...props }, ref) => {
        const radius = 100; // radius of the spotlight
        const [visible, setVisible] = useState(false);
        let mouseX = useMotionValue(0);
        let mouseY = useMotionValue(0);

        function handleMouseMove({ currentTarget, clientX, clientY }: any) {
            let { left, top } = currentTarget.getBoundingClientRect();

            mouseX.set(clientX - left);
            mouseY.set(clientY - top);
        }

        return (
            <motion.div
                style={{
                    background: useMotionTemplate`
        radial-gradient(
          ${visible ? radius + "px" : "0px"} circle at ${mouseX}px ${mouseY}px,
          var(--primary),
          transparent 80%
        )
      `,
                }}
                onMouseMove={handleMouseMove}
                onMouseEnter={() => setVisible(true)}
                onMouseLeave={() => setVisible(false)}
                className={cn(
                    "p-[2px] rounded-lg transition duration-300 group/input pointer-events-none",
                    containerClassName
                )}
            >
                <Input
                    ref={ref}
                    className={cn(
                        "bg-zinc-900 border-transparent focus:border-transparent focus:ring-0 placeholder:text-zinc-500 pointer-events-auto",
                        className
                    )}
                    {...props}
                />
            </motion.div>
        );
    }
);
InputSpotlight.displayName = "InputSpotlight";
