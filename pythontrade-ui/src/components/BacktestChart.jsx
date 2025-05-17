// src/components/BacktestChart.jsx
import React from "react";
import * as UPlotModule from "react-uplot";
import "uplot/dist/uPlot.min.css";

const UplotReact = UPlotModule.default || UPlotModule;

export function BacktestChart({ data }) {
  const opts = {
    width: 800,
    height: 400,
    series: [
      {},               // x 轴（时间戳）
      { label: "价格" }, // 第一个数据序列
      // 如果有更多序列，可以继续添加
    ],
    axes: [{}, {}],
  };
  // data 格式： [ timestampsArray, series1Array, series2Array, … ]
  return <UplotReact options={opts} data={data} />;
}
