import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "TrueNews · how the press covers the same stories";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#fbfaf7",
          color: "#201e1a",
          padding: "72px 80px",
          fontFamily: "Georgia, serif",
        }}
      >
        <div style={{ display: "flex", gap: 10 }}>
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                width: 26,
                height: 92,
                borderRadius: 5,
                background: i < 3 ? "#ab2213" : "#d9d3c6",
              }}
            />
          ))}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", fontSize: 112, letterSpacing: "-0.03em", lineHeight: 1 }}>
            <span>True</span>
            <span style={{ color: "#ab2213" }}>News</span>
          </div>
          <div style={{ display: "flex", fontSize: 40, color: "#494339", lineHeight: 1.3, maxWidth: 940 }}>
            How the same story reads from one outlet to the next: grouped by event, compared
            across outlets, in 22 countries.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            fontSize: 24,
            color: "#857d6f",
            textTransform: "uppercase",
            letterSpacing: "0.12em",
            borderTopWidth: 2,
            borderTopStyle: "solid",
            borderTopColor: "#d9d3c6",
            paddingTop: 22,
          }}
        >
          Bangladesh · India · Pakistan · UK · USA · and more
        </div>
      </div>
    ),
    size,
  );
}
