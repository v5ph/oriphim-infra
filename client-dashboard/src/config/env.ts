type EnvName =
  | 'VITE_API_BASE_URL'
  | 'VITE_API_TIMEOUT'
  | 'VITE_POLLING_INTERVAL_MS'
  | 'VITE_HEALTH_CHECK_INTERVAL_MS'
  | 'VITE_AUTH_TOKEN_STORAGE_KEY'
  | 'VITE_REFRESH_TOKEN_STORAGE_KEY';

const envSource = import.meta.env as Record<string, string | undefined>;

const getOptionalString = (name: EnvName): string | undefined => {
  const value = envSource[name]?.trim();
  return value ? value : undefined;
};

const getString = (name: EnvName, defaultValue: string): string => {
  return getOptionalString(name) ?? defaultValue;
};

const getNumber = (name: EnvName, defaultValue: number): number => {
  const rawValue = getOptionalString(name);
  if (!rawValue) {
    return defaultValue;
  }

  const parsed = Number(rawValue);
  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error(`${name} must be a non-negative number. Received: ${rawValue}`);
  }

  return parsed;
};

const getUrl = (name: EnvName, defaultValue: string): string => {
  const value = getString(name, defaultValue);

  try {
    const parsed = new URL(value);
    return parsed.toString().replace(/\/$/, '');
  } catch {
    throw new Error(`${name} must be a valid URL. Received: ${value}`);
  }
};

export interface RuntimeEnv {
  apiBaseUrl: string;
  apiTimeoutMs: number;
  pollingIntervalMs: number;
  healthCheckIntervalMs: number;
  authTokenStorageKey: string;
  refreshTokenStorageKey: string;
}

export const env: RuntimeEnv = Object.freeze({
  apiBaseUrl: getUrl('VITE_API_BASE_URL', 'http://localhost:8000'),
  apiTimeoutMs: getNumber('VITE_API_TIMEOUT', 5000),
  pollingIntervalMs: getNumber('VITE_POLLING_INTERVAL_MS', 2000),
  healthCheckIntervalMs: getNumber('VITE_HEALTH_CHECK_INTERVAL_MS', 2000),
  authTokenStorageKey: getString('VITE_AUTH_TOKEN_STORAGE_KEY', 'oriphim_access_token'),
  refreshTokenStorageKey: getString('VITE_REFRESH_TOKEN_STORAGE_KEY', 'oriphim_refresh_token'),
});
