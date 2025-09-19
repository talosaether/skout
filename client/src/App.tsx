import { useEffect, useState } from "react";
import CameraCapture from "./components/CameraCapture";
import { listAssets, deleteAsset } from "./lib/api";
import type { Asset } from "./lib/api";

export default function App() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);

  async function refresh() {
    try {
      const res = await listAssets(50, 0);
      setAssets(res.items);
      setTotal(res.total);
    } catch (error) {
      console.error("Failed to load assets:", error);
    }
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">CRUD + Camera (PWA)</h1>
          <button onClick={refresh} className="px-3 py-2 bg-slate-700 rounded-xl">Refresh</button>
        </header>

        <CameraCapture onUploadSuccess={refresh} />

        <section>
          <h2 className="text-xl font-semibold mt-6 mb-2">Assets ({total})</h2>
          <ul className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {assets.map(a => (
              <li key={a.id} className="bg-slate-800 rounded-xl p-2 space-y-2">
                <img src={`/api/assets/${a.id}`} alt={a.filename} className="w-full h-32 object-cover rounded-lg" />
                <div className="text-xs break-all">{a.filename}</div>
                <button
                  onClick={async () => { await deleteAsset(a.id); await refresh(); }}
                  className="w-full px-2 py-1 bg-rose-600 rounded-lg"
                >Delete</button>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
