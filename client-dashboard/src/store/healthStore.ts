import { create } from 'zustand';
import type { HealthMetrics } from '@/types';

interface HealthStore {
  health: HealthMetrics | null;
  setHealth: (health: HealthMetrics | null) => void;
}

export const useHealthStore = create<HealthStore>((set) => ({
  health: null,
  setHealth: (health) => set({ health }),
}));
