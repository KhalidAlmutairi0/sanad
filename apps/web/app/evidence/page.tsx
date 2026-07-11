import { EvidenceView } from "@/components/evidence/EvidenceView";
import { isDemo } from "@/lib/demo";

export default function EvidencePage() {
  return <EvidenceView demo={isDemo()} />;
}
