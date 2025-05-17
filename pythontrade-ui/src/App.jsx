// src/App.jsx
import React, { useState } from 'react';
import { runBacktest }           from './api';
import { StrategySelector }      from './components/StrategySelector';
import { ParameterInput }        from './components/ParameterInput';
import { BacktestResult }        from './components/BacktestResult';
import { SymbolSelector }        from './components/SymbolSelector';

export default function App() {
  // 表单状态
  const [strategy, setStrategy]     = useState('bollinger_narrow');
  const [symbols,  setSymbols]      = useState('BTC/USD');
  const [timeframe,setTimeframe]    = useState('4h');
  const [limit,    setLimit]        = useState(300);
  const [lastN,    setLastN]        = useState(-1);
  const [window,   setWindow]       = useState(20);
  const [period,   setPeriod]       = useState(20);
  const [mult,     setMult]         = useState(2);
  const [ratio,    setRatio]        = useState(0.5);
  const [stopLoss, setStopLoss]     = useState(0.05);
  const [takeProfit,setTakeProfit]  = useState(0.1);
  const [positionSize, setPositionSize] = useState(1.0);
  const [outDir,   setOutDir]       = useState('out');

  // 回测结果状态
  const [result,  setResult]        = useState(null);
  const [loading, setLoading]       = useState(false);

  const handleRun = async () => {
    setLoading(true);
    setResult(null);
    const payload = {
      mode:          'backtest',
      strategy, symbols, timeframe,
      limit:         Number(limit),
      last_n:        Number(lastN),
      window:        Number(window),
      period:        Number(period),
      mult:          Number(mult),
      ratio:         Number(ratio),
      stop_loss:     Number(stopLoss),
      take_profit:   Number(takeProfit),
      trailing_ma:   null,
      position_size: Number(positionSize),
      out_dir:       outDir,
    };
    try {
      const res = await runBacktest(payload);
      setResult(res);
    } catch (e) {
      console.error(e);
      alert('回测失败：' + (e.response?.data?.message || e.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-11/12 mx-auto space-y-8">
      <div className="w-11/12 mx-auto space-y-8">
        {/* 标题 */}
        <header className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-800">PythonTrade 回测面板</h1>
          <p className="mt-2 text-gray-600">配置参数，实时生成信号图和回测结果</p>
        </header>

        {/* 参数表单卡片 */}
        <section className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4">回测配置</h2>
          <div className="grid grid-cols-2 gap-6">
            <StrategySelector value={strategy} onChange={setStrategy} />
            <SymbolSelector   value={symbols}     onChange={setSymbols} />
            <ParameterInput label="Symbols"        value={symbols}      onChange={setSymbols} />
            <ParameterInput label="Timeframe"      value={timeframe}    onChange={setTimeframe} />
            <ParameterInput label="Limit"          type="number" value={limit}        onChange={setLimit} />
            <ParameterInput label="Last N"         type="number" value={lastN}        onChange={setLastN} />
            <ParameterInput label="Window"         type="number" value={window}       onChange={setWindow} />
            <ParameterInput label="Period"         type="number" value={period}       onChange={setPeriod} />
            <ParameterInput label="Mult"           type="number" value={mult}         onChange={setMult} />
            <ParameterInput label="Ratio"          type="number" step="0.01" value={ratio}        onChange={setRatio} />
            <ParameterInput label="Stop Loss"      type="number" step="0.01" value={stopLoss}     onChange={setStopLoss} />
            <ParameterInput label="Take Profit"    type="number" step="0.01" value={takeProfit}   onChange={setTakeProfit} />
            <ParameterInput label="Position Size"  type="number" step="0.1"  value={positionSize} onChange={setPositionSize} />
            <ParameterInput
              label="Out Dir"
              value={outDir}
              onChange={setOutDir}
              className="col-span-2"
            />
          </div>
          <div className="text-center mt-6">
            <button
              onClick={handleRun}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-indigo-600 hover:to-blue-600 text-white font-medium rounded-lg shadow-lg disabled:opacity-50 transition"
            >
              {loading ? '运行中…' : '运行回测'}
            </button>
          </div>
        </section>

        {/* 结果展示 */}
        {result && (
          <section className="space-y-8">
            <BacktestResult result={result} outDir={outDir} />
          </section>
        )}
      </div>
    </div>
  );
}
