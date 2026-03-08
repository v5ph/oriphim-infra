import { create } from 'zustand';
import APIClient from '@services/api';
import { STORAGE_KEYS } from '@lib/constants/storage';
import { getStorageItem, removeStorageItem, setStorageItem } from '@lib/utils/storage';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: { user_id: string; tenant_id: string; scope: string } | null;
  isLoading: boolean;
  error: string | null;
  login: (apiKey: string) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<boolean>;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: getStorageItem(STORAGE_KEYS.accessToken),
  refreshToken: getStorageItem(STORAGE_KEYS.refreshToken),
  user: null,
  isLoading: false,
  error: null,

  login: async (apiKey: string) => {
    set({ isLoading: true, error: null });
    try {
      const client = new APIClient();
      const response = await client.login(apiKey);
      const { access_token, refresh_token } = response.data;

      setStorageItem(STORAGE_KEYS.accessToken, access_token);
      setStorageItem(STORAGE_KEYS.refreshToken, refresh_token);

      const verifiedClient = new APIClient(access_token);
      const verified = await verifiedClient.verifyToken();

      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        user: verified.data,
        isLoading: false,
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Login failed',
        isLoading: false,
      });
      throw err;
    }
  },

  logout: async () => {
    try {
      const client = new APIClient();
      await client.logout();
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      removeStorageItem(STORAGE_KEYS.accessToken);
      removeStorageItem(STORAGE_KEYS.refreshToken);
      set({ accessToken: null, refreshToken: null, user: null });
    }
  },

  restoreSession: async () => {
    const token = getStorageItem(STORAGE_KEYS.accessToken);
    if (!token) {
      set({ isLoading: false });
      return false;
    }

    set({ isLoading: true });
    try {
      const client = new APIClient(token);
      const verified = await client.verifyToken();
      set({ user: verified.data, accessToken: token, isLoading: false });
      return true;
    } catch (err) {
      console.error('Session restore failed:', err);
      removeStorageItem(STORAGE_KEYS.accessToken);
      removeStorageItem(STORAGE_KEYS.refreshToken);
      set({ accessToken: null, refreshToken: null, user: null, isLoading: false });
      return false;
    }
  },

  setError: (error: string | null) => set({ error }),
}));

export const useAuth = () => useAuthStore();
