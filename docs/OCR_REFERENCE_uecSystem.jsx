import { useState } from "react";

const UEC = [
  {
    id:"green", num:"01", label:"ENTER", former:"DOOR", status:"KEEP",
    hex:"#1A6B2F", light:"#E8F5EC", grade:"A+",
    semantics:"Go · Access · Safe Passage",
    description:"Venue entry, gate access, facility check-in, lobby scan, room unlock",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic","Tourism","Bars","Gov't"],
    auditNotes:[
      "Dark green on white = excellent contrast — passes WCAG AAA",
      "Traffic light green is the most universal 'go' signal on Earth",
      "Rename DOOR → ENTER broadens use beyond physical doors",
      "Works indoors and outdoors — legible at distance on signage",
    ],
    rationale:{
      psychology:"Green is the only color that means the same thing in every culture on Earth — go, safe, proceed. It is the entry point to every event and every platform interaction.",
      why:"ENTER is the first scan of every event. It sets the tone for everything that follows. The color must be instantly legible, universally understood, and impossible to confuse.",
      contexts:["A parent arriving at a school concert","A fan entering a stadium","A parishioner scanning into a church event","A tourist checking in at a heritage site"],
      verdict:"No color challenge possible. Green for ENTER is permanent.",
    },
    change:null,
    url:"https://oursharedevents.com/enter",
  },
  {
    id:"coral", num:"02", label:"LIVE", former:"GAME", status:"CHANGE",
    hex:"#C04048", light:"#FFE8EA", grade:"A+",
    semantics:"Exciting · Warm · Now",
    description:"Live scoring, real-time bracket, active event feed, fundraiser thermometer, live auction",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic","Tourism","Bars","Fundraising"],
    auditNotes:[
      "Dark coral on white achieves strong contrast — scans reliably",
      "Coral = the exact midpoint between red's excitement and orange's warmth — without the baggage of either",
      "Orange carried 'caution tape / clearance sale' associations — coral does not",
      "Rename GAME → LIVE expands use to church, school, civic, and fundraising equally",
      "Fundraising thermometers, school spirit posters, and festival banners already live in this color space",
    ],
    rationale:{
      psychology:"Coral sits at the precise intersection of excitement, warmth, and welcome. It carries the energy of red without the alarm, and the inclusivity of orange without the caution signal.",
      why:"The LIVE code is scanned at peak event energy — maximum foot traffic, maximum sponsor visibility, maximum community engagement. The color must match that energy.",
      contexts:["A fundraising thermometer hitting 80% of goal","A championship bracket with one game left","A church festival at peak Saturday afternoon"],
      verdict:"Upgraded from Orange. Coral is the correct choice for all event types — especially non-sports.",
    },
    change:"UPGRADED: Orange → Coral (#C04048). Orange carried caution/industrial associations incompatible with school and church contexts. Coral is warm, exciting, and universally welcoming.",
    url:"https://oursharedevents.com/live",
  },
  {
    id:"blue", num:"03", label:"SPONSOR", former:"SPONSOR", status:"KEEP",
    hex:"#1A3A8A", light:"#E8EEFF", grade:"A+",
    semantics:"Trust · Commerce · Partnership",
    description:"Sponsor landing page, partner offers, advertiser profile, brand activation, local business deals",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic","Tourism","Bars","Gov't"],
    auditNotes:[
      "Navy blue = highest contrast of all 7 codes against white",
      "Blue universally signals institutional trust — banks, hospitals, governments all use it",
      "Sponsors recognize blue as 'their' color — reduces friction at point of scan",
      "Critical revenue code — premium placement on all posters and signage",
    ],
    rationale:{
      psychology:"Blue is the color of trust in every culture studied. When a local sponsor sees their brand on a blue code, they feel at home. When an attendee scans blue, they expect value.",
      why:"The sponsor relationship is the economic engine of ourSharedEvents. The color carries weight — it must feel premium, trustworthy, and worth the investment.",
      contexts:["A brewery's offer at a bocce tournament","A school supply store's discount at a school event","A local restaurant's coupon at a civic festival"],
      verdict:"No color challenge possible. Navy blue for sponsors is permanent.",
    },
    change:null,
    url:"https://oursharedevents.com/sponsor",
  },
  {
    id:"purple", num:"04", label:"ARCHIVE", former:"ARCHIVE", status:"KEEP",
    hex:"#5E1A9A", light:"#F3E8FF", grade:"A",
    semantics:"Memory · History · Record",
    description:"Past results, statistics, event memories, photos, SharedReport, legacy data, season records",
    verticals:["Sports","School","Church","Museum","Civic","Tourism","Gov't"],
    auditNotes:[
      "Deep purple scans cleanly — strong contrast on white",
      "Purple = royalty + permanence across Western and Eastern color systems",
      "The archive is the competitive moat — this code should feel premium",
      "This is the code that brings people back between events — core loyalty driver",
    ],
    rationale:{
      psychology:"Purple has meant permanence and importance across cultures for thousands of years. It is the color of memory made tangible — royalty, ritual, record.",
      why:"The archive is what separates ourSharedEvents from every competitor. Most platforms end when the event ends. Purple makes the past permanent and valuable.",
      contexts:["A bocce league's five-year win record","A school's championship history since 1987","A church's annual festival photo archive"],
      verdict:"Premium color for the platform's most differentiated feature. Permanent.",
    },
    change:null,
    url:"https://oursharedevents.com/archive",
  },
  {
    id:"pink", num:"05", label:"HELP", former:"NEW", status:"ADD",
    hex:"#B01468", light:"#FFE8F3", grade:"A",
    semantics:"Care · Assistance · Accessibility",
    description:"ADA assistance, staff contact, first aid location, lost & found, volunteer info, accessibility services",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic","Tourism","Bars","Gov't"],
    auditNotes:[
      "Deep magenta-pink on white — strong contrast, scans reliably",
      "Pink is globally associated with care: healthcare, safety, and assistance",
      "Zero conflict with any other UEC code — unique hue in the system",
      "Critical for ADA compliance signage at schools and civic venues",
      "Highest human stakes of any code — help when it's actually needed",
    ],
    rationale:{
      psychology:"Pink and magenta have globally converged on a single meaning: care and human assistance. It is the color of healthcare, safety, and compassionate service.",
      why:"Every event has someone who needs help but won't ask. An elderly attendee needing accessible seating. A lost child. A medical situation. Pink makes help visible without stigma.",
      contexts:["Accessible entrance directions at a sports venue","First aid tent location at a festival","Lost & found at a school event","Volunteer contact at a civic gathering"],
      verdict:"New addition. Fills a gap that exists at every single event in every vertical.",
    },
    change:"NEW — highest priority addition. Covers ADA, accessibility, and human assistance. Fills a gap that exists at every single event.",
    url:"https://oursharedevents.com/help",
  },
  {
    id:"amber", num:"06", label:"FEEDBACK", former:"YELLOW", status:"CHANGE",
    hex:"#8A5A00", light:"#FFF8E5", grade:"B+",
    semantics:"Voice · Opinion · Response",
    description:"Attendee surveys, player ratings, post-event input, experience scoring, community voice",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic","Tourism","Bars"],
    auditNotes:[
      "CRITICAL FIX: Original Yellow (#FFDD00) fails QR scanning — near-zero contrast on white background",
      "Dark Amber (#8A5A00) preserves warmth while achieving reliable scan contrast",
      "Yellow is reserved for ALERT — its universal meaning is caution, not conversation",
      "Amber = warm invitation to share — appropriate for post-event community voice",
    ],
    rationale:{
      psychology:"Amber is warm without being alarming — it carries the golden quality of harvest and completion. It invites reflection rather than demanding attention.",
      why:"Feedback closes the flywheel. If attendees scan amber and feel invited rather than interrogated, completion rates rise and the data becomes meaningful.",
      contexts:["30-second survey after a bocce tournament","Parent satisfaction form after a school play","Post-service input at a church event"],
      verdict:"Fixed from physically invalid yellow. Dark amber is the correct implementation.",
    },
    change:"FIXED: Yellow → Dark Amber. Yellow fails to scan (near-zero contrast on white) and its universal caution meaning conflicts with the feedback use case.",
    url:"https://oursharedevents.com/feedback",
  },
  {
    id:"charcoal", num:"07", label:"UTILITY", former:"WHITE", status:"CHANGE",
    hex:"#2A2A3A", light:"#F0F0F5", grade:"B",
    semantics:"General · Info · Infrastructure",
    description:"WiFi password, schedule PDF, venue map, general announcements, admin quick links",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic","Tourism","Bars","Gov't"],
    auditNotes:[
      "CRITICAL FIX: White QR modules on white background are physically impossible to scan",
      "Charcoal (#2A2A3A) achieves maximum possible contrast — most scannable in the system",
      "Neutral charcoal reads as infrastructure — backstage, utility, general information",
      "Catch-all code — anything without a dedicated UEC color receives Utility charcoal",
    ],
    rationale:{
      psychology:"Charcoal and near-black are the colors of infrastructure — circuit breakers, pipe labels, server racks. They say 'this is the system working behind the scenes.'",
      why:"Every event has miscellaneous information that doesn't fit a dedicated code. Charcoal is the catch-all — reliable, neutral, and impossible to confuse with any semantic code.",
      contexts:["WiFi password at any indoor event","Parking map at a large sports venue","Event schedule PDF at a school concert"],
      verdict:"Fixed from physically impossible white. Charcoal is correct.",
    },
    change:"FIXED: White → Charcoal. White QR is physically invalid — zero contrast. Charcoal achieves maximum contrast and reads as infrastructure.",
    url:"https://oursharedevents.com/utility",
  },
];

