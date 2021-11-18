@ jlite compiler: compile.py -v -O test/02_cse.j
.text
	@ constant branch eliminated; fallthrough
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  'foooo', 'x'
	@ assigns:  '_c13' = v1;   '_c16' = v1;   '_c21' = v1;   '_c24' = v1;   '_c26' = v1
	@            '_c3' = v1;   '_c30' = v1;   '_c34' = v1;   '_c37' = v1;   '_c43' = v1
	@            '_c6' = v1;   '_c71' = v1;   '_c86' = v1;    '_c9' = v1;   '_c91' = v1
	@           '_t11' = v1;   '_t12' = v1;   '_t13' = v1;   '_t14' = v1;   '_t23' = v1
	@           '_t24' = v1;   '_t25' = v1;   '_t26' = v1;   '_t27' = v1;    '_t6' = v1
	@            '_t9' = v1;      'c' = v1;    'ccc' = v1;      'e' = v1;      'f' = v1
	@          'foooo' = v1;      'g' = v1;      'h' = v1;      'x' = v1;  '_c101' = v2
	@          '_c104' = v2;  '_c107' = v2;  '_c110' = v2;  '_c113' = v2;   '_c70' = v2
	@           '_c74' = v2;   '_c77' = v2;   '_c80' = v2;   '_c83' = v2;   '_c98' = v2
	@           '_t15' = v2;      'd' = v2;    'foo' = v2;    '_t0' = v3;    '_t5' = v3
	@              'b' = v4
	stmfd sp!, {lr}
	sub sp, sp, #8
	stmfd sp!, {v1, v2, v3, v4}
