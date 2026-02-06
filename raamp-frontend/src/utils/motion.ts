import { Variants } from "framer-motion";

export const fadeInUp: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.5,
            ease: "easeOut"
        }
    }
};

export const staggerContainer: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2
        }
    }
};

export const decoderText: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 }
};

export const springSlide: Variants = {
    hidden: { x: -50, opacity: 0 },
    visible: {
        x: 0,
        opacity: 1,
        transition: {
            type: "spring",
            stiffness: 100,
            damping: 12
        }
    }
};

export const pulseGlow: Variants = {
    initial: { opacity: 0.6, scale: 1 },
    animate: {
        opacity: [0.6, 1, 0.6],
        scale: [1, 1.05, 1],
        transition: {
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
        }
    }
};

export const magneticSpring = {
    type: "spring",
    stiffness: 150,
    damping: 15,
    mass: 0.1
};

export const pageTransition: Variants = {
    initial: { opacity: 0, scale: 0.95, filter: "blur(10px)" },
    animate: {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        transition: { duration: 0.4, ease: "circOut" }
    },
    exit: {
        opacity: 0,
        scale: 0.95,
        filter: "blur(10px)",
        transition: { duration: 0.3, ease: "circIn" }
    }
};
