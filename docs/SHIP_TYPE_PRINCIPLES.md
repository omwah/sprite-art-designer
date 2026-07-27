# Ship Type Design Principles and Media Touchstones

## Purpose

This document defines the visual identity of every ship role currently shipped
with Edge Art Designer. It complements
[`SHIP_DESIGN_PRINCIPALS.md`](SHIP_DESIGN_PRINCIPALS.md), which explains the
shared procedural-art system. The shared document answers *how ships are
authored and rendered*; this document answers *what each ship type should look
and feel like*.

The media references below are **touchstones, not templates**. They identify a
useful visual idea—an exposed engine, a lived-in cargo spine, a fortress prow,
or an organic carapace. New art should combine those ideas with the ship's own
section grammar and the terminal-art constraints. It should not reproduce a
copyrighted silhouette, emblem, or arrangement of signature details.

## Shared visual language

All twelve types obey the same foundation:

- **Role must survive recoloring.** The silhouette and structural rhythm must
  communicate function before an archetype palette is applied.
- **The ship reads from drive to intent.** Horizontal art is authored
  tail-to-nose and canonically faces right. Engines establish the tail; sensors,
  screens, landing gear, or weapons establish the bow.
- **Length comes from the middle.** Repeatable cargo, hull, radiator, weapon, or
  habitat sections grow the ship. Engines and prows remain recognizable caps.
- **Vertical art is a real view.** It preserves the same functional order but is
  independently authored, not rotated at runtime.
- **Each tier is a deliberate symbol.** Full, medium, and compact tiers express
  the same role with progressively fewer details. Compact art is an emblematic
  restatement, not a cropped full-detail ship.
- **Glyph and mask have different jobs.** Shaded glyphs describe mass, bevel,
  and recess. Facet glyphs describe small surface features. The parallel color
  mask identifies Surface, Engine, Beacon, Window, Weapons, or Defensive
  function.
- **Asymmetry gives direction and history.** A mast, pod, repair, gun, or uneven
  plate can make a hull feel operated rather than diagrammatic. The finished
  ship must still reflect cleanly for the opposite facing.

## Role comparison

| Ship type | Immediate read | Repeatable visual rhythm | Primary contrast |
|---|---|---|---|
| Fighter | Fast, fragile interceptor | Narrow fuselage | Swept drive versus pointed gun nose |
| Transport | Boxy general-purpose carrier | Container bays | Broad cargo mass versus token armament |
| Warship | Purpose-built combatant | Armored spine | Dense centerline gun and screened prow |
| Capital Warship | Command-scale fleet anchor | Layered heavy hull | Tall superstructure and massive extremities |
| Needle Picket | Long-range patrol and detection | Sensor-ribbed spine | Exposed drive nodes and oversized sensor bow |
| Falsehold Raider | Merchant silhouette hiding violence | False cargo seams | Familiar freighter body and concealed battery |
| Junction Pinnace | Tiny courier and landing craft | Short cabin | Overpowered drive and blunt landing nose |
| Radiant Lance | Elegant high-energy combat ship | Folding radiator diamonds | Fine luminous spine and long lance |
| Hearth Freighter | Old, inhabited working transport | Patched cargo modules | Industrial drive and conspicuous habitat drum |
| Pearl Shell | Alien troop carrier | Recessed weapon ring | Layered carapace and protected troop lobe |
| Marrow Dart | Grown assault organism | Bound spars and muscle bands | Sinew drive and hardened beak |
| Broadside Citadel | Fortress linebreaker | Lateral battery decks | Repeated broadsides and command keep |

## Fighter

### Core fantasy

The Fighter is acceleration wrapped around one pilot, a compact hull, and a
forward weapon. It should feel eager to move even while stationary. Its visual
story is not endurance or cargo capacity; it is a short path from engine thrust
to target.

### Silhouette and section grammar

