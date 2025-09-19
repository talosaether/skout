import { useEffect, useRef, useState } from "react";
import { uploadBlob } from "../lib/api";

export default function CameraCapture() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let mounted = true;

    const initCamera = async () => {
      try {
        // Check if mediaDevices is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error("Camera API not available. HTTPS is required for camera access.");
        }

        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false
        });

        if (mounted && videoRef.current && stream) {
          videoRef.current.srcObject = stream;
          try {
            await videoRef.current.play();
            if (mounted) setReady(true);
          } catch (playError) {
            console.warn("Video play interrupted:", playError);
          }
        }
      } catch (e: any) {
        if (mounted) {
          setError(e?.message ?? "Camera access failed (HTTPS required)");
        }
      }
    };

    initCamera();

    return () => {
      mounted = false;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setReady(false);
    };
  }, []);

  const capture = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    setBusy(true);
    setError(null);

    const v = videoRef.current;
    const c = canvasRef.current;
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    ctx?.drawImage(v, 0, 0);

    const blob = await new Promise<Blob | null>(res => c.toBlob(b => res(b), "image/jpeg", 0.9));
    if (!blob) {
      setError("Failed to capture image");
      setBusy(false);
      return;
    }

    try {
      await uploadBlob(blob, `capture_${Date.now()}.jpg`);
    } catch (e: any) {
      setError(e?.message ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="rounded-2xl overflow-hidden shadow">
        <video ref={videoRef} className="w-full h-auto" playsInline muted />
      </div>
      <div className="flex gap-2">
        <button
          onClick={capture}
          disabled={!ready || busy}
          className="px-4 py-2 rounded-xl bg-sky-600 text-white disabled:opacity-50"
        >
          {busy ? "Uploading..." : "Capture & Upload"}
        </button>
        {error && <p className="text-red-600">{error}</p>}
      </div>
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}