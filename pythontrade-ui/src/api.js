// src/api.js
import axios from 'axios';

/**
 * 调用后端回测接口
 * @param {Object} params - 回测参数，示例结构：
 * {
 *   mode:          'backtest',
 *   symbols:       'BTC/USD',      // Kraken 支持的格式
 *   timeframe:     '4h',
 *   limit:         300,
 *   last_n:        -1,
 *   strategy:      'bollinger_narrow',
 *   window:        20,
 *   period:        20,
 *   mult:          2,
 *   ratio:         0.5,
 *   stop_loss:     0.05,
 *   take_profit:   0.10,
 *   trailing_ma:   null,
 *   position_size: 1.0,
 *   out_dir:       'out'
 * }
 * @returns {Promise<Object>} 返回后端 JSON：
 *   { run_id: string, out_dir: string, results: { [symbol]: { signals, backtest, performance, … } } }
 */
export function runBacktest(params) {
  return axios
    .post('http://localhost:5000/run', params)
    .then(res => res.data)
    .catch(err => {
      console.error('回测接口调用失败：', err);
      throw err;
    });
}
