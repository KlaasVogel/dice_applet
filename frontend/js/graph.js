// Reusable p5.js decay-curve graph component.
//
// createDecayGraph(containerEl, options) -> { destroy(), resize(), update(lines, opts) }
//   options.lines:      [{ data: number[], color: string, key?: string }]  (1 or 2 lines)
//   options.axisLabels:  { x: string, y: string }  (already-translated label text)
//   options.totalDice:   number, default 100 — fixes the y-axis domain
//
// Notes:
// - Instance-mode p5, noLoop() + manual redraw() — this is a static chart, not an
//   animation, so there's no reason to run a 60fps draw loop.
// - createDecayGraph()/resize() must only be called while containerEl is visible
//   (display !== 'none'); clientWidth reads 0 otherwise and the canvas will be sized
//   incorrectly. Callers are responsible for only creating/resizing after showing
//   the containing view.
// - Curve smoothing uses a monotone cubic Hermite (Steffen's method) instead of
//   p5's built-in curveVertex()/Catmull-Rom: verified against the real mock data
//   (Activity 3 player 2's "...,62,55,56,48,..." wiggle) that Catmull-Rom's
//   automatic tangents visibly overshoot there, implying a bump the data doesn't
//   support. Steffen's method guarantees each segment stays within the range of
//   its two endpoints.

const GRAPH_MARGIN = { top: 16, right: 16, bottom: 36, left: 48 };
const GRAPH_DOT_RADIUS = 4;
const GRAPH_CROSSHAIR_COLOR = "#dc2626";

function createDecayGraph(containerEl, options) {
  let currentLines = _normalizeLines(options.lines);
  let axisLabels = options.axisLabels || { x: "", y: "" };
  const totalDice = options.totalDice || 100;
  let hoverIndex = null;

  const sketch = (p) => {
    p.setup = () => {
      const w = containerEl.clientWidth;
      const canvas = p.createCanvas(w, _computeHeight(w));
      canvas.parent(containerEl);
      canvas.elt.style.touchAction = "none"; // scoped to the canvas only; rest of the page still scrolls
      p.noLoop();
    };

    p.draw = () => {
      p.background("#ffffff");
      const plot = _plotRect(p.width, p.height);
      const n = Math.max(1, ..._lineLengths(currentLines));

      _drawAxes(p, plot, totalDice, n, axisLabels);

      for (const line of currentLines) {
        const pts = _toPixelPoints(line.data, plot, totalDice, n);
        _drawSmoothLine(p, pts, line.color);
        _drawDots(p, pts, line.color);
      }

      if (hoverIndex !== null) {
        _drawCrosshair(p, plot, currentLines, totalDice, n, hoverIndex);
      }
    };

    p.mouseMoved = () => _updateHover(p, plot_(p), currentLines, totalDice);
    p.touchMoved = () => {
      _updateHover(p, plot_(p), currentLines, totalDice);
      return false;
    };
    p.mouseOut = () => _clearHover(p);
    p.touchEnded = () => _clearHover(p);

    function plot_(pInst) {
      return _plotRect(pInst.width, pInst.height);
    }

    function _updateHover(pInst, plot, lines, total) {
      const n = Math.max(1, ..._lineLengths(lines));
      if (pInst.mouseX < plot.x - 8 || pInst.mouseX > plot.x + plot.w + 8) {
        if (hoverIndex !== null) {
          hoverIndex = null;
          pInst.redraw();
        }
        return;
      }
      const idx = _pixelXToIndex(pInst.mouseX, plot.x, plot.w, n);
      if (idx !== hoverIndex) {
        hoverIndex = idx;
        pInst.redraw();
      }
    }

    function _clearHover(pInst) {
      if (hoverIndex !== null) {
        hoverIndex = null;
        pInst.redraw();
      }
    }
  };

  const instance = new p5(sketch);

  return {
    destroy() {
      instance.remove();
    },
    resize() {
      const w = containerEl.clientWidth;
      instance.resizeCanvas(w, _computeHeight(w));
      instance.redraw();
    },
    update(newLines, opts = {}) {
      currentLines = _normalizeLines(newLines);
      if (opts.axisLabels) axisLabels = opts.axisLabels;
      hoverIndex = null;
      instance.redraw();
    },
  };
}

function _normalizeLines(lines) {
  return (lines || []).map((line) => ({
    data: line.data || [],
    color: line.color || "#2563eb",
    key: line.key || "",
  }));
}

function _lineLengths(lines) {
  return lines.length ? lines.map((l) => l.data.length) : [0];
}

function _computeHeight(width) {
  return Math.max(200, Math.min(320, Math.round(width * 0.68)));
}

function _plotRect(width, height) {
  return {
    x: GRAPH_MARGIN.left,
    y: GRAPH_MARGIN.top,
    w: Math.max(1, width - GRAPH_MARGIN.left - GRAPH_MARGIN.right),
    h: Math.max(1, height - GRAPH_MARGIN.top - GRAPH_MARGIN.bottom),
  };
}

function _xScale(index, plot, n) {
  if (n <= 1) return plot.x;
  return plot.x + (index / (n - 1)) * plot.w;
}

function _yScale(value, plot, totalDice) {
  return plot.y + plot.h - (value / totalDice) * plot.h;
}

function _pixelXToIndex(px, plotX, plotW, n) {
  const t = Math.min(1, Math.max(0, (px - plotX) / plotW));
  return Math.round(t * (n - 1));
}

