@ jlite compiler: ./compile.py --dump-ir3-lowered -O test/03_phi.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns:  '_c1' = v1;  '_c27' = v1;  '_c30' = v1;  '_c33' = v1;   '_t3' = v1
	@           '_t4' = v1;   '_t7' = v1;   'foo' = v1;  '_c14' = v2;   '_t1' = v2
	@           '_t2' = v2
	stmfd sp!, {lr}
	stmfd sp!, {v1, v2}
.main_dummy_entry:
	ldr v1, =.string0                       @ _c1 = "start";
	mov a1, v1                              @ println(_c1);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, #1                              @ foo = new Foo();
	mov a2, #4
	bl calloc(PLT)
	mov v1, a1
	mov a1, v1                              @ _t1 = _J3Foo_3oneE(foo);
	bl _J3Foo_3oneE
	mov v2, a1
	cmp v2, #69                             @ _t2 = _t1 == 69;
	moveq v2, #1
	movne v2, #0
	cmp v2, #0                              @ if (_t2) goto .L1;
	bne .main_dummy_L1
	b .main_dummy_L2                        @ goto .L2;
.main_dummy_L2:
	mov a1, v1                              @ _t3 = _J3Foo_3twoE(foo);
	bl _J3Foo_3twoE
	mov v1, a1
	ldr v2, =#420                           @ _c14 = 420;
	cmp v1, v2                              @ _t4 = _t3 == _c14;
	moveq v1, #1
	movne v1, #0
	cmp v1, #0                              @ if (_t4) goto .L1;
	bne .main_dummy_L1
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L3:
	mov v1, #0                              @ _t7 = false;
	b .main_dummy_L4                        @ goto .L4;
.main_dummy_L1:
	mov v1, #1                              @ _t7 = true;
	b .main_dummy_L4                        @ goto .L4;
.main_dummy_L4:
	cmp v1, #0                              @ if (_t7) goto .L5;
	bne .main_dummy_L5
	b .main_dummy_L6                        @ goto .L6;
.main_dummy_L6:
	ldr v1, =.string1                       @ _c27 = "failure";
	mov a1, v1                              @ println(_c27);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L7                        @ goto .L7;
.main_dummy_L5:
	ldr v1, =.string2                       @ _c30 = "success";
	mov a1, v1                              @ println(_c30);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L7                        @ goto .L7;
.main_dummy_L7:
	ldr v1, =.string3                       @ _c33 = "end";
	mov a1, v1                              @ println(_c33);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2}
	ldmfd sp!, {pc}


.global _J3Foo_3oneE
.type _J3Foo_3oneE, %function
_J3Foo_3oneE:
	@ spills:  <none>
	@ assigns: '_c1' = v1
	stmfd sp!, {lr}
	stmfd sp!, {v1}
._J3Foo_3oneE_entry:
	ldr v1, =.string4                       @ _c1 = "one";
	mov a1, v1                              @ println(_c1);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, #69                             @ return 69;
	b ._J3Foo_3oneE_exit
._J3Foo_3oneE_exit:
	ldmfd sp!, {v1}
	ldmfd sp!, {pc}


.global _J3Foo_3twoE
.type _J3Foo_3twoE, %function
_J3Foo_3twoE:
	@ spills:  <none>
	@ assigns: '_c1' = v1;  '_c3' = v1
	stmfd sp!, {lr}
	stmfd sp!, {v1}
._J3Foo_3twoE_entry:
	ldr v1, =.string5                       @ _c1 = "you shouldn't see this";
	mov a1, v1                              @ println(_c1);
	add a1, a1, #4
	bl puts(PLT)
	ldr v1, =#420                           @ _c3 = 420;
	mov a1, v1                              @ return _c3;
	b ._J3Foo_3twoE_exit
._J3Foo_3twoE_exit:
	ldmfd sp!, {v1}
	ldmfd sp!, {pc}



.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	@ we need a 'this' argument for this guy, so just allocate nothing.
	sub sp, sp, #4
	mov a1, sp

	bl main_dummy

	add sp, sp, #4

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4

.data
.string0:
    .word 5
.string0_raw:
    .asciz "start"

.string1:
    .word 7
.string1_raw:
    .asciz "failure"

.string2:
    .word 7
.string2_raw:
    .asciz "success"

.string3:
    .word 3
.string3_raw:
    .asciz "end"

.string4:
    .word 3
.string4_raw:
    .asciz "one"

.string5:
    .word 22
.string5_raw:
    .asciz "you shouldn't see this"

