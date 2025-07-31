/**
 * Arbitrage monitoring API helpers.
 */
import axios from 'axios'

export const fetchArbitrageData = async () => {
  const response = await axios.get('/api/arbitrage/current')
  return response.data
}
