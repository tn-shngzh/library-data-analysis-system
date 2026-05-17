import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import {
  BarChart,
  LineChart,
  PieChart,
  HeatmapChart,
  RadarChart,
  ScatterChart
} from "echarts/charts"
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  MarkLineComponent,
  MarkPointComponent,
  GraphicComponent
} from "echarts/components"
import VChart from "vue-echarts"

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  HeatmapChart,
  RadarChart,
  ScatterChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  MarkLineComponent,
  MarkPointComponent,
  GraphicComponent
])

export { VChart }