const EXTENSIONS = [
  {
    id:"yellow", label:"ALERT", hex:"#B8960A", light:"#FFFCE5", icon:"⚠️",
    priority:"HIGH", grade:"A+",
    description:"Safety notices, weather delays, schedule changes, venue emergencies, urgent announcements",
    rationale:"Yellow universally means caution — the one color whose meaning is universal and non-negotiable. Reserved exclusively for urgent real-world alerts.",
    verticals:["All — especially outdoor sports, schools, civic"],
  },
  {
    id:"red", label:"STAFF", hex:"#A00020", light:"#FFE8EB", icon:"👤",
    priority:"HIGH", grade:"A",
    description:"Staff-only pages, volunteer check-in, admin tools, event worker resources, backstage access",
    rationale:"Red = authority and restricted access. Separates operational codes from public-facing codes. Staff see red; attendees do not.",
    verticals:["Sports","School","Church","Museum","Rec Center","Civic"],
  },
  {
    id:"teal", label:"CHECK-IN", hex:"#006B6B", light:"#E5F7F7", icon:"✅",
    priority:"MEDIUM", grade:"A",
    description:"Attendance tracking, membership verification, roster check-in, season pass confirmation",
    rationale:"Distinct from ENTER — you can enter a building but still need to register attendance separately. Check-in closes the attendance loop.",
    verticals:["School","Church","Sports","Rec Center","Civic"],
  },
  {
    id:"teal-shop", label:"SHOP", hex:"#1A4A48", light:"#E5F4F3", icon:"SHOPBAG",
    priority:"MEDIUM", grade:"B+",
    description:"Merchandise, ticket upgrades, concession ordering, team store, silent auction, fundraising purchases",
    rationale:"Commerce beyond sponsors. Separates buying (transaction) from sponsorship (relationship). Shop is attendee-initiated; sponsor is platform-placed.",
    verticals:["Sports","Museum","Tourism","Bars","Fundraising"],
  },
];

