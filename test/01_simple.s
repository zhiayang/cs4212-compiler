@ jlite compiler: compile.py -v -O test/01_simple.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns:  '_c1' = v1;   '_t0' = v1;   '_t1' = v1;     'z' = v1;  '_c21' = v2
	@           '_c9' = v2;   '_t2' = v2;   '_t3' = v2;   '_t4' = v2;     'k' = v2
	@             'r' = v2;   '_c8' = v3;     'j' = v3;   '_c6' = v4
	stmfd sp!, {lr}
	stmfd sp!, {v1, v2, v3, v4}
.main_dummy_entry:
	ldr v1, =.string0                       @ _c1 = "asdf";
	mov a1, v1                              @ println(_c1);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, #1                              @ _t0 = new Foo();
	mov a2, #12
	bl calloc(PLT)
	mov v1, a1
	ldr v4, =#420                           @ _c6 = 420;
	ldr v3, =#69420                         @ _c8 = 69420;
	ldr v2, =#12345                         @ _c9 = 12345;
	str v2, [sp, #-4]!                      @ _t1 = _J3Foo_3fooiiiiiE(_t0, 69, _c6, 77, _c8, _c9);
	str v3, [sp, #-4]!
	mov a1, v1
	mov a2, #69
	mov a3, v4
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	mov v1, a1
	mov v1, v1                              @ z = _t1;
	mov v2, #69                             @ k = 69;
	mov v3, #1                              @ j = true;
	rsb v2, v2, #0                          @ _t2 = -k;
	ldr a1, =.string1_raw                   @ println(_t2);
	mov a2, v2
	bl printf(PLT)
	ldr v2, =#420                           @ _c21 = 420;
	ldr a1, =.string1_raw                   @ println(_c21);
	mov a2, v2
	bl printf(PLT)
	rsb v2, v3, #1                          @ _t3 = !j;
	mov v2, v2                              @ r = _t3;
	movs a1, #0                             @ println(false);
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	rsb v2, v2, #1                          @ _t4 = !r;
	movs a1, v2                             @ println(_t4);
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	ldr a1, =.string1_raw                   @ println(z);
	mov a2, v1
	bl printf(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, v3, v4}
	ldmfd sp!, {pc}


.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	@ spills:  '_c1', 'm', 'y'
	@ assigns:  '_c1' = v1;  '_c16' = v1;  '_c20' = v1;  '_c22' = v1;  '_c30' = v1
	@          '_c32' = v1;  '_c40' = v1;  '_c51' = v1;  '_c54' = v1;  '_c62' = v1
	@          '_c65' = v1;  '_g27' = v1;  '_g37' = v1;  '_g41' = v1;   '_g9' = v1
	@           '_t1' = v1;  '_t10' = v1;   '_t2' = v1;   '_t3' = v1;   '_t4' = v1
	@           '_t5' = v1;   '_t6' = v1;   '_t7' = v1;   '_t8' = v1;   '_t9' = v1
	@             'm' = v1;     'y' = v1;   '_t0' = v2;     'k' = v2;     'x' = v2
	@          'this' = v3;  '_c47' = v4;     'w' = v4
	stmfd sp!, {lr}
	sub sp, sp, #8
	stmfd sp!, {v1, v2, v3, v4}
	mov v3, a1
	mov v2, a2
	mov v1, a3
._J3Foo_3fooiiiiiE_entry:
	str v1, [sp, #4]                        @ spill y;
	mov v1, #3                              @ _c1 = 3;
	str v1, [sp, #0]                        @ spill _c1;
	ldr v1, [sp, #0]                        @ restore _c1;
	mul v2, v2, v1                          @ _t0 = x * _c1;
	ldr v1, [sp, #4]                        @ restore y;
	add v1, v2, v1                          @ _t1 = _t0 + y;
	mov v2, v1                              @ k = _t1;
	mov v1, #102                            @ _g9 = 102;
	str v1, [v3, #8]                        @ storefield: Int, *this.f3 = _g9;
	ldr a1, =.string1_raw                   @ println(k);
	mov a2, v2
	bl printf(PLT)
	mov v1, #50                             @ m = 50;
	str v1, [sp, #20]                       @ spill m;
	ldr v1, =#627                           @ _c16 = 627;
	cmp v2, v1                              @ _t2 = k == _c16;
	moveq v1, #1
	movne v1, #0
	cmp v1, #0                              @ if (_t2) goto .L1;
	bne ._J3Foo_3fooiiiiiE_L1
	b ._J3Foo_3fooiiiiiE_L2                 @ goto .L2;
._J3Foo_3fooiiiiiE_L2:
	ldr v1, =.string4                       @ _c20 = "omegalul";
	mov a1, v1                              @ println(_c20);
	add a1, a1, #4
	bl puts(PLT)
	mov v1, #5                              @ _c22 = 5;
	mul v1, v2, v1                          @ _t4 = k * _c22;
	mov v2, v1                              @ k = _t4;
	mov v1, #19                             @ _g27 = 19;
	str v1, [v3, #4]                        @ storefield: Int, *this.f2 = _g27;
	b ._J3Foo_3fooiiiiiE_L3                 @ goto .L3;
._J3Foo_3fooiiiiiE_L1:
	ldr v1, =.string5                       @ _c30 = "kekw";
	mov a1, v1                              @ println(_c30);
	add a1, a1, #4
	bl puts(PLT)
	mov v1, #2                              @ _c32 = 2;
	mul v1, v2, v1                          @ _t3 = k * _c32;
	mov v2, v1                              @ k = _t3;
	mov v1, #69                             @ _g37 = 69;
	str v1, [v3, #4]                        @ storefield: Int, *this.f2 = _g37;
	b ._J3Foo_3fooiiiiiE_L3                 @ goto .L3;
._J3Foo_3fooiiiiiE_L3:
	ldr v1, =#420                           @ _c40 = 420;
	mov v1, v1                              @ _g41 = _c40;
	str v1, [v3, #0]                        @ storefield: Int, *this.f1 = _g41;
	add v1, v4, #1                          @ _t5 = w + 1;
	ldr v4, =#69420                         @ _c47 = 69420;
	cmp v1, v4                              @ _t6 = _t5 != _c47;
	movne v1, #1
	moveq v1, #0
	cmp v1, #0                              @ if (_t6) goto .L4;
	bne ._J3Foo_3fooiiiiiE_L4
	b ._J3Foo_3fooiiiiiE_L5                 @ goto .L5;
._J3Foo_3fooiiiiiE_L5:
	ldr v1, =.string6                       @ _c51 = "sadge";
	mov a1, v1                              @ println(_c51);
	add a1, a1, #4
	bl puts(PLT)
	b ._J3Foo_3fooiiiiiE_L6                 @ goto .L6;
._J3Foo_3fooiiiiiE_L4:
	ldr v1, =.string7                       @ _c54 = "poggers";
	mov a1, v1                              @ println(_c54);
	add a1, a1, #4
	bl puts(PLT)
	b ._J3Foo_3fooiiiiiE_L6                 @ goto .L6;
._J3Foo_3fooiiiiiE_L6:
	ldr v1, [sp, #20]                       @ restore m;
	cmp v1, #50                             @ _t7 = m == 50;
	moveq v1, #1
	movne v1, #0
	cmp v1, #0                              @ if (_t7) goto .L7;
	bne ._J3Foo_3fooiiiiiE_L7
	b ._J3Foo_3fooiiiiiE_L8                 @ goto .L8;
._J3Foo_3fooiiiiiE_L8:
	ldr v1, =.string8                       @ _c62 = "riperino";
	mov a1, v1                              @ println(_c62);
	add a1, a1, #4
	bl puts(PLT)
	b ._J3Foo_3fooiiiiiE_L9                 @ goto .L9;
._J3Foo_3fooiiiiiE_L7:
	ldr v1, =.string9                       @ _c65 = "poggerino";
	mov a1, v1                              @ println(_c65);
	add a1, a1, #4
	bl puts(PLT)
	b ._J3Foo_3fooiiiiiE_L9                 @ goto .L9;
._J3Foo_3fooiiiiiE_L9:
	ldr v1, [v3, #0]                        @ _t8 = this.f1;
	ldr a1, =.string1_raw                   @ println(_t8);
	mov a2, v1
	bl printf(PLT)
	ldr v1, [v3, #4]                        @ _t9 = this.f2;
	ldr a1, =.string1_raw                   @ println(_t9);
	mov a2, v1
	bl printf(PLT)
	ldr v1, [v3, #8]                        @ _t10 = this.f3;
	ldr a1, =.string1_raw                   @ println(_t10);
	mov a2, v1
	bl printf(PLT)
	mov a1, v2                              @ return k;
	b ._J3Foo_3fooiiiiiE_exit
._J3Foo_3fooiiiiiE_exit:
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
    .word 8
.string4_raw:
    .asciz "omegalul"

.string5:
    .word 4
.string5_raw:
    .asciz "kekw"

.string6:
    .word 5
.string6_raw:
    .asciz "sadge"

.string7:
    .word 7
.string7_raw:
    .asciz "poggers"

.string8:
    .word 8
.string8_raw:
    .asciz "riperino"

.string9:
    .word 9
.string9_raw:
    .asciz "poggerino"

