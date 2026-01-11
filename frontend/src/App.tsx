import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import QuoteDetails from './pages/QuoteDetails'
import Analytics from './pages/Analytics'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quote/:id" element={<QuoteDetails />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
