import { useState } from "react";
import { useTranslation } from "react-i18next";

/** Uses the native Web Share API where available; falls back to copying the link to the clipboard.
 * The URL is the public, no-login tracking page only - no private data can be reached through it. */
export default function ShareTrackingButton({ trackingNumber }: { trackingNumber: string }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const url = `${window.location.origin}/track/${trackingNumber}`;

  async function onShare() {
    if (navigator.share) {
      try {
        await navigator.share({ title: trackingNumber, url });
      } catch {
        // user dismissed the share sheet - not an error
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // clipboard unavailable - nothing more we can honestly do
    }
  }

  return (
    <button className="btn btn-secondary" type="button" onClick={onShare} aria-label={t("track.shareTracking")}>
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <path d="M14 6a2 2 0 100-4 2 2 0 000 4zM6 12a2 2 0 100-4 2 2 0 000 4zm8 6a2 2 0 100-4 2 2 0 000 4zM7.6 10.8l4.8-2.6m-4.8 2.6l4.8 2.6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
      {copied ? t("track.linkCopied") : t("track.shareTracking")}
    </button>
  );
}
