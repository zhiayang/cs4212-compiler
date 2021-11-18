@ jlite compiler: compile.py -O test/02_cse.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns: 'foooo' = a1;   '_c11' = v1;   '_c13' = v1;   '_c15' = v1;   '_c17' = v1
	@            '_c2' = v1;   '_c33' = v1;   '_c35' = v1;   '_c37' = v1;    '_c5' = v1
	@            '_c8' = v1;    '_t6' = v1;    '_t9' = v1;      'e' = v1;   '_c21' = v2
	@              'd' = v2;   '_c26' = v3
	stmfd sp!, {lr}
	stmfd sp!, {v1, v2, v3}
.main_dummy_entry:
.main_dummy_L1:
	ldr v1, =.string0                       @ _c2 = "kekw";
	sub sp, sp, #4                          @ println(_c2);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
.main_dummy_L5:
	ldr v1, =.string1                       @ _c5 = "phew";
	sub sp, sp, #4                          @ println(_c5);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
.main_dummy_L7:
	ldr v1, =.string2                       @ _c8 = "cool";
	sub sp, sp, #4                          @ println(_c8);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
.main_dummy_L9:
	ldr v1, =#489                           @ _c11 = 489;
	sub sp, sp, #4                          @ println(_c11);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =#489                           @ _c13 = 489;
	sub sp, sp, #4                          @ println(_c13);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =#520                           @ _c15 = 520;
	sub sp, sp, #4                          @ println(_c15);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =#1723                          @ _c17 = 1723;
	sub sp, sp, #4                          @ println(_c17);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	sub sp, sp, #4                          @ _t6 = _J3Foo_11side_effectE(foooo);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	bl _J3Foo_11side_effectE
	mov v1, a1
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v2, =#300                           @ _c21 = 300;
	add v2, v2, v1                          @ d = _c21 + _t6;
	sub sp, sp, #4                          @ _t9 = _J3Foo_11side_effectE(foooo);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	bl _J3Foo_11side_effectE
	mov v1, a1
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v3, =#300                           @ _c26 = 300;
	add v1, v3, v1                          @ e = _c26 + _t9;
	sub sp, sp, #4                          @ println(d);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v2
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	sub sp, sp, #4                          @ println(e);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =#4200                          @ _c33 = 4200;
	sub sp, sp, #4                          @ println(_c33);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =#4200                          @ _c35 = 4200;
	sub sp, sp, #4                          @ println(_c35);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =#3901                          @ _c37 = 3901;
	sub sp, sp, #4                          @ println(_c37);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string3_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
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

