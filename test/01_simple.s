.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #32
	stmfd sp!, {v1, v2, v3}
	@ prologue

.main_dummy_entry:
	@ println("asdf");                     scratch = a2
	ldr a2, =.string0
	str a1, [fp, #-28]                     @ spilling 'this'
	mov a1, a2
	add a1, a1, #4
	bl puts(PLT)
	@ _t0 = _J3Foo_3fooiiiiiE(foo, 69, 420, 77, 69420, 12345);
	str a1, [fp, #-28]                     @ spilling 'this'
	ldr a1, =#12345
	str a1, [sp, #-4]!
	ldr a1, =#69420
	str a1, [sp, #-4]!
	str a2, [fp, #-16]                     @ spilling '_t0'
	ldr a1, [fp, #0]                       @ load 'foo'
	mov a2, #69
	ldr a3, =#420
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	@ k = 69;
	mov a3, #69
	@ j = true;
	mov a4, #1
	@ _t1 = -k;
	rsb v1, a3, #0
	@ println(_t1);
	str a1, [fp, #0]                       @ spilling 'foo'
	str a2, [fp, #-16]                     @ spilling '_t0'
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ println(420);                        scratch = v2
	ldr v2, =#420
	str a1, [fp, #0]                       @ spilling 'foo'
	str a2, [fp, #-16]                     @ spilling '_t0'
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ _t2 = !j;
	rsb v2, a4, #1
	@ r = _t2;
	mov v3, v2
	@ println(false);
	str a1, [fp, #0]                       @ spilling 'foo'
	mov a1, #0
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ println(j);
	str a1, [fp, #0]                       @ spilling 'foo'
	mov a1, a4
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	ldmfd sp!, {v1, v2, v3}
	add sp, sp, #32
	ldmfd sp!, {fp, pc}
	

.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #64
	stmfd sp!, {v1, v2, v3, v4, v5}
	@ prologue

._J3Foo_3fooiiiiiE_entry:
	@ _t0 = 3 * x;
	lsl a4, a2, #1
	add a4, a4, a2
	@ _t1 = _t0 + y;
	add v1, a4, a3
	@ k = _t1;
	mov v2, v1
	@ _t2 = k == 627;                      scratch = v4
	ldr v4, =#627
	mov v3, #0
	cmp v2, v4
	moveq v3, #1
	@ if (_t2) goto .L1;
	cmp v3, #0
	bne ._J3Foo_3fooiiiiiE_L1
._J3Foo_3fooiiiiiE_L2:
	@ println("omegalul");                 scratch = v4
	ldr v4, =.string4
	str a1, [fp, #-36]                     @ spilling 'this'
	mov a1, v4
	add a1, a1, #4
	bl puts(PLT)
	@ _t4 = 5 * k;
	lsl v4, v2, #3
	add v4, v4, v2
	@ k = _t4;
	mov v2, v4
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L1:
	@ println("kekw");                     scratch = v5
	ldr v5, =.string5
	str a1, [fp, #-36]                     @ spilling 'this'
	mov a1, v5
	add a1, a1, #4
	bl puts(PLT)
	@ _t3 = 2 * k;
	lsl v5, v2, #1
	@ k = _t3;
	mov v2, v5
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L3:
	@ _t5 = w + 1;
	str a1, [fp, #-36]                     @ spilling 'this' - for '_t5'
	str a2, [fp, #-40]                     @ spilling 'x' - for 'w'
	ldr a2, [fp, #8]                       @ load(3) 'w'
	add a1, a2, #1
	@ _t6 = _t5 != 69420;
	str a1, [fp, #-24]                     @ spilling '_t5' - for '_t6'
	str a2, [fp, #8]                       @ spilling 'w' - for '_t5'
	ldr a2, [fp, #-24]                     @ load(3) '_t5'
	str a3, [fp, #-44]                     @ spilling 'y'
	ldr a3, =#69420
	mov a1, #0
	cmp a2, a3
	movne a1, #1
	@ if (_t6) goto .L4;
	cmp a1, #0
	bne ._J3Foo_3fooiiiiiE_L4
._J3Foo_3fooiiiiiE_L5:
	@ println("sadge");
	ldr a3, =.string6
	str a1, [fp, #-28]                     @ spilling '_t6'
	mov a1, a3
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L4:
	@ println("poggers");
	ldr a3, =.string7
	str a1, [fp, #-28]                     @ spilling '_t6'
	mov a1, a3
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L6:
	@ _t7 = m == 12345;                     - for '_t7'
	str a1, [fp, #-28]                     @ spilling '_t6' - for 'm'
	ldr a1, [fp, #12]                      @ load(3) 'm'
	str a2, [fp, #-24]                     @ spilling '_t5'
	ldr a2, =#12345
	mov a3, #0
	cmp a1, a2
	moveq a3, #1
	@ if (_t7) goto .L7;
	cmp a3, #0
	bne ._J3Foo_3fooiiiiiE_L7
._J3Foo_3fooiiiiiE_L8:
	@ println("riperino");
	ldr a2, =.string8
	str a1, [fp, #12]                      @ spilling 'm'
	mov a1, a2
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L9;
	b ._J3Foo_3fooiiiiiE_L9
._J3Foo_3fooiiiiiE_L7:
	@ println("poggerino");
	ldr a2, =.string9
	str a1, [fp, #12]                      @ spilling 'm'
	mov a1, a2
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
	ldmfd sp!, {v1, v2, v3, v4, v5}
	add sp, sp, #64
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

