import { useState, useEffect } from 'react';

interface FileData {
  name: string;
  code: string;
  description: string;
}

export function CodeViewer() {
  const [activeFile, setActiveFile] = useState('market_analyzer.py');
  const [files, setFiles] = useState<FileData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadFiles = async () => {
      const fileList = [
        { name: 'market_analyzer.py', description: 'Основной модуль сканера (полный код)' },
        { name: 'requirements.txt', description: 'Зависимости Python' },
        { name: 'run.bat', description: 'Скрипт запуска для Windows' },
        { name: '.env.example', description: 'Пример конфигурации' },
      ];

      const loaded: FileData[] = [];
      for (const file of fileList) {
        try {
          const response = await fetch(`/${file.name}`);
          const code = await response.text();
          loaded.push({ ...file, code });
        } catch {
          loaded.push({ ...file, code: '// Ошибка загрузки файла' });
        }
      }
      setFiles(loaded);
      setLoading(false);
    };
    loadFiles();
  }, []);

  const currentFile = files.find(f => f.name === activeFile);

  const handleCopy = () => {
    if (currentFile) {
      navigator.clipboard.writeText(currentFile.code);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Загрузка файлов...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-300 mb-2">💻 Python код проекта</h2>
        <p className="text-sm text-gray-500">
          Полный код для запуска на вашем компьютере. Скопируйте файлы и запустите.
        </p>
      </div>

      {/* File Tabs */}
      <div className="flex gap-1 mb-4 flex-wrap">
        {files.map((file) => (
          <button
            key={file.name}
            onClick={() => setActiveFile(file.name)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              activeFile === file.name
                ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700/50'
                : 'bg-gray-800 text-gray-500 hover:text-gray-300 border border-gray-700'
            }`}
          >
            {file.name}
          </button>
        ))}
      </div>

      {/* File Description */}
      {currentFile && (
        <div className="mb-3 text-xs text-gray-500">
          📄 {currentFile.description}
        </div>
      )}

      {/* Code Block */}
      {currentFile && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800/50 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              <span className="ml-2 text-xs text-gray-500 font-mono">{currentFile.name}</span>
            </div>
            <button
              onClick={handleCopy}
              className="text-xs text-gray-500 hover:text-white transition-colors px-2 py-1 rounded hover:bg-gray-700"
            >
              📋 Копировать
            </button>
          </div>
          <pre className="p-4 overflow-x-auto text-xs leading-relaxed max-h-[600px] overflow-y-auto">
            <code className="text-gray-300">{currentFile.code}</code>
          </pre>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 p-5 rounded-xl bg-gray-900 border border-gray-800">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">🚀 Инструкция по запуску</h3>
        <ol className="space-y-2 text-xs text-gray-400">
          <li className="flex gap-2">
            <span className="text-emerald-400 font-bold">1.</span>
            <span>Установите Python 3.10+ с <a href="https://python.org" className="text-cyan-400 underline" target="_blank" rel="noreferrer">python.org</a></span>
          </li>
          <li className="flex gap-2">
            <span className="text-emerald-400 font-bold">2.</span>
            <span>Создайте папку проекта, скопируйте <code className="text-emerald-400">market_analyzer.py</code> и <code className="text-emerald-400">requirements.txt</code></span>
          </li>
          <li className="flex gap-2">
            <span className="text-emerald-400 font-bold">3.</span>
            <span>Установите зависимости: <code className="text-emerald-400 bg-gray-800 px-1 rounded">pip install -r requirements.txt</code></span>
          </li>
          <li className="flex gap-2">
            <span className="text-emerald-400 font-bold">4.</span>
            <span>Запустите: <code className="text-emerald-400 bg-gray-800 px-1 rounded">python market_analyzer.py --mock</code> (тест) или без <code className="text-emerald-400">--mock</code> (реальные данные)</span>
          </li>
          <li className="flex gap-2">
            <span className="text-emerald-400 font-bold">5.</span>
            <span>Или дважды кликните <code className="text-emerald-400 bg-gray-800 px-1 rounded">run.bat</code> на Windows</span>
          </li>
        </ol>
      </div>

      {/* Architecture */}
      <div className="mt-4 p-5 rounded-xl bg-gray-900 border border-gray-800">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">🏗 Архитектура проекта</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-400">
          <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
            <h4 className="text-emerald-400 font-medium mb-1">MarketScanner</h4>
            <p>Загружает рынки с Polymarket API, фильтрует крипто, сохраняет в SQLite</p>
          </div>
          <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
            <h4 className="text-cyan-400 font-medium mb-1">Oracle</h4>
            <p>Получает цены с Binance, парсит вопросы, считает "объективную" вероятность</p>
          </div>
          <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
            <h4 className="text-amber-400 font-medium mb-1">AnomalyDetector</h4>
            <p>Сравнивает вероятности, находит расхождения &gt; порога, сортирует</p>
          </div>
          <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
            <h4 className="text-purple-400 font-medium mb-1">Reporter</h4>
            <p>Генерирует текстовый/JSON отчёт с рекомендациями BUY YES/NO</p>
          </div>
        </div>
      </div>
    </div>
  );
}
