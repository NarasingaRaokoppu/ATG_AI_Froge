import { type MouseEvent, useRef, useState, useMemo } from "react";

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
  const [searchQuery, setSearchQuery] = useState("");
  const editRef = useRef<HTMLInputElement>(null);

  // Group and filter threads
  const groupedThreads = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    // Filter by search query
    const filtered = threads.filter((t) =>
      (t.title || "").toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Group by date
    const groups: Record<string, Thread[]> = {
      today: [],
      yesterday: [],
      week: [],
      older: [],
    };

    for (const thread of filtered) {
      const threadDate = new Date(
        thread.created_at || new Date().toISOString()
      );
      const threadDateOnly = new Date(
        threadDate.getFullYear(),
        threadDate.getMonth(),
        threadDate.getDate()
      );

      if (threadDateOnly.getTime() === today.getTime()) {
        groups.today.push(thread);
      } else if (threadDateOnly.getTime() === yesterday.getTime()) {
        groups.yesterday.push(thread);
      } else if (threadDateOnly.getTime() >= weekAgo.getTime()) {
        groups.week.push(thread);
      } else {
        groups.older.push(thread);
      }
    }

    return groups;
  }, [threads, searchQuery]);

  return (
    <aside className="flex h-full w-72 max-w-full flex-col border-r border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900">
      {/* Header with new chat button */}
      <div className="border-b border-gray-200 p-3 dark:border-gray-800">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
        >
          + New chat
        </button>
      </div>

      {/* Search box */}
      <div className="border-b border-gray-200 p-2 dark:border-gray-800">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search conversations..."
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400"
          aria-label="Search conversations"
        />
      </div>

      {/* Threads list with grouping */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <p className="px-2 py-3 text-xs text-gray-500 dark:text-gray-400">
            Loading conversations…
          </p>
        ) : threads.length === 0 ? (
          <p className="px-2 py-3 text-xs text-gray-500 dark:text-gray-400">
            Start a new conversation.
          </p>
        ) : Object.values(groupedThreads).every((g) => g.length === 0) ? (
          <p className="px-2 py-3 text-xs text-gray-500 dark:text-gray-400">
            No conversations match your search.
          </p>
        ) : (
          <div className="space-y-4">
            {/* Today */}
            {groupedThreads.today.length > 0 && (
              <ThreadGroup
                title="Today"
                threads={groupedThreads.today}
                activeThreadId={activeThreadId}
                editingId={editingId}
                editValue={editValue}
                editRef={editRef}
                onSetEditValue={setEditValue}
                onSelect={onSelect}
                onEdit={(id) => {
                  setEditingId(id);
                  setEditValue(threads.find((t) => t.id === id)?.title ?? "");
                  setTimeout(() => editRef.current?.select(), 0);
                }}
                onCommitEdit={async (id) => {
                  const trimmed = editValue.trim();
                  if (trimmed && trimmed !== threads.find((t) => t.id === id)?.title) {
                    await onRename(id, trimmed);
                  }
                  setEditingId(null);
                }}
                onCancelEdit={() => setEditingId(null)}
                onDelete={onDelete}
              />
            )}

            {/* Yesterday */}
            {groupedThreads.yesterday.length > 0 && (
              <ThreadGroup
                title="Yesterday"
                threads={groupedThreads.yesterday}
                activeThreadId={activeThreadId}
                editingId={editingId}
                editValue={editValue}
                editRef={editRef}
                onSetEditValue={setEditValue}
                onSelect={onSelect}
                onEdit={(id) => {
                  setEditingId(id);
                  setEditValue(threads.find((t) => t.id === id)?.title ?? "");
                  setTimeout(() => editRef.current?.select(), 0);
                }}
                onCommitEdit={async (id) => {
                  const trimmed = editValue.trim();
                  if (trimmed && trimmed !== threads.find((t) => t.id === id)?.title) {
                    await onRename(id, trimmed);
                  }
                  setEditingId(null);
                }}
                onCancelEdit={() => setEditingId(null)}
                onDelete={onDelete}
              />
            )}

            {/* This Week */}
            {groupedThreads.week.length > 0 && (
              <ThreadGroup
                title="This Week"
                threads={groupedThreads.week}
                activeThreadId={activeThreadId}
                editingId={editingId}
                editValue={editValue}
                editRef={editRef}
                onSetEditValue={setEditValue}
                onSelect={onSelect}
                onEdit={(id) => {
                  setEditingId(id);
                  setEditValue(threads.find((t) => t.id === id)?.title ?? "");
                  setTimeout(() => editRef.current?.select(), 0);
                }}
                onCommitEdit={async (id) => {
                  const trimmed = editValue.trim();
                  if (trimmed && trimmed !== threads.find((t) => t.id === id)?.title) {
                    await onRename(id, trimmed);
                  }
                  setEditingId(null);
                }}
                onCancelEdit={() => setEditingId(null)}
                onDelete={onDelete}
              />
            )}

            {/* Older */}
            {groupedThreads.older.length > 0 && (
              <ThreadGroup
                title="Older"
                threads={groupedThreads.older}
                activeThreadId={activeThreadId}
                editingId={editingId}
                editValue={editValue}
                editRef={editRef}
                onSetEditValue={setEditValue}
                onSelect={onSelect}
                onEdit={(id) => {
                  setEditingId(id);
                  setEditValue(threads.find((t) => t.id === id)?.title ?? "");
                  setTimeout(() => editRef.current?.select(), 0);
                }}
                onCommitEdit={async (id) => {
                  const trimmed = editValue.trim();
                  if (trimmed && trimmed !== threads.find((t) => t.id === id)?.title) {
                    await onRename(id, trimmed);
                  }
                  setEditingId(null);
                }}
                onCancelEdit={() => setEditingId(null)}
                onDelete={onDelete}
              />
            )}
          </div>
        )}
      </div>

      {/* User profile footer */}
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

