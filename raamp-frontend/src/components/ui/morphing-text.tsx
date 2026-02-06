import { useEffect, useRef, useState } from 'react';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import { cn } from '@/lib/utils';

interface MorphingTextProps {
    text: string;
    className?: string;
    delay?: number;
    duration?: number;
}

export const MorphingText = ({
    text,
    className = '',
    delay = 0,
    duration = 0.8
}: MorphingTextProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const isInView = useInView(ref, { once: true, margin: '-100px' });

    const words = text.split(' ');

    return (
        <div ref={ref} className={cn('overflow-hidden', className)}>
            {words.map((word, wordIndex) => (
                <span key={wordIndex} className="inline-block mr-2">
                    {word.split('').map((char, charIndex) => (
                        <motion.span
                            key={charIndex}
                            className="inline-block"
                            initial={{ opacity: 0, y: 50, rotateX: 90 }}
                            animate={
                                isInView
                                    ? { opacity: 1, y: 0, rotateX: 0 }
                                    : { opacity: 0, y: 50, rotateX: 90 }
                            }
                            transition={{
                                duration,
                                delay: delay + (wordIndex * 0.05) + (charIndex * 0.03),
                                ease: [0.33, 1, 0.68, 1],
                            }}
                        >
                            {char}
                        </motion.span>
                    ))}
                </span>
            ))}
        </div>
    );
};

interface ScrollMorphTextProps {
    text: string;
    className?: string;
    startColor?: string;
    endColor?: string;
}

export const ScrollMorphText = ({
    text,
    className = '',
    startColor = 'rgba(255, 255, 255, 0.3)',
    endColor = 'rgba(0, 224, 208, 1)'
}: ScrollMorphTextProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ['start end', 'end start'],
    });

    const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [0.3, 1, 0.3]);
    const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.95, 1, 0.95]);

    return (
        <motion.div
            ref={ref}
            style={{ opacity, scale }}
            className={cn('transition-colors duration-500', className)}
        >
            {text}
        </motion.div>
    );
};

interface SplitTextRevealProps {
    text: string;
    className?: string;
    delay?: number;
}

export const SplitTextReveal = ({
    text,
    className = '',
    delay = 0
}: SplitTextRevealProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const isInView = useInView(ref, { once: true, margin: '-50px' });

    const lines = text.split('\n');

    return (
        <div ref={ref} className={cn('overflow-hidden', className)}>
            {lines.map((line, lineIndex) => (
                <div key={lineIndex} className="overflow-hidden">
                    <motion.div
                        initial={{ y: '100%', opacity: 0 }}
                        animate={
                            isInView
                                ? { y: 0, opacity: 1 }
                                : { y: '100%', opacity: 0 }
                        }
                        transition={{
                            duration: 0.8,
                            delay: delay + lineIndex * 0.1,
                            ease: [0.33, 1, 0.68, 1],
                        }}
                    >
                        {line}
                    </motion.div>
                </div>
            ))}
        </div>
    );
};

interface WaveTextProps {
    text: string;
    className?: string;
    delay?: number;
}

export const WaveText = ({
    text,
    className = '',
    delay = 0
}: WaveTextProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const isInView = useInView(ref, { once: true });

    return (
        <div ref={ref} className={cn('inline-flex', className)}>
            {text.split('').map((char, index) => (
                <motion.span
                    key={index}
                    className="inline-block"
                    initial={{ y: 0 }}
                    animate={
                        isInView
                            ? {
                                y: [0, -20, 0],
                                transition: {
                                    duration: 0.6,
                                    delay: delay + index * 0.05,
                                    ease: 'easeInOut',
                                },
                            }
                            : { y: 0 }
                    }
                >
                    {char === ' ' ? '\u00A0' : char}
                </motion.span>
            ))}
        </div>
    );
};

interface GlitchTextProps {
    text: string;
    className?: string;
}

export const GlitchText = ({ text, className = '' }: GlitchTextProps) => {
    const [isGlitching, setIsGlitching] = useState(false);

    useEffect(() => {
        const interval = setInterval(() => {
            setIsGlitching(true);
            setTimeout(() => setIsGlitching(false), 200);
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className={cn('relative inline-block', className)}>
            <span className="relative z-10">{text}</span>
            {isGlitching && (
                <>
                    <motion.span
                        className="absolute top-0 left-0 text-primary opacity-70"
                        initial={{ x: 0, y: 0 }}
                        animate={{ x: [-2, 2, -2], y: [1, -1, 1] }}
                        transition={{ duration: 0.2 }}
                    >
                        {text}
                    </motion.span>
                    <motion.span
                        className="absolute top-0 left-0 text-red-500 opacity-70"
                        initial={{ x: 0, y: 0 }}
                        animate={{ x: [2, -2, 2], y: [-1, 1, -1] }}
                        transition={{ duration: 0.2 }}
                    >
                        {text}
                    </motion.span>
                </>
            )}
        </div>
    );
};
