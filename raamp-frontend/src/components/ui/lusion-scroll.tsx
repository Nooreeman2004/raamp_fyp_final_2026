import { useEffect, useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SmoothScrollContainerProps {
    children: React.ReactNode;
    className?: string;
    speed?: number;
}

export const SmoothScrollContainer = ({
    children,
    className,
    speed = 1
}: SmoothScrollContainerProps) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll();

    const smoothProgress = useSpring(scrollYProgress, {
        stiffness: 100,
        damping: 30,
        restDelta: 0.001
    });

    return (
        <div ref={scrollRef} className={cn('relative', className)}>
            {children}
        </div>
    );
};

interface ScrollSnapSectionProps {
    children: React.ReactNode;
    className?: string;
    id?: string;
}

export const ScrollSnapSection = ({
    children,
    className,
    id
}: ScrollSnapSectionProps) => {
    return (
        <section
            id={id}
            className={cn(
                'min-h-screen w-full snap-start snap-always',
                'flex items-center justify-center',
                className
            )}
        >
            {children}
        </section>
    );
};

interface ScrollSnapContainerProps {
    children: React.ReactNode;
    className?: string;
}

export const ScrollSnapContainer = ({
    children,
    className
}: ScrollSnapContainerProps) => {
    return (
        <div
            className={cn(
                'h-screen overflow-y-scroll snap-y snap-mandatory',
                'scroll-smooth',
                className
            )}
        >
            {children}
        </div>
    );
};

interface ParallaxScrollProps {
    children: React.ReactNode;
    offset?: number;
    className?: string;
}

export const ParallaxScroll = ({
    children,
    offset = 50,
    className
}: ParallaxScrollProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start']
    });

    const y = useTransform(scrollYProgress, [0, 1], [offset, -offset]);
    const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

    return (
        <motion.div
            ref={ref}
            style={{ y, opacity }}
            className={className}
        >
            {children}
        </motion.div>
    );
};

interface ScrollRevealProps {
    children: React.ReactNode;
    className?: string;
    delay?: number;
}

export const ScrollReveal = ({
    children,
    className,
    delay = 0
}: ScrollRevealProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start 0.9', 'start 0.5']
    });

    const opacity = useTransform(scrollYProgress, [0, 1], [0, 1]);
    const scale = useTransform(scrollYProgress, [0, 1], [0.8, 1]);
    const y = useTransform(scrollYProgress, [0, 1], [100, 0]);

    return (
        <motion.div
            ref={ref}
            style={{ opacity, scale, y }}
            transition={{ delay }}
            className={className}
        >
            {children}
        </motion.div>
    );
};

interface ScrollProgressBarProps {
    className?: string;
    color?: string;
}

export const ScrollProgressBar = ({
    className,
    color = 'bg-primary'
}: ScrollProgressBarProps) => {
    const { scrollYProgress } = useScroll();
    const scaleX = useSpring(scrollYProgress, {
        stiffness: 100,
        damping: 30,
        restDelta: 0.001
    });

    return (
        <motion.div
            className={cn(
                'fixed top-0 left-0 right-0 h-1 z-50 origin-left',
                color,
                className
            )}
            style={{ scaleX }}
        />
    );
};

interface HorizontalScrollSectionProps {
    children: React.ReactNode;
    className?: string;
}

export const HorizontalScrollSection = ({
    children,
    className
}: HorizontalScrollSectionProps) => {
    const targetRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: targetRef,
    });

    const x = useTransform(scrollYProgress, [0, 1], ['0%', '-75%']);

    return (
        <section ref={targetRef} className="relative h-[400vh]">
            <div className="sticky top-0 h-screen flex items-center overflow-hidden">
                <motion.div
                    style={{ x }}
                    className={cn('flex gap-8', className)}
                >
                    {children}
                </motion.div>
            </div>
        </section>
    );
};
