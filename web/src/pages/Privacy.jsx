/**
 * Privacy policy — public page (no auth required).
 */
export default function Privacy() {
  return (
    <div className="min-h-screen bg-brand-bg text-brand-silver p-6 md:p-12">
      <div className="max-w-2xl mx-auto">
        <a href="/" className="text-brand-muted text-sm hover:text-brand-silver transition-colors">
          &larr; Back to Iron Skillet
        </a>

        <h1 className="text-2xl font-black text-brand-text tracking-wide mt-6 mb-8">
          Privacy Policy
        </h1>

        <div className="space-y-6 text-sm leading-relaxed">
          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">What we collect</h2>
            <p>
              Iron Skillet stores only the data you provide directly:
            </p>
            <ul className="list-disc ml-5 mt-2 space-y-1">
              <li>Account info (email, name, dietary preferences)</li>
              <li>Recipes you save, cooking log entries, and ratings</li>
              <li>Shopping list items</li>
              <li>Search terms used in Instant Chef</li>
              <li>Todoist integration token (encrypted at rest)</li>
            </ul>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">How we use your data</h2>
            <ul className="list-disc ml-5 space-y-1">
              <li>Generate personalized meal plan suggestions based on your preferences and favorites</li>
              <li>Send meal plan emails (only if you opt in)</li>
              <li>Sync ingredients to your Todoist grocery list (only if you connect it)</li>
            </ul>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">Emails</h2>
            <p>
              We send meal plan emails only to users who explicitly opt in.
              You can unsubscribe at any time via the link in every email or
              in your <a href="/settings" className="text-brand-blue underline">Settings</a>.
              A one-time welcome email is sent when you create an account.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">Cookies</h2>
            <p>
              We use a single HTTP-only session cookie (<code>session_token</code>) to
              keep you logged in. No tracking, analytics, or third-party cookies are used.
            </p>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">Data retention</h2>
            <ul className="list-disc ml-5 space-y-1">
              <li>Sessions expire after 30 days and are cleaned up daily</li>
              <li>Search history and sync logs are automatically deleted after 90 days</li>
              <li>Recipes and cooking logs are kept until you delete them or your account</li>
            </ul>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">Your rights</h2>
            <p>You can exercise the following at any time from your <a href="/settings" className="text-brand-blue underline">Settings</a> page:</p>
            <ul className="list-disc ml-5 mt-2 space-y-1">
              <li><strong>Export your data</strong> — download everything we store about you as JSON</li>
              <li><strong>Delete your account</strong> — permanently removes all your data, uploaded images, and sessions</li>
              <li><strong>Update email preferences</strong> — opt in or out of meal plan emails</li>
            </ul>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">Security</h2>
            <ul className="list-disc ml-5 space-y-1">
              <li>Passwords are hashed with bcrypt</li>
              <li>Third-party API tokens are encrypted with Fernet symmetric encryption</li>
              <li>Session cookies are HTTP-only and SameSite=Lax</li>
            </ul>
          </section>

          <section>
            <h2 className="font-bold text-brand-text text-base mb-2">Self-hosted</h2>
            <p>
              Iron Skillet is self-hosted. Your data lives on your own server and is
              never shared with third parties (except Todoist, if you connect it, and
              web search providers used to find recipe URLs).
            </p>
          </section>
        </div>

        <p className="text-brand-muted text-xs mt-10">
          Last updated: April 2026
        </p>
      </div>
    </div>
  )
}
