import { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { cn } from '@/lib/utils';

interface Text3DScrollProps {
    text: string;
    className?: string;
}

export const Text3DScroll = ({ text, className }: Text3DScrollProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start'],
    });

    const rotateX = useTransform(scrollYProgress, [0, 0.5, 1], [45, 0, -45]);
    const rotateY = useTransform(scrollYProgress, [0, 0.5, 1], [-45, 0, 45]);
    const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.8, 1.2, 0.8]);
    const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

    return (
        <div ref={ref} className={cn('h-screen flex items-center justify-center perspective-1000', className)}>
            <motion.h1
                style={{
                    rotateX,
                    rotateY,
                    scale,
                    opacity,
                    transformStyle: 'preserve-3d',
                }}
                className="text-6xl md:text-9xl font-bold text-white"
            >
                {text}
            </motion.h1>
        </div>
    );
};

interface SplitText3DProps {
    text: string;
    className?: string;
    delay?: number;
}

export const SplitText3D = ({ text, className, delay = 0 }: SplitText3DProps) => {
    const letters = text.split('');

    return (
        <div className={cn('inline-flex perspective-1000', className)}>
            {letters.map((letter, index) => (
                <motion.span
                    key={index}
                    className="inline-block"
                    style={{ transformStyle: 'preserve-3d' }}
                    initial={{
                        rotateY: -90,
                        opacity: 0,
                        z: -100
                    }}
                    animate={{
                        rotateY: 0,
                        opacity: 1,
                        z: 0
                    }}
                    transition={{
                        duration: 0.8,
                        delay: delay + index * 0.05,
                        ease: [0.33, 1, 0.68, 1],
                    }}
                    whileHover={{
                        rotateY: 360,
                        color: 'hsl(var(--primary))',
                        transition: { duration: 0.6 },
                    }}
                >
                    {letter === ' ' ? '\u00A0' : letter}
                </motion.span>
            ))}
        </div>
    );
};

interface LayeredText3DProps {
    text: string;
    layers?: number;
    className?: string;
}

export const LayeredText3D = ({
    text,
    layers = 5,
    className
}: LayeredText3DProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start'],
    });

    const depth = useTransform(scrollYProgress, [0, 0.5, 1], [0, 50, 0]);

    return (
        <div ref={ref} className={cn('relative perspective-1000', className)}>
            <div className="relative" style={{ transformStyle: 'preserve-3d' }}>
                {Array.from({ length: layers }).map((_, index) => {
                    const zOffset = -index * 10;
                    const opacity = 1 - (index / layers) * 0.7;

                    return (
                        <motion.div
                            key={index}
                            className="absolute inset-0 text-6xl md:text-9xl font-bold"
                            style={{
                                transform: `translateZ(${zOffset}px)`,
                                opacity,
                                color: index === 0 ? 'hsl(var(--primary))' : 'hsl(var(--primary) / 0.3)',
                                WebkitTextStroke: index === 0 ? '0px' : '1px hsl(var(--primary))',
                                WebkitTextFillColor: index === 0 ? 'hsl(var(--primary))' : 'transparent',
                            }}
                        >
                            {text}
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

interface FloatingText3DProps {
    text: string;
    className?: string;
}

export const FloatingText3D = ({ text, className }: FloatingText3DProps) => {
    return (
        <motion.div
            className={cn('perspective-1000', className)}
            animate={{
                rotateX: [0, 5, 0, -5, 0],
                rotateY: [0, 5, 0, -5, 0],
                z: [0, 20, 0, -20, 0],
            }}
            transition={{
                duration: 10,
                repeat: Infinity,
                ease: 'easeInOut',
            }}
            style={{ transformStyle: 'preserve-3d' }}
        >
            <h1 className="text-6xl md:text-9xl font-bold text-white">
                {text}
            </h1>
        </motion.div>
    );
};

interface PerspectiveTextProps {
    text: string;
    className?: string;
}

export const PerspectiveText = ({ text, className }: PerspectiveTextProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start'],
    });

    const perspective = useTransform(scrollYProgress, [0, 0.5, 1], [2000, 500, 2000]);
    const rotateX = useTransform(scrollYProgress, [0, 0.5, 1], [60, 0, -60]);

    return (
        <div ref={ref} className="h-screen flex items-center justify-center overflow-hidden">
            <motion.div
                style={{ perspective }}
                className={cn('w-full', className)}
            >
                <motion.h1
                    style={{ rotateX, transformStyle: 'preserve-3d' }}
                    className="text-6xl md:text-9xl font-bold text-center text-white origin-center"
                >
                    {text}
                </motion.h1>
            </motion.div>
        </div>
    );
};

interface ExplodingTextProps {
    text: string;
    className?: string;
}

export const ExplodingText = ({ text, className }: ExplodingTextProps) => {
    const letters = text.split('');
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start'],
    });

    return (
        <div ref={ref} className={cn('h-screen flex items-center justify-center perspective-1000', className)}>
            <div className="relative" style={{ transformStyle: 'preserve-3d' }}>
                {letters.map((letter, index) => {
                    const angle = (index / letters.length) * 360;
                    const radius = useTransform(
                        scrollYProgress,
                        [0.3, 0.5, 0.7],
                        [0, 200, 0]
                    );

                    const x = useTransform(radius, (r) => Math.cos((angle * Math.PI) / 180) * r);
                    const y = useTransform(radius, (r) => Math.sin((angle * Math.PI) / 180) * r);
                    const z = useTransform(scrollYProgress, [0.3, 0.5, 0.7], [0, 100, 0]);
                    const rotateZ = useTransform(scrollYProgress, [0.3, 0.5, 0.7], [0, 360, 720]);

                    return (
                        <motion.span
                            key={index}
                            className="absolute text-6xl md:text-9xl font-bold text-primary"
                            style={{
                                x,
                                y,
                                z,
                                rotateZ,
                                transformStyle: 'preserve-3d',
                                left: '50%',
                                top: '50%',
                            }}
                        >
                            {letter === ' ' ? '\u00A0' : letter}
                        </motion.span>
                    );
                })}
            </div>
        </div>
    );
};
