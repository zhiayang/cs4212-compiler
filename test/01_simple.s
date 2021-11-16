.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ assigns: _t4 = v1, r = v1, _t3 = v1, _c20 = v1, _t2 = v1, j = v2, z = v3, k = v1, _t1 = v1, _c8 = v1, _c7 = v2, _c5 = v3, _t0 = a1, _c0 = v1
	@ spills:  set()
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3}
	@ prologue

.main_dummy_entry:
	@ _c0 = "asdf";
	ldr v1, =.string0
	@ println(_c0);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _t0 = new Foo();
	mov a1, #1
	ldr a2, =#12
	bl calloc(PLT)
	@ _c5 = 420;
	ldr v3, =#420
	@ _c7 = 69420;
	ldr v2, =#69420
	@ _c8 = 12345;
	ldr v1, =#12345
	@ _t1 = _J3Foo_3fooiiiiiE(_t0, 69, _c5, 77, _c7, _c8);
	stmfd sp!, {a1}
	str v1, [sp, #-4]!
	str v2, [sp, #-4]!
	mov a2, #69
	mov a3, v3
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	mov v1, a1
	ldmfd sp!, {a1}
	@ z = _t1;
	mov v3, v1
	@ k = 69;
	mov v1, #69
	@ j = true;
	mov v2, #1
	@ _t2 = -k;
	rsb v1, v1, #0
	@ println(_t2);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _c20 = 420;
	ldr v1, =#420
	@ println(_c20);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _t3 = !j;
	rsb v1, v2, #1
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
	mov a2, v3
	bl printf(PLT)
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	ldmfd sp!, {v1, v2, v3}
	add sp, sp, #0
	ldmfd sp!, {fp, pc}
	

.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	@ assigns: y = a3, this = a1, x = a2, _t4 = v1, _t3 = v1, _t2 = v1, k = v2, _t1 = v1, _t0 = v1
	@ spills:  set()
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2}
	@ prologue

._J3Foo_3fooiiiiiE_entry:
	@ _t0 = 3 * x;
	lsl v1, a2, #1
	add v1, v1, a2
	@ _t1 = _t0 + y;
	add v1, v1, a3
	@ k = _t1;
	mov v2, v1
	@ _t2 = this.f1;
	ldr v1, [a1, #0]
	@ println(_t2);
	stmfd sp!, {a1}
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}
	@ _t3 = this.f2;
	ldr v1, [a1, #4]
	@ println(_t3);
	stmfd sp!, {a1}
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}
	@ _t4 = this.f3;
	ldr v1, [a1, #8]
	@ println(_t4);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ return k;
	mov a1, v2
	b ._J3Foo_3fooiiiiiE_epilogue

	@ epilogue
._J3Foo_3fooiiiiiE_epilogue:
	ldmfd sp!, {v1, v2}
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