The full ship follows **Thrusters → Spindrive → Hull → Screens → Main Gun**.
The engine and drive sections are relatively wide for the amount of hull they
push. The repeatable fuselage stays thin so additional length reads as a longer
interceptor, not as new internal volume. A small screened or cockpit-like
section interrupts the line immediately before an asymmetrical pointed nose.
The top and bottom contours should sweep inward toward that nose.

The fighter's negative space matters. Empty rows above and below the centerline
make its few solid cells feel fast and light. Avoid filling those rows merely
because the full tier has room available.

### Scale and color intent

At medium scale, preserve the engine flare, narrow waist, and pointed weapon.
At compact scale, the minimum statement is glow, a thin body band, and a muzzle.
Engine masks may occupy a larger percentage of visible ink than on any heavy
ship. Weapons color should remain a sharp forward accent; defensive and window
accents should not turn the craft into a multicolored ornament.

### Media touchstones

- The **X-wing** from *Star Wars* demonstrates how engine placement and a
  converging attack silhouette communicate speed without motion.
- The **Colonial Viper** from *Battlestar Galactica* demonstrates the
  engine-heavy tail, narrow pilot volume, and dart-like nose.
- Fighters in *Wing Commander* demonstrate how a small set of exaggerated
  features can separate combat roles at icon and HUD scale.

Borrow the clarity of those proportions, not their exact wing counts or hull
outlines.

### Avoid

Do not broaden the repeatable hull into cargo bays, add a capital-style bridge,
or make the screens larger than the drive. A fighter that reads as a shuttle or
miniature cruiser has lost its purpose.

## Transport

### Core fantasy

The Transport is a dependable machine whose payload determines its length. It
is deliberately less romantic than a fighter and less threatening than a
warship. Its interest comes from modular structure: doors, frames, container
seams, braces, and occasional service hardware.

### Silhouette and section grammar

The familiar five-part grammar remains **Thrusters → Spindrive → Hull →
Screens → Main Gun**, but the repeatable Hull dominates. Box-drawing glyphs
frame discrete cargo bays, and the upper and lower contours remain comparatively
flat. The drive is broad enough to plausibly move the mass. Screens form a slim
transition to a stubby command or utility prow; the main gun is intentionally a
token defensive fit rather than a spinal weapon.

The visual rhythm should be easy to count. Repetition communicates capacity:
one bay is a local hauler, many bays are a long-haul carrier. Variants may change
paneling, external rails, or service fittings without obscuring that rhythm.

### Scale and color intent

Medium art should retain visible bay boundaries. Compact art may collapse each
bay into a heavy block, but the center must remain broader than the engine and
nose. Windows should be manually clustered around the forward control area,
not scattered across sealed cargo. Engine color belongs aft; Weapons and
Defensive masks should be restrained.

### Media touchstones

- The **Nostromo** from *Alien* supplies the sense of an industrial tug built
  around work rather than heroism.
- The modular pods of the **Eagle Transporter** from *Space: 1999* show how
  repeated payload structure can become the vessel's identity.
- Freighters throughout *Star Wars* provide the useful contrast between worn,
  irregular machinery and clean military silhouettes.

The target is an archetypal working carrier, not a copy of the *Millennium
Falcon* or any other singular hero ship.

### Avoid

Do not taper every bay into a sleek aerodynamic body. Do not let a large weapon
or elaborate bridge overpower the cargo modules. The Transport should look
valuable because of what it carries, not dangerous because of what it mounts.

## Warship

### Core fantasy

The Warship is a line combatant: compact enough to maneuver, heavy enough to
exchange fire, and organized around a clear weapon axis. Every section should
look intentional and mutually supporting.

### Silhouette and section grammar

Its sequence is **Thrusters → Spindrive → Armored Hull → Screens → Main Gun**.
Compared with the Transport, the repeatable center has thicker top and bottom
plates, darker recesses, and a tighter cadence. Dorsal and ventral hull facets
imply armor geometry rather than cargo doors. Screens form a visible defensive
collar near the bow, after which the centerline continues into a pronounced
barrel and muzzle.

