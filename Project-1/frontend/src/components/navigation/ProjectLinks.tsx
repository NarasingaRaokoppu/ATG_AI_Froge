import { Link, useLocation } from "react-router-dom";

type Variant = "compact" | "cards";

const PROJECT_LINKS = [
  {
    to: "/data-explorer",
    badge: "Project 8",
    label: "SQL Data Explorer",
    description: "Query databases and spreadsheets with natural language.",
  },
  {
    to: "/spreadsheet-explorer",
    badge: "Project 9",
    label: "Spreadsheet Agent",
    description: "Upload sheets, connect Google Sheets, and stream analysis.",
  },
  {
    to: "/research-digest",
    badge: "Project 10",
    label: "Research Digest",
    description: "Search arXiv, gather evidence, and stream a live digest.",
  },
];

interface ProjectLinksProps {
  variant?: Variant;
}

export function ProjectLinks({ variant = "compact" }: ProjectLinksProps) {
  const location = useLocation();

  if (variant === "cards") {
    return (
      <div className="grid gap-3 sm:grid-cols-3">
        {PROJECT_LINKS.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`rounded-xl border p-4 text-left transition ${
                isActive
                  ? "border-blue-500 bg-blue-50 shadow-sm dark:border-blue-400 dark:bg-blue-500/10"
                  : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/60 dark:border-gray-700 dark:bg-gray-800/40 dark:hover:border-blue-500"
              }`}
            >
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
                {item.badge}
              </div>
              <div className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                {item.label}
              </div>
              <p className="mt-1 text-xs leading-5 text-gray-600 dark:text-gray-400">
                {item.description}
              </p>
            </Link>
          );
        })}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {PROJECT_LINKS.map((item) => {
        const isActive = location.pathname === item.to;
        return (
          <Link
            key={item.to}
            to={item.to}
            className={`inline-flex items-center rounded-full border px-3 py-1.5 text-xs font-medium transition ${
              isActive
                ? "border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-500/10 dark:text-blue-200"
                : "border-gray-300 text-gray-600 hover:border-blue-300 hover:text-blue-700 dark:border-gray-700 dark:text-gray-300 dark:hover:border-blue-500 dark:hover:text-blue-200"
            }`}
          >
            {item.badge}: {item.label}
          </Link>
        );
      })}
    </div>
  );
}
