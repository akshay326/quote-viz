import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import QuoteDetails from './pages/QuoteDetails'
import Analytics from './pages/Analytics'
import Search from './pages/Search'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quote/:id" element={<QuoteDetails />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
