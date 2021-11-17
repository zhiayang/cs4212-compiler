.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns:  '_t4' = v1;     'r' = v1;   '_t3' = v1;  '_c21' = v1;   '_t2' = v1
	@             'k' = v1;   '_t1' = v1;   '_c9' = v1;   '_c1' = v1;     'z' = v2
	@           '_c8' = v2;     'j' = v3;   '_c6' = v3;   '_t0' = v4
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

.main_dummy_entry:
	@ dummy;
	@ _c1 = "asdf";
	ldr v1, =.string0
	@ println(_c1);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _t0 = new Foo();
	mov a1, #1
	ldr a2, =#12
	bl calloc(PLT)
	mov v4, a1
	@ _c6 = 420;
	ldr v3, =#420
	@ _c8 = 69420;
	ldr v2, =#69420
	@ _c9 = 12345;
	ldr v1, =#12345
	@ _t1 = _J3Foo_3fooiiiiiE(_t0, 69, _c6, 77, _c8, _c9);
	str v1, [sp, #-4]!
	str v2, [sp, #-4]!
	mov a1, v4
	mov a2, #69
	mov a3, v3
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	mov v1, a1
	@ z = _t1;
	mov v2, v1
	@ k = 69;
	mov v1, #69
	@ j = true;
	mov v3, #1
	@ _t2 = -k;
	rsb v1, v1, #0
	@ println(_t2);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _c21 = 420;
	ldr v1, =#420
	@ println(_c21);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _t3 = !j;
	rsb v1, v3, #1
	@ r = _t3;
	mov v1, v1
	@ println(false);
	mov a1, #0
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ _t4 = !r;
	rsb v1, v1, #1
	@ println(_t4);
	mov a1, v1
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ println(z);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #0
	ldmfd sp!, {fp, pc}
	

.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	@ spills:  'm', 'w'
	@ assigns: 'this' = v1;  '_t10' = v1;     'y' = v2;   '_t9' = v2;   '_t8' = v2
	@          '_c62' = v2;  '_c59' = v2;   '_t7' = v2;     'm' = v2;  '_c53' = v2
	@          '_c50' = v2;   '_t6' = v2;  '_c47' = v2;     'w' = v2;  '_g40' = v2
	@          '_c39' = v2;  '_g36' = v2;   '_t3' = v2;  '_c31' = v2;  '_c29' = v2
	@          '_g25' = v2;   '_t4' = v2;  '_c20' = v2;  '_c18' = v2;   '_t2' = v2
	@          '_c15' = v2;   '_g9' = v2;   '_t1' = v2;     'x' = v3;     'k' = v3
	@           '_t0' = v3;  '_c56' = v4;   '_t5' = v4;  '_g39' = v4;  '_g35' = v4
	@          '_g24' = v4;   '_g8' = v4;   '_c1' = v4
	stmfd sp!, {fp, lr}
	mov fp, sp
	sub sp, sp, #0
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

	mov v1, a1
	mov v3, a2
	mov v2, a3
._J3Foo_3fooiiiiiE_entry:
	@ dummy;
	@ _c1 = 3;
	ldr v4, =#3
	@ _t0 = x * _c1;
	mul v3, v3, v4
	@ _t1 = _t0 + y;
	add v2, v3, v2
	@ k = _t1;
	mov v3, v2
	@ _g8 = getelementptr this, f3;
	add v4, v1, #8
	@ _g9 = 102;
	mov v2, #102
	@ storefield: Int, *_g8 = _g9;
	str v2, [v4]
	@ println(k);
	ldr a1, =.string1_raw
	mov a2, v3
	bl printf(PLT)
	@ _c15 = 627;
	ldr v2, =#627
	@ _t2 = k == _c15;
	cmp v3, v2
	moveq v2, #1
	movne v2, #0
	@ if (_t2) goto .L1;
	cmp v2, #0
	bne ._J3Foo_3fooiiiiiE_L1
._J3Foo_3fooiiiiiE_L2:
	@ _c18 = "omegalul";
	ldr v2, =.string4
	@ println(_c18);
	mov a1, v2
	add a1, a1, #4
	bl puts(PLT)
	@ _c20 = 5;
	ldr v2, =#5
	@ _t4 = k * _c20;
	mul v2, v3, v2
	@ k = _t4;
	mov v3, v2
	@ _g24 = getelementptr this, f2;
	add v4, v1, #4
	@ _g25 = 19;
	mov v2, #19
	@ storefield: Int, *_g24 = _g25;
	str v2, [v4]
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L1:
	@ _c29 = "kekw";
	ldr v2, =.string5
	@ println(_c29);
	mov a1, v2
	add a1, a1, #4
	bl puts(PLT)
	@ _c31 = 2;
	ldr v2, =#2
	@ _t3 = k * _c31;
	mul v2, v3, v2
	@ k = _t3;
	mov v3, v2
	@ _g35 = getelementptr this, f2;
	add v4, v1, #4
	@ _g36 = 69;
	mov v2, #69
	@ storefield: Int, *_g35 = _g36;
	str v2, [v4]
._J3Foo_3fooiiiiiE_L3:
	@ _c39 = 420;
	ldr v2, =#420
	@ _g39 = getelementptr this, f1;
	add v4, v1, #0
	@ _g40 = _c39;
	mov v2, v2
	@ storefield: Int, *_g39 = _g40;
	str v2, [v4]
	@ restore w;
	ldr v2, [fp, #8]                       @ restore w
	@ _t5 = w + 1;
	ldr v2, [fp, #8]                       @ restore w
	add v4, v2, #1
	@ _c47 = 69420;
	ldr v2, =#69420
	@ _t6 = _t5 != _c47;
	cmp v4, v2
	movne v2, #1
	moveq v2, #0
	@ if (_t6) goto .L4;
	cmp v2, #0
	bne ._J3Foo_3fooiiiiiE_L4
._J3Foo_3fooiiiiiE_L5:
	@ _c50 = "sadge";
	ldr v2, =.string6
	@ println(_c50);
	mov a1, v2
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L4:
	@ _c53 = "poggers";
	ldr v2, =.string7
	@ println(_c53);
	mov a1, v2
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_3fooiiiiiE_L6:
	@ _c56 = 12345;
	ldr v4, =#12345
	@ restore m;
	ldr v2, [fp, #12]                      @ restore m
	@ _t7 = m == _c56;
	ldr v2, [fp, #12]                      @ restore m
	cmp v2, v4
	moveq v2, #1
	movne v2, #0
	@ if (_t7) goto .L7;
	cmp v2, #0
	bne ._J3Foo_3fooiiiiiE_L7
._J3Foo_3fooiiiiiE_L8:
	@ _c59 = "riperino";
	ldr v2, =.string8
	@ println(_c59);
	mov a1, v2
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L9;
	b ._J3Foo_3fooiiiiiE_L9
._J3Foo_3fooiiiiiE_L7:
	@ _c62 = "poggerino";
	ldr v2, =.string9
	@ println(_c62);
	mov a1, v2
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_3fooiiiiiE_L9:
	@ _t8 = this.f1;
	ldr v2, [v1, #0]
	@ println(_t8);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ _t9 = this.f2;
	ldr v2, [v1, #4]
	@ println(_t9);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ _t10 = this.f3;
	ldr v1, [v1, #8]
	@ println(_t10);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ return k;
	mov a1, v3
	b ._J3Foo_3fooiiiiiE_epilogue

	@ epilogue
._J3Foo_3fooiiiiiE_epilogue:
	ldmfd sp!, {v1, v2, v3, v4}
	add sp, sp, #0
	ldmfd sp!, {fp, pc}
	

	
.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	@ we need a 'this' argument for this guy, so just allocate
	@ nothing.
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

