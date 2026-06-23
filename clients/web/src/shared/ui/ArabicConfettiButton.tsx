import { useState, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Button } from "react-aria-components";

const confetti = [
  ["ب", -112, -64, -18, "primary"],
  ["ل", -78, -104, 14, "warning"],
  ["ي", -32, -86, -22, "danger"],
  ["غ", 24, -112, 18, "primary"],
  ["ض", 79, -86, -12, "danger"],
  ["ع", 116, -54, 20, "warning"],
  ["ف", -126, -4, 12, "danger"],
  ["ق", 131, 4, -18, "primary"],
  ["ش", -102, 58, -20, "warning"],
  ["س", -48, 86, 14, "danger"],
  ["ت", 14, 98, -14, "warning"],
  ["ك", 75, 78, 22, "primary"],
  ["م", 118, 48, -12, "danger"],
] as const;

type ArabicConfettiButtonProps = {
  children: ReactNode;
  className?: string;
  onPress?: () => void;
};

export function ArabicConfettiButton({
  children,
  className,
  onPress,
}: ArabicConfettiButtonProps) {
  const [burst, setBurst] = useState(0);
  const reduceMotion = useReducedMotion();

  const trigger = () => {
    setBurst((value) => value + 1);
    onPress?.();
  };

  return (
    <span className="confetti-button-wrap">
      {!reduceMotion && burst > 0 && (
        <span key={burst} className="arabic-confetti" aria-hidden="true">
          {confetti.map(([letter, x, y, rotate, tone], index) => (
            <motion.span
              key={`${letter}-${index}`}
              className={`arabic-confetti__letter arabic-confetti__letter--${tone}`}
              initial={{ opacity: 0, x: 0, y: 0, rotate: 0, scale: 0.45 }}
              animate={{
                opacity: [0, 1, 1, 0],
                x,
                y,
                rotate,
                scale: [0.45, 1.15, 0.9],
              }}
              transition={{
                duration: 0.9,
                delay: index * 0.015,
                ease: [0.16, 1, 0.3, 1],
              }}
            >
              {letter}
            </motion.span>
          ))}
        </span>
      )}
      <Button
        className={["confetti-button", className].filter(Boolean).join(" ")}
        onHoverStart={() => setBurst((value) => value + 1)}
        onPress={trigger}
      >
        {children}
      </Button>
    </span>
  );
}
