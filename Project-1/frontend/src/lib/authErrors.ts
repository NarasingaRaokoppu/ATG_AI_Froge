import { APIError } from "./api";

import type { FieldErrors } from "../components/auth/AuthForm";

interface APIErrorDetail {
  error?: string;
  message?: string;
}

export function mapAuthErrors(err: unknown): FieldErrors {
  if (err instanceof APIError) {
    if (typeof err.detail === "object" && err.detail) {
      const detail = err.detail as APIErrorDetail;
      const message = detail.message ?? JSON.stringify(detail);

      if (
        detail.error === "forbidden_domain" ||
        detail.error === "email_taken" ||
        detail.error === "user_not_registered"
      ) {
        return { email: message };
      }

      if (detail.error === "invalid_credentials") {
        return { password: message };
      }

      return { form: message };
    }

    return { form: String(err.detail) };
  }

  if (err instanceof Error) {
    return { form: err.message };
  }

  return { form: "Something went wrong" };
}