interface ThreadGroupProps {
  title: string;
  threads: Thread[];
  activeThreadId: string | null;
  editingId: string | null;
  editValue: string;
  editRef: React.RefObject<HTMLInputElement>;
  onSetEditValue: (value: string) => void;
  onSelect: (threadId: string) => void;
  onEdit: (threadId: string) => void;
  onCommitEdit: (threadId: string) => Promise<void>;
  onCancelEdit: () => void;
  onDelete: (threadId: string) => void;
}

function ThreadGroup({
  title,
  threads,
  activeThreadId,
  editingId,
  editValue,
  editRef,
  onSetEditValue,
  onSelect,
  onEdit,
  onCommitEdit,
  onCancelEdit,
  onDelete,
}: ThreadGroupProps) {
  return (
    <div>
      <h3 className="px-2 py-1 text-[11px] font-semibold uppercase text-gray-500 dark:text-gray-400">
        {title}
      </h3>
      <ul className="space-y-1">
        {threads.map((t) => {
          const isActive = t.id === activeThreadId;
          const isEditing = editingId === t.id;

          return (
            <li key={t.id} className="group relative">
              {isEditing ? (
                <input
                  ref={editRef}
                  value={editValue}
                  onChange={(e) => onSetEditValue(e.target.value)}
                  onBlur={() => void onCommitEdit(t.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void onCommitEdit(t.id);
                    if (e.key === "Escape") onCancelEdit();
                  }}
                  className="w-full rounded-lg border border-blue-400 bg-white px-3 py-2 text-sm text-gray-900 outline-none dark:bg-gray-800 dark:text-gray-100"
                  aria-label="Rename conversation"
                />
              ) : (
                <button
                  type="button"
                  onClick={() => onSelect(t.id)}
                  onDoubleClick={() => onEdit(t.id)}
                  title="Double-click to rename"
                  className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                    isActive
                      ? "bg-blue-100 font-semibold text-blue-900 dark:bg-blue-900/40 dark:text-blue-100"
                      : "text-gray-700 hover:bg-gray-200 dark:text-gray-200 dark:hover:bg-gray-800"
                  }`}
                >
                  {t.title || "Untitled conversation"}
                </button>
              )}

              {!isEditing && (
                <div className="absolute right-1 top-1 flex flex-col gap-0.5 opacity-100 transition lg:opacity-0 lg:group-hover:opacity-100">
                  <button
                    type="button"
                    aria-label="Rename conversation"
                    onClick={() => onEdit(t.id)}
                    className="rounded p-1 text-xs text-gray-500 hover:bg-gray-200 hover:text-gray-900 dark:hover:bg-gray-700 dark:hover:text-gray-100"
                  >
                    ✎
                  </button>
                  <button
                    type="button"
                    aria-label="Delete conversation"
                    onClick={(e: MouseEvent) => {
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
    </div>
  );
}
