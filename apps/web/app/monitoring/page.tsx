import { MonitoringView } from "@/components/monitoring/MonitoringView";
import { isDemo } from "@/lib/demo";

export default function MonitoringPage() {
  return <MonitoringView demo={isDemo()} />;
}