The ship should read as one weapon system rather than a collection of turrets.
Its engines, armor, screens, and gun all reinforce the longitudinal line. Small
variant details can imply vents, magazines, or bridge structures, but the spine
must remain dominant.

### Scale and color intent

At medium scale, keep the armored diamond or slab around the centerline and the
screen-to-gun transition. At compact scale, a dense body and unmistakable muzzle
matter more than showing individual subsystems. Defensive masks can emphasize
the screen collar. Weapons masks should trace the barrel or muzzle, not repaint
the entire hull as a weapon.

### Media touchstones

- The **Rocinante** and other combat ships in *The Expanse* demonstrate
  compact, armored utility and a hull shaped by weapon and drive placement.
- The **Defiant** from *Star Trek: Deep Space Nine* demonstrates how a small
  warship can look unusually dense and overpowered without becoming a capital
  ship.
- Frigates in *Homeworld* demonstrate strong role recognition through one
  dominant axis and a few exaggerated hardpoints.

### Avoid

Do not give the Warship the layered height or command keep of a Capital
Warship. Do not make its repeatable section read as civilian containers. It is
a disciplined fleet tool, not a fortress and not an improvised raider.

## Capital Warship

### Core fantasy

The Capital Warship is a fleet anchor and command presence. It carries the same
functional sequence as the Warship, but scale changes the meaning: drives become
clusters, hull bands become decks, and the prow becomes a major installation.
It should seem capable of continuing to fight after smaller ships would fail.

### Silhouette and section grammar

The sequence is **Thrusters → Spindrive → Heavy Hull → Screens → Main Gun**.
Seven-row full-detail art permits separate upper and lower engine structures,
a tall center, dark internal decks, and a heavy forward battery. Repetition
extends a layered fortress spine rather than a simple tube. The screens and gun
should feel embedded in the prow instead of attached as light accessories.

Vertical mass is essential. A long ship with the Warship's height is merely a
long cruiser; a capital hull needs towers, keels, shoulders, or multiple deck
lines that establish hierarchy within the silhouette.

### Scale and color intent

Medium art should preserve at least two apparent deck levels and the distinction
between engine cluster and prow. Compact art becomes a heavy bar with forceful
caps, but should still look denser than the Warship at an equivalent width.
Beacon and Window masks can mark command areas in moderation. Defensive masks
belong around the forward screen complex; Weapons masks belong on the main
battery and any unmistakable hardpoints.

### Media touchstones

- The **Imperial Star Destroyer** from *Star Wars* demonstrates command-scale
  silhouette hierarchy: a dominant hull, readable superstructure, and obvious
  forward threat.
- The **Battlestars** of *Battlestar Galactica* demonstrate layered armor,
  repeated deck rhythm, and a vessel that feels like a mobile base.
- Capital ships in *Homeworld* demonstrate how scale can be conveyed with
  terraces and contrasting masses even when viewed at a small size.

### Avoid

Do not rely on a triangular wedge alone; that would import a franchise-specific
silhouette rather than its design lesson. Do not cover every cell with facets.
Large areas of quiet armor are necessary to make towers, windows, and weapons
look significant.

## Needle Picket

### Core fantasy

The Needle Picket is an independent patrol ship that finds trouble before the
fleet does. It trades volume and armor for endurance, sensors, and a forward
profile that can probe distant space. “Needle” describes both its narrow body
and its directed attention.

### Silhouette and section grammar

Its sequence is **Thruster Fork → Drive Nodes → Patrol Spine → Sensor Crown →
Needle Prow**. Exposed or forked engine forms make the tail look serviceable in
the field. The repeatable spine uses sparse ribs rather than continuous heavy
decks. The sensor crown interrupts that repetition near the bow, and the prow
finishes as a long, fine point rather than a large gun block.

