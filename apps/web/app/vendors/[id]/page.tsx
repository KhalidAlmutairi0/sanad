import { VendorResultsView } from "@/components/vendor/VendorResultsView";

export default function VendorResultsPage({ params }: { params: { id: string } }) {
  return <VendorResultsView evaluationId={params.id} />;
}
