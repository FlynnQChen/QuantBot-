import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
 
export async function exportToPDF(elementId, fileName = 'report.pdf')  {
  const element = document.getElementById(elementId) 
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true
  })
  
  const pdf = new jsPDF('p', 'mm', 'a4')
  const imgData = canvas.toDataURL('image/png') 
  const imgWidth = 210 // A4 width in mm 
  const pageHeight = 295 // A4 height in mm
  const imgHeight = canvas.height  * imgWidth / canvas.width 
  let heightLeft = imgHeight
  let position = 0 
 
  pdf.addImage(imgData,  'PNG', 0, position, imgWidth, imgHeight)
  heightLeft -= pageHeight 
 
  while (heightLeft >= 0) {
    position = heightLeft - imgHeight
    pdf.addPage() 
    pdf.addImage(imgData,  'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight
  }
 
  pdf.save(fileName) 
}