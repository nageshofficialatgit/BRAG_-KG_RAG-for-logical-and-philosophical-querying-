import React, { useEffect, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import './GraphVisualization.css'

function GraphVisualization({ graphData }) {
  const graphRef = useRef()

  useEffect(() => {
    if (graphRef.current && graphData.nodes.length > 0) {
      graphRef.current.zoomToFit(400, 20)
    }
  }, [graphData])

  const handleNodeClick = (node) => {
    console.log('Node clicked:', node)
  }

  const handleNodeHover = (node, prevNode) => {
    if (node) {
      document.body.style.cursor = 'pointer'
    } else {
      document.body.style.cursor = 'default'
    }
  }

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <h2>Knowledge Graph</h2>
        <div className="graph-stats">
          {graphData.nodes.length > 0 && (
            <span>{graphData.nodes.length} nodes, {graphData.edges.length} relationships</span>
          )}
        </div>
      </div>
      
      <div className="graph-container">
        {graphData.nodes.length === 0 ? (
          <div className="empty-graph">
            <p>No graph data yet. Ask a question or add reference text to see the knowledge graph.</p>
          </div>
        ) : (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeLabel={(node) => node.label || node.id}
            nodeColor={(node) => {
              // Color nodes based on type or random
              const colors = ['#4a90e2', '#50c878', '#e24a4a', '#e2a04a', '#9b4ae2']
              const hash = node.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
              return colors[hash % colors.length]
            }}
            nodeVal={(node) => {
              // Node size based on connections
              const connections = graphData.edges.filter(
                e => e.source === node.id || e.target === node.id
              ).length
              return Math.max(5, Math.min(15, 5 + connections * 2))
            }}
            linkLabel={(link) => link.relationship || 'related'}
            linkColor={() => '#666'}
            linkWidth={2}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            backgroundColor="#0a0a1a"
            nodeCanvasObjectMode={() => 'after'}
            nodeCanvasObject={(node, ctx) => {
              const label = node.label || node.id
              const fontSize = 10
              ctx.font = `${fontSize}px Sans-Serif`
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = '#e0e0e0'
              ctx.fillText(label, node.x, node.y + 20)
            }}
          />
        )}
      </div>
    </div>
  )
}

export default GraphVisualization
