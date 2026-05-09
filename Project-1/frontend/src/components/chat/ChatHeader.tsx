import type { Thread } from "../../types";

interface ChatHeaderProps {
  activeThread: Thread | null;
  sidebarOpen: boolean;
  onSidebarToggle: () => void;
}

export function ChatHeader({
  activeThread,
  sidebarOpen,
  onSidebarToggle,
}: ChatHeaderProps) {
  return (
    <header className="border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-900 sm:px-6 sm:py-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onSidebarToggle}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800 lg:hidden"
          aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
        >
          ≡
        </button>

        <div className="flex-1">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {activeThread?.title || "New conversation"}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Powered by Gemini via LiteLLM proxy
          </p>
        </div>
      </div>
    </header>
  );
}
