import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';

const AnimatedSphere = () => {
    const sphereRef = useRef<THREE.Mesh>(null);

    useFrame((state) => {
        if (sphereRef.current) {
            // Gentle rotation
            sphereRef.current.rotation.x = state.clock.getElapsedTime() * 0.2;
            sphereRef.current.rotation.y = state.clock.getElapsedTime() * 0.3;

            // Mouse interaction (parallax)
            const { x, y } = state.mouse;
            sphereRef.current.position.x = THREE.MathUtils.lerp(sphereRef.current.position.x, x * 2, 0.1);
            sphereRef.current.position.y = THREE.MathUtils.lerp(sphereRef.current.position.y, y * 2, 0.1);
        }
    });

    return (
        <Float speed={2} rotationIntensity={1} floatIntensity={2}>
            <Sphere ref={sphereRef} args={[1, 100, 100]} scale={2.5}>
                <MeshDistortMaterial
                    color="#00E0D0" // Primary teal color
                    attach="material"
                    distort={0.5} // Strength of distortion
                    speed={2} // Speed of distortion
                    roughness={0.2}
                    metalness={0.8}
                />
            </Sphere>
        </Float>
    );
};

const LiquidBackground = () => {
    return (
        <div className="absolute inset-0 -z-10 opacity-30 pointer-events-none">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <pointLight position={[-10, -10, -5]} intensity={1} color="#00E0D0" />
                <AnimatedSphere />
            </Canvas>
        </div>
    );
};

export default LiquidBackground;
