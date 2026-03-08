import APIClient from './api';

const client = new APIClient();

export const rewindAgent = (agentId: string) => client.rewindAgent(agentId);
