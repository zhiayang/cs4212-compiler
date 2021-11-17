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
	mov v1, a1
	@ _c6 = 420;
	ldr v4, =#420
	@ _c8 = 69420;
	ldr v3, =#69420
	@ _c9 = 12345;
	ldr v2, =#12345
	@ _t1 = _J3Foo_3fooiiiiiE(_t0, 69, _c6, 77, _c8, _c9);
	str v2, [sp, #-4]!
	str v3, [sp, #-4]!
	mov a1, v1
	mov a2, #69
	mov a3, v4
	mov a4, #77
	bl _J3Foo_3fooiiiiiE
	add sp, sp, #8
	mov v1, a1
	@ z = _t1;
	mov v1, v1
	@ k = 69;
	mov v2, #69
	@ j = true;
	mov v3, #1
	@ _t2 = -k;
	rsb v2, v2, #0
	@ println(_t2);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ _c21 = 420;
	ldr v2, =#420
	@ println(_c21);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ _t3 = !j;
	rsb v2, v3, #1
	@ r = _t3;
	mov v2, v2
	@ println(false);
	mov a1, #0
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ _t4 = !r;
	rsb v2, v2, #1
	@ println(_t4);
	mov a1, v2
	cmp a1, #0
	ldreq a1, =.string2_raw
	ldrne a1, =.string3_raw
	bl puts(PLT)
	@ println(z);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	ldmfd sp!, {v1, v2, v3, v4}
	ldmfd sp!, {pc}
	

.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	@ spills:  'm', 'w'
	@ assigns: '_c17' = v1;  '_c20' = v1;  '_c22' = v1;  '_c31' = v1;  '_c33' = v1
	@          '_c41' = v1;  '_c52' = v1;  '_c55' = v1;  '_c61' = v1;  '_c64' = v1
	@          '_g27' = v1;  '_g38' = v1;  '_g42' = v1;   '_g9' = v1;   '_t1' = v1
	@          '_t10' = v1;   '_t2' = v1;   '_t3' = v1;   '_t4' = v1;   '_t5' = v1
	@           '_t6' = v1;   '_t7' = v1;   '_t8' = v1;   '_t9' = v1;     'm' = v1
	@             'w' = v1;     'y' = v1;   '_t0' = v2;     'k' = v2;     'x' = v2
	@          'this' = v3;   '_c1' = v4;  '_c49' = v4;  '_c58' = v4;  '_g26' = v4
	@          '_g37' = v4;  '_g41' = v4;   '_g8' = v4
	stmfd sp!, {lr}
	stmfd sp!, {v1, v2, v3, v4}
	@ prologue

	mov v3, a1
	mov v2, a2
	mov v1, a3
._J3Foo_3fooiiiiiE_entry:
	@ dummy;
	@ _c1 = 3;
	ldr v4, =#3
	@ _t0 = x * _c1;
	mul v2, v2, v4
	@ _t1 = _t0 + y;
	add v1, v2, v1
	@ k = _t1;
	mov v2, v1
	@ _g8 = getelementptr this, f3;
	add v4, v3, #8
	@ _g9 = 102;
	mov v1, #102
	@ storefield: Int, *_g8 = _g9;
	str v1, [v4]
	@ println(k);
	ldr a1, =.string1_raw
	mov a2, v2
	bl printf(PLT)
	@ m = 50;
	mov v1, #50
	@ spill m;
	str v1, [sp, #12]                      @ spill/wb m
	@ _c17 = 627;
	ldr v1, =#627
	@ _t2 = k == _c17;
	cmp v2, v1
	moveq v1, #1
	movne v1, #0
	@ if (_t2) goto .L1;
	cmp v1, #0
	bne ._J3Foo_3fooiiiiiE_L1
._J3Foo_3fooiiiiiE_L2:
	@ _c20 = "omegalul";
	ldr v1, =.string4
	@ println(_c20);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _c22 = 5;
	ldr v1, =#5
	@ _t4 = k * _c22;
	mul v1, v2, v1
	@ k = _t4;
	mov v2, v1
	@ _g26 = getelementptr this, f2;
	add v4, v3, #4
	@ _g27 = 19;
	mov v1, #19
	@ storefield: Int, *_g26 = _g27;
	str v1, [v4]
	@ goto .L3;
	b ._J3Foo_3fooiiiiiE_L3
._J3Foo_3fooiiiiiE_L1:
	@ _c31 = "kekw";
	ldr v1, =.string5
	@ println(_c31);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ _c33 = 2;
	ldr v1, =#2
	@ _t3 = k * _c33;
	mul v1, v2, v1
	@ k = _t3;
	mov v2, v1
	@ _g37 = getelementptr this, f2;
	add v4, v3, #4
	@ _g38 = 69;
	mov v1, #69
	@ storefield: Int, *_g37 = _g38;
	str v1, [v4]
._J3Foo_3fooiiiiiE_L3:
	@ _c41 = 420;
	ldr v1, =#420
	@ _g41 = getelementptr this, f1;
	add v4, v3, #0
	@ _g42 = _c41;
	mov v1, v1
	@ storefield: Int, *_g41 = _g42;
	str v1, [v4]
	@ restore w;
	ldr v1, [sp, #8]                       @ restore w
	@ _t5 = w + 1;
	add v1, v1, #1
	@ _c49 = 69420;
	ldr v4, =#69420
	@ _t6 = _t5 != _c49;
	cmp v1, v4
	movne v1, #1
	moveq v1, #0
	@ if (_t6) goto .L4;
	cmp v1, #0
	bne ._J3Foo_3fooiiiiiE_L4
._J3Foo_3fooiiiiiE_L5:
	@ _c52 = "sadge";
	ldr v1, =.string6
	@ println(_c52);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L6;
	b ._J3Foo_3fooiiiiiE_L6
._J3Foo_3fooiiiiiE_L4:
	@ _c55 = "poggers";
	ldr v1, =.string7
	@ println(_c55);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_3fooiiiiiE_L6:
	@ _c58 = 12345;
	ldr v4, =#12345
	@ restore m;
	ldr v1, [sp, #12]                      @ restore m
	@ _t7 = m == _c58;
	cmp v1, v4
	moveq v1, #1
	movne v1, #0
	@ if (_t7) goto .L7;
	cmp v1, #0
	bne ._J3Foo_3fooiiiiiE_L7
._J3Foo_3fooiiiiiE_L8:
	@ _c61 = "riperino";
	ldr v1, =.string8
	@ println(_c61);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	@ goto .L9;
	b ._J3Foo_3fooiiiiiE_L9
._J3Foo_3fooiiiiiE_L7:
	@ _c64 = "poggerino";
	ldr v1, =.string9
	@ println(_c64);
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_3fooiiiiiE_L9:
	@ _t8 = this.f1;
	ldr v1, [v3, #0]
	@ println(_t8);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _t9 = this.f2;
	ldr v1, [v3, #4]
	@ println(_t9);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ _t10 = this.f3;
	ldr v1, [v3, #8]
	@ println(_t10);
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	@ return k;
	mov a1, v2
	b ._J3Foo_3fooiiiiiE_epilogue

	@ epilogue
._J3Foo_3fooiiiiiE_epilogue:
	ldmfd sp!, {v1, v2, v3, v4}
	ldmfd sp!, {pc}
	

	
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

