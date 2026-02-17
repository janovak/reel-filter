/**
 * API client service with axios configuration
 */
import axios, { AxiosInstance, AxiosError } from 'axios'

// Get API base URL from environment
const API_BASE_URL = ((import.meta as unknown) as { env: { VITE_API_BASE_URL: string } }).env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // User-friendly error messages
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          console.error('Bad Request:', data)
          break
        case 404:
          console.error('Not Found:', data)
          break
        case 500:
          console.error('Server Error:', data)
          break
        default:
          console.error('API Error:', data)
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error: Unable to connect to the server')
    } else {
      // Error in request setup
      console.error('Request Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
