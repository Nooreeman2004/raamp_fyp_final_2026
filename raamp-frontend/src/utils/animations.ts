import { Variants } from 'framer-motion';

//Configuration 
// defining 1 variable, will be using ahead consistently 
const smoothEasing: [number, number, number, number] = [0.25, 0.1, 0.25, 1];

//1. Basic Entrances
export const fadeIn: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.5, ease: smoothEasing } },
};

export const fadeInUp: Variants = {
    hidden: { opacity: 0, y: 40 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: smoothEasing } },
};

export const fadeInDown: Variants = {
    hidden: { opacity: 0, y: -40 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: smoothEasing } },
};

export const fadeInLeft: Variants = {
    hidden: { opacity: 0, x: -50 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.6, ease: smoothEasing } },
};

export const fadeInRight: Variants = {
    hidden: { opacity: 0, x: 50 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.6, ease: smoothEasing } },
};

//2. Scaling & Zooming
export const zoomIn: Variants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: smoothEasing } },
};

export const zoomOut: Variants = {
    hidden: { opacity: 0, scale: 1.1 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: smoothEasing } },
};

export const scaleUp: Variants = {
    hidden: { scale: 0, opacity: 0 },
    visible: { scale: 1, opacity: 1, transition: { type: "spring", stiffness: 260, damping: 20 } },
};

//3. Blur Effects
export const blurIn: Variants = {
    hidden: { opacity: 0, filter: "blur(10px)" },
    visible: { opacity: 1, filter: "blur(0px)", transition: { duration: 0.8, ease: "easeOut" } },
};

export const blurInUp: Variants = {
    hidden: { opacity: 0, y: 20, filter: "blur(8px)" },
    visible: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.6 } },
};

//4. Text Stagger Effects 
export const textStaggerContainer: Variants = {
    hidden: {},
    visible: {
        transition: { staggerChildren: 0.05, delayChildren: 0.1 }
    }
};

export const letterAnimation: Variants = {
    hidden: { y: 50, opacity: 0 },
    visible: {
        y: 0,
        opacity: 1,
        transition: { type: "spring", damping: 12, stiffness: 100 }
    }
};

// Mask Reveal
export const maskReveal: Variants = {
    hidden: { y: "100%" },
    visible: {
        y: "0%",
        transition: { duration: 0.5, ease: smoothEasing }
    }
};

// --- 5. Container Orchestration (Staggering Children) ---
export const staggerContainer: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.15, delayChildren: 0.2 }
    }
};

export const staggerContainerFast: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.05 }
    }
};

//6. 3D & Perspective Effects
export const flipX: Variants = {
    hidden: { opacity: 0, rotateX: 90 },
    visible: { opacity: 1, rotateX: 0, transition: { duration: 0.6 } },
};

export const flipY: Variants = {
    hidden: { opacity: 0, rotateY: 90 },
    visible: { opacity: 1, rotateY: 0, transition: { duration: 0.6 } },
};

export const rotateIn: Variants = {
    hidden: { opacity: 0, rotate: -180, scale: 0.8 },
    visible: { opacity: 1, rotate: 0, scale: 1, transition: { duration: 0.6 } },
};

//7. Button & Card Interactions
export const hoverScale: Variants = {
    rest: { scale: 1 },
    hover: { scale: 1.05, transition: { type: "spring", stiffness: 400, damping: 10 } },
    tap: { scale: 0.95 }
};

export const hoverLift: Variants = {
    rest: { y: 0, boxShadow: "0px 5px 15px rgba(0,0,0,0)" },
    hover: {
        y: -5,
        boxShadow: "0px 10px 25px rgba(0,0,0,0.1)", // Adjust shadow color based on theme
        transition: { type: "spring", stiffness: 300 }
    }
};

export const hoverGlow: Variants = {
    rest: { boxShadow: "0 0 0 rgba(var(--primary), 0)" },
    hover: {
        boxShadow: "0 0 20px rgba(var(--primary), 0.5)",
        transition: { duration: 0.3 }
    }
};

//8. Attention Seekers 
export const pulse: Variants = {
    rest: { scale: 1 },
    animate: {
        scale: [1, 1.05, 1],
        transition: { duration: 1.5, repeat: Infinity }
    }
};

export const shake: Variants = {
    rest: { x: 0 },
    animate: {
        x: [-10, 10, -10, 10, 0],
        transition: { duration: 0.4 }
    }
};

//9. Layout Utilities
export const accordion: Variants = {
    closed: { height: 0, opacity: 0, overflow: "hidden" },
    open: { height: "auto", opacity: 1, transition: { duration: 0.3 } }
};

export const slideInDrawer: Variants = {
    closed: { x: "100%", opacity: 0 },
    open: { x: 0, opacity: 1, transition: { type: "spring", stiffness: 300, damping: 30 } }
};