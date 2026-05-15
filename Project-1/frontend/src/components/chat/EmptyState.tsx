import { ProjectLinks } from "../navigation/ProjectLinks";

export function EmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center px-4 py-8">
      <div className="w-full max-w-5xl text-center">
        <div className="mb-4 text-4xl">💬</div>
        
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 sm:text-2xl">
          What would you like to do?
        </h2>
        
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Start a conversation, upload documents, generate images, or analyze files.
        </p>

        <div className="mt-6 text-left">
          <div className="mb-3 text-center text-xs font-semibold uppercase tracking-[0.2em] text-gray-500 dark:text-gray-400">
            Jump To Projects
          </div>
          <ProjectLinks variant="cards" />
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <SuggestedAction
            icon="💭"
            title="Ask a Question"
            description="Chat about anything"
          />
          <SuggestedAction
            icon="📕"
            title="Upload PDF"
            description="Analyze documents"
          />
          <SuggestedAction
            icon="🎨"
            title="Generate Image"
            description="Create with AI"
          />
          <SuggestedAction
            icon="📎"
            title="Analyze File"
            description="Upload & discuss"
          />
        </div>

        <p className="mt-6 text-xs text-gray-500 dark:text-gray-400">
          Use the input box below to get started.
        </p>
      </div>
    </div>
  );
}

function SuggestedAction({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50">
      <div className="text-xl">{icon}</div>
      <h3 className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">
        {title}
      </h3>
      <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
        {description}
      </p>
    </div>
  );
}