const STATUS_STYLE = {
  KEEP:   { bg:"#0A1A0A", color:"#4ADE80", border:"#1A3A1A", label:"✓ KEEP" },
  ADD:    { bg:"#0F0A1A", color:"#C084FC", border:"#2A1A4A", label:"★ NEW"  },
  CHANGE: { bg:"#1A0608", color:"#C04048", border:"#4A1018", label:"⚡ UPDATED" },
};

const GRADE_COLOR = { "A+":"#4ADE80", "A":"#60A5FA", "B+":"#C084FC", "B":"#D4A017" };

const PRIORITY_STYLE = {
  HIGH:   { bg:"#1A0A0A", color:"#F87171", border:"#4A1A1A" },
  MEDIUM: { bg:"#0A120A", color:"#4ADE80", border:"#1A3A1A" },
};

const JOURNEY = [
  { hex:"#1A6B2F", label:"GREEN · ENTER",    moment:"Arrives at venue. Scans green. No instructions needed — the color tells them everything." },
  { hex:"#1A3A8A", label:"BLUE · SPONSOR",   moment:"Sees a local offer on the display. Scans blue. Gets a real discount from a real neighbor." },
  { hex:"#C04048", label:"CORAL · LIVE",     moment:"Event begins. Scans coral. Real-time action — scores, brackets, thermometer — all live." },
  { hex:"#B01468", label:"PINK · HELP",      moment:"Needs accessible seating. Scans pink. Help arrives. No embarrassment. No confusion." },
  { hex:"#8A5A00", label:"AMBER · FEEDBACK", moment:"Event ends. Scans amber. 30 seconds. Feels heard. Returns next time." },
  { hex:"#5E1A9A", label:"PURPLE · ARCHIVE", moment:"Comes home. Shares the purple link. Their team's win lives forever." },
];

const CHECKLIST = [
  [true,  "All module colors are dark on white — contrast ratios pass WCAG"],
  [true,  "Error correction level H (30%) — allows logo overlay on all codes"],
  [true,  "URL paths are human-readable — not raw event IDs"],
  [true,  "7 codes cover full lifecycle: pre-event, during, and post"],
  [true,  "Color semantics align with global color psychology research"],
  [true,  "Each code has exactly one meaning — zero ambiguity across the set"],
  [true,  "System works in grayscale — label backup for accessibility"],
  [true,  "Pink/HELP satisfies ADA and accessibility signage requirements"],
  [true,  "Coral replaces orange — warm, inviting, zero caution associations"],
  [false, "Yellow removed from QR use — insufficient contrast on white"],
  [false, "White removed — physically invalid as a QR module color"],
];

