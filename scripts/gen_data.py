#!/usr/bin/env python3
"""Generate data/registers.json from RISC-V privileged ISA spec."""
import json, pathlib

OUT = pathlib.Path(__file__).parent.parent / "data" / "registers.json"
OUT.parent.mkdir(exist_ok=True)

SPEC_BASE   = "https://github.com/riscv/riscv-isa-manual/blob/main/src/priv"
SPEC_BASE_U = "https://github.com/riscv/riscv-isa-manual/blob/main/src"

def wpri(msb, lsb):
    return {"name": "WPRI", "msb": msb, "lsb": lsb,
            "description": "Reserved, writes preserved, reads ignored.",
            "values": [], "reserved": True, "rwtype": "WPRI"}

def wiri(msb, lsb):
    return {"name": "WIRI", "msb": msb, "lsb": lsb,
            "description": "Reserved, writes ignored, reads ignored.",
            "values": [], "reserved": True, "rwtype": "WIRI"}

FS_VS = [
    {"val": 0, "label": "Off — unit disabled or context not initialized"},
    {"val": 1, "label": "Initial — context is at initial (clean) value"},
    {"val": 2, "label": "Clean — context may differ from initial but matches last save"},
    {"val": 3, "label": "Dirty — context has been modified since last save"},
]
XS = [
    {"val": 0, "label": "All off"},
    {"val": 1, "label": "None dirty or clean, some on"},
    {"val": 2, "label": "None dirty, some clean"},
    {"val": 3, "label": "Some dirty"},
]
MPP = [
    {"val": 0, "label": "U — User mode"},
    {"val": 1, "label": "S — Supervisor mode"},
    {"val": 3, "label": "M — Machine mode"},
]
SPP = [
    {"val": 0, "label": "U — User mode"},
    {"val": 1, "label": "S — Supervisor mode"},
]
XL = [
    {"val": 1, "label": "32-bit (XLEN=32)"},
    {"val": 2, "label": "64-bit (XLEN=64)"},
    {"val": 3, "label": "128-bit (XLEN=128)"},
]
ENDIAN = [
    {"val": 0, "label": "Little-endian"},
    {"val": 1, "label": "Big-endian"},
]
TVEC_MODE = [
    {"val": 0, "label": "Direct — all traps set pc to BASE"},
    {"val": 1, "label": "Vectored — exceptions to BASE, interrupts to BASE+4×cause"},
]
SATP_MODE_RV64 = [
    {"val": 0,  "label": "Bare — no translation or protection"},
    {"val": 8,  "label": "Sv39 — 39-bit virtual address, 3-level page table"},
    {"val": 9,  "label": "Sv48 — 48-bit virtual address, 4-level page table"},
    {"val": 10, "label": "Sv57 — 57-bit virtual address, 5-level page table"},
]
SATP_MODE_RV32 = [
    {"val": 0, "label": "Bare — no translation or protection"},
    {"val": 1, "label": "Sv32 — 32-bit virtual address, 2-level page table"},
]
CBIE = [
    {"val": 0, "label": "00 — Disabled (illegal instruction)"},
    {"val": 1, "label": "01 — Enabled (CBO.INVAL performs flush)"},
    {"val": 3, "label": "11 — Enabled (CBO.INVAL performs invalidate)"},
]
PMM = [
    {"val": 0, "label": "00 — Pointer masking disabled (PMLEN=0)"},
    {"val": 1, "label": "01 — Reserved"},
    {"val": 2, "label": "10 — PMLEN = XLEN-57 (7 bits on RV64)"},
    {"val": 3, "label": "11 — PMLEN = XLEN-48 (16 bits on RV64)"},
]

FRM = [
    {"val": 0, "label": "RNE — Round to Nearest, ties to Even"},
    {"val": 1, "label": "RTZ — Round toward Zero"},
    {"val": 2, "label": "RDN — Round Down (toward −∞)"},
    {"val": 3, "label": "RUP — Round Up (toward +∞)"},
    {"val": 4, "label": "RMM — Round to Nearest, ties to Max Magnitude"},
    {"val": 7, "label": "DYN — Dynamic (use frm field; only valid in instruction encoding)"},
]
VXRM = [
    {"val": 0, "label": "rnu — Round to Nearest Up (round-half-up)"},
    {"val": 1, "label": "rne — Round to Nearest Even"},
    {"val": 2, "label": "rdn — Round Down (truncate)"},
    {"val": 3, "label": "rod — Round to Odd (OR bits into LSB)"},
]
VSEW = [
    {"val": 0, "label": "e8 — 8-bit elements"},
    {"val": 1, "label": "e16 — 16-bit elements"},
    {"val": 2, "label": "e32 — 32-bit elements"},
    {"val": 3, "label": "e64 — 64-bit elements"},
]
VLMUL = [
    {"val": 5, "label": "mf8 — LMUL=1/8"},
    {"val": 6, "label": "mf4 — LMUL=1/4"},
    {"val": 7, "label": "mf2 — LMUL=1/2"},
    {"val": 0, "label": "m1  — LMUL=1"},
    {"val": 1, "label": "m2  — LMUL=2"},
    {"val": 2, "label": "m4  — LMUL=4"},
    {"val": 3, "label": "m8  — LMUL=8"},
]
SEED_OPST = [
    {"val": 0, "label": "BIST — Built-In Self-Test in progress"},
    {"val": 1, "label": "WAIT — Entropy not ready; retry"},
    {"val": 2, "label": "ES16 — 16 bits of entropy available in bits[15:0]"},
    {"val": 3, "label": "DEAD — Non-recoverable error"},
]

registers = []

