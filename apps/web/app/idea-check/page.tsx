import { IdeaCheckClient } from "@/components/idea/IdeaCheckClient";
import { isDemo } from "@/lib/demo";

export default function IdeaCheckPage() {
  return <IdeaCheckClient demo={isDemo()} />;
}