const PITCH_CARDS = [
  { icon:"🔥", title:"Coral LIVE is the fundraising moment.",       body:"The LIVE code is scanned at peak energy. That's the moment a fundraising thermometer hits 80%. That's when the sponsor logo matters most. Coral puts that energy in a color that works at a bocce tournament and a church fundraiser equally." },
  { icon:"🌐", title:"Every person. Every event.",                   body:"The same 7 colors work at a bocce tournament, a school play, a church festival, and a civic hearing. No vertical requires a different system. The color is the instruction." },
  { icon:"🏛️", title:"The sponsor code becomes permanent real estate.", body:"When blue appears on every poster at every event in a corridor, sponsors stop buying ads and start buying presence. Blue is the most valuable pixel in the system." },
  { icon:"📚", title:"Purple closes the loop no one else closes.",    body:"Most platforms end when the event ends. Purple makes the past permanent. A bocce league's five-year record. A school's championship archive since 1987. Purple is why people come back." },
];

// ─── SHARED UI ──────────────────────────────────────────────────────────────

function QRDisplay({ url, dark, size = 112 }) {
  const [status, setStatus] = useState("loading");
  const hex = dark.replace("#", "");
  const src = `https://quickchart.io/qr?text=${encodeURIComponent(url)}&size=${size * 2}&dark=${hex}&light=ffffff&ecLevel=H&margin=1`;
  return (
    <div style={{ width: size, height: size, background: "#fff", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
      {status === "loading" && <span style={{ fontSize: 9, color: "#aaa", fontFamily: "monospace" }}>loading…</span>}
      {status === "error"   && <span style={{ fontSize: 9, color: "#888", fontFamily: "monospace", textAlign: "center", padding: 4 }}>QR unavailable</span>}
      <img
        src={src}
        alt={`QR code for ${url}`}
        width={size}
        height={size}
        onLoad={() => setStatus("ok")}
        onError={() => setStatus("error")}
        style={{ display: status === "ok" ? "block" : "none", width: size, height: size }}
      />
    </div>
  );
}

function Chip({ label, hex, bg, border }) {
  return (
    <span style={{
      background: bg, color: hex, border: `1px solid ${border || hex + "44"}`,
      fontFamily: "monospace", fontWeight: 700, fontSize: 9,
      padding: "2px 7px", borderRadius: 4, letterSpacing: "0.08em",
    }}>{label}</span>
  );
}

function VerticalTags({ verticals }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
      {verticals.map(v => (
        <span key={v} style={{ background: "#111827", border: "1px solid #1E2233", color: "#6B7280", fontFamily: "monospace", fontSize: 8, padding: "2px 6px", borderRadius: 3 }}>{v}</span>
      ))}
    </div>
  );
}

function SectionLabel({ children }) {
  return <div style={{ fontSize: 8, fontFamily: "monospace", color: "#2A3040", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 6 }}>{children}</div>;
}

// ─── CODES TAB ──────────────────────────────────────────────────────────────

function CodeCard({ code, expanded, onToggle }) {
  const st = STATUS_STYLE[code.status];
  return (
    <div
      onClick={onToggle}
      style={{
        background: expanded ? "#141824" : "#0D1117",
        border: `1.5px solid ${expanded ? code.hex + "99" : "#1E2233"}`,
        borderRadius: 13, overflow: "hidden", cursor: "pointer",
        transition: "border-color 0.2s, background 0.2s",
        boxShadow: expanded ? `0 0 36px ${code.hex}14` : "none",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "15px 18px" }}>
        <div style={{ width: 44, height: 44, borderRadius: 9, flexShrink: 0, background: code.hex, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontFamily: "monospace", color: "#fff", fontSize: 11, fontWeight: 700, letterSpacing: "0.05em" }}>{code.num}</span>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap", marginBottom: 3 }}>
            <span style={{ fontFamily: "'Courier New',monospace", fontWeight: 700, fontSize: 15, letterSpacing: "0.08em", color: code.hex }}>{code.label}</span>
            <Chip label={st.label} hex={st.color} bg={st.bg} border={st.border} />
          </div>
          <div style={{ fontSize: 10.5, color: "#3B4A6B", fontFamily: "monospace" }}>{code.semantics}</div>
        </div>
        <div style={{ fontFamily: "monospace", fontWeight: 700, fontSize: 17, color: GRADE_COLOR[code.grade] }}>{code.grade}</div>
        <div style={{ color: "#2A3040", fontSize: 11, transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>▼</div>
      </div>

      {expanded && (
        <div style={{ borderTop: "1px solid #1A1F2E", padding: 18, display: "flex", gap: 18, flexWrap: "wrap" }}>
          <div style={{ background: "#080C14", borderRadius: 11, padding: 13, border: `1px solid ${code.hex}33`, display: "flex", flexDirection: "column", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <QRDisplay url={code.url} dark={code.hex} size={112} />
            <div style={{ background: code.light, color: code.hex, fontFamily: "monospace", fontWeight: 700, fontSize: 10, padding: "3px 10px", borderRadius: 4 }}>{code.label}</div>
            <div style={{ fontSize: 8, color: "#2A3040", fontFamily: "monospace", textAlign: "center" }}>{code.url}</div>
          </div>
          <div style={{ flex: 1, minWidth: 190, display: "flex", flexDirection: "column", gap: 13 }}>
            <div>
              <SectionLabel>USE CASES</SectionLabel>
              <div style={{ fontSize: 11.5, color: "#9AA0B0", lineHeight: 1.65 }}>{code.description}</div>
            </div>
            {code.change && (
              <div style={{ background: "#1A0608", border: "1px solid #4A1018", borderRadius: 7, padding: "8px 12px", fontSize: 10.5, color: "#9A7060", lineHeight: 1.5 }}>{code.change}</div>
            )}
            <div>
              <SectionLabel>TECHNICAL AUDIT</SectionLabel>
              {code.auditNotes.map((n, i) => (
                <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 10.5, color: "#6B7280", lineHeight: 1.55, paddingBottom: 4 }}>
                  <span style={{ color: code.hex, flexShrink: 0 }}>›</span>
                  <span>{n}</span>
                </div>
              ))}
            </div>
            <VerticalTags verticals={code.verticals} />
          </div>
        </div>
      )}
    </div>
  );
}

function CodesSection() {
  const [expanded, setExpanded] = useState(null);
  const toggle = (id) => setExpanded(prev => prev === id ? null : id);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
      <div style={{ fontSize: 10, color: "#2A3040", fontFamily: "monospace", letterSpacing: "0.04em", marginBottom: 4 }}>
        Tap any row to expand the full audit, live QR preview, and deployment notes.
      </div>
      {UEC.map(code => (
        <CodeCard key={code.id} code={code} expanded={expanded === code.id} onToggle={() => toggle(code.id)} />
      ))}
    </div>
  );
}

// ─── RATIONALE TAB ──────────────────────────────────────────────────────────

function RationaleCard({ code }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      onClick={() => setOpen(o => !o)}
      style={{
        background: open ? "#141824" : "#0D1117",
        border: `1.5px solid ${open ? code.hex + "88" : "#1E2233"}`,
        borderRadius: 12, overflow: "hidden", cursor: "pointer",
        transition: "border-color 0.2s, background 0.2s",
        boxShadow: open ? `0 0 28px ${code.hex}14` : "none",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 13, padding: "14px 18px" }}>
        <div style={{ width: 32, height: 32, borderRadius: 7, background: code.hex, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: "'Courier New',monospace", fontWeight: 700, fontSize: 13, letterSpacing: "0.08em", color: code.hex }}>{code.label}</div>
          <div style={{ fontSize: 10, color: "#3B4A6B", fontStyle: "italic", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{code.semantics}</div>
        </div>
        <div style={{ color: "#2A3040", fontSize: 11, transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>▼</div>
      </div>
      {open && (
        <div style={{ borderTop: "1px solid #1A1F2E", padding: "18px 20px", display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <SectionLabel>COLOR PSYCHOLOGY</SectionLabel>
            <div style={{ fontSize: 12, color: "#9AA0B0", lineHeight: 1.75 }}>{code.rationale.psychology}</div>
          </div>
          <div style={{ background: "#080C14", border: `1px solid ${code.hex}33`, borderRadius: 8, padding: "12px 14px" }}>
            <SectionLabel>WHY THIS CODE</SectionLabel>
            <div style={{ fontSize: 11.5, color: "#8892A4", lineHeight: 1.65 }}>{code.rationale.why}</div>
          </div>
          <div>
            <SectionLabel>REAL SCENARIOS</SectionLabel>
            {code.rationale.contexts.map((ctx, i) => (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", fontSize: 11, color: "#6B7280", lineHeight: 1.6, paddingBottom: 5 }}>
                <span style={{ color: code.hex, flexShrink: 0 }}>◆</span>
                <span>{ctx}</span>
              </div>
            ))}
          </div>
          <div style={{ background: code.hex + "18", border: `1px solid ${code.hex}44`, borderRadius: 7, padding: "10px 14px", fontSize: 11.5, color: "#9AA0B0", fontStyle: "italic", lineHeight: 1.6 }}>
            ↳ {code.rationale.verdict}
          </div>
        </div>
      )}
    </div>
  );
}

function RationaleSection() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ fontSize: 11, color: "#2A3040", fontFamily: "monospace", letterSpacing: "0.04em", marginBottom: 4 }}>
        Every color was chosen for specific psychological and cultural reasons — not aesthetics.
      </div>
      {UEC.map(code => (
        <RationaleCard key={code.id} code={code} />
      ))}
    </div>
  );
}

// ─── AUDIT TAB ──────────────────────────────────────────────────────────────

function AuditSection() {
  const changed = UEC.filter(c => c.change);
  const tiles = [
    { label: "KEEP",          count: UEC.filter(c => c.status === "KEEP").length,   color: "#4ADE80", bg: "#0A1A0A", border: "#1A3A1A" },
    { label: "NEW",           count: UEC.filter(c => c.status === "ADD").length,    color: "#C084FC", bg: "#0F0A1A", border: "#2A1A4A" },
    { label: "UPDATED",       count: UEC.filter(c => c.status === "CHANGE").length, color: "#C04048", bg: "#1A0608", border: "#4A1018" },
    { label: "INVALID→FIXED", count: 2,                                              color: "#F87171", bg: "#1A0A0A", border: "#4A1A1A" },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8 }}>
        {tiles.map(s => (
          <div key={s.label} style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 10, padding: "14px 10px", textAlign: "center" }}>
            <div style={{ fontSize: 26, fontWeight: 700, color: s.color, fontFamily: "monospace" }}>{s.count}</div>
            <div style={{ fontSize: 8, fontFamily: "monospace", color: s.color, opacity: 0.7, letterSpacing: "0.1em" }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "#1A0608", border: "1px solid #4A1018", borderRadius: 12, padding: "14px 16px" }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, letterSpacing: "0.15em", color: "#C04048", marginBottom: 10 }}>CHANGES APPLIED</div>
        {changed.map((c, i) => (
          <div key={c.id} style={{ display: "flex", gap: 10, alignItems: "flex-start", paddingBottom: i < changed.length - 1 ? 12 : 0, borderBottom: i < changed.length - 1 ? "1px solid #2A0A10" : "none", marginBottom: i < changed.length - 1 ? 12 : 0 }}>
            <div style={{ width: 18, height: 18, borderRadius: 4, background: c.hex, flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontFamily: "monospace", fontSize: 11, color: "#E0E4F0", marginBottom: 3 }}>
                {c.former} → <strong style={{ color: c.hex }}>{c.label}</strong>
              </div>
              <div style={{ fontSize: 10.5, color: "#9A7060", lineHeight: 1.5 }}>{c.change}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: "#0D1117", border: "1px solid #1E2233", borderRadius: 12, padding: "14px 16px" }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, letterSpacing: "0.15em", color: "#2A3040", marginBottom: 10 }}>DEPLOYMENT CHECKLIST</div>
        {CHECKLIST.map(([pass, note], i) => (
          <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "5px 0", borderBottom: "1px solid #0F1420" }}>
            <span style={{ fontSize: 11, color: pass ? "#4ADE80" : "#F87171", flexShrink: 0, marginTop: 1 }}>{pass ? "✓" : "✗"}</span>
            <span style={{ fontSize: 11, color: pass ? "#6B7280" : "#9AA0B0", lineHeight: 1.5 }}>{note}</span>
          </div>
        ))}
      </div>

      <div style={{ background: "#0D1117", border: "1px solid #1E2233", borderRadius: 12, padding: "14px 16px" }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, letterSpacing: "0.15em", color: "#2A3040", marginBottom: 10 }}>MASTER TABLE</div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 10.5 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1E2233" }}>
              {["#", "", "CODE", "HEX", "SEMANTIC", "GRADE"].map(h => (
                <th key={h} style={{ fontFamily: "monospace", fontSize: 8, letterSpacing: "0.1em", color: "#2A3040", textAlign: "left", padding: "4px 7px", fontWeight: 400 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {UEC.map(c => (
              <tr key={c.id} style={{ borderBottom: "1px solid #0F1420" }}>
                <td style={{ padding: "7px 7px", fontFamily: "monospace", color: "#333", fontSize: 9 }}>{c.num}</td>
                <td style={{ padding: "7px 7px" }}><div style={{ width: 16, height: 16, borderRadius: 3, background: c.hex }} /></td>
                <td style={{ padding: "7px 7px", fontFamily: "monospace", fontWeight: 700, color: c.hex, fontSize: 11 }}>{c.label}</td>
                <td style={{ padding: "7px 7px", fontFamily: "monospace", color: "#3B4A6B", fontSize: 9 }}>{c.hex}</td>
                <td style={{ padding: "7px 7px", color: "#6B7280", fontSize: 10.5 }}>{c.semantics}</td>
                <td style={{ padding: "7px 7px", fontFamily: "monospace", fontWeight: 700, color: GRADE_COLOR[c.grade], fontSize: 11 }}>{c.grade}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── EXTEND TAB ─────────────────────────────────────────────────────────────

function ShopBagIcon({ size = 28 }) {
  const iconColor = "#5AADAA";
  const shadowColor = "#0D2E2D";
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5 10h18l-2 13H7L5 10z" fill={iconColor} />
      <path d="M5 10l2 13H7L5 10z" fill={shadowColor} opacity="0.35" />
      <path d="M10 10V7a4 4 0 0 1 8 0v3" stroke={iconColor} strokeWidth="1.8" strokeLinecap="round" fill="none" />
      <line x1="5" y1="10" x2="23" y2="10" stroke={iconColor} strokeWidth="1.5" strokeOpacity="0.4" />
    </svg>
  );
}

function ExtensionsSection() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ background: "#0D1117", border: "1px solid #1E2233", borderRadius: 10, padding: "12px 16px", fontSize: 11, color: "#6B7280", lineHeight: 1.7 }}>
        The core 7 UEC codes handle 95% of all event scenarios. These 4 extensions address specific operational needs.{" "}
        <strong style={{ color: "#9AA0B0" }}>Yellow/ALERT is highest priority — the one universal caution signal reserved for real emergencies.</strong>
      </div>
      {EXTENSIONS.map(ext => {
        const ps = PRIORITY_STYLE[ext.priority];
        return (
          <div key={ext.id} style={{ background: "#111827", border: `1.5px dashed ${ext.hex}55`, borderRadius: 12, padding: "16px 18px", display: "flex", gap: 16, alignItems: "flex-start" }}>
            <div style={{ width: 44, height: 44, borderRadius: 9, flexShrink: 0, background: ext.hex, display: "flex", alignItems: "center", justifyContent: "center" }}>
              {ext.icon === "SHOPBAG" ? <ShopBagIcon size={26} /> : <span style={{ fontSize: 22 }}>{ext.icon}</span>}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5, flexWrap: "wrap" }}>
                <span style={{ fontFamily: "monospace", fontWeight: 700, fontSize: 13, letterSpacing: "0.08em", color: ext.hex }}>{ext.label}</span>
                <Chip label={`PRIORITY: ${ext.priority}`} hex={ps.color} bg={ps.bg} border={ps.border} />
                <span style={{ fontFamily: "monospace", fontWeight: 700, fontSize: 13, color: GRADE_COLOR[ext.grade] }}>{ext.grade}</span>
              </div>
              <div style={{ fontSize: 11.5, color: "#9AA0B0", marginBottom: 7, lineHeight: 1.55 }}>{ext.description}</div>
              <div style={{ fontSize: 11, color: "#555", lineHeight: 1.55, fontStyle: "italic", marginBottom: 8 }}>{ext.rationale}</div>
              <VerticalTags verticals={ext.verticals} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── PITCH TAB ──────────────────────────────────────────────────────────────

function PitchSection() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ background: "linear-gradient(135deg,#0D1117,#141824)", border: "1px solid #1E2233", borderRadius: 14, padding: "28px 24px", textAlign: "center" }}>
        <div style={{ fontFamily: "'Georgia',serif", fontSize: 21, fontWeight: 700, color: "#F0F0F5", lineHeight: 1.4, marginBottom: 14 }}>
          A QR code should tell you what it does<br />
          <span style={{ color: "#444", fontSize: 17, fontWeight: 400 }}>before you scan it.</span>
        </div>
        <div style={{ fontSize: 12.5, color: "#6B7280", lineHeight: 1.75, maxWidth: 520, margin: "0 auto" }}>
          The Universal Event Code is a color-based semantic standard for QR codes at public events. Seven colors. One meaning each. No instructions required.
        </div>
      </div>

      {PITCH_CARDS.map((p, i) => (
        <div key={i} style={{ background: "#0D1117", border: "1px solid #1E2233", borderRadius: 12, padding: "16px 20px", display: "flex", gap: 16, alignItems: "flex-start" }}>
          <div style={{ fontSize: 26, flexShrink: 0, lineHeight: 1, marginTop: 2 }}>{p.icon}</div>
          <div>
            <div style={{ fontFamily: "'Georgia',serif", fontSize: 14, color: "#E0E4F0", fontWeight: 700, marginBottom: 6 }}>{p.title}</div>
            <div style={{ fontSize: 11.5, color: "#6B7280", lineHeight: 1.75 }}>{p.body}</div>
          </div>
        </div>
      ))}

      <div style={{ background: "#0D1117", border: "1px solid #1E2233", borderRadius: 12, padding: 20 }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, letterSpacing: "0.18em", color: "#2A3040", marginBottom: 12 }}>ONE ATTENDEE · ONE EVENT · SIX SCANS</div>
        {JOURNEY.map((step, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "8px 0", borderBottom: i < JOURNEY.length - 1 ? "1px solid #0F1420" : "none" }}>
            <div style={{ fontFamily: "monospace", color: "#2A2F40", fontSize: 9, flexShrink: 0, width: 16 }}>{i + 1}</div>
            <div style={{ width: 12, height: 12, borderRadius: 3, background: step.hex, flexShrink: 0, marginTop: 2 }} />
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#3B4A6B", flexShrink: 0, width: 110 }}>{step.label}</div>
            <div style={{ fontSize: 11, color: "#6B7280", lineHeight: 1.55 }}>{step.moment}</div>
          </div>
        ))}
      </div>

      <div style={{ borderRadius: 8, overflow: "hidden", height: 8, display: "flex" }}>
        {UEC.map(c => <div key={c.id} style={{ flex: 1, background: c.hex }} />)}
      </div>
      <div style={{ textAlign: "center", fontFamily: "monospace", fontSize: 8, color: "#2A3040", letterSpacing: "0.12em" }}>
        ourSharedEvents · Universal Event Code v1.1 · 7 colors · All events · All people
      </div>
    </div>
  );
}

