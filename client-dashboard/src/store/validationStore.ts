import { create } from 'zustand';
import type { ValidationMetrics } from '@/types';

interface ValidationStore {
  validations: ValidationMetrics[];
  setValidations: (validations: ValidationMetrics[]) => void;
}

export const useValidationStore = create<ValidationStore>((set) => ({
  validations: [],
  setValidations: (validations) => set({ validations }),
}));
