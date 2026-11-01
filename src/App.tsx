import { useState, useMemo, useCallback } from 'react';
import { Market, ArbitrageOpportunity, Filters } from './types';
import { mockMarkets } from './data/mockData';
import { findArbitrageOpportunities, analyzeAllMarkets } from './utils/detector';
import { Header } from './components/Header';
import { MetricCards } from './components/MetricCards';
import { FiltersPanel } from './components/FiltersPanel';
import { OpportunitiesTable } from './components/OpportunitiesTable';
import { EdgeChart } from './components/EdgeChart';
import { MarketDetail } from './components/MarketDetail';

export default function App() {
  const [filters, setFilters] = useState<Filters>({
    category: 'all',
    minVolume: 0,
    minEdge: 0.10,
    sortBy: 'edge',
    sortDir: 'desc',
  });
  const [selectedMarketId, setSelectedMarketId] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScanTime, setLastScanTime] = useState<string>(new Date().toLocaleTimeString('ru-RU'));
  const [scanCount, setScanCount] = useState(0);

  // Анализ всех рынков
  const allAnalysis = useMemo(() => analyzeAllMarkets(mockMarkets), [scanCount]);

  // Все возможности (без фильтра по порогу — фильтруем в UI)
  const allOpportunities = useMemo(
    () => findArbitrageOpportunities(mockMarkets, 0.01),
    [scanCount]
  );

  // Фильтрация и сортировка
  const filteredOpportunities = useMemo(() => {
    let result = allOpportunities.filter(opp => {
      if (filters.category !== 'all' && opp.market.category !== filters.category) return false;
      if (opp.market.volume < filters.minVolume) return false;
      if (Math.abs(opp.edge) < filters.minEdge) return false;
      return true;
    });

    // Сортировка
    result.sort((a, b) => {
      let valA: number, valB: number;
      switch (filters.sortBy) {
        case 'edge':
          valA = Math.abs(a.edge); valB = Math.abs(b.edge); break;
        case 'volume':
          valA = a.market.volume; valB = b.market.volume; break;
        case 'market_price':
          valA = a.market.implied_probability; valB = b.market.implied_probability; break;
        case 'oracle_price':
          valA = a.oracle.oracle_probability; valB = b.oracle.oracle_probability; break;
        case 'expiry':
          valA = a.oracle.daysToExpiry || 9999; valB = b.oracle.daysToExpiry || 9999; break;
        default:
          valA = Math.abs(a.edge); valB = Math.abs(b.edge);
      }
      return filters.sortDir === 'desc' ? valB - valA : valA - valB;
    });

    return result;
  }, [allOpportunities, filters]);

  // Метрики
  const metrics = useMemo(() => {
    const totalMarkets = mockMarkets.length;
    const opportunities = filteredOpportunities.length;
    const avgEdge = opportunities > 0
      ? filteredOpportunities.reduce((s, o) => s + Math.abs(o.edge), 0) / opportunities
      : 0;
    const totalVolume = filteredOpportunities.reduce((s, o) => s + o.market.volume, 0);
    const highSeverity = filteredOpportunities.filter(o => o.severity === 'high').length;
    const buyYes = filteredOpportunities.filter(o => o.recommendation === 'BUY YES').length;
    const buyNo = filteredOpportunities.filter(o => o.recommendation === 'BUY NO').length;

    return { totalMarkets, opportunities, avgEdge, totalVolume, highSeverity, buyYes, buyNo };
  }, [filteredOpportunities]);

  // Обработчик обновления
  const handleRefresh = useCallback(() => {
    setIsScanning(true);
    // Имитация задержки сканирования
    setTimeout(() => {
      setScanCount(c => c + 1);
      setLastScanTime(new Date().toLocaleTimeString('ru-RU'));
      setIsScanning(false);
    }, 1500);
  }, []);

  // Выбранный рынок для детального просмотра
  const selectedMarket = selectedMarketId
    ? allAnalysis.find(a => a.market.id === selectedMarketId)
    : null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100">
      <Header
        lastScanTime={lastScanTime}
        isScanning={isScanning}
        onRefresh={handleRefresh}
        totalMarkets={metrics.totalMarkets}
        opportunities={metrics.opportunities}
      />

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Metric Cards */}
        <MetricCards metrics={metrics} />

        {/* Main Grid: Filters + Content */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6 mt-6">
          {/* Filters Sidebar */}
          <aside className="lg:sticky lg:top-24 lg:self-start">
            <FiltersPanel filters={filters} onFiltersChange={setFilters} />
          </aside>

          {/* Main Content */}
          <div className="space-y-6">
            {/* Opportunities Table */}
            <OpportunitiesTable
              opportunities={filteredOpportunities}
              filters={filters}
              onFiltersChange={setFilters}
              onSelectMarket={setSelectedMarketId}
              selectedMarketId={selectedMarketId}
            />

            {/* Edge Chart */}
            <EdgeChart
              marketId={selectedMarketId || (filteredOpportunities[0]?.market.id ?? null)}
              markets={mockMarkets}
              onSelectMarket={setSelectedMarketId}
            />

            {/* Market Detail */}
            {selectedMarket && (
              <MarketDetail
                market={selectedMarket.market}
                oracle={selectedMarket.oracle}
                edge={selectedMarket.edge}
                onClose={() => setSelectedMarketId(null)}
              />
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 mt-12 py-6">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between text-xs text-gray-600">
          <p>PolyArb Scanner v2.0 • Mock Data Mode</p>
          <p>⚠️ Не является финансовым советом</p>
        </div>
      </footer>
    </div>
  );
}
