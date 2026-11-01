interface DataSourceBannerProps {
  marketsSource: 'live' | 'mock';
  pricesSource: 'live' | 'mock';
  errors: string[];
}

export function DataSourceBanner({ marketsSource, pricesSource, errors }: DataSourceBannerProps) {
  const isLive = marketsSource === 'live' || pricesSource === 'live';
  const hasErrors = errors.length > 0;
  
  if (!isLive && !hasErrors) return null;

  return (
    <div className={`mb-4 rounded-xl border p-4 ${
      hasErrors
        ? 'bg-amber-950/20 border-amber-800/40'
        : 'bg-emerald-950/20 border-emerald-800/40'
    }`}>
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
          hasErrors ? 'bg-amber-900/50' : 'bg-emerald-900/50'
        }`}>
          {hasErrors ? (
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          ) : (
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          )}
        </div>
        
        <div className="flex-1">
          <h3 className={`text-sm font-semibold mb-1 ${
            hasErrors ? 'text-amber-300' : 'text-emerald-300'
          }`}>
            {hasErrors ? '⚠️ Частичное подключение' : '🟢 Подключено к реальным данным'}
          </h3>
          
          <div className="flex flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${
                marketsSource === 'live' ? 'bg-emerald-400' : 'bg-gray-500'
              }`} />
              <span className="text-gray-400">Polymarket:</span>
              <span className={marketsSource === 'live' ? 'text-emerald-400' : 'text-gray-500'}>
                {marketsSource === 'live' ? 'LIVE' : 'Mock'}
              </span>
            </div>
            
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${
                pricesSource === 'live' ? 'bg-emerald-400' : 'bg-gray-500'
              }`} />
              <span className="text-gray-400">Binance:</span>
              <span className={pricesSource === 'live' ? 'text-emerald-400' : 'text-gray-500'}>
                {pricesSource === 'live' ? 'LIVE' : 'Mock'}
              </span>
            </div>
          </div>
          
          {hasErrors && (
            <div className="mt-2 space-y-1">
              {errors.map((error, i) => (
                <p key={i} className="text-xs text-amber-400/70">
                  • {error}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
