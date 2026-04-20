import Onboarding from "@/pages/Onboarding";

/**
 * Settings-owned route for integrations.
 * We reuse the existing Integrations UI, but keep routing ownership under /settings.
 */
const SettingsIntegrations = () => {
  return (
    <Onboarding />
  );
};

export default SettingsIntegrations;

