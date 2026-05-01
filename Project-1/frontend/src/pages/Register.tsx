import { useEffect, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { AuthForm, type FieldErrors } from "../components/auth/AuthForm";
import { useAuthStore } from "../lib/authStore";
import { mapAuthErrors } from "../lib/authErrors";

export default function Register() {
  const navigate = useNavigate();
  const location = useLocation();
  const register = useAuthStore((state) => state.register);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setEmail("");
    setPassword("");
    setErrors({});
    setSubmitting(false);
  }, [location.pathname]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);

    try {
      await register(email.trim(), password);
      navigate("/login", {
        replace: true,
        state: { message: "Account created successfully. Please login." },
      });
    } catch (err) {
      setErrors(mapAuthErrors(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-shell flex min-h-screen items-center justify-center px-4 py-10 dark:bg-slate-950 sm:px-6 lg:px-8">
      <div className="relative z-10 w-full max-w-md">
        <AuthForm
          title="Create your account"
          subtitle="Register with your Amzur domain to access internal AI tools."
          submitLabel="Create account"
          submittingLabel="Creating your account..."
          email={email}
          password={password}
          errors={errors}
          submitting={submitting}
          onEmailChange={setEmail}
          onPasswordChange={setPassword}
          onSubmit={handleSubmit}
          footerPrompt="Already have an account?"
          footerLinkLabel="Login"
          footerLinkTo="/login"
        />
      </div>
    </main>
  );
}