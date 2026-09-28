# GBU-39 / DiamondBack wing reference correction

2026-09-23. Research for visual game-asset accuracy. K remains rejected.
2026-09-24 follow-up: L/Joined Wing R1 is a built `cad-review` replacement study;
see `JOINED_WING_R1_CONTRACT.md`. J/R7 body remains the local baseline.

## Finding

K/Wing Prototype R1 is rejected as the GBU-39-inspired mechanism. It modeled one
unconnected panel rotating around a fixed roof pin. Passing its own envelope
and collision tests did not establish reference fidelity. Do not repeat or
detail that mechanism as the Phantom's selected wing architecture.

MBDA identifies the GBU-39/B's DiamondBack system as a **joined tandem wing**
that expands from compact stowage to a diamond-shaped deployed platform.
Directly inspected manufacturer imagery shows forward and rear lifting panels
joined outboard, with roots at different longitudinal positions on a central
wing-kit housing. The resulting open areas between panels are a major visual
feature missing from K.

## Source ledger

1. **Primary — MBDA product page**, fetched and read:
   https://mbdainc.com/products/diamond-back/
   Explicitly identifies joined tandem architecture, compact stowage,
   diamond-shaped deployed platform and use on GBU-39/B. Does not document
   production hinge axes, exact sequencing or internal actuation.

2. **Primary — MBDA 2019 two-page data sheet**, both text and page images read:
   https://mbdainc.com/wp-content/uploads/2020/07/2019-Diamond-Back-Wing-Kit-Product-Data-Sheet.pdf
   Page 1 confirms joined tandem architecture and shows the complete joined
   deployed arrangement. Page 2 includes a compact/partly opened kit image
   showing paired forward roots and the long central housing. It is a still,
   not a timed deployment sequence. Its dimensions are reference context only,
   not Phantom dimensions. Local inspection copy:
   `C:/Users/erena/AppData/Local/Temp/opencode/mbda-diamond-back-2019.pdf`.

3. **Primary — MBDA illustrated product overview**, one-page image inspected:
   https://mbdainc.com/wp-content/uploads/2017/10/MBDA-Diamond-Back-Wing-Kit.pdf
   Clearly shows the forward/rear panels meeting outboard and the dorsal
   housing; text states deployment after launch and symmetrical deployment.
   Local inspection copy:
   `C:/Users/erena/AppData/Local/Temp/opencode/mbda-diamond-back-wing-overview.pdf`.

4. **Secondary — GlobalSecurity Diamond Back overview**, fetched and read:
   https://www.globalsecurity.org/military/systems/munitions/diamond-back.htm
   Explicitly describes extension by rearward movement of a carriage to which
   the rear wings attach. This is a historical family-level account covering
   JDAM/SSB development; treat carriage-driven deployment as supported at that
   level, not proof of every production GBU-39 detail.

5. **Visual corroboration — USAF-attributed illustration on Wikimedia**, actual
   image fetched and directly inspected:
   https://commons.wikimedia.org/wiki/File:Boeing_GBU-39_Small_Diameter_Bomb.jpg
   https://upload.wikimedia.org/wikipedia/commons/4/42/Boeing_GBU-39_Small_Diameter_Bomb.jpg
   Confirms the visible joined arrangement, swept fore/rear panels and open
   triangular spaces beside the central housing. Illustration, not motion footage.

6. **Video lead, not reviewed:** MBDAInc's "Diamond Back Wing Kit":
   https://vimeo.com/513430938
   Search identified title/uploader; page returned human verification. No video
   frames or timing were inspected. Do not claim the video verifies sequencing.

## Corrected understanding

- The full lifting assembly is the reference unit. Treating a lone hinged
  panel as a faithful mechanism prototype omitted the defining coupled structure.
- Forward and rear panels form joined lateral assemblies; the central module
  has separated root locations. The diamond-like outline and its negative
  spaces must be judged in deployed views.
- The published family-level mechanism combines longitudinal carriage travel
  with linked panel rotation. It cannot be represented by rotating a rigid
  standalone wing through 90 degrees around one stationary roof pivot.
- Compact stowage must account for both members on each side, the outboard
  connection and the dorsal kit housing, not just one panel lying on the roof.

## What remains unverified

Exact production pivot-axis orientations, carriage stroke, panel layering,
actuator/locking details and frame-by-frame deployment sequence. Do not fill
these gaps with unlabelled assumptions. Do not import GBU-53/StormBreaker or
generic swing-wing imagery as evidence for GBU-39. One attempted generic SDB
article redirected to SDB II and was excluded from the mechanism findings.
The attempted Boeing product-card link returned 404. A speculative Moog
literature lead failed; no Moog attribution is supported. Google/Bing results
were unhelpful; DuckDuckGo led to the MBDA sources above.

## Consequence for the next visual study

Prototype the **joined wing module**, with recognizable forward/rear panels,
outboard joints and longitudinal housing/carriage relationship. Present matched
stowed, intermediate and deployed arrangements and label any motion inferred
for the fictional adaptation. Seek approval of that module before propagation
or detailing. Phantom remains an original 2.8 m game asset under its own
250 mm stowed envelope; real-reference dimensions do not replace those limits.

No replacement CAD was built in this research pass. Historical K files stay
available as rejected experiments. Their geometry checks are not reference
acceptance; body symmetry findings remain valid and unaffected.
