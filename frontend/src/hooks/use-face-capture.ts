import * as React from "react";

export type FaceCaptureState = "idle" | "requesting" | "active" | "stopped";

export interface UseFaceCapture {
  state: FaceCaptureState;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  start: () => Promise<void>;
  stop: () => void;
  capture: () => Promise<Blob>;
}

export function useFaceCapture(): UseFaceCapture {
  const [state, setState] = React.useState<FaceCaptureState>("idle");
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const streamRef = React.useRef<MediaStream | null>(null);

  const start = React.useCallback(async () => {
    setState("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setState("active");
    } catch (err) {
      setState("idle");
      throw err;
    }
  }, []);

  const stop = React.useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setState("stopped");
  }, []);

  const capture = React.useCallback(async (): Promise<Blob> => {
    const video = videoRef.current;
    if (!video) throw new Error("No video element");

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Could not get canvas context");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (blob) => (blob ? resolve(blob) : reject(new Error("Canvas toBlob failed"))),
        "image/jpeg",
        0.9,
      );
    });
  }, []);

  React.useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return { state, videoRef, start, stop, capture };
}
