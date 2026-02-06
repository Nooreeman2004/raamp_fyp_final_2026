import { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '@/lib/utils';

interface MagneticImageProps {
    src: string;
    alt: string;
    className?: string;
    strength?: number;
    scale?: number;
}

export const MagneticImage = ({
    src,
    alt,
    className,
    strength = 0.15,
    scale = 1.05
}: MagneticImageProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [isHovered, setIsHovered] = useState(false);

    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const springConfig = { damping: 20, stiffness: 200 };
    const xSpring = useSpring(x, springConfig);
    const ySpring = useSpring(y, springConfig);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;

        const rect = ref.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const distanceX = e.clientX - centerX;
        const distanceY = e.clientY - centerY;

        x.set(distanceX * strength);
        y.set(distanceY * strength);
    };

    const handleMouseLeave = () => {
        setIsHovered(false);
        x.set(0);
        y.set(0);
    };

    return (
        <motion.div
            ref={ref}
            className={cn('relative overflow-hidden rounded-2xl cursor-pointer', className)}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={handleMouseLeave}
            whileHover={{ scale }}
            transition={{ duration: 0.4, ease: [0.33, 1, 0.68, 1] }}
        >
            <motion.img
                src={src}
                alt={alt}
                className="w-full h-full object-cover"
                style={{ x: xSpring, y: ySpring }}
            />

            {/* Overlay gradient on hover */}
            <motion.div
                className="absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-transparent"
                initial={{ opacity: 0 }}
                animate={{ opacity: isHovered ? 1 : 0 }}
                transition={{ duration: 0.3 }}
            />
        </motion.div>
    );
};

interface DepthParallaxCardProps {
    children: React.ReactNode;
    className?: string;
    depth?: number;
}

export const DepthParallaxCard = ({
    children,
    className,
    depth = 20
}: DepthParallaxCardProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [isHovered, setIsHovered] = useState(false);

    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const rotateX = useTransform(y, [-0.5, 0.5], [depth, -depth]);
    const rotateY = useTransform(x, [-0.5, 0.5], [-depth, depth]);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;

        const rect = ref.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const distanceX = (e.clientX - centerX) / rect.width;
        const distanceY = (e.clientY - centerY) / rect.height;

        x.set(distanceX);
        y.set(distanceY);
    };

    const handleMouseLeave = () => {
        setIsHovered(false);
        x.set(0);
        y.set(0);
    };

    return (
        <motion.div
            ref={ref}
            className={cn('relative', className)}
            style={{
                transformStyle: 'preserve-3d',
                perspective: 1000,
            }}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={handleMouseLeave}
        >
            <motion.div
                style={{
                    rotateX,
                    rotateY,
                    transformStyle: 'preserve-3d',
                }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            >
                {children}
            </motion.div>

            {/* Glow effect */}
            <motion.div
                className="absolute inset-0 bg-primary/20 blur-3xl -z-10 rounded-2xl"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{
                    opacity: isHovered ? 1 : 0,
                    scale: isHovered ? 1 : 0.8
                }}
                transition={{ duration: 0.3 }}
            />
        </motion.div>
    );
};

interface TiltCardProps {
    children: React.ReactNode;
    className?: string;
    maxTilt?: number;
}

export const TiltCard = ({
    children,
    className,
    maxTilt = 10
}: TiltCardProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [rotateX, setRotateX] = useState(0);
    const [rotateY, setRotateY] = useState(0);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;

        const rect = ref.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateXValue = ((y - centerY) / centerY) * -maxTilt;
        const rotateYValue = ((x - centerX) / centerX) * maxTilt;

        setRotateX(rotateXValue);
        setRotateY(rotateYValue);
    };

    const handleMouseLeave = () => {
        setRotateX(0);
        setRotateY(0);
    };

    return (
        <motion.div
            ref={ref}
            className={cn('relative', className)}
            style={{
                transformStyle: 'preserve-3d',
                perspective: 1000,
            }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            animate={{
                rotateX,
                rotateY,
            }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
            {children}
        </motion.div>
    );
};

interface ImageRevealProps {
    src: string;
    alt: string;
    className?: string;
    direction?: 'left' | 'right' | 'top' | 'bottom';
}

export const ImageReveal = ({
    src,
    alt,
    className,
    direction = 'bottom'
}: ImageRevealProps) => {
    const [isHovered, setIsHovered] = useState(false);

    const clipPathVariants = {
        left: {
            initial: 'polygon(0 0, 0 0, 0 100%, 0 100%)',
            hover: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)',
        },
        right: {
            initial: 'polygon(100% 0, 100% 0, 100% 100%, 100% 100%)',
            hover: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)',
        },
        top: {
            initial: 'polygon(0 0, 100% 0, 100% 0, 0 0)',
            hover: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)',
        },
        bottom: {
            initial: 'polygon(0 100%, 100% 100%, 100% 100%, 0 100%)',
            hover: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)',
        },
    };

    return (
        <div
            className={cn('relative overflow-hidden', className)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <motion.img
                src={src}
                alt={alt}
                className="w-full h-full object-cover"
                style={{
                    clipPath: isHovered
                        ? clipPathVariants[direction].hover
                        : clipPathVariants[direction].initial,
                }}
                transition={{ duration: 0.6, ease: [0.33, 1, 0.68, 1] }}
            />
        </div>
    );
};
