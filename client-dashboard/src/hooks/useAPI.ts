import APIClient from '@/lib/services/api';

export const useAPI = () => {
  return new APIClient();
};
