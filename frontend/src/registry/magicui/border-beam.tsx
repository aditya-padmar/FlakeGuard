"use client"

import React from "react"
import { motion, type MotionStyle, type Transition } from "framer-motion"
import { cn } from "@/lib/utils"

export interface BorderBeamProps {
  /**
   * The size of the border beam in pixels (controls beam arc width).
   */
  size?: number
  /**
   * The duration of the border beam in seconds.
   */
  duration?: number
  /**
   * The delay of the border beam in seconds.
   */
  delay?: number
  /**
   * The color of the border beam from.
   */
  colorFrom?: string
  /**
   * The color of the border beam to.
   */
  colorTo?: string
  /**
   * The motion transition of the border beam.
   */
  transition?: Transition
  /**
   * The class name of the border beam.
   */
  className?: string
  /**
   * The style of the border beam.
   */
  style?: React.CSSProperties
  /**
   * Whether to reverse the animation direction.
   */
  reverse?: boolean
  /**
   * The initial offset position (0-100).
   */
  initialOffset?: number
  /**
   * The border width of the beam in pixels.
   */
  borderWidth?: number
  /**
   * Anchor point for the beam (0-100).
   */
  anchor?: number
  /**
   * Border radius of the container in pixels.
   */
  borderRadius?: number
}

export const BorderBeam = ({
  className,
  size = 100,
  delay = 0,
  duration = 8,
  colorFrom = "#ffaa40",
  colorTo = "#9c40ff",
  transition,
  style,
  reverse = false,
  initialOffset = 0,
  borderWidth = 1.5,
}: BorderBeamProps) => {
  // Spread arc angle in degrees (ensures strictly a single beam segment)
  const spread = Math.min(80, Math.max(30, (size / 100) * 55))

  return (
    <div
      className="pointer-events-none absolute inset-0 rounded-[inherit] overflow-hidden"
      style={
        {
          padding: `${borderWidth}px`,
          WebkitMask:
            "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          WebkitMaskComposite: "xor",
          mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          maskComposite: "exclude",
        } as React.CSSProperties
      }
    >
      <motion.div
        className={cn(
          "absolute aspect-square pointer-events-none",
          className
        )}
        style={
          {
            inset: "-250%",
            margin: "auto",
            width: "600%",
            height: "600%",
            background: `conic-gradient(from 0deg at 50% 50%, transparent 0deg, transparent ${360 - spread}deg, ${colorFrom} ${360 - spread * 0.6}deg, ${colorTo} ${360 - spread * 0.12}deg, transparent 360deg)`,
            filter: "drop-shadow(0 0 6px rgba(156, 64, 255, 0.4))",
            ...style,
          } as MotionStyle
        }
        initial={{ rotate: initialOffset * 3.6 }}
        animate={{
          rotate: reverse
            ? [initialOffset * 3.6 - 360, initialOffset * 3.6]
            : [initialOffset * 3.6, initialOffset * 3.6 + 360],
        }}
        transition={{
          repeat: Infinity,
          ease: "linear",
          duration,
          delay: -delay,
          ...transition,
        }}
      />
    </div>
  )
}

export default BorderBeam
