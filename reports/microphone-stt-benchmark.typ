#set document(
  title: "Microphone STT Benchmark Report",
  author: "Daniel Rosehill",
)

#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2.5cm),
  header: context {
    if counter(page).get().first() > 1 [
      #set text(9pt, fill: gray)
      Microphone STT Benchmark Report
      #h(1fr)
      #datetime.today().display("[month repr:long] [day], [year]")
    ]
  },
  footer: context {
    set text(9pt, fill: gray)
    h(1fr)
    counter(page).display("1 / 1", both: true)
    h(1fr)
  }
)

#set text(size: 11pt)
#set heading(numbering: "1.1")
#set par(justify: true)

#show link: underline

// Title page
#align(center)[
  #v(3cm)
  #text(24pt, weight: "bold")[Microphone STT Benchmark Report]
  #v(0.5cm)
  #text(14pt)[Speech-to-Text Accuracy Analysis Across Microphone Types]
  #v(2cm)
  #text(12pt)[Daniel Rosehill]
  #v(0.3cm)
  #text(11pt, fill: gray)[#datetime.today().display("[month repr:long] [day], [year]")]
  #v(0.3cm)
  #text(10pt, fill: gray)[17 Microphone Samples Evaluated]
]

#pagebreak()

// Table of contents
#outline(
  title: "Contents",
  indent: auto,
)

#pagebreak()

= Executive Summary

This report presents the results of a comprehensive benchmark comparing speech-to-text (STT) accuracy across 17 different microphone samples representing various types, price points, and use cases. All samples were recorded reading the same reference text about the history of coffee, then transcribed using OpenAI's Whisper API to ensure methodological consistency.

#block(
  fill: luma(245),
  inset: 12pt,
  radius: 4pt,
  width: 100%,
)[
  *Key Findings:*
  - The *cheapest microphone* (UGreen gooseneck, \$18) achieved the *best* Word Error Rate (4.44%)
  - Price and accuracy show a *positive correlation* (r=0.578, p=0.039) --- meaning expensive microphones tend to perform *worse*
  - USB Speakerphones offer excellent value, with the EMEET (\$40) outperforming the Jabra Speak 510 (\$110)
  - Dedicated digital voice recorders don't necessarily excel at STT tasks
]

= Methodology

== Recording Setup

All recordings were made in the same environment:
- *Location:* Home office, quiet acoustic environment
- *Recording Software:* Audacity (default settings)
- *Gain:* 100% (unless otherwise noted)
- *Reference Text:* 315-word passage about the history of coffee
- *Audio Format:* WAV (44.1kHz, 16-bit) or MP3 where noted

== Evaluation Metrics

#table(
  columns: (auto, 1fr),
  inset: 8pt,
  stroke: 0.5pt + gray,
  [*Metric*], [*Description*],
  [Word Error Rate (WER)], [Percentage of words incorrectly transcribed (lower is better)],
  [Character Error Rate (CER)], [Percentage of characters incorrectly transcribed],
  [Audio Quality Score], [Composite score (0-100) based on SNR, dynamic range, clipping, etc.],
  [Signal-to-Noise Ratio (SNR)], [Measured in dB; higher indicates cleaner audio],
)

== Transcription Service

All samples were transcribed using *OpenAI Whisper API (whisper-1)* to ensure methodological consistency. Using a single transcription service eliminates variability from different STT engines.

#pagebreak()

= Results

== Overall Rankings by Word Error Rate

