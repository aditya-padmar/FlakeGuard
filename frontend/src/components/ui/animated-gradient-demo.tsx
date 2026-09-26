import AnimatedGradient from '@/components/ui/animated-gradient';

export default function AnimatedGradientDemo() {
  return (
    <div className="relative isolate flex min-h-[400px] items-center justify-center overflow-hidden rounded-xl p-8">
      <AnimatedGradient config={{ preset: 'Prism', speed: 10 }} />
      <div className="relative rounded-lg bg-black/60 px-6 py-4 text-white">Animated gradient preview</div>
    </div>
  );
}
