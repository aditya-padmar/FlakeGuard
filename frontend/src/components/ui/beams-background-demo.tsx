import { BeamsBackground } from '@/components/ui/beams-background';

export function BeamsBackgroundDemo() {
  return <BeamsBackground>
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 text-center">
      <h1 className="text-6xl font-semibold tracking-tighter text-white md:text-7xl">Beams<br />Background</h1>
      <p className="text-lg text-white/70 md:text-2xl">For your pleasure</p>
    </div>
  </BeamsBackground>;
}