// ─── APP ────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "codes",     label: "7 CODES",   sub: "UEC v1.1" },
  { id: "rationale", label: "RATIONALE", sub: "Color Psychology" },
  { id: "audit",     label: "AUDIT",     sub: "Best Practices" },
  { id: "extend",    label: "EXTEND",    sub: "+ 4 More" },
  { id: "pitch",     label: "THE CASE",  sub: "Why It Works" },
];

export default function App() {
  const [tab, setTab] = useState("codes");

  const renderTab = () => {
    switch (tab) {
      case "codes":     return <CodesSection />;
      case "rationale": return <RationaleSection />;
      case "audit":     return <AuditSection />;
      case "extend":    return <ExtensionsSection />;
      case "pitch":     return <PitchSection />;
      default:          return null;
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#080C14", fontFamily: "'Georgia',serif", color: "#E0E4F0" }}>
      <style>{`* { box-sizing: border-box; } ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: #1E2233; border-radius: 2px; }`}</style>

      <div style={{ background: "#0D1117", borderBottom: "1px solid #1E2233", padding: "24px 20px 0" }}>
        <div style={{ maxWidth: 680, margin: "0 auto" }}>
          <div style={{ fontFamily: "monospace", fontSize: 8, letterSpacing: "0.32em", color: "#1E2A3A", marginBottom: 4 }}>
            ourSharedEvents · Universal Event Code
          </div>
          <div style={{ fontFamily: "'Georgia',serif", fontSize: 22, fontWeight: 700, color: "#F0F0F5", marginBottom: 2 }}>
            Universal Event Code
          </div>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#1E2A3A", letterSpacing: "0.18em", marginBottom: 14 }}>
            UEC v1.1 — COLOR STANDARD FOR ALL PUBLIC EVENTS
          </div>
          <div style={{ display: "flex", gap: 2, marginBottom: 16, borderRadius: 4, overflow: "hidden", height: 5 }}>
            {UEC.map(c => <div key={c.id} style={{ flex: 1, background: c.hex }} />)}
          </div>
          <div style={{ display: "flex", overflowX: "auto" }}>
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  flexShrink: 0, background: "transparent", border: "none", cursor: "pointer",
                  borderBottom: `2px solid ${tab === t.id ? "#C04048" : "transparent"}`,
                  padding: "9px 12px", transition: "border-color 0.15s",
                }}
              >
                <div style={{ fontFamily: "monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.1em", color: tab === t.id ? "#E0E4F0" : "#3B4A6B" }}>{t.label}</div>
                <div style={{ fontSize: 8, fontFamily: "monospace", color: tab === t.id ? "#C04048" : "#1E2A3A", marginTop: 2 }}>{t.sub}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 680, margin: "0 auto", padding: "20px 20px 48px" }}>
        {renderTab()}
      </div>
    </div>
  );
}
