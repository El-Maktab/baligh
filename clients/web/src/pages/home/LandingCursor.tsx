import { useEffect, useState } from "react";
import { motion, useMotionValue, useSpring } from "motion/react";

export function LandingCursor() {
  const [visible, setVisible] = useState(false);
  const [active, setActive] = useState(false);
  const pointerX = useMotionValue(-40);
  const pointerY = useMotionValue(-40);
  const x = useSpring(pointerX, { stiffness: 520, damping: 34, mass: 0.35 });
  const y = useSpring(pointerY, { stiffness: 520, damping: 34, mass: 0.35 });

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      pointerX.set(event.clientX - 15);
      pointerY.set(event.clientY - 15);
      setVisible(true);
      setActive(
        event.target instanceof Element &&
          Boolean(event.target.closest("a, button, [data-cursor-active]")),
      );
    };
    const handlePointerLeave = () => setVisible(false);

    window.addEventListener("pointermove", handlePointerMove);
    document.documentElement.addEventListener("mouseleave", handlePointerLeave);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      document.documentElement.removeEventListener(
        "mouseleave",
        handlePointerLeave,
      );
    };
  }, [pointerX, pointerY]);

  return (
    <motion.div
      aria-hidden="true"
      className="landing-cursor"
      data-active={active || undefined}
      data-visible={visible || undefined}
      style={{ x, y }}
    >
      <span>ب</span>
    </motion.div>
  );
}
