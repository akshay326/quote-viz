import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { quoteApi } from '../api/client'

function QuoteDetails() {
  const { id } = useParams<{ id: string }>()

  const { data: quote, isLoading } = useQuery({
    queryKey: ['quote', id],
    queryFn: () => quoteApi.get(id!).then(res => res.data),
    enabled: !!id,
  })

  if (isLoading) return <div style={{ padding: '2rem' }}>Loading...</div>

  if (!quote) return <div style={{ padding: '2rem' }}>Quote not found</div>

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <Link to="/" style={{ display: 'inline-block', marginBottom: '2rem' }}>
        ← Back to Home
      </Link>

      <article style={{ marginBottom: '3rem' }}>
        <blockquote style={{
          fontSize: '1.5rem',
          fontStyle: 'italic',
          marginBottom: '1rem',
          padding: '1rem',
          borderLeft: '4px solid #646cff'
        }}>
          "{quote.text}"
        </blockquote>

        <div style={{ fontSize: '1.1rem', color: '#888', marginBottom: '0.5rem' }}>
          — {quote.author.name}
        </div>

        {quote.context && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#333', borderRadius: '0.5rem' }}>
            <strong>Context:</strong> {quote.context}
          </div>
        )}

        {quote.cluster_id !== null && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#888' }}>
            Cluster: {quote.cluster_id}
          </div>
        )}
      </article>

      {quote.similar_quotes && quote.similar_quotes.length > 0 && (
        <section>
          <h2 style={{ marginBottom: '1rem' }}>Similar Quotes</h2>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {quote.similar_quotes.map((similar) => (
              <Link
                key={similar.id}
                to={`/quote/${similar.id}`}
                style={{
                  display: 'block',
                  padding: '1rem',
                  border: '1px solid #444',
                  borderRadius: '0.5rem',
                  textDecoration: 'none',
                  color: 'inherit',
                }}
              >
                <p style={{ fontStyle: 'italic', marginBottom: '0.5rem' }}>
                  "{similar.text}"
                </p>
                <p style={{ fontSize: '0.9rem', color: '#888' }}>
                  — {similar.author.name}
                  {similar.similarity_score && (
                    <span> • Similarity: {(similar.similarity_score * 100).toFixed(1)}%</span>
                  )}
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

export default QuoteDetails
