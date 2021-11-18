@ jlite compiler: ./compile.py --dump-ir3 -O -v test/02_cse.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns:   '_c2' = v1;   '_c33' = v1;   '_c35' = v1;   '_c37' = v1;    '_c5' = v1
	@            '_t9' = v1;      'e' = v1;  'foooo' = v1;   '_c11' = v2;   '_c13' = v2
	@           '_c15' = v2;   '_c17' = v2;    '_c8' = v2;    '_t6' = v2;      'd' = v2
	@           '_c21' = v3;   '_c26' = v3
	stmfd sp!, {lr}
	stmfd sp!, {v1, v2, v3}
.main_dummy_entry:
	b .main_dummy_L1                        @ goto .L1;
.main_dummy_L1:
	ldr v1, =.string0                       @ _c2 = "kekw";
	mov a1, v1                              @ println(_c2);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L5                        @ goto .L5;
.main_dummy_L5:
	ldr v1, =.string1                       @ _c5 = "phew";
	mov a1, v1                              @ println(_c5);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L7                        @ goto .L7;
.main_dummy_L7:
	ldr v2, =.string2                       @ _c8 = "cool";
	mov a1, v2                              @ println(_c8);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L9                        @ goto .L9;
.main_dummy_L9:
	ldr v2, =#489                           @ _c11 = 489;
	ldr a1, =.string3_raw                   @ println(_c11);
	mov a2, v2
	bl printf(PLT)
	ldr v2, =#489                           @ _c13 = 489;
	ldr a1, =.string3_raw                   @ println(_c13);
	mov a2, v2
	bl printf(PLT)
	ldr v2, =#520                           @ _c15 = 520;
	ldr a1, =.string3_raw                   @ println(_c15);
	mov a2, v2
	bl printf(PLT)
	ldr v2, =#1723                          @ _c17 = 1723;
	ldr a1, =.string3_raw                   @ println(_c17);
	mov a2, v2
	bl printf(PLT)
	mov a1, v1                              @ _t6 = _J3Foo_11side_effectE(foooo);
	bl _J3Foo_11side_effectE
	mov v2, a1
	ldr v3, =#300                           @ _c21 = 300;
	add v2, v3, v2                          @ d = _c21 + _t6;
	mov a1, v1                              @ _t9 = _J3Foo_11side_effectE(foooo);
	bl _J3Foo_11side_effectE
	mov v1, a1
	ldr v3, =#300                           @ _c26 = 300;
	add v1, v3, v1                          @ e = _c26 + _t9;
	ldr a1, =.string3_raw                   @ println(d);
	mov a2, v2
	bl printf(PLT)
	ldr a1, =.string3_raw                   @ println(e);
	mov a2, v1
	bl printf(PLT)
	ldr v1, =#4200                          @ _c33 = 4200;
	ldr a1, =.string3_raw                   @ println(_c33);
	mov a2, v1
	bl printf(PLT)
	ldr v1, =#4200                          @ _c35 = 4200;
	ldr a1, =.string3_raw                   @ println(_c35);
	mov a2, v1
	bl printf(PLT)
	ldr v1, =#3901                          @ _c37 = 3901;
	ldr a1, =.string3_raw                   @ println(_c37);
	mov a2, v1
	bl printf(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, v3}
	ldmfd sp!, {pc}


.global _J3Foo_11side_effectE
.type _J3Foo_11side_effectE, %function
_J3Foo_11side_effectE:
	@ spills:  <none>
	@ assigns: '_c1' = v1
	stmfd sp!, {lr}
	stmfd sp!, {v1}
._J3Foo_11side_effectE_entry:
	ldr v1, =.string4                       @ _c1 = "you should see this twice";
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
    .word 4
.string0_raw:
    .asciz "kekw"

.string1:
    .word 4
.string1_raw:
    .asciz "phew"

.string2:
    .word 4
.string2_raw:
    .asciz "cool"

.string3:
    .word 3
.string3_raw:
    .asciz "%d\n"

.string4:
    .word 25
.string4_raw:
    .asciz "you should see this twice"

