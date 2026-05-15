import type { DatabaseConnection } from "../../types";

interface Props {
  connections: DatabaseConnection[];
  activeConnectionId: string | null;
  onSelect: (id: string) => void;
  onEdit: (item: DatabaseConnection) => void;
  onDelete: (item: DatabaseConnection) => void;
  onTest: (item: DatabaseConnection) => void;
}

export function ConnectionList({
  connections,
  activeConnectionId,
  onSelect,
  onEdit,
  onDelete,
  onTest,
}: Props) {
  if (connections.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-600">
        No connections yet. Add one to start querying.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {connections.map((item) => (
        <button
          key={item.id}
          className={`w-full rounded-xl border p-3 text-left transition ${
            activeConnectionId === item.id
              ? "border-slate-900 bg-slate-100"
              : "border-slate-200 bg-white hover:border-slate-400"
          }`}
          onClick={() => onSelect(item.id)}
        >
          <div className="flex items-center justify-between gap-2">
            <div>
              <div className="font-medium text-slate-900">{item.name}</div>
              <div className="text-xs text-slate-600">
                {item.username}@{item.host}:{item.port}/{item.database}
              </div>
            </div>
            <div className="flex gap-1">
              <span
                className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  onTest(item);
                }}
              >
                Test
              </span>
              <span
                className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(item);
                }}
              >
                Edit
              </span>
              <span
                className="rounded-md border border-rose-300 px-2 py-1 text-xs text-rose-700"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(item);
                }}
              >
                Delete
              </span>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
