"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/i18n";
import { apiPost } from "@/lib/api";

interface CreateResp {
  id: string;
  upload_url: string;
}

export function UploadContract() {
  const { dict } = useApp();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !title) return;
    setBusy(true);
    setError(null);
    try {
      const created = await apiPost<CreateResp>("/contracts", { title });
      // Presigned PUT goes directly to MinIO (not through the BFF).
      const put = await fetch(created.upload_url, { method: "PUT", body: file });
      if (!put.ok) throw new Error("upload_failed");
      await apiPost(`/contracts/${created.id}/uploaded`);
      setTitle("");
      setFile(null);
      router.refresh();
    } catch (e) {
      setError((e as Error & { code?: string }).code ?? "upload_failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="rounded-card border border-line bg-surface p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <label className="flex-1">
          <span className="text-label text-muted">{dict.contracts.newTitle}</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-chip border border-line bg-paper px-4 py-2 text-body text-ink"
            required
          />
        </label>
        <label className="flex-1">
          <span className="text-label text-muted">{dict.contracts.chooseFile}</span>
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 w-full text-label text-ink file:me-3 file:rounded-chip file:border-0 file:bg-orange-bg file:px-4 file:py-2 file:text-orange-ink"
            required
          />
        </label>
        <button
          type="submit"
          disabled={busy || !file || !title}
          className="rounded-chip bg-orange px-6 py-2 text-label text-white disabled:opacity-50"
        >
          {busy ? dict.contracts.uploading : dict.contracts.upload}
        </button>
      </div>
      {error && <p className="mt-3 text-label text-severity-critical">{error}</p>}
    </form>
  );
}
