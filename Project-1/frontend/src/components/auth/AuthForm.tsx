import type { FormEventHandler } from "react";
import { Link } from "react-router-dom";

export interface FieldErrors {
  email?: string;
  password?: string;
  form?: string;
}

interface AuthFormProps {
  title: string;
  subtitle: string;
  submitLabel: string;
  submittingLabel: string;
  email: string;
  password: string;
  errors: FieldErrors;
  submitting: boolean;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
  footerPrompt: string;
  footerLinkLabel: string;
  footerLinkTo: string;
  successMessage?: string | null;
}

export function AuthForm({
  title,
  subtitle,
  submitLabel,
  submittingLabel,
  email,
  password,
  errors,
  submitting,
  onEmailChange,
  onPasswordChange,
  onSubmit,
  footerPrompt,
  footerLinkLabel,
  footerLinkTo,
  successMessage,
}: AuthFormProps) {
  const isLogin = footerLinkTo === "/register";

  return (
    <form
      onSubmit={onSubmit}
      className="auth-card auth-fade-in w-full max-w-md space-y-6 rounded-2xl border border-slate-200/80 bg-white p-8 shadow-xl shadow-slate-900/10 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/30"
      noValidate
    >
      <div className="space-y-5 text-center">
        <div className="mx-auto inline-flex items-center justify-center rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-blue-700 dark:border-blue-900/60 dark:bg-blue-950/60 dark:text-blue-300">
          Amzur AI Chat
        </div>
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
            {title}
          </h1>
          <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
            {subtitle}
          </p>
        </div>
      </div>

      {successMessage ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/50 dark:text-emerald-300">
          {successMessage}
        </div>
      ) : null}

      <div className="space-y-4">
        <div>
          <label
            htmlFor="auth-email"
            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Work email
          </label>
          <input
            id="auth-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            aria-invalid={errors.email ? "true" : "false"}
            aria-describedby={errors.email ? "auth-email-error" : "auth-email-hint"}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-50"
            placeholder="name@amzur.com"
          />
          {errors.email ? (
            <p
              id="auth-email-error"
              className="mt-2 text-sm text-red-500"
            >
              {errors.email}
            </p>
          ) : (
            <p
              id="auth-email-hint"
              className="mt-2 text-sm text-slate-500 dark:text-slate-400"
            >
              Only @amzur.com domain can access this application.
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="auth-password"
            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300"
          >
            Password
          </label>
          <input
            id="auth-password"
            type="password"
            required
            minLength={isLogin ? 1 : 8}
            autoComplete={isLogin ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            aria-invalid={errors.password || errors.form ? "true" : "false"}
            aria-describedby={
              errors.password || errors.form
                ? "auth-password-error"
                : "auth-password-hint"
            }
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-50"
            placeholder={isLogin ? "Enter your password" : "Create a secure password"}
          />
          {errors.password || errors.form ? (
            <p
              id="auth-password-error"
              className="mt-2 text-sm text-red-500"
            >
              {errors.password ?? errors.form}
            </p>
          ) : (
            <p
              id="auth-password-hint"
              className="mt-2 text-sm text-slate-500 dark:text-slate-400"
            >
              {isLogin
                ? "Use the password linked to your company account."
                : "Use at least 8 characters for your password."}
            </p>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70 dark:focus:ring-offset-slate-900"
        >
          {submitting && <span className="auth-spinner" aria-hidden="true" />}
          <span>{submitting ? submittingLabel : submitLabel}</span>
        </button>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          {footerPrompt}{" "}
          <Link
            to={footerLinkTo}
            className="font-medium text-blue-600 transition-colors duration-200 hover:text-blue-700 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
          >
            {footerLinkLabel}
          </Link>
        </p>
      </div>
    </form>
  );
}
