import {describe, it, expect, vi, beforeEach, afterEach} from 'vitest';

// Mock getConfig before importing base-client
vi.mock('@/lib/config', () => ({
  getConfig: () => ({
    API_BASE_URL: 'http://localhost:9421',
    API_PREFIX: '/api/v2',
  }),
}));

// We test the exported apiClient methods and the internal buildUrl logic
// by importing the module and using mocked fetch
describe('base-client', () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    // Mock document.cookie for cookie helpers
    vi.stubGlobal('document', {
      cookie: 'access_token=test-token; refresh_token=refresh-val',
    });
    // Mock window.location
    vi.stubGlobal('window', {
      location: {
        pathname: '/test',
        search: '',
        href: '',
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // We need to dynamically import after mocks are set up
  async function getClient() {
    const mod = await import('./base-client');
    return mod.apiClient;
  }

  describe('apiClient.get', () => {
    it('should make a GET request with correct URL', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true, data: {id: 1}})),
      });

      const client = await getClient();
      const result = await client.get<{ id: number }>('/articles');

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, opts] = fetchSpy.mock.calls[0];
      expect(url).toContain('/api/v2/articles');
      expect(opts.method).toBe('GET');
      expect(opts.credentials).toBe('include');
      expect(result.success).toBe(true);
      expect(result.data).toEqual({id: 1});
    });

    it('should append query params for GET requests', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true, data: []})),
      });

      const client = await getClient();
      await client.get('/articles', {page: '1', status: 'published'});

      const [url] = fetchSpy.mock.calls[0];
      expect(url).toContain('page=1');
      expect(url).toContain('status=published');
    });

    it('should filter null/undefined params', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true, data: []})),
      });

      const client = await getClient();
      await client.get('/articles', {page: '1', status: undefined, tag: null, q: ''});

      const [url] = fetchSpy.mock.calls[0];
      expect(url).toContain('page=1');
      expect(url).not.toContain('status=');
      expect(url).not.toContain('tag=');
      expect(url).not.toContain('q=');
    });
  });

  describe('apiClient.post', () => {
    it('should make a POST request with JSON body', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true, data: {id: 2}})),
      });

      const client = await getClient();
      const result = await client.post('/articles', {title: 'Test'});

      const [url, opts] = fetchSpy.mock.calls[0];
      expect(url).toContain('/api/v2/articles');
      expect(opts.method).toBe('POST');
      expect(opts.headers['Content-Type']).toBe('application/json');
      expect(opts.body).toBe(JSON.stringify({title: 'Test'}));
      expect(result.success).toBe(true);
    });
  });

  describe('apiClient.put', () => {
    it('should make a PUT request', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.put('/articles/1', {title: 'Updated'});

      const [url, opts] = fetchSpy.mock.calls[0];
      expect(url).toContain('/api/v2/articles/1');
      expect(opts.method).toBe('PUT');
    });
  });

  describe('apiClient.delete', () => {
    it('should make a DELETE request', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.delete('/articles/1');

      const [url, opts] = fetchSpy.mock.calls[0];
      expect(url).toContain('/api/v2/articles/1');
      expect(opts.method).toBe('DELETE');
    });
  });

  describe('apiClient.postForm', () => {
    it('should make a POST request with form-urlencoded body', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.postForm('/auth/login', {username: 'admin', password: '123'});

      const [, opts] = fetchSpy.mock.calls[0];
      expect(opts.headers['Content-Type']).toBe('application/x-www-form-urlencoded');
      expect(opts.body).toContain('username=admin');
      expect(opts.body).toContain('password=123');
    });
  });

  describe('Authorization header', () => {
    it('should include Authorization header when access_token cookie exists', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.get('/me');

      const [, opts] = fetchSpy.mock.calls[0];
      expect(opts.headers.Authorization).toBe('Bearer test-token');
    });
  });

  describe('error handling', () => {
    it('should handle non-JSON response', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 500,
        text: () => Promise.resolve('Internal Server Error'),
      });

      const client = await getClient();
      const result = await client.get('/broken');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Internal Server Error');
    });

    it('should handle network error', async () => {
      fetchSpy.mockRejectedValueOnce(new Error('Network failure'));

      const client = await getClient();
      const result = await client.get('/offline');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network failure');
    });

    it('should handle fetch throwing non-Error', async () => {
      fetchSpy.mockRejectedValueOnce('string error');

      const client = await getClient();
      const result = await client.get('/fail');

      expect(result.success).toBe(false);
      expect(result.error).toBe('网络异常');
    });
  });

  describe('apiClient.request', () => {
    it('should support custom method via request()', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.request('/articles/1/publish', {method: 'PATCH'});

      const [, opts] = fetchSpy.mock.calls[0];
      expect(opts.method).toBe('PATCH');
    });
  });

  describe('URL building', () => {
    it('should prefix paths without /api/ with /api/v2', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.get('articles');

      const [url] = fetchSpy.mock.calls[0];
      expect(url).toContain('/api/v2/articles');
    });

    it('should not double-prefix paths that already start with /api/', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.get('/api/v1/old-endpoint');

      const [url] = fetchSpy.mock.calls[0];
      expect(url).toContain('/api/v1/old-endpoint');
      expect(url).not.toContain('/api/v2/api/v1');
    });

    it('should use absolute URL as-is', async () => {
      fetchSpy.mockResolvedValueOnce({
        status: 200,
        text: () => Promise.resolve(JSON.stringify({success: true})),
      });

      const client = await getClient();
      await client.get('https://external-api.com/data');

      const [url] = fetchSpy.mock.calls[0];
      expect(url).toBe('https://external-api.com/data');
    });
  });
});
