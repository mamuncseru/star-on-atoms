// Custom Typst show-template for the PDF edition.
//
// Quarto's stock orange-book partial never forwards `papersize`, `margin` or
// `fontsize` to the underlying template, so those keys in _quarto.yml are
// silently ignored and the book renders A4 at template defaults with tight
// leading. This partial passes them explicitly and pins the accent colour to
// the same brand blue as the website theme (styles/theme-light.scss).
//
// Geometry matched to the sister volumes: 11pt across a 14.6 cm measure,
// which puts the prose near the classic 65-70 characters per line. The page
// budget in OUTLINE.md is calibrated against exactly this.

#import "@preview/orange-book:0.7.1": book, part, chapter, appendices

#show: book.with(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
$endif$
$if(date)$
  date: "$date$",
$endif$
$if(lang)$
  lang: "$lang$",
$endif$
  paper-size: "us-letter",
  margin: (x: 3.5cm, top: 2.8cm, bottom: 2.5cm),
  font-size: 11pt,
  main-color: rgb("#256abf"),
  // Part-opener contents lists chapters only. At the default depth of 2 the
  // subsection list grows upward and collides with the part title.
  outline-small-depth: 1,
$if(toc-depth)$
  outline-depth: $toc-depth$,
$endif$
$if(quarto.language.crossref-ch-prefix)$
  supplement-chapter: "$quarto.language.crossref-ch-prefix$",
$endif$
)

// Line spacing. Increasing the leading is the one lever that makes long
// technical prose easier to read without narrowing the measure further, and
// it is what stops paragraphs crowding the block that follows them.
#set par(leading: 0.78em, spacing: 1.35em)

// Code set a little smaller than the prose, so a line of 76 characters --
// the house limit enforced by tools/check_code.py -- fits the measure
// without wrapping.
#show raw: set text(size: 9pt)

// Callouts must be able to break across pages. Quarto's stock callout is an
// unbreakable block inside a figure, and a figure is unbreakable too, so a
// callout taller than the space left on its page neither moves nor warns:
// its last rows print on top of one another at the foot of the page. Every
// Rosetta box in Part I did exactly that on its first render, and the row
// count guard in tools/check_structure.py could not see it, because the
// boxes are short in rows and tall in wrapped text. The fix is structural:
// let figures break, and redefine the callout -- after Quarto's definitions,
// before the body that calls it -- with a breakable outer block.
#show figure: set block(breakable: true)

#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"),
             icon: none, icon_color: black,
             body_background_color: white) = {
  block(
    breakable: true,
    fill: background_color,
    stroke: (paint: icon_color, thickness: 0.5pt, cap: "round"),
    width: 100%,
    radius: 2pt,
    block(
      inset: 1pt,
      width: 100%,
      below: 0pt,
      block(
        fill: background_color,
        width: 100%,
        inset: 8pt)[#if icon != none [#text(icon_color, weight: 900)[#icon] ]#title]) +
      if body != [] {
        block(
          inset: 1pt,
          width: 100%,
          block(fill: body_background_color, width: 100%, inset: 8pt, body))
      }
  )
}
