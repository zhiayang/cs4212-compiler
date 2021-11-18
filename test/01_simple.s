@ jlite compiler: compile.py -O test/01_simple.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns:  '_t0' = a1;   '_t2' = a1;   '_c9' = a3;   '_c1' = v1;  '_c12' = v1
	@          '_c16' = v1;  '_c11' = v2
	stmfd sp!, {v1, v2, lr}
.main_dummy_entry:
	ldr v1, =.string0                       @ _c1 = "asdf";
	mov a1, v1                              @ println(_c1);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, #1                              @ _t0 = new Foo();
	mov a2, #12
	bl calloc(PLT)
	bl _J3Foo_4asdfE
	mov a1, #1                              @ _t2 = new Foo();
	mov a2, #12
	bl calloc(PLT)
	ldr a3, =#420                           @ _c9 = 420;
	ldr v2, =#69420                         @ _c11 = 69420;
	ldr v1, =#12345                         @ _c12 = 12345;
	sub sp, sp, #4                          @ _J3Foo_3fooiiiiiE(_t2, 69, _c9, 77, _c11, _c12);; align adjustment
	stmfd sp!, {a3}                         @ caller-save
	str v1, [sp, #-4]!
	str v2, [sp, #-4]!
	mov a2, #69
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	ldmfd sp!, {a3}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a1, =.string1_raw                   @ println(-69);
	mov a2, #-69
	bl printf(PLT)
	ldr v1, =#420                           @ _c16 = 420;
	ldr a1, =.string1_raw                   @ println(_c16);
	mov a2, v1
	bl printf(PLT)
	movs a1, #0                             @ println(false);
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	movs a1, #1                             @ println(true);
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, pc}


.global _J3Foo_4asdfE
.type _J3Foo_4asdfE, %function
_J3Foo_4asdfE:
	@ spills:  <none>
	@ assigns: 
	stmfd sp!, {lr}
._J3Foo_4asdfE_entry:
	mov a1, #69                             @ return 69;
	b ._J3Foo_4asdfE_exit
._J3Foo_4asdfE_exit:
	ldmfd sp!, {pc}


.global _J3Foo_4bsdfiE
.type _J3Foo_4bsdfiE, %function
_J3Foo_4bsdfiE:
	@ spills:  <none>
	@ assigns:    'm' = a2;   '_c1' = v1;     'k' = v1;  '_c14' = v2;  '_c17' = v2
	@          '_c30' = v2;   '_t1' = v2;   '_t2' = v2;   '_t4' = v2
	stmfd sp!, {v1, v2, lr}
._J3Foo_4bsdfiE_entry:
	mov v1, #2                              @ _c1 = 2;
	mul v1, a2, v1                          @ k = m * _c1;
._J3Foo_4bsdfiE_L1:
	cmp v1, #0                              @ _t1 = k > 0;
	bgt ._J3Foo_4bsdfiE_L8
	b ._J3Foo_4bsdfiE_L9                    @ goto .L9;
._J3Foo_4bsdfiE_L8:
	cmp v1, #8                              @ _t2 = k < 8;
	blt ._J3Foo_4bsdfiE_L2
._J3Foo_4bsdfiE_L3:
	ldr v2, =.string4                       @ _c14 = "you should also see this 7 times";
	mov a1, v2                              @ println(_c14);
	add a1, a1, #4
	bl puts(PLT)
	b ._J3Foo_4bsdfiE_L4                    @ goto .L4;
._J3Foo_4bsdfiE_L2:
	ldr v2, =.string5                       @ _c17 = "you should see this 7 times";
	mov a1, v2                              @ println(_c17);
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_4bsdfiE_L4:
	ldr a1, =.string1_raw                   @ println(k);
	mov a2, v1
	bl printf(PLT)
	sub v1, v1, #1                          @ k = k - 1;
	cmp v1, #0                              @ _t4 = k == 0;
	beq ._J3Foo_4bsdfiE_L5
	b ._J3Foo_4bsdfiE_L1                    @ goto .L1;
._J3Foo_4bsdfiE_L5:
	ldr v2, =#569                           @ _c30 = 569;
	ldr a1, =.string1_raw                   @ println(_c30);
	mov a2, v2
	bl printf(PLT)
	b ._J3Foo_4bsdfiE_L1                    @ goto .L1;
._J3Foo_4bsdfiE_L9:
	mov a1, v1                              @ return k;
	b ._J3Foo_4bsdfiE_exit
._J3Foo_4bsdfiE_exit:
	ldmfd sp!, {v1, v2, pc}


.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	@ spills:  <none>
	@ assigns: '_t12' = a1;  '_t14' = a1;  'this' = a1;     'x' = a2;     'y' = a3
	@          '_c45' = v1;  '_c48' = v1;  '_c51' = v1;  '_t10' = v1;  '_t11' = v1
	@           '_t6' = v1;   '_t7' = v1;   '_t9' = v1;     'w' = v1;   '_c1' = v2
	@           '_t0' = v2;     'k' = v2;  '_c14' = v3;  '_c18' = v3;  '_c20' = v3
	@          '_c26' = v3;  '_c28' = v3;  '_c34' = v3;  '_c41' = v3;  '_g23' = v3
	@          '_g31' = v3;  '_g35' = v3;   '_g7' = v3;   '_t3' = v3
	stmfd sp!, {v1, v2, v3, lr}
._J3Foo_3fooiiiiiE_entry:
	mov v2, #3                              @ _c1 = 3;
	mul v2, a2, v2                          @ _t0 = x * _c1;
	add v2, v2, a3                          @ k = _t0 + y;
	mov v3, #102                            @ _g7 = 102;
	str v3, [a1, #8]                        @ storefield: Int, *this.f3 = _g7;
	sub sp, sp, #4                          @ println(k);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v3, =#627                           @ _c14 = 627;
	cmp v2, v3                              @ _t3 = k == _c14;
	beq ._J3Foo_3fooiiiiiE_L10
._J3Foo_3fooiiiiiE_L11:
	ldr v3, =.string6                       @ _c18 = "omegalul";
	sub sp, sp, #4                          @ println(_c18);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v3
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	mov v3, #5                              @ _c20 = 5;
	mul v2, v2, v3                          @ k = k * _c20;
	mov v3, #19                             @ _g23 = 19;
	str v3, [a1, #4]                        @ storefield: Int, *this.f2 = _g23;
	b ._J3Foo_3fooiiiiiE_L12                @ goto .L12;
._J3Foo_3fooiiiiiE_L10:
	ldr v3, =.string7                       @ _c26 = "kekw";
	sub sp, sp, #4                          @ println(_c26);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v3
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	mov v3, #2                              @ _c28 = 2;
	mul v2, v2, v3                          @ k = k * _c28;
	mov v3, #69                             @ _g31 = 69;
	str v3, [a1, #4]                        @ storefield: Int, *this.f2 = _g31;
._J3Foo_3fooiiiiiE_L12:
	ldr v3, =#420                           @ _c34 = 420;
	str v3, [a1, #0]                        @ storefield: Int, *this.f1 = _g35;
	add v1, v1, #1                          @ _t6 = w + 1;
	ldr v3, =#69420                         @ _c41 = 69420;
	cmp v1, v3                              @ _t7 = _t6 != _c41;
	bne ._J3Foo_3fooiiiiiE_L13
._J3Foo_3fooiiiiiE_L14:
	ldr v1, =.string8                       @ _c45 = "sadge";
	sub sp, sp, #4                          @ println(_c45);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	b ._J3Foo_3fooiiiiiE_L16                @ goto .L16;
._J3Foo_3fooiiiiiE_L13:
	ldr v1, =.string9                       @ _c48 = "poggers";
	sub sp, sp, #4                          @ println(_c48);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
._J3Foo_3fooiiiiiE_L16:
	ldr v1, =.string10                      @ _c51 = "poggerino";
	sub sp, sp, #4                          @ println(_c51);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
._J3Foo_3fooiiiiiE_L18:
	ldr v1, [a1, #0]                        @ _t9 = this.f1;
	sub sp, sp, #4                          @ println(_t9);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, [a1, #4]                        @ _t10 = this.f2;
	sub sp, sp, #4                          @ println(_t10);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, [a1, #8]                        @ _t11 = this.f3;
	ldr a1, =.string1_raw                   @ println(_t11);
	mov a2, v1
	bl printf(PLT)
	mov a1, #1                              @ _t12 = new Foo();
	mov a2, #12
	bl calloc(PLT)
	bl _J3Foo_4asdfE
	mov a1, #1                              @ _t14 = new Foo();
	mov a2, #12
	bl calloc(PLT)
	mov a2, #7
	bl _J3Foo_4bsdfiE
	mov a1, v2                              @ return k;
	b ._J3Foo_3fooiiiiiE_exit
._J3Foo_3fooiiiiiE_exit:
	ldmfd sp!, {v1, v2, v3, pc}



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


.global __string_concat
.type __string_concat, %function
__string_concat:
	stmfd sp!, {v1, v2, v3, v4, v5, lr}

	@ takes two args: (the strings, duh) and returns 1 (the result, duh)

	@ 0. save the string pointers into not-a1 and not-a2
	mov v1, a1
	mov v2, a2

	@ 1. load the lengths of the two strings (they are pascal-style but 4 bytes)
	ldr a1, [v1, #0]
	ldr a2, [v2, #0]

	@ 2. get the new length; a1 contains the +5 (for length + null term), v3 the real length
	add v3, a1, a2
	add a1, v3, #5

	@ 3. malloc some memory (memory in a1)
	bl malloc(PLT)




	ldmfd sp!, {v1, v2, v3, v4, v5, pc}

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
    .word 32
.string4_raw:
    .asciz "you should also see this 7 times"

.string5:
    .word 27
.string5_raw:
    .asciz "you should see this 7 times"

.string6:
    .word 8
.string6_raw:
    .asciz "omegalul"

.string7:
    .word 4
.string7_raw:
    .asciz "kekw"

.string8:
    .word 5
.string8_raw:
    .asciz "sadge"

.string9:
    .word 7
.string9_raw:
    .asciz "poggers"

.string10:
    .word 9
.string10_raw:
    .asciz "poggerino"

