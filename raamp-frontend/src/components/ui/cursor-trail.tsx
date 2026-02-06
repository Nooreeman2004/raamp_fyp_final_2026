import { useEffect, useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

interface CursorTrailProps {
    color?: string;
    size?: number;
    blur?: number;
}

export const CursorTrail = ({
    color = 'rgba(0, 224, 208, 0.4)',
    size = 20,
    blur = 30
}: CursorTrailProps) => {
    const cursorX = useMotionValue(-100);
    const cursorY = useMotionValue(-100);

    const springConfig = { damping: 25, stiffness: 200 };
    const cursorXSpring = useSpring(cursorX, springConfig);
    const cursorYSpring = useSpring(cursorY, springConfig);

    useEffect(() => {
        const moveCursor = (e: MouseEvent) => {
            cursorX.set(e.clientX - size / 2);
            cursorY.set(e.clientY - size / 2);
        };

        window.addEventListener('mousemove', moveCursor);

        return () => {
            window.removeEventListener('mousemove', moveCursor);
        };
    }, [cursorX, cursorY, size]);

    return (
        <>
            {/* Main cursor dot */}
            <motion.div
                className="pointer-events-none fixed z-[9999] mix-blend-screen"
                style={{
                    left: cursorXSpring,
                    top: cursorYSpring,
                    width: size,
                    height: size,
                }}
            >
                <div
                    className="w-full h-full rounded-full"
                    style={{
                        background: color,
                        filter: `blur(${blur}px)`,
                        boxShadow: `0 0 ${blur * 2}px ${color}`,
                    }}
                />
            </motion.div>

            {/* Secondary trail effect */}
            <motion.div
                className="pointer-events-none fixed z-[9998] mix-blend-screen"
                style={{
                    left: cursorXSpring,
                    top: cursorYSpring,
                    width: size * 1.5,
                    height: size * 1.5,
                }}
                transition={{ type: 'spring', damping: 30, stiffness: 150 }}
            >
                <div
                    className="w-full h-full rounded-full opacity-30"
                    style={{
                        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
                        filter: `blur(${blur * 1.5}px)`,
                    }}
                />
            </motion.div>
        </>
    );
};

interface MagneticCursorProps {
    children: React.ReactNode;
    strength?: number;
    className?: string;
}

export const MagneticCursor = ({
    children,
    strength = 0.3,
    className = ''
}: MagneticCursorProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const springConfig = { damping: 20, stiffness: 200 };
    const xSpring = useSpring(x, springConfig);
    const ySpring = useSpring(y, springConfig);

    useEffect(() => {
        if (!ref.current) return;

        const handleMouseMove = (e: MouseEvent) => {
            if (!ref.current) return;

            const rect = ref.current.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;

            const distanceX = e.clientX - centerX;
            const distanceY = e.clientY - centerY;

            const distance = Math.sqrt(distanceX ** 2 + distanceY ** 2);
            const maxDistance = 150;

            if (distance < maxDistance) {
                x.set(distanceX * strength);
                y.set(distanceY * strength);
            } else {
                x.set(0);
                y.set(0);
            }
        };

        const handleMouseLeave = () => {
            x.set(0);
            y.set(0);
        };

        window.addEventListener('mousemove', handleMouseMove);
        ref.current.addEventListener('mouseleave', handleMouseLeave);

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            ref.current?.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, [x, y, strength]);

    return (
        <motion.div
            ref={ref}
            style={{ x: xSpring, y: ySpring }}
            className={className}
        >
            {children}
        </motion.div>
    );
};
