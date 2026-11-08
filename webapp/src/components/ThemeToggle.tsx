import type { ReactNode } from 'react'
import { type ThemePreference, useTheme } from '../theme/useTheme'

const iconProps = {
  'aria-hidden': true,
  className: 'size-4',
  fill: 'none',
  stroke: 'currentColor',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  strokeWidth: 2,
  viewBox: '0 0 24 24',
} as const

const options: { value: ThemePreference; label: string; icon: ReactNode }[] = [
  {
    value: 'system',
    label: 'System',
    icon: (
      <svg {...iconProps}>
        <rect x="3" y="4" width="18" height="12" rx="2" />
        <path d="M8 20h8M12 16v4" />
      </svg>
    ),
  },
  {
    value: 'light',
    label: 'Light',
    icon: (
      <svg {...iconProps}>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
    ),
  },
  {
    value: 'dark',
    label: 'Dark',
    icon: (
      <svg {...iconProps}>
        <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
      </svg>
    ),
  },
]

/** A segmented control to choose between the system, light and dark theme. */
export function ThemeToggle() {
  const { preference, setPreference } = useTheme()

  return (
    <fieldset className="m-0 flex rounded-item border border-border bg-surface p-0.5">
      <legend className="sr-only">Theme</legend>
      {options.map(({ value, label, icon }) => (
        <label
          key={value}
          title={label}
          className="flex cursor-pointer items-center rounded-item px-1.5 py-1 hover:bg-hover has-checked:bg-selected-bg has-checked:text-selected-fg has-focus-visible:outline-2 has-focus-visible:outline-accent"
        >
          <input
            type="radio"
            name="theme"
            value={value}
            checked={preference === value}
            onChange={() => setPreference(value)}
            className="sr-only"
          />
          {icon}
          <span className="sr-only">{label}</span>
        </label>
      ))}
    </fieldset>
  )
}