The sensor crown must be visually larger than the vessel's weapon cues. That
single relationship distinguishes a picket from a destroyer. Beacon-like mask
accents can suggest active dishes, warning lights, or calibration nodes.

### Scale and color intent

Medium art should retain exposed drive geometry, at least one rib, and the
sensor-before-needle order. Compact art becomes a thin patrol dash with a small
engine glow and pointed bow. Beacon and Window colors may concentrate around
the sensor crown. Weapons color, if used, should remain a secondary pinpoint.

### Media touchstones

- Science and survey ships in *Star Trek* demonstrate how a prominent sensor
  assembly can communicate mission before armament.
- Sensor platforms and specialized frigates in *Homeworld* demonstrate role
  readability through exposed modules and elongated profiles.
- Patrol craft in *The Expanse* offer a useful hard-science tone: practical
  drives, sparse hull volume, and equipment mounted where it has a clear job.

### Avoid

Do not thicken the patrol spine until it reads as cargo capacity, and do not
turn the needle into a Warship-scale spinal cannon. Its tension comes from
seeing first and surviving through distance, not overpowering the target.

## Falsehold Raider

### Core fantasy

The Falsehold Raider is deception made structural. At first glance it is an
ordinary merchant vessel. On closer inspection its bay seams, reinforced spine,
and forward fittings reveal magazines and concealed batteries. The design must
support both readings.

### Silhouette and section grammar

Its sequence is **Merchant Drive → Armored Buttress → False Cargo Holds →
Masked Battery → Merchant Prow**. The repeatable middle deliberately uses the
box rhythm of a Transport, but darker recesses and suspicious facets break the
innocence. Armor appears behind the bays where a real merchant might use light
framework. The masked battery is placed late in the sequence so the bow can
still pass as civilian from a distance.

Variants should offer plausible deniability: a seam that could be a loading
door, a protrusion that could be a docking fixture, or a beacon that could be
navigation equipment. The reveal comes from accumulation, not one enormous gun.

### Scale and color intent

The full tier carries the double reading. At medium scale, retain bay outlines
plus one reinforced transition. At compact scale, favor the merchant profile;
the role becomes apparent through a weapon-colored bow accent or unusually
dense body. Keep civilian-looking Windows and Beacons sparse and intentional.
Weapons masks should hide along seams until the silhouette is examined.

### Media touchstones

- The armed merchant **Q-ships** in David Weber's *Honor Harrington* novels are
  the clearest narrative touchstone: commerce-shaped hulls concealing military
  intent.
- Tramp freighters in *Star Wars* and *Firefly* supply the worn, adaptable
  civilian visual language that makes the disguise believable.
- *The Expanse* repeatedly uses transponders, hull identity, and converted
  civilian hardware as tools of misdirection; the Raider translates that idea
  into visible seams and hidden mass.

### Avoid

Do not simply draw a Warship with cargo-box decoration. If the armored prow,
engine cluster, or weapon colors reveal the role immediately, the “falsehold”
premise has failed.

## Junction Pinnace

### Core fantasy

The Junction Pinnace is the small craft that makes a larger travel network
useful. It carries messages, specialists, and light cargo between ships,
stations, and planetary surfaces. It is short-ranged, frequently handled, and
slightly over-engined so schedules matter more than comfort.

### Silhouette and section grammar

Its abbreviated grammar is **Overdrive → Sail Nodes → Cabin → Landing Nose**.
There is no separate screen or main-gun section. The compact cabin can repeat a
few times, but never enough to become a Transport. Drive and sail nodes occupy
an intentionally large share of the hull. The nose is blunt or beveled so it
can imply a docking collar, ramp, landing skid, or utility clamp.

The design should feel graspable: a crew could walk around it in a hangar and
recognize every major component. Large uninterrupted armor fields work against
that scale.

### Scale and color intent

