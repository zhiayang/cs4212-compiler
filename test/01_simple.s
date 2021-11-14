.global main_dummy
.type main_dummy, %function
main_dummy:
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #8
	@ prologue

.main_dummy_entry:
	@ _t0 = _J3Foo_3fooiiE(foo, 69, 420);
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	add sp, sp, #8
	ldmfd sp!, {fp, pc}
	

.global _J3Foo_3fooiiE
.type _J3Foo_3fooiiE, %function
_J3Foo_3fooiiE:
	stmfd sp!, {v1, v2, fp, lr}
	mov fp, sp
	sub sp, sp, #16
	@ prologue

._J3Foo_3fooiiE_entry:
	@ _t0 = 3 * x;
	mov a4, a2, lsl #2
	add a4, a4, a2
	@ _t1 = _t0 + y;
	add v1, a4, a3
	@ k = _t1;
	mov v2, v1
	@ return k;
	mov a1, v2
	b ._J3Foo_3fooiiE_epilogue

	@ epilogue
._J3Foo_3fooiiE_epilogue:
	add sp, sp, #16
	ldmfd sp!, {v1, v2, fp, pc}
	

	
.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	bl main_dummy

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4

