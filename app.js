"use strict";

// ── State ────────────────────────────────────────────────────────────────────

let registers  = [];
let nameIndex  = {};
let addrIndex  = {};
let currentReg = null;
let selectedIdx = -1;

// ── DOM refs ─────────────────────────────────────────────────────────────────

const regInput       = document.getElementById("reg-input");
const dropdown       = document.getElementById("reg-dropdown");
const valInput       = document.getElementById("val-input");
const regInfo        = document.getElementById("reg-info");
const regTitle       = document.getElementById("reg-title");
const regPrivBadge   = document.getElementById("reg-priv-badge");
const regAccessBadge = document.getElementById("reg-access-badge");
const regAddrBadge   = document.getElementById("reg-addr-badge");
const regDesc        = document.getElementById("reg-desc");
const regLink        = document.getElementById("reg-link");
const fieldsBody     = document.getElementById("fields-body");
const loadingMsg     = document.getElementById("loading-msg");
const noDataMsg      = document.getElementById("no-data-msg");
const disclaimer     = document.getElementById("profile-disclaimer");

// ── Load data ────────────────────────────────────────────────────────────────

fetch("data/registers.json")
  .then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(data => {
    registers = data;
    nameIndex = {};
    addrIndex = {};
    for (const reg of registers) {
      nameIndex[reg.name.toUpperCase()] = reg;
      if (reg.address) addrIndex[reg.address.toUpperCase()] = reg;
    }
    console.log(`[RVRF] Loaded ${registers.length} CSRs`);
    loadingMsg.hidden = true;
    regInput.disabled = false;
    valInput.disabled = false;
    regInput.focus();
    setDisclaimer();
    handleUrlHash();
  })
  .catch(err => {
    console.error("[RVRF] Failed to load data:", err);
    loadingMsg.hidden = true;
    noDataMsg.hidden = false;
  });

// ── Disclaimer ───────────────────────────────────────────────────────────────

function setDisclaimer() {
  disclaimer.textContent = "Register data is based on the ";
  const a = document.createElement("a");
  a.href = "https://github.com/riscv/riscv-isa-manual/tree/main/src/priv";
  a.target = "_blank";
  a.rel = "noopener";
  a.textContent = "RISC-V Privileged ISA Specification v1.13";
  disclaimer.appendChild(a);
  disclaimer.appendChild(document.createTextNode(
    ". Users are responsible for verifying the correctness of this information."
  ));
}

// ── URL hash navigation ───────────────────────────────────────────────────────

function handleUrlHash() {
  const params = new URLSearchParams(location.search);
  const regParam = (params.get("reg") || "").toUpperCase();
  const valParam = params.get("val") || "";
  // fall back to bare hash for backwards compat
  const hash = regParam || decodeURIComponent(location.hash.slice(1)).toUpperCase();
  if (!hash) return;
  const reg = nameIndex[hash] || addrIndex[hash];
  if (!reg) return;
  if (valParam) valInput.value = valParam;
  selectRegister(reg.name);
}

// ── Autocomplete ─────────────────────────────────────────────────────────────

function showSuggestions(query) {
  const q = query.trim().toUpperCase();
  if (!q) { hideDropdown(); return; }

  const prefix = registers.filter(r => r.name.toUpperCase().startsWith(q));
  const addr   = registers.filter(r =>
    !r.name.toUpperCase().startsWith(q) && r.address && r.address.toUpperCase().startsWith(q)
  );
  const substr = registers.filter(r =>
    !r.name.toUpperCase().startsWith(q) &&
    !(r.address && r.address.toUpperCase().startsWith(q)) &&
    (r.name.toUpperCase().includes(q) || r.long_name.toUpperCase().includes(q))
  );
  const matches = [...prefix, ...addr, ...substr].slice(0, 14);

  if (matches.length === 0) { hideDropdown(); return; }

  dropdown.innerHTML = "";
  selectedIdx = -1;

  for (const reg of matches) {
    const li = document.createElement("li");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", "false");
    li.dataset.name = reg.name;

    const nameSpan = document.createElement("span");
    nameSpan.className = "dd-name";
    nameSpan.textContent = reg.name;

    const addrSpan = document.createElement("span");
    addrSpan.className = "dd-addr";
    addrSpan.textContent = reg.address || "";

    const privSpan = document.createElement("span");
    privSpan.className = "dd-priv " + (reg.privilege || "");
    privSpan.textContent = reg.privilege || "";

    const longSpan = document.createElement("span");
    longSpan.className = "dd-long";
    longSpan.textContent = reg.long_name || "";

    li.appendChild(nameSpan);
    li.appendChild(addrSpan);
    li.appendChild(privSpan);
    li.appendChild(longSpan);

    li.addEventListener("mousedown", e => {
      e.preventDefault();
      selectRegister(reg.name);
    });

    dropdown.appendChild(li);
  }

  dropdown.hidden = false;
}

