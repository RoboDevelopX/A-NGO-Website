/**
 * Renders a configured photo, or a branded placeholder when no image is set,
 * so a fresh install looks finished before any photos are added.
 */
export function Media({
  src,
  alt,
  label,
  className = "",
  priority = false,
}: {
  src?: string;
  alt?: string;
  label: string;
  className?: string;
  priority?: boolean;
}) {
  if (src) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={src}
        alt={alt ?? label}
        className={`media ${className}`}
        loading={priority ? "eager" : "lazy"}
      />
    );
  }
  return (
    <div className={`media media--placeholder ${className}`} role="img" aria-label={alt ?? `${label} (placeholder image)`}>
      <svg viewBox="0 0 24 24" aria-hidden="true" width="36" height="36">
        <path
          fill="currentColor"
          d="M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2ZM8.5 11a2 2 0 1 1 0-4 2 2 0 0 1 0 4ZM5 19l4.5-6 3.5 4.5 2.5-3L19 19H5Z"
        />
      </svg>
      <span>{label}</span>
    </div>
  );
}
