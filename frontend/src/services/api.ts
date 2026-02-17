/**
 * API client service with axios configuration and user-friendly error messages
 */
import axios, { AxiosInstance, AxiosError } from 'axios'

// Get API base URL from environment
const API_BASE_URL = ((import.meta as unknown) as { env: { VITE_API_BASE_URL: string } }).env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// User-friendly error messages by status code
const ERROR_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your search criteria and try again.',
  404: 'The requested resource was not found.',
  408: 'The request timed out. Please try again.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'Something went wrong on our end. Please try again later.',
  502: 'The service is temporarily unavailable. Please try again later.',
  503: 'The service is currently down for maintenance. Please try again later.',
}

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
    if (error.response) {
      const { status, data } = error.response
      const userMessage = ERROR_MESSAGES[status] || 'An unexpected error occurred. Please try again.'

      // Attach user-friendly message to the error
      const enhancedError = error as AxiosError & { userMessage: string }
      enhancedError.userMessage = userMessage

      // Log details for debugging
      console.error(`API Error [${status}]:`, data)
    } else if (error.request) {
      // Network error - no response received
      const enhancedError = error as AxiosError & { userMessage: string }
      enhancedError.userMessage = 'Unable to connect to the server. Please check your internet connection.'
      console.error('Network Error: Unable to connect to the server')
    } else {
      const enhancedError = error as AxiosError & { userMessage: string }
      enhancedError.userMessage = 'An unexpected error occurred.'
      console.error('Request Error:', error.message)
    }

    return Promise.reject(error)
  }
)

/**
 * Get a user-friendly error message from an API error
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const enhanced = error as AxiosError & { userMessage?: string }
    return enhanced.userMessage || 'An unexpected error occurred.'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred.'
}

export default apiClient
