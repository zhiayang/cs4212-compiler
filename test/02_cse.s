@ jlite compiler: ./compile.py --dump-ir3 -O -v test/02_cse.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  'x'
	@ assigns: '_c17' = v1;  '_c22' = v1;   '_c3' = v1;   '_c5' = v1;     'b' = v1
	@           'baz' = v1;     'x' = v1;   'foo' = v2;   'bar' = v3;   '_t0' = v4
	@             'a' = v4
	stmfd sp!, {lr}
	sub sp, sp, #8
	stmfd sp!, {v1, v2, v3, v4}
.main_dummy_entry:
	mov v2, #69                             @ foo = 69;
	ldr v1, =#420                           @ _c3 = 420;
	mov v3, v1                              @ bar = _c3;
	ldr v1, =#1234                          @ _c5 = 1234;
	mov v1, v1                              @ baz = _c5;
	add v4, v2, v3                          @ _t0 = foo + bar;
	add v1, v4, v1                          @ x = _t0 + baz;
	str v1, [sp, #4]                        @ spill x;
	mov v4, v4                              @ a = _t0;
	b .main_dummy_L1                        @ if (true) goto .L1;
	b .main_dummy_L2                        @ goto .L2;
.main_dummy_L2:
	ldr v1, =.string0                       @ _c17 = "sadge";
	mov a1, v1                              @ println(_c17);
	add a1, a1, #4
	bl puts(PLT)
	mov v2, #69                             @ foo = 69;
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L1:
	ldr v1, =.string1                       @ _c22 = "kekw";
	mov a1, v1                              @ println(_c22);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L3:
	add v1, v2, v3                          @ b = foo + bar;
	ldr a1, =.string2_raw                   @ println(a);
	mov a2, v4
	bl printf(PLT)
	ldr a1, =.string2_raw                   @ println(b);
	mov a2, v1
	bl printf(PLT)
	ldr v1, [sp, #4]                        @ restore x;
	ldr a1, =.string2_raw                   @ println(x);
	mov a2, v1
	bl printf(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #8
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
    .asciz "sadge"

.string1:
    .word 4
.string1_raw:
    .asciz "kekw"

.string2:
    .word 3
.string2_raw:
    .asciz "%d\n"

