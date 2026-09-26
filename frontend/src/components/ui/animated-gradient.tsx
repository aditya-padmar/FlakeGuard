"use client";

import { useEffect, useRef, type CSSProperties } from "react";

type PatternShape = "Checks" | "Stripes" | "Edge";
type PresetName = "Prism" | "Lava" | "Plasma" | "Pulse" | "Vortex" | "Mist";

const PatternShapes: Record<PatternShape, number> = {
  Checks: 0,
  Stripes: 1,
  Edge: 2,
};

interface PresetParams {
  color1: string;
  color2: string;
  color3: string;
  rotation: number;
  proportion: number;
  scale: number;
  speed: number;
  distortion: number;
  swirl: number;
  swirlIterations: number;
  softness: number;
  offset: number;
  shape: PatternShape;
  shapeSize: number;
}

const presets: Record<PresetName, PresetParams> = {
  Prism: {
    color1: "#050505",
    color2: "#66B3FF",
    color3: "#FFFFFF",
    rotation: -50,
    proportion: 1,
    scale: 0.01,
    speed: 30,
    distortion: 0,
    swirl: 50,
    swirlIterations: 16,
    softness: 47,
    offset: -299,
    shape: "Checks",
    shapeSize: 45,
  },
  Lava: {
    color1: "#FF9F21",
    color2: "#FF0303",
    color3: "#000000",
    rotation: 114,
    proportion: 100,
    scale: 0.52,
    speed: 30,
    distortion: 7,
    swirl: 18,
    swirlIterations: 20,
    softness: 100,
    offset: 717,
    shape: "Edge",
    shapeSize: 12,
  },
  Plasma: {
    color1: "#B566FF",
    color2: "#000000",
    color3: "#000000",
    rotation: 0,
    proportion: 63,
    scale: 0.75,
    speed: 30,
    distortion: 5,
    swirl: 61,
    swirlIterations: 5,
    softness: 100,
    offset: -168,
    shape: "Checks",
    shapeSize: 28,
  },
  Pulse: {
    color1: "#66FF85",
    color2: "#000000",
    color3: "#000000",
    rotation: -167,
    proportion: 92,
    scale: 0,
    speed: 20,
    distortion: 54,
    swirl: 75,
    swirlIterations: 3,
    softness: 28,
    offset: -813,
    shape: "Checks",
    shapeSize: 79,
  },
  Vortex: {
    color1: "#000000",
    color2: "#FFFFFF",
    color3: "#000000",
    rotation: 50,
    proportion: 41,
    scale: 0.4,
    speed: 20,
    distortion: 0,
    swirl: 100,
    swirlIterations: 3,
    softness: 5,
    offset: -744,
    shape: "Stripes",
    shapeSize: 80,
  },
  Mist: {
    color1: "#050505",
    color2: "#FF66B8",
    color3: "#050505",
    rotation: 0,
    proportion: 33,
    scale: 0.48,
    speed: 39,
    distortion: 4,
    swirl: 65,
    swirlIterations: 5,
    softness: 100,
    offset: -235,
    shape: "Edge",
    shapeSize: 48,
  },
};

interface CustomConfig {
  preset: "custom";
  color1: string;
  color2: string;
  color3: string;
  rotation?: number;
  proportion?: number;
  scale?: number;
  speed?: number;
  distortion?: number;
  swirl?: number;
  swirlIterations?: number;
  softness?: number;
  offset?: number;
  shape?: PatternShape;
  shapeSize?: number;
}

interface PresetConfig {
  preset: PresetName;
  speed?: number;
}

export type GradientConfig = CustomConfig | PresetConfig;

interface NoiseConfig {
  opacity: number;
  scale?: number;
}

/** Decorative background only; place content in a sibling above this layer. */
export interface AnimatedGradientProps {
  config?: GradientConfig;
  noise?: NoiseConfig;
  radius?: string;
  style?: CSSProperties;
  className?: string;
}

