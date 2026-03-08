import APIClient from '@services/api';

export const useAPI = () => {
  return new APIClient();
};
