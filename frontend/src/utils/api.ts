// Re-export shared API client (web adapter default)
import api, { setSessionRevokedHandler } from '../../packages/api-client';

export { setSessionRevokedHandler };
export default api;
