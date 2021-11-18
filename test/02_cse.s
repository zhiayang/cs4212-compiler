@ jlite compiler: ./compile.py --dump-ir3 -O -v test/02_cse.j
.text
	@ constant branch eliminated; fallthrough
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  'a', 'aaa', 'baz', 'bbb', 'ccc', 'ddd', 'eee', 'fff', 'foooo'
	@          'ggg', 'hhh', 'iii', 'x'
	@ assigns:  '_c11' = v1;   '_c13' = v1;   '_c15' = v1;   '_c17' = v1;   '_c19' = v1
	@           '_c21' = v1;   '_c23' = v1;    '_c3' = v1;   '_c33' = v1;   '_c36' = v1
	@           '_c43' = v1;   '_c46' = v1;   '_c48' = v1;    '_c5' = v1;    'aaa' = v1
	@              'b' = v1;    'baz' = v1;    'bbb' = v1;    'ddd' = v1;      'e' = v1
	@            'eee' = v1;      'f' = v1;    'fff' = v1;  'foooo' = v1;      'g' = v1
	@            'ggg' = v1;      'h' = v1;    'hhh' = v1;    'iii' = v1;      'x' = v1
	@           '_c59' = v2;   '_t11' = v2;   '_t12' = v2;   '_t13' = v2;   '_t14' = v2
	@           '_t15' = v2;   '_t23' = v2;   '_t24' = v2;   '_t25' = v2;   '_t26' = v2
	@           '_t27' = v2;    '_t5' = v2;    '_t6' = v2;      'c' = v2;      'd' = v2
	@            'foo' = v2;    '_t8' = v3;    '_t9' = v3;    'bar' = v3;   '_c56' = v4
	@            '_t0' = v4;      'a' = v4;    'ccc' = v4
	stmfd sp!, {lr}
	sub sp, sp, #56
	stmfd sp!, {v1, v2, v3, v4}
