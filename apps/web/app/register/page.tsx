import { RegisterView } from "@/components/register/RegisterView";
import { isDemo } from "@/lib/demo";

export default function RegisterPage() {
  return <RegisterView demo={isDemo()} />;
}
