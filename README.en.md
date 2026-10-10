# Limbus Company Story Korean Anki Deck【Full Story · English · Audio · Word-by-word】

<div align="center">

[![Releases](https://img.shields.io/badge/Download-Releases-2e6ce6?style=for-the-badge&logo=github)](../../releases/tag/v1.2-en)
[![Issues](https://img.shields.io/badge/Feedback-Issues-ea4aaa?style=for-the-badge&logo=github)](../../issues)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey?style=for-the-badge)](LICENSE)

</div>

> **English edition.** The back of each card uses the **official English** translation.
> A Simplified-Chinese edition is also available — see [Releases](../../releases).

## Intro

An Anki deck for **learning Korean through the story of Limbus Company**: the **entire main story + Interludes + Identity stories**, made into **44,727 cards**.

Each card: **front = the Korean line → back = the English translation + word-by-word gloss + morphemes + dictionary + audio.**

**Completely free** on GitHub. If you see it sold anywhere, it is not authorized.

> Unofficial fan project. Not affiliated with Project Moon, Naver, or the 都市零协会 translation group. All assets belong to their respective owners — see [License](#license).

## Deck content

- Covers the **Prologue + Cantos I–X**, the **Interludes**, and the **Identity stories** — **44,727 cards** total.
- **19 decks**, ordered by story order and named after the chapter:
  `00 Prologue · Selva Oscura`, `01 Canto I · The Outcast` … `10 Canto X · The Gaze Bearing`, `03.5 Interlude I · Hell's Chicken` … `99 Personality`.
- Each **scene code** (e.g. `S101B`) is a tag — filter by tag to study a single scene.

**Card structure**
- **Front**: the Korean line (+ speaker icon)
- **Back**: the English line, **Words** (per-word gloss), **Morphemes** (POS), **Dictionary** (Korean–English), audio
- **Identity stories**: the whole story on one card; front = base-form art, back = Uptie-3 art
- A **source code** at the bottom (e.g. `S101B#3`) for error reports

**Audio**
- Most clips are the **in-game voice**.
- ~800 lines are matched from the game script; the rest are auto-aligned by ASR (similarity ≥0.6 for ~83%) — **some may be mismatched**.
- Dante has no voice in-game (a tick sound is used).

**Dictionary**
- Word glosses come from the **Naver Korean–English dictionary**; verb stems are resolved heuristically, so a few entries may be off.

## Download & install

1. Open [Releases](../../releases/tag/v1.2-en) and download the **English** `.apkg` (about **1.6 GB**).
2. In Anki: `File → Import`.
3. First sync to mobile is slow (lots of audio) — keep Anki in the foreground.

## Known issues

- **Audio**: ~800 lines are script-exact; the rest are ASR-aligned, so a few may be mismatched.
- **Dictionary**: heuristic verb-stem resolution; some entries/POS may be wrong.
- **Identity stories** have no voice (none in the game).

## Feedback

Found a mistake? Open an [Issue](../../issues) and include the **source code** at the bottom of the card (e.g. `S101B#3`).

## Credits

- Story, art, voice: **Project Moon**
- English text: **Project Moon (official localization)**
- Korean–English dictionary: **Naver**
- Morphology: **KoNLPy / Komoran**
- Deck generation: **genanki**

## License

Compiled by hrocfd, under [**CC BY-NC 4.0**](https://creativecommons.org/licenses/by-nc/4.0/) (attribution, non-commercial).

> Story/art/voice © Project Moon; dictionary © Naver. This license only covers the compilation.
