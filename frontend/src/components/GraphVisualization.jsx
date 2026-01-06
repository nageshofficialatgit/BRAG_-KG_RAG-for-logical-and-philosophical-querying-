import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import './GraphVisualization.css'

function GraphVisualization({ graphData }) {
  const canvasRef = useRef(null)
  const nodesRef = useRef([])
  const edgesRef = useRef([])
  const hoveredRef = useRef({ nodeId: null, edgeId: null })
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: '' })

  // Simple canvas-based graph visualization
  // Helper: compute layout and render. Stored nodes/edges in refs for interactivity.
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    // Set canvas size
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    // Layout: circle placement for stability
    const padding = 50
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    const maxRadius = Math.min(canvas.width, canvas.height) / 2 - padding

    const nodes = graphData.nodes.map((node, index) => ({
      ...node,
      x: centerX + maxRadius * Math.cos((index / Math.max(1, graphData.nodes.length)) * Math.PI * 2),
      y: centerY + maxRadius * Math.sin((index / Math.max(1, graphData.nodes.length)) * Math.PI * 2),
      radius: 20
    }))

    const edges = graphData.edges.map(e => ({ ...e }))

    nodesRef.current = nodes
    edgesRef.current = edges

    const draw = (hoverNodeId = null, hoverEdgeId = null) => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = 'rgba(255,255,255,1)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Draw edges
      edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.source)
        const target = nodes.find(n => n.id === edge.target)
        if (!source || !target) return

        const isHover = hoverEdgeId === edge.id
        ctx.strokeStyle = isHover ? '#2563eb' : '#d0d0d0'
        ctx.lineWidth = isHover ? 3 : 2
        ctx.beginPath()
        ctx.moveTo(source.x, source.y)
        ctx.lineTo(target.x, target.y)
        ctx.stroke()

        // Arrow
        const angle = Math.atan2(target.y - source.y, target.x - source.x)
        const arrowSize = isHover ? 10 : 8
        ctx.fillStyle = isHover ? '#2563eb' : '#999999'
        ctx.beginPath()
        ctx.moveTo(target.x, target.y)
        ctx.lineTo(target.x - arrowSize * Math.cos(angle - Math.PI / 6), target.y - arrowSize * Math.sin(angle - Math.PI / 6))
        ctx.lineTo(target.x - arrowSize * Math.cos(angle + Math.PI / 6), target.y - arrowSize * Math.sin(angle + Math.PI / 6))
        ctx.fill()
      })

      // Draw nodes
      nodes.forEach((node, index) => {
        const isHover = hoverNodeId === node.id
        const colors = ['#2563eb', '#059669', '#dc2626', '#ea580c', '#7c3aed']
        const color = colors[index % colors.length]

        ctx.beginPath()
        ctx.fillStyle = color
        const r = isHover ? node.radius + 6 : node.radius
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2)
        ctx.fill()

        ctx.strokeStyle = isHover ? '#000' : 'white'
        ctx.lineWidth = isHover ? 3 : 2
        ctx.stroke()

        ctx.fillStyle = 'white'
        ctx.font = 'bold 11px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        const label = node.label || node.id
        const shortLabel = label.length > 15 ? label.substring(0, 12) + '...' : label
        ctx.fillText(shortLabel, node.x, node.y)
      })
    }

    // initial draw
    draw(hoveredRef.current.nodeId, hoveredRef.current.edgeId)

  }, [graphData])

  // Event handlers for hover interactivity
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const getMousePos = (e) => {
      const rect = canvas.getBoundingClientRect()
      return { x: e.clientX - rect.left, y: e.clientY - rect.top }
    }

    const distanceToSegment = (px, py, x1, y1, x2, y2) => {
      const A = px - x1
      const B = py - y1
      const C = x2 - x1
      const D = y2 - y1
      const dot = A * C + B * D
      const lenSq = C * C + D * D
      let param = -1
      if (lenSq !== 0) param = dot / lenSq
      let xx, yy
      if (param < 0) {
        xx = x1
        yy = y1
      } else if (param > 1) {
        xx = x2
        yy = y2
      } else {
        xx = x1 + param * C
        yy = y1 + param * D
      }
      const dx = px - xx
      const dy = py - yy
      return Math.sqrt(dx * dx + dy * dy)
    }

    const onMove = (e) => {
      const pos = getMousePos(e)
      const nodes = nodesRef.current || []
      const edges = edgesRef.current || []
      let foundNode = null
      let foundEdge = null

      // check nodes first
      for (const n of nodes) {
        const d = Math.hypot(pos.x - n.x, pos.y - n.y)
        if (d <= n.radius + 6) {
          foundNode = n
          break
        }
      }

      if (!foundNode) {
        // check edges
        for (const eObj of edges) {
          const s = nodes.find(nn => nn.id === eObj.source)
          const t = nodes.find(nn => nn.id === eObj.target)
          if (!s || !t) continue
          const dist = distanceToSegment(pos.x, pos.y, s.x, s.y, t.x, t.y)
          if (dist <= 6) {
            foundEdge = eObj
            break
          }
        }
      }

      // Update tooltip and hovered refs
      const canvasRect = canvas.getBoundingClientRect()
      if (foundNode) {
        hoveredRef.current = { nodeId: foundNode.id, edgeId: null }
        const content = `${foundNode.label || foundNode.id}${foundNode.type ? ' — ' + foundNode.type : ''}`
        setTooltip({ visible: true, x: canvasRect.left + foundNode.x + 12, y: canvasRect.top + foundNode.y - 12, content })
      } else if (foundEdge) {
        hoveredRef.current = { nodeId: null, edgeId: foundEdge.id }
        const content = `${foundEdge.type || foundEdge.label || foundEdge.relation || 'edge'}`
        // position midpoint
        const s = nodesRef.current.find(nn => nn.id === foundEdge.source)
        const t = nodesRef.current.find(nn => nn.id === foundEdge.target)
        const mx = s && t ? (s.x + t.x) / 2 : pos.x
        const my = s && t ? (s.y + t.y) / 2 : pos.y
        setTooltip({ visible: true, x: canvasRect.left + mx + 12, y: canvasRect.top + my - 12, content })
      } else {
        hoveredRef.current = { nodeId: null, edgeId: null }
        setTooltip({ visible: false, x: 0, y: 0, content: '' })
      }

      // redraw with highlights
      const ctx = canvas.getContext('2d')
      const drawNow = () => {
        // mimic the draw routine used earlier but only using refs
        const nodes = nodesRef.current || []
        const edges = edgesRef.current || []
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.fillStyle = 'rgba(255,255,255,1)'
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        edges.forEach(edge => {
          const source = nodes.find(n => n.id === edge.source)
          const target = nodes.find(n => n.id === edge.target)
          if (!source || !target) return
          const isHover = hoveredRef.current.edgeId === edge.id
          ctx.strokeStyle = isHover ? '#2563eb' : '#d0d0d0'
          ctx.lineWidth = isHover ? 3 : 2
          ctx.beginPath()
          ctx.moveTo(source.x, source.y)
          ctx.lineTo(target.x, target.y)
          ctx.stroke()
          const angle = Math.atan2(target.y - source.y, target.x - source.x)
          const arrowSize = isHover ? 10 : 8
          ctx.fillStyle = isHover ? '#2563eb' : '#999999'
          ctx.beginPath()
          ctx.moveTo(target.x, target.y)
          ctx.lineTo(target.x - arrowSize * Math.cos(angle - Math.PI / 6), target.y - arrowSize * Math.sin(angle - Math.PI / 6))
          ctx.lineTo(target.x - arrowSize * Math.cos(angle + Math.PI / 6), target.y - arrowSize * Math.sin(angle + Math.PI / 6))
          ctx.fill()
        })

        nodes.forEach((node, index) => {
          const isHover = hoveredRef.current.nodeId === node.id
          const colors = ['#2563eb', '#059669', '#dc2626', '#ea580c', '#7c3aed']
          const color = colors[index % colors.length]
          ctx.beginPath()
          ctx.fillStyle = color
          const r = isHover ? node.radius + 6 : node.radius
          ctx.arc(node.x, node.y, r, 0, Math.PI * 2)
          ctx.fill()
          ctx.strokeStyle = isHover ? '#000' : 'white'
          ctx.lineWidth = isHover ? 3 : 2
          ctx.stroke()
          ctx.fillStyle = 'white'
          ctx.font = 'bold 11px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          const label = node.label || node.id
          const shortLabel = label.length > 15 ? label.substring(0, 12) + '...' : label
          ctx.fillText(shortLabel, node.x, node.y)
        })
      }

      drawNow()
    }

    const onOut = () => {
      hoveredRef.current = { nodeId: null, edgeId: null }
      setTooltip({ visible: false, x: 0, y: 0, content: '' })
      // redraw to remove highlights
      const ctx = canvas.getContext('2d')
      const nodes = nodesRef.current || []
      const edges = edgesRef.current || []
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = 'rgba(255,255,255,1)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.source)
        const target = nodes.find(n => n.id === edge.target)
        if (!source || !target) return
        ctx.strokeStyle = '#d0d0d0'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(source.x, source.y)
        ctx.lineTo(target.x, target.y)
        ctx.stroke()
      })
      nodes.forEach((node, index) => {
        const colors = ['#2563eb', '#059669', '#dc2626', '#ea580c', '#7c3aed']
        const color = colors[index % colors.length]
        ctx.beginPath()
        ctx.fillStyle = color
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = 'white'
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.fillStyle = 'white'
        ctx.font = 'bold 11px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        const label = node.label || node.id
        const shortLabel = label.length > 15 ? label.substring(0, 12) + '...' : label
        ctx.fillText(shortLabel, node.x, node.y)
      })
    }

    canvas.addEventListener('mousemove', onMove)
    canvas.addEventListener('mouseleave', onOut)
    return () => {
      canvas.removeEventListener('mousemove', onMove)
      canvas.removeEventListener('mouseleave', onOut)
    }
  }, [canvasRef.current])

  const getNodeCount = () => graphData.nodes.length
  const getEdgeCount = () => graphData.edges.length

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <h2>╔─ Knowledge Graph ─╗</h2>
        <div className="graph-stats">
          {getNodeCount() > 0 && (
            <span>{getNodeCount()} nodes • {getEdgeCount()} edges</span>
          )}
        </div>
      </div>
      
      <div className="graph-container">
        {getNodeCount() === 0 ? (
          <motion.div 
            className="empty-graph"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <p>
             ╔════════════════════════════════════════════╗
            ║   No graph data yet.                      ║
            ║   Ask a question or add reference text    ║
            ║   to see the knowledge graph.             ║
            ╚════════════════════════════════════════════╝
            </p>
          </motion.div>
        ) : (
          <motion.canvas
            ref={canvasRef}
            className="graph-canvas"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          />
        )}
        {tooltip.visible && (
          <div
            className="gv-tooltip"
            style={{ left: tooltip.x + 'px', top: tooltip.y + 'px' }}
            role="status"
            aria-hidden={!tooltip.visible}
          >
            {tooltip.content}
          </div>
        )}
      </div>
    </div>
  )
}

export default GraphVisualization
