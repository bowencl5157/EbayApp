import { useState, useCallback } from "react";

const SYSTEM_PROMPT = `You are an expert eBay SEO specialist for clothing, shoes & accessories. Given product details, generate a fully optimized eBay listing in JSON format.

CRITICAL: Return ONLY a raw JSON object. No markdown fences, no backticks, no explanation, no preamble. Start your response with { and end with }.

Use this exact structure:
{
  "title": "eBay title max 80 chars, keyword-rich, no special chars except hyphens",
  "subtitle": "55-char subtitle with complementary keywords",
  "primaryKeywords": ["8 to 10 high-volume primary keywords"],
  "longTailKeywords": ["10 to 12 long-tail buyer-intent phrases"],
  "itemSpecifics": {
    "Brand": "brand name",
    "Style": "style type",
    "Material": "material",
    "Color": "color",
    "Size Type": "regular/plus/petite etc",
    "Department": "Men/Women/Unisex/Boys/Girls",
    "Occasion": "occasion",
    "Season": "season",
    "Pattern": "solid/floral/striped etc",
    "Fit": "slim/regular/relaxed etc"
  },
  "description": "HTML description under 250 words. Use <b> for emphasis. Include: product highlights, key features, why buy. Keep it concise.",
  "categoryPath": "eBay category path",
  "conditionNotes": "condition description",
  "seoTips": ["3 actionable tips to boost rankings"]
}`;

const themes = {
  bg: "#0a0a0f",
  surface: "#13131a",
  card: "#1a1a24",
  border: "#2a2a3d",
  accent: "#f0c040",
  accentDim: "#a07a10",
  text: "#e8e8f0",
  muted: "#7070a0",
  success: "#40d080",
  ebayBlue: "#3665f3",
  ebayRed: "#e53238",
};

