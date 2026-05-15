import { useMemo, useState } from "react";

import type {
  DatabaseConnection,
  DatabaseConnectionCreateInput,
  DatabaseConnectionUpdateInput,
} from "../../types";

interface Props {
  open: boolean;
  editing?: DatabaseConnection | null;
  onClose: () => void;
  onSubmit: (
    payload: DatabaseConnectionCreateInput | DatabaseConnectionUpdateInput
  ) => Promise<void>;
}

export function DatabaseConnectionModal({
  open,
  editing,
  onClose,
  onSubmit,
}: Props) {
  const initial = useMemo(
    () => ({
      name: editing?.name ?? "",
      host: editing?.host ?? "",
      port: editing?.port ?? 5432,
      database: editing?.database ?? "",
      username: editing?.username ?? "",
      password: "",
    }),
    [editing]
  );

  const [form, setForm] = useState(initial);
  const [busy, setBusy] = useState(false);

  if (!open) return null;

  const updateField = (key: keyof typeof form, value: string | number) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (editing) {
        await onSubmit({
          name: form.name,
          host: form.host,
          port: Number(form.port),
          database: form.database,
          username: form.username,
          ...(form.password ? { password: form.password } : {}),
        });
      } else {
        await onSubmit({
          name: form.name,
          host: form.host,
          port: Number(form.port),
          database: form.database,
          username: form.username,
          password: form.password,
        });
      }
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-xl space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl"
      >
        <h2 className="text-xl font-semibold text-slate-900">
          {editing ? "Edit connection" : "New connection"}
        </h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <input
            className="rounded-lg border border-slate-300 p-2"
            placeholder="Connection name"
            value={form.name}
            onChange={(e) => updateField("name", e.target.value)}
            required
          />
          <input
            className="rounded-lg border border-slate-300 p-2"
            placeholder="Host"
            value={form.host}
            onChange={(e) => updateField("host", e.target.value)}
            required
          />
          <input
            className="rounded-lg border border-slate-300 p-2"
            placeholder="Port"
            type="number"
            value={form.port}
            onChange={(e) => updateField("port", Number(e.target.value))}
            required
          />
          <input
            className="rounded-lg border border-slate-300 p-2"
            placeholder="Database"
            value={form.database}
            onChange={(e) => updateField("database", e.target.value)}
            required
          />
          <input
            className="rounded-lg border border-slate-300 p-2"
            placeholder="Username"
            value={form.username}
            onChange={(e) => updateField("username", e.target.value)}
            required
          />
          <input
            className="rounded-lg border border-slate-300 p-2"
            placeholder={editing ? "Password (optional to keep current)" : "Password"}
            type="password"
            value={form.password}
            onChange={(e) => updateField("password", e.target.value)}
            required={!editing}
          />
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700"
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="rounded-lg bg-slate-900 px-4 py-2 text-white disabled:opacity-50"
            disabled={busy}
          >
            {busy ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