function clamp(value: number, min: number, max: number, fallback = min): number {
  return Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : fallback;
}

function resolveParams(config: GradientConfig): PresetParams {
  const source: PresetParams = config.preset === "custom"
    ? {
        color1: config.color1,
        color2: config.color2,
        color3: config.color3,
        rotation: config.rotation ?? 0,
        proportion: config.proportion ?? 35,
        scale: config.scale ?? 1,
        speed: config.speed ?? 25,
        distortion: config.distortion ?? 12,
        swirl: config.swirl ?? 80,
        swirlIterations: config.swirlIterations ?? 10,
        softness: config.softness ?? 100,
        offset: config.offset ?? 0,
        shape: config.shape ?? "Checks",
        shapeSize: config.shapeSize ?? 10,
      }
    : {
        ...(presets[config.preset] ?? presets.Prism),
        speed: config.speed ?? (presets[config.preset] ?? presets.Prism).speed,
      };

  return {
    ...source,
    color1: cssColor(source.color1),
    color2: cssColor(source.color2),
    color3: cssColor(source.color3),
    rotation: clamp(source.rotation, -360, 360),
    proportion: clamp(source.proportion, 0, 100, 35),
    scale: clamp(source.scale, 0, 10, 1),
    speed: clamp(source.speed, 0, 100, 25),
    distortion: clamp(source.distortion, 0, 100, 12),
    swirl: clamp(source.swirl, 0, 200, 80),
    swirlIterations: Math.round(clamp(source.swirlIterations, 0, 30, 10)),
    softness: clamp(source.softness, 0, 100, 100),
    offset: clamp(source.offset, -10000, 10000),
    shape: Object.prototype.hasOwnProperty.call(PatternShapes, source.shape) ? source.shape : "Checks",
    shapeSize: clamp(source.shapeSize, 0, 100, 10),
  };
}

