/**
 * OgreLoading — shown whenever the app is waiting on the LLM.
 * The ogre consults his recipe book while we wait.
 *
 * Props:
 *   message  — primary line of text (default: "Looking for a recipe…")
 *   hint     — smaller secondary line (optional)
 */
export default function OgreLoading({
  message = 'Looking for a recipe…',
  hint,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 select-none">
      <div className="relative w-full max-w-md">
        <img
          src="/ogre-cooking-loading.png"
          alt="The ogre is thinking…"
          className="w-full rounded-2xl shadow-forge-lg"
        />
      </div>
      <p className="mt-5 text-brand-silver font-semibold text-sm tracking-wide">{message}</p>
      {hint && (
        <p className="mt-1 text-brand-muted text-xs">{hint}</p>
      )}
    </div>
  )
}
