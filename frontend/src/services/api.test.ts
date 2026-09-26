import axios from 'axios';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { repositoryApi } from './api';

afterEach(() => vi.restoreAllMocks());

describe('repository API cancellation', () => {
  it('forwards AbortSignal to every analysis request without changing payloads', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({ data: {} });
    const controller = new AbortController();
    const clone = { repo_url: 'https://github.com/acme/api', num_runs: 5 };
    const local = { repo_path: 'sample-repo', num_runs: 5 };
    const upload = new FormData();
    upload.append('num_runs', '5');

    await repositoryApi.cloneAndAnalyze(clone, controller.signal);
    await repositoryApi.uploadAndAnalyze(upload, controller.signal);
    await repositoryApi.analyzeLocal(local, controller.signal);
    expect(post).toHaveBeenNthCalledWith(1, '/api/repository/clone-and-analyze', clone, { signal: controller.signal });
    expect(post).toHaveBeenNthCalledWith(2, '/api/repository/upload', upload, { headers: { 'Content-Type': 'multipart/form-data' }, signal: controller.signal });
    expect(post).toHaveBeenNthCalledWith(3, '/api/repository/analyze-local', local, { signal: controller.signal });
  });

  it('forwards AbortSignal for the source list', async () => {
    const get = vi.spyOn(axios, 'get').mockResolvedValue({ data: { sources: [] } });
    const controller = new AbortController();
    await repositoryApi.getSources(controller.signal);
    expect(get).toHaveBeenCalledExactlyOnceWith('/api/repository/sources', { signal: controller.signal });
  });

  it('keeps existing callers without a signal valid', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({ data: {} });
    const get = vi.spyOn(axios, 'get').mockResolvedValue({ data: { sources: [] } });
    await repositoryApi.analyzeLocal({ repo_path: 'sample-repo' });
    await repositoryApi.uploadAndAnalyze(new FormData());
    await repositoryApi.getSources();
    expect(post.mock.calls[0][2]?.signal).toBeUndefined();
    expect(post.mock.calls[1][2]?.signal).toBeUndefined();
    expect(get).toHaveBeenCalledExactlyOnceWith('/api/repository/sources', { signal: undefined });
  });
});
