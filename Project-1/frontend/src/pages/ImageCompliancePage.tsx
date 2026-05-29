import { useMemo, useState } from "react";

import { imageComplianceApi, uploadApi } from "../lib/endpoints";
import type {
  ComplianceRule,
  ImageComplianceImageInput,
  ImageComplianceResponse,
} from "../types";

const SAMPLE_RULES: ComplianceRule[] = [
  {
    id: "safety_helmet",
    description: "Worker must wear a helmet",
    logic: "and",
    conditions: [
      {
        field: "ppe.helmet",
        operator: "eq",
        value: true,
      },
    ],
  },
  {
    id: "badge_present",
    description: "ID badge must be visible",
    logic: "and",
    conditions: [
      {
        field: "person.id_badge",
        operator: "eq",
        value: true,
      },
    ],
  },
];

function parseRules(input: string): ComplianceRule[] {
  const parsed = JSON.parse(input);
  if (!Array.isArray(parsed)) {
    throw new Error("Rules JSON must be an array.");
  }
  return parsed as ComplianceRule[];
}

export default function ImageCompliancePage() {
  const [ruleSetName, setRuleSetName] = useState("factory-visual-safety");
  const [rulesText, setRulesText] = useState(JSON.stringify(SAMPLE_RULES, null, 2));
  const [images, setImages] = useState<ImageComplianceImageInput[]>([]);
  const [result, setResult] = useState<ImageComplianceResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadedNames = useMemo(() => new Set(images.map((item) => item.name || "")), [images]);

  const onSelectFiles = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) {
      return;
    }

    setError(null);
    setBusy(true);
    try {
      const uploaded: ImageComplianceImageInput[] = [];
      for (const file of files) {
        const uploadResult = await uploadApi.uploadFile(file);
        if (uploadResult.attachment_type !== "image") {
          continue;
        }
        uploaded.push({
          attachment_url: uploadResult.attachment_url,
          name: uploadResult.name,
        });
      }
      setImages((prev) => [...prev, ...uploaded]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Image upload failed");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  };

  const evaluate = async () => {
    setError(null);
    setResult(null);

    if (images.length === 0) {
      setError("Upload at least one image before evaluation.");
      return;
    }

    let rules: ComplianceRule[];
    try {
      rules = parseRules(rulesText);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rules JSON is invalid");
      return;
    }

    setBusy(true);
    try {
      const response = await imageComplianceApi.evaluate({
        rule_set_name: ruleSetName.trim() || "default-rule-set",
        rules,
        images,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compliance evaluation failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-white p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <h1 className="text-2xl font-semibold text-slate-900">Project 9: Image Compliance</h1>
          <p className="mt-1 text-sm text-slate-600">
            Upload images, extract structured fields with vision, and validate against rule sets.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-[420px_1fr]">
          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Rule Set Name
              </label>
              <input
                value={ruleSetName}
                onChange={(e) => setRuleSetName(e.target.value)}
                className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                placeholder="factory-visual-safety"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Rules JSON
              </label>
              <textarea
                value={rulesText}
                onChange={(e) => setRulesText(e.target.value)}
                rows={14}
                className="w-full rounded-lg border border-slate-300 p-2 font-mono text-xs"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Upload Images
              </label>
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                onChange={onSelectFiles}
                disabled={busy}
                className="w-full text-sm"
              />
              <div className="max-h-40 overflow-auto rounded-lg border border-slate-200 p-2 text-xs text-slate-600">
                {images.length === 0 ? (
                  <div>No images uploaded yet.</div>
                ) : (
                  images.map((img) => (
                    <div key={`${img.attachment_url}`} className="truncate py-0.5">
                      {img.name || img.attachment_url}
                    </div>
                  ))
                )}
              </div>
            </div>

            <button
              className="w-full rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
              disabled={busy || images.length === 0}
              onClick={() => void evaluate()}
            >
              {busy ? "Running Compliance..." : "Evaluate Images"}
            </button>

            {error && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </div>
            )}
          </section>

          <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="text-lg font-semibold text-slate-900">Run Result</h2>
            {!result ? (
              <div className="text-sm text-slate-500">Run evaluation to see extracted fields and violations.</div>
            ) : (
              <>
                <div className="grid gap-3 sm:grid-cols-3">
                  <Metric label="Run ID" value={result.run_id.slice(0, 8)} />
                  <Metric label="Passed" value={String(result.passed_count)} tone="green" />
                  <Metric label="Failed" value={String(result.failed_count)} tone="rose" />
                </div>

                <div className="space-y-3">
                  {result.results.map((item) => (
                    <article
                      key={`${item.image_url}-${item.image_name}`}
                      className={`rounded-xl border p-3 ${
                        item.passed ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="truncate text-sm font-medium text-slate-800">{item.image_name}</div>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                            item.passed ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-700"
                          }`}
                        >
                          {item.passed ? "PASS" : "FAIL"}
                        </span>
                      </div>

                      <div className="mt-2">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Extracted</div>
                        <pre className="mt-1 overflow-auto rounded-lg bg-slate-900 p-2 text-[11px] text-slate-100">
                          {JSON.stringify(item.extracted, null, 2)}
                        </pre>
                      </div>

                      <div className="mt-2 space-y-1">
                        {item.rule_results.map((rule) => (
                          <div key={rule.rule_id} className="rounded-lg border border-slate-200 bg-white px-2 py-1">
                            <div className="text-xs font-medium text-slate-800">
                              {rule.rule_id}: {rule.passed ? "pass" : "fail"}
                            </div>
                            {!rule.passed && rule.violations.length > 0 && (
                              <ul className="mt-1 list-disc pl-4 text-[11px] text-rose-700">
                                {rule.violations.map((v) => (
                                  <li key={v}>{v}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>

        {uploadedNames.size > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-500">
            Uploaded image count: {uploadedNames.size}
          </div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value, tone = "slate" }: { label: string; value: string; tone?: "slate" | "green" | "rose" }) {
  const palette =
    tone === "green"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : tone === "rose"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <div className={`rounded-lg border px-3 py-2 ${palette}`}>
      <div className="text-[10px] uppercase tracking-wide">{label}</div>
      <div className="mt-0.5 text-sm font-semibold">{value}</div>
    </div>
  );
}