function _toPixelPoints(data, plot, totalDice, n) {
  return data.map((v, i) => ({ x: _xScale(i, plot, n), y: _yScale(v, plot, totalDice) }));
}

function _xTickStep(n) {
  if (n <= 11) return 1;
  if (n <= 21) return 2;
  return 5;
}

function _drawAxes(p, plot, totalDice, n, axisLabels) {
  p.stroke("#e5e7eb");
  p.strokeWeight(1);
  p.textSize(10);
  p.textAlign(p.RIGHT, p.CENTER);
  p.noStroke();
  p.fill("#6b7280");
  const yStep = totalDice / 5;
  for (let v = 0; v <= totalDice; v += yStep) {
    const y = _yScale(v, plot, totalDice);
    p.stroke("#e5e7eb");
    p.line(plot.x, y, plot.x + plot.w, y);
    p.noStroke();
    p.text(Math.round(v), plot.x - 6, y);
  }

  p.textAlign(p.CENTER, p.TOP);
  const step = _xTickStep(n);
  for (let i = 0; i < n; i += step) {
    const x = _xScale(i, plot, n);
    p.fill("#6b7280");
    p.text(i, x, plot.y + plot.h + 6);
  }

  p.stroke("#9ca3af");
  p.strokeWeight(1.5);
  p.line(plot.x, plot.y, plot.x, plot.y + plot.h);
  p.line(plot.x, plot.y + plot.h, plot.x + plot.w, plot.y + plot.h);

  p.noStroke();
  p.fill("#374151");
  p.textSize(11);
  p.textAlign(p.CENTER, p.BOTTOM);
  p.text(axisLabels.x, plot.x + plot.w / 2, plot.y + plot.h + 34);

  p.push();
  p.translate(12, plot.y + plot.h / 2);
  p.rotate(-p.HALF_PI);
  p.textAlign(p.CENTER, p.TOP);
  p.text(axisLabels.y, 0, 0);
  p.pop();
}

// Steffen's method — single-pass monotone tangents, no overshoot past neighbour values.
function _monotoneTangents(ys) {
  const n = ys.length;
  const m = new Array(n);
  if (n < 2) return m.fill(0);
  const s = (i) => ys[i + 1] - ys[i];
  m[0] = s(0);
  m[n - 1] = s(n - 2);
  for (let i = 1; i < n - 1; i++) {
    const sPrev = s(i - 1);
    const sNext = s(i);
    if (sPrev === 0 || sNext === 0 || sPrev > 0 !== sNext > 0) {
      m[i] = 0;
    } else {
      const avg = (sPrev + sNext) / 2;
      const sign = Math.sign(sPrev);
      m[i] = sign * Math.min(Math.abs(avg), 2 * Math.abs(sPrev), 2 * Math.abs(sNext));
    }
  }
  return m;
}

function _drawSmoothLine(p, pts, color) {
  if (pts.length === 0) return;
  if (pts.length === 1) {
    return;
  }
  // Tangents are computed with an implicit dx of 1 index-step (see _monotoneTangents:
  // it works on ys[i+1]-ys[i] directly, not divided by the real pixel spacing). So
  // each tangent already represents "y-change over one full index-step" — the Bezier
  // y-offset for a third of that step is tangent/3, NOT tangent*dx_pixel/3. Only the
  // x-offset needs the real pixel dx (one-third of the segment's pixel width).
  const tangents = _monotoneTangents(pts.map((pt) => pt.y));
  p.noFill();
  p.stroke(color);
  p.strokeWeight(2);
  p.beginShape();
  p.vertex(pts[0].x, pts[0].y);
  for (let i = 0; i < pts.length - 1; i++) {
    const dx = pts[i + 1].x - pts[i].x;
    const cp1x = pts[i].x + dx / 3;
    const cp1y = pts[i].y + tangents[i] / 3;
    const cp2x = pts[i + 1].x - dx / 3;
    const cp2y = pts[i + 1].y - tangents[i + 1] / 3;
    p.bezierVertex(cp1x, cp1y, cp2x, cp2y, pts[i + 1].x, pts[i + 1].y);
  }
  p.endShape();
}

function _drawDots(p, pts, color) {
  p.noStroke();
  p.fill(color);
  for (const pt of pts) {
    p.circle(pt.x, pt.y, GRAPH_DOT_RADIUS * 2);
  }
}

function _drawCrosshair(p, plot, lines, totalDice, n, index) {
  const x = _xScale(index, plot, n);
  p.stroke(GRAPH_CROSSHAIR_COLOR);
  p.strokeWeight(1);
  p.line(x, plot.y, x, plot.y + plot.h);

  lines.forEach((line) => {
    if (index >= line.data.length) return;
    const value = line.data[index];
    const y = _yScale(value, plot, totalDice);
    p.stroke(GRAPH_CROSSHAIR_COLOR);
    p.line(plot.x, y, plot.x + plot.w, y);

    const label = `(${index}, ${value})`;
    p.textSize(10);
    const labelW = p.textWidth(label) + 8;
    const flipBelow = y - 18 < plot.y;
    const labelY = flipBelow ? y + 6 : y - 18;
    const labelX = Math.min(x + 6, plot.x + plot.w - labelW);

    p.noStroke();
    p.fill("#ffffff");
    p.rect(labelX, labelY, labelW, 16, 3);
    p.fill(GRAPH_CROSSHAIR_COLOR);
    p.textAlign(p.LEFT, p.TOP);
    p.text(label, labelX + 4, labelY + 3);
  });
}
