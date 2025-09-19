export default function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">CRUD + Camera (PWA)</h1>
          <button className="px-3 py-2 bg-slate-700 rounded-xl">Hello World</button>
        </header>

        <div className="bg-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Application Ready</h2>
          <p className="text-slate-300">
            Frontend is running with React + Vite + Tailwind CSS
          </p>
        </div>
      </div>
    </div>
  );
}