The full tier can show a cabin window, navigation beacon, and landing detail.
The medium tier should still read as engine, cabin, and docking nose. Compact
art is almost a pictogram. Windows and Beacons can be proportionally prominent
because they establish inhabited scale. Engine color should make the small
craft feel lively; Weapons and Defensive colors should be rare.

### Media touchstones

- **Runabouts and shuttlecraft** in *Star Trek* demonstrate the visual grammar
  of a complete, inhabited vessel at a much smaller scale than its parent ship.
- Courier and landing craft in *Star Wars* demonstrate how a strong nose or
  folding appendage can make a utility craft immediately recognizable.
- Small transfer craft in *The Expanse* reinforce the idea that access, docking,
  and drive hardware should dominate a vehicle built for short practical trips.

### Avoid

Do not give the Pinnace a fighter's long weapon nose or a freighter's repeated
cargo train. It should look like it belongs beside a docking hatch, not at the
center of a fleet engagement.

## Radiant Lance

### Core fantasy

The Radiant Lance is a refined military vessel that displays its energy economy
rather than hiding it. Heat, thrust, habitation, and weapon alignment form a
single glittering spine. Its elegance should feel engineered and slightly
ceremonial, but never delicate enough to lose combat credibility.

### Silhouette and section grammar

Its sequence is **Fusion Bell → Engine Swell → Diamond Radiators → Habitat
Petals → Lance**. The repeatable radiator section creates a chain of diamonds or
folded vanes, producing a lighter visual rhythm than armor or cargo bays. The
habitat petals form a wider living node before the hull narrows into a long
centerline weapon.

Open diagonals and paired facets are central to the design. They make the ship
look luminous and thermally active without requiring animation. Solid blocks
should cluster in the engine swell, habitat, and weapon root so the open vanes
have something substantial to connect.

### Scale and color intent

Medium art must keep at least one radiator diamond and the lance. Compact art
reduces the vanes to alternating facets along a thin body. Engine color should
burn strongly at the fusion bell. Beacon or Window accents belong in the
habitat petals. Weapons color may run along the lance, while the radiator
geometry should usually retain Surface shading so archetype palettes still
control the whole vessel's cultural identity.

### Media touchstones

- **Minbari ships** from *Babylon 5* demonstrate luminous, blade-like military
  silhouettes whose elegance still communicates power.
- The **Discovery One** from *2001: A Space Odyssey* demonstrates functional
  separation along a long spine and a distinct inhabited node.
- Capital and specialist ships in *Homeworld* demonstrate how diamond, fin, and
  sail shapes can establish a technological culture at tactical-view scale.

### Avoid

Do not close every radiator opening into armor blocks; that turns the ship into
a conventional Warship. Do not make the habitat petals wider than every other
section, or the Lance will read as a transport with a decorative nose.

## Hearth Freighter

### Core fantasy

The Hearth Freighter is not merely old; it is inhabited history. Repairs,
workshops, cargo modules, and a rotating living space have accumulated over a
century of service. The crew treats it as home, so practical changes are visible
rather than smoothed into one factory silhouette.

### Silhouette and section grammar

Its sequence is **Retrofitted Drive → Machine Shop → Cargo Modules → Hearth
Drum → Mining Prow**. The repeatable cargo train resembles a Transport, but its
variants should not be perfectly uniform. The machine shop creates a busy,
patched transition aft. The large drum or ring near the bow provides the
identity: it is where people live, not another cargo bay. The mining prow is a
tool—drill, cutter, tractor fixture, or reinforced bumper—rather than a naval
main gun.

The ship should look maintainable. External rails, mismatched panels, access
voids, and modest asymmetry communicate continuous repair. Those details must
remain organized enough that the hull does not become visual noise.

### Scale and color intent

Full and medium tiers should preserve the drum as a distinct rounded or open
shape. Compact art can only imply it with a widened or faceted body segment.
Windows belong around the habitat, while Beacons can mark working areas and
docking points. Engine colors may be uneven across retrofitted thrusters.
Weapons colors should generally be reserved for a mining cutter or emergency
defense, not a combat battery.

