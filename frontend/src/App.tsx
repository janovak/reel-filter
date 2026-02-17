import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import MovieDetail from './pages/MovieDetail'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Main search page */}
          <Route path="/" element={<SearchPage />} />
          <Route path="/search" element={<SearchPage />} />
          
          {/* Movie detail page */}
          <Route path="/movies/:id" element={<MovieDetail />} />
          
          {/* Redirect unknown routes to search */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
