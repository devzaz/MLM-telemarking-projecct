// static/mlm/js/tree_d3.js
// Resilient D3 v7 tree renderer with nodeSize spacing + dynamic viewBox + zoom + resize
// Place this file at: static/mlm/js/tree_d3.js
// Requires:
//  - window.MLM_TREE_CONFIG.apiSubtreeUrlTemplate (template with {node_id})
//  - window.MLM_INIT_NODE (user view) or window.MLM_INIT_ADMIN_NODE (admin view)
//  - d3 v7 loaded before this script runs

(function () {
  'use strict';

  // ---- Defensive checks ----
  if (typeof d3 === 'undefined') {
    console.error('MLM: D3 not loaded. tree_d3.js requires d3 v7.');
    return;
  }

  if (!window.MLM_TREE_CONFIG || !window.MLM_TREE_CONFIG.apiSubtreeUrlTemplate) {
    console.warn('MLM: window.MLM_TREE_CONFIG.apiSubtreeUrlTemplate missing. Using fallback path /mlm/api/subtree/{node_id}/');
    window.MLM_TREE_CONFIG = window.MLM_TREE_CONFIG || {};
    window.MLM_TREE_CONFIG.apiSubtreeUrlTemplate = window.location.origin + '/mlm/api/subtree/{node_id}/';
  }

  // Keep the last fetched hierarchy so resize can re-render without refetch
  let LAST_ROOT_DATA = null;
  let LAST_START_NODE_ID = null;

  // ---- Utilities ----
  // static/mlm/js/tree_d3.js
// --- paste/replace this function in place of your old fetchSubtree ---
async function fetchSubtree(nodeId, depth = 6) {
  const url = `/mlm/api/subtree/${nodeId}/?depth=${depth}`;
  console.log('MLM: fetchSubtree called, url=', url);
  try {
    const resp = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      // try include (more permissive) instead of same-origin
      credentials: 'include'
    });
    console.log('MLM: fetch response status', resp.status, resp.statusText);
    if (!resp.ok) {
      let bodyText;
      try { bodyText = await resp.text(); } catch(e){ bodyText = ''; }
      throw new Error(`Failed to fetch subtree: ${resp.status} ${resp.statusText} - ${bodyText}`);
    }
    const data = await resp.json();
    console.log('MLM: subtree data loaded', data);
    return data;
  } catch (err) {
    console.error('MLM tree init error:', err);
    throw err;
  }
}


  function buildHierarchy(nodes, rootId) {
    const map = new Map();
    nodes.forEach(n => {
      // ensure expected shape:
      map.set(n.id, Object.assign({}, n, { children: [] }));
    });
    // attach children
    map.forEach(node => {
      if (node.parent && map.has(node.parent)) {
        map.get(node.parent).children.push(node);
      }
    });
    // pick root by id, otherwise a node with no parent
    let root = map.get(rootId);
    if (!root) {
      for (const v of map.values()) {
        if (!v.parent) { root = v; break; }
      }
    }
    return root || null;
  }

  // measure container size robustly (accounts for admin shell)
  function containerSize(container) {
    const r = container.getBoundingClientRect();
    return {
      width: Math.max(900, Math.floor(r.width || container.clientWidth || 900)),
      height: Math.max(480, Math.floor(r.height || container.clientHeight || 600))
    };
  }

  // create an SVG element (returns d3 selection)
  function createSvgElement(container, viewBox) {
    // remove old svg if present
    const existing = container.querySelector('svg.mlm-tree-svg');
    if (existing) existing.remove();

    const svg = d3.select(container)
      .append('svg')
      .attr('class', 'mlm-tree-svg')
      .attr('width', '100%')
      .attr('height', '100%');

    if (viewBox) {
      svg.attr('viewBox', `${viewBox.minX} ${viewBox.minY} ${viewBox.width} ${viewBox.height}`);
      svg.attr('preserveAspectRatio', 'xMidYMin meet');
    }

    return svg;
  }

  // Render tree into the container given a rootData (hierarchy object)
  function renderTreeInto(container, rootData) {
    if (!rootData) {
      container.innerHTML = '<div class="alert alert-warning">No nodes to display.</div>';
      return;
    }

    // constants (card size must match your node visuals)
    const cardW = 180;   // card width in px
    const cardH = 56;    // card height in px
    const hGap = 56;     // horizontal gap between centers (tweak to taste)
    const vGap = 96;     // vertical gap between levels

    // create a d3.hierarchy
    const hierarchyRoot = d3.hierarchy(rootData, d => d.children);

    // use nodeSize so d3 reserves enough spacing for our card sizes
    const treeLayout = d3.tree().nodeSize([cardW + hGap, cardH + vGap]);
    treeLayout(hierarchyRoot);

    // compute bounding box of nodes (minX,maxX,minY,maxY)
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    hierarchyRoot.descendants().forEach(d => {
      if (d.x < minX) minX = d.x;
      if (d.x > maxX) maxX = d.x;
      if (d.y < minY) minY = d.y;
      if (d.y > maxY) maxY = d.y;
    });

    // margins
    const marginX = cardW;
    const marginY = cardH;
    minX -= marginX;
    maxX += marginX;
    minY -= marginY;
    maxY += marginY;

    const viewWidth = Math.ceil(maxX - minX);
    const viewHeight = Math.ceil(maxY - minY);

    // clear container and create svg with computed viewBox
    container.innerHTML = '';
    const viewBox = { minX: minX, minY: minY, width: Math.max(viewWidth, containerSize(container).width), height: Math.max(viewHeight, containerSize(container).height) };
    const svg = createSvgElement(container, viewBox);

    // add defs (gradient) for nicer node fill
    const defs = svg.append('defs');
    const grad = defs.append('linearGradient').attr('id', 'mlm-grad').attr('x1', '0%').attr('x2', '100%');
    grad.append('stop').attr('offset', '0%').attr('stop-color', '#1a73e8');
    grad.append('stop').attr('offset', '100%').attr('stop-color', '#00c4a7');

    // main group (translate so nodes fit within margin)
    const translateX = -minX + 40;
    const translateY = -minY + 20;
    const g = svg.append('g').attr('transform', `translate(${translateX},${translateY})`);

    // links (use d3.linkVertical)
    g.selectAll('path.mlm-link')
      .data(hierarchyRoot.links())
      .join('path')
      .attr('class', 'mlm-link')
      .attr('d', d3.linkVertical().x(d => d.x).y(d => d.y))
      .attr('stroke', '#1a73e8')
      .attr('stroke-width', 2)
      .attr('fill', 'none')
      .attr('opacity', 0.95);

    // nodes
    const nodeGroups = g.selectAll('g.mlm-node-group')
      .data(hierarchyRoot.descendants(), d => d.data.id)
      .join('g')
      .attr('class', 'mlm-node-group mlm-node')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer');

    // card rect
    nodeGroups.append('rect')
      .attr('class', 'mlm-node-rect')
      .attr('x', -cardW / 2)
      .attr('y', -cardH / 2)
      .attr('width', cardW)
      .attr('height', cardH)
      .attr('rx', 10).attr('ry', 10)
      .style('fill', d => d.data.active ? 'url(#mlm-grad)' : '#f3f4f6')
      .style('stroke', d => d.data.active ? '#0f5ec7' : '#e6eefc');

    // username (wrap if too long)
    nodeGroups.append('text')
      .attr('class', 'mlm-node-text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-6')
      .each(function (d) {
        const text = (d.data.user ? d.data.user : `#${d.data.id}`).toString();
        const sel = d3.select(this);
        // simple wrap: split into two lines if > 18 chars
        if (text.length <= 18) {
          sel.text(text);
        } else {
          sel.text(null);
          sel.append('tspan').attr('x', 0).attr('dy', 0).text(text.slice(0, 18));
          sel.append('tspan').attr('x', 0).attr('dy', '1.1em').style('font-size', '11px').text(text.slice(18));
        }
        if (!d.data.active) sel.classed('inactive', true).style('fill', '#111827');
        else sel.style('fill', '#ffffff');
      });

    // position meta (L/R)
    nodeGroups.append('text')
      .attr('class', 'mlm-node-meta')
      .attr('text-anchor', 'middle')
      .attr('dy', '16')
      .text(d => d.data.position ? d.data.position : '')
      .style('fill', d => d.data.active ? 'rgba(255,255,255,0.9)' : '#6b7280');

    // zoom & pan
    const zoom = d3.zoom()
      .scaleExtent([0.2, 2.5])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // small hover effect done via CSS; click logs node for now
    nodeGroups.on('click', (event, d) => {
      console.log('MLM node clicked:', d.data);
    });
  } // renderTreeInto

  // ---- public init: fetch and render once ----
  (async function init() {
    try {
      const container = document.getElementById('mlm-tree-container') || document.getElementById('user-tree');
      if (!container) {
        console.warn('MLM: no container element (#mlm-tree-container or #user-tree).');
        return;
      }

      // determine start node id
      const nodeId = (typeof window.MLM_INIT_NODE !== 'undefined' && window.MLM_INIT_NODE !== null)
        ? window.MLM_INIT_NODE
        : (typeof window.MLM_INIT_ADMIN_NODE !== 'undefined' && window.MLM_INIT_ADMIN_NODE !== null)
          ? window.MLM_INIT_ADMIN_NODE
          : null;

      if (!nodeId) {
        container.innerHTML = '<div class="alert alert-warning">No nodes to display.</div>';
        return;
      }

      LAST_START_NODE_ID = nodeId;
      console.log('MLM: fetching subtree for node', nodeId);
      const payload = await fetchSubtree(nodeId, 6);
      if (!payload || !payload.nodes) {
        throw new Error('Invalid payload: missing nodes');
      }

      const hierarchyRoot = buildHierarchy(payload.nodes, nodeId);
      if (!hierarchyRoot) {
        container.innerHTML = '<div class="alert alert-warning">No nodes to display.</div>';
        return;
      }

      // store for resize rerender
      LAST_ROOT_DATA = hierarchyRoot;
      renderTreeInto(container, hierarchyRoot);
      console.log('MLM: tree rendered for node', nodeId);

      // responsive: re-render on resize (debounced)
      let resizeTimeout = null;
      window.addEventListener('resize', () => {
        if (resizeTimeout) clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
          try {
            if (LAST_ROOT_DATA && LAST_START_NODE_ID) {
              // re-render using the same hierarchy data (no refetch)
              renderTreeInto(container, LAST_ROOT_DATA);
            }
          } catch (err) {
            console.error('MLM: error re-rendering on resize', err);
          }
        }, 220);
      });

    } catch (err) {
      console.error('MLM tree init error:', err);
      const container = document.getElementById('mlm-tree-container') || document.getElementById('user-tree');
      if (container) container.innerHTML = '<div class="alert alert-danger">Unable to load tree visualization.</div>';
    }
  })();

})();
