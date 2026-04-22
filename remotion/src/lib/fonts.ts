// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
import { loadFont as loadBlackHanSans } from "@remotion/google-fonts/BlackHanSans";
import { loadFont as loadNotoSansKR } from "@remotion/google-fonts/NotoSansKR";
import { loadFont as loadNotoSansJP } from "@remotion/google-fonts/NotoSansJP";
import { loadFont as loadDoHyeon } from "@remotion/google-fonts/DoHyeon";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

/**
 * Font system for Shorts Naberal Remotion compositions.
 *
 * - Title: BlackHanSans (굵고 임팩트 있는 제목)
 * - Subtitle: DoHyeon (깔끔하고 가독성 좋은 자막)
 * - Body/UI: NotoSansKR (범용 본문, 한국어)
 * - Japanese: NotoSansJP (일본어 채널용)
 * - English: Inter (영어 채널 wildlife/documentary용)
 */

// Note: CJK fonts have 80+ unicode-range subsets — warnings are expected and harmless
export const titleFont = loadBlackHanSans();
export const subtitleFont = loadDoHyeon();
export const bodyFont = loadNotoSansKR("normal", {
  weights: ["400", "700", "900"],
});

// 영어 폰트 — wildlife/documentary 채널에서 fontFamily="Inter" 시 사용
export const englishFont = loadInter("normal", {
  weights: ["400", "700", "900"],
});

// 일본어 폰트 — incidents_jp 채널에서 fontFamily="Noto Sans JP" 시 사용
export const japaneseFont = loadNotoSansJP("normal", {
  weights: ["400", "700", "900"],
});

// 일본어 제목 폰트 — Dela Gothic One (超極太, 범죄/미스터리 인팩트)
// @remotion/google-fonts에 미포함 → staticFile + @font-face로 로드
import { staticFile } from "remotion";
import { continueRender, delayRender } from "remotion";

const jpTitleFontFamily = "Dela Gothic One";
let jpTitleFontLoaded = false;

export function ensureJpTitleFont() {
  if (jpTitleFontLoaded) return;
  const handle = delayRender("Loading Dela Gothic One");
  const font = new FontFace(
    jpTitleFontFamily,
    `url(${staticFile("fonts/DelaGothicOne-Regular.ttf")})`
  );
  font.load().then(() => {
    document.fonts.add(font);
    jpTitleFontLoaded = true;
    continueRender(handle);
  }).catch(() => {
    // Fallback: proceed without custom font
    jpTitleFontLoaded = true;
    continueRender(handle);
  });
}

// 일본어 자막 폰트 — M PLUS Rounded 1c (둥글고 가독성 높음)
const jpSubFontFamily = "M PLUS Rounded 1c";
let jpSubFontLoaded = false;

export function ensureJpSubFont() {
  if (jpSubFontLoaded) return;
  const handle = delayRender("Loading M PLUS Rounded 1c");
  const font = new FontFace(
    jpSubFontFamily,
    `url(${staticFile("fonts/MPLUSRounded1c-Bold.ttf")})`,
    { weight: "700" }
  );
  font.load().then(() => {
    document.fonts.add(font);
    jpSubFontLoaded = true;
    continueRender(handle);
  }).catch(() => {
    jpSubFontLoaded = true;
    continueRender(handle);
  });
}

export { jpTitleFontFamily, jpSubFontFamily };
