/**
 * AuthCallback — landing page after Google OAuth redirect.
 *
 * The backend already set the JWT httpOnly cookie before redirecting here.
 * This page just hydrates the auth store (one GET /me call) then
 * sends the user to /chat.  If hydration fails, it drops them back to /login.
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "../lib/authStore";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { hydrate } = useAuthStore();

  useEffect(() => {
    (async () => {
      try {
        await hydrate();
        navigate("/chat", { replace: true });
      } catch {
        navigate("/login", {
          replace: true,
          state: { message: "Google sign-in failed. Please try again." },
        });
      }
    })();
  }, [hydrate, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
      <div className="flex flex-col items-center gap-4 text-slate-500 dark:text-slate-400">
        <span className="auth-spinner !h-6 !w-6" aria-hidden="true" />
        <p className="text-sm">Signing you in with Google…</p>
      </div>
    </div>
  );
}
