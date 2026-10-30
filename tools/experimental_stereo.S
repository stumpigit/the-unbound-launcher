// Tail filter for GlassUtil.GetHomeGlassModeFromSettings. The original model
// selector runs first; its result arrives in w0. The retired analytics block
// at the wrapper site gives this filter exactly 232 bytes.
//
// Preference file byte semantics (unbound-experimental-stereo):
//   1 = Force 3D: mono EGlassMode values 1, 5, 10, 11 become SBS 60 Hz (3).
//   2 = Force 2D: stereo EGlassMode values become mono 60 Hz (1). The Unity
//       home selector otherwise returns a stereo mode on 3D glasses, which
//       renders side-by-side on a mono display (one half of the image per
//       eye) whenever the SDK kept the display in 2D.
//   Anything else, unknown modes, and failed reads retain the default.
//
// Known modes are 1..11 (mask 0xFFE); mono members are 1, 5, 10, 11
// (mask 0xC36). x11 is 1 for stereo members, 0 for mono members. The
// override fires only when (flag - 1) equals x11, so Force 3D never touches
// stereo modes and Force 2D never touches mono modes. Result is 3 - 2*x11:
// mono becomes 3, stereo becomes 1.
.text
experimental_stereo:
    sub sp, sp, #48
    str x0, [sp]
    cmp w0, #11
    b.hi done                 // Shift guard: modes above 11 keep the default.
    mov x9, #0xffe
    lsr x9, x9, x0
    tbz w9, #0, done          // Mode 0 and gaps keep the default.
    mov x9, #0xc36
    lsr x9, x9, x0
    and x11, x9, #1
    eor x11, x11, #1          // x11 = 1 for stereo members, 0 for mono.
    str x11, [sp, #24]
    mov x0, #-100
    adr x1, preference_path
    mov x2, #0
    mov x8, #56               // openat
    svc #0
    tbnz x0, #63, done
    mov x9, x0
    add x1, sp, #32
    mov x2, #2                // Reject anything except exactly one byte.
    mov x8, #63               // read
    svc #0
    mov x10, x0
    mov x0, x9
    mov x8, #57               // close, even after a failed read
    svc #0
    subs x10, x10, #1
    b.ne done
    ldrb w10, [sp, #32]
    ldr x11, [sp, #24]
    sub w10, w10, #1
    cmp w10, w11
    b.ne done
    mov w10, #3
    sub w10, w10, w11, lsl #1 // Mono becomes 3 (SBS 60 Hz), stereo 1 (mono 60 Hz).
    str x10, [sp]
done:
    ldr x0, [sp]
    add sp, sp, #48
    ret
preference_path:
    // Pinned original literal; package_identity.py relocates it after native patches.
    .asciz "/data/user/0/com.xreal.evapro.nebula/files/unbound-experimental-stereo"
    .balign 4
