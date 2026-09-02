function Bar({ w, h = "h-3" }: { w: string; h?: string }) {
  return <div className={`${h} ${w} rounded shimmer`} style={{ background: "var(--border)" }} />;
}

export default function Loading() {
  return (
    <div aria-busy="true" aria-label="Loading stories">
      <div className="mb-8 space-y-3.5">
        <Bar w="w-full" h="h-9" />
        <div className="flex gap-4">
          {["w-8", "w-16", "w-14", "w-20", "w-12"].map((w, i) => (
            <Bar key={i} w={w} h="h-4" />
          ))}
        </div>
      </div>

      <div className="space-y-3 pb-7">
        <Bar w="w-40" h="h-3" />
        <Bar w="w-11/12" h="h-8" />
        <Bar w="w-3/4" h="h-8" />
        <div className="pt-1 space-y-1.5">
          <Bar w="w-full" h="h-3.5" />
          <Bar w="w-2/3" h="h-3.5" />
        </div>
      </div>

      <div className="divide-y hairline border-t hairline">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-2.5 py-5">
            <Bar w="w-44" h="h-3" />
            <Bar w={i % 2 ? "w-4/5" : "w-5/6"} h="h-5" />
            <Bar w="w-2/3" h="h-3.5" />
          </div>
        ))}
      </div>
    </div>
  );
}
