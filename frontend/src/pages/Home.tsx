import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { graphApi } from '../api/client'
import { useMemo, useCallback, useRef, useEffect } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'
import SpriteText from 'three-spritetext'

// Generate consistent color from author name
function getAuthorColor(authorName: string): string {
  let hash = 0
  for (let i = 0; i < authorName.length; i++) {
    hash = authorName.charCodeAt(i) + ((hash << 5) - hash)
  }

  // Generate HSL color with good saturation and lightness
  const hue = Math.abs(hash % 360)
  const saturation = 65 + (Math.abs(hash) % 20) // 65-85%
  const lightness = 55 + (Math.abs(hash >> 8) % 15) // 55-70%

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`
}

interface ForceGraphNode {
  id: string
  name: string
  type: string
  x?: number
  y?: number
  z?: number
  val: number
  color: string
  text?: string
  image_url?: string
}

interface ForceGraphLink {
  source: string
  target: string
  value: number
  type: string
}

// Helper function to create fallback node with colored sphere and initials
function createFallbackNode(node: ForceGraphNode): THREE.Group {
  const group = new THREE.Group()

  // Colored sphere
  const geometry = new THREE.SphereGeometry(15, 32, 32)
  const material = new THREE.MeshBasicMaterial({ color: node.color })
  const sphere = new THREE.Mesh(geometry, material)
  group.add(sphere)

  // Initials overlay
  const initials = node.name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const sprite = new SpriteText(initials)
  sprite.color = 'white'
  sprite.textHeight = 8
  group.add(sprite)

  return group
}

// Helper function to create circular image texture from URL
function createCircularImageTexture(imageUrl: string): Promise<THREE.Texture> {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'

    img.onload = () => {
      // Create canvas for circular mask
      const size = 256
      const canvas = document.createElement('canvas')
      canvas.width = size
      canvas.height = size
      const ctx = canvas.getContext('2d')!

      // Draw circular clip path
      ctx.beginPath()
      ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2)
      ctx.closePath()
      ctx.clip()

      // Draw image centered and scaled
      const aspectRatio = img.width / img.height
      let drawWidth = size
      let drawHeight = size
      let offsetX = 0
      let offsetY = 0

      if (aspectRatio > 1) {
        drawWidth = size * aspectRatio
        offsetX = -(drawWidth - size) / 2
      } else {
        drawHeight = size / aspectRatio
        offsetY = -(drawHeight - size) / 2
      }

      ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)

      // Create texture from canvas
      const texture = new THREE.CanvasTexture(canvas)
      texture.needsUpdate = true
      resolve(texture)
    }

    img.onerror = () => {
      // Return a blank texture on error
      const canvas = document.createElement('canvas')
      canvas.width = 256
      canvas.height = 256
      const texture = new THREE.CanvasTexture(canvas)
      resolve(texture)
    }

    img.src = imageUrl
  })
}

// Helper function to create author node with image
function createAuthorNode(node: ForceGraphNode): THREE.Object3D {
  // Check if we have a real image URL (starts with http)
  if (node.image_url && node.image_url.startsWith('http')) {
    // Create a group to hold the sprite
    const group = new THREE.Group()

    // Create sprite with placeholder first
    const spriteMaterial = new THREE.SpriteMaterial({
      color: 0xcccccc,
      sizeAttenuation: true,
    })
    const sprite = new THREE.Sprite(spriteMaterial)
    sprite.scale.set(35, 35, 1)
    group.add(sprite)

    // Load circular image asynchronously
    createCircularImageTexture(node.image_url).then((texture) => {
      spriteMaterial.map = texture
      spriteMaterial.color.setHex(0xffffff) // Remove gray tint
      spriteMaterial.needsUpdate = true
      console.log(`✓ Loaded circular image for ${node.name}`)
    }).catch(() => {
      console.warn(`✗ Failed to load image for ${node.name}`)
    })

    return group
  }

  // For data URLs (SVG) or no image, use fallback
  return createFallbackNode(node)
}

function Home() {
  const navigate = useNavigate()
  const graphRef = useRef<any>()

  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ['graph'],
    queryFn: () => graphApi.get().then(res => res.data),
  })

  // Transform graph data for react-force-graph
  const forceGraphData = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] }

    const nodes: ForceGraphNode[] = graphData.nodes.map(node => {
      const isQuote = node.type === 'quote'
      const hasUMAP = node.data.umap_x !== null && node.data.umap_x !== undefined &&
                      node.data.umap_y !== null && node.data.umap_y !== undefined

      // Use cluster_id for Z-axis positioning (multiply by 200 for spacing)
      const clusterId = node.data.cluster_id
      const zPosition = (clusterId !== null && clusterId !== undefined) ? clusterId * 200 : 0

      // Determine author name for color
      const authorName = isQuote ? (node.data.author || 'Unknown') : node.label

      return {
        id: node.id,
        name: authorName,
        type: node.type,
        x: hasUMAP ? (node.data.umap_x - 0.5) * 1000 : undefined,
        y: hasUMAP ? (node.data.umap_y - 0.5) * 1000 : undefined,
        z: zPosition,
        val: isQuote ? 8 : 12,
        color: getAuthorColor(authorName),
        text: isQuote ? node.data.text : undefined,
        image_url: !isQuote ? node.data.image_url : undefined
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
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <header style={{ padding: '1.5rem 2rem', borderBottom: '1px solid #444' }}>
        <nav style={{ display: 'flex', gap: '1rem' }}>
          <Link to="/">Home</Link>
          <Link to="/analytics">Analytics</Link>
          <Link to="/search">Search</Link>
        </nav>
      </header>

      <main style={{ flex: 1, overflow: 'hidden', background: '#0a0a0a' }}>
        {graphLoading ? (
          <div style={{ padding: '2rem', color: '#888' }}>Loading graph...</div>
        ) : forceGraphData.nodes.length > 0 ? (
          <ForceGraph3D
            ref={graphRef}
            graphData={forceGraphData}
            nodeLabel={(node: any) => {
              const n = node as ForceGraphNode
              if (n.type === 'quote' && n.text) {
                return `${n.text.slice(0, 100)}${n.text.length > 100 ? '...' : ''}`
              }
              return n.name
            }}
            nodeThreeObject={(node: any) => {
              const n = node as ForceGraphNode
              if (n.type === 'person') {
                return createAuthorNode(n)
              } else {
                const geometry = new THREE.SphereGeometry(8, 16, 16)
                const material = new THREE.MeshBasicMaterial({ color: n.color })
                return new THREE.Mesh(geometry, material)
              }
            }}
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
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
            warmupTicks={100}
            cooldownTicks={0}
            enableNodeDrag={true}
            enableNavigationControls={true}
          />
        ) : (
          <div style={{ padding: '2rem', color: '#888' }}>No graph data available.</div>
        )}
      </main>
    </div>
  )
}

export default Home
