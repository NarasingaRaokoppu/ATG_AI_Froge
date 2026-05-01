import { type MouseEvent, useRef, useState } from "react";

import type { Thread } from "../../types";
import { useAuthStore } from "../../lib/authStore";

interface SidebarProps {
  threads: Thread[];
  activeThreadId: string | null;
  onSelect: (threadId: string | null) => void;
  onNewChat: () => void;
  onDelete: (threadId: string) => void;
  onRename: (threadId: string, newTitle: string) => Promise<void>;
  loading: boolean;
}

export function Sidebar({
  threads,
  activeThreadId,
  onSelect,
  onNewChat,
  onDelete,
  onRename,
  loading,
}: SidebarProps) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const editRef = useRef<HTMLInputElement>(null);

  return (
    <aside className="flex h-full w-72 max-w-full flex-col border-r border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900">
      <div className="border-b border-gray-200 p-3 dark:border-gray-800">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <p className="px-2 py-3 text-xs text-gray-500 dark:text-gray-400">
            Loading threads…
          </p>
        ) : threads.length === 0 ? (
          <p className="px-2 py-3 text-xs text-gray-500 dark:text-gray-400">
            Start a new conversation.
          </p>
        ) : (
          <ul className="space-y-1">
            {threads.map((t) => {
              const isActive = t.id === activeThreadId;
              const isEditing = editingId === t.id;

              const startEdit = (e: MouseEvent) => {
                e.stopPropagation();
                setEditingId(t.id);
                setEditValue(t.title ?? "");
                setTimeout(() => editRef.current?.select(), 0);
              };

              const commitEdit = async () => {
                const trimmed = editValue.trim();
                if (trimmed && trimmed !== t.title) {
                  await onRename(t.id, trimmed);
                }
                setEditingId(null);
              };

              return (
                <li key={t.id} className="group relative">
                  {isEditing ? (
                    <input
                      ref={editRef}
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={commitEdit}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") void commitEdit();
                        if (e.key === "Escape") setEditingId(null);
                      }}
                      className="w-full rounded-lg border border-blue-400 bg-white px-3 py-2 text-sm text-gray-900 outline-none dark:bg-gray-800 dark:text-gray-100"
                      aria-label="Rename thread"
                    />
                  ) : (
                    <button
                      type="button"
                      onClick={() => onSelect(t.id)}
                      onDoubleClick={startEdit}
                      title="Double-click to rename"
                      className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                        isActive
                          ? "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100"
                          : "text-gray-700 hover:bg-gray-200 dark:text-gray-200 dark:hover:bg-gray-800"
                      }`}
                    >
                      {t.title || "Untitled chat"}
                    </button>
                  )}

                  {!isEditing && (
                    <div className="absolute right-1 top-1 flex flex-col gap-0.5 opacity-100 transition lg:opacity-0 lg:group-hover:opacity-100">
                      <button
                        type="button"
                        aria-label="Rename thread"
                        onClick={startEdit}
                        className="rounded p-1 text-xs text-gray-500 hover:bg-gray-200 hover:text-gray-900 dark:hover:bg-gray-700 dark:hover:text-gray-100"
                      >
                        ✎
                      </button>
                      <button
                        type="button"
                        aria-label="Delete thread"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm("Delete this conversation?")) onDelete(t.id);
                        }}
                        className="rounded p-1 text-xs text-gray-500 hover:bg-red-100 hover:text-red-700 dark:hover:bg-red-900/30 dark:hover:text-red-400"
                      >
                        ✕
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="border-t border-gray-200 p-3 text-xs text-gray-600 dark:border-gray-800 dark:text-gray-300">
        <div className="truncate" title={user?.email}>
          {user?.email}
        </div>
        <button
          type="button"
          onClick={logout}
          className="mt-2 w-full rounded-md border border-gray-300 px-2 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
