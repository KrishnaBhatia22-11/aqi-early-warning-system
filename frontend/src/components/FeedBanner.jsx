import { formatAsOf, formatAge } from "../utils/feed";

// Site-wide notice whenever the live CPCB feed is not what is being shown.
export default function FeedBanner({ feed, loading }) {
  if (loading || !feed) return null;

  if (feed.mode === "snapshot") {
    return (
      <div className="feed-banner feed-banner-snapshot" role="alert">
        <b>LIVE CPCB FEED UNAVAILABLE.</b>{" "}
        Showing last stored readings from {formatAsOf(feed.asOfLatest)} ({formatAge(feed.asOfLatest)}).
        These are not current values.
      </div>
    );
  }
  if (feed.mode === "unavailable") {
    return (
      <div className="feed-banner feed-banner-none" role="alert">
        <b>LIVE CPCB FEED UNAVAILABLE.</b>{" "}
        Live CPCB data is currently unavailable (source not responding) and no stored readings exist.
        Showing no values.
      </div>
    );
  }
  return null;
}
