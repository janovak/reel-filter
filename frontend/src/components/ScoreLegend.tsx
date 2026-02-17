/**
 * ScoreLegend Component
 * Content score legend with color-coded labels and tooltips
 * 0=None, 1-2=Mild, 3-4=Moderate, 5-6=Strong, 7-8=Intense, 9-10=Extreme
 */

interface ScoreLegendProps {
  compact?: boolean
}

const SCORE_LEVELS = [
  { range: '0', label: 'None', color: 'bg-gray-300', textColor: 'text-gray-600' },
  { range: '1–2', label: 'Mild', color: 'bg-green-400', textColor: 'text-green-700' },
  { range: '3–4', label: 'Moderate', color: 'bg-yellow-400', textColor: 'text-yellow-700' },
  { range: '5–6', label: 'Strong', color: 'bg-orange-400', textColor: 'text-orange-700' },
  { range: '7–8', label: 'Intense', color: 'bg-red-400', textColor: 'text-red-700' },
  { range: '9–10', label: 'Extreme', color: 'bg-red-700', textColor: 'text-red-800' },
]

const ScoreLegend = ({ compact = false }: ScoreLegendProps) => {
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2 text-xs">
        {SCORE_LEVELS.map((level) => (
          <div
            key={level.range}
            className="flex items-center gap-1"
            title={`${level.range}: ${level.label}`}
          >
            <div className={`w-3 h-3 rounded-full ${level.color}`} />
            <span className={`font-medium ${level.textColor}`}>
              {level.range}
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Content Score Legend
      </h4>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
        {SCORE_LEVELS.map((level) => (
          <div
            key={level.range}
            className="flex items-center gap-2 p-2 rounded-lg bg-white border border-gray-100"
            title={`Score ${level.range}: ${level.label} content`}
          >
            <div className={`w-4 h-4 rounded-full flex-shrink-0 ${level.color}`} />
            <div>
              <div className="text-xs font-bold text-gray-800">{level.range}</div>
              <div className="text-xs text-gray-500">{level.label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ScoreLegend