function hideDropdown() {
  dropdown.hidden = true;
  selectedIdx = -1;
}

function moveSuggestion(dir) {
  const items = dropdown.querySelectorAll("li");
  if (!items.length) return;
  if (selectedIdx >= 0) items[selectedIdx].setAttribute("aria-selected", "false");
  selectedIdx = (selectedIdx + dir + items.length) % items.length;
  items[selectedIdx].setAttribute("aria-selected", "true");
  items[selectedIdx].scrollIntoView({ block: "nearest" });
}

regInput.addEventListener("input", () => showSuggestions(regInput.value));

regInput.addEventListener("keydown", e => {
  if (e.key === "ArrowDown") {
    e.preventDefault();
    if (!dropdown.hidden) moveSuggestion(1);
    else showSuggestions(regInput.value);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    if (!dropdown.hidden) moveSuggestion(-1);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (!dropdown.hidden && selectedIdx >= 0) {
      const item = dropdown.querySelectorAll("li")[selectedIdx];
      if (item) selectRegister(item.dataset.name);
    } else {
      const q = regInput.value.trim().toUpperCase();
      const exact = nameIndex[q] || addrIndex[q];
      if (exact) selectRegister(exact.name);
    }
  } else if (e.key === "Escape") {
    hideDropdown();
  }
});

regInput.addEventListener("blur", () => {
  setTimeout(() => {
    hideDropdown();
    const typed = regInput.value.trim().toUpperCase();
    if (typed && (!currentReg || currentReg.name.toUpperCase() !== typed)) {
      const exact = nameIndex[typed] || addrIndex[typed];
      if (exact) selectRegister(exact.name);
    }
  }, 150);
});

// ── Register selection ────────────────────────────────────────────────────────

function selectRegister(name) {
  const reg = nameIndex[name.toUpperCase()];
  if (!reg) return;

  currentReg = reg;
  regInput.value = reg.name;
  hideDropdown();

  // Header
  regTitle.textContent = reg.long_name ? `${reg.name}  —  ${reg.long_name}` : reg.name;

  regPrivBadge.textContent = reg.privilege ? reg.privilege + "-mode" : "";
  regPrivBadge.className   = "priv-badge " + (reg.privilege || "");
  regPrivBadge.hidden      = !reg.privilege;

  regAccessBadge.textContent = reg.access || "";
  regAccessBadge.className   = "access-badge" + (reg.access === "RO" ? " RO" : "");
  regAccessBadge.hidden      = !reg.access;

  regAddrBadge.textContent = reg.address || "";
  regAddrBadge.hidden      = !reg.address;

  regDesc.textContent = reg.description || "";
  regDesc.hidden = !reg.description;

  regLink.href = reg.spec_url || "#";
  regInfo.hidden = false;

  decodeAndRender();
}

// ── Value parsing ─────────────────────────────────────────────────────────────

function parseValue(str) {
  const s = str.trim().replace(/[\s_]/g, "");
  if (!s) return null;
  try {
    if (/^0[xX][0-9a-fA-F]+$/.test(s)) return BigInt(s);
    if (/^[0-9]+$/.test(s))             return BigInt(s);
    if (/^[0-9a-fA-F]+$/.test(s))       return BigInt("0x" + s);
  } catch { /* ignore */ }
  return null;
}

function extractBits(value, msb, lsb) {
  const width = BigInt(msb - lsb + 1);
  const mask = (1n << width) - 1n;
  return (value >> BigInt(lsb)) & mask;
}

function fmtHex(val, width) {
  const nibbles = Math.max(1, Math.ceil(width / 4));
  return "0x" + val.toString(16).toUpperCase().padStart(nibbles, "0");
}

