import React from 'react';

const OPTIONS = [
  { value: 'bollinger_narrow', label: 'Bollinger 窄幅' },
  { value: 'ma15_breakout',    label: 'MA15 突破' },
  { value: 'follow_through',   label: 'Follow Through' },
];

export function StrategySelector({ value, onChange }) {
  return (
    <div>
      <label className="block mb-1">策略</label>
      <select
        className="w-full border rounded p-2"
        value={value}
        onChange={e => onChange(e.target.value)}
      >
        {OPTIONS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

