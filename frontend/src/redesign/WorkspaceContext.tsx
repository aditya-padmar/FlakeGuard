import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import axios from 'axios';
import { repositoryApi, type PipelineAnalysisResult } from '../services/api';
import { adaptAnalysis, createDemoData, parseGithubUrl, type WorkspaceData } from './data';

interface ProcessState { mode: 'demo' | 'live'; repository: string; step: number; startedAt: number }
interface WorkspaceContextValue {
  data: WorkspaceData;
  process: ProcessState | null;
  error: string | null;
  startDemo: () => void;
  startLive: (url: string, branch: string) => Promise<void>;
  cancel: () => void;
  validateDemo: (id: string) => void;
  setAnalysis: (result: PipelineAnalysisResult) => void;
}
const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState(createDemoData);
  const [process, setProcess] = useState<ProcessState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const clearTimer = useCallback(() => { if (timer.current) clearInterval(timer.current); timer.current = null; }, []);
  const cancel = useCallback(() => {
    generation.current += 1;
    controller.current?.abort();
    clearTimer();
    setProcess(null);
  }, [clearTimer]);
  useEffect(() => () => { generation.current += 1; controller.current?.abort(); clearTimer(); }, [clearTimer]);

  const startDemo = useCallback(() => {
    cancel();
    setError(null);
    const started = Date.now();
    setProcess({ mode: 'demo', repository: 'acme / commerce-api', step: 0, startedAt: started });
    timer.current = setInterval(() => {
      const elapsed = (Date.now() - started) / 1000;
      if (elapsed >= 15) {
        clearTimer();
        setData(createDemoData());
        setProcess(null);
      } else {
        const step = Math.min(5, Math.floor(elapsed / 2.5));
        setProcess(previous => previous && previous.step !== step ? { ...previous, step } : previous);
      }
    }, 2500);
  }, [cancel, clearTimer]);

  const startLive = useCallback(async (url: string, branch: string) => {
    const normalized = parseGithubUrl(url);
    if (!normalized) { setError('Enter a valid HTTPS GitHub repository URL.'); return; }
    cancel();
    const currentGeneration = generation.current;
    const requestController = new AbortController();
    controller.current = requestController;
    const started = Date.now();
    setProcess({ mode: 'live', repository: normalized.replace('https://github.com/', ''), step: 0, startedAt: started });
    try {
      const response = await repositoryApi.cloneAndAnalyze({ repo_url: normalized, branch: branch.trim() || 'main', num_runs: 10 }, requestController.signal);
      if (generation.current !== currentGeneration) return;
      const result = response.data;
      if (result.status === 'unsupported') {
        setError(result.errors?.[0]?.message || result.message || 'This repository’s test framework is not supported by the configured runner.');
        return;
      }
      if (result.status === 'no_tests') {
        const backendMsg = result.errors?.[0]?.message || result.message || '';
        // Backend message already contains the base description; only append if
        // it includes an extra hint (e.g. ImportError detail from pytest stderr)
        const hasHint = backendMsg.toLowerCase().includes('hint:') || backendMsg.toLowerCase().includes('modulenotfounderror') || backendMsg.toLowerCase().includes('importerror');
        const msg = hasHint
          ? backendMsg
          : 'No pytest-compatible tests were found in this repository. FlakeGuard requires a Python project with test files named test_*.py or *_test.py.';
        setError(msg);
        return;
      }
      if (result.status === 'error') {
        const reason = result.errors?.[0]?.message || result.message || 'Analysis failed.';
        // Strip any local server paths from the message before showing to the user
        const safe = reason.replace(/[A-Za-z]:\\[^\s.]+/g, '<server path>').replace(/\/[^\s]*\/data\/repos\/[^\s]*/g, '<server path>');
        setError(`Analysis failed: ${safe}`);
        return;
      }
      // Ensure the user gets to see the complete investigation pipeline before transitioning to results
      const isTestEnv = typeof window !== 'undefined' && (import.meta as unknown as { env?: { MODE?: string } })?.env?.MODE === 'test';
      if (!isTestEnv) {
        const elapsedMs = Date.now() - started;
        const minDurationMs = 13500;
        if (elapsedMs < minDurationMs) {
          await new Promise(resolve => setTimeout(resolve, minDurationMs - elapsedMs));
        }
      }
      if (generation.current !== currentGeneration) return;
      setData(adaptAnalysis(result));
    } catch (cause) {
      if (generation.current !== currentGeneration || axios.isCancel(cause)) return;
      const detail = axios.isAxiosError(cause) ? cause.response?.data?.detail : null;
      const rawMessage = typeof detail === 'string' ? detail : null;
      // Sanitize any local server paths that may appear in error details
      const safeMessage = rawMessage
        ? rawMessage.replace(/[A-Za-z]:\\[^\s.]+/g, '<server path>').replace(/\/[^\s]*\/data\/repos\/[^\s]*/g, '<server path>')
        : null;
      setError(safeMessage || 'The analysis service could not complete this request. Check that the backend is running on port 8000 and that the repository is accessible. Your previous results have been kept.');
    } finally {
      if (generation.current === currentGeneration) { clearTimer(); setProcess(null); }
    }
  }, [cancel, clearTimer]);

  const validateDemo = useCallback((id: string) => {
    setData(previous => previous.mode !== 'demo' ? previous : { ...previous, tests: previous.tests.map(test => test.id === id && test.diff ? { ...test, fixStatus: 'validated' } : test) });
  }, []);
  const setAnalysis = useCallback((result: PipelineAnalysisResult) => { cancel(); setError(null); setData(adaptAnalysis(result)); }, [cancel]);
  const value = useMemo(() => ({ data, process, error, startDemo, startLive, cancel, validateDemo, setAnalysis }), [data, process, error, startDemo, startLive, cancel, validateDemo, setAnalysis]);
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error('useWorkspace must be used within WorkspaceProvider');
  return context;
}
