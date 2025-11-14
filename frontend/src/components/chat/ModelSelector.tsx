'use client';

import { useChatStore } from '../../stores/chatStore';

export default function ModelSelector() {
  const { models, selectedModel, setSelectedModel } = useChatStore();

  if (models.length === 0) {
    return <div className="text-sm text-gray-500">Loading models...</div>;
  }

  return (
    <div className="flex items-center space-x-2">
      <label htmlFor="model-select" className="text-sm font-medium">
        Model:
      </label>
      <select
        id="model-select"
        value={selectedModel}
        onChange={(e) => setSelectedModel(e.target.value)}
        className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800"
      >
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name} ({model.provider})
          </option>
        ))}
      </select>
    </div>
  );
}
