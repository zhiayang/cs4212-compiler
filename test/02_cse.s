@ jlite compiler: ./compile.py --dump-ir3 -O -v test/02_cse.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns: '_c1' = v1;  '_c3' = v1;  '_c5' = v1;  '_c7' = v1;  'fff' = v1
	@            'g' = v1;  'eee' = v2;    'f' = v2;  '_t0' = v3;  '_t1' = v3
	@          'ddd' = v3;  'ccc' = v4
	stmfd sp!, {lr}
	stmfd sp!, {v1, v2, v3, v4}
.main_dummy_entry:
	ldr v1, =#300                           @ _c1 = 300;
	mov v4, v1                              @ ccc = _c1;
	ldr v1, =#400                           @ _c3 = 400;
	mov v3, v1                              @ ddd = _c3;
	ldr v1, =#500                           @ _c5 = 500;
	mov v2, v1                              @ eee = _c5;
	ldr v1, =#600                           @ _c7 = 600;
	mov v1, v1                              @ fff = _c7;
	add v3, v4, v3                          @ _t0 = ccc + ddd;
	add v3, v3, v2                          @ _t1 = _t0 + eee;
	add v2, v3, v1                          @ f = _t1 + fff;
	ldr a1, =.string0_raw                   @ println(f);
	mov a2, v2
	bl printf(PLT)
	add v1, v3, v1                          @ g = _t1 + fff;
	ldr a1, =.string0_raw                   @ println(g);
	mov a2, v1
	bl printf(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, v3, v4}
	ldmfd sp!, {pc}


.global _J3Foo_11side_effectE
.type _J3Foo_11side_effectE, %function
_J3Foo_11side_effectE:
	@ spills:  <none>
	@ assigns: '_c1' = v1
	stmfd sp!, {lr}
	stmfd sp!, {v1}
._J3Foo_11side_effectE_entry:
	ldr v1, =.string1                       @ _c1 = "you should see this twice";
	mov a1, v1                              @ println(_c1);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, #69                             @ return 69;
	b ._J3Foo_11side_effectE_exit
._J3Foo_11side_effectE_exit:
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
    .word 3
.string0_raw:
    .asciz "%d\n"

.string1:
    .word 25
.string1_raw:
    .asciz "you should see this twice"

