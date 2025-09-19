import { useEffect, useRef, useState } from "react";
import { uploadBlob } from "../lib/api";

export default function CameraCapture() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream;
    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setReady(true);
        }
      } catch (e: any) {
        setError(e?.message ?? "Camera access failed (https required?)");
      }
    })();
    return () => { stream?.getTracks().forEach(t => t.stop()); };
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