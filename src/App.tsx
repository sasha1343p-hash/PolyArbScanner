import { useState, useMemo } from 'react';
import { Market, ArbitrageOpportunity } from './types';
import { mockMarkets } from './data/mockData';
import { findArbitrageOpportunities, analyzeAllMarkets } from './utils/detector';
import { generateTextReport, generateJsonReport } from './utils/reporter';
import { Dashboard } from './components/Dashboard';
import { ReportView } from './components/ReportView';
import { CodeViewer } from './components/CodeViewer';
import { AllMarketsView } from './components/AllMarketsView';

type Tab = 'dashboard' | 'all-markets' | 'report' | 'code';

export default function App() {
  const [threshold, setThreshold] = useState(0.15);
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [reportFormat, setReportFormat] = useState<'text' | 'json'>('text');

  // Анализ всех рынков
  const allAnalysis = useMemo(() => analyzeAllMarkets(mockMarkets), []);

  // Поиск арбитражных возможностей
  const opportunities = useMemo(
    () => findArbitrageOpportunities(mockMarkets, threshold),
    [threshold]
  );

  // Генерация отчёта
  const reportText = useMemo(() => {
    if (reportFormat === 'json') {
      return generateJsonReport(opportunities);
    }
    return generateTextReport(opportunities);
  }, [opportunities, reportFormat]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-xl">
                🔍
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  PolyArb Scanner
                </h1>
                <p className="text-xs text-gray-500">Сканер арбитражных возможностей на предиктивных рынках</p>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-400">Порог edge:</label>
                <input
                  type="range"
                  min="0.05"
                  max="0.40"
                  step="0.01"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-24 accent-emerald-500"
                />
                <span className="text-sm font-mono text-emerald-400 w-10">
                  {(threshold * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
                <span className="text-xs text-gray-500 px-2">Режим:</span>
                <span className="text-xs bg-emerald-900/50 text-emerald-400 px-2 py-0.5 rounded">
                  MOCK DATA
                </span>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4">
            {[
              { id: 'dashboard' as Tab, label: '🔥 Возможности', count: opportunities.length },
              { id: 'all-markets' as Tab, label: '📊 Все рынки', count: mockMarkets.length },
              { id: 'report' as Tab, label: '📋 Отчёт' },
              { id: 'code' as Tab, label: '💻 Python код' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-gray-800 text-emerald-400 border-b-2 border-emerald-500'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && (
                  <span className={`ml-2 px-1.5 py-0.5 rounded-full text-xs ${
                    activeTab === tab.id ? 'bg-emerald-900/50 text-emerald-400' : 'bg-gray-700 text-gray-400'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && (
          <Dashboard opportunities={opportunities} threshold={threshold} />
        )}
        {activeTab === 'all-markets' && (
          <AllMarketsView analysis={allAnalysis} threshold={threshold} />
        )}
        {activeTab === 'report' && (
          <ReportView
            reportText={reportText}
            format={reportFormat}
            onFormatChange={setReportFormat}
          />
        )}
        {activeTab === 'code' && <CodeViewer />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-600">
          <p>⚠️ Это демонстрационная версия. Не является финансовым советом.</p>
          <p className="mt-1">PolyArb Scanner v1.0 • Mock Data Mode • {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}
