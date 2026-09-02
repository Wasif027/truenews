"""Per-country source configuration.

A country is *data*, not code: to add one, append a list here, add it to
COUNTRIES, and include its code in the COUNTRIES env var. Keep to outlets with a
genuine native English-language edition.

An outlet can have several feed URLs (section feeds), which are merged and
de-duplicated by article URL. RSS URLs drift and outlets go behind bot
protection — run `python -m app.cli verify-feeds` after editing, and treat any
feed as allowed to fail at runtime (the pipeline logs and skips).

Verified working & fresh as of 2026-09 (22 countries). Some outlets are known to
be flaky from certain IPs (Cloudflare/WAF 403s) but work from others — the
pipeline logs and skips a feed that fails, so a borderline one is left in rather
than dropped. Excluded for good: bdnews24 / Daily Sun (Cloudflare 403), UAE
press (no working English feed found — The National + Arabian Business only,
short of the 3-source bar). Google News per-site RSS gives obfuscated redirect
links that break "read at source", so it's never used.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConfig:
    slug: str
    name: str
    homepage: str
    feeds: tuple[str, ...]


COUNTRIES: dict[str, str] = {
    "bd": "Bangladesh",
    "in": "India",
    "pk": "Pakistan",
    "ng": "Nigeria",
    "ph": "Philippines",
    "uk": "United Kingdom",
    "us": "United States",
    "au": "Australia",
    "ie": "Ireland",
    "sg": "Singapore",
    "my": "Malaysia",
    "ca": "Canada",
    "nz": "New Zealand",
    "za": "South Africa",
    "ke": "Kenya",
    "gh": "Ghana",
    "ug": "Uganda",
    "zw": "Zimbabwe",
    "jp": "Japan",
    "lk": "Sri Lanka",
    "np": "Nepal",
    "jm": "Jamaica",
}

SOURCES: dict[str, list[SourceConfig]] = {
    "bd": [
        SourceConfig(
            "daily-star",
            "The Daily Star",
            "https://www.thedailystar.net",
            (
                "https://www.thedailystar.net/news/bangladesh/rss.xml",
                "https://www.thedailystar.net/business/rss.xml",
                "https://www.thedailystar.net/sports/rss.xml",
                "https://www.thedailystar.net/opinion/rss.xml",
                "https://www.thedailystar.net/entertainment/rss.xml",
            ),
        ),
        SourceConfig(
            "dhaka-tribune",
            "Dhaka Tribune",
            "https://www.dhakatribune.com",
            ("https://www.dhakatribune.com/feed/",),
        ),
        SourceConfig(
            "tbs",
            "The Business Standard",
            "https://www.tbsnews.net",
            (
                "https://www.tbsnews.net/bangladesh/rss.xml",
                "https://www.tbsnews.net/economy/rss.xml",
                "https://www.tbsnews.net/sports/rss.xml",
            ),
        ),
        SourceConfig(
            "prothom-alo-en",
            "Prothom Alo (English)",
            "https://en.prothomalo.com",
            ("https://en.prothomalo.com/stories.rss",),
        ),
        SourceConfig(
            "observer",
            "The Daily Observer",
            "https://www.observerbd.com",
            ("https://www.observerbd.com/rss.php",),
        ),
        SourceConfig("bss", "Bangladesh Sangbad Sangstha", "https://www.bssnews.net",
                     ("https://www.bssnews.net/rss/rss.xml",)),
    ],
    "in": [
        SourceConfig(
            "the-hindu",
            "The Hindu",
            "https://www.thehindu.com",
            (
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "https://www.thehindu.com/news/international/feeder/default.rss",
                "https://www.thehindu.com/business/feeder/default.rss",
                "https://www.thehindu.com/sport/feeder/default.rss",
            ),
        ),
        SourceConfig(
            "indian-express",
            "The Indian Express",
            "https://indianexpress.com",
            (
                "https://indianexpress.com/section/india/feed/",
                "https://indianexpress.com/section/world/feed/",
                "https://indianexpress.com/section/business/feed/",
                "https://indianexpress.com/section/sports/feed/",
            ),
        ),
        SourceConfig(
            "hindustan-times",
            "Hindustan Times",
            "https://www.hindustantimes.com",
            (
                "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
                "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
                "https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml",
            ),
        ),
        SourceConfig(
            "ndtv",
            "NDTV",
            "https://www.ndtv.com",
            (
                "https://feeds.feedburner.com/ndtvnews-top-stories",
                "https://feeds.feedburner.com/ndtvnews-world-news",
            ),
        ),
        SourceConfig(
            "times-of-india",
            "The Times of India",
            "https://timesofindia.indiatimes.com",
            (
                "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
            ),
        ),
        SourceConfig(
            "livemint",
            "Mint",
            "https://www.livemint.com",
            ("https://www.livemint.com/rss/news",),
        ),
        SourceConfig(
            "economic-times",
            "The Economic Times",
            "https://economictimes.indiatimes.com",
            ("https://economictimes.indiatimes.com/rssfeedstopstories.cms",),
        ),
        SourceConfig(
            "business-standard-in",
            "Business Standard",
            "https://www.business-standard.com",
            ("https://www.business-standard.com/rss/home_page_top_stories.rss",),
        ),
        SourceConfig("india-today", "India Today", "https://www.indiatoday.in",
                     ("https://www.indiatoday.in/rss/1206578",)),
        SourceConfig("scroll-in", "Scroll.in", "https://scroll.in",
                     ("https://feeds.feedburner.com/ScrollinArticles.rss",)),
    ],
    "pk": [
        SourceConfig(
            "dawn", "Dawn", "https://www.dawn.com",
            (
                "https://www.dawn.com/feeds/home",
                "https://www.dawn.com/feeds/world",
                "https://www.dawn.com/feeds/business",
                "https://www.dawn.com/feeds/sport",
            ),
        ),
        SourceConfig(
            "express-tribune", "The Express Tribune", "https://tribune.com.pk",
            (
                "https://tribune.com.pk/feed/home",
                "https://tribune.com.pk/feed/world",
                "https://tribune.com.pk/feed/business",
                "https://tribune.com.pk/feed/sports",
            ),
        ),
        SourceConfig(
            "business-recorder", "Business Recorder", "https://www.brecorder.com",
            ("https://www.brecorder.com/feeds/latest-news",),
        ),
        SourceConfig(
            "app-pk", "Associated Press of Pakistan", "https://www.app.com.pk",
            ("https://www.app.com.pk/feed/",),
        ),
        SourceConfig("geo-news", "Geo News", "https://www.geo.tv",
                     ("https://www.geo.tv/rss/1/1",)),
        SourceConfig("the-nation-pk", "The Nation", "https://www.nation.com.pk",
                     ("https://www.nation.com.pk/rss/national",)),
        SourceConfig("ary-news", "ARY News", "https://arynews.tv",
                     ("https://arynews.tv/feed/",)),
    ],
    "ng": [
        SourceConfig("premium-times", "Premium Times", "https://www.premiumtimesng.com",
                     ("https://www.premiumtimesng.com/feed",)),
        SourceConfig("daily-post-ng", "Daily Post", "https://dailypost.ng",
                     ("https://dailypost.ng/feed/",)),
        SourceConfig("channels-tv", "Channels Television", "https://www.channelstv.com",
                     ("https://www.channelstv.com/feed/",)),
        SourceConfig("tribune-ng", "Nigerian Tribune", "https://tribuneonlineng.com",
                     ("https://tribuneonlineng.com/feed/",)),
        SourceConfig("leadership-ng", "Leadership", "https://leadership.ng",
                     ("https://leadership.ng/feed/",)),
        SourceConfig("nairametrics", "Nairametrics", "https://nairametrics.com",
                     ("https://nairametrics.com/feed/",)),
        SourceConfig("vanguard-ng", "Vanguard", "https://www.vanguardngr.com",
                     ("https://www.vanguardngr.com/feed/",)),
        SourceConfig("thisday", "This Day", "https://www.thisdaylive.com",
                     ("https://www.thisdaylive.com/index.php/feed/",)),
        SourceConfig("daily-trust", "Daily Trust", "https://dailytrust.com",
                     ("https://dailytrust.com/feed/",)),
        SourceConfig("businessday-ng", "BusinessDay", "https://businessday.ng",
                     ("https://businessday.ng/feed/",)),
        SourceConfig("sahara-reporters", "Sahara Reporters", "https://saharareporters.com",
                     ("https://saharareporters.com/rss.xml",)),
    ],
    "ph": [
        SourceConfig(
            "inquirer", "Philippine Daily Inquirer", "https://www.inquirer.net",
            (
                "https://newsinfo.inquirer.net/feed",
                "https://globalnation.inquirer.net/feed",
                "https://business.inquirer.net/feed",
            ),
        ),
        SourceConfig(
            "philstar", "The Philippine Star", "https://www.philstar.com",
            (
                "https://www.philstar.com/rss/headlines",
                "https://www.philstar.com/rss/nation",
                "https://www.philstar.com/rss/world",
                "https://www.philstar.com/rss/business",
            ),
        ),
        SourceConfig("rappler", "Rappler", "https://www.rappler.com",
                     ("https://data.rappler.com/feed/",)),
        SourceConfig("manila-times", "The Manila Times", "https://www.manilatimes.net",
                     ("https://www.manilatimes.net/news/feed/",)),
        SourceConfig("mindanews", "MindaNews", "https://mindanews.com",
                     ("https://mindanews.com/feed/",)),
        SourceConfig("businessworld-ph", "BusinessWorld", "https://www.bworldonline.com",
                     ("https://www.bworldonline.com/feed/",)),
        SourceConfig("interaksyon", "Interaksyon", "https://interaksyon.philstar.com",
                     ("https://interaksyon.philstar.com/feed/",)),
    ],
    "uk": [
        SourceConfig("bbc", "BBC News", "https://www.bbc.co.uk/news",
                     ("https://feeds.bbci.co.uk/news/rss.xml",)),
        SourceConfig("guardian", "The Guardian", "https://www.theguardian.com",
                     ("https://www.theguardian.com/uk/rss",)),
        SourceConfig("independent", "The Independent", "https://www.independent.co.uk",
                     ("https://www.independent.co.uk/news/uk/rss",)),
        SourceConfig("sky-news", "Sky News", "https://news.sky.com",
                     ("https://feeds.skynews.com/feeds/rss/home.xml",)),
        SourceConfig("mirror", "The Mirror", "https://www.mirror.co.uk",
                     ("https://www.mirror.co.uk/news/?service=rss",)),
        SourceConfig("telegraph", "The Telegraph", "https://www.telegraph.co.uk",
                     ("https://www.telegraph.co.uk/rss.xml",)),
        SourceConfig("evening-standard", "Evening Standard", "https://www.standard.co.uk",
                     ("https://www.standard.co.uk/news/rss",)),
        SourceConfig("inews", "The i Paper", "https://inews.co.uk",
                     ("https://inews.co.uk/feed",)),
        SourceConfig("express-uk", "Daily Express", "https://www.express.co.uk",
                     ("https://www.express.co.uk/posts/rss/1/news",)),
        SourceConfig("metro-uk", "Metro", "https://metro.co.uk",
                     ("https://metro.co.uk/feed/",)),
    ],
    "us": [
        SourceConfig("npr", "NPR", "https://www.npr.org",
                     ("https://feeds.npr.org/1001/rss.xml",)),
        SourceConfig("politico", "Politico", "https://www.politico.com",
                     ("https://rss.politico.com/politics-news.xml",)),
        SourceConfig("the-hill", "The Hill", "https://thehill.com",
                     ("https://thehill.com/news/feed/",)),
        SourceConfig("abc-news", "ABC News", "https://abcnews.go.com",
                     ("https://abcnews.go.com/abcnews/topstories",)),
        SourceConfig("axios", "Axios", "https://www.axios.com",
                     ("https://www.axios.com/feeds/feed.rss",)),
        SourceConfig("cbs-news", "CBS News", "https://www.cbsnews.com",
                     ("https://www.cbsnews.com/latest/rss/main",)),
        SourceConfig("fox-news", "Fox News", "https://www.foxnews.com",
                     ("https://moxie.foxnews.com/google-publisher/latest.xml",)),
        SourceConfig("ap-news", "Associated Press", "https://apnews.com",
                     ("https://feedx.net/rss/ap.xml",)),
        SourceConfig("guardian-us", "The Guardian (US)", "https://www.theguardian.com",
                     ("https://www.theguardian.com/us-news/rss",)),
        SourceConfig("nbc-news", "NBC News", "https://www.nbcnews.com",
                     ("https://feeds.nbcnews.com/nbcnews/public/news",)),
        SourceConfig("newsweek", "Newsweek", "https://www.newsweek.com",
                     ("https://www.newsweek.com/rss",)),
        SourceConfig("pbs-newshour", "PBS NewsHour", "https://www.pbs.org/newshour",
                     ("https://www.pbs.org/newshour/feeds/rss/headlines",)),
    ],
    "au": [
        SourceConfig("abc-au", "ABC News (Australia)", "https://www.abc.net.au/news",
                     ("https://www.abc.net.au/news/feed/2942460/rss.xml",)),
        # SMH and The Age share Nine Entertainment's newsroom and run near-identical
        # national copy, so carrying both just double-counts one outlet's framing
        # (it inflated 71 of 73 AU "multi-source" stories with no real 2nd source).
        SourceConfig("smh", "The Sydney Morning Herald", "https://www.smh.com.au",
                     ("https://www.smh.com.au/rss/feed.xml",)),
        SourceConfig("guardian-au", "The Guardian (Australia)", "https://www.theguardian.com",
                     ("https://www.theguardian.com/australia-news/rss",)),
        SourceConfig("7news-au", "7NEWS", "https://7news.com.au",
                     ("https://7news.com.au/news/feed",)),
        SourceConfig("sbs-news", "SBS News", "https://www.sbs.com.au/news",
                     ("https://www.sbs.com.au/news/topic/latest/feed",)),
        SourceConfig("conversation-au", "The Conversation (AU)", "https://theconversation.com/au",
                     ("https://theconversation.com/au/articles.atom",)),
    ],
    "ie": [
        SourceConfig("irish-times", "The Irish Times", "https://www.irishtimes.com",
                     ("https://www.irishtimes.com/cmlink/news-1.1319192",)),
        SourceConfig("rte", "RTÉ News", "https://www.rte.ie/news",
                     ("https://www.rte.ie/feeds/rss/?index=/news/",)),
        SourceConfig("irish-independent", "Irish Independent", "https://www.independent.ie",
                     ("https://www.independent.ie/rss/",)),
        SourceConfig("the-journal", "TheJournal.ie", "https://www.thejournal.ie",
                     ("https://www.thejournal.ie/feed/",)),
        SourceConfig("irish-mirror", "Irish Mirror", "https://www.irishmirror.ie",
                     ("https://www.irishmirror.ie/news/?service=rss",)),
        SourceConfig("newstalk", "Newstalk", "https://www.newstalk.com",
                     ("https://www.newstalk.com/feed",)),
    ],
    "sg": [
        SourceConfig(
            "straits-times", "The Straits Times", "https://www.straitstimes.com",
            (
                "https://www.straitstimes.com/news/singapore/rss.xml",
                "https://www.straitstimes.com/news/world/rss.xml",
                "https://www.straitstimes.com/news/business/rss.xml",
            ),
        ),
        SourceConfig("cna", "CNA", "https://www.channelnewsasia.com",
                     ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",)),
        SourceConfig("mothership", "Mothership", "https://mothership.sg",
                     ("https://mothership.sg/feed/",)),
        SourceConfig("independent-sg", "The Independent Singapore", "https://theindependent.sg",
                     ("https://theindependent.sg/feed/",)),
        SourceConfig("business-times-sg", "The Business Times", "https://www.businesstimes.com.sg",
                     ("https://www.businesstimes.com.sg/rss/top-stories",)),
        SourceConfig("mustsharenews", "MS News", "https://mustsharenews.com",
                     ("https://mustsharenews.com/feed/",)),
    ],
    "my": [
        SourceConfig("malay-mail", "Malay Mail", "https://www.malaymail.com",
                     ("https://www.malaymail.com/feed/rss/malaysia",)),
        SourceConfig("fmt", "Free Malaysia Today", "https://www.freemalaysiatoday.com",
                     ("https://www.freemalaysiatoday.com/feed/",)),
        SourceConfig("malaysiakini", "Malaysiakini", "https://www.malaysiakini.com",
                     ("https://www.malaysiakini.com/rss/en/news.rss",)),
        SourceConfig("nst-my", "New Straits Times", "https://www.nst.com.my",
                     ("https://www.nst.com.my/feed",)),
        SourceConfig("the-sun-my", "The Sun", "https://thesun.my",
                     ("https://thesun.my/rss",)),
        SourceConfig("the-vibes-my", "The Vibes", "https://www.thevibes.com",
                     ("https://www.thevibes.com/rss",)),
    ],
    "ca": [
        SourceConfig("cbc", "CBC News", "https://www.cbc.ca/news",
                     ("https://www.cbc.ca/webfeed/rss/rss-topstories",
                      "https://www.cbc.ca/webfeed/rss/rss-world")),
        SourceConfig("global-news", "Global News", "https://globalnews.ca",
                     ("https://globalnews.ca/feed/",)),
        SourceConfig("national-post", "National Post", "https://nationalpost.com",
                     ("https://nationalpost.com/feed/",)),
        SourceConfig("ctv-news", "CTV News", "https://www.ctvnews.ca",
                     ("https://www.ctvnews.ca/arc/outboundfeeds/rss/",)),
        SourceConfig("toronto-sun", "Toronto Sun", "https://torontosun.com",
                     ("https://torontosun.com/feed",)),
    ],
    "nz": [
        SourceConfig("nz-herald", "The New Zealand Herald", "https://www.nzherald.co.nz",
                     ("https://www.nzherald.co.nz/arc/outboundfeeds/rss/section/nz/?outputType=xml",)),
        SourceConfig("stuff-nz", "Stuff", "https://www.stuff.co.nz",
                     ("https://www.stuff.co.nz/rss",)),
        SourceConfig("newsroom-nz", "Newsroom", "https://www.newsroom.co.nz",
                     ("https://www.newsroom.co.nz/feed",)),
        SourceConfig("rnz", "RNZ", "https://www.rnz.co.nz",
                     ("https://www.rnz.co.nz/rss/national.xml",)),
    ],
    "za": [
        SourceConfig("iol", "IOL", "https://www.iol.co.za",
                     ("https://www.iol.co.za/rss",)),
        SourceConfig("sabc-news", "SABC News", "https://www.sabcnews.com",
                     ("https://www.sabcnews.com/sabcnews/feed/",)),
        SourceConfig("daily-maverick", "Daily Maverick", "https://www.dailymaverick.co.za",
                     ("https://www.dailymaverick.co.za/dmrss/",)),
        SourceConfig("moneyweb", "Moneyweb", "https://www.moneyweb.co.za",
                     ("https://www.moneyweb.co.za/feed/",)),
        SourceConfig("news24", "News24", "https://www.news24.com",
                     ("https://www.news24.com/news24/rss",)),
    ],
    "ke": [
        SourceConfig("standard-ke", "The Standard", "https://www.standardmedia.co.ke",
                     ("https://www.standardmedia.co.ke/rss/headlines.php",)),
        SourceConfig("capital-fm-ke", "Capital FM", "https://www.capitalfm.co.ke",
                     ("https://www.capitalfm.co.ke/news/feed/",)),
        SourceConfig("tuko", "Tuko", "https://www.tuko.co.ke",
                     ("https://www.tuko.co.ke/rss/all.rss",)),
        SourceConfig("nation-ke", "Nation", "https://nation.africa",
                     ("https://www.nation.co.ke/kenya/rss",)),
    ],
    "gh": [
        SourceConfig("myjoyonline", "MyJoyOnline", "https://www.myjoyonline.com",
                     ("https://www.myjoyonline.com/feed/",)),
        SourceConfig("3news-gh", "3News", "https://3news.com",
                     ("https://3news.com/feed/",)),
        SourceConfig("adomonline", "Adom Online", "https://www.adomonline.com",
                     ("https://www.adomonline.com/feed/",)),
        SourceConfig("starrfm-gh", "Starr FM", "https://starrfm.com.gh",
                     ("https://starrfm.com.gh/feed/",)),
    ],
    "ug": [
        SourceConfig("nile-post", "Nile Post", "https://nilepost.co.ug",
                     ("https://nilepost.co.ug/feed",)),
        SourceConfig("independent-ug", "The Independent", "https://www.independent.co.ug",
                     ("https://www.independent.co.ug/feed/",)),
        SourceConfig("pml-daily", "PML Daily", "https://pmldaily.com",
                     ("https://pmldaily.com/feed",)),
        SourceConfig("observer-ug", "The Observer", "https://observer.ug",
                     ("https://observer.ug/rss",)),
        SourceConfig("softpower-ug", "SoftPower News", "https://www.softpower.ug",
                     ("https://www.softpower.ug/feed/",)),
    ],
    "zw": [
        SourceConfig("newsday-zw", "NewsDay", "https://www.newsday.co.zw",
                     ("https://www.newsday.co.zw/feed",)),
        SourceConfig("newzimbabwe", "New Zimbabwe", "https://www.newzimbabwe.com",
                     ("https://www.newzimbabwe.com/feed/",)),
        SourceConfig("zimeye", "ZimEye", "https://www.zimeye.net",
                     ("https://www.zimeye.net/feed/",)),
        SourceConfig("263chat", "263Chat", "https://www.263chat.com",
                     ("https://263chat.com/feed/",)),
    ],
    "jp": [
        SourceConfig("japan-times", "The Japan Times", "https://www.japantimes.co.jp",
                     ("https://www.japantimes.co.jp/feed/",)),
        SourceConfig("mainichi", "The Mainichi", "https://mainichi.jp/english",
                     ("https://mainichi.jp/rss/etc/english_latest.rss",)),
        SourceConfig("japan-today", "Japan Today", "https://japantoday.com",
                     ("https://japantoday.com/feed",)),
        SourceConfig("nhk-world", "NHK World-Japan", "https://www3.nhk.or.jp/nhkworld/en/news",
                     ("https://www3.nhk.or.jp/nhkworld/en/news/feeds/all.xml",)),
    ],
    "lk": [
        SourceConfig("ada-derana", "Ada Derana", "https://www.adaderana.lk",
                     ("https://www.adaderana.lk/rss.php",)),
        SourceConfig("the-island-lk", "The Island", "https://island.lk",
                     ("https://island.lk/feed/",)),
        SourceConfig("economynext", "EconomyNext", "https://economynext.com",
                     ("https://economynext.com/feed",)),
        SourceConfig("newswire-lk", "NewsWire", "https://www.newswire.lk",
                     ("https://www.newswire.lk/feed/",)),
    ],
    "np": [
        SourceConfig("kathmandu-post", "The Kathmandu Post", "https://kathmandupost.com",
                     ("https://kathmandupost.com/rss",)),
        SourceConfig("online-khabar-en", "Online Khabar", "https://english.onlinekhabar.com",
                     ("https://english.onlinekhabar.com/feed",)),
        SourceConfig("nepali-times", "Nepali Times", "https://www.nepalitimes.com",
                     ("https://www.nepalitimes.com/feed",)),
    ],
    "jm": [
        SourceConfig("jamaica-gleaner", "Jamaica Gleaner", "https://jamaica-gleaner.com",
                     ("https://jamaica-gleaner.com/feed/rss.xml",)),
        SourceConfig("jamaica-observer", "Jamaica Observer", "https://www.jamaicaobserver.com",
                     ("https://www.jamaicaobserver.com/feed/",)),
        SourceConfig("nationwide-jm", "Nationwide News Network", "https://nationwideradiojm.com",
                     ("https://nationwideradiojm.com/feed/",)),
    ],
}


def sources_for(country: str) -> list[SourceConfig]:
    if country not in SOURCES:
        raise KeyError(f"No source config for country {country!r}. Known: {list(SOURCES)}")
    return SOURCES[country]
