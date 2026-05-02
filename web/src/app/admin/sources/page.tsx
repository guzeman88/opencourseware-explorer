"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchUniversities } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ExternalLink } from "lucide-react";

// ── Static metadata for known sources ────────────────────────────────────────
// "estimated" = total publicly available free courses from that source
const SOURCE_META: Record<
  string,
  { name: string; country: string; estimated: number; url: string; category: string }
> = {
  // ── Original 17 sources ──────────────────────────────────────────────────
  mit_ocw:           { name: "MIT OpenCourseWare",                             country: "USA",         estimated: 2573, url: "https://ocw.mit.edu",                                         category: "University OCW" },
  nptel:             { name: "NPTEL (IIT/IISc)",                               country: "India",       estimated: 3200, url: "https://nptel.ac.in",                                         category: "University OCW" },
  yale:              { name: "Yale Open Yale Courses",                         country: "USA",         estimated: 42,   url: "https://oyc.yale.edu",                                         category: "University OCW" },
  harvard:           { name: "Harvard Online Learning",                        country: "USA",         estimated: 142,  url: "https://pll.harvard.edu/catalog/free",                         category: "University OCW" },
  stanford:          { name: "Stanford Online / SEE",                          country: "USA",         estimated: 130,  url: "https://see.stanford.edu",                                     category: "University OCW" },
  berkeley:          { name: "UC Berkeley",                                    country: "USA",         estimated: 300,  url: "https://www.youtube.com/@UCBerkeley",                          category: "University OCW" },
  princeton:         { name: "Princeton University",                           country: "USA",         estimated: 50,   url: "https://www.youtube.com/@Princeton",                           category: "University OCW" },
  cmu:               { name: "Carnegie Mellon University (CMU)",               country: "USA",         estimated: 60,   url: "https://oli.cmu.edu",                                          category: "University OCW" },
  oxford:            { name: "University of Oxford",                           country: "UK",          estimated: 100,  url: "https://podcasts.ox.ac.uk",                                    category: "University OCW" },
  cambridge:         { name: "University of Cambridge",                        country: "UK",          estimated: 60,   url: "https://www.youtube.com/@Cambridge",                           category: "University OCW" },
  gatech:            { name: "Georgia Institute of Technology",                country: "USA",         estimated: 80,   url: "https://www.youtube.com/@GeorgiaTech",                         category: "University OCW" },
  khan:              { name: "Khan Academy",                                   country: "USA",         estimated: 200,  url: "https://www.khanacademy.org",                                  category: "MOOC / Platform" },
  freecodecamp:      { name: "freeCodeCamp",                                   country: "USA",         estimated: 700,  url: "https://www.freecodecamp.org",                                 category: "YouTube" },
  crashcourse:       { name: "Crash Course",                                   country: "USA",         estimated: 44,   url: "https://www.youtube.com/@crashcourse",                         category: "YouTube" },
  simons:            { name: "Simons Institute for the Theory of Computing",   country: "USA",         estimated: 60,   url: "https://simons.berkeley.edu",                                  category: "Research" },
  "3b1b":            { name: "3Blue1Brown",                                    country: "USA",         estimated: 15,   url: "https://www.youtube.com/@3blue1brown",                         category: "YouTube" },
  mit_youtube:       { name: "MIT (YouTube Channel)",                          country: "USA",         estimated: 150,  url: "https://www.youtube.com/@mitocw",                              category: "University OCW" },

  // ── USA — Traditional OCW ────────────────────────────────────────────────
  tufts:             { name: "Tufts University",                               country: "USA",         estimated: 100,  url: "https://ocw.tufts.edu",                                        category: "University OCW" },
  utah_state:        { name: "Utah State University",                          country: "USA",         estimated: 150,  url: "https://ocw.usu.edu",                                          category: "University OCW" },
  uci:               { name: "UC Irvine OpenCourseWare",                       country: "USA",         estimated: 35,   url: "https://ocw.uci.edu",                                          category: "University OCW" },
  jhsph_ocw:         { name: "Johns Hopkins Bloomberg School of Public Health", country: "USA",        estimated: 80,   url: "https://ocw.jhsph.edu",                                        category: "University OCW" },
  notre_dame:        { name: "University of Notre Dame",                       country: "USA",         estimated: 0,    url: "https://ocw.nd.edu",                                           category: "University OCW" },
  saylor:            { name: "Saylor Academy",                                 country: "USA",         estimated: 400,  url: "https://www.saylor.org",                                       category: "University OCW" },

  // ── USA — MOOC Audit / YouTube ───────────────────────────────────────────
  caltech:           { name: "California Institute of Technology (Caltech)",   country: "USA",         estimated: 30,   url: "https://www.youtube.com/@CalTech",                             category: "YouTube" },
  upenn:             { name: "University of Pennsylvania",                     country: "USA",         estimated: 60,   url: "https://www.coursera.org/upenn",                               category: "MOOC / Platform" },
  duke:              { name: "Duke University",                                country: "USA",         estimated: 45,   url: "https://www.coursera.org/duke",                                category: "MOOC / Platform" },
  umich:             { name: "University of Michigan",                         country: "USA",         estimated: 100,  url: "https://open.umich.edu",                                       category: "MOOC / Platform" },
  ucsd:              { name: "UC San Diego",                                   country: "USA",         estimated: 30,   url: "https://www.edx.org/school/uc-san-diegox",                     category: "MOOC / Platform" },
  uwashington:       { name: "University of Washington",                       country: "USA",         estimated: 40,   url: "https://www.coursera.org/uw",                                  category: "MOOC / Platform" },
  rice:              { name: "Rice University",                                country: "USA",         estimated: 30,   url: "https://www.coursera.org/rice",                                category: "MOOC / Platform" },
  ut_austin:         { name: "University of Texas at Austin",                  country: "USA",         estimated: 30,   url: "https://www.edx.org/school/utaustinx",                         category: "MOOC / Platform" },
  vanderbilt:        { name: "Vanderbilt University",                          country: "USA",         estimated: 30,   url: "https://www.coursera.org/vanderbilt",                          category: "MOOC / Platform" },
  uf:                { name: "University of Florida",                          country: "USA",         estimated: 25,   url: "https://www.coursera.org/uf",                                  category: "MOOC / Platform" },
  purdue:            { name: "Purdue University",                              country: "USA",         estimated: 20,   url: "https://www.edx.org/school/purduex",                           category: "MOOC / Platform" },
  academic_earth:    { name: "Academic Earth",                                 country: "USA",         estimated: 1000, url: "https://academicearth.org",                                    category: "MOOC / Platform" },

  // ── UK ───────────────────────────────────────────────────────────────────
  open_university_uk:{ name: "Open University UK (OpenLearn)",                 country: "UK",          estimated: 1000, url: "https://www.open.edu/openlearn",                               category: "University OCW" },
  edinburgh:         { name: "University of Edinburgh",                        country: "UK",          estimated: 100,  url: "https://www.coursera.org/edinburgh",                           category: "MOOC / Platform" },
  glasgow:           { name: "University of Glasgow",                          country: "UK",          estimated: 30,   url: "https://www.coursera.org/glasgow",                             category: "MOOC / Platform" },

  // ── Australia ─────────────────────────────────────────────────────────────
  unsw:              { name: "UNSW Sydney",                                    country: "Australia",   estimated: 30,   url: "https://www.edx.org/school/unsw",                              category: "MOOC / Platform" },
  umelbourne:        { name: "University of Melbourne",                        country: "Australia",   estimated: 30,   url: "https://www.coursera.org/melbourne",                           category: "MOOC / Platform" },
  anu:               { name: "Australian National University (ANU)",           country: "Australia",   estimated: 20,   url: "https://www.edx.org/school/anux",                              category: "MOOC / Platform" },
};