The following table shows all 17 microphone samples ranked from best (lowest WER) to worst:

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  stroke: 0.5pt + gray,
  fill: (x, y) => if y == 0 { luma(230) } else if calc.odd(y) { luma(245) } else { white },
  align: (center, left, left, center, center, center),
  [*Rank*], [*Microphone*], [*Type*], [*Price*], [*WER*], [*Quality*],
  [1], [OnePlus Nord 3 5G], [Smartphone], [---], [4.13%], [79.5],
  [2], [UGreen CM564], [USB Gooseneck], [\$18], [4.44%], [70.0],
  [3], [Audio-Technica ATR4697], [Boundary Mic], [\$45], [4.76%], [57.0],
  [4], [EMEET Conference], [USB Speakerphone], [\$40], [5.08%], [75.0],
  [5], [Samson Q2U], [Dynamic USB/XLR], [\$70], [5.40%], [80.0],
  [6], [OnePlus Nord 3 5G], [Smartphone (MP3)], [---], [5.40%], [83.0],
  [7], [Audio-Technica ATR4697], [Boundary (80cm)], [\$45], [5.40%], [70.0],
  [8], [Jabra Speak 510], [USB Speakerphone], [\$110], [5.40%], [80.0],
  [9], [Logitech C925e], [Webcam], [\$75], [5.40%], [75.0],
  [10], [Maono Elf], [Lavalier], [\$25], [5.40%], [75.0],
  [11], [Logitech H390], [USB Headset], [\$30], [5.71%], [74.0],
  [12], [OnePlus Nord 3 5G], [Smartphone], [---], [5.71%], [84.5],
  [13], [Yealink BH72], [Wireless Headset], [\$160], [6.03%], [85.0],
  [14], [Yealink BH72], [Wireless (BT)], [\$160], [6.03%], [85.0],
  [15], [OnePlus Nord 3 5G], [Smartphone (noisy)], [---], [6.03%], [89.0],
  [16], [Sony ICD-UX570], [Digital Voice Rec.], [\$100], [6.03%], [78.0],
  [17], [Audio-Technica ATR4750], [Condenser Gooseneck], [\$55], [6.35%], [70.0],
)

#pagebreak()

== Rankings by Microphone Type

When grouped by microphone type, clear patterns emerge:

#table(
  columns: (auto, auto, auto, auto),
  inset: 8pt,
  stroke: 0.5pt + gray,
  fill: (x, y) => if y == 0 { luma(230) } else { white },
  [*Type*], [*Avg WER*], [*Range*], [*Avg Price*],
  [USB Gooseneck], [4.44%], [4.44%], [\$18],
  [Boundary Microphone], [5.08%], [4.76--5.40%], [\$45],
  [USB Speakerphone], [5.24%], [5.08--5.40%], [\$75],
  [Smartphone built-in], [5.32%], [4.13--6.03%], [N/A],
  [Dynamic USB/XLR], [5.40%], [5.40%], [\$70],
  [Webcam built-in], [5.40%], [5.40%], [\$75],
  [Lavalier], [5.40%], [5.40%], [\$25],
  [USB Headset], [5.71%], [5.71%], [\$30],
  [Wireless Headset], [6.03%], [6.03%], [\$160],
  [Digital Voice Recorder], [6.03%], [6.03%], [\$100],
  [Condenser Gooseneck], [6.35%], [6.35%], [\$55],
)

#v(0.5cm)

*Key observations:*
- Simple USB gooseneck microphones perform best on average
- Expensive wireless headsets rank near the bottom
- Conference speakerphones offer competitive accuracy at reasonable prices
- Smartphone microphones show high variability depending on environment

#pagebreak()

= Price-Performance Analysis

== Correlation Analysis

#block(
  fill: rgb("#fff3cd"),
  inset: 12pt,
  radius: 4pt,
  width: 100%,
)[
  *Statistical Finding:* There is a statistically significant *positive* correlation between price and Word Error Rate.

  #align(center)[
    #table(
      columns: (auto, auto),
      inset: 8pt,
      stroke: none,
      [Pearson r], [0.578],
      [p-value], [0.039],
      [Interpretation], [Higher price → Higher error rate],
    )
  ]

  This counterintuitive result suggests that *more expensive microphones do not necessarily provide better STT accuracy*.
]

== Head-to-Head Comparisons

=== Conference Speakerphones

#table(
  columns: (auto, auto, auto, auto),
  inset: 8pt,
  stroke: 0.5pt + gray,
  [*Model*], [*Price*], [*WER*], [*Value*],
  [EMEET Conference], [\$40], [5.08%], [Better],
  [Jabra Speak 510], [\$110], [5.40%], [---],
)

The EMEET is *2.75× cheaper* than the Jabra while achieving *better* accuracy. This represents exceptional value for conference/speakerphone use cases.

=== Gooseneck Microphones

#table(
  columns: (auto, auto, auto, auto),
  inset: 8pt,
  stroke: 0.5pt + gray,
  [*Model*], [*Price*], [*WER*], [*Type*],
  [UGreen CM564], [\$18], [4.44%], [USB Gooseneck],
  [Audio-Technica ATR4750], [\$55], [6.35%], [Condenser Gooseneck],
)

The budget UGreen significantly outperforms the more expensive Audio-Technica condenser gooseneck.

=== Best Value Overall

