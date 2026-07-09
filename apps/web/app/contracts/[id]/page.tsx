import { redirect } from "next/navigation";
import { serverGet, ApiRequestError } from "@/lib/server-api";
import { Header } from "@/components/ui/Header";
import { ReviewWorkspace } from "@/components/review/ReviewWorkspace";
import { isDemo, demoContractDetail, demoClauses, demoFindings, demoRadarVerdict } from "@/lib/demo";
import type { Clause, ContractDetail, Finding } from "@/types";

interface RadarResp {
  verdict: "GO" | "REVIEW" | "STOP";
}

export default async function ContractReviewPage({ params }: { params: { id: string } }) {
  const { id } = params;

  if (isDemo()) {
    return (
      <div className="min-h-screen">
        <Header />
        <main className="mx-auto max-w-6xl px-6 py-12">
          <ReviewWorkspace
            contract={demoContractDetail(id)}
            clauses={demoClauses(id)}
            findings={demoFindings(id)}
            verdict={demoRadarVerdict(id)}
            demo
          />
        </main>
      </div>
    );
  }

  try {
    const [contract, clausesRes, findingsRes, radar] = await Promise.all([
      serverGet<ContractDetail>(`/contracts/${id}`),
      serverGet<{ items: Clause[] }>(`/contracts/${id}/clauses`),
      serverGet<{ items: Finding[] }>(`/contracts/${id}/findings`),
      serverGet<RadarResp>(`/contracts/${id}/radar`),
    ]);

    return (
      <div className="min-h-screen">
        <Header />
        <main className="mx-auto max-w-6xl px-6 py-12">
          <ReviewWorkspace
            contract={contract}
            clauses={clausesRes.items}
            findings={findingsRes.items}
            verdict={radar.verdict}
          />
        </main>
      </div>
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 401) redirect("/login");
    throw e;
  }
}
