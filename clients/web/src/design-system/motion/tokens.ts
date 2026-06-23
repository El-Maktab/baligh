export const motionTokens = {
  duration: {
    instant: 0.12,
    quick: 0.2,
    standard: 0.36,
    expressive: 0.72,
  },
  easing: {
    standard: [0.22, 1, 0.36, 1] as const,
    emphasized: [0.16, 1, 0.3, 1] as const,
  },
} as const;

export const motionPresets = {
  enter: {
    initial: { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: {
      duration: motionTokens.duration.standard,
      ease: motionTokens.easing.standard,
    },
  },
  softScale: {
    initial: { opacity: 0, scale: 0.96 },
    animate: { opacity: 1, scale: 1 },
    transition: {
      duration: motionTokens.duration.expressive,
      ease: motionTokens.easing.emphasized,
    },
  },
} as const;
