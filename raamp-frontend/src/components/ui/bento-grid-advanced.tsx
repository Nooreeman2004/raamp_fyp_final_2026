import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface BentoGridAdvancedProps {
    children: ReactNode;
    className?: string;
}

export const BentoGridAdvanced = ({ children, className }: BentoGridAdvancedProps) => {
    return (
        <div
            className={cn(
                'grid grid-cols-1 md:grid-cols-6 lg:grid-cols-12 gap-4 auto-rows-[200px]',
                className
            )}
        >
            {children}
        </div>
    );
};

interface BentoCardAdvancedProps {
    title: string;
    description?: string;
    icon?: ReactNode;
    className?: string;
    colSpan?: string;
    rowSpan?: string;
    gradient?: string;
    children?: ReactNode;
    onClick?: () => void;
}

export const BentoCardAdvanced = ({
    title,
    description,
    icon,
    className,
    colSpan = 'md:col-span-3 lg:col-span-4',
    rowSpan = 'row-span-1',
    gradient = 'from-primary/20 via-primary/5 to-transparent',
    children,
    onClick,
}: BentoCardAdvancedProps) => {
    return (
        <motion.div
            className={cn(
                'group relative overflow-hidden rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm',
                'hover:border-primary/50 transition-all duration-500 cursor-pointer',
                'border-b-2 border-b-primary/30', // Added explicit bottom border
                colSpan,
                rowSpan,
                className
            )}
            whileHover={{ scale: 1.02, y: -5 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            onClick={onClick}
        >
            {/* Bottom Accent Border */}
            <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary/40 z-20" />

            {/* Gradient Background */}
            <div
                className={cn(
                    'absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500',
                    gradient
                )}
            />

            {/* Glow Effect */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1/2 bg-primary/20 blur-3xl" />
            </div>

            {/* Content */}
            <div className="relative h-full p-6 flex flex-col justify-between z-10">
                <div>
                    <div className="flex items-center gap-3 mb-4">
                        {icon && (
                            <motion.div
                                className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary flex-shrink-0"
                                whileHover={{ rotate: 15, scale: 1.1 }}
                                transition={{ duration: 0.3 }}
                            >
                                {icon}
                            </motion.div>
                        )}
                        <h3 className="text-xl md:text-2xl font-bold text-foreground group-hover:text-primary transition-colors duration-300">
                            {title}
                        </h3>
                    </div>
                    {description && (
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            {description}
                        </p>
                    )}
                </div>

                {children && <div className="mt-4">{children}</div>}
            </div>

            {/* Animated Highlight (Overlay for border feel) */}
            <motion.div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 pointer-events-none"
                style={{
                    background:
                        'linear-gradient(90deg, transparent, rgba(0, 224, 208, 0.2), transparent)',
                    backgroundSize: '200% 100%',
                }}
                animate={{
                    backgroundPosition: ['200% 0', '-200% 0'],
                }}
                transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: 'linear',
                }}
            />
        </motion.div>
    );
};

interface BentoFeatureCardProps {
    title: string;
    description: string;
    icon: ReactNode;
    stats?: { label: string; value: string }[];
    className?: string;
    colSpan?: string;
    rowSpan?: string;
}

export const BentoFeatureCard = ({
    title,
    description,
    icon,
    stats,
    className,
    colSpan = 'md:col-span-3 lg:col-span-4',
    rowSpan = 'row-span-2',
}: BentoFeatureCardProps) => {
    return (
        <BentoCardAdvanced
            title={title}
            description={description}
            icon={icon}
            className={className}
            colSpan={colSpan}
            rowSpan={rowSpan}
        >
            {stats && (
                <div className="grid grid-cols-2 gap-4 mt-auto">
                    {stats.map((stat, index) => (
                        <motion.div
                            key={index}
                            className="p-3 rounded-lg bg-foreground/5 border border-border/50"
                            whileHover={{ scale: 1.05 }}
                        >
                            <div className="text-2xl font-bold text-primary">{stat.value}</div>
                            <div className="text-xs text-muted-foreground">{stat.label}</div>
                        </motion.div>
                    ))}
                </div>
            )}
        </BentoCardAdvanced>
    );
};

interface BentoImageCardProps {
    title: string;
    description?: string;
    image: string;
    className?: string;
    colSpan?: string;
    rowSpan?: string;
}

export const BentoImageCard = ({
    title,
    description,
    image,
    className,
    colSpan = 'md:col-span-3 lg:col-span-4',
    rowSpan = 'row-span-2',
}: BentoImageCardProps) => {
    return (
        <motion.div
            className={cn(
                'group relative overflow-hidden rounded-2xl border border-border/50',
                'hover:border-primary/50 transition-all duration-500 cursor-pointer',
                colSpan,
                rowSpan,
                className
            )}
            whileHover={{ scale: 1.02, y: -5 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
            {/* Background Image */}
            <div className="absolute inset-0">
                <img
                    src={image}
                    alt={title}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-background/50 to-transparent" />
            </div>

            {/* Content */}
            <div className="relative h-full p-6 flex flex-col justify-end z-10">
                <h3 className="text-xl md:text-2xl font-bold text-foreground mb-2 group-hover:text-primary transition-colors duration-300">
                    {title}
                </h3>
                {description && (
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        {description}
                    </p>
                )}
            </div>
        </motion.div>
    );
};
