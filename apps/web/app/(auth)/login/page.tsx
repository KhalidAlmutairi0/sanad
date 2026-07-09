import { LoginForm } from "@/components/auth/LoginForm";
import { isDemo } from "@/lib/demo";

export default function LoginPage() {
  return <LoginForm demo={isDemo()} />;
}
