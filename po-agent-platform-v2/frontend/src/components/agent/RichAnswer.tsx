import { Fragment, ReactNode } from 'react'

function inline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.filter(Boolean).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    return <Fragment key={index}>{part}</Fragment>
  })
}

function isTableDivider(line: string): boolean {
  return /^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*$/.test(line)
}

function splitTableRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map(cell => cell.trim())
}

export function RichAnswer({ text }: { text: string }) {
  const lines = text.replace(/\r/g, '').split('\n')
  const nodes: ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i].trim()

    if (!line) {
      i += 1
      continue
    }

    if (line.startsWith('|') && i + 1 < lines.length && isTableDivider(lines[i + 1])) {
      const headers = splitTableRow(lines[i])
      const rows: string[][] = []
      i += 2
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        rows.push(splitTableRow(lines[i]))
        i += 1
      }
      nodes.push(
        <div className="answer-table-wrap" key={'table-' + i}>
          <table className="answer-table">
            <thead><tr>{headers.map((cell, index) => <th key={index}>{inline(cell)}</th>)}</tr></thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{inline(cell)}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>,
      )
      continue
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      const level = heading[1].length
      nodes.push(<div className={'answer-heading answer-heading-' + level} key={'h-' + i}>{inline(heading[2])}</div>)
      i += 1
      continue
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ''))
        i += 1
      }
      nodes.push(<ul className="answer-list" key={'ul-' + i}>{items.map((item, index) => <li key={index}>{inline(item)}</li>)}</ul>)
      continue
    }

    nodes.push(<p className="answer-paragraph" key={'p-' + i}>{inline(line)}</p>)
    i += 1
  }

  return <div className="rich-answer">{nodes}</div>
}

export default RichAnswer
