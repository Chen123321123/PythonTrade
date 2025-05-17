import React from 'react';

export function ParameterInput({ label, value, onChange, type = 'text', step }) {
  return (
    <div>
      <label className="block mb-1">{label}</label>
      <input
        type={type}
        step={step}
        className="w-full border rounded p-2"
        value={value}
        onChange={e => onChange(e.target.value)}
      />
    </div>
  );
}