.main_dummy_entry:
	mov v2, #69                             @ foo = 69;
	ldr v1, =#300                           @ _c3 = 300;
	mov v1, v1                              @ ccc = _c3;
	ldr v1, =#420                           @ _c6 = 420;
	add v3, v1, #69                         @ _t0 = 69 + _c6;
	ldr v1, =#1234                          @ _c9 = 1234;
	add v1, v3, v1                          @ x = _t0 + _c9;
	str v1, [sp, #4]                        @ spill x;
	b .main_dummy_L1                        @ if (true) goto .L1;
	b .main_dummy_L2                        @ goto .L2;
.main_dummy_L2:
	ldr v1, =.string0                       @ _c13 = "sadge";
	mov a1, v1                              @ println(_c13);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L1:
	ldr v1, =.string1                       @ _c16 = "kekw";
	mov a1, v1                              @ println(_c16);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L3:
	b .main_dummy_L5                        @ goto .L5;
.main_dummy_L5:
	ldr v1, =.string2                       @ _c21 = "phew";
	mov a1, v1                              @ println(_c21);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L6                        @ goto .L6;
.main_dummy_L4:
	ldr v1, =.string3                       @ _c24 = "what";
	mov a1, v1                              @ println(_c24);
	add a1, a1, #4
	bl puts(PLT)
	ldr v1, =#420                           @ _c26 = 420;
	mov v2, v1                              @ foo = _c26;
	b .main_dummy_L6                        @ goto .L6;
.main_dummy_L6:
	ldr v1, =#420                           @ _c30 = 420;
	add v4, v2, v1                          @ b = foo + _c30;
	b .main_dummy_L7                        @ if (true) goto .L7;
	b .main_dummy_L8                        @ goto .L8;
.main_dummy_L8:
	ldr v1, =.string4                       @ _c34 = "asdf";
	mov a1, v1                              @ println(_c34);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L9                        @ goto .L9;
.main_dummy_L7:
	ldr v1, =.string5                       @ _c37 = "cool";
	mov a1, v1                              @ println(_c37);
	add a1, a1, #4
	bl puts(PLT)
	mov v2, #100                            @ foo = 100;
	b .main_dummy_L9                        @ goto .L9;
.main_dummy_L9:
	ldr v1, =#420                           @ _c43 = 420;
	add v1, v2, v1                          @ c = foo + _c43;
	ldr a1, =.string6_raw                   @ println(_t0);
	mov a2, v3
	bl printf(PLT)
	ldr a1, =.string6_raw                   @ println(b);
	mov a2, v4
	bl printf(PLT)
	ldr a1, =.string6_raw                   @ println(c);
	mov a2, v1
	bl printf(PLT)
	ldr v1, [sp, #4]                        @ restore x;
	ldr a1, =.string6_raw                   @ println(x);
	mov a2, v1
	bl printf(PLT)
	ldr v3, =#300                           @ _t5 = 100 + 200;
	ldr v1, [sp, #0]                        @ restore foooo;
	mov a1, v1                              @ _t6 = _J3Foo_11side_effectE(foooo);
	bl _J3Foo_11side_effectE
	mov v1, a1
	add v2, v3, v1                          @ d = _t5 + _t6;
	ldr v1, [sp, #0]                        @ restore foooo;
	mov a1, v1                              @ _t9 = _J3Foo_11side_effectE(foooo);
	bl _J3Foo_11side_effectE
	mov v1, a1
	add v1, v3, v1                          @ e = _t5 + _t9;
	ldr a1, =.string6_raw                   @ println(d);
	mov a2, v2
	bl printf(PLT)
	ldr a1, =.string6_raw                   @ println(e);
	mov a2, v1
	bl printf(PLT)
	ldr v2, =#300                           @ _c70 = 300;
	ldr v1, =#400                           @ _c71 = 400;
	add v1, v2, v1                          @ _t11 = _c70 + _c71;
	ldr v2, =#500                           @ _c74 = 500;
	add v1, v1, v2                          @ _t12 = _t11 + _c74;
	ldr v2, =#600                           @ _c77 = 600;
	add v1, v1, v2                          @ _t13 = _t12 + _c77;
	ldr v2, =#700                           @ _c80 = 700;
	add v1, v1, v2                          @ _t14 = _t13 + _c80;
	ldr v2, =#800                           @ _c83 = 800;
	add v2, v1, v2                          @ _t15 = _t14 + _c83;
	ldr v1, =#900                           @ _c86 = 900;
	add v1, v2, v1                          @ f = _t15 + _c86;
	ldr a1, =.string6_raw                   @ println(f);
	mov a2, v1
	bl printf(PLT)
	ldr v1, =#900                           @ _c91 = 900;
	add v1, v2, v1                          @ g = _t15 + _c91;
	ldr a1, =.string6_raw                   @ println(g);
	mov a2, v1
	bl printf(PLT)
	mov v1, #1                              @ ccc = 1;
	ldr v2, =#400                           @ _c98 = 400;
	add v1, v1, v2                          @ _t23 = ccc + _c98;
	ldr v2, =#500                           @ _c101 = 500;
	add v1, v1, v2                          @ _t24 = _t23 + _c101;
	ldr v2, =#600                           @ _c104 = 600;
	add v1, v1, v2                          @ _t25 = _t24 + _c104;
	ldr v2, =#700                           @ _c107 = 700;
	add v1, v1, v2                          @ _t26 = _t25 + _c107;
	ldr v2, =#800                           @ _c110 = 800;
	add v1, v1, v2                          @ _t27 = _t26 + _c110;
	ldr v2, =#900                           @ _c113 = 900;
	add v1, v1, v2                          @ h = _t27 + _c113;
	ldr a1, =.string6_raw                   @ println(h);
	mov a2, v1
	bl printf(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #8
	ldmfd sp!, {pc}


.global _J3Foo_11side_effectE
.type _J3Foo_11side_effectE, %function
_J3Foo_11side_effectE:
	@ spills:  <none>
	@ assigns: '_c1' = v1
	stmfd sp!, {lr}
	stmfd sp!, {v1}
._J3Foo_11side_effectE_entry:
	ldr v1, =.string7                       @ _c1 = "you should see this twice";
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
    .word 5
.string0_raw:
    .asciz "sadge"

.string1:
    .word 4
.string1_raw:
    .asciz "kekw"

.string2:
    .word 4
.string2_raw:
    .asciz "phew"

.string3:
    .word 4
.string3_raw:
    .asciz "what"

.string4:
    .word 4
.string4_raw:
    .asciz "asdf"

.string5:
    .word 4
.string5_raw:
    .asciz "cool"

.string6:
    .word 3
.string6_raw:
    .asciz "%d\n"

.string7:
    .word 25
.string7_raw:
    .asciz "you should see this twice"