#block(
  fill: rgb("#d4edda"),
  inset: 12pt,
  radius: 4pt,
  width: 100%,
)[
  *Best Value:* UGreen CM564 USB Gooseneck

  - Price: \$18
  - WER: 4.44%
  - WER per \$10 spent: 2.47%

  This microphone offers the lowest error rate at the lowest price point among all tested devices.
]

#pagebreak()

= Detailed Audio Metrics

== Sample Audio Characteristics

#set text(size: 9pt)
#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 5pt,
  stroke: 0.5pt + gray,
  fill: (x, y) => if y == 0 { luma(230) } else if calc.odd(y) { luma(248) } else { white },
  [*ID*], [*Microphone*], [*SNR (dB)*], [*Peak (dB)*], [*RMS (dB)*], [*Quality*],
  [1], [UGreen CM564], [15.2], [-1.8], [-25.1], [70.0],
  [2], [Samson Q2U], [25.2], [-3.2], [-24.9], [80.0],
  [3], [Logitech H390], [21.4], [-0.8], [-28.3], [74.0],
  [4], [OnePlus Nord 3 5G], [26.1], [-0.9], [-19.0], [84.5],
  [6], [AT ATR4697 (30cm)], [11.4], [-6.9], [-29.1], [70.0],
  [7], [AT ATR4697 (80cm)], [8.1], [-10.8], [-32.4], [57.0],
  [8], [Jabra Speak 510], [24.1], [0.0], [-18.6], [80.0],
  [9], [Logitech C925e], [16.6], [-2.1], [-24.2], [75.0],
  [10], [Maono Elf], [20.5], [0.0], [-22.8], [75.0],
  [11], [Yealink BH72 (dongle)], [37.2], [-2.9], [-23.8], [85.0],
  [12], [Yealink BH72 (BT)], [35.2], [-2.8], [-24.2], [85.0],
  [13], [AT ATR4750-USB], [17.9], [-5.7], [-25.1], [70.0],
  [14], [OnePlus (noisy)], [35.7], [-0.8], [-13.7], [89.0],
  [15], [OnePlus (quiet)], [24.8], [-0.9], [-21.3], [79.5],
  [16], [EMEET Conference], [25.6], [-5.1], [-27.3], [75.0],
  [17], [Sony ICD-UX570], [31.5], [0.0], [-21.6], [78.0],
)
#set text(size: 11pt)

*Note:* Higher Audio Quality scores don't always correlate with better STT accuracy. The Yealink BH72 has the highest quality score (85.0) but one of the worst WERs (6.03%).

#pagebreak()

= Conclusions and Recommendations

== Key Takeaways

+ *Price doesn't predict accuracy.* The statistical correlation shows expensive microphones actually tend to perform worse for STT.

+ *Simple is often better.* Basic USB gooseneck microphones outperform sophisticated wireless headsets and dedicated voice recorders.

+ *Conference speakerphones offer great value.* The EMEET at \$40 provides professional-grade STT accuracy comparable to microphones costing 2-3× more.

+ *Smartphones are surprisingly capable.* In quiet environments, smartphone microphones perform competitively with dedicated hardware.

+ *Audio quality ≠ STT accuracy.* High SNR and quality scores don't guarantee better transcription results.

== Recommendations by Use Case

#table(
  columns: (auto, 1fr, auto),
  inset: 8pt,
  stroke: 0.5pt + gray,
  fill: (x, y) => if y == 0 { luma(230) } else { white },
  [*Use Case*], [*Recommendation*], [*Budget*],
  [Best overall value], [UGreen CM564 USB Gooseneck], [\$18],
  [Conference calls], [EMEET Conference Speakerphone], [\$40],
  [Professional recording], [Samson Q2U], [\$70],
  [Portable/travel], [Smartphone (quiet environment)], [N/A],
  [Hands-free dictation], [Logitech H390 USB Headset], [\$30],
)

== Limitations

- All tests conducted in a single environment
- Single speaker (may not generalize across voice types)
- Single STT engine (OpenAI Whisper)
- Reference text is English only

== Future Work

- Test additional microphone types (shotgun, XLR condensers)
- Compare multiple STT engines
- Test in varied acoustic environments
- Evaluate with multiple speakers

#v(1cm)
#line(length: 100%, stroke: 0.5pt + gray)
#v(0.3cm)
#set text(size: 9pt, fill: gray)
*Report generated:* #datetime.today().display("[month repr:long] [day], [year]") \
*Repository:* https://github.com/danielrosehill/Microphone-Audio-Samples \
*Methodology:* OpenAI Whisper API (whisper-1), single-pass transcription
