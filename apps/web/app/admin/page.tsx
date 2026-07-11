import { AdminView } from "@/components/admin/AdminView";
import { isDemo } from "@/lib/demo";

export default function AdminPage() {
  return <AdminView demo={isDemo()} />;
}
