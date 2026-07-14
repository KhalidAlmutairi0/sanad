import { redirect } from "next/navigation";
import { serverGet, ApiRequestError } from "@/lib/server-api";
import { AppLayout } from "@/components/design/Shared";
import { ReviewWorkspace } from "@/components/review/ReviewWorkspace";
import type { Clause, ContractDetail, Finding } from "@/types";

interface RadarResp {
  verdict: "GO" | "REVIEW" | "STOP";
}

export default async function ContractReviewPage({ params }: { params: { id: string } }) {
  const { id } = params;

  try {
    const [contract, clausesRes, findingsRes, radar] = await Promise.all([
      serverGet<ContractDetail>(`/contracts/${id}`),
      serverGet<{ items: Clause[] }>(`/contracts/${id}/clauses`),
      serverGet<{ items: Finding[] }>(`/contracts/${id}/findings`),
      serverGet<RadarResp>(`/contracts/${id}/radar`),
    ]);

    return (
      <AppLayout>
        <ReviewWorkspace
          contract={contract}
          clauses={clausesRes.items}
          findings={findingsRes.items}
          verdict={radar.verdict}
        />
      </AppLayout>
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 401) redirect("/login");
    throw e;
  }
}
