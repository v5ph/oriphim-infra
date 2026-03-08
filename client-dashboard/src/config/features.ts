const readFlag = (name: string, defaultValue: boolean = false): boolean => {
  const rawValue = import.meta.env[name]?.toString().trim().toLowerCase();
  if (!rawValue) {
    return defaultValue;
  }

  return rawValue === '1' || rawValue === 'true' || rawValue === 'yes' || rawValue === 'on';
};

export interface FeatureFlags {
  enableVerboseApiErrors: boolean;
  enableIntegrationWorkspace: boolean;
}

export const features: FeatureFlags = Object.freeze({
  enableVerboseApiErrors: readFlag('VITE_FEATURE_VERBOSE_API_ERRORS', false),
  enableIntegrationWorkspace: readFlag('VITE_FEATURE_INTEGRATION_WORKSPACE', true),
});
