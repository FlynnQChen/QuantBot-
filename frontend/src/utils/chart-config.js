import { Chart, registerables } from 'chart.js' 
import zoomPlugin from 'chartjs-plugin-zoom'
 
Chart.register(...registerables,  zoomPlugin)
 
export const defaultConfig = {
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false 
  },
  plugins: {
    legend: {
      position: 'top'
    },
    zoom: {
      zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: 'xy'
      },
      pan: {
        enabled: true,
        mode: 'xy'
      }
    }
  }
}