export function AnimatedGradient({
  config = { preset: "Prism" },
  noise,
  radius = "0px",
  style,
  className,
}: AnimatedGradientProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const params = resolveParams(config);
  // Resolved scalar values, not the caller's object identity, own the GPU lifetime.
  const paramsKey = JSON.stringify(params);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const values: PresetParams = JSON.parse(paramsKey);
    let gl: WebGL2RenderingContext | null;
    try {
      gl = canvas.getContext("webgl2", {
        premultipliedAlpha: true,
        alpha: true,
        antialias: false,
        depth: false,
        stencil: false,
      });
    } catch {
      return;
    }
    if (!gl) return;
    const context = gl;
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    let reducedMotion = motionQuery.matches;
    let intersecting = typeof IntersectionObserver === "undefined";
    let disposed = false;
    let ready = false;
    let hasSize = false;
    let frameId: number | undefined;
    let lastTime: number | undefined;
    let elapsed = 0;
    let pixelRatio = 1;
    let maxDimension = 4096;
    let program: WebGLProgram | null = null;
    let positionBuffer: WebGLBuffer | null = null;
    let vertexShader: WebGLShader | null = null;
    let fragmentShader: WebGLShader | null = null;
    let uniforms: Record<string, WebGLUniformLocation | null> = {};

    const stop = () => {
      if (frameId !== undefined) cancelAnimationFrame(frameId);
      frameId = undefined;
      lastTime = undefined;
    };

    const release = () => {
      stop();
      ready = false;
      canvas.style.visibility = "hidden";
      if (positionBuffer) context.deleteBuffer(positionBuffer);
      if (program) context.deleteProgram(program);
      if (vertexShader) context.deleteShader(vertexShader);
      if (fragmentShader) context.deleteShader(fragmentShader);
      positionBuffer = null;
      program = null;
      vertexShader = null;
      fragmentShader = null;
      uniforms = {};
    };

    const canRender = () => !disposed && ready && hasSize && intersecting
      && !document.hidden && !context.isContextLost();
    const canAnimate = () => canRender() && !reducedMotion && values.speed > 0;

    const draw = () => {
      if (!canRender()) return;
      context.useProgram(program);
      context.uniform1f(uniforms.u_time, elapsed * (values.speed / 100) * 5 + values.offset * 0.01);
      context.uniform2f(uniforms.u_resolution, canvas.width, canvas.height);
      context.uniform1f(uniforms.u_pixelRatio, pixelRatio);
      context.drawArrays(context.TRIANGLES, 0, 6);
      canvas.style.visibility = "visible";
    };

    const animate = (time: number) => {
      frameId = undefined;
      if (!canAnimate()) {
        lastTime = undefined;
        return;
      }
      if (lastTime !== undefined) elapsed += Math.max(0, time - lastTime) / 1000;
      lastTime = time;
      draw();
      frameId = requestAnimationFrame(animate);
    };

    const refresh = () => {
      if (!canAnimate()) stop();
      draw();
      if (canAnimate() && frameId === undefined) {
        lastTime = performance.now();
        frameId = requestAnimationFrame(animate);
      }
    };

    const resize = () => {
      if (disposed) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      hasSize = width > 0 && height > 0;
      if (!hasSize) {
        stop();
        return;
      }
      // Cap both density and total allocation, including unusually wide/tall parents.
      pixelRatio = Math.min(
        clamp(window.devicePixelRatio || 1, 0.1, 1.5, 1),
        Math.sqrt(2_000_000 / (width * height)),
        maxDimension / width,
        maxDimension / height,
      );
      const nextWidth = Math.max(1, Math.floor(width * pixelRatio));
      const nextHeight = Math.max(1, Math.floor(height * pixelRatio));
      if (canvas.width !== nextWidth) canvas.width = nextWidth;
      if (canvas.height !== nextHeight) canvas.height = nextHeight;
      if (ready) context.viewport(0, 0, canvas.width, canvas.height);
      refresh();
    };

    const initialize = () => {
      if (disposed || context.isContextLost()) return;
      release();
      try {
        vertexShader = context.createShader(context.VERTEX_SHADER);
        fragmentShader = context.createShader(context.FRAGMENT_SHADER);
        if (!vertexShader || !fragmentShader) throw new Error("Shader allocation failed");
        context.shaderSource(vertexShader, VERTEX_SHADER);
        context.compileShader(vertexShader);
        if (!context.getShaderParameter(vertexShader, context.COMPILE_STATUS)) {
          throw new Error("Vertex shader compilation failed");
        }
        context.shaderSource(fragmentShader, FRAGMENT_SHADER);
        context.compileShader(fragmentShader);
        if (!context.getShaderParameter(fragmentShader, context.COMPILE_STATUS)) {
          throw new Error("Fragment shader compilation failed");
        }
        program = context.createProgram();
        if (!program) throw new Error("Program allocation failed");
        context.attachShader(program, vertexShader);
        context.attachShader(program, fragmentShader);
        context.linkProgram(program);
        if (!context.getProgramParameter(program, context.LINK_STATUS)) {
          throw new Error("Shader linking failed");
        }
        context.useProgram(program);
        // Once linked, the executable no longer needs attached shader objects.
        context.detachShader(program, vertexShader);
        context.detachShader(program, fragmentShader);
        context.deleteShader(vertexShader);
        context.deleteShader(fragmentShader);
        vertexShader = null;
        fragmentShader = null;

        positionBuffer = context.createBuffer();
        if (!positionBuffer) throw new Error("Buffer allocation failed");
        context.bindBuffer(context.ARRAY_BUFFER, positionBuffer);
        context.bufferData(
          context.ARRAY_BUFFER,
          new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
          context.STATIC_DRAW,
        );
        const position = context.getAttribLocation(program, "a_position");
        if (position < 0) throw new Error("Missing position attribute");
        context.enableVertexAttribArray(position);
        context.vertexAttribPointer(position, 2, context.FLOAT, false, 0, 0);
        for (const name of [
          "u_time", "u_resolution", "u_pixelRatio", "u_scale", "u_rotation",
          "u_color1", "u_color2", "u_color3", "u_proportion", "u_softness",
          "u_shape", "u_shapeScale", "u_distortion", "u_swirl", "u_swirlIterations",
        ]) {
          uniforms[name] = context.getUniformLocation(program, name);
          if (uniforms[name] === null) throw new Error(`Missing uniform ${name}`);
        }
        context.uniform1f(uniforms.u_scale, values.scale);
        context.uniform1f(uniforms.u_rotation, (values.rotation * Math.PI) / 180);
        for (const [name, color] of [
          ["u_color1", values.color1], ["u_color2", values.color2], ["u_color3", values.color3],
        ]) {
          context.uniform4f(uniforms[name], ...hexToRgba(color));
        }
        context.uniform1f(uniforms.u_proportion, values.proportion / 100);
        context.uniform1f(uniforms.u_softness, values.softness / 100);
        context.uniform1f(uniforms.u_shape, PatternShapes[values.shape]);
        context.uniform1f(uniforms.u_shapeScale, values.shapeSize / 100);
        context.uniform1f(uniforms.u_distortion, values.distortion / 50);
        context.uniform1f(uniforms.u_swirl, values.swirl / 100);
        context.uniform1f(uniforms.u_swirlIterations, values.swirl === 0 ? 0 : values.swirlIterations);
        const viewport = context.getParameter(context.MAX_VIEWPORT_DIMS) as Int32Array;
        maxDimension = Math.max(1, Math.min(
          4096,
          context.getParameter(context.MAX_RENDERBUFFER_SIZE) as number,
          viewport[0], viewport[1],
        ));
        if (context.getError() !== context.NO_ERROR) throw new Error("WebGL initialization failed");
        ready = true;
        resize();
      } catch {
        // Keep the CSS gradient visible when WebGL is unavailable or compilation fails.
        release();
      }
    };

    const onVisibility = () => refresh();
    const onMotion = () => {
      reducedMotion = motionQuery.matches;
      refresh();
    };
    const onContextLost = (event: Event) => {
      event.preventDefault();
      release();
    };
    const onContextRestored = () => initialize();
    canvas.addEventListener("webglcontextlost", onContextLost);
    canvas.addEventListener("webglcontextrestored", onContextRestored);
    document.addEventListener("visibilitychange", onVisibility);
    motionQuery.addEventListener("change", onMotion);
    window.addEventListener("resize", resize);
    const resizeObserver = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
    const intersectionObserver = typeof IntersectionObserver !== "undefined"
      ? new IntersectionObserver((entries) => {
          if (disposed) return;
          intersecting = entries.some((entry) => entry.target === container && entry.isIntersecting);
          refresh();
        })
      : null;
    resizeObserver?.observe(container);
    intersectionObserver?.observe(container);
    initialize();

    return () => {
      disposed = true;
      resizeObserver?.disconnect();
      intersectionObserver?.disconnect();
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
      motionQuery.removeEventListener("change", onMotion);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      canvas.removeEventListener("webglcontextrestored", onContextRestored);
      release();
    };
  }, [paramsKey]);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className={className}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 0,
        borderRadius: radius,
        overflow: "hidden",
        background: `linear-gradient(${params.rotation}deg, ${params.color1}, ${params.color2}, ${params.color3})`,
        ...style,
        pointerEvents: "none",
      }}
    >
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        style={{ display: "block", width: "100%", height: "100%", visibility: "hidden", pointerEvents: "none" }}
      />
      {noise && noise.opacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwBAMAAAClLOS0AAAAElBMVEUAAAAAAAAAAAAAAAAAAAAAAADgKxmiAAAABnRSTlMCCgkGBAVJOAVJAAAASklEQVQ4y2NgGAWjYBSMglEwCgY/YGRgZBQUYmJiZGQEkYwMjIyMgoKCjIyMIJKBgRFIMjIyAklGRkYGRkFBYEcwMDIyMjAOUQAA1I4HwVwZAkYAAAAASUVORK5CYII=")`,
            backgroundSize: clamp(noise.scale ?? 1, 0.01, 10, 1) * 200,
            backgroundRepeat: "repeat",
            opacity: clamp(noise.opacity, 0, 1) / 2,
            pointerEvents: "none",
          }}
        />
      )}
    </div>
  );
}

