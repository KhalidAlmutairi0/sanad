import { ApplicabilityView } from "@/components/applicability/ApplicabilityView";

export default function ApplicabilityPage({ params }: { params: { id: string } }) {
  return <ApplicabilityView contractId={params.id} />;
}
