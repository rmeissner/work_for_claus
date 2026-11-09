const COMMIT_URL = 'https://github.com/rmeissner/work_for_claus/commit/'

/** The app version and the commit it was built from, e.g. `v0.1.0 · 3f73489`. */
export function AppVersion() {
  return (
    <p className="m-0 text-sm whitespace-nowrap text-muted">
      v{__APP_VERSION__} ·{' '}
      {__APP_COMMIT__ === 'dev' ? (
        __APP_COMMIT__
      ) : (
        <a href={`${COMMIT_URL}${__APP_COMMIT__}`} className="underline">
          {__APP_COMMIT__}
        </a>
      )}
    </p>
  )
}
