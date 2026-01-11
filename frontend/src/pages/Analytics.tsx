import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { analyticsApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

function Analytics() {
  const queryClient = useQueryClient()

  const { data: stats, isLoading } = useQuery({
    queryKey: ['analytics-stats'],
    queryFn: () => analyticsApi.stats().then(res => res.data),
  })

  const recomputeMutation = useMutation({
    mutationFn: () => analyticsApi.recomputeSimilarities().then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics-stats'] })
      queryClient.invalidateQueries({ queryKey: ['quotes'] })
      queryClient.invalidateQueries({ queryKey: ['graph'] })
    },
  })

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem' }}>
        <nav style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
          <Link to="/">Home</Link>
          <Link to="/analytics">Analytics</Link>
          <Link to="/search">Search</Link>
        </nav>
        <h1>Analytics</h1>
      </header>

      {isLoading ? (
        <p>Loading statistics...</p>
      ) : (
        <div>
          <section style={{ marginBottom: '3rem' }}>
            <h2 style={{ marginBottom: '1rem' }}>Overview</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1.5rem', background: '#333', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{stats?.total_quotes || 0}</div>
                <div style={{ color: '#888' }}>Total Quotes</div>
              </div>
              <div style={{ padding: '1.5rem', background: '#333', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{stats?.total_people || 0}</div>
                <div style={{ color: '#888' }}>People</div>
              </div>
              <div style={{ padding: '1.5rem', background: '#333', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                  {stats?.avg_quotes_per_person?.toFixed(1) || 0}
                </div>
                <div style={{ color: '#888' }}>Avg Quotes/Person</div>
              </div>
              <div style={{ padding: '1.5rem', background: '#333', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{stats?.total_clusters || 0}</div>
                <div style={{ color: '#888' }}>Total Clusters</div>
              </div>
              <div style={{ padding: '1.5rem', background: '#333', borderRadius: '0.5rem' }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                  {stats?.avg_cluster_size?.toFixed(1) || 0}
                </div>
                <div style={{ color: '#888' }}>Avg Cluster Size</div>
              </div>
            </div>
          </section>

          <section style={{ marginBottom: '3rem' }}>
            <h2 style={{ marginBottom: '1rem' }}>Top People</h2>
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {stats?.top_people?.map((person: any) => (
                <div
                  key={person.name}
                  style={{
                    padding: '1rem',
                    background: '#333',
                    borderRadius: '0.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{person.name}</span>
                  <span style={{ color: '#888' }}>{person.quote_count} quotes</span>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginBottom: '3rem' }}>
            <h2 style={{ marginBottom: '1rem' }}>Cluster Distribution</h2>
            {stats?.cluster_distribution && stats.cluster_distribution.length > 0 ? (
              <div style={{ background: '#333', padding: '1.5rem', borderRadius: '0.5rem' }}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.cluster_distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                    <XAxis
                      dataKey="cluster_id"
                      stroke="#888"
                      label={{ value: 'Cluster ID', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis stroke="#888" />
                    <Tooltip
                      contentStyle={{ background: '#222', border: '1px solid #555' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Legend />
                    <Bar dataKey="quote_count" fill="#3b82f6" name="Quote Count" />
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '0.5rem' }}>
                  {stats.cluster_distribution.map((cluster: any) => (
                    <div
                      key={cluster.cluster_id}
                      style={{
                        padding: '0.75rem',
                        background: '#222',
                        borderRadius: '0.25rem',
                        fontSize: '0.9rem',
                      }}
                    >
                      <div style={{ fontWeight: 'bold' }}>Cluster {cluster.cluster_id}</div>
                      <div style={{ color: '#888', marginTop: '0.25rem' }}>
                        {cluster.quote_count} quotes • {(cluster.avg_similarity * 100).toFixed(1)}% avg similarity
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p style={{ color: '#888' }}>No cluster data available</p>
            )}
          </section>

          <section>
            <h2 style={{ marginBottom: '1rem' }}>Actions</h2>
            <button
              onClick={() => recomputeMutation.mutate()}
              disabled={recomputeMutation.isPending}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#646cff',
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: recomputeMutation.isPending ? 'not-allowed' : 'pointer',
                opacity: recomputeMutation.isPending ? 0.6 : 1,
              }}
            >
              {recomputeMutation.isPending ? 'Computing...' : 'Recompute Similarities'}
            </button>
            {recomputeMutation.isSuccess && (
              <p style={{ marginTop: '1rem', color: '#4ade80' }}>
                Similarities recomputed successfully!
              </p>
            )}
          </section>
        </div>
      )}
    </div>
  )
}

export default Analytics
