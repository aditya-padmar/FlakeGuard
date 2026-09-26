// @vitest-environment jsdom
import { act, cleanup, render, renderHook, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { WorkspaceProvider, useWorkspace } from './WorkspaceContext';
import { useElapsedSeconds } from './useElapsedSeconds';
import { createAnimationClock } from '../components/ui/animation-clock';
import { repositoryApi, type PipelineAnalysisResult } from '../services/api';

vi.mock('../services/api', () => ({ repositoryApi: { cloneAndAnalyze: vi.fn() } }));
const emptyResult: PipelineAnalysisResult = { pipeline_id: 'test', source_type: 'github', repository: 'https://github.com/acme/test', branch: 'main', commit_sha: 'abc', started_at: '', completed_at: '', runs: 0, detection: { total_runs: 0, flaky_tests_count: 0, confidence: 0, flaky_tests: [] }, classifications: [], fixes: [] };

beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date('2026-09-26T12:00:00Z')); });
afterEach(() => { cleanup(); vi.useRealTimers(); vi.resetAllMocks(); });

describe('background frame budget', () => {
  it('caps drawing on high-refresh displays while retaining elapsed-time speed', () => {
    const clock = createAnimationClock();
    const deltas: number[] = [];
    for (let frame = 0; frame <= 144; frame++) {
      const delta = clock.tick(frame * 1000 / 144);
      if (delta !== null) deltas.push(delta);
    }
    expect(deltas.length).toBeLessThanOrEqual(31);
    expect(deltas.length).toBeGreaterThan(20);
    expect(deltas.reduce((sum, delta) => sum + delta, 0)).toBeGreaterThan(55);
    clock.reset();
    expect(clock.tick(100000)).toBe(0);
  });
});

describe('isolated pipeline clock', () => {
  it('updates elapsed time locally and removes its interval on unmount', () => {
    const started = Date.now();
    const { result, unmount } = renderHook(() => useElapsedSeconds(started));
    expect(result.current).toBe(0);
    act(() => vi.advanceTimersByTime(3200));
    expect(result.current).toBe(3);
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('does not render workspace consumers on live elapsed ticks', async () => {
    let workspace: ReturnType<typeof useWorkspace> | undefined;
    let renders = 0;
    let resolve: ((value: { data: PipelineAnalysisResult }) => void) | undefined;
    vi.mocked(repositoryApi.cloneAndAnalyze).mockImplementation(() => new Promise(done => { resolve = done as typeof resolve; }));
    function Probe() { workspace = useWorkspace(); renders++; return <span>{workspace.process?.mode ?? 'idle'}</span>; }
    render(<WorkspaceProvider><Probe /></WorkspaceProvider>);
    let request: Promise<void> | undefined;
    act(() => { request = workspace!.startLive('https://github.com/acme/test', 'main'); });
    expect(screen.getByText('live')).toBeDefined();
    const afterStart = renders;
    act(() => vi.advanceTimersByTime(10000));
    expect(renders).toBe(afterStart);
    await act(async () => { resolve!({ data: emptyResult }); await request; });
    expect(screen.getByText('idle')).toBeDefined();
  });

  it('only broadcasts demo stage changes and cancels its schedule', () => {
    let workspace: ReturnType<typeof useWorkspace> | undefined;
    let renders = 0;
    function Probe() { workspace = useWorkspace(); renders++; return null; }
    render(<WorkspaceProvider><Probe /></WorkspaceProvider>);
    act(() => workspace!.startDemo());
    const afterStart = renders;
    act(() => vi.advanceTimersByTime(2000));
    expect(renders).toBe(afterStart);
    act(() => vi.advanceTimersByTime(500));
    expect(workspace!.process?.step).toBe(1);
    expect(renders).toBe(afterStart + 1);
    act(() => workspace!.cancel());
    expect(workspace!.process).toBeNull();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('preserves results when the backend reports an unsupported framework', async () => {
    vi.mocked(repositoryApi.cloneAndAnalyze).mockResolvedValue({ data: { ...emptyResult, status: 'unsupported', message: 'Jest execution is not configured.' } } as Awaited<ReturnType<typeof repositoryApi.cloneAndAnalyze>>);
    let workspace: ReturnType<typeof useWorkspace> | undefined;
    function Probe() { workspace = useWorkspace(); return null; }
    render(<WorkspaceProvider><Probe /></WorkspaceProvider>);
    const original = workspace!.data;
    await act(async () => { await workspace!.startLive('https://github.com/acme/test', 'main'); });
    expect(workspace!.data).toBe(original);
    expect(workspace!.error).toContain('Jest execution');
  });
});
