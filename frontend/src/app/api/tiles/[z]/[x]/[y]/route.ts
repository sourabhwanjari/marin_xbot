import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest,
  { params }: { params: { z: string; x: string; y: string } }
) {
  const { z, x, y } = params;
  // Strip .png extension if present on y coordinate
  const cleanY = y.replace(/\.png$/, "");

  const apiKey =
    process.env.NEXT_PUBLIC_RAPIDAPI_KEY ||
    process.env.RAPIDAPI_KEY ||
    "e5f367a1d1mshceae8e687637286p187d55jsnab86f1cf2552";

  const apiHost =
    process.env.NEXT_PUBLIC_RAPIDAPI_HOST ||
    process.env.RAPIDAPI_HOST ||
    "maptiles.p.rapidapi.com";

  const targetUrl = `https://${apiHost}/en/map/v1/${z}/${x}/${cleanY}.png`;

  try {
    const res = await fetch(targetUrl, {
      method: "GET",
      headers: {
        "x-rapidapi-host": apiHost,
        "x-rapidapi-key": apiKey,
      },
      // Cache tiles for 24 hours to preserve API quota
      next: { revalidate: 86400 },
    });

    if (!res.ok) {
      // Fallback: If RapidAPI proxy returns error, redirect directly to tile with query param
      const directFallback = `https://${apiHost}/en/map/v1/${z}/${x}/${cleanY}.png?rapidapi-key=${apiKey}`;
      return NextResponse.redirect(directFallback);
    }

    const imageBuffer = await res.arrayBuffer();

    return new NextResponse(imageBuffer, {
      status: 200,
      headers: {
        "Content-Type": "image/png",
        "Cache-Control": "public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800",
        "X-Tile-Provider": "RapidAPI-MapTiles",
      },
    });
  } catch (err) {
    console.error(`[MapTiles Proxy Error] Failed fetching tile ${z}/${x}/${cleanY}:`, err);
    // Direct fallback redirect
    const directFallback = `https://${apiHost}/en/map/v1/${z}/${x}/${cleanY}.png?rapidapi-key=${apiKey}`;
    return NextResponse.redirect(directFallback);
  }
}
