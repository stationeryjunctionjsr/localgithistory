import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { createApiClient, ApiAdapter } from '@sj/api-client';

describe('createApiClient token refresh mutex', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('batches concurrent 401s into a single POST /auth/refresh call and retries all requests', async () => {
    let currentToken: string | null = 'stale-token';
    const mockAdapter: ApiAdapter = {
      getAccessToken: jest.fn(() => currentToken),
      getRefreshToken: jest.fn(() => 'valid-refresh-token'),
      clearTokens: jest.fn(() => {
        currentToken = null;
      }),
      setTokens: jest.fn((data: { token: string; refreshToken?: string; sessionId?: string }) => {
        currentToken = data.token;
      }),
      onUnauthorized: jest.fn(),
      onSessionRevoked: jest.fn(),
    };

    const client = createApiClient(mockAdapter);

    let refreshCallCount = 0;
    jest.spyOn(axios, 'post').mockImplementation(async (url: string) => {
      if (url.includes('/auth/refresh')) {
        refreshCallCount++;
        // Delay to simulate in-flight network request and force overlap
        await new Promise((resolve) => setTimeout(resolve, 50));
        return {
          data: {
            token: 'fresh-token',
            refreshToken: 'fresh-refresh-token',
          },
        } as AxiosResponse;
      }
      return { data: {} } as AxiosResponse;
    });

    client.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
      const authHeader = config.headers.Authorization as string;
      if (authHeader === 'Bearer stale-token') {
        const error = new AxiosError(
          'Request failed with status code 401',
          'ERR_BAD_REQUEST',
          config,
          null,
          {
            status: 401,
            statusText: 'Unauthorized',
            data: { detail: 'Token expired' },
            headers: {},
            config,
          } as AxiosResponse
        );
        return Promise.reject(error);
      }

      return {
        data: { success: true, url: config.url },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      } as AxiosResponse;
    };

    // Fire two concurrent requests
    const [res1, res2] = await Promise.all([
      client.get('/cart'),
      client.get('/products'),
    ]);

    expect(res1.data.success).toBe(true);
    expect(res2.data.success).toBe(true);
    expect(refreshCallCount).toBe(1); // Crucial: exactly ONE refresh call was dispatched!
    expect(mockAdapter.setTokens).toHaveBeenCalledWith(
      expect.objectContaining({ token: 'fresh-token' })
    );
    expect(mockAdapter.clearTokens).not.toHaveBeenCalled();
    expect(mockAdapter.onUnauthorized).not.toHaveBeenCalled();
  });

  it('handles SESSION_REVOKED during refresh without calling onUnauthorized', async () => {
    const mockAdapter: ApiAdapter = {
      getAccessToken: jest.fn(() => 'stale-token'),
      getRefreshToken: jest.fn(() => 'reused-refresh-token'),
      clearTokens: jest.fn(),
      setTokens: jest.fn(),
      onUnauthorized: jest.fn(),
      onSessionRevoked: jest.fn(),
    };

    const client = createApiClient(mockAdapter);

    jest.spyOn(axios, 'post').mockImplementation(async (url: string, _data, config) => {
      if (url.includes('/auth/refresh')) {
        const error = new AxiosError(
          'Request failed with status code 401',
          'ERR_BAD_REQUEST',
          config as InternalAxiosRequestConfig,
          null,
          {
            status: 401,
            statusText: 'Unauthorized',
            data: { code: 'SESSION_REVOKED', reason: 'refresh_mismatch' },
            headers: {},
            config: config as InternalAxiosRequestConfig,
          } as AxiosResponse
        );
        return Promise.reject(error);
      }
      return { data: {} } as AxiosResponse;
    });

    client.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
      const error = new AxiosError(
        'Request failed with status code 401',
        'ERR_BAD_REQUEST',
        config,
        null,
        {
          status: 401,
          statusText: 'Unauthorized',
          data: { detail: 'Token expired' },
          headers: {},
          config,
        } as AxiosResponse
      );
      return Promise.reject(error);
    };

    await expect(client.get('/orders')).rejects.toThrow();

    expect(mockAdapter.clearTokens).toHaveBeenCalled();
    expect(mockAdapter.onSessionRevoked).toHaveBeenCalledWith(
      expect.objectContaining({ code: 'SESSION_REVOKED', reason: 'refresh_mismatch' })
    );
    expect(mockAdapter.onUnauthorized).not.toHaveBeenCalled();
  });
});