# ──────────────────────────────────────────────────────────────────────────────
# UNPRIVILEGED CSRs — Floating-Point (F extension)
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "fflags",
    "long_name": "Floating-Point Accrued Exceptions",
    "description": "Accumulates floating-point exception flags. Each bit is sticky: set on a matching exception and cleared only by explicit software write.",
    "address": "0x001", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/unpriv/f-st-ext.adoc",
    "fields": [
        wpri(31, 5),
        {"name": "NV", "msb": 4, "lsb": 4, "description": "Invalid Operation: set when a floating-point operation produces an invalid result (e.g., 0/0, ∞−∞, √−1).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "DZ", "msb": 3, "lsb": 3, "description": "Divide by Zero: set when a finite non-zero value is divided by zero.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "OF", "msb": 2, "lsb": 2, "description": "Overflow: set when the rounded result exceeds the representable range.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "UF", "msb": 1, "lsb": 1, "description": "Underflow: set when the result is tiny and suffers a loss of precision.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "NX", "msb": 0, "lsb": 0, "description": "Inexact: set when the rounded result differs from the mathematical result.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "frm",
    "long_name": "Floating-Point Dynamic Rounding Mode",
    "description": "Specifies the dynamic rounding mode used by floating-point instructions that use DYN rounding. Also aliased in fcsr[7:5].",
    "address": "0x002", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/unpriv/f-st-ext.adoc",
    "fields": [
        wpri(31, 3),
        {"name": "FRM", "msb": 2, "lsb": 0, "description": "Floating-point rounding mode.", "values": FRM, "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "fcsr",
    "long_name": "Floating-Point Control and Status Register",
    "description": "Combines the floating-point rounding mode (frm) and accrued exception flags (fflags) into a single CSR. Bits 31:8 are reserved for future standard extensions.",
    "address": "0x003", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/unpriv/f-st-ext.adoc",
    "fields": [
        wpri(31, 8),
        {"name": "FRM",    "msb": 7, "lsb": 5, "description": "Dynamic rounding mode (mirrors frm CSR).", "values": FRM, "reserved": False, "rwtype": "WARL"},
        {"name": "NV",     "msb": 4, "lsb": 4, "description": "Invalid Operation accrued exception flag.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "DZ",     "msb": 3, "lsb": 3, "description": "Divide by Zero accrued exception flag.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "OF",     "msb": 2, "lsb": 2, "description": "Overflow accrued exception flag.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "UF",     "msb": 1, "lsb": 1, "description": "Underflow accrued exception flag.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "NX",     "msb": 0, "lsb": 0, "description": "Inexact accrued exception flag.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

# ──────────────────────────────────────────────────────────────────────────────
# UNPRIVILEGED CSRs — Entropy Source (Zkr extension)
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "seed",
    "long_name": "Entropy Source CSR",
    "description": "Provides access to a hardware entropy source (Zkr). Read with csrrw to poll for fresh entropy; the write value is ignored. Access requires mseccfg.SSEED/USEED to be set.",
    "address": "0x015", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/scalar-crypto.adoc",
    "fields": [
        {"name": "OPST",    "msb": 31, "lsb": 30, "description": "Operation status: indicates whether entropy is available.", "values": SEED_OPST, "reserved": False, "rwtype": "RO"},
        wpri(29, 16),
        {"name": "entropy", "msb": 15, "lsb":  0, "description": "16 bits of randomness, valid only when OPST=ES16. Reads as 0 in other states.", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

# ──────────────────────────────────────────────────────────────────────────────
# UNPRIVILEGED CSRs — Vector (V extension)
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "vstart",
    "long_name": "Vector Start Index Register",
    "description": "Specifies the index of the first element to be executed by a vector instruction. Normally written to 0 by hardware after each vector instruction. Upper bits are WARL (implementation-defined width).",
    "address": "0x008", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        wpri(63, 16),
        {"name": "vstart", "msb": 15, "lsb": 0, "description": "Start element index. Number of writable bits is implementation-defined (at most log2(VLEN)).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "vxsat",
    "long_name": "Vector Fixed-Point Saturation Flag",
    "description": "Single-bit sticky flag set when a vector fixed-point instruction saturates. Also mirrored in vcsr[0]. Write 0 to clear.",
    "address": "0x009", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        wpri(63, 1),
        {"name": "vxsat", "msb": 0, "lsb": 0, "description": "Saturation flag: set when a fixed-point instruction saturates the result.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "vxrm",
    "long_name": "Vector Fixed-Point Rounding Mode Register",
    "description": "Selects the rounding mode for vector fixed-point arithmetic instructions. Also mirrored in vcsr[2:1].",
    "address": "0x00A", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        wpri(63, 2),
        {"name": "vxrm", "msb": 1, "lsb": 0, "description": "Fixed-point rounding mode.", "values": VXRM, "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "vcsr",
    "long_name": "Vector Control and Status Register",
    "description": "Provides unified access to vxrm and vxsat. Writes to vcsr are reflected in vxrm and vxsat and vice versa.",
    "address": "0x00F", "privilege": "U", "access": "RW",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        wpri(63, 3),
        {"name": "vxrm",  "msb": 2, "lsb": 1, "description": "Fixed-point rounding mode (mirrors vxrm CSR).", "values": VXRM, "reserved": False, "rwtype": "WARL"},
        {"name": "vxsat", "msb": 0, "lsb": 0, "description": "Fixed-point saturation flag (mirrors vxsat CSR).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "vl",
    "long_name": "Vector Length Register",
    "description": "Read-only register holding the number of elements to be updated by a vector instruction. Set by vsetvl/vsetvli/vsetivli.",
    "address": "0xC20", "privilege": "U", "access": "RO",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        {"name": "vl", "msb": 63, "lsb": 0, "description": "Active vector length in elements. Range: 0 to VLMAX.", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "vtype",
    "long_name": "Vector Data Type Register",
    "description": "Read-only register set by vsetvl/vsetvli/vsetivli. Encodes element width, register grouping, and agnostic policies. vill=1 means an unsupported configuration was requested.",
    "address": "0xC21", "privilege": "U", "access": "RO",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        {"name": "vill",   "msb": 63, "lsb": 63, "description": "Illegal configuration: set when vsetvl writes an unsupported vtype. All other bits read as 0 when vill=1.", "values": [{"val":0,"label":"Valid configuration"},{"val":1,"label":"Illegal — unsupported vtype requested"}], "reserved": False, "rwtype": "RO"},
        wpri(62, 8),
        {"name": "vma",    "msb":  7, "lsb":  7, "description": "Vector Mask Agnostic: when set, masked-off elements may be written with all 1s or left undisturbed.", "values": [{"val":0,"label":"Undisturbed"},{"val":1,"label":"Agnostic (may write 1s)"}], "reserved": False, "rwtype": "RO"},
        {"name": "vta",    "msb":  6, "lsb":  6, "description": "Vector Tail Agnostic: when set, tail elements (beyond vl) may be written with all 1s or left undisturbed.", "values": [{"val":0,"label":"Undisturbed"},{"val":1,"label":"Agnostic (may write 1s)"}], "reserved": False, "rwtype": "RO"},
        {"name": "vsew",   "msb":  5, "lsb":  3, "description": "Selected Element Width: encodes the element data type width.", "values": VSEW, "reserved": False, "rwtype": "RO"},
        {"name": "vlmul",  "msb":  2, "lsb":  0, "description": "Vector Length Multiplier: controls register grouping (LMUL). Signed 3-bit value; negative values represent fractional LMUL.", "values": VLMUL, "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "vlenb",
    "long_name": "Vector Register Length in Bytes",
    "description": "Read-only constant holding VLEN/8 — the number of bytes in a single vector register. Useful for computing stride values without disturbing vl/vtype.",
    "address": "0xC22", "privilege": "U", "access": "RO",
    "spec_url": f"{SPEC_BASE_U}/v-st-ext.adoc",
    "fields": [
        {"name": "vlenb", "msb": 63, "lsb": 0, "description": "Bytes per vector register = VLEN/8. Design-time constant.", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

# ──────────────────────────────────────────────────────────────────────────────
# SUPERVISOR-LEVEL CSRs
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "sstatus",
    "long_name": "Supervisor Status Register",
    "description": "Tracks and controls the hart's current operating state; a restricted view of mstatus.",
    "address": "0x100", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "SD",    "msb": 63, "lsb": 63, "description": "Dirty summary: set if FS, VS, or XS == Dirty.", "values": [], "reserved": False, "rwtype": "RO"},
        wpri(62, 34),
        {"name": "UXL",  "msb": 33, "lsb": 32, "description": "User XLEN: controls XLEN for U-mode (RV64 only).", "values": XL, "reserved": False, "rwtype": "WARL"},
        wpri(31, 25),
        {"name": "SDT",   "msb": 24, "lsb": 24, "description": "S-mode disable-trap bit (Ssdbltrp): set on trap entry, cleared by SRET. Prevents double-trap from being delivered to S-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "SPELP", "msb": 23, "lsb": 23, "description": "Supervisor previous expected-landing-pad state (Zicfilp): holds ELP prior to trap into S-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(22, 20),
        {"name": "MXR",  "msb": 19, "lsb": 19, "description": "Make eXecutable Readable: when set, loads from execute-only pages succeed.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "SUM",  "msb": 18, "lsb": 18, "description": "Supervisor User Memory access: when set, S-mode may access U-mode pages.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(17, 17),
        {"name": "XS",   "msb": 16, "lsb": 15, "description": "Extension state summary for user-mode extensions.", "values": XS, "reserved": False, "rwtype": "RO"},
        {"name": "FS",   "msb": 14, "lsb": 13, "description": "Floating-point unit state.", "values": FS_VS, "reserved": False, "rwtype": "WARL"},
        wpri(12, 11),
        {"name": "VS",   "msb": 10, "lsb":  9, "description": "Vector unit state.", "values": FS_VS, "reserved": False, "rwtype": "WARL"},
        {"name": "SPP",  "msb":  8, "lsb":  8, "description": "Supervisor Previous Privilege: privilege mode before trap into S-mode.", "values": SPP, "reserved": False, "rwtype": "WARL"},
        wpri(7, 7),
        {"name": "UBE",  "msb":  6, "lsb":  6, "description": "U-mode endianness: 0=little-endian, 1=big-endian for U-mode explicit accesses.", "values": ENDIAN, "reserved": False, "rwtype": "WARL"},
        {"name": "SPIE", "msb":  5, "lsb":  5, "description": "Supervisor Previous Interrupt Enable: value of SIE prior to trap.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(4, 2),
        {"name": "SIE",  "msb":  1, "lsb":  1, "description": "Supervisor Interrupt Enable: when set, interrupts are enabled in S-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(0, 0),
    ],
})

registers.append({
    "name": "sie",
    "long_name": "Supervisor Interrupt Enable Register",
    "description": "Controls which interrupts are enabled in supervisor mode. Writable subset of mie.",
    "address": "0x104", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        wiri(63, 14),
        {"name": "LCOFIE", "msb": 13, "lsb": 13, "description": "Local counter-overflow interrupt enable (Sscofpmf extension).", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(12, 10),
        {"name": "SEIE",  "msb":  9, "lsb":  9, "description": "Supervisor external interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(8, 6),
        {"name": "STIE",  "msb":  5, "lsb":  5, "description": "Supervisor timer interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(4, 2),
        {"name": "SSIE",  "msb":  1, "lsb":  1, "description": "Supervisor software interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(0, 0),
    ],
})

registers.append({
    "name": "stvec",
    "long_name": "Supervisor Trap-Vector Base-Address Register",
    "description": "Holds the trap-vector base address and mode for supervisor traps.",
    "address": "0x105", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "BASE", "msb": 63, "lsb": 2, "description": "Trap-handler base address (4-byte aligned; lower 2 bits always zero when used as address).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "MODE", "msb":  1, "lsb": 0, "description": "Trap-vector mode.", "values": TVEC_MODE, "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "scounteren",
    "long_name": "Supervisor Counter Enable Register",
    "description": "Controls availability of performance counters to U-mode.",
    "address": "0x106", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "HPM31","msb": 31,"lsb": 31,"description": "Enable hpmcounter31 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM30","msb": 30,"lsb": 30,"description": "Enable hpmcounter30 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM29","msb": 29,"lsb": 29,"description": "Enable hpmcounter29 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM28","msb": 28,"lsb": 28,"description": "Enable hpmcounter28 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM27","msb": 27,"lsb": 27,"description": "Enable hpmcounter27 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM26","msb": 26,"lsb": 26,"description": "Enable hpmcounter26 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM25","msb": 25,"lsb": 25,"description": "Enable hpmcounter25 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM24","msb": 24,"lsb": 24,"description": "Enable hpmcounter24 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM23","msb": 23,"lsb": 23,"description": "Enable hpmcounter23 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM22","msb": 22,"lsb": 22,"description": "Enable hpmcounter22 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM21","msb": 21,"lsb": 21,"description": "Enable hpmcounter21 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM20","msb": 20,"lsb": 20,"description": "Enable hpmcounter20 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM19","msb": 19,"lsb": 19,"description": "Enable hpmcounter19 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM18","msb": 18,"lsb": 18,"description": "Enable hpmcounter18 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM17","msb": 17,"lsb": 17,"description": "Enable hpmcounter17 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM16","msb": 16,"lsb": 16,"description": "Enable hpmcounter16 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM15","msb": 15,"lsb": 15,"description": "Enable hpmcounter15 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM14","msb": 14,"lsb": 14,"description": "Enable hpmcounter14 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM13","msb": 13,"lsb": 13,"description": "Enable hpmcounter13 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM12","msb": 12,"lsb": 12,"description": "Enable hpmcounter12 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM11","msb": 11,"lsb": 11,"description": "Enable hpmcounter11 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM10","msb": 10,"lsb": 10,"description": "Enable hpmcounter10 for U-mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM9", "msb":  9,"lsb":  9,"description": "Enable hpmcounter9 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM8", "msb":  8,"lsb":  8,"description": "Enable hpmcounter8 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM7", "msb":  7,"lsb":  7,"description": "Enable hpmcounter7 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM6", "msb":  6,"lsb":  6,"description": "Enable hpmcounter6 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM5", "msb":  5,"lsb":  5,"description": "Enable hpmcounter5 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM4", "msb":  4,"lsb":  4,"description": "Enable hpmcounter4 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM3", "msb":  3,"lsb":  3,"description": "Enable hpmcounter3 for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "IR",   "msb":  2,"lsb":  2,"description": "Enable instret counter for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "TM",   "msb":  1,"lsb":  1,"description": "Enable time counter for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "CY",   "msb":  0,"lsb":  0,"description": "Enable cycle counter for U-mode.", "values":[],"reserved":False,"rwtype":"WARL"},
    ],
})

registers.append({
    "name": "senvcfg",
    "long_name": "Supervisor Environment Configuration Register",
    "description": "Controls certain characteristics of the U-mode execution environment.",
    "address": "0x10A", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        wpri(63, 34),
        {"name": "PMM",   "msb": 33, "lsb": 32, "description": "Pointer masking mode for U-mode (Ssnpm). Read-only zero when not implemented or RV32.", "values": PMM, "reserved": False, "rwtype": "WARL"},
        wpri(31,  8),
        {"name": "CBZE",  "msb":  7, "lsb":  7, "description": "Cache Block Zero (CBO.ZERO) enable for U-mode (Zicboz). 0=illegal, 1=enabled.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "CBCFE", "msb":  6, "lsb":  6, "description": "Cache Block Clean/Flush (CBO.CLEAN/FLUSH) enable for U-mode (Zicbom).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "CBIE",  "msb":  5, "lsb":  4, "description": "Cache Block Invalidate (CBO.INVAL) enable and behavior for U-mode (Zicbom).", "values": CBIE, "reserved": False, "rwtype": "WARL"},
        {"name": "SSE",   "msb":  3, "lsb":  3, "description": "Shadow Stack Enable for U/VU-mode (Zicfiss). 0=inactive, 1=active.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "LPE",   "msb":  2, "lsb":  2, "description": "Landing Pad Enable for U/VU-mode (Zicfilp). 0=disabled, 1=enabled.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(1, 1),
        {"name": "FIOM",  "msb":  0, "lsb":  0, "description": "Fence of I/O implies Memory: in U-mode, FENCE with I/O bits also orders memory accesses.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "sscratch",
    "long_name": "Supervisor Scratch Register",
    "description": "Dedicated scratch register for supervisor mode; typically holds a pointer to the hart-local supervisor context while running user code.",
    "address": "0x140", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "SSCRATCH", "msb": 63, "lsb": 0, "description": "Scratch value for supervisor use.", "values": [], "reserved": False, "rwtype": "RW"},
    ],
})

registers.append({
    "name": "sepc",
    "long_name": "Supervisor Exception Program Counter",
    "description": "Holds the virtual address of the instruction that was interrupted or caused an exception when a trap is taken into S-mode.",
    "address": "0x141", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "PC", "msb": 63, "lsb": 1, "description": "Exception program counter (bits XLEN-1:1). Bit 0 is always 0.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "0",  "msb":  0, "lsb": 0, "description": "Always reads as 0.", "values": [], "reserved": True, "rwtype": "RO"},
    ],
})

_SCAUSE_INTERRUPT = [
    {"val": 1,  "label": "Supervisor software interrupt"},
    {"val": 5,  "label": "Supervisor timer interrupt"},
    {"val": 9,  "label": "Supervisor external interrupt"},
    {"val": 13, "label": "Counter-overflow interrupt (Sscofpmf)"},
]
_SCAUSE_EXCEPTION = [
    {"val": 0,  "label": "Instruction address misaligned"},
    {"val": 1,  "label": "Instruction access fault"},
    {"val": 2,  "label": "Illegal instruction"},
    {"val": 3,  "label": "Breakpoint"},
    {"val": 4,  "label": "Load address misaligned"},
    {"val": 5,  "label": "Load access fault"},
    {"val": 6,  "label": "Store/AMO address misaligned"},
    {"val": 7,  "label": "Store/AMO access fault"},
    {"val": 8,  "label": "Environment call from U-mode"},
    {"val": 9,  "label": "Environment call from S-mode"},
    {"val": 12, "label": "Instruction page fault"},
    {"val": 13, "label": "Load page fault"},
    {"val": 15, "label": "Store/AMO page fault"},
    {"val": 18, "label": "Software check exception (Zicfilp/Zicfiss)"},
    {"val": 19, "label": "Hardware error"},
]

registers.append({
    "name": "scause",
    "long_name": "Supervisor Cause Register",
    "description": "Written by hardware when a trap is taken into S-mode; encodes the trap cause.",
    "address": "0x142", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "Interrupt",      "msb": 63, "lsb": 63, "description": "1 = trap caused by an interrupt; 0 = synchronous exception.", "values": [{"val":0,"label":"Exception"},{"val":1,"label":"Interrupt"}], "reserved": False, "rwtype": "WLRL"},
        {"name": "Exception Code", "msb": 62, "lsb":  0, "description": "Identifies the last exception (Interrupt=0) or interrupt (Interrupt=1).", "values": [], "reserved": False, "rwtype": "WLRL"},
    ],
})

registers.append({
    "name": "stval",
    "long_name": "Supervisor Trap Value Register",
    "description": "Written with exception-specific information when a trap is taken into S-mode (e.g., faulting address or illegal instruction bits).",
    "address": "0x143", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "STVAL", "msb": 63, "lsb": 0, "description": "Trap value (faulting address, or instruction bits for illegal-instruction traps, or 0).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "sip",
    "long_name": "Supervisor Interrupt Pending Register",
    "description": "Shows pending interrupts visible to supervisor mode; writable subset of mip.",
    "address": "0x144", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        wiri(63, 14),
        {"name": "LCOFIP", "msb": 13, "lsb": 13, "description": "Local counter-overflow interrupt pending (Sscofpmf). Read-write.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(12, 10),
        {"name": "SEIP",  "msb":  9, "lsb":  9, "description": "Supervisor external interrupt pending. Read-only (set/cleared by execution environment).", "values": [], "reserved": False, "rwtype": "RO"},
        wiri(8, 6),
        {"name": "STIP",  "msb":  5, "lsb":  5, "description": "Supervisor timer interrupt pending. Read-only (reflects stimecmp comparison when Sstc is implemented).", "values": [], "reserved": False, "rwtype": "RO"},
        wiri(4, 2),
        {"name": "SSIP",  "msb":  1, "lsb":  1, "description": "Supervisor software interrupt pending. Writable by S-mode software.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(0, 0),
    ],
})

registers.append({
    "name": "stimecmp",
    "long_name": "Supervisor Timer Comparison Register",
    "description": "A timer interrupt becomes pending (STIP) when time >= stimecmp (Sstc extension).",
    "address": "0x14D", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "STIMECMP", "msb": 63, "lsb": 0, "description": "64-bit unsigned comparison value. STIP is set when time >= stimecmp.", "values": [], "reserved": False, "rwtype": "RW"},
    ],
})

registers.append({
    "name": "satp",
    "long_name": "Supervisor Address Translation and Protection Register",
    "description": "Controls supervisor-mode address translation: holds root page table PPN, ASID, and translation mode.",
    "address": "0x180", "privilege": "S", "access": "RW",
    "spec_url": f"{SPEC_BASE}/supervisor.adoc",
    "fields": [
        {"name": "MODE (RV64)", "msb": 63, "lsb": 60, "description": "Address-translation mode (RV64). Writing an unsupported value has no effect.", "values": SATP_MODE_RV64, "reserved": False, "rwtype": "WARL"},
        {"name": "ASID (RV64)", "msb": 59, "lsb": 44, "description": "Address Space ID (RV64, up to 16 bits). Facilitates per-address-space TLB flushing.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "PPN (RV64)",  "msb": 43, "lsb":  0, "description": "Physical Page Number of root page table (RV64, 44 bits = PA >> 12).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

# ──────────────────────────────────────────────────────────────────────────────
# MACHINE-LEVEL CSRs
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "mstatus",
    "long_name": "Machine Status Register",
    "description": "Tracks and controls the hart's current operating state. A restricted view appears as sstatus.",
    "address": "0x300", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "SD",   "msb": 63, "lsb": 63, "description": "Dirty summary: set (RO) when FS, VS, or XS == Dirty.", "values": [], "reserved": False, "rwtype": "RO"},
        wpri(62, 38),
        {"name": "MBE",  "msb": 37, "lsb": 37, "description": "M-mode endianness: 0=little-endian, 1=big-endian for M-mode explicit memory accesses.", "values": ENDIAN, "reserved": False, "rwtype": "WARL"},
        {"name": "SBE",  "msb": 36, "lsb": 36, "description": "S-mode endianness: 0=little-endian, 1=big-endian for S-mode explicit memory accesses.", "values": ENDIAN, "reserved": False, "rwtype": "WARL"},
        {"name": "SXL",  "msb": 35, "lsb": 34, "description": "S-mode XLEN (RV64): controls XLEN for S-mode.", "values": XL, "reserved": False, "rwtype": "WARL"},
        {"name": "UXL",  "msb": 33, "lsb": 32, "description": "U-mode XLEN (RV64): controls XLEN for U-mode.", "values": XL, "reserved": False, "rwtype": "WARL"},
        wpri(31, 25),
        {"name": "SDT",  "msb": 24, "lsb": 24, "description": "S-mode disable-trap (Ssdbltrp): mirrors sstatus.SDT; controls double-trap handling in S-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "SPELP","msb": 23, "lsb": 23, "description": "Supervisor previous expected-landing-pad (Zicfilp): holds ELP prior to S-mode trap.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "TSR",  "msb": 22, "lsb": 22, "description": "Trap SRET: when set, SRET executed in S-mode raises an illegal-instruction exception.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "TW",   "msb": 21, "lsb": 21, "description": "Timeout Wait: when set, WFI in less-privileged modes may raise illegal-instruction exception.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "TVM",  "msb": 20, "lsb": 20, "description": "Trap Virtual Memory: when set, satp access and SFENCE.VMA in S-mode trap to M-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "MXR",  "msb": 19, "lsb": 19, "description": "Make eXecutable Readable: when set, loads from execute-only pages succeed.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "SUM",  "msb": 18, "lsb": 18, "description": "Supervisor User Memory access: when set, S-mode may access U-mode pages.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "MPRV", "msb": 17, "lsb": 17, "description": "Modify PRiVilege: when set, M-mode memory accesses use the privilege level in MPP.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "XS",   "msb": 16, "lsb": 15, "description": "Extension state summary for user-mode extensions.", "values": XS, "reserved": False, "rwtype": "RO"},
        {"name": "FS",   "msb": 14, "lsb": 13, "description": "Floating-point unit state.", "values": FS_VS, "reserved": False, "rwtype": "WARL"},
        {"name": "MPP",  "msb": 12, "lsb": 11, "description": "Machine Previous Privilege: privilege mode before trap into M-mode.", "values": MPP, "reserved": False, "rwtype": "WARL"},
        {"name": "VS",   "msb": 10, "lsb":  9, "description": "Vector unit state.", "values": FS_VS, "reserved": False, "rwtype": "WARL"},
        {"name": "SPP",  "msb":  8, "lsb":  8, "description": "Supervisor Previous Privilege: privilege mode before trap into S-mode.", "values": SPP, "reserved": False, "rwtype": "WARL"},
        {"name": "MPIE", "msb":  7, "lsb":  7, "description": "Machine Previous Interrupt Enable: value of MIE prior to M-mode trap.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "UBE",  "msb":  6, "lsb":  6, "description": "U-mode endianness: 0=little-endian, 1=big-endian.", "values": ENDIAN, "reserved": False, "rwtype": "WARL"},
        {"name": "SPIE", "msb":  5, "lsb":  5, "description": "Supervisor Previous Interrupt Enable: value of SIE prior to S-mode trap.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(4, 4),
        {"name": "MIE",  "msb":  3, "lsb":  3, "description": "Machine Interrupt Enable: when set, interrupts are enabled in M-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(2, 2),
        {"name": "SIE",  "msb":  1, "lsb":  1, "description": "Supervisor Interrupt Enable: when set, interrupts are enabled in S-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(0, 0),
    ],
})

registers.append({
    "name": "misa",
    "long_name": "Machine ISA Register",
    "description": "Reports the ISA supported by the hart. Returns 0 if not implemented.",
    "address": "0x301", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "MXL", "msb": 63, "lsb": 62,
         "description": "Machine XLEN (read-only): native base integer ISA width.",
         "values": XL, "reserved": False, "rwtype": "RO"},
        wpri(61, 26),
        {"name": "Z", "msb": 25, "lsb": 25, "description": "Extension 'Z': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "Y", "msb": 24, "lsb": 24, "description": "Extension 'Y': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "X", "msb": 23, "lsb": 23, "description": "Extension 'X': Non-standard extensions present.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "W", "msb": 22, "lsb": 22, "description": "Extension 'W': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "V", "msb": 21, "lsb": 21, "description": "Extension 'V': Vector extension.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "U", "msb": 20, "lsb": 20, "description": "Extension 'U': User mode implemented.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "T", "msb": 19, "lsb": 19, "description": "Extension 'T': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "S", "msb": 18, "lsb": 18, "description": "Extension 'S': Supervisor mode implemented.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "R", "msb": 17, "lsb": 17, "description": "Extension 'R': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "Q", "msb": 16, "lsb": 16, "description": "Extension 'Q': Quad-precision floating-point.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "P", "msb": 15, "lsb": 15, "description": "Extension 'P': Tentatively reserved for Packed-SIMD.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "O", "msb": 14, "lsb": 14, "description": "Extension 'O': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "N", "msb": 13, "lsb": 13, "description": "Extension 'N': Tentatively reserved for User-Level Interrupts.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "M", "msb": 12, "lsb": 12, "description": "Extension 'M': Integer Multiply/Divide.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "L", "msb": 11, "lsb": 11, "description": "Extension 'L': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "K", "msb": 10, "lsb": 10, "description": "Extension 'K': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "J", "msb":  9, "lsb":  9, "description": "Extension 'J': Reserved.", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "I", "msb":  8, "lsb":  8, "description": "Extension 'I': RV32I/64I base ISA.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "H", "msb":  7, "lsb":  7, "description": "Extension 'H': Hypervisor extension.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "G", "msb":  6, "lsb":  6, "description": "Extension 'G': Reserved (shorthand for IMAFD).", "values": [], "reserved": True, "rwtype": "WARL"},
        {"name": "F", "msb":  5, "lsb":  5, "description": "Extension 'F': Single-precision floating-point.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "E", "msb":  4, "lsb":  4, "description": "Extension 'E': RV32E/64E base ISA (read-only complement of I).", "values": [], "reserved": False, "rwtype": "RO"},
        {"name": "D", "msb":  3, "lsb":  3, "description": "Extension 'D': Double-precision floating-point.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "C", "msb":  2, "lsb":  2, "description": "Extension 'C': Compressed instructions.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "B", "msb":  1, "lsb":  1, "description": "Extension 'B': Zba+Zbb+Zbs bit manipulation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "A", "msb":  0, "lsb":  0, "description": "Extension 'A': Atomic instructions.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "medeleg",
    "long_name": "Machine Exception Delegation Register",
    "description": "Bit i set = exception i is delegated to S-mode trap handler (when occurring in S or U mode).",
    "address": "0x302", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wpri(63, 24),
        {"name": "Exc[23:20]", "msb": 23, "lsb": 20, "description": "Custom-use exception delegation bits.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "HardErr",   "msb": 19, "lsb": 19, "description": "Hardware error exception (code 19) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "SwCheck",   "msb": 18, "lsb": 18, "description": "Software check exception (code 18) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(17, 17),
        {"name": "DblTrap",   "msb": 16, "lsb": 16, "description": "Double trap (code 16) delegation — always read-only zero.", "values": [], "reserved": True, "rwtype": "RO"},
        {"name": "StoreAMOPF","msb": 15, "lsb": 15, "description": "Store/AMO page fault (code 15) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(14, 14),
        {"name": "LoadPF",    "msb": 13, "lsb": 13, "description": "Load page fault (code 13) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "InstPF",    "msb": 12, "lsb": 12, "description": "Instruction page fault (code 12) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "MEcall",    "msb": 11, "lsb": 11, "description": "M-mode environment call (code 11) — always read-only zero (never delegatable).", "values": [], "reserved": True, "rwtype": "RO"},
        {"name": "SEcall",    "msb":  9, "lsb":  9, "description": "S-mode environment call (code 9) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "UEcall",    "msb":  8, "lsb":  8, "description": "U-mode environment call (code 8) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "StoreAMOAF","msb":  7, "lsb":  7, "description": "Store/AMO access fault (code 7) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "StoreAMOMA","msb":  6, "lsb":  6, "description": "Store/AMO address misaligned (code 6) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "LoadAF",    "msb":  5, "lsb":  5, "description": "Load access fault (code 5) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "LoadMA",    "msb":  4, "lsb":  4, "description": "Load address misaligned (code 4) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "Breakpt",   "msb":  3, "lsb":  3, "description": "Breakpoint (code 3) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "IllegalI",  "msb":  2, "lsb":  2, "description": "Illegal instruction (code 2) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "InstAF",    "msb":  1, "lsb":  1, "description": "Instruction access fault (code 1) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "InstMA",    "msb":  0, "lsb":  0, "description": "Instruction address misaligned (code 0) delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "mideleg",
    "long_name": "Machine Interrupt Delegation Register",
    "description": "Bit i set = interrupt i is delegated to S-mode. Bit layout matches mip/mie.",
    "address": "0x303", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wiri(63, 14),
        {"name": "LCOFID", "msb": 13, "lsb": 13, "description": "Counter-overflow interrupt delegation (Sscofpmf).", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(12, 12),
        {"name": "MEID",  "msb": 11, "lsb": 11, "description": "Machine external interrupt delegation — normally read-only zero.", "values": [], "reserved": True, "rwtype": "WARL"},
        wiri(10, 10),
        {"name": "SEID",  "msb":  9, "lsb":  9, "description": "Supervisor external interrupt delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(8, 8),
        {"name": "MTID",  "msb":  7, "lsb":  7, "description": "Machine timer interrupt delegation — normally read-only zero.", "values": [], "reserved": True, "rwtype": "WARL"},
        wiri(6, 6),
        {"name": "STID",  "msb":  5, "lsb":  5, "description": "Supervisor timer interrupt delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(4, 4),
        {"name": "MSID",  "msb":  3, "lsb":  3, "description": "Machine software interrupt delegation — normally read-only zero.", "values": [], "reserved": True, "rwtype": "WARL"},
        wiri(2, 2),
        {"name": "SSID",  "msb":  1, "lsb":  1, "description": "Supervisor software interrupt delegation.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(0, 0),
    ],
})

registers.append({
    "name": "mie",
    "long_name": "Machine Interrupt Enable Register",
    "description": "Controls which interrupts are enabled in machine mode.",
    "address": "0x304", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wiri(63, 14),
        {"name": "LCOFIE", "msb": 13, "lsb": 13, "description": "Local counter-overflow interrupt enable (Sscofpmf).", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(12, 12),
        {"name": "MEIE",  "msb": 11, "lsb": 11, "description": "Machine external interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(10, 10),
        {"name": "SEIE",  "msb":  9, "lsb":  9, "description": "Supervisor external interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(8, 8),
        {"name": "MTIE",  "msb":  7, "lsb":  7, "description": "Machine timer interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(6, 6),
        {"name": "STIE",  "msb":  5, "lsb":  5, "description": "Supervisor timer interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(4, 4),
        {"name": "MSIE",  "msb":  3, "lsb":  3, "description": "Machine software interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(2, 2),
        {"name": "SSIE",  "msb":  1, "lsb":  1, "description": "Supervisor software interrupt enable.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(0, 0),
    ],
})

registers.append({
    "name": "mtvec",
    "long_name": "Machine Trap-Vector Base-Address Register",
    "description": "Holds the machine-mode trap-vector base address and mode.",
    "address": "0x305", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "BASE", "msb": 63, "lsb": 2, "description": "Trap-handler base address (4-byte aligned; lower 2 bits are always zero when used as address).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "MODE", "msb":  1, "lsb": 0, "description": "Trap-vector mode.", "values": TVEC_MODE, "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "mcounteren",
    "long_name": "Machine Counter Enable Register",
    "description": "Controls availability of performance-monitoring counters to S-mode (and U-mode if S-mode not present).",
    "address": "0x306", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "HPM31","msb": 31,"lsb": 31,"description": "Enable hpmcounter31 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM30","msb": 30,"lsb": 30,"description": "Enable hpmcounter30 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM29","msb": 29,"lsb": 29,"description": "Enable hpmcounter29 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM28","msb": 28,"lsb": 28,"description": "Enable hpmcounter28 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM27","msb": 27,"lsb": 27,"description": "Enable hpmcounter27 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM26","msb": 26,"lsb": 26,"description": "Enable hpmcounter26 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM25","msb": 25,"lsb": 25,"description": "Enable hpmcounter25 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM24","msb": 24,"lsb": 24,"description": "Enable hpmcounter24 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM23","msb": 23,"lsb": 23,"description": "Enable hpmcounter23 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM22","msb": 22,"lsb": 22,"description": "Enable hpmcounter22 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM21","msb": 21,"lsb": 21,"description": "Enable hpmcounter21 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM20","msb": 20,"lsb": 20,"description": "Enable hpmcounter20 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM19","msb": 19,"lsb": 19,"description": "Enable hpmcounter19 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM18","msb": 18,"lsb": 18,"description": "Enable hpmcounter18 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM17","msb": 17,"lsb": 17,"description": "Enable hpmcounter17 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM16","msb": 16,"lsb": 16,"description": "Enable hpmcounter16 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM15","msb": 15,"lsb": 15,"description": "Enable hpmcounter15 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM14","msb": 14,"lsb": 14,"description": "Enable hpmcounter14 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM13","msb": 13,"lsb": 13,"description": "Enable hpmcounter13 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM12","msb": 12,"lsb": 12,"description": "Enable hpmcounter12 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM11","msb": 11,"lsb": 11,"description": "Enable hpmcounter11 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM10","msb": 10,"lsb": 10,"description": "Enable hpmcounter10 for next-lower privilege mode.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM9", "msb":  9,"lsb":  9,"description": "Enable hpmcounter9 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM8", "msb":  8,"lsb":  8,"description": "Enable hpmcounter8 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM7", "msb":  7,"lsb":  7,"description": "Enable hpmcounter7 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM6", "msb":  6,"lsb":  6,"description": "Enable hpmcounter6 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM5", "msb":  5,"lsb":  5,"description": "Enable hpmcounter5 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM4", "msb":  4,"lsb":  4,"description": "Enable hpmcounter4 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM3", "msb":  3,"lsb":  3,"description": "Enable hpmcounter3 for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "IR",   "msb":  2,"lsb":  2,"description": "Enable instret counter for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "TM",   "msb":  1,"lsb":  1,"description": "Enable time counter for next-lower privilege mode. Also gates stimecmp/vstimecmp access.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "CY",   "msb":  0,"lsb":  0,"description": "Enable cycle counter for next-lower privilege mode.", "values":[],"reserved":False,"rwtype":"WARL"},
    ],
})

registers.append({
    "name": "mcountinhibit",
    "long_name": "Machine Counter-Inhibit Register",
    "description": "Controls which hardware performance-monitoring counters increment. Does not affect accessibility.",
    "address": "0x320", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wpri(31, 32 - 1),  # upper bits past HPM31
        {"name": "HPM31","msb": 31,"lsb": 31,"description": "Inhibit hpmcounter31.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM30","msb": 30,"lsb": 30,"description": "Inhibit hpmcounter30.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM29","msb": 29,"lsb": 29,"description": "Inhibit hpmcounter29.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM28","msb": 28,"lsb": 28,"description": "Inhibit hpmcounter28.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM27","msb": 27,"lsb": 27,"description": "Inhibit hpmcounter27.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM26","msb": 26,"lsb": 26,"description": "Inhibit hpmcounter26.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM25","msb": 25,"lsb": 25,"description": "Inhibit hpmcounter25.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM24","msb": 24,"lsb": 24,"description": "Inhibit hpmcounter24.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM23","msb": 23,"lsb": 23,"description": "Inhibit hpmcounter23.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM22","msb": 22,"lsb": 22,"description": "Inhibit hpmcounter22.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM21","msb": 21,"lsb": 21,"description": "Inhibit hpmcounter21.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM20","msb": 20,"lsb": 20,"description": "Inhibit hpmcounter20.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM19","msb": 19,"lsb": 19,"description": "Inhibit hpmcounter19.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM18","msb": 18,"lsb": 18,"description": "Inhibit hpmcounter18.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM17","msb": 17,"lsb": 17,"description": "Inhibit hpmcounter17.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM16","msb": 16,"lsb": 16,"description": "Inhibit hpmcounter16.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM15","msb": 15,"lsb": 15,"description": "Inhibit hpmcounter15.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM14","msb": 14,"lsb": 14,"description": "Inhibit hpmcounter14.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM13","msb": 13,"lsb": 13,"description": "Inhibit hpmcounter13.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM12","msb": 12,"lsb": 12,"description": "Inhibit hpmcounter12.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM11","msb": 11,"lsb": 11,"description": "Inhibit hpmcounter11.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM10","msb": 10,"lsb": 10,"description": "Inhibit hpmcounter10.","values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM9", "msb":  9,"lsb":  9,"description": "Inhibit hpmcounter9.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM8", "msb":  8,"lsb":  8,"description": "Inhibit hpmcounter8.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM7", "msb":  7,"lsb":  7,"description": "Inhibit hpmcounter7.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM6", "msb":  6,"lsb":  6,"description": "Inhibit hpmcounter6.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM5", "msb":  5,"lsb":  5,"description": "Inhibit hpmcounter5.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM4", "msb":  4,"lsb":  4,"description": "Inhibit hpmcounter4.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "HPM3", "msb":  3,"lsb":  3,"description": "Inhibit hpmcounter3.", "values":[],"reserved":False,"rwtype":"WARL"},
        {"name": "IR",   "msb":  2,"lsb":  2,"description": "Inhibit minstret counter.", "values":[],"reserved":False,"rwtype":"WARL"},
        wpri(1, 1),
        {"name": "CY",   "msb":  0,"lsb":  0,"description": "Inhibit mcycle counter.", "values":[],"reserved":False,"rwtype":"WARL"},
    ],
})

registers.append({
    "name": "menvcfg",
    "long_name": "Machine Environment Configuration Register",
    "description": "Controls certain characteristics of the S-mode and U-mode execution environments.",
    "address": "0x30A", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wpri(63, 64),  # placeholder — will be overwritten
        {"name": "STCE",  "msb": 63, "lsb": 63, "description": "Sstc enable: when set, enables stimecmp and vstimecmp registers.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "PBMTE", "msb": 62, "lsb": 62, "description": "Page-Based Memory Types Enable (Svpbmt). When set, Svpbmt is active for S/U-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "ADUE",  "msb": 61, "lsb": 61, "description": "HGAT PTE A/D Update Enable (Svadu). Enables hardware A/D bit updates for S/U-mode page tables.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "CDE",   "msb": 60, "lsb": 60, "description": "Zicfiss Shadow Stack Enable for VS/VU-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(59, 62 - 59 + 59),
        wpri(59, 34),
        {"name": "PMM",   "msb": 33, "lsb": 32, "description": "Pointer masking mode for S/U-mode (Smnpm/Ssnpm).", "values": PMM, "reserved": False, "rwtype": "WARL"},
        wpri(31,  8),
        {"name": "CBZE",  "msb":  7, "lsb":  7, "description": "CBO.ZERO enable for S/U-mode (Zicboz).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "CBCFE", "msb":  6, "lsb":  6, "description": "CBO.CLEAN/FLUSH enable for S/U-mode (Zicbom).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "CBIE",  "msb":  5, "lsb":  4, "description": "CBO.INVAL enable and behavior for S/U-mode (Zicbom).", "values": CBIE, "reserved": False, "rwtype": "WARL"},
        {"name": "SSE",   "msb":  3, "lsb":  3, "description": "Shadow Stack Enable for S/HS-mode (Zicfiss).", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "LPE",   "msb":  2, "lsb":  2, "description": "Landing Pad Enable for S-mode (Zicfilp).", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(1, 1),
        {"name": "FIOM",  "msb":  0, "lsb":  0, "description": "Fence of I/O implies Memory for S/U-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "mscratch",
    "long_name": "Machine Scratch Register",
    "description": "Dedicated scratch register for M-mode; typically holds a pointer to the hart-local M-mode context.",
    "address": "0x340", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "MSCRATCH", "msb": 63, "lsb": 0, "description": "Scratch value for machine-mode use.", "values": [], "reserved": False, "rwtype": "RW"},
    ],
})

registers.append({
    "name": "mepc",
    "long_name": "Machine Exception Program Counter",
    "description": "Holds the virtual address of the instruction that was interrupted or caused an exception when a trap is taken into M-mode.",
    "address": "0x341", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "PC", "msb": 63, "lsb": 1, "description": "Exception program counter (bits XLEN-1:1). Bit 0 is always 0.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "0",  "msb":  0, "lsb": 0, "description": "Always reads as 0.", "values": [], "reserved": True, "rwtype": "RO"},
    ],
})

_MCAUSE_INTERRUPT = [
    {"val": 1,  "label": "Supervisor software interrupt"},
    {"val": 3,  "label": "Machine software interrupt"},
    {"val": 5,  "label": "Supervisor timer interrupt"},
    {"val": 7,  "label": "Machine timer interrupt"},
    {"val": 9,  "label": "Supervisor external interrupt"},
    {"val": 11, "label": "Machine external interrupt"},
    {"val": 13, "label": "Counter-overflow interrupt (Sscofpmf)"},
]
_MCAUSE_EXCEPTION = [
    {"val": 0,  "label": "Instruction address misaligned"},
    {"val": 1,  "label": "Instruction access fault"},
    {"val": 2,  "label": "Illegal instruction"},
    {"val": 3,  "label": "Breakpoint"},
    {"val": 4,  "label": "Load address misaligned"},
    {"val": 5,  "label": "Load access fault"},
    {"val": 6,  "label": "Store/AMO address misaligned"},
    {"val": 7,  "label": "Store/AMO access fault"},
    {"val": 8,  "label": "Environment call from U-mode"},
    {"val": 9,  "label": "Environment call from S-mode"},
    {"val": 11, "label": "Environment call from M-mode"},
    {"val": 12, "label": "Instruction page fault"},
    {"val": 13, "label": "Load page fault"},
    {"val": 15, "label": "Store/AMO page fault"},
    {"val": 16, "label": "Double trap"},
    {"val": 18, "label": "Software check exception"},
    {"val": 19, "label": "Hardware error"},
]

registers.append({
    "name": "mcause",
    "long_name": "Machine Cause Register",
    "description": "Written by hardware when a trap is taken into M-mode; encodes the trap cause.",
    "address": "0x342", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Interrupt",      "msb": 63, "lsb": 63, "description": "1 = trap caused by an interrupt; 0 = synchronous exception.", "values": [{"val":0,"label":"Exception"},{"val":1,"label":"Interrupt"}], "reserved": False, "rwtype": "WLRL"},
        {"name": "Exception Code", "msb": 62, "lsb":  0, "description": "Identifies the last exception or interrupt cause.", "values": [], "reserved": False, "rwtype": "WLRL"},
    ],
})

registers.append({
    "name": "mtval",
    "long_name": "Machine Trap Value Register",
    "description": "Written with exception-specific information when a trap is taken into M-mode (faulting address, illegal instruction bits, or 0).",
    "address": "0x343", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "MTVAL", "msb": 63, "lsb": 0, "description": "Trap value (faulting virtual address, instruction bits for illegal-instruction traps, or 0).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "mip",
    "long_name": "Machine Interrupt Pending Register",
    "description": "Shows which interrupts are currently pending. Some bits are read-only (set by hardware).",
    "address": "0x344", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wiri(63, 14),
        {"name": "LCOFIP", "msb": 13, "lsb": 13, "description": "Local counter-overflow interrupt pending (Sscofpmf). Read-write.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(12, 12),
        {"name": "MEIP",  "msb": 11, "lsb": 11, "description": "Machine external interrupt pending. Read-only (set by platform interrupt controller).", "values": [], "reserved": False, "rwtype": "RO"},
        wiri(10, 10),
        {"name": "SEIP",  "msb":  9, "lsb":  9, "description": "Supervisor external interrupt pending. Writable by M-mode; OR'd with external interrupt signal.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(8, 8),
        {"name": "MTIP",  "msb":  7, "lsb":  7, "description": "Machine timer interrupt pending. Read-only (cleared by writing memory-mapped mtimecmp).", "values": [], "reserved": False, "rwtype": "RO"},
        wiri(6, 6),
        {"name": "STIP",  "msb":  5, "lsb":  5, "description": "Supervisor timer interrupt pending. Writable by M-mode (or RO when Sstc implemented).", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(4, 4),
        {"name": "MSIP",  "msb":  3, "lsb":  3, "description": "Machine software interrupt pending. Read-only (written via memory-mapped msip register).", "values": [], "reserved": False, "rwtype": "RO"},
        wiri(2, 2),
        {"name": "SSIP",  "msb":  1, "lsb":  1, "description": "Supervisor software interrupt pending. Writable by M-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        wiri(0, 0),
    ],
})

registers.append({
    "name": "mtinst",
    "long_name": "Machine Trap Instruction Register",
    "description": "Written with a pseudo-instruction encoding when a trap is taken into M-mode from a virtual machine (hypervisor extension).",
    "address": "0x34A", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "MTINST", "msb": 63, "lsb": 0, "description": "Trap instruction encoding (pseudo-instruction or 0).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "mtval2",
    "long_name": "Machine Trap Value 2 Register",
    "description": "Used by the hypervisor extension to provide additional trap information (e.g., guest physical address for guest-page faults).",
    "address": "0x34B", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "MTVAL2", "msb": 63, "lsb": 0, "description": "Secondary trap value (e.g., guest PA on guest page fault, or 0).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

registers.append({
    "name": "mvendorid",
    "long_name": "Machine Vendor ID Register",
    "description": "Read-only register providing the JEDEC manufacturer ID of the core provider. Returns 0 if not implemented.",
    "address": "0xF11", "privilege": "M", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Bank",   "msb": 31, "lsb": 7, "description": "Number of JEDEC continuation codes (bank number minus one).", "values": [], "reserved": False, "rwtype": "RO"},
        {"name": "Offset", "msb":  6, "lsb": 0, "description": "Final byte of JEDEC manufacturer ID (parity bit discarded).", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "marchid",
    "long_name": "Machine Architecture ID Register",
    "description": "Read-only register encoding the base microarchitecture. Open-source IDs have MSB=0; commercial IDs have MSB=1.",
    "address": "0xF12", "privilege": "M", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Architecture ID", "msb": 63, "lsb": 0, "description": "Microarchitecture identifier. MSB=0 for open-source, MSB=1 for commercial.", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "mimpid",
    "long_name": "Machine Implementation ID Register",
    "description": "Read-only register encoding the version of the processor implementation.",
    "address": "0xF13", "privilege": "M", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Implementation", "msb": 63, "lsb": 0, "description": "Implementation version (format defined by the implementor).", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "mhartid",
    "long_name": "Hart ID Register",
    "description": "Read-only register containing the integer ID of the hardware thread. One hart must have ID 0.",
    "address": "0xF14", "privilege": "M", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Hart ID", "msb": 63, "lsb": 0, "description": "Unique hardware thread identifier within the execution environment.", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "mconfigptr",
    "long_name": "Machine Configuration Pointer Register",
    "description": "Read-only register holding the physical address of the configuration data structure, or 0 if not implemented.",
    "address": "0xF15", "privilege": "M", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Pointer", "msb": 63, "lsb": 0, "description": "Physical address of the configuration data structure (must be 8-byte aligned), or 0.", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "mcycle",
    "long_name": "Machine Cycle Counter",
    "description": "64-bit counter tracking the number of clock cycles executed on the processor core. Shared between harts on the same core.",
    "address": "0xB00", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Count", "msb": 63, "lsb": 0, "description": "Cycle count (64-bit on RV32 and RV64; mcycleh holds bits 63:32 on RV32).", "values": [], "reserved": False, "rwtype": "RW"},
    ],
})

registers.append({
    "name": "minstret",
    "long_name": "Machine Instructions-Retired Counter",
    "description": "64-bit counter tracking the number of instructions the hart has retired.",
    "address": "0xB02", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Count", "msb": 63, "lsb": 0, "description": "Instructions-retired count (64-bit on RV32 and RV64; minstreth holds bits 63:32 on RV32).", "values": [], "reserved": False, "rwtype": "RW"},
    ],
})

# ──────────────────────────────────────────────────────────────────────────────
# MACHINE-LEVEL CSRs (continued) — PMP, counters, misc
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "mstatush",
    "long_name": "Machine Status High Register (RV32 only)",
    "description": "Upper 32 bits of mstatus for RV32. Holds endianness control bits MBE and SBE.",
    "address": "0x310", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wpri(31, 6),
        {"name": "MBE", "msb": 5, "lsb": 5, "description": "M-mode memory endianness: 0=little-endian, 1=big-endian.", "values": ENDIAN, "reserved": False, "rwtype": "WARL"},
        {"name": "SBE", "msb": 4, "lsb": 4, "description": "S-mode memory endianness: 0=little-endian, 1=big-endian.", "values": ENDIAN, "reserved": False, "rwtype": "WARL"},
        wpri(3, 0),
    ],
})

registers.append({
    "name": "mseccfg",
    "long_name": "Machine Security Configuration Register",
    "description": "Controls PMP security policies (Smepmp), seed CSR access (Zkr), and other security-related settings.",
    "address": "0x747", "privilege": "M", "access": "RW",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        wpri(63, 35),
        {"name": "MLPE",  "msb": 34, "lsb": 34, "description": "Machine Landing Pad Enable (Zicfilp): enables landing-pad enforcement for M-mode indirect calls/jumps.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "PMM",   "msb": 33, "lsb": 32, "description": "Pointer Masking Mode for M-mode (Smmpm): controls pointer masking tag width.", "values": PMM, "reserved": False, "rwtype": "WARL"},
        wpri(31, 10),
        {"name": "USEED", "msb":  9, "lsb":  9, "description": "U-mode seed access (Zkr): when set, U-mode may read the seed CSR.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "SSEED", "msb":  8, "lsb":  8, "description": "S-mode seed access (Zkr): when set, S-mode may read the seed CSR.", "values": [], "reserved": False, "rwtype": "WARL"},
        wpri(7, 3),
        {"name": "MML",   "msb":  2, "lsb":  2, "description": "Machine Mode Lockdown (Smepmp): tightens PMP permissions; M-mode must match a PMP entry to execute.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "MMWP",  "msb":  1, "lsb":  1, "description": "Machine Mode Whitelist Policy (Smepmp): when set, M-mode accesses denied unless matched by a PMP entry.", "values": [], "reserved": False, "rwtype": "WARL"},
        {"name": "RLB",   "msb":  0, "lsb":  0, "description": "Rule Locking Bypass (Smepmp): when set, allows modification of locked PMP entries (must be cleared before locking).", "values": [], "reserved": False, "rwtype": "WARL"},
    ],
})

# PMP A-field encoding
_PMP_A = [
    {"val": 0, "label": "OFF — region disabled"},
    {"val": 1, "label": "TOR — top-of-range"},
    {"val": 2, "label": "NA4 — naturally aligned 4-byte region"},
    {"val": 3, "label": "NAPOT — naturally aligned power-of-two region"},
]

# pmpcfg0–pmpcfg15: each 64-bit reg holds 8 PMP config bytes (RV64)
# In RV64, odd-numbered pmpcfg registers (pmpcfg1, pmpcfg3, …) are illegal.
for i in range(16):
    addr = 0x3A0 + i
    # Build fields: 8 bytes, each 8 bits, from high to low
    fields = []
    for byte in range(7, -1, -1):
        pmp_n = i * 8 + byte
        hi = byte * 8 + 7
        lo = byte * 8
        fields.append({"name": f"pmp{pmp_n}cfg", "msb": hi, "lsb": lo,
                        "description": f"PMP configuration byte for region {pmp_n}. "
                                       f"[7]=L(lock), [6:5]=WPRI, [4:3]=A(addr mode), [2]=X, [1]=W, [0]=R.",
                        "values": [], "reserved": False, "rwtype": "WARL"})
    registers.append({
        "name": f"pmpcfg{i}",
        "long_name": f"Physical Memory Protection Configuration Register {i}",
        "description": f"Holds PMP configuration bytes for PMP regions {i*8}–{i*8+7}. "
                       f"In RV64 this register{'is illegal (use even-numbered pmpcfg only)' if i % 2 == 1 else 'packs 8 config bytes into 64 bits'}.",
        "address": f"0x{addr:03X}", "privilege": "M", "access": "RW",
        "spec_url": f"{SPEC_BASE}/machine.adoc",
        "fields": fields,
    })

# pmpaddr0–pmpaddr63
for i in range(64):
    addr = 0x3B0 + i
    registers.append({
        "name": f"pmpaddr{i}",
        "long_name": f"Physical Memory Protection Address Register {i}",
        "description": f"Encodes bits [55:2] of the physical address for PMP region {i} (RV64). "
                       f"Bits [53:0] of this register correspond to PA[55:2].",
        "address": f"0x{addr:03X}", "privilege": "M", "access": "RW",
        "spec_url": f"{SPEC_BASE}/machine.adoc",
        "fields": [
            wpri(63, 54),
            {"name": "ADDRESS", "msb": 53, "lsb": 0,
             "description": "Physical address bits [55:2] (PA = ADDRESS << 2). Interpretation depends on pmpcfg A field.",
             "values": [], "reserved": False, "rwtype": "WARL"},
        ],
    })

# mhpmevent3–mhpmevent31: hardware performance-monitoring event selectors
for i in range(3, 32):
    addr = 0x320 + i
    registers.append({
        "name": f"mhpmevent{i}",
        "long_name": f"Machine Hardware Performance-Monitoring Event Selector {i}",
        "description": f"Selects the event counted by mhpmcounter{i}. "
                       f"Event encoding is implementation-defined. "
                       f"Sscofpmf adds mode-inhibit and overflow bits in the upper portion.",
        "address": f"0x{addr:03X}", "privilege": "M", "access": "RW",
        "spec_url": f"{SPEC_BASE}/machine.adoc",
        "fields": [
            {"name": "MINH",  "msb": 63, "lsb": 63, "description": "Machine-mode count inhibit (Sscofpmf): when set, counter does not increment in M-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "SINH",  "msb": 62, "lsb": 62, "description": "Supervisor-mode count inhibit (Sscofpmf).", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "UINH",  "msb": 61, "lsb": 61, "description": "User-mode count inhibit (Sscofpmf).", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "VSINH", "msb": 60, "lsb": 60, "description": "VS-mode count inhibit (Sscofpmf, H extension).", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "VUINH", "msb": 59, "lsb": 59, "description": "VU-mode count inhibit (Sscofpmf, H extension).", "values": [], "reserved": False, "rwtype": "WARL"},
            wpri(58, 56),
            {"name": "OF",    "msb": 55, "lsb": 55, "description": "Overflow flag (Sscofpmf): set when counter overflows from all-ones to zero. Sticky; write 0 to clear.", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "EVENT", "msb": 54, "lsb":  0, "description": "Implementation-defined event selector. Selects which hardware event is counted.", "values": [], "reserved": False, "rwtype": "WARL"},
        ],
    })

# mhpmcounter3–mhpmcounter31: hardware performance-monitoring counters
for i in range(3, 32):
    addr = 0xB00 + i
    registers.append({
        "name": f"mhpmcounter{i}",
        "long_name": f"Machine Hardware Performance-Monitoring Counter {i}",
        "description": f"64-bit counter that counts events selected by mhpmevent{i}. "
                       f"Does not increment when the corresponding mhpmevent inhibit bit is set or mcountinhibit.HPM{i} is set.",
        "address": f"0x{addr:03X}", "privilege": "M", "access": "RW",
        "spec_url": f"{SPEC_BASE}/machine.adoc",
        "fields": [
            {"name": "Count", "msb": 63, "lsb": 0, "description": f"Event count (64-bit on RV64; mhpmcounter{i}h holds bits 63:32 on RV32).", "values": [], "reserved": False, "rwtype": "RW"},
        ],
    })

# ──────────────────────────────────────────────────────────────────────────────
# UNPRIVILEGED COUNTER SHADOWS (User-mode readable)
# ──────────────────────────────────────────────────────────────────────────────

registers.append({
    "name": "cycle",
    "long_name": "Cycle Counter (unprivileged shadow)",
    "description": "Read-only shadow of mcycle for U-mode. Accessible when mcounteren.CY and (if S-mode present) scounteren.CY are set.",
    "address": "0xC00", "privilege": "U", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Count", "msb": 63, "lsb": 0, "description": "Cycle count (read-only shadow of mcycle).", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "time",
    "long_name": "Real-Time Counter (unprivileged shadow)",
    "description": "Read-only shadow of the memory-mapped mtime register. Accessible when mcounteren.TM and scounteren.TM are set.",
    "address": "0xC01", "privilege": "U", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Count", "msb": 63, "lsb": 0, "description": "Real-time clock value (shadow of memory-mapped mtime).", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

registers.append({
    "name": "instret",
    "long_name": "Instructions-Retired Counter (unprivileged shadow)",
    "description": "Read-only shadow of minstret for U-mode. Accessible when mcounteren.IR and scounteren.IR are set.",
    "address": "0xC02", "privilege": "U", "access": "RO",
    "spec_url": f"{SPEC_BASE}/machine.adoc",
    "fields": [
        {"name": "Count", "msb": 63, "lsb": 0, "description": "Instructions-retired count (read-only shadow of minstret).", "values": [], "reserved": False, "rwtype": "RO"},
    ],
})

for i in range(3, 32):
    addr = 0xC00 + i
    registers.append({
        "name": f"hpmcounter{i}",
        "long_name": f"Hardware Performance-Monitoring Counter {i} (unprivileged shadow)",
        "description": f"Read-only U-mode shadow of mhpmcounter{i}. "
                       f"Accessible when mcounteren.HPM{i} and scounteren.HPM{i} are set.",
        "address": f"0x{addr:03X}", "privilege": "U", "access": "RO",
        "spec_url": f"{SPEC_BASE}/machine.adoc",
        "fields": [
            {"name": "Count", "msb": 63, "lsb": 0, "description": f"Read-only shadow of mhpmcounter{i}.", "values": [], "reserved": False, "rwtype": "RO"},
        ],
    })

# Fix mcountinhibit — remove the bogus wpri at the top
for r in registers:
    if r["name"] == "mcountinhibit":
        r["fields"] = [f for f in r["fields"] if not (f["name"] == "WPRI" and f["msb"] == 31 and f["lsb"] == 31)]
        break

# Fix menvcfg — deduplicate wpri fields
for r in registers:
    if r["name"] == "menvcfg":
        # Rebuild with correct fields only
        r["fields"] = [
            {"name": "STCE",  "msb": 63, "lsb": 63, "description": "Sstc enable: enables stimecmp and vstimecmp registers for S/VS-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "PBMTE", "msb": 62, "lsb": 62, "description": "Page-Based Memory Types Enable (Svpbmt) for S/U-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "ADUE",  "msb": 61, "lsb": 61, "description": "Hardware A/D bit update enable (Svadu) for S/U-mode page tables.", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "CDE",   "msb": 60, "lsb": 60, "description": "Shadow Stack Enable for VS/VU-mode (Zicfiss hypervisor extension).", "values": [], "reserved": False, "rwtype": "WARL"},
            wpri(59, 34),
            {"name": "PMM",   "msb": 33, "lsb": 32, "description": "Pointer masking mode for next-lower privilege mode (Ssnpm/Smnpm).", "values": PMM, "reserved": False, "rwtype": "WARL"},
            wpri(31, 8),
            {"name": "CBZE",  "msb":  7, "lsb":  7, "description": "CBO.ZERO enable for S/U-mode (Zicboz).", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "CBCFE", "msb":  6, "lsb":  6, "description": "CBO.CLEAN/FLUSH enable for S/U-mode (Zicbom).", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "CBIE",  "msb":  5, "lsb":  4, "description": "CBO.INVAL enable and behavior for S/U-mode (Zicbom).", "values": CBIE, "reserved": False, "rwtype": "WARL"},
            {"name": "SSE",   "msb":  3, "lsb":  3, "description": "Shadow Stack Enable for S/HS-mode (Zicfiss).", "values": [], "reserved": False, "rwtype": "WARL"},
            {"name": "LPE",   "msb":  2, "lsb":  2, "description": "Landing Pad Enable for S-mode (Zicfilp).", "values": [], "reserved": False, "rwtype": "WARL"},
            wpri(1, 1),
            {"name": "FIOM",  "msb":  0, "lsb":  0, "description": "Fence of I/O implies Memory for S/U-mode.", "values": [], "reserved": False, "rwtype": "WARL"},
        ]
        break

OUT.write_text(json.dumps(registers, indent=2))
print(f"Wrote {len(registers)} registers to {OUT}")
