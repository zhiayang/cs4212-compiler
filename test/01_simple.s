.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

.main_dummy_entry:
	@ _c0 = asdf;
	ldr v1, =.string0
	@ println(_c0);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _c4 = 420;
	ldr v3, =#420
	@ _c6 = 69420;
	ldr v2, =#69420
	@ _c7 = 12345;
	ldr v1, =#12345
	@ _t0 = _J3Foo_3fooiiiiiE(foo, 69, _c4, 77, _c6, _c7);
	str v1, [sp, #-4]!
	str v2, [sp, #-4]!
	mov a1, v4
	mov a2, #69
	mov a3, v3
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	@ k = 69;
	mov v1, #69
	@ j = true;
	mov v2, #1
	@ _t1 = -k;
	rsb v1, v1, #0
	@ println(_t1);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _c17 = 420;
	ldr v1, =#420
	@ println(_c17);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _t2 = !j;
	rsb v1, v2, #1
	@ r = _t2;
	mov v1, v1
	@ println(false);
	mov a1, #0
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ _t3 = !r;
	rsb v1, v1, #1
	@ println(_t3);
	mov a1, v1
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #0
	ldmfd sp!, {fp, pc}
	

.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

	mov v1, a3
._J3Foo_3fooiiiiiE_entry:
	@ _t0 = 3 * x;
	lsl v2, a2, #1
	add v2, v2, a2
	@ _t1 = _t0 + y;
	add v1, v2, v1
	@ k = _t1;
	mov v2, v1
	@ _c9 = 627;
	ldr v1, =#627
	@ _t2 = k == _c9;
	mov v1, #0
	cmp v2, v1
	moveq v1, #1
	@ if (_t2) goto .L1;
	cmp v1, #0
	bne ._J3Foo_3fooiiiiiE_L1
._J3Foo_3fooiiiiiE_L2:
	@ _c12 = omegalul;
	ldr v1, =.string4
	@ println(_c12);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _t4 = 5 * k;
	lsl v1, v2, #3
	add v1, v1, v2
	@ k = _t4;
	mov v2, v1
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L1:
	@ _c20 = kekw;
	ldr v1, =.string5
	@ println(_c20);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _t3 = 2 * k;
	lsl v1, v2, #1
	@ k = _t3;
	mov v2, v1
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L3:
	@ _t5 = w + 1;
	ldr a4, [fp, #4]                       @ restore w
	add v4, a4, #1
	@ _c32 = 69420;
	ldr v1, =#69420
	@ _t6 = _t5 != _c32;
	mov v1, #0
	cmp v4, v1
	movne v1, #1
	@ if (_t6) goto .L4;
	cmp v1, #0
	bne ._J3Foo_3fooiiiiiE_L4
._J3Foo_3fooiiiiiE_L5:
	@ _c35 = sadge;
	ldr v1, =.string6
	@ println(_c35);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L4:
	@ _c38 = poggers;
	ldr v1, =.string7
	@ println(_c38);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L6:
	@ _c42 = 12345;
	ldr v1, =#12345
	@ _t7 = m == _c42;
	ldr a4, [fp, #8]                       @ restore m
	mov v1, #0
	cmp a4, v1
	moveq v1, #1
	@ if (_t7) goto .L7;
	cmp v1, #0
	bne ._J3Foo_3fooiiiiiE_L7
._J3Foo_3fooiiiiiE_L8:
	@ _c45 = riperino;
	ldr v1, =.string8
	@ println(_c45);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L9;
	b ._J3Foo_3fooiiiiiE_L9
._J3Foo_3fooiiiiiE_L7:
	@ _c48 = poggerino;
	ldr v1, =.string9
	@ println(_c48);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L9;
	b ._J3Foo_3fooiiiiiE_L9
._J3Foo_3fooiiiiiE_L9:
	@ return k;
	mov a1, v2
	b ._J3Foo_3fooiiiiiE_epilogue

	@ epilogue
._J3Foo_3fooiiiiiE_epilogue:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #0
	ldmfd sp!, {fp, pc}
	

	
.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	@ we need a 'this' argument for this guy, so just allocate
	@ nothing.

	bl main_dummy

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4

.data
.string0:
	.word 4
.string0_raw:
	.asciz "asdf"

.string1:
	.word 3
.string1_raw:
	.asciz "%d\n"

.string2:
	.word 5
.string2_raw:
	.asciz "false"

.string3:
	.word 4
.string3_raw:
	.asciz "true"

.string4:
	.word 8
.string4_raw:
	.asciz "omegalul"

.string5:
	.word 4
.string5_raw:
	.asciz "kekw"

.string6:
	.word 5
.string6_raw:
	.asciz "sadge"

.string7:
	.word 7
.string7_raw:
	.asciz "poggers"

.string8:
	.word 8
.string8_raw:
	.asciz "riperino"

.string9:
	.word 9
.string9_raw:
	.asciz "poggerino"

