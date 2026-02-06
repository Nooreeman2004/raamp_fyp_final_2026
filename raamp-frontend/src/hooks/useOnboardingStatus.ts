import { useMemo } from 'react';
import { useAuth } from './useAuth';

export interface OnboardingStep {
    id: string;
    label: string;
    route: string;
    isCompleted: boolean;
}

export const useOnboardingStatus = () => {
    const { user } = useAuth();

    const currentStatus = useMemo(() => {
        if (!user || !user.onboarding_status) {
            // Fallback for missing status (assume nothing is done if profile is incomplete)
            return {
                profile_completed: user?.profile_completed || false,
                business_setup_completed: false,
                brand_setup_completed: false,
                connections_completed: false,
            };
        }
        return user.onboarding_status;
    }, [user]);

    const steps: OnboardingStep[] = [
        {
            id: 'personal_details',
            label: 'Personal Details',
            route: '/profile/personal-details',
            isCompleted: currentStatus.profile_completed,
        },
        {
            id: 'business_setup',
            label: 'Business Setup',
            route: '/profile/business-setup',
            isCompleted: currentStatus.business_setup_completed,
        },
        {
            id: 'brand_settings',
            label: 'Brand Settings',
            route: '/profile/brand-settings',
            isCompleted: currentStatus.brand_setup_completed,
        },
        {
            id: 'connections',
            label: 'Connections',
            route: '/profile/onboarding',
            isCompleted: currentStatus.connections_completed,
        },
    ];

    // Find the first incomplete step
    const nextStep = steps.find((step) => !step.isCompleted);
    const isFullyOnboarded = !nextStep;

    return {
        status: currentStatus,
        steps,
        nextStep,
        isFullyOnboarded,
        isLoading: !user, // Simply loading if user not loaded
    };
};
