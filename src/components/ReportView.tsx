import { useState } from 'react';

interface ReportViewProps {
  reportText: string;
  format: 'text' | 'json';
  onFormatChange: (format: 'text' | 'json') => void;
}

export function ReportView({ reportText, format, onFormatChange }: ReportViewProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-300">📋 Отчёт сканера</h2>
        <div className="flex items-center gap-3">
          {/* Format Toggle */}
          <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => onFormatChange('text')}
              className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                format === 'text'
                  ? 'bg-emerald-900/50 text-emerald-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              Text
            </button>
            <button
              onClick={() => onFormatChange('json')}
              className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                format === 'json'
                  ? 'bg-emerald-900/50 text-emerald-400'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              JSON
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-700 text-xs text-gray-400 hover:text-white hover:border-gray-600 transition-all"
          >
            {copied ? '✅ Скопировано!' : '📋 Копировать'}
          </button>
        </div>
      </div>

      {/* Report Content */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
        {/* Terminal Header */}
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/50 border-b border-gray-800">
          <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
          <span className="ml-2 text-xs text-gray-500 font-mono">
            market_analyzer.py — {format === 'text' ? 'stdout' : 'output.json'}
          </span>
        </div>

        {/* Report Body */}
        <pre className={`p-6 overflow-x-auto text-sm leading-relaxed ${
          format === 'json' ? 'text-cyan-300' : 'text-gray-300'
        }`}>
          <code>{reportText}</code>
        </pre>
      </div>

      {/* Info */}
      <div className="mt-4 p-4 rounded-xl bg-gray-900 border border-gray-800">
        <p className="text-xs text-gray-500">
          💡 Этот отчёт генерируется модулем <code className="text-emerald-400">reporter.py</code>. 
          В Python-версии он выводится в консоль через <code className="text-emerald-400">logging</code> и 
          может быть сохранён в файл с флагом <code className="text-emerald-400">--output json</code>.
        </p>
      </div>
    </div>
  );
}