export default AnimatedGradient;

type Rgba = [number, number, number, number];

function cssColor(value: string): string {
  const [r, g, b, a] = hexToRgba(value);
  return `rgba(${r * 255}, ${g * 255}, ${b * 255}, ${a})`;
}

/** Hex (including alpha), comma/space RGB(A), and HSL(A); invalid colors are black. */
function hexToRgba(value: string): Rgba {
  const color = typeof value === "string" ? value.trim().toLowerCase() : "";
  if (color === "transparent") return [0, 0, 0, 0];
  if (/^#(?:[\da-f]{3}|[\da-f]{4}|[\da-f]{6}|[\da-f]{8})$/.test(color)) {
    let hex = color.slice(1);
    if (hex.length <= 4) hex = [...hex].map((digit) => digit + digit).join("");
    return [
      parseInt(hex.slice(0, 2), 16) / 255,
      parseInt(hex.slice(2, 4), 16) / 255,
      parseInt(hex.slice(4, 6), 16) / 255,
      hex.length === 8 ? parseInt(hex.slice(6, 8), 16) / 255 : 1,
    ];
  }
  const match = /^(rgba?|hsla?)\((.*)\)$/.exec(color);
  if (!match) return [0, 0, 0, 1];
  const parts = match[2].trim().split(/[\s,/]+/);
  if (parts.length < 3 || parts.length > 4 || parts.some((part) => !Number.isFinite(parseFloat(part)))) {
    return [0, 0, 0, 1];
  }
  const alpha = parts[3] === undefined ? 1
    : clamp(parseFloat(parts[3]) / (parts[3].endsWith("%") ? 100 : 1), 0, 1, 1);
  if (match[1].startsWith("rgb")) {
    const channel = (part: string) => clamp(parseFloat(part) / (part.endsWith("%") ? 100 : 255), 0, 1);
    return [channel(parts[0]), channel(parts[1]), channel(parts[2]), alpha];
  }
  let hue = parseFloat(parts[0]);
  if (parts[0].endsWith("turn")) hue *= 360;
  else if (parts[0].endsWith("grad")) hue *= 0.9;
  else if (parts[0].endsWith("rad")) hue *= 180 / Math.PI;
  const h = ((hue % 360) + 360) % 360 / 360;
  const s = clamp(parseFloat(parts[1]) / 100, 0, 1);
  const l = clamp(parseFloat(parts[2]) / 100, 0, 1);
  return [...hslToRgb(h, s, l), alpha];
}

