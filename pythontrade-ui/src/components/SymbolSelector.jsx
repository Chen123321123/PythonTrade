// src/components/SymbolSelector.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { fetchSymbols } from '../api';   // 根据你的路径调整一下

export function SymbolSelector({ value, onChange }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);

useEffect(() => {
  setLoading(true)
  fetchSymbols()
    .then(list => {
      console.log('拿到 symbols 列表：', list)
      setOptions(list)
    })
    .catch(err => {
      console.error('获取 symbols 失败', err)
      setOptions([])
    })
    .finally(() => setLoading(false))
}, [])


  if (loading) {
    return <div>加载币种列表中…</div>;
  }

  return (
    <div>
      <label className="block mb-1">Symbols</label>
      <select
        className="w-full border rounded p-2"
        value={value}
        onChange={e => onChange(e.target.value)}
      >
        {options.map(sym => (
          <option key={sym} value={sym}>{sym}</option>
        ))}
      </select>
    </div>
  );
}
