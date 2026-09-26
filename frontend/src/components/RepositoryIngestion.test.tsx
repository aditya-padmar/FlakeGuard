// @vitest-environment jsdom
import { StrictMode } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { AxiosError, AxiosHeaders, CanceledError, type AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import RepositoryIngestion from './RepositoryIngestion';
import { repositoryApi, type PipelineAnalysisResult } from '../services/api';

vi.mock('../services/api', () => ({
  repositoryApi: {
    getSources: vi.fn(),
    cloneAndAnalyze: vi.fn(),
    uploadAndAnalyze: vi.fn(),
    analyzeLocal: vi.fn(),
  },
}));

const result: PipelineAnalysisResult = {
  status: 'success', pipeline_id: 'test', source_type: 'github', repository: 'acme/api', branch: 'main', commit_sha: 'abc',
  started_at: '', completed_at: '', runs: 5,
  detection: { total_runs: 5, flaky_tests_count: 0, confidence: 0, flaky_tests: [] },
  classifications: [], fixes: [], quarantine_audit: {},
};
const response = <T,>(data: T): AxiosResponse<T> => ({ data, status: 200, statusText: 'OK', headers: {}, config: { headers: new AxiosHeaders() } });
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((accept, fail) => { resolve = accept; reject = fail; });
  return { promise, resolve, reject };
}