### Media touchstones

- **Serenity** from *Firefly* supplies the strongest “ship as home” principle:
  worn utility, readable living space, and modifications that reveal its crew.
- The **Nostromo** from *Alien* and the **Bebop** from *Cowboy Bebop* contribute
  industrial mass, maintenance history, and an unglamorous working life.
- The rotating habitats of *2001: A Space Odyssey* and *The Expanse* provide a
  functional basis for the conspicuous hearth drum.

### Avoid

Do not make every cargo module identical and pristine; that collapses the role
back into the generic Transport. Do not make the mining prow look like a siege
gun. The Hearth Freighter survives through adaptability, not combat dominance.

## Pearl Shell

### Core fantasy

The Pearl Shell is an alien troop carrier that protects living cargo the way a
shell protects soft tissue. Its armor is layered, offset, and grown or assembled
around a central weapon ring and troop lobe. The result should be strange but
immediately robust.

### Silhouette and section grammar

Its sequence is **Ciliary Drive → Rear Carapace → Weapon Ring → Troop Lobe →
Carapace Beak**. Unlike human modular ships, the boundaries should overlap.
Upper and lower plates do not need to align, and the repeatable weapon ring may
look like a sequence of recessed pores rather than mounted turrets. The troop
lobe adds protected volume; the beak closes the form with screens and layered
armor instead of a conventional barrel.

Alternation is important: hard plate, dark recess, hard plate. Facet glyphs can
suggest pores, eyes, pearls, joints, or shell imperfections, but the silhouette
must retain enough shaded mass to feel armored.

### Scale and color intent

Medium art should retain at least one overlapping plate and one recessed weapon
port. Compact art becomes a dark core between shell-like caps. Weapons masks can
sit inside recesses so they appear when active without repainting the carapace.
Defensive masks suit the forward beak and outer plate edges. Windows should be
rare or absent unless the chosen cultural interpretation calls for visible
troop chambers.

### Media touchstones

- **Vorlon vessels** from *Babylon 5* demonstrate alien hulls whose armor and
  anatomy are difficult to separate.
- **Zerg** ships from *StarCraft* and **Tyranid** bio-ships from *Warhammer
  40,000* demonstrate layered carapaces, recessed organs, and weapon structures
  integrated into the body.
- The alien craft of *Independence Day* demonstrate how repeated surface
  cavities can make a large troop-carrying vessel feel nonhuman and ominous.

### Avoid

Do not organize the shell into clean human cargo boxes, windows, and turrets.
Do not make it so organic that the armor disappears; the “pearl shell” promise
requires a protected inner volume and a legible carapace.

## Marrow Dart

### Core fantasy

The Marrow Dart is a reckless assault organism. It is grown to cross distance,
survive just long enough to strike, and drive a hardened beak into the enemy.
Its structure should appear tense: bones or spars bound by muscle rather than
plates attached to a frame.

### Silhouette and section grammar

Its sequence is **Sinew Drive → Marrow Knot → Bound Spars → Nerve Cluster →
Hardened Beak**. The drive begins with uneven tendons and a hot muscular root.
The marrow knot acts as a dense joint. Repeated spars create alternating open
diamonds and compressed bands, so increasing length makes the creature more
serpentine rather than more spacious. The nerve cluster gathers facets near the
front before the whole form closes into a sharp beak.

Diagonal glyphs are crucial because they imply tension and attachment. Dark
shading should sit inside the body like cavities. Facets may read as nerves,
eyes, or exposed organs, but should be clustered rather than evenly decorated.

### Scale and color intent

Medium art should preserve the alternation of spar and muscle plus the beak.
Compact art becomes a jagged body with an aggressive point. Engine masks can be
interpreted as metabolic thrust. Beacon colors can become nerve flashes.
Weapons color belongs in the hardened beak or selected attack organs;
Defensive color should be minimal because this type expresses survival through
speed and commitment.

