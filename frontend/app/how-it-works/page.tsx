export const metadata = { title: "How it works" };

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="font-display mb-2 text-[1.35rem] leading-tight">{title}</h2>
      <p className="max-w-[64ch] text-[0.95rem] leading-[1.7]" style={{ color: "var(--fg-soft)" }}>
        {children}
      </p>
    </section>
  );
}

export default function HowItWorks() {
  return (
    <div className="reveal mx-auto max-w-[44rem]">
      <span className="kicker">In plain terms</span>
      <h1 className="font-display mt-2 text-[2.25rem] leading-tight">How TrueNews works</h1>
      <p className="mt-3 max-w-[60ch] text-[1.05rem] leading-relaxed" style={{ color: "var(--fg-soft)" }}>
        The idea is simple: take one news event, put every outlet&rsquo;s version of it side by
        side, and let you see how the coverage changes from one paper to the next. TrueNews never
        decides whether a story is true &mdash; only how it is being told.
      </p>

      <div className="mt-10 space-y-9">
        <Section title="Where the news comes from">
          About once an hour, TrueNews checks the public news feeds of the outlets it tracks in each
          country and pulls in anything new &mdash; the headline, the first paragraph, and a link
          back to the full article. It doesn&rsquo;t keep the whole article; for the full piece you
          click through to the outlet.
        </Section>

        <Section title="How articles become one “story”">
          When several articles are clearly about the same event &mdash; the same flood, the same
          match, the same election result &mdash; TrueNews groups them into a single story. It works
          this out by comparing the wording of the headlines and spotting the ones that are really
          describing the same thing. Stories keep collecting new articles for about three days, then
          drop off the feed.
        </Section>

        <Section title="The summary and the coverage comparison">
          For each story you get a short, plain recap, a one-line note on the biggest way the
          coverage differs, and &mdash; where the write-up model is switched on &mdash; a longer
          walk-through of how each outlet handled it: who led with what, who emphasised or
          buried an angle, who included a quote the others dropped. To write that, TrueNews
          reads each outlet&rsquo;s full article once, uses it, and discards it &mdash; the full
          text is never stored. Nothing is invented, and it never says which outlet got it right.
        </Section>

        <Section title="Compare (when you paste your own links)">
          The <em>Compare</em> page is the one place TrueNews reads full articles you choose. Paste
          two or more links about the same event and it fetches each page, pulls out the body text,
          and asks the write-up model to lay the versions side by side: the account they share,
          where they agree, where they diverge, and &mdash; for each one &mdash; how it is angled,
          measured against plain wire-service style rather than against the other links you pasted.
          So if every article you give it leans the same way, it says so and names what is missing,
          instead of calling the least slanted one &ldquo;neutral&rdquo;. Every lean label comes
          with the quotes from that article it rests on. It describes one story as told by one
          outlet on one day, not a standing verdict on the outlet, and the fetched text is dropped
          as soon as the comparison is written. Comparisons draw on a shared free-tier model, so
          there&rsquo;s an hourly limit &mdash; Compare also has a &ldquo;use your own API
          key&rdquo; option that runs on your own account instead, kept only in your browser and
          sent for that one request.
        </Section>

        <Section title="“4 of 8 outlets covered this”">
          A head count of how many <em>independent</em> newsrooms ran the story. When two mastheads
          publish the same wire copy or the same group&rsquo;s national article word for word, that
          counts once, not twice &mdash; the point is how many separate takes exist. If only one
          outlet picked something up, the story is still shown, but marked &ldquo;not yet
          corroborated&rdquo;.
        </Section>

        <Section title="The highlighted words">
          On every story, TrueNews marks words in the original headlines that lean emotional or
          loaded &mdash; &ldquo;slams&rdquo;, &ldquo;chaos&rdquo;, &ldquo;humiliation&rdquo;, rows
          of exclamation marks. That part is a straightforward word check, not a political-bias
          meter. The reasoned lean read &mdash; the one that will say an article &ldquo;amplifies
          the government line&rdquo; &mdash; only ever runs on the <em>Compare</em> page, on links
          you choose, and always shows the quotes behind the call.
        </Section>

        <Section title="What it deliberately doesn’t do">
          It doesn&rsquo;t fact-check, rate, or rank outlets, and it doesn&rsquo;t tell you what to
          think. It shows you the spread of coverage and sends you to the originals so you can judge
          for yourself.
        </Section>
      </div>
    </div>
  );
}
