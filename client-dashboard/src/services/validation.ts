import APIClient from './api';

const client = new APIClient();

export const getValidationStatus = (requestId: string) => client.getValidationStatus(requestId);