### Media touchstones

- **Cylon Raiders** from *Battlestar Galactica* demonstrate an attack craft that
  is both machine and living organism, with a predatory forward profile.
- **Shadow vessels** from *Babylon 5* demonstrate how spikes, negative space,
  and asymmetry produce instinctive menace.
- Zerg and Tyranid spacecraft from *StarCraft* and *Warhammer 40,000* supply the
  vocabulary of bone spars, muscle bands, nerve centers, and grown weapons.

### Avoid

Do not smooth the body into a Pearl Shell-style armored lobe. Do not give it a
human bridge or regular cargo seams. The Marrow Dart should look expendable,
painfully alive, and already leaning into its attack.

## Broadside Citadel

### Core fantasy

The Broadside Citadel is a capital linebreaker built to enter a firing line,
absorb punishment, and answer with layered lateral batteries. Where the Capital
Warship is a fleet anchor organized around a forward axis, the Citadel is a
mobile fortress whose sides are the main event.

### Silhouette and section grammar

Its sequence is **Capital Drive → Drive Citadel → Broadside Decks → Command Keep
→ Siege Prow**. The repeatable middle contains stacked batteries and heavy deck
frames. Each additional repetition must read as more firing line, not simply
more internal hull. The drive citadel braces the engines against that mass. A
raised or enclosed command keep breaks the deck rhythm before the siege prow
finishes the ship with a secondary forward threat.

The silhouette needs vertical layering: upper battery, armored core, lower
battery, with recesses between. The broadside glyph rhythm may be regular, but
the command keep and prow prevent the ship from becoming a featureless wall.

### Scale and color intent

Full detail should make individual battery positions countable. Medium art can
merge each deck into a stronger line while retaining upper and lower fire. At
compact scale, a long heavy body and fortified prow distinguish it from the
Capital Warship's more tapered command profile. Weapons masks should repeat
along the lateral decks. Defensive masks may reinforce the drive citadel and
prow. Windows and Beacons should cluster around the command keep rather than
compete with the batteries.

### Media touchstones

- **Space Battleship Yamato** demonstrates the romantic clarity of a vessel
  whose gun decks and armored superstructure openly declare “battleship.”
- **Battlestars** from *Battlestar Galactica* demonstrate repeated lateral
  structures surrounding a protected command core.
- Imperial warships in *Warhammer 40,000* demonstrate the mobile-fortress
  extreme: layered broadsides, cathedral-like command mass, and a siege prow.

Use those works to understand hierarchy and battery rhythm, not to import a
naval hull outline or gothic ornament wholesale.

### Avoid

Do not place all visual emphasis on one spinal gun; that is the Capital Warship
or Warship language. Do not repeat broadside decks without interruption until
the hull becomes a barcode. Fortress scale requires hierarchy as well as mass.

## Reviewing a ship type

When revising any role, review it in this order:

1. Render the full horizontal tier in one color and identify the tail, repeated
   structure, role-defining section, and bow without reading labels.
2. Compare it with the other eleven roles at the same bounds. If two silhouettes
   communicate the same purpose, strengthen their differing proportions before
   adding details.
3. Check medium and compact tiers as independent symbols. Confirm that the
   role-defining contrast survives rather than merely the outer dimensions.
4. Inspect both horizontal facings and both vertical facings. Direction must be
   clear, reflection must be reversible, and the vertical art must express the
   same functional order.
5. Preview multiple archetypes. If the role vanishes under a different palette,
   the geometry is relying too heavily on color.
6. Audit masks intentionally. Engine, Beacon, Window, Weapons, and Defensive
   cells should mark function; they should not be used as general decoration.
7. Compare against the media touchstones at the level of principle. Remove any
   arrangement that has become a recognizable copy of one source.

The final test is a one-sentence description: a viewer should be able to infer
something close to each role's “Immediate read” from the art alone.
