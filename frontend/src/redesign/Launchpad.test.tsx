// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Launchpad from './Launchpad';

vi.mock('../components/ui/beams-background', () => ({ BeamsBackground: () => null }));
vi.mock('../components/ui/shine-border', () => ({ ShineBorder: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock('../registry/magicui/border-beam', () => ({ BorderBeam: () => null }));

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('IntersectionObserver', class {
    observe() {}
    disconnect() {}
    unobserve() {}
  });
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); });

describe('landing diagnostics interaction', () => {
  it('validates before starting the decorative button animation', () => {
    const onRun = vi.fn();
    render(<Launchpad onRun={onRun} onDemo={vi.fn()} error={null} busy={false} />);
    fireEvent.click(screen.getByRole('button', { name: 'Run diagnostics' }));
    expect(screen.getByRole('alert').textContent).toContain('Enter a GitHub repository URL');
    expect(onRun).not.toHaveBeenCalled();
    expect(screen.queryByText('Targeting…')).toBeNull();
  });

  it('cancels delayed submission when leaving the landing page', () => {
    const onRun = vi.fn().mockResolvedValue(undefined);
    const { unmount } = render(<Launchpad onRun={onRun} onDemo={vi.fn()} error={null} busy={false} />);
    fireEvent.change(screen.getByRole('textbox', { name: 'Analyze a repository' }), { target: { value: 'https://github.com/acme/tests' } });
    fireEvent.click(screen.getByRole('button', { name: 'Run diagnostics' }));
    unmount();
    act(() => vi.advanceTimersByTime(1000));
    expect(onRun).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('locks duplicate form submissions before the animation finishes', async () => {
    const onRun = vi.fn().mockResolvedValue(undefined);
    render(<Launchpad onRun={onRun} onDemo={vi.fn()} error={null} busy={false} />);
    const input = screen.getByRole('textbox', { name: 'Analyze a repository' });
    fireEvent.change(input, { target: { value: 'https://github.com/acme/tests' } });
    const form = input.closest('form')!;
    act(() => { fireEvent.submit(form); fireEvent.submit(form); });
    await act(async () => vi.advanceTimersByTimeAsync(600));
    expect(onRun).toHaveBeenCalledTimes(1);
  });
});
