/**
 * ContentBadge Component
 * Displays color-coded content rating badges
 * Green: within threshold, Red: exceeds threshold, Gray: no threshold set
 */

interface ContentBadgeProps {
  label: 'Sex' | 'Violence' | 'Language'
  score: number
  threshold?: number | null
}

const ContentBadge = ({ label, score, threshold }: ContentBadgeProps) => {
  // Determine color based on threshold
  let bgColor = 'bg-content-unavailable' // Gray - no threshold set
  let textColor = 'text-gray-800'

  if (threshold !== null && threshold !== undefined) {
    if (score <= threshold) {
      bgColor = 'bg-content-safe' // Green - within threshold
      textColor = 'text-white'
    } else {
      bgColor = 'bg-content-warning' // Red - exceeds threshold
      textColor = 'text-white'
    }
  } else {
    textColor = 'text-gray-700'
  }

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${bgColor} ${textColor}`}
      title={`${label}: ${score}/10${threshold !== null && threshold !== undefined ? ` (threshold: ${threshold})` : ' (no filter)'}`}
    >
      {label} {score}
    </span>
  )
}

export default ContentBadge
