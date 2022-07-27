graph [
  directed 1
  name "G"
  graph [
    concentrate 0
    nodesep 0.1
    ranksep 0.3
    splines 1
    rankdir "TB"
  ]
  node [
    id 0
    label "Vmem"
    style "filled"
    shape "oval"
    color "maroon"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 1
    label "Na"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 2
    label "Pmem_Na"
    style "filled"
    color "DarkSeaGreen"
    shape "hexagon"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 3
    label "Na_env"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 4
    label "K"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 5
    label "Pmem_K"
    style "filled"
    color "DarkSeaGreen"
    shape "hexagon"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 6
    label "K_env"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 7
    label "P"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 8
    label "M"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 9
    label "Pmem_M"
    style "filled"
    color "DarkSeaGreen"
    shape "hexagon"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 10
    label "M_env"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 11
    label "Anion"
    style "filled"
    color "LightCyan"
    shape "ellipse"
    fontcolor "Black"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 12
    label "Anion_growth"
    style "filled"
    color "DarkSeaGreen"
    shape "rect"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 13
    label "Anion_decay"
    style "filled"
    color "DarkSeaGreen"
    shape "rect"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  node [
    id 14
    label "K_Channel1"
    style "filled"
    color "DarkSeaGreen"
    shape "pentagon"
    fontcolor "White"
    fontname "DejaVu Sans"
    fontsize 16
  ]
  edge [
    source 1
    target 2
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 2
    target 3
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 2
    target 0
    arrowhead "dot"
    color "blue"
    penwidth 2.0
  ]
  edge [
    source 4
    target 5
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 5
    target 6
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 5
    target 0
    arrowhead "tee"
    color "red"
    penwidth 2.0
  ]
  edge [
    source 6
    target 0
    arrowhead "dot"
    color "blue"
    penwidth 2.0
  ]
  edge [
    source 8
    target 9
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 9
    target 10
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 11
    target 13
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 11
    target 14
    arrowhead "tee"
    color "red"
    penwidth 2.0
  ]
  edge [
    source 12
    target 11
    arrowhead "normal"
    coeff 1.0
    penwidth 2.0
  ]
  edge [
    source 14
    target 5
    arrowhead "dot"
    color "blue"
    penwidth 2.0
  ]
]
