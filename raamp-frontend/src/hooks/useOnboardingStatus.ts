import { useMemo, useEffect } from 'react';
import { useAuth } from './useAuth';
import type { OnboardingStatus, UserResponse } from '@/types/user.types';

/** First incomplete onboarding route, or `null` when all steps are done. */
export function getNextOnboardingRoute(status: OnboardingStatus): string | null {
    if (!status.profile_completed) return '/profile/personal-details';
    if (!status.business_setup_completed) return '/profile/business-setup';
    if (!status.brand_setup_completed) return '/profile/brand-settings';
    if (!status.connections_completed) return '/profile/onboarding';
    return null;
}

/** Resolves onboarding status from API user (including legacy responses without `onboarding_status`). */
export function getNextOnboardingRouteFromUser(user: UserResponse | null | undefined): string | null {
    if (!user) return '/profile/personal-details';
    const status: OnboardingStatus = user.onboarding_status ?? {
        profile_completed: user.profile_completed,
        business_setup_completed: false,
        brand_setup_completed: false,
        connections_completed: false,
    };
    return getNextOnboardingRoute(status);
}

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

    // Source of truth: API-derived steps only. Stale `raamp_onboarded` must not block progress.
    const isFullyOnboarded = !nextStep;

    useEffect(() => {
        if (nextStep) {
            localStorage.removeItem('raamp_onboarded');
        } else {
            localStorage.setItem('raamp_onboarded', 'true');
        }
        if (!user) {
            localStorage.removeItem('raamp_onboarded');
        }
    }, [nextStep, user]);

    return {
        status: currentStatus,
        steps,
        nextStep,
        isFullyOnboarded,
        isLoading: !user, // Simply loading if user not loaded
    };
};