type Source = 'github' | 'upload' | 'local';
function submitSource(source: Source, container: HTMLElement) {
  let label = /Clone & Analyze with Bob Agent/;
  if (source === 'upload') {
    fireEvent.click(screen.getByRole('button', { name: /Upload Test Suite/ }));
    const input = container.querySelector<HTMLInputElement>('input[type="file"]')!;
    fireEvent.change(input, { target: { files: [new File(['def test_ok(): pass'], 'test_ok.py', { type: 'text/plain' })] } });
    label = /Upload & Run Full Analysis/;
  } else if (source === 'local') {
    fireEvent.click(screen.getByRole('button', { name: /Local \/ Sample Repo/ }));
    label = /Run Analysis on sample-repo/;
  }
  const form = screen.getByRole('button', { name: label }).closest('form')!;
  fireEvent.submit(form);
  return form;
}
function pendingAnalysis() {
  const request = deferred<AxiosResponse<PipelineAnalysisResult>>();
  vi.mocked(repositoryApi.cloneAndAnalyze).mockReturnValue(request.promise);
  vi.mocked(repositoryApi.uploadAndAnalyze).mockReturnValue(request.promise);
  vi.mocked(repositoryApi.analyzeLocal).mockReturnValue(request.promise);
  return request;
}
function signalFor(source: Source) {
  if (source === 'github') return vi.mocked(repositoryApi.cloneAndAnalyze).mock.calls[0][1];
  if (source === 'upload') return vi.mocked(repositoryApi.uploadAndAnalyze).mock.calls[0][1];
  return vi.mocked(repositoryApi.analyzeLocal).mock.calls[0][1];
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.resetAllMocks();
  vi.mocked(repositoryApi.getSources).mockResolvedValue(response({ sources: [] }));
});
afterEach(() => {
  cleanup();
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('repository request lifecycle', () => {
  it.each<Source>(['github', 'upload', 'local'])('aborts %s and suppresses completion after unmount', async source => {
    const request = pendingAnalysis();
    const onComplete = vi.fn();
    const { container, unmount } = render(<RepositoryIngestion onAnalysisComplete={onComplete} />);
    await act(async () => {});
    submitSource(source, container);
    const signal = signalFor(source);
    expect(signal).toBeInstanceOf(AbortSignal);
    expect(signal?.aborted).toBe(false);
    expect(vi.getTimerCount()).toBe(source === 'github' ? 3 : source === 'upload' ? 2 : 0);

    unmount();
    expect(signal?.aborted).toBe(true);
    expect(vi.mocked(repositoryApi.getSources).mock.calls[0][0]?.aborted).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
    // The transport deliberately ignores abort and completes anyway.
    await act(async () => { vi.advanceTimersByTime(10_000); request.resolve(response(result)); });
    expect(onComplete).not.toHaveBeenCalled();
  });

  it.each<Source>(['github', 'upload', 'local'])('completes %s once and clears progress timers', async source => {
    const request = pendingAnalysis();
    const onComplete = vi.fn();
    const { container } = render(<RepositoryIngestion onAnalysisComplete={onComplete} />);
    await act(async () => {});
    submitSource(source, container);
    await act(async () => { request.resolve(response(result)); });
    expect(onComplete).toHaveBeenCalledExactlyOnceWith(result);
    expect(vi.getTimerCount()).toBe(0);
    expect(screen.getByText('Analysis Completed Successfully!')).toBeTruthy();
  });

  it('locks duplicate submissions before React disables the submit button', async () => {
    const request = pendingAnalysis();
    const onComplete = vi.fn();
    const { container } = render(<RepositoryIngestion onAnalysisComplete={onComplete} />);
    await act(async () => {});
    act(() => {
      const form = submitSource('github', container);
      fireEvent.submit(form);
    });
    expect(repositoryApi.cloneAndAnalyze).toHaveBeenCalledTimes(1);
    await act(async () => { request.resolve(response(result)); });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it('rejects stale source responses from StrictMode effect replay', async () => {
    const first = deferred<AxiosResponse<{ sources: { id: string; name: string; path: string; description: string }[] }>>();
    const second = deferred<AxiosResponse<{ sources: { id: string; name: string; path: string; description: string }[] }>>();
    vi.mocked(repositoryApi.getSources).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    render(<StrictMode><RepositoryIngestion onAnalysisComplete={vi.fn()} /></StrictMode>);
    expect(repositoryApi.getSources).toHaveBeenCalledTimes(2);
    expect(vi.mocked(repositoryApi.getSources).mock.calls[0][0]?.aborted).toBe(true);
    expect(vi.mocked(repositoryApi.getSources).mock.calls[1][0]?.aborted).toBe(false);
    fireEvent.click(screen.getByRole('button', { name: /Local \/ Sample Repo/ }));
    await act(async () => { second.resolve(response({ sources: [{ id: 'new', name: 'Current source', path: 'new', description: 'Current' }] })); });
    await act(async () => { first.resolve(response({ sources: [{ id: 'old', name: 'Stale source', path: 'old', description: 'Stale' }] })); });
    expect(screen.getByText('Current source')).toBeTruthy();
    expect(screen.queryByText('Stale source')).toBeNull();
  });

  it('keeps a new route instance pending when the old request resolves', async () => {
    const oldRequest = deferred<AxiosResponse<PipelineAnalysisResult>>();
    const newRequest = deferred<AxiosResponse<PipelineAnalysisResult>>();
    vi.mocked(repositoryApi.cloneAndAnalyze).mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(newRequest.promise);
    const onComplete = vi.fn();
    const first = render(<RepositoryIngestion onAnalysisComplete={onComplete} />);
    await act(async () => {});
    submitSource('github', first.container);
    first.unmount();
    const second = render(<RepositoryIngestion onAnalysisComplete={onComplete} />);
    await act(async () => {});
    submitSource('github', second.container);
    await act(async () => { oldRequest.resolve(response(result)); });
    expect(onComplete).not.toHaveBeenCalled();
    expect(screen.getByRole<HTMLButtonElement>('button', { name: /Cloning & Running Pipeline/ }).disabled).toBe(true);
    await act(async () => { newRequest.resolve(response({ ...result, pipeline_id: 'new' })); });
    expect(onComplete).toHaveBeenCalledExactlyOnceWith({ ...result, pipeline_id: 'new' });
  });

  it('shows typed Axios details and allows a clean retry after failure', async () => {
    const first = deferred<AxiosResponse<PipelineAnalysisResult>>();
    const second = deferred<AxiosResponse<PipelineAnalysisResult>>();
    vi.mocked(repositoryApi.cloneAndAnalyze).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const onComplete = vi.fn();
    const { container } = render(<RepositoryIngestion onAnalysisComplete={onComplete} />);
    await act(async () => {});
    submitSource('github', container);
    const failureResponse = response({ detail: 'Repository is not accessible' });
    await act(async () => { first.reject(new AxiosError('Request failed', 'ERR_BAD_REQUEST', undefined, undefined, failureResponse)); });
    expect(screen.getByText('GitHub Analysis Failed: Repository is not accessible')).toBeTruthy();
    expect(vi.getTimerCount()).toBe(0);
    expect(onComplete).not.toHaveBeenCalled();
    submitSource('github', container);
    expect(screen.queryByText(/GitHub Analysis Failed/)).toBeNull();
    await act(async () => { second.resolve(response(result)); });
    expect(onComplete).toHaveBeenCalledExactlyOnceWith(result);
  });

  it('does not display cancellation as an API error', async () => {
    const request = pendingAnalysis();
    const { container } = render(<RepositoryIngestion onAnalysisComplete={vi.fn()} />);
    await act(async () => {});
    submitSource('github', container);
    await act(async () => { request.reject(new CanceledError()); });
    expect(screen.queryByText(/GitHub Analysis Failed/)).toBeNull();
    expect(screen.getByRole<HTMLButtonElement>('button', { name: /Clone & Analyze with Bob Agent/ }).disabled).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });
});
