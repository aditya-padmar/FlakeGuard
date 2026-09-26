"use client"

import React from "react"
import { cn } from "@/lib/utils"

type TColorProp = string | string[]

export interface ShineBorderProps extends Omit<React.HTMLAttributes<HTMLElement>, "color"> {
  as?: React.ElementType
  borderRadius?: number
  borderWidth?: number
  duration?: number
  color?: TColorProp
  className?: string
  children: React.ReactNode
}

/**
 * @name Shine Border
 * @description It is an animated background border effect component with easy to use and configurable props.
 * @param as specifies the rendered element (div, article, section, etc.). Defaults to "div".
 * @param borderRadius defines the radius of the border.
 * @param borderWidth defines the width of the border.
 * @param duration defines the animation duration to be applied on the shining border in seconds.
 * @param color a string or string array to define border color.
 * @param className defines the class name to be applied to the component.
 * @param children contains react node elements.
 */
export function ShineBorder({
  as: Component = "div",
  borderRadius = 8,
  borderWidth = 1.5,
  duration = 8,
  color = ["#00F0FF", "#A07CFE", "#FF7849"],
  className,
  style,
  children,
  ...props
}: ShineBorderProps) {
  const colorString = color instanceof Array ? color.join(",") : color

  return (
    <Component
      style={
        {
          "--border-radius": `${borderRadius}px`,
          ...style,
        } as React.CSSProperties
      }
      className={cn("relative overflow-hidden", className)}
      {...props}
    >
      <div
        style={
          {
            "--border-width": `${borderWidth}px`,
            "--border-radius": `${borderRadius}px`,
            "--duration": `${duration}s`,
            "--mask-linear-gradient": `linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)`,
            "--background-radial-gradient": `radial-gradient(transparent,transparent, ${colorString},transparent,transparent)`,
            animationDuration: `${duration}s`,
          } as React.CSSProperties
        }
        className="fg-shine-overlay"
        aria-hidden="true"
      />
      {children}
    </Component>
  )
}

export default ShineBorder
