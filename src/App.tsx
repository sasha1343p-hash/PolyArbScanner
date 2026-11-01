import { useState, useMemo, useCallback, useEffect } from 'react';
import { Market, Filters } from './types';
import { mockMarkets, mockCurrentPrices } from './data/mockData';
import { findArbitrageOpportunities, analyzeAllMarkets } from './utils/detector';
import { fetchAllLiveData } from './api/liveData';
import { Header } from './components/Header';
import { MetricCards } from './components/MetricCards';
import { FiltersPanel } from './components/FiltersPanel';
import { OpportunitiesTable } from './components/OpportunitiesTable';
import { EdgeChart } from './components/EdgeChart';
import { MarketDetail } from './components/MarketDetail';
import { DataSourceBanner } from './components/DataSourceBanner';

export default function App() {
  // Состояние данных
  const [markets, setMarkets] = useState<Market[]>(mockMarkets);
  const [livePrices, setLivePrices] = useState<Record<string, number>>(mockCurrentPrices);
  const [marketsSource, setMarketsSource] = useState<'live' | 'mock'>('mock');
  const [pricesSource, setPricesSource] = useState<'live' | 'mock'>('mock');
  const [dataErrors, setDataErrors] = useState<string[]>([]);
  
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
  const [initialLoading, setInitialLoading] = useState(true);

  // Загрузка данных
  const loadData = useCallback(async (showLoading = true) => {
    if (showLoading) setIsScanning(true);
    
    try {
      const result = await fetchAllLiveData(mockMarkets, mockCurrentPrices);
      
      setMarkets(result.markets);
      setLivePrices(result.prices);
      setMarketsSource(result.marketsSource);
      setPricesSource(result.pricesSource);
      setDataErrors(result.errors);
      setLastScanTime(new Date().toLocaleTimeString('ru-RU'));
      setScanCount(c => c + 1);
      
      console.log('📊 Данные обновлены:', {
        markets: result.markets.length,
        marketsSource: result.marketsSource,
        pricesSource: result.pricesSource,
        errors: result.errors,
      });
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      setDataErrors(['Неизвестная ошибка загрузки']);
    } finally {
      setIsScanning(false);
      setInitialLoading(false);
    }
  }, []);

  // Первоначальная загрузка
  useEffect(() => {
    loadData(true);
  }, [loadData]);

  // Анализ всех рынков
  const allAnalysis = useMemo(
    () => analyzeAllMarkets(markets, livePrices),
    [markets, livePrices, scanCount]
  );

  // Все возможности (без фильтра по порогу — фильтруем в UI)
  const allOpportunities = useMemo(
    () => findArbitrageOpportunities(markets, 0.01, livePrices),
    [markets, livePrices, scanCount]
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
    const totalMarkets = markets.length;
    const opportunities = filteredOpportunities.length;
    const avgEdge = opportunities > 0
      ? filteredOpportunities.reduce((s, o) => s + Math.abs(o.edge), 0) / opportunities
      : 0;
    const totalVolume = filteredOpportunities.reduce((s, o) => s + o.market.volume, 0);
    const highSeverity = filteredOpportunities.filter(o => o.severity === 'high').length;
    const buyYes = filteredOpportunities.filter(o => o.recommendation === 'BUY YES').length;
    const buyNo = filteredOpportunities.filter(o => o.recommendation === 'BUY NO').length;

    return { totalMarkets, opportunities, avgEdge, totalVolume, highSeverity, buyYes, buyNo };
  }, [markets, filteredOpportunities]);

  // Обработчик обновления
  const handleRefresh = useCallback(() => {
    loadData(true);
  }, [loadData]);

  // Выбранный рынок для детального просмотра
  const selectedMarket = selectedMarketId
    ? allAnalysis.find(a => a.market.id === selectedMarketId)
    : null;

  // Показываем loader при первой загрузке
  if (initialLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center animate-pulse">
            <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Загрузка данных...</h2>
          <p className="text-sm text-gray-500">Подключение к Polymarket и Binance API</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100">
      <Header
        lastScanTime={lastScanTime}
        isScanning={isScanning}
        onRefresh={handleRefresh}
        totalMarkets={metrics.totalMarkets}
        opportunities={metrics.opportunities}
        marketsSource={marketsSource}
        pricesSource={pricesSource}
      />

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Data Source Banner */}
        <DataSourceBanner
          marketsSource={marketsSource}
          pricesSource={pricesSource}
          errors={dataErrors}
        />

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
              markets={markets}
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
          <p>PolyArb Scanner v2.1 • {marketsSource === 'live' ? '🟢 LIVE' : '⚪ Mock'} Data</p>
          <p>⚠️ Не является финансовым советом</p>
        </div>
      </footer>
    </div>
  );
}
