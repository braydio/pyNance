/**
 * Arbit dashboard API helpers.
 */
import axios from 'axios'

export const fetchArbitStatus = async () => {
  const response = await axios.get('/api/arbit/status')
  return response.data
}
