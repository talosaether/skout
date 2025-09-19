export type Asset = {
  id: string;
  created_at: string;
  filename: string;
  mime: string;
  size: number;
};

export async function listAssets(limit = 20, offset = 0) {
  const res = await fetch(`/api/assets?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to list assets");
  return (await res.json()) as { items: Asset[]; total: number };
}

export async function uploadBlob(file: Blob, filename: string) {
  const fd = new FormData();
  fd.append("file", file, filename);
  const res = await fetch("/api/assets", { method: "POST", body: fd });
  if (!res.ok) throw new Error("Upload failed");
  return await res.json();
}

export async function deleteAsset(id: string) {
  const res = await fetch(`/api/assets/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Delete failed");
}