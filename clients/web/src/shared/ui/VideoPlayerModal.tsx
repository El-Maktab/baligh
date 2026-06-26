import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

type VideoPlayerModalProps = {
  open: boolean;
  onClose: () => void;
};

export function VideoPlayerModal({ open, onClose }: VideoPlayerModalProps) {
  const reduceMotion = useReducedMotion();
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <motion.div
      className="video-modal-backdrop"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="مقطع تعريفي ببليغ"
    >
      <motion.div
        className="video-modal-container"
        initial={reduceMotion ? false : { opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="video-modal-close"
          type="button"
          onClick={onClose}
          aria-label="إغلاق"
        >
          <X aria-hidden="true" size={24} />
        </button>
        <video
          ref={videoRef}
          className="video-modal-player"
          src="/baligh-demo-compressed.mp4"
          controls
          autoPlay
          playsInline
        />
      </motion.div>
    </motion.div>
  );
}