export default function SourcesAnalysisPage() {
  // Fetch all universities (up to 100)
  const { data, isLoading } = useQuery({
    queryKey: ["admin_sources"],
    queryFn: () => fetchUniversities(1, 100),
  });

  const dbItems = data?.items ?? [];

  // Build a DB lookup by source_key so we can merge with SOURCE_META
  const dbLookup = new Map(dbItems.map((u) => [u.source_key, u]));

  // All known sources from SOURCE_META, merged with DB counts
  const allSources = Object.entries(SOURCE_META).map(([sourceKey, meta]) => ({
    source_key: sourceKey,
    name: meta.name,
    country: meta.country,
    course_count: dbLookup.get(sourceKey)?.course_count ?? 0,
    slug: dbLookup.get(sourceKey)?.slug ?? sourceKey,
    inDb: dbLookup.has(sourceKey),
  }));

  // Compute totals
  const totalInDb = allSources.reduce((s, u) => s + u.course_count, 0);
  const totalEstimated = allSources.reduce(
    (s, u) => s + SOURCE_META[u.source_key].estimated,
    0
  );

  // Group by category
  const byCategory: Record<string, typeof allSources> = {};
  for (const u of allSources) {
    const cat = SOURCE_META[u.source_key].category;
    (byCategory[cat] ??= []).push(u);
  }

  // Sort each category: indexed sources first (by count desc), then unindexed
  for (const cat of Object.keys(byCategory)) {
    byCategory[cat].sort((a, b) => {
      if (a.inDb !== b.inDb) return a.inDb ? -1 : 1;
      return b.course_count - a.course_count;
    });
  }

  const categoryOrder = ["University OCW", "MOOC / Platform", "YouTube", "Research", "Other"];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Sources Analysis</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Coverage overview — how many courses are available per source vs. how many we've indexed
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { label: "Total Sources", value: allSources.length },
          { label: "Indexed Sources", value: allSources.filter((u) => u.inDb).length },
          { label: "Courses in DB", value: totalInDb.toLocaleString() },
          { label: "Est. Available", value: totalEstimated.toLocaleString() },
          {
            label: "Overall Coverage",
            value:
              totalEstimated > 0
                ? `${((totalInDb / totalEstimated) * 100).toFixed(1)}%`
                : "—",
          },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="rounded-lg border border-border bg-card p-4 space-y-1"
          >
            <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">
              {label}
            </p>
            {isLoading ? (
              <div className="h-7 w-20 bg-muted animate-pulse rounded" />
            ) : (
              <p className="text-2xl font-bold tabular-nums">{value}</p>
            )}
          </div>
        ))}
      </div>

      {/* Per-category tables */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-10 bg-muted animate-pulse rounded" />
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          {categoryOrder
            .filter((cat) => byCategory[cat]?.length > 0)
            .map((cat) => {
              const rows = byCategory[cat];
              const catInDb = rows.reduce((s, u) => s + u.course_count, 0);
              const catEst = rows.reduce(
                (s, u) => s + SOURCE_META[u.source_key].estimated,
                0
              );

              return (
                <div key={cat}>
                  {/* Category header */}
                  <div className="flex items-baseline gap-3 mb-2">
                    <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                      {cat}
                    </h2>
                    <span className="text-xs text-muted-foreground">
                      {catInDb.toLocaleString()} / {catEst.toLocaleString()} indexed
                    </span>
                  </div>

                  {/* Table */}
                  <div className="rounded-lg border border-border overflow-hidden">
                    {/* Table header */}
                    <div className="grid grid-cols-[1fr_80px_120px_120px_120px] gap-0 text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-muted/60 border-b border-border">
                      <div className="px-3 py-2">Source</div>
                      <div className="px-3 py-2">Country</div>
                      <div className="px-3 py-2 border-l border-border">Source Key</div>
                      <div className="px-3 py-2 border-l border-border text-right">Courses in DB</div>
                      <div className="px-3 py-2 border-l border-border text-right">Total Available</div>
                    </div>

                    {/* Rows */}
                    {rows.map((u, i) => {
                      const meta = SOURCE_META[u.source_key];
                      const inDb = u.course_count;
                      const est = meta.estimated;

                      return (
                        <div
                          key={u.slug}
                          className={cn(
                            "grid grid-cols-[1fr_80px_120px_120px_120px] gap-0 text-sm border-b border-border/40 last:border-0",
                            i % 2 === 0 ? "bg-background" : "bg-muted/10"
                          )}
                        >
                          {/* Name */}
                          <div className="px-3 py-2.5 flex items-center gap-2 min-w-0">
                            <span className={cn("font-medium truncate", !u.inDb && "text-muted-foreground")}>{u.name}</span>
                            {!u.inDb && (
                              <span className="text-[10px] bg-muted text-muted-foreground px-1 py-0.5 rounded shrink-0">not indexed</span>
                            )}
                            {meta?.url && (
                              <a
                                href={meta.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-muted-foreground hover:text-primary shrink-0"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>

                          {/* Country */}
                          <div className="px-3 py-2.5 text-xs text-muted-foreground">
                            {u.country ?? "—"}
                          </div>

                          {/* Source key */}
                          <div className="px-3 py-2.5 border-l border-border/40">
                            <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                              {u.source_key}
                            </code>
                          </div>

                          {/* In DB */}
                          <div className="px-3 py-2.5 border-l border-border/40 text-right tabular-nums font-medium">
                            {inDb.toLocaleString()}
                          </div>

                          {/* Total available */}
                          <div className="px-3 py-2.5 border-l border-border/40 text-right tabular-nums text-muted-foreground">
                            {est.toLocaleString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
}
