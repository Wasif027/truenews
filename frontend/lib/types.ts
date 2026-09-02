export type Outlet = {
  slug: string;
  name: string;
  homepage: string;
};

export type SourceArticle = {
  id: number;
  outlet: Outlet;
  url: string;
  headline: string;
  byline: string | null;
  published_at: string;
  is_first: boolean;
  flagged_sentences: string[];
};

export type StoryListItem = {
  id: number;
  title: string;
  country: string; // display name, e.g. "Bangladesh"
  categories: string[]; // 1 or 2, most prominent first
  summary: string | null;
  outlet_count: number;
  article_count: number;
  is_single_source: boolean;
  first_reported_by: Outlet | null;
  first_reported_at: string | null;
  updated_at: string;
  hotness: number;
};

export type StoryDetail = StoryListItem & {
  coverage_diff: string | null;
  coverage_detail: string | null;
  coverage: { reported: string[]; not_reporting: string[] };
  sources: SourceArticle[];
};

export type User = { username: string };

export type CategoryCount = { category: string; count: number };

export type Status = {
  country: string;
  outlets: number;
  articles: number;
  stories: number;
  last_story_update: string | null;
  window_hours: number;
  sim_threshold: number;
  llm_enabled: boolean;
};
