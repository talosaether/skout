import { useEffect, useRef, useState } from "react";
import { uploadBlob } from "../lib/api";

interface CameraCaptureProps {
  onUploadSuccess?: () => void;
}

export default function CameraCapture({ onUploadSuccess }: CameraCaptureProps) {
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
      } catch (e: unknown) {
        if (mounted) {
          const error = e as Error;
          setError(error?.message ?? "Camera access failed (HTTPS required)");
        }
      }
    };

    initCamera();

    return () => {
      mounted = false;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      const video = videoRef.current;
      if (video) {
        video.srcObject = null;
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
      onUploadSuccess?.();
    } catch (e: unknown) {
      const error = e as Error;
      setError(error?.message ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-3xl p-6 space-y-6 shadow-2xl">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-sky-100 rounded-full flex items-center justify-center">
          <svg className="w-5 h-5 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Camera</h3>
          <p className="text-sm text-slate-400">Capture and upload photos instantly</p>
        </div>
      </div>

      <div className="relative rounded-2xl overflow-hidden shadow-xl bg-black">
        {!ready && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-700 z-10">
            <div className="text-center space-y-3">
              <div className="w-12 h-12 mx-auto border-4 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-slate-300">Initializing camera...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-700 z-10">
            <div className="text-center space-y-3 p-6">
              <div className="w-16 h-16 mx-auto bg-rose-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.982 16c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <p className="text-slate-300 font-medium">Camera Error</p>
                <p className="text-sm text-slate-400 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        <video
          ref={videoRef}
          className="w-full h-auto min-h-[200px] md:min-h-[300px]"
          playsInline
          muted
        />

        {ready && (
          <div style={{
            position: 'absolute',
            bottom: '16px',
            left: '50%',
            transform: 'translateX(-50%)'
          }}>
            <button
              onClick={capture}
              disabled={busy}
              style={{
                width: '64px',
                height: '64px',
                backgroundColor: 'white',
                borderRadius: '50%',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: 'none',
                cursor: busy ? 'not-allowed' : 'pointer',
                transition: 'transform 0.2s',
                opacity: busy ? 0.5 : 1
              }}
              onMouseOver={(e) => !busy && (e.target.style.transform = 'scale(1.1)')}
              onMouseOut={(e) => !busy && (e.target.style.transform = 'scale(1)')}
            >
              {busy ? (
                <div style={{
                  width: '24px',
                  height: '24px',
                  border: '2px solid #475569',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
              ) : (
                <div style={{
                  width: '48px',
                  height: '48px',
                  backgroundColor: '#0ea5e9',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <svg style={{ width: '24px', height: '24px', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
              )}
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${ready ? 'bg-green-500' : error ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
          <span className="text-sm text-slate-400">
            {ready ? 'Ready to capture' : error ? 'Camera unavailable' : 'Connecting...'}
          </span>
        </div>

        {busy && (
          <div className="flex items-center gap-2 text-sky-400">
            <div className="w-3 h-3 border border-sky-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm">Uploading...</span>
          </div>
        )}
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}