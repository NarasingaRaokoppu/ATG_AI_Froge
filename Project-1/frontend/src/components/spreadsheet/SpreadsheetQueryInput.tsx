interface Props {
  question: string;
  onChange: (value: string) => void;
  onSubmit: () => void | Promise<void>;
  disabled?: boolean;
}

export function SpreadsheetQueryInput({
  question,
  onChange,
  onSubmit,
  disabled,
}: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Ask a question
      </label>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-lg border border-slate-300 p-2 text-sm"
          placeholder="Which employee has highest salary?"
          value={question}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
          disabled={disabled || !question.trim()}
          onClick={() => void onSubmit()}
        >
          Query
        </button>
      </div>
    </div>
  );
}
