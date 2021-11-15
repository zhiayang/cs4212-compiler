.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #16
	@ prologue

.main_dummy_entry:
	@ _t0 = _J3Foo_3fooiiE(foo, 69, 420);
	@ NOT IMPLEMENTED (expression)
	@ println("asdf");
	ldr a3, =.string0
	str a1, [fp, #-8]
	mov a1, a3
	add a1, a1, #4
	bl puts(PLT)
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	add sp, sp, #16
	ldmfd sp!, {fp, pc}
	

.global _J3Foo_3fooiiE
.type _J3Foo_3fooiiE, %function
_J3Foo_3fooiiE:
	stmfd sp!, {v1, v2, v3, v4, v5, fp, lr}
	mov fp, sp
	sub sp, sp, #40
	@ prologue

._J3Foo_3fooiiE_entry:
	@ _t0 = 3 * x;
	mov a4, a2, lsl #2
	add a4, a4, a2
	@ _t1 = _t0 + y;
	add v1, a4, a3
	@ k = _t1;
	mov v2, v1
	@ _t2 = k == 1;
	eor v3, v3, v3
	moveq v3, #1
	@ if (_t2) goto .L1;
	cmp v3, #0
	bne ._J3Foo_3fooiiE_L1
._J3Foo_3fooiiE_L2:
	@ println("omegalul");
	ldr v4, =.string1
	str a1, [fp, #-24]
	mov a1, v4
	add a1, a1, #4
	bl puts(PLT)
	@ _t4 = 5 * k;
	mov v4, v2, lsl #4
	add v4, v4, v2
	@ k = _t4;
	mov v2, v4
	@ goto .L3;
	b ._J3Foo_3fooiiE_L3
._J3Foo_3fooiiE_L1:
	@ println("kekw");
	ldr v5, =.string2
	str a1, [fp, #-24]
	mov a1, v5
	add a1, a1, #4
	bl puts(PLT)
	@ _t3 = 2 * k;
	mov v5, v2, lsl #2
	@ k = _t3;
	mov v2, v5
	@ goto .L3;
	b ._J3Foo_3fooiiE_L3
._J3Foo_3fooiiE_L3:
	@ return k;
	mov a1, v2
	b ._J3Foo_3fooiiE_epilogue

	@ epilogue
._J3Foo_3fooiiE_epilogue:
	add sp, sp, #40
	ldmfd sp!, {v1, v2, v3, v4, v5, fp, pc}
	

	
.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	bl main_dummy

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4

.data
.string0:
	.word 4
	.asciz "asdf"

.string1:
	.word 8
	.asciz "omegalul"

.string2:
	.word 4
	.asciz "kekw"