function fmtBin(val, width) {
  return val.toString(2).padStart(width, "0");
}

function truncate(str, maxLen) {
  if (!str || str.length <= maxLen) return str;
  return str.slice(0, maxLen).trimEnd() + "…";
}

// ── URL sync ──────────────────────────────────────────────────────────────────

function updateUrl() {
  if (!currentReg) return;
  const params = new URLSearchParams({ reg: currentReg.name });
  const val = valInput.value.trim();
  if (val) params.set("val", val);
  history.replaceState(null, "", "?" + params.toString());
}

// ── Render ────────────────────────────────────────────────────────────────────

function decodeAndRender() {
  if (!currentReg) return;
  updateUrl();

  const value = valInput.value.trim() ? parseValue(valInput.value) : null;

  fieldsBody.innerHTML = "";

  for (const field of currentReg.fields) {
    const tr = document.createElement("tr");
    const width = field.msb - field.lsb + 1;

    if (field.reserved) tr.classList.add("is-reserved");

    // Bits
    const tdBits = document.createElement("td");
    tdBits.className = "bits";
    tdBits.textContent = field.msb === field.lsb
      ? String(field.msb)
      : `${field.msb}:${field.lsb}`;
    tr.appendChild(tdBits);

    // Field name
    const tdName = document.createElement("td");
    tdName.className = "field-name";
    tdName.textContent = field.name;
    tr.appendChild(tdName);

    // Type (rwtype)
    const tdType = document.createElement("td");
    tdType.className = "field-type";
    tdType.textContent = field.rwtype || "";
    tr.appendChild(tdType);

    // Value
    const tdVal = document.createElement("td");
    tdVal.className = "field-val";
    if (value !== null && !field.reserved) {
      const bits = extractBits(value, field.msb, field.lsb);
      const hexSpan = document.createElement("span");
      hexSpan.className = "hex";
      hexSpan.textContent = width <= 4 ? bits.toString(10) : fmtHex(bits, width);
      const binSpan = document.createElement("span");
      binSpan.className = "bin";
      binSpan.textContent = width > 1 ? ` (${fmtBin(bits, width)})` : "";
      tdVal.appendChild(hexSpan);
      if (width > 1) tdVal.appendChild(binSpan);
    } else if (value !== null && field.reserved) {
      const hexSpan = document.createElement("span");
      hexSpan.className = "hex";
      const bits = extractBits(value, field.msb, field.lsb);
      hexSpan.textContent = width <= 4 ? bits.toString(10) : fmtHex(bits, width);
      tdVal.appendChild(hexSpan);
    } else {
      tdVal.textContent = "—";
    }
    tr.appendChild(tdVal);

    // Meaning
    const tdMeaning = document.createElement("td");
    tdMeaning.className = "meaning";

    if (value !== null && field.values && field.values.length > 0) {
      const bits = extractBits(value, field.msb, field.lsb);
      const match = field.values.find(v => v.val !== null && BigInt(v.val) === bits);
      if (match) {
        const enumSpan = document.createElement("span");
        enumSpan.className = "enum-match";
        enumSpan.textContent = match.label;
        tdMeaning.appendChild(enumSpan);
        if (field.description) {
          const descDiv = document.createElement("div");
          descDiv.className = "desc";
          descDiv.textContent = truncate(field.description, 100);
          tdMeaning.appendChild(descDiv);
        }
      } else {
        // no enum match — show description + all values hint
        if (field.description) {
          const descDiv = document.createElement("div");
          descDiv.className = "desc";
          descDiv.textContent = truncate(field.description, 140);
          tdMeaning.appendChild(descDiv);
        }
      }
    } else if (field.description) {
      const descDiv = document.createElement("div");
      descDiv.className = "desc";
      descDiv.textContent = truncate(field.description, 140);
      tdMeaning.appendChild(descDiv);
    }

    tr.appendChild(tdMeaning);
    fieldsBody.appendChild(tr);
  }
}

// ── Value input ───────────────────────────────────────────────────────────────

valInput.addEventListener("input", decodeAndRender);

valInput.addEventListener("focus", () => {
  if (!valInput.value && currentReg) {
    valInput.placeholder = "0x0000000000000000";
  }
});
