import React from 'react';

export function BacktestResult({ result, outDir }) {
  const base = encodeURIComponent(outDir);

  // 中文映射和格式化逻辑
  const zhMap = {
    "Annualized Return": "年化收益率",
    "Annualized Volatility": "年化波动率",
    "Max Drawdown": "最大回撤",
    "Sharpe Ratio": "夏普比率",
  };

  return (
    <div className="space-y-6 mt-6">
      <h2 className="text-xl font-bold">回测结果：{result.run_id}</h2>
      {Object.entries(result.results).map(([symbol, info]) => {
        const sigFile = info.signals.split('\\').pop();
        const btFile  = info.backtest?.split('\\').pop();
        const eqFile  = info.equity_png?.split('\\').pop();

        return (
          <div key={symbol} className="border p-4 rounded">
            <h3 className="text-lg font-semibold mb-2">{symbol}</h3>

            <img
              src={`http://localhost:5000/results/${result.run_id}/${sigFile}?base=${base}`}
              alt={`${symbol} signals`}
              className="mb-4 w-full"
            />

            {btFile && (
              <img
                src={`http://localhost:5000/results/${result.run_id}/${btFile}?base=${base}`}
                alt={`${symbol} backtest`}
                className="mb-4 w-full "
              />
            )}

            {eqFile && (
              <img
                src={`http://localhost:5000/results/${result.run_id}/${eqFile}?base=${base}`}
                alt={`${symbol} equity curve`}
                className="mb-4 w-full"
              />
            )}

            {info.performance && (
              <div className="bg-gray-100 p-4 rounded space-y-1">
                {Object.entries(info.performance).map(([key, val]) => {
                  // 翻译标签
                  const label = zhMap[key] || key;
                  // 格式化数值：除夏普比率外乘100并保留两位小数
                  const text = key === "Sharpe Ratio"
                    ? val.toFixed(2)
                    : (val * 100).toFixed(2) + "%";
                  return (
                    <div key={key} className="flex justify-between">
                      <span>{label}</span>
                      <span>{text}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
