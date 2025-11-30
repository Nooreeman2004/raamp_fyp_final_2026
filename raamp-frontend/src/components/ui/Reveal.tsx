import React from 'react';
import { motion, Variants, useInView } from 'framer-motion';
import { useRef } from 'react';
import * as animations from '@/utils/animations'; 

interface RevealProps {
  children: React.ReactNode;
  variant?: keyof typeof animations; 
  delay?: number;
  duration?: number;
  className?: string;
  once?: boolean; 
}

const Reveal: React.FC<RevealProps> = ({ 
  children, 
  variant = 'fadeInUp', 
  delay = 0, 
  duration,
  className = "",
  once = true 
}) => {
  const ref = useRef(null);
  const selectedVariant = animations[variant] as Variants;

  return (
    <motion.div
      ref={ref}
      variants={selectedVariant}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: "-50px" }} 
      transition={{ delay, duration }} 
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default Reveal;