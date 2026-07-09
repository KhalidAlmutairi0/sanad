import Link from "next/link";
import { redirect } from "next/navigation";
import { serverGet, ApiRequestError } from "@/lib/server-api";
import { Header } from "@/components/ui/Header";
import { UploadContract } from "@/components/contracts/UploadContract";
import { StatusPill } from "@/components/contracts/StatusPill";
import { ContractsHeading, EmptyState } from "./ui";
import { isDemo, DEMO_CONTRACTS } from "@/lib/demo";
import type { ContractListItem } from "@/types";

interface ContractList {
  items: ContractListItem[];
  total: number;
}

export default async function ContractsPage() {
  const demo = isDemo();
  let data: ContractList;
  if (demo) {
    data = { items: DEMO_CONTRACTS, total: DEMO_CONTRACTS.length };
  } else {
    try {
      data = await serverGet<ContractList>("/contracts");
    } catch (e) {
      if (e instanceof ApiRequestError && e.status === 401) redirect("/login");
      throw e;
    }
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-12">
        <ContractsHeading />
        {!demo && (
          <div className="mt-8">
            <UploadContract />
          </div>
        )}

        {data.items.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="mt-8 divide-y divide-line rounded-card border border-line bg-surface">
            {data.items.map((c) => (
              <li key={c.id}>
                <Link href={`/contracts/${c.id}`} className="flex items-center justify-between gap-4 px-6 py-4 hover:bg-paper">
                  <span className="text-body text-ink">{c.title}</span>
                  <span className="flex items-center gap-6">
                    <StatusPill status={c.status} />
                    <span className="tabular text-label text-muted" style={{ fontFamily: "var(--font-plex-mono)" }}>
                      {c.readiness_score ?? "—"}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
