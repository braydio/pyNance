
// src/api/teller.js
import axios from 'axios'

export const saveTellerToken = async (data) => {
  const response = await axios.post('/api/link/teller/save_token', data)
  return response.data
}
