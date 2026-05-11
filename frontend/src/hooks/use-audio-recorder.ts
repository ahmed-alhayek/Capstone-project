import { useCallback, useRef, useState } from "react";
import { blobToWav } from "@/lib/audio-utils";

export type RecorderState = "idle" | "requesting" | "recording" | "processing";

export function useAudioRecorder() {
  const [state, setState] = useState<RecorderState>("idle");
  const [duration, setDuration] = useState(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTsRef = useRef(0);
  const tickRef = useRef<number | null>(null);

  const cleanup = () => {
    if (tickRef.current) {
      window.clearInterval(tickRef.current);
      tickRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    recorderRef.current = null;
    chunksRef.current = [];
    setDuration(0);
  };

  const start = useCallback(async () => {
    if (state !== "idle") return;
    setState("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.start();
      startTsRef.current = Date.now();
      tickRef.current = window.setInterval(() => {
        setDuration(Math.floor((Date.now() - startTsRef.current) / 1000));
      }, 250);

      setState("recording");
    } catch (err) {
      cleanup();
      setState("idle");
      throw err;
    }
  }, [state]);

  /** Stops recording and returns a 16kHz mono WAV blob ready to upload. */
  const stop = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = recorderRef.current;
      if (!recorder || state !== "recording") {
        reject(new Error("Not recording"));
        return;
      }
      setState("processing");

      recorder.onstop = async () => {
        try {
          const raw = new Blob(chunksRef.current, {
            type: recorder.mimeType || "audio/webm",
          });
          const wav = await blobToWav(raw, 16000);
          cleanup();
          setState("idle");
          resolve(wav);
        } catch (err) {
          cleanup();
          setState("idle");
          reject(err);
        }
      };

      recorder.stop();
    });
  }, [state]);

  const cancel = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.onstop = null;
      try {
        recorder.stop();
      } catch {
        /* ignore */
      }
    }
    cleanup();
    setState("idle");
  }, []);

  return { state, duration, start, stop, cancel };
}