function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  if (s === 0) return [l, l, l];
  const hue2rgb = (p: number, q: number, hue: number) => {
    const t = (hue + 1) % 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  return [hue2rgb(p, q, h + 1 / 3), hue2rgb(p, q, h), hue2rgb(p, q, h - 1 / 3)];
}

const VERTEX_SHADER = `#version 300 es
in vec4 a_position;
void main() {
  gl_Position = a_position;
}`;

// Original supplied fragment shader: preserve the noise, swirl, shapes, and blending.
const FRAGMENT_SHADER = `#version 300 es
precision highp float;

uniform float u_time;
uniform float u_pixelRatio;
uniform vec2 u_resolution;

uniform float u_scale;
uniform float u_rotation;
uniform vec4 u_color1;
uniform vec4 u_color2;
uniform vec4 u_color3;
uniform float u_proportion;
uniform float u_softness;
uniform float u_shape;
uniform float u_shapeScale;
uniform float u_distortion;
uniform float u_swirl;
uniform float u_swirlIterations;

out vec4 fragColor;

#define TWO_PI 6.28318530718
#define PI 3.14159265358979323846

vec2 rotate(vec2 uv, float th) {
  return mat2(cos(th), sin(th), -sin(th), cos(th)) * uv;
}

float random(vec2 st) {
  return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float noise(vec2 st) {
  vec2 i = floor(st);
  vec2 f = fract(st);
  float a = random(i);
  float b = random(i + vec2(1.0, 0.0));
  float c = random(i + vec2(0.0, 1.0));
  float d = random(i + vec2(1.0, 1.0));

  vec2 u = f * f * (3.0 - 2.0 * f);

  float x1 = mix(a, b, u.x);
  float x2 = mix(c, d, u.x);
  return mix(x1, x2, u.y);
}

vec4 blend_colors(vec4 c1, vec4 c2, vec4 c3, float mixer, float edgesWidth, float edge_blur) {
    vec3 color1 = c1.rgb * c1.a;
    vec3 color2 = c2.rgb * c2.a;
    vec3 color3 = c3.rgb * c3.a;

    float r1 = smoothstep(.0 + .35 * edgesWidth, .7 - .35 * edgesWidth + .5 * edge_blur, mixer);
    float r2 = smoothstep(.3 + .35 * edgesWidth, 1. - .35 * edgesWidth + edge_blur, mixer);

    vec3 blended_color_2 = mix(color1, color2, r1);
    float blended_opacity_2 = mix(c1.a, c2.a, r1);

    vec3 c = mix(blended_color_2, color3, r2);
    float o = mix(blended_opacity_2, c3.a, r2);
    return vec4(c, o);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;

    float t = .5 * u_time;

    float noise_scale = .0005 + .006 * u_scale;

    uv -= .5;
    uv *= (noise_scale * u_resolution);
    uv = rotate(uv, u_rotation * .5 * PI);
    uv /= u_pixelRatio;
    uv += .5;

    float n1 = noise(uv * 1. + t);
    float n2 = noise(uv * 2. - t);
    float angle = n1 * TWO_PI;
    uv.x += 4. * u_distortion * n2 * cos(angle);
    uv.y += 4. * u_distortion * n2 * sin(angle);

    float iterations_number = ceil(clamp(u_swirlIterations, 1., 30.));
    for (float i = 1.; i <= iterations_number; i++) {
        uv.x += clamp(u_swirl, 0., 2.) / i * cos(t + i * 1.5 * uv.y);
        uv.y += clamp(u_swirl, 0., 2.) / i * cos(t + i * 1. * uv.x);
    }

    float proportion = clamp(u_proportion, 0., 1.);

    float shape = 0.;
    float mixer = 0.;
    if (u_shape < .5) {
      vec2 checks_shape_uv = uv * (.5 + 3.5 * u_shapeScale);
      shape = .5 + .5 * sin(checks_shape_uv.x) * cos(checks_shape_uv.y);
      mixer = shape + .48 * sign(proportion - .5) * pow(abs(proportion - .5), .5);
    } else if (u_shape < 1.5) {
      vec2 stripes_shape_uv = uv * (.25 + 3. * u_shapeScale);
      float f = fract(stripes_shape_uv.y);
      shape = smoothstep(.0, .55, f) * smoothstep(1., .45, f);
      mixer = shape + .48 * sign(proportion - .5) * pow(abs(proportion - .5), .5);
    } else {
      float sh = 1. - uv.y;
      sh -= .5;
      sh /= (noise_scale * u_resolution.y);
      sh += .5;
      float shape_scaling = .2 * (1. - u_shapeScale);
      shape = smoothstep(.45 - shape_scaling, .55 + shape_scaling, sh + .3 * (proportion - .5));
      mixer = shape;
    }

    vec4 color_mix = blend_colors(u_color1, u_color2, u_color3, mixer, 1. - clamp(u_softness, 0., 1.), .01 + .01 * u_scale);

    fragColor = vec4(color_mix.rgb, color_mix.a);
}
`;
