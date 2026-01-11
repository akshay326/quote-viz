import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { quoteApi, Quote } from '../api/client'

function Search() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedQuoteId, setSelectedQuoteId] = useState<string | null>(null)

  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => quoteApi.search(searchQuery, 50).then(res => res.data),
    enabled: searchQuery.length > 0,
  })

  const { data: similarQuotes, isLoading: similarLoading } = useQuery({
    queryKey: ['similar', selectedQuoteId],
    queryFn: () => quoteApi.similar(selectedQuoteId!, 100).then(res => res.data),
    enabled: !!selectedQuoteId,
  })

  // Get top 5 most similar and top 5 least similar
  const topSimilar = similarQuotes?.slice(0, 5) || []
  const leastSimilar = similarQuotes
    ?.slice()
    .reverse()
    .slice(0, 5) || []

  const handleQuoteSelect = (quoteId: string) => {
    setSelectedQuoteId(quoteId)
  }

  const selectedQuote = searchResults?.find(q => q.id === selectedQuoteId)

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem' }}>
        <nav style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
          <Link to="/">Home</Link>
          <Link to="/analytics">Analytics</Link>
          <Link to="/search">Search</Link>
        </nav>
        <h1>Quote Search</h1>
      </header>

      <main>
        <section style={{ marginBottom: '2rem' }}>
          <input
            type="text"
            placeholder="Search quotes by text, author, or context..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '1rem',
              fontSize: '1rem',
              background: '#333',
              border: '1px solid #555',
              borderRadius: '0.5rem',
              color: '#fff',
            }}
          />
        </section>

        {searchQuery && (
          <div style={{ display: 'grid', gridTemplateColumns: selectedQuoteId ? '1fr 1fr' : '1fr', gap: '2rem' }}>
            <section>
              <h2 style={{ marginBottom: '1rem' }}>
                Search Results {searchResults && `(${searchResults.length})`}
              </h2>
              {searchLoading ? (
                <p>Searching...</p>
              ) : searchResults && searchResults.length > 0 ? (
                <div style={{ display: 'grid', gap: '0.75rem', maxHeight: '600px', overflowY: 'auto' }}>
                  {searchResults.map((quote) => (
                    <div
                      key={quote.id}
                      onClick={() => handleQuoteSelect(quote.id)}
                      style={{
                        padding: '1rem',
                        background: selectedQuoteId === quote.id ? '#444' : '#333',
                        border: selectedQuoteId === quote.id ? '2px solid #3b82f6' : '1px solid #555',
                        borderRadius: '0.5rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      <p style={{ fontStyle: 'italic', marginBottom: '0.5rem' }}>
                        "{quote.text}"
                      </p>
                      <p style={{ fontSize: '0.85rem', color: '#888' }}>
                        — {quote.author.name}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#888' }}>No results found</p>
              )}
            </section>

            {selectedQuoteId && (
              <section>
                <h2 style={{ marginBottom: '1rem' }}>Similarity Analysis</h2>
                {similarLoading ? (
                  <p>Loading similarity data...</p>
                ) : (
                  <div>
                    <div style={{ marginBottom: '1rem', padding: '1rem', background: '#222', borderRadius: '0.5rem' }}>
                      <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Selected Quote</h3>
                      <p style={{ fontStyle: 'italic', marginBottom: '0.5rem' }}>
                        "{selectedQuote?.text}"
                      </p>
                      <p style={{ fontSize: '0.85rem', color: '#888' }}>
                        — {selectedQuote?.author.name}
                      </p>
                    </div>

                    <div style={{ marginBottom: '2rem' }}>
                      <h3 style={{ fontSize: '1.1rem', marginBottom: '0.75rem', color: '#4ade80' }}>
                        Top 5 Most Similar Quotes
                      </h3>
                      <div style={{ display: 'grid', gap: '0.5rem' }}>
                        {topSimilar.length > 0 ? (
                          topSimilar.map((quote) => (
                            <Link
                              key={quote.id}
                              to={`/quote/${quote.id}`}
                              style={{
                                display: 'block',
                                padding: '0.75rem',
                                background: '#2a4a2a',
                                border: '1px solid #4ade80',
                                borderRadius: '0.5rem',
                                textDecoration: 'none',
                                color: 'inherit',
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span style={{ fontSize: '0.85rem', color: '#4ade80', fontWeight: 'bold' }}>
                                  {quote.similarity_score ? `${(quote.similarity_score * 100).toFixed(1)}%` : 'N/A'}
                                </span>
                              </div>
                              <p style={{ fontStyle: 'italic', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                                "{quote.text}"
                              </p>
                              <p style={{ fontSize: '0.8rem', color: '#888' }}>
                                — {quote.author.name}
                              </p>
                            </Link>
                          ))
                        ) : (
                          <p style={{ color: '#888' }}>No similar quotes found</p>
                        )}
                      </div>
                    </div>

                    <div>
                      <h3 style={{ fontSize: '1.1rem', marginBottom: '0.75rem', color: '#f87171' }}>
                        Top 5 Least Similar Quotes
                      </h3>
                      <div style={{ display: 'grid', gap: '0.5rem' }}>
                        {leastSimilar.length > 0 ? (
                          leastSimilar.map((quote) => (
                            <Link
                              key={quote.id}
                              to={`/quote/${quote.id}`}
                              style={{
                                display: 'block',
                                padding: '0.75rem',
                                background: '#4a2a2a',
                                border: '1px solid #f87171',
                                borderRadius: '0.5rem',
                                textDecoration: 'none',
                                color: 'inherit',
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span style={{ fontSize: '0.85rem', color: '#f87171', fontWeight: 'bold' }}>
                                  {quote.similarity_score ? `${(quote.similarity_score * 100).toFixed(1)}%` : 'N/A'}
                                </span>
                              </div>
                              <p style={{ fontStyle: 'italic', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                                "{quote.text}"
                              </p>
                              <p style={{ fontSize: '0.8rem', color: '#888' }}>
                                — {quote.author.name}
                              </p>
                            </Link>
                          ))
                        ) : (
                          <p style={{ color: '#888' }}>No dissimilar quotes found</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default Search
