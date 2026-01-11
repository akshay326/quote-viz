import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { graphApi, quoteApi } from '../api/client'
import { useMemo, useCallback, useRef, useEffect } from 'react'
import ForceGraph from 'react-force-graph-2d'

interface ForceGraphNode {
  id: string
  name: string
  type: string
  x?: number
  y?: number
  val: number
  color: string
  text?: string
}

interface ForceGraphLink {
  source: string
  target: string
  value: number
  type: string
}

function Home() {
  const navigate = useNavigate()
  const graphRef = useRef<any>()

  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ['graph'],
    queryFn: () => graphApi.get().then(res => res.data),
  })

  const { data: quotes } = useQuery({
    queryKey: ['quotes'],
    queryFn: () => quoteApi.list({ limit: 20 }).then(res => res.data),
  })

  // Transform graph data for react-force-graph
  const forceGraphData = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] }

    const nodes: ForceGraphNode[] = graphData.nodes.map(node => {
      const isQuote = node.type === 'quote'
      const hasUMAP = node.data.umap_x !== null && node.data.umap_x !== undefined &&
                      node.data.umap_y !== null && node.data.umap_y !== undefined

      return {
        id: node.id,
        name: isQuote ? node.data.author || 'Unknown' : node.label,
        type: node.type,
        x: hasUMAP ? (node.data.umap_x - 0.5) * 1000 : undefined,
        y: hasUMAP ? (node.data.umap_y - 0.5) * 1000 : undefined,
        val: isQuote ? 8 : 12,
        color: isQuote ? '#3b82f6' : '#f97316',
        text: isQuote ? node.data.text : undefined
      }
    })

    const links: ForceGraphLink[] = graphData.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      value: edge.weight || 1,
      type: edge.type
    }))

    return { nodes, links }
  }, [graphData])

  // Handle node click
  const handleNodeClick = useCallback((node: ForceGraphNode) => {
    if (node.type === 'quote') {
      navigate(`/quote/${node.id}`)
    }
  }, [navigate])

  // Center graph on mount
  useEffect(() => {
    if (graphRef.current && forceGraphData.nodes.length > 0) {
      graphRef.current.zoomToFit(400, 100)
    }
  }, [forceGraphData])

  return (
    <div style={{ padding: '2rem' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1>Quote Visualization</h1>
        <nav style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
          <Link to="/">Home</Link>
          <Link to="/analytics">Analytics</Link>
        </nav>
      </header>

      <main>
        <section style={{ marginBottom: '2rem', border: '1px solid #444', borderRadius: '0.5rem' }}>
          <h2 style={{ padding: '1rem', margin: 0, borderBottom: '1px solid #444' }}>
            Quote Similarity Graph
          </h2>
          {graphLoading ? (
            <div style={{ padding: '1rem' }}>Loading graph...</div>
          ) : forceGraphData.nodes.length > 0 ? (
            <div>
              <div style={{ padding: '1rem', background: '#1a1a1a' }}>
                <div style={{ marginBottom: '0.5rem', color: '#4ade80' }}>
                  ✓ Visualization ready
                </div>
                <div style={{ fontSize: '0.9rem', color: '#888', marginBottom: '0.5rem' }}>
                  {graphData && `${graphData.nodes.length} nodes • ${graphData.edges.length} connections`}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#666' }}>
                  <span style={{ color: '#3b82f6' }}>●</span> Quotes •
                  <span style={{ color: '#f97316' }}> ●</span> Authors •
                  Click quote to view details
                </div>
              </div>
              <div style={{ height: '600px', background: '#0a0a0a', borderBottomLeftRadius: '0.5rem', borderBottomRightRadius: '0.5rem' }}>
                <ForceGraph
                  ref={graphRef}
                  graphData={forceGraphData}
                  nodeLabel={(node: any) => {
                    const n = node as ForceGraphNode
                    if (n.type === 'quote' && n.text) {
                      return `${n.text.slice(0, 100)}${n.text.length > 100 ? '...' : ''}`
                    }
                    return n.name
                  }}
                  nodeColor={(node: any) => (node as ForceGraphNode).color}
                  nodeVal={(node: any) => (node as ForceGraphNode).val}
                  linkColor={(link: any) => {
                    const l = link as ForceGraphLink
                    return l.type === 'similar_to' ? '#666' : '#333'
                  }}
                  linkWidth={(link: any) => {
                    const l = link as ForceGraphLink
                    return l.type === 'similar_to' ? l.value * 2 : 1
                  }}
                  linkDirectionalParticles={(link: any) => {
                    const l = link as ForceGraphLink
                    return l.type === 'similar_to' ? 2 : 0
                  }}
                  linkDirectionalParticleWidth={2}
                  onNodeClick={handleNodeClick}
                  dagMode={null}
                  d3AlphaDecay={0.02}
                  d3VelocityDecay={0.3}
                  warmupTicks={100}
                  cooldownTicks={0}
                  enableNodeDrag={true}
                  enableZoomInteraction={true}
                  enablePanInteraction={true}
                />
              </div>
            </div>
          ) : (
            <div style={{ padding: '1rem' }}>No graph data available. Run migration first.</div>
          )}
        </section>

        <section>
          <h2>Recent Quotes</h2>
          <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
            {quotes?.map((quote) => (
              <Link
                key={quote.id}
                to={`/quote/${quote.id}`}
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
                  "{quote.text}"
                </p>
                <p style={{ fontSize: '0.9rem', color: '#888' }}>
                  — {quote.author.name}
                </p>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default Home
