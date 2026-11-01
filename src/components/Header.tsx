interface HeaderProps {
  lastScanTime: string;
  isScanning: boolean;
  onRefresh: () => void;
  totalMarkets: number;
  opportunities: number;
  marketsSource: 'live' | 'mock';
  pricesSource: 'live' | 'mock';
}

export function Header({
  lastScanTime,
  isScanning,
  onRefresh,
  totalMarkets,
  opportunities,
  marketsSource,
  pricesSource,
}: HeaderProps) {
  const isLive = marketsSource === 'live' || pricesSource === 'live';
  
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800/50 bg-[#0a0a0f]/90 backdrop-blur-xl">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              {isScanning && (
                <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full animate-ping" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-white tracking-tight">PolyArb Scanner</h1>
                {isLive && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-900/50 border border-emerald-700/50">
                    <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                    <span className="text-[10px] font-medium text-emerald-400">LIVE</span>
                  </span>
                )}
              </div>
              <p className="text-[10px] text-gray-500 -mt-0.5">Prediction Markets Arbitrage</p>
            </div>
          </div>

          {/* Status & Actions */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-4 text-xs text-gray-500">
              <span>
                <span className="text-gray-400">{totalMarkets}</span> рынков
              </span>
              <span className="w-px h-3 bg-gray-800" />
              <span>
                <span className="text-emerald-400">{opportunities}</span> возможностей
              </span>
              <span className="w-px h-3 bg-gray-800" />
              <span>Обновлено: {lastScanTime}</span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={isScanning}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600/20 border border-emerald-600/30 text-emerald-400 text-sm font-medium hover:bg-emerald-600/30 hover:border-emerald-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="hidden sm:inline">{isScanning ? 'Сканирование...' : 'Обновить'}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
