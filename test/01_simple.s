.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ assigns: _t4 = v1, r = v1, _t3 = v1, z = v2, _c21 = v1, _t2 = v1, j = v3, k = v1, _t1 = v1, _c9 = v1, _c8 = v2, _c6 = v3, _t0 = v4, _c1 = v1
	@ spills:  set()
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

.main_dummy_entry:
	@ dummy;
	@ _c1 = "asdf";
	ldr v1, =.string0
	@ println(_c1);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _t0 = new Foo();
	mov a1, #1
	ldr a2, =#12
	bl calloc(PLT)
	mov v4, a1
	@ _c6 = 420;
	ldr v3, =#420
	@ _c8 = 69420;
	ldr v2, =#69420
	@ _c9 = 12345;
	ldr v1, =#12345
	@ _t1 = _J3Foo_3fooiiiiiE(_t0, 69, _c6, 77, _c8, _c9);
	str v1, [sp, #-4]!
	str v2, [sp, #-4]!
	mov a1, v4
	mov a2, #69
	mov a3, v3
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	mov v1, a1
	@ z = _t1;
	mov v2, v1
	@ k = 69;
	mov v1, #69
	@ j = true;
	mov v3, #1
	@ _t2 = -k;
	rsb v1, v1, #0
	@ println(_t2);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _c21 = 420;
	ldr v1, =#420
	@ println(_c21);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _t3 = !j;
	rsb v1, v3, #1
	@ r = _t3;
	mov v1, v1
	@ println(false);
	mov a1, #0
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ _t4 = !r;
	rsb v1, v1, #1
	@ println(_t4);
	mov a1, v1
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ println(z);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
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
	@ assigns: this = v1, x = v2, y = v3, _t7 = v1, w = v4, k = v2, _t6 = v3, _t5 = v3, _c28 = v3, _c25 = v3, _t4 = v3, m = v3, _c22 = v4, _c19 = v3, _c16 = v3, _t3 = v3, _c13 = v3, _t2 = v4, _t1 = v2, _t0 = v2
	@ spills:  {'m'}
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

	mov v1, a1
	mov v2, a2
	mov v3, a3
._J3Foo_3fooiiiiiE_entry:
	@ dummy;
	@ _t0 = 3 * x;
	lsl v2, v2, #1
	add v2, v2, v2
	@ _t1 = _t0 + y;
	add v2, v2, v3
	@ k = _t1;
	mov v2, v2
	@ _t2 = w + 1;
	add v4, v4, #1
	@ _c13 = 69420;
	ldr v3, =#69420
	@ _t3 = _t2 != _c13;
	cmp v4, v3
	movne v3, #1
	moveq v3, #0
	@ if (_t3) goto .L1;
	cmp v3, #0
	bne ._J3Foo_3fooiiiiiE_L1
._J3Foo_3fooiiiiiE_L2:
	@ _c16 = "sadge";
	ldr v3, =.string4
	@ println(_c16);
	mov a1, v3
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L1:
	@ _c19 = "poggers";
	ldr v3, =.string5
	@ println(_c19);
	mov a1, v3
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_3fooiiiiiE_L3:
	@ _c22 = 12345;
	ldr v4, =#12345
	@ restore m;
	ldr v3, [fp, #12]                      @ restore m
	@ _t4 = m == _c22;
	ldr v3, [fp, #12]                      @ restore m
	cmp v3, v4
	moveq v3, #1
	movne v3, #0
	@ if (_t4) goto .L4;
	cmp v3, #0
	bne ._J3Foo_3fooiiiiiE_L4
._J3Foo_3fooiiiiiE_L5:
	@ _c25 = "riperino";
	ldr v3, =.string6
	@ println(_c25);
	mov a1, v3
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L4:
	@ _c28 = "poggerino";
	ldr v3, =.string7
	@ println(_c28);
	mov a1, v3
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_3fooiiiiiE_L6:
	@ _t5 = this.f1;
	ldr v3, [v1, #0]
	@ println(_t5);
	ldr a1, =.string1_raw
	mov a2, v3
	bl printf(PLT)
	@ _t6 = this.f2;
	ldr v3, [v1, #4]
	@ println(_t6);
	ldr a1, =.string1_raw
	mov a2, v3
	bl printf(PLT)
	@ _t7 = this.f3;
	ldr v1, [v1, #8]
	@ println(_t7);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
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
	sub sp, sp, #4
	mov a1, sp

	bl main_dummy

	add sp, sp, #4

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
	.word 5
.string4_raw:
	.asciz "sadge"

.string5:
	.word 7
.string5_raw:
	.asciz "poggers"

.string6:
	.word 8
.string6_raw:
	.asciz "riperino"

.string7:
	.word 9
.string7_raw:
	.asciz "poggerino"