.main_dummy_entry:
	mov v2, #69                             @ foo = 69;
	ldr v1, =#420                           @ _c3 = 420;
	mov v3, v1                              @ bar = _c3;
	ldr v1, =#1234                          @ _c5 = 1234;
	mov v1, v1                              @ baz = _c5;
	str v1, [sp, #52]                       @ spill baz;
	mov v1, #100                            @ aaa = 100;
	str v1, [sp, #48]                       @ spill aaa;
	mov v1, #200                            @ bbb = 200;
	str v1, [sp, #44]                       @ spill bbb;
	ldr v1, =#300                           @ _c11 = 300;
	mov v4, v1                              @ ccc = _c11;
	str v4, [sp, #40]                       @ spill ccc;
	ldr v1, =#400                           @ _c13 = 400;
	mov v1, v1                              @ ddd = _c13;
	str v1, [sp, #36]                       @ spill ddd;
	ldr v1, =#500                           @ _c15 = 500;
	mov v1, v1                              @ eee = _c15;
	str v1, [sp, #32]                       @ spill eee;
	ldr v1, =#600                           @ _c17 = 600;
	mov v1, v1                              @ fff = _c17;
	str v1, [sp, #28]                       @ spill fff;
	ldr v1, =#700                           @ _c19 = 700;
	mov v1, v1                              @ ggg = _c19;
	str v1, [sp, #24]                       @ spill ggg;
	ldr v1, =#800                           @ _c21 = 800;
	mov v1, v1                              @ hhh = _c21;
	str v1, [sp, #20]                       @ spill hhh;
	ldr v1, =#900                           @ _c23 = 900;
	mov v1, v1                              @ iii = _c23;
	str v1, [sp, #16]                       @ spill iii;
	add v4, v2, v3                          @ _t0 = foo + bar;
	ldr v1, [sp, #52]                       @ restore baz;
	add v1, v4, v1                          @ x = _t0 + baz;
	str v1, [sp, #8]                        @ spill x;
	b .main_dummy_L1                        @ if (true) goto .L1;
	b .main_dummy_L2                        @ goto .L2;
.main_dummy_L2:
	ldr v1, =.string0                       @ _c33 = "sadge";
	mov a1, v1                              @ println(_c33);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L1:
	ldr v1, =.string1                       @ _c36 = "kekw";
	mov a1, v1                              @ println(_c36);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L3                        @ goto .L3;
.main_dummy_L3:
	mov v4, v4                              @ a = _t0;
	str v4, [sp, #12]                       @ spill a;
	b .main_dummy_L5                        @ goto .L5;
.main_dummy_L5:
	ldr v1, =.string2                       @ _c43 = "phew";
	mov a1, v1                              @ println(_c43);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L6                        @ goto .L6;
.main_dummy_L4:
	ldr v1, =.string3                       @ _c46 = "what";
	mov a1, v1                              @ println(_c46);
	add a1, a1, #4
	bl puts(PLT)
	ldr v1, =#420                           @ _c48 = 420;
	mov v2, v1                              @ foo = _c48;
	b .main_dummy_L6                        @ goto .L6;
.main_dummy_L6:
	add v1, v2, v3                          @ b = foo + bar;
	b .main_dummy_L7                        @ if (true) goto .L7;
	b .main_dummy_L8                        @ goto .L8;
.main_dummy_L8:
	ldr v4, =.string4                       @ _c56 = "asdf";
	mov a1, v4                              @ println(_c56);
	add a1, a1, #4
	bl puts(PLT)
	b .main_dummy_L9                        @ goto .L9;
.main_dummy_L7:
	ldr v2, =.string5                       @ _c59 = "cool";
	mov a1, v2                              @ println(_c59);
	add a1, a1, #4
	bl puts(PLT)
	mov v2, #100                            @ foo = 100;
	b .main_dummy_L9                        @ goto .L9;
.main_dummy_L9:
	add v2, v2, v3                          @ c = foo + bar;
	ldr v4, [sp, #12]                       @ restore a;
	ldr a1, =.string6_raw                   @ println(a);
	mov a2, v4
	bl printf(PLT)
	ldr a1, =.string6_raw                   @ println(b);
	mov a2, v1
	bl printf(PLT)
	ldr a1, =.string6_raw                   @ println(c);
	mov a2, v2
	bl printf(PLT)
	ldr v1, [sp, #8]                        @ restore x;
	ldr a1, =.string6_raw                   @ println(x);
	mov a2, v1
	bl printf(PLT)
	ldr v1, [sp, #4]                        @ restore foooo;
	mov a1, v1                              @ _t5 = _J3Foo_11side_effectE(foooo);
	bl _J3Foo_11side_effectE
	mov v2, a1
	ldr v1, [sp, #48]                       @ restore aaa;
	add v2, v1, v2                          @ _t6 = aaa + _t5;
	ldr v1, [sp, #44]                       @ restore bbb;
	add v2, v2, v1                          @ d = _t6 + bbb;
	ldr v1, [sp, #4]                        @ restore foooo;
	mov a1, v1                              @ _t8 = _J3Foo_11side_effectE(foooo);
	bl _J3Foo_11side_effectE
	mov v3, a1
	ldr v1, [sp, #48]                       @ restore aaa;
	add v3, v1, v3                          @ _t9 = aaa + _t8;
	ldr v1, [sp, #44]                       @ restore bbb;
	add v1, v3, v1                          @ e = _t9 + bbb;
	ldr a1, =.string6_raw                   @ println(d);
	mov a2, v2
	bl printf(PLT)
	ldr a1, =.string6_raw                   @ println(e);
	mov a2, v1
	bl printf(PLT)
	ldr v4, [sp, #40]                       @ restore ccc;
	ldr v1, [sp, #36]                       @ restore ddd;
	add v2, v4, v1                          @ _t11 = ccc + ddd;
	ldr v1, [sp, #32]                       @ restore eee;
	add v2, v2, v1                          @ _t12 = _t11 + eee;
	ldr v1, [sp, #28]                       @ restore fff;
	add v2, v2, v1                          @ _t13 = _t12 + fff;
	ldr v1, [sp, #24]                       @ restore ggg;
	add v2, v2, v1                          @ _t14 = _t13 + ggg;
	ldr v1, [sp, #20]                       @ restore hhh;
	add v2, v2, v1                          @ _t15 = _t14 + hhh;
	ldr v1, [sp, #16]                       @ restore iii;
	add v1, v2, v1                          @ f = _t15 + iii;
	ldr a1, =.string6_raw                   @ println(f);
	mov a2, v1
	bl printf(PLT)
	ldr v1, [sp, #16]                       @ restore iii;
	add v1, v2, v1                          @ g = _t15 + iii;
	ldr a1, =.string6_raw                   @ println(g);
	mov a2, v1
	bl printf(PLT)
	mov v4, #1                              @ ccc = 1;
	str v4, [sp, #40]                       @ spill ccc;
	ldr v4, [sp, #40]                       @ restore ccc;
	ldr v1, [sp, #36]                       @ restore ddd;
	add v2, v4, v1                          @ _t23 = ccc + ddd;
	ldr v1, [sp, #32]                       @ restore eee;
	add v2, v2, v1                          @ _t24 = _t23 + eee;
	ldr v1, [sp, #28]                       @ restore fff;
	add v2, v2, v1                          @ _t25 = _t24 + fff;
	ldr v1, [sp, #24]                       @ restore ggg;
	add v2, v2, v1                          @ _t26 = _t25 + ggg;
	ldr v1, [sp, #20]                       @ restore hhh;
	add v2, v2, v1                          @ _t27 = _t26 + hhh;
	ldr v1, [sp, #16]                       @ restore iii;
	add v1, v2, v1                          @ h = _t27 + iii;
	ldr a1, =.string6_raw                   @ println(h);
	mov a2, v1
	bl printf(PLT)
	b .main_dummy_exit                      @ return;
.main_dummy_exit:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #56
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

