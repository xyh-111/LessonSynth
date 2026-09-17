import { saveAs } from 'file-saver'
import { ElMessage } from 'element-plus'
import {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, TabStopType, TabStopPosition,
} from 'docx'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

function safeFilename(name) {
  return (name || '教案').replace(/[\\/:*?"<>|]/g, '_')
}

export function lessonToMarkdown(data) {
  const lines = []
  const td = data.teaching_design
  const obj = data.teaching_objectives
  const kp = data.key_difficult_points

  lines.push(`# ${data.lesson_title}`)
  lines.push('')

  lines.push('## 一、教学目标')
  lines.push('')
  lines.push(`- **知识与技能**：${obj.knowledge}`)
  lines.push(`- **过程与方法**：${obj.process}`)
  lines.push(`- **情感态度与价值观**：${obj.emotion}`)
  lines.push('')

  lines.push('## 二、重点难点')
  lines.push('')
  lines.push(`- **教学重点**：${kp.key_point}`)
  lines.push(`- **教学难点**：${kp.difficult_point}`)
  lines.push('')

  lines.push('## 三、课前准备')
  lines.push('')
  td.pre_class_prep.forEach((item, i) => {
    lines.push(`${i + 1}. ${item}`)
  })
  lines.push('')

  lines.push('## 四、教学过程')
  lines.push('')
  td.teaching_process.forEach((stage, idx) => {
    lines.push(`### ${idx + 1}. ${stage.stage_name}`)
    lines.push('')
    lines.push('**教学步骤：**')
    lines.push('')
    stage.steps.forEach((step, i) => {
      lines.push(`${i + 1}. ${step}`)
    })
    lines.push('')
    if (stage.student_presets && stage.student_presets.length) {
      lines.push('**学情预设：**')
      lines.push('')
      stage.student_presets.forEach(s => {
        lines.push(`- ${s}`)
      })
      lines.push('')
    }
    if (stage.teacher_summary) {
      lines.push(`**教师小结**：${stage.teacher_summary}`)
      lines.push('')
    }
    lines.push(`> **【设计意图】** ${stage.design_intent}`)
    lines.push('')
  })

  lines.push('## 五、板书设计')
  lines.push('')
  lines.push(td.blackboard_design)
  lines.push('')

  lines.push('## 六、作业设计')
  lines.push('')
  td.homework.forEach((h, i) => {
    lines.push(`${i + 1}. ${h}`)
  })
  lines.push('')

  if (td.teaching_reflection) {
    lines.push('## 七、教学反思')
    lines.push('')
    lines.push(td.teaching_reflection)
    lines.push('')
  }

  return lines.join('\n')
}

export function exportMarkdown(data) {
  const md = lessonToMarkdown(data)
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  saveAs(blob, `${safeFilename(data.lesson_title)}.md`)
}

function p(text, paragraphOpts = {}) {
  let runs
  if (typeof text === 'string') {
    runs = [new TextRun({ text })]
  } else if (Array.isArray(text)) {
    runs = text.map(t =>
      t instanceof TextRun ? t : new TextRun({ text: t })
    )
  } else if (text instanceof TextRun) {
    runs = [text]
  } else {
    runs = [new TextRun({ text: String(text) })]
  }
  return new Paragraph({ children: runs, ...paragraphOpts })
}

function heading(text, level) {
  return new Paragraph({
    text,
    heading: level,
    spacing: { before: 200, after: 100 },
  })
}

function bullet(text, bold = false) {
  return new Paragraph({
    children: [new TextRun({ text, bold })],
    bullet: { level: 0 },
    spacing: { after: 60 },
  })
}

export function exportDocx(data) {
  const td = data.teaching_design
  const obj = data.teaching_objectives
  const kp = data.key_difficult_points

  const children = []

  children.push(new Paragraph({
    children: [new TextRun({ text: data.lesson_title, bold: true, size: 36 })],
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
  }))

  children.push(heading('一、教学目标', HeadingLevel.HEADING_1))
  children.push(bullet(`知识与技能：${obj.knowledge}`))
  children.push(bullet(`过程与方法：${obj.process}`))
  children.push(bullet(`情感态度与价值观：${obj.emotion}`))

  children.push(heading('二、重点难点', HeadingLevel.HEADING_1))
  children.push(bullet(`教学重点：${kp.key_point}`))
  children.push(bullet(`教学难点：${kp.difficult_point}`))

  children.push(heading('三、课前准备', HeadingLevel.HEADING_1))
  td.pre_class_prep.forEach(item => children.push(bullet(item)))

  children.push(heading('四、教学过程', HeadingLevel.HEADING_1))
  td.teaching_process.forEach((stage, idx) => {
    children.push(heading(`${idx + 1}. ${stage.stage_name}`, HeadingLevel.HEADING_2))
    children.push(p(new TextRun({ text: '教学步骤：', bold: true }), { spacing: { before: 100 } }))
    stage.steps.forEach((step, i) => {
      children.push(new Paragraph({
        children: [new TextRun({ text: `${i + 1}. ${step}` })],
        spacing: { after: 60 },
        indent: { left: 360 },
      }))
    })
    if (stage.student_presets && stage.student_presets.length) {
      children.push(p(new TextRun({ text: '学情预设：', bold: true }), { spacing: { before: 100 } }))
      stage.student_presets.forEach(s => children.push(bullet(s)))
    }
    if (stage.teacher_summary) {
      children.push(new Paragraph({
        children: [
          new TextRun({ text: '教师小结：', bold: true }),
          new TextRun({ text: stage.teacher_summary }),
        ],
        spacing: { before: 100, after: 60 },
      }))
    }
    children.push(new Paragraph({
      children: [
        new TextRun({ text: '【设计意图】', bold: true, color: '4d6bfe' }),
        new TextRun({ text: stage.design_intent, color: '4d6bfe' }),
      ],
      spacing: { before: 100, after: 200 },
      shading: { type: 'clear', fill: 'EEF2FF' },
      indent: { left: 200, right: 200 },
    }))
  })

  children.push(heading('五、板书设计', HeadingLevel.HEADING_1))
  children.push(p(td.blackboard_design, { spacing: { after: 60 } }))

  children.push(heading('六、作业设计', HeadingLevel.HEADING_1))
  td.homework.forEach((h, i) => {
    children.push(new Paragraph({
      children: [new TextRun({ text: `${i + 1}. ${h}` })],
      spacing: { after: 60 },
    }))
  })

  if (td.teaching_reflection) {
    children.push(heading('七、教学反思', HeadingLevel.HEADING_1))
    children.push(p(td.teaching_reflection))
  }

  const doc = new Document({
    sections: [{ children }],
  })

  Packer.toBlob(doc).then(blob => {
    saveAs(blob, `${safeFilename(data.lesson_title)}.docx`)
  })
}

export function exportPdf(data) {
  const td = data.teaching_design
  const obj = data.teaching_objectives
  const kp = data.key_difficult_points

  const esc = s => String(s || '').replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]))

  let body = `<h1>${esc(data.lesson_title)}</h1>\n`

  body += `<h2>一、教学目标</h2>\n<ul>\n`
  body += `<li><strong>知识与技能</strong>：${esc(obj.knowledge)}</li>\n`
  body += `<li><strong>过程与方法</strong>：${esc(obj.process)}</li>\n`
  body += `<li><strong>情感态度与价值观</strong>：${esc(obj.emotion)}</li>\n</ul>\n`

  body += `<h2>二、重点难点</h2>\n<ul>\n`
  body += `<li><strong>教学重点</strong>：${esc(kp.key_point)}</li>\n`
  body += `<li><strong>教学难点</strong>：${esc(kp.difficult_point)}</li>\n</ul>\n`

  body += `<h2>三、课前准备</h2>\n<ol>\n`
  td.pre_class_prep.forEach(item => { body += `<li>${esc(item)}</li>\n` })
  body += `</ol>\n`

  body += `<h2>四、教学过程</h2>\n`
  td.teaching_process.forEach((stage, idx) => {
    body += `<h3>${idx + 1}. ${esc(stage.stage_name)}</h3>\n`
    body += `<p><strong>教学步骤：</strong></p>\n<ol>\n`
    stage.steps.forEach(step => { body += `<li>${esc(step)}</li>\n` })
    body += `</ol>\n`
    if (stage.student_presets && stage.student_presets.length) {
      body += `<p><strong>学情预设：</strong></p>\n<ul>\n`
      stage.student_presets.forEach(s => { body += `<li>${esc(s)}</li>\n` })
      body += `</ul>\n`
    }
    if (stage.teacher_summary) {
      body += `<p><strong>教师小结</strong>：${esc(stage.teacher_summary)}</p>\n`
    }
    body += `<blockquote><strong>【设计意图】</strong> ${esc(stage.design_intent)}</blockquote>\n`
  })

  body += `<h2>五、板书设计</h2>\n<p>${esc(td.blackboard_design)}</p>\n`

  body += `<h2>六、作业设计</h2>\n<ol>\n`
  td.homework.forEach(h => { body += `<li>${esc(h)}</li>\n` })
  body += `</ol>\n`

  if (td.teaching_reflection) {
    body += `<h2>七、教学反思</h2>\n<p>${esc(td.teaching_reflection)}</p>\n`
  }

  const container = document.createElement('div')
  container.className = 'pdf-export-container'
  container.style.cssText = `
    position: fixed;
    left: -9999px;
    top: 0;
    width: 794px;
    min-height: 1123px;
    background: #ffffff;
    padding: 40px 50px;
    font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
    line-height: 1.8;
    color: #1f2937;
    box-sizing: border-box;
  `
  container.innerHTML = `
    <style>
      .pdf-export-container h1 { text-align: center; font-size: 24px; margin-bottom: 24px; color: #1f2937; border-bottom: 2px solid #4d6bfe; padding-bottom: 12px; }
      .pdf-export-container h2 { font-size: 18px; color: #4d6bfe; margin-top: 28px; margin-bottom: 12px; border-left: 4px solid #4d6bfe; padding-left: 10px; }
      .pdf-export-container h3 { font-size: 15px; color: #1f2937; margin-top: 20px; margin-bottom: 10px; }
      .pdf-export-container ul, .pdf-export-container ol { padding-left: 24px; }
      .pdf-export-container li { margin-bottom: 6px; }
      .pdf-export-container p { margin: 8px 0; }
      .pdf-export-container blockquote {
        margin: 12px 0;
        padding: 10px 16px;
        background: #eef2ff;
        border-left: 4px solid #4d6bfe;
        color: #4d6bfe;
        border-radius: 0 6px 6px 0;
      }
      .pdf-export-container strong { color: #1f2937; }
    </style>
    ${body}
  `
  document.body.appendChild(container)

  html2canvas(container, {
    scale: 2,
    useCORS: true,
    backgroundColor: '#ffffff',
  }).then(canvas => {
    const imgWidth = 210
    const pageHeight = 297
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    const pdf = new jsPDF('p', 'mm', 'a4')
    let position = 0
    let heightLeft = imgHeight

    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    pdf.save(`${safeFilename(data.lesson_title)}.pdf`)
    document.body.removeChild(container)
    ElMessage.success('PDF 导出成功')
  }).catch(err => {
    console.error(err)
    document.body.removeChild(container)
    ElMessage.error('PDF 导出失败，请重试')
  })
}