export default function EbayListingGenerator() {
  const [productInput, setProductInput] = useState("");
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState("");
  const [activeTab, setActiveTab] = useState("title");

  const generate = useCallback(async () => {
    if (!productInput.trim()) return;
    setLoading(true);
    setError("");
    setListing(null);

    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: SYSTEM_PROMPT,
          messages: [{ role: "user", content: `Generate an eBay listing for this product:\n\n${productInput}` }],
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error?.message || `API error ${response.status}`);
      }

      const text = data.content?.map((b) => b.text || "").join("") || "";

      // Robustly extract JSON between first { and last }
      const firstBrace = text.indexOf("{");
      const lastBrace = text.lastIndexOf("}");
      if (firstBrace === -1 || lastBrace === -1) throw new Error("No JSON in response");
      const parsed = JSON.parse(text.slice(firstBrace, lastBrace + 1));

      setListing(parsed);
      setActiveTab("title");
    } catch (err) {
      setError(`Error: ${err.message || "Something went wrong. Please try again."}`);
    } finally {
      setLoading(false);
    }
  }, [productInput]);

  const copyText = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(""), 2000);
  };

  const tabs = listing
    ? [
        { key: "title", label: "Title & SEO" },
        { key: "keywords", label: "Keywords" },
        { key: "specifics", label: "Item Specifics" },
        { key: "description", label: "Description" },
        { key: "tips", label: "Pro Tips" },
      ]
    : [];

  return (
    <div style={{ minHeight: "100vh", background: themes.bg, fontFamily: "'Georgia', 'Times New Roman', serif", color: themes.text, padding: "0" }}>
      {/* Header */}
      <div style={{ background: themes.surface, borderBottom: `1px solid ${themes.border}`, padding: "20px 24px", display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ display: "flex", gap: "4px" }}>
          <span style={{ background: themes.ebayRed, color: "#fff", fontWeight: "900", fontSize: "22px", padding: "2px 6px", letterSpacing: "-1px", fontFamily: "Arial, sans-serif" }}>e</span>
          <span style={{ background: themes.ebayBlue, color: "#fff", fontWeight: "900", fontSize: "22px", padding: "2px 6px", letterSpacing: "-1px", fontFamily: "Arial, sans-serif" }}>b</span>
          <span style={{ background: themes.accent, color: "#000", fontWeight: "900", fontSize: "22px", padding: "2px 6px", letterSpacing: "-1px", fontFamily: "Arial, sans-serif" }}>a</span>
          <span style={{ background: themes.success, color: "#fff", fontWeight: "900", fontSize: "22px", padding: "2px 6px", letterSpacing: "-1px", fontFamily: "Arial, sans-serif" }}>y</span>
        </div>
        <div>
          <div style={{ fontFamily: "Arial, sans-serif", fontWeight: "700", fontSize: "16px", letterSpacing: "0.05em", color: themes.text }}>LISTING GENERATOR</div>
          <div style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: themes.muted, letterSpacing: "0.08em" }}>AI-POWERED SEO FOR CLOTHING & ACCESSORIES</div>
        </div>
      </div>

      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "28px 20px" }}>
        {/* Input Area */}
        <div style={{ background: themes.card, border: `1px solid ${themes.border}`, borderRadius: "10px", padding: "24px", marginBottom: "28px" }}>
          <label style={{ display: "block", fontFamily: "Arial, sans-serif", fontSize: "13px", fontWeight: "700", letterSpacing: "0.1em", color: themes.accent, marginBottom: "12px" }}>
            PASTE PRODUCT DETAILS
          </label>
          <div style={{ fontSize: "12px", color: themes.muted, fontFamily: "Arial, sans-serif", marginBottom: "12px" }}>
            Copy & paste the product title, description, bullet points, material, size info — anything from Amazon or your supplier. The more detail, the better!
          </div>
          <textarea
            value={productInput}
            onChange={(e) => setProductInput(e.target.value)}
            placeholder="e.g. Women's Floral Wrap Midi Dress — 95% Polyester 5% Spandex — Available in S/M/L/XL — V-neck, short flutter sleeves, adjustable tie waist, flowy skirt, perfect for summer weddings, brunch, vacation..."
            style={{
              width: "100%",
              minHeight: "150px",
              background: themes.surface,
              border: `1px solid ${themes.border}`,
              borderRadius: "8px",
              color: themes.text,
              fontFamily: "Arial, sans-serif",
              fontSize: "14px",
              padding: "14px",
              resize: "vertical",
              outline: "none",
              boxSizing: "border-box",
              lineHeight: "1.6",
            }}
          />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "14px" }}>
            <span style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", color: themes.muted }}>
              {productInput.length} characters
            </span>
            <button
              onClick={generate}
              disabled={loading || !productInput.trim()}
              style={{
                background: loading || !productInput.trim() ? themes.accentDim : themes.accent,
                color: "#000",
                border: "none",
                borderRadius: "6px",
                padding: "11px 28px",
                fontFamily: "Arial, sans-serif",
                fontWeight: "800",
                fontSize: "13px",
                letterSpacing: "0.06em",
                cursor: loading || !productInput.trim() ? "not-allowed" : "pointer",
                transition: "all 0.2s",
              }}
            >
              {loading ? "⚙ GENERATING..." : "⚡ GENERATE LISTING"}
            </button>
          </div>
        </div>

        {error && (
          <div style={{ background: "#2a1010", border: "1px solid #a03030", borderRadius: "8px", padding: "14px 18px", marginBottom: "20px", fontFamily: "Arial, sans-serif", fontSize: "13px", color: "#f08080" }}>
            {error}
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", padding: "50px 20px" }}>
            <div style={{ fontSize: "36px", marginBottom: "16px", animation: "spin 1s linear infinite" }}>⚙</div>
            <div style={{ fontFamily: "Arial, sans-serif", color: themes.muted, fontSize: "14px", letterSpacing: "0.08em" }}>
              ANALYZING PRODUCT & BUILDING OPTIMIZED LISTING...
            </div>
            <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {listing && (
          <div style={{ background: themes.card, border: `1px solid ${themes.border}`, borderRadius: "10px", overflow: "hidden" }}>
            {/* Tabs */}
            <div style={{ display: "flex", borderBottom: `1px solid ${themes.border}`, overflowX: "auto" }}>
              {tabs.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key)}
                  style={{
                    background: activeTab === t.key ? themes.accent : "transparent",
                    color: activeTab === t.key ? "#000" : themes.muted,
                    border: "none",
                    borderBottom: activeTab === t.key ? `2px solid ${themes.accent}` : "2px solid transparent",
                    padding: "13px 18px",
                    fontFamily: "Arial, sans-serif",
                    fontWeight: "700",
                    fontSize: "12px",
                    letterSpacing: "0.06em",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    transition: "all 0.2s",
                  }}
                >
                  {t.label.toUpperCase()}
                </button>
              ))}
            </div>

            <div style={{ padding: "24px" }}>
              {/* TITLE & SEO TAB */}
              {activeTab === "title" && (
                <div>
                  <Section label="EBAY TITLE" charLimit={80} value={listing.title} onCopy={() => copyText(listing.title, "title")} copied={copied === "title"} accent={themes.accent}>
                    <div style={{ fontSize: "17px", fontFamily: "Arial, sans-serif", fontWeight: "700", color: themes.ebayBlue, lineHeight: "1.4", letterSpacing: "0.01em" }}>
                      {listing.title}
                    </div>
                    <CharBar length={listing.title?.length || 0} max={80} />
                  </Section>

                  {listing.subtitle && (
                    <Section label="SUBTITLE (55 chars)" charLimit={55} value={listing.subtitle} onCopy={() => copyText(listing.subtitle, "subtitle")} copied={copied === "subtitle"} accent={themes.accent}>
                      <div style={{ fontSize: "14px", fontFamily: "Arial, sans-serif", color: themes.muted, fontStyle: "italic" }}>{listing.subtitle}</div>
                      <CharBar length={listing.subtitle?.length || 0} max={55} />
                    </Section>
                  )}

                  <Section label="CATEGORY" value={listing.categoryPath} onCopy={() => copyText(listing.categoryPath, "cat")} copied={copied === "cat"} accent={themes.accent}>
                    <div style={{ fontSize: "14px", fontFamily: "Arial, sans-serif", color: themes.text }}>{listing.categoryPath}</div>
                  </Section>

                  <Section label="CONDITION NOTES" value={listing.conditionNotes} onCopy={() => copyText(listing.conditionNotes, "cond")} copied={copied === "cond"} accent={themes.accent}>
                    <div style={{ fontSize: "14px", fontFamily: "Arial, sans-serif", color: themes.text }}>{listing.conditionNotes}</div>
                  </Section>
                </div>
              )}

              {/* KEYWORDS TAB */}
              {activeTab === "keywords" && (
                <div>
                  <Section label="PRIMARY KEYWORDS" value={listing.primaryKeywords?.join(", ")} onCopy={() => copyText(listing.primaryKeywords?.join(", "), "pk")} copied={copied === "pk"} accent={themes.accent}>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {listing.primaryKeywords?.map((kw, i) => (
                        <span key={i} style={{ background: themes.ebayBlue + "22", border: `1px solid ${themes.ebayBlue}55`, borderRadius: "4px", padding: "5px 12px", fontFamily: "Arial, sans-serif", fontSize: "13px", color: themes.text, fontWeight: "600" }}>
                          {kw}
                        </span>
                      ))}
                    </div>
                  </Section>

                  <Section label="LONG-TAIL KEYWORDS" value={listing.longTailKeywords?.join("\n")} onCopy={() => copyText(listing.longTailKeywords?.join("\n"), "lt")} copied={copied === "lt"} accent={themes.accent}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
                      {listing.longTailKeywords?.map((kw, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <span style={{ color: themes.success, fontSize: "10px" }}>🔍</span>
                          <span style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", color: themes.text }}>{kw}</span>
                        </div>
                      ))}
                    </div>
                  </Section>
                </div>
              )}

              {/* ITEM SPECIFICS TAB */}
              {activeTab === "specifics" && (
                <Section label="ITEM SPECIFICS" value={Object.entries(listing.itemSpecifics || {}).map(([k, v]) => `${k}: ${v}`).join("\n")} onCopy={() => copyText(Object.entries(listing.itemSpecifics || {}).map(([k, v]) => `${k}: ${v}`).join("\n"), "spec")} copied={copied === "spec"} accent={themes.accent}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                    {Object.entries(listing.itemSpecifics || {}).map(([key, val]) => (
                      <div key={key} style={{ background: themes.surface, borderRadius: "6px", padding: "10px 14px", border: `1px solid ${themes.border}` }}>
                        <div style={{ fontFamily: "Arial, sans-serif", fontSize: "10px", color: themes.muted, letterSpacing: "0.1em", fontWeight: "700", marginBottom: "4px" }}>{key.toUpperCase()}</div>
                        <div style={{ fontFamily: "Arial, sans-serif", fontSize: "14px", color: themes.text, fontWeight: "600" }}>{val}</div>
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* DESCRIPTION TAB */}
              {activeTab === "description" && (
                <Section label="EBAY DESCRIPTION (HTML)" value={listing.description} onCopy={() => copyText(listing.description, "desc")} copied={copied === "desc"} accent={themes.accent}>
                  <div style={{ background: themes.surface, borderRadius: "8px", padding: "18px", border: `1px solid ${themes.border}` }}>
                    <div style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", color: themes.muted, marginBottom: "10px", letterSpacing: "0.06em" }}>PREVIEW:</div>
                    <div style={{ fontFamily: "Arial, sans-serif", fontSize: "14px", lineHeight: "1.7", color: themes.text }} dangerouslySetInnerHTML={{ __html: listing.description }} />
                  </div>
                  <div style={{ marginTop: "14px" }}>
                    <div style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", color: themes.muted, marginBottom: "8px", letterSpacing: "0.06em" }}>RAW HTML:</div>
                    <textarea
                      readOnly
                      value={listing.description}
                      style={{ width: "100%", minHeight: "120px", background: themes.bg, border: `1px solid ${themes.border}`, borderRadius: "6px", color: themes.muted, fontFamily: "monospace", fontSize: "12px", padding: "12px", resize: "vertical", boxSizing: "border-box" }}
                    />
                  </div>
                </Section>
              )}

              {/* PRO TIPS TAB */}
              {activeTab === "tips" && (
                <Section label="PRO SEO TIPS FOR THIS LISTING" accent={themes.accent}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                    {listing.seoTips?.map((tip, i) => (
                      <div key={i} style={{ display: "flex", gap: "14px", background: themes.surface, borderRadius: "8px", padding: "14px 16px", border: `1px solid ${themes.border}` }}>
                        <div style={{ background: themes.accent, color: "#000", fontWeight: "800", fontFamily: "Arial, sans-serif", fontSize: "13px", width: "26px", height: "26px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{i + 1}</div>
                        <div style={{ fontFamily: "Arial, sans-serif", fontSize: "14px", color: themes.text, lineHeight: "1.6" }}>{tip}</div>
                      </div>
                    ))}
                  </div>
                </Section>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ label, children, value, onCopy, copied, charLimit, accent }) {
  return (
    <div style={{ marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
        <div style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", fontWeight: "700", letterSpacing: "0.12em", color: accent || "#f0c040" }}>{label}</div>
        {onCopy && (
          <button
            onClick={onCopy}
            style={{
              background: copied ? "#1a3a1a" : "transparent",
              color: copied ? "#40d080" : "#7070a0",
              border: `1px solid ${copied ? "#40d080" : "#2a2a3d"}`,
              borderRadius: "4px",
              padding: "4px 12px",
              fontFamily: "Arial, sans-serif",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              letterSpacing: "0.06em",
              transition: "all 0.2s",
            }}
          >
            {copied ? "✓ COPIED" : "COPY"}
          </button>
        )}
      </div>
      {children}
    </div>
  );
}

function CharBar({ length, max }) {
  const pct = Math.min((length / max) * 100, 100);
  const color = pct > 95 ? "#e53238" : pct > 80 ? "#f0c040" : "#40d080";
  return (
    <div style={{ marginTop: "10px" }}>
      <div style={{ height: "4px", background: "#2a2a3d", borderRadius: "2px", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: "2px", transition: "width 0.4s" }} />
      </div>
      <div style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: color, marginTop: "4px", textAlign: "right" }}>
        {length}/{max} characters
      </div>
    </div>
  );
}
