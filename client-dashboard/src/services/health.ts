import APIClient from './api';

const client = new APIClient();

export const getHealth = () => client.getHealth();
