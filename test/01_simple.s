@ jlite compiler: compile.py -O test/01_simple.j
.text
.global main_dummy
.type main_dummy, %function
main_dummy:
	@ spills:  <none>
	@ assigns:   'rb' = v1;    'ri' = v1;    'rs' = v1;  '_c12' = v2;   '_c2' = v2
	@           '_c7' = v2
	stmfd sp!, {v1, v2, lr}
.main_dummy_entry:
	bl __readln_int                         @ readln(ri);
	mov v1, a1
	ldr v2, =.string0                       @ _c2 = "read integer:";
	mov a1, v2                              @ println(_c2);
	add a1, a1, #4
	bl puts(PLT)
	ldr a1, =.string1_raw                   @ println(ri);
	mov a2, v1
	bl printf(PLT)
	bl __readln_string                      @ readln(rs);
	mov v1, a1
	ldr v2, =.string2                       @ _c7 = "read string:";
	mov a1, v2                              @ println(_c7);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, v1                              @ println(rs);
	add a1, a1, #4
	bl puts(PLT)
	bl __readln_bool                        @ readln(rb);
	mov v1, a1
	ldr v2, =.string3                       @ _c12 = "read boolean:";
	mov a1, v2                              @ println(_c12);
	add a1, a1, #4
	bl puts(PLT)
	movs a1, v1                             @ println(rb);
	ldreq a1, =.string4_raw
	ldrne a1, =.string5_raw
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
	@ assigns:    'm' = a2;   '_c1' = v1;   '_c3' = v1;  '_c48' = v1;   '_c5' = v1
	@           '_t7' = v1;   'str' = v1;     'k' = v2;  '_c44' = v3;     'c' = v3
	@          '_c18' = v4;  '_c21' = v4;  '_c30' = v4;   '_t1' = v4;   '_t2' = v4
	@           '_t5' = v4;   '_t6' = v4
	stmfd sp!, {v1, v2, v3, v4, lr}
._J3Foo_4bsdfiE_entry:
	mov v1, #2                              @ _c1 = 2;
	mul v2, a2, v1                          @ k = m * _c1;
	ldr v1, =#500                           @ _c3 = 500;
	mov v3, v1                              @ c = _c3;
	ldr v1, =.string6                       @ _c5 = "should have 14 chars: '";
._J3Foo_4bsdfiE_L1:
	cmp v2, #0                              @ _t1 = k > 0;
	bgt ._J3Foo_4bsdfiE_L8
	b ._J3Foo_4bsdfiE_L9                    @ goto .L9;
._J3Foo_4bsdfiE_L8:
	cmp v2, #8                              @ _t2 = k < 8;
	blt ._J3Foo_4bsdfiE_L2
._J3Foo_4bsdfiE_L3:
	ldr v4, =.string7                       @ _c18 = "you should also see this 7 times";
	mov a1, v4                              @ println(_c18);
	add a1, a1, #4
	bl puts(PLT)
	b ._J3Foo_4bsdfiE_L4                    @ goto .L4;
._J3Foo_4bsdfiE_L2:
	ldr v4, =.string8                       @ _c21 = "you should see this 7 times";
	mov a1, v4                              @ println(_c21);
	add a1, a1, #4
	bl puts(PLT)
._J3Foo_4bsdfiE_L4:
	ldr a1, =.string1_raw                   @ println(k);
	mov a2, v2
	bl printf(PLT)
	sub v2, v2, #1                          @ k = k - 1;
	ldr v4, =.string9                       @ _c30 = "x";
	mov a1, v1                              @ str = str s+ _c30;
	mov a2, v4
	bl __string_concat
	mov v1, a1
	cmp v2, #0                              @ _t5 = k == 0;
	beq ._J3Foo_4bsdfiE_L5
	b ._J3Foo_4bsdfiE_L1                    @ goto .L1;
._J3Foo_4bsdfiE_L5:
	add v4, v3, #69                         @ _t6 = c + 69;
	ldr a1, =.string1_raw                   @ println(_t6);
	mov a2, v4
	bl printf(PLT)
	b ._J3Foo_4bsdfiE_L1                    @ goto .L1;
._J3Foo_4bsdfiE_L9:
	ldr v3, =.string10                      @ _c44 = "'";
	mov a1, v1                              @ _t7 = str s+ _c44;
	mov a2, v3
	bl __string_concat
	mov v1, a1
	mov a1, v1                              @ println(_t7);
	add a1, a1, #4
	bl puts(PLT)
	ldr v1, =.string11                      @ _c48 = "                      -123456789abcde-";
	mov a1, v1                              @ println(_c48);
	add a1, a1, #4
	bl puts(PLT)
	mov a1, v2                              @ return k;
	b ._J3Foo_4bsdfiE_exit
._J3Foo_4bsdfiE_exit:
	ldmfd sp!, {v1, v2, v3, v4, pc}


.global _J3Foo_3fooiiiiiE
.type _J3Foo_3fooiiiiiE, %function
_J3Foo_3fooiiiiiE:
	@ spills:  <none>
	@ assigns:  'this' = a1;   '_c73' = a2;   '_c81' = a2;   '_c89' = a2;   '_c97' = a2
	@              'x' = a2;  '_c104' = a3;  '_c112' = a3;      'y' = a3;  '_c108' = v1
	@          '_c116' = v1;  '_c118' = v1;  '_c126' = v1;   '_c45' = v1;   '_c48' = v1
	@           '_c51' = v1;   '_c70' = v1;   '_c78' = v1;   '_c86' = v1;   '_c94' = v1
	@           '_t10' = v1;   '_t11' = v1;   '_t12' = v1;   '_t14' = v1;   '_t16' = v1
	@           '_t17' = v1;   '_t18' = v1;   '_t19' = v1;   '_t20' = v1;   '_t21' = v1
	@           '_t22' = v1;   '_t23' = v1;    '_t6' = v1;    '_t7' = v1;    '_t9' = v1
	@              'w' = v1;    '_c1' = v2;    '_t0' = v2;      'k' = v2;   '_c14' = v3
	@           '_c18' = v3;   '_c20' = v3;   '_c26' = v3;   '_c28' = v3;   '_c34' = v3
	@           '_c41' = v3;   '_g23' = v3;   '_g31' = v3;   '_g35' = v3;    '_g7' = v3
	@            '_t3' = v3
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
	ldr v3, =.string12                      @ _c18 = "omegalul";
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
	ldr v3, =.string13                      @ _c26 = "kekw";
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
	ldr v1, =.string14                      @ _c45 = "sadge";
	sub sp, sp, #4                          @ println(_c45);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	b ._J3Foo_3fooiiiiiE_L16                @ goto .L16;
._J3Foo_3fooiiiiiE_L13:
	ldr v1, =.string15                      @ _c48 = "poggers";
	sub sp, sp, #4                          @ println(_c48);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
._J3Foo_3fooiiiiiE_L16:
	ldr v1, =.string16                      @ _c51 = "poggerino";
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
	sub sp, sp, #4                          @ println(_t11);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	sub sp, sp, #4                          @ _t12 = new Foo();; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, #1
	mov a2, #12
	bl calloc(PLT)
	mov v1, a1
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	mov a1, v1                              @ _J3Foo_4asdfE(_t12);
	bl _J3Foo_4asdfE
	sub sp, sp, #4                          @ _t14 = new Foo();; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, #1
	mov a2, #12
	bl calloc(PLT)
	mov v1, a1
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	mov a1, v1                              @ _J3Foo_4bsdfiE(_t14, 7);
	mov a2, #7
	bl _J3Foo_4bsdfiE
	ldr v1, =.string17                      @ _c70 = "420 / 69 is:";
	sub sp, sp, #4                          @ println(_c70);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a2, =#420                           @ _c73 = 420;
	stmfd sp!, {a1, a2}                     @ _t16 = _J3Foo_9do_divideiiE(this, _c73, 69);; caller-save
	mov a3, #69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1, a2}                     @ caller-restore
	sub sp, sp, #4                          @ println(_t16);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string18                      @ _c78 = "69 / 420 is:";
	sub sp, sp, #4                          @ println(_c78);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a2, =#-420                          @ _c81 = -420;
	stmfd sp!, {a1, a2}                     @ _t17 = _J3Foo_9do_divideiiE(this, _c81, 69);; caller-save
	mov a3, #69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1, a2}                     @ caller-restore
	sub sp, sp, #4                          @ println(_t17);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string19                      @ _c86 = "420 / -69 is:";
	sub sp, sp, #4                          @ println(_c86);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a2, =#420                           @ _c89 = 420;
	stmfd sp!, {a1, a2}                     @ _t18 = _J3Foo_9do_divideiiE(this, _c89, -69);; caller-save
	mov a3, #-69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1, a2}                     @ caller-restore
	sub sp, sp, #4                          @ println(_t18);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string20                      @ _c94 = "-420 / -69 is:";
	sub sp, sp, #4                          @ println(_c94);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a2, =#-420                          @ _c97 = -420;
	stmfd sp!, {a1, a2}                     @ _t19 = _J3Foo_9do_divideiiE(this, _c97, -69);; caller-save
	mov a3, #-69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1, a2}                     @ caller-restore
	sub sp, sp, #4                          @ println(_t19);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a3, =#420                           @ _c104 = 420;
	stmfd sp!, {a1, a3}                     @ _t20 = _J3Foo_9do_divideiiE(this, 69, _c104);; caller-save
	mov a2, #69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1, a3}                     @ caller-restore
	sub sp, sp, #4                          @ println(_t20);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string21                      @ _c108 = "-69 / 420 is:";
	sub sp, sp, #4                          @ println(_c108);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a3, =#420                           @ _c112 = 420;
	stmfd sp!, {a1, a3}                     @ _t21 = _J3Foo_9do_divideiiE(this, -69, _c112);; caller-save
	mov a2, #-69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1, a3}                     @ caller-restore
	sub sp, sp, #4                          @ println(_t21);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string22                      @ _c116 = "-420 / 69 is:";
	sub sp, sp, #4                          @ println(_c116);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string23                      @ _c118 = "0 / 69 is:";
	sub sp, sp, #4                          @ println(_c118);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	sub sp, sp, #4                          @ _t22 = _J3Foo_9do_divideiiE(this, 0, 69);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a2, #0
	mov a3, #69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	sub sp, sp, #4                          @ println(_t22);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	ldr a1, =.string1_raw
	mov a2, v1
	bl printf(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr v1, =.string24                      @ _c126 = "69 / -69 is:";
	sub sp, sp, #4                          @ println(_c126);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a1, v1
	add a1, a1, #4
	bl puts(PLT)
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	sub sp, sp, #4                          @ _t23 = _J3Foo_9do_divideiiE(this, 69, -69);; align adjustment
	stmfd sp!, {a1}                         @ caller-save
	mov a2, #69
	mov a3, #-69
	bl _J3Foo_9do_divideiiE
	mov v1, a1
	ldmfd sp!, {a1}                         @ caller-restore
	add sp, sp, #4                          @ align adjustment
	ldr a1, =.string1_raw                   @ println(_t23);
	mov a2, v1
	bl printf(PLT)
	mov a1, v2                              @ return k;
	b ._J3Foo_3fooiiiiiE_exit
._J3Foo_3fooiiiiiE_exit:
	ldmfd sp!, {v1, v2, v3, pc}


.global _J3Foo_9do_divideiiE
.type _J3Foo_9do_divideiiE, %function
_J3Foo_9do_divideiiE:
	@ spills:  <none>
	@ assigns:   'a' = a2;    'b' = a3;  '_t0' = v1
	stmfd sp!, {v1, lr}
._J3Foo_9do_divideiiE_entry:
	stmfd sp!, {a2, a3}                     @ _t0 = a / b;; caller-save
	mov a1, a2
	mov a2, a3
	bl __divide_int
	mov v1, a1
	ldmfd sp!, {a2, a3}                     @ caller-restore
	mov a1, v1                              @ return _t0;
	b ._J3Foo_9do_divideiiE_exit
._J3Foo_9do_divideiiE_exit:
	ldmfd sp!, {v1, pc}



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
	@ takes two args: (the strings, duh) and returns 1 (the result, duh)
	stmfd sp!, {v1, v2, v3, v4, v5, fp, lr}
	mov v1, a1              @ save the string pointers into not-a1 and not-a2
	mov v2, a2
	ldr v4, [v1, #0]        @ load the lengths of the two strings
	ldr v5, [v2, #0]
	add v3, v4, v5          @ get the new length; a1 contains the +5 (for length + null term)
	add a2, v3, #5          @ v3 = the real length
	mov a1, #1
	bl calloc(PLT)          @ malloc some memory (memory in a1)
	mov fp, a1              @ save the return pointer
	str v3, [a1, #0]        @ store the length (v3)
	add a1, a1, #4          @ dst
	add a2, v1, #4          @ src - string 1
	mov a3, v4              @ len - string 1
	bl memcpy(PLT)          @ memcpy returns dst.
	add a1, fp, v4
	add a1, a1, #4
	add a2, v2, #4          @ src - string 2
	mov a3, v5              @ len - string 2
	bl memcpy(PLT)          @ copy the second string
	mov a1, fp              @ return value
	ldmfd sp!, {v1, v2, v3, v4, v5, fp, pc}


.global __divide_int
.type __divide_int, %function
__divide_int:
	@ takes two args: (dividend, divisor) and returns the quotient.
	stmfd sp!, {v1, v2, v3, v4, v5, fp, lr}
	movs v4, a1, asr #31    @ sign bit (1 if negative)
	rsbne a1, a1, #0        @ negate if the sign bit was set (ie. abs)
	movs v5, a2, asr #31    @ also sign bit
	rsbne a2, a2, #0        @ negate if the sign bit was set (ie. abs)
	mov v3, #0              @ store the quotient
.__divide_int_L1:
	subs a1, a1, a2         @ check if we're done
	blt .__divide_int_done
	add v3, v3, #1
	b .__divide_int_L1
.__divide_int_done:
	mov a1, v3
	eors v1, v4, v5         @ check if the sign bits are different
	rsbne a1, a1, #0        @ negate if so
	ldmfd sp!, {v1, v2, v3, v4, v5, fp, pc}


.global __readln_int
.type __readln_int, %function
__readln_int:
	@ takes no args and returns the int
	stmfd sp!, {lr}
	sub sp, sp, #4          @ save some stack space (scanf wants a pointer)
	mov a2, sp              @ a2 is the pointer argument
	ldr a1, =.string25_raw
	bl scanf(PLT)
	cmp a1, #1              @ if scanf returned < 1...
	bge .__readln_int_ok
	mov a1, #0              @ just return 0.
	b .__readln_int_exit
.__readln_int_ok:
	ldr a1, [sp, #0]        @ load the value from stack
.__readln_int_exit:
	add sp, sp, #4          @ restore the stack
	ldmfd sp!, {pc}


.global __readln_bool
.type __readln_bool, %function
__readln_bool:
	@ takes no args and returns the bool
	@ accepts: '1_' (anything starting with '1', or 'T_'/'t_' (anything starting with 't')
	@ anything else is false.
	stmfd sp!, {lr}
	sub sp, sp, #12          @ space for the buffer
	mov a2, sp
	ldr a1, =.string26_raw
	bl scanf(PLT)
	cmp a1, #1              @ if scanf returned < 1, then it's probably eof?
	blt .__readln_bool_false
	ldrb a1, [sp, #0]       @ otherwise, load the first char
	cmp a1, #49             @ 49 = '1'
	beq .__readln_bool_true
	cmp a1, #84             @ 84 = 'T'
	beq .__readln_bool_true
	cmp a1, #116            @ 116 = 't'
	beq .__readln_bool_true
.__readln_bool_false:
	mov a1, #0
	b .__readln_bool_exit
.__readln_bool_true:
	mov a1, #1
.__readln_bool_exit:
	add sp, sp, #12
	ldmfd sp!, {pc}


.global __readln_string
.type __readln_string, %function
__readln_string:
	@ takes no args and returns the string
	stmfd sp!, {v1, lr}
	mov a1, #256            @ allocate 256 for the actual string
	add a1, a1, #5          @ plus 4 (len) + 1 (null term)
	mov a2, #1
	bl calloc(PLT)
	mov v1, a1              @ save it
	add a1, a1, #4          @ skip the length (will write later)
	mov a2, #256            @ buffer len
	ldr a3, =stdin
	ldr a3, [a3, #0]
	bl fgets(PLT)           @ 'a1' is now the string
	cmp a1, #0
	beq .__readln_string_bar
	bl strlen(PLT)          @ get the length
	b .__readln_string_exit
.__readln_string_bar:
	mov a1, #0
.__readln_string_exit:
	str a1, [v1, #0]        @ write the length
	mov a1, v1              @ return
	ldmfd sp!, {v1, pc}

.data
.global stdin
.align 4
.string0:
    .word 13
.string0_raw:
    .asciz "read integer:"

.align 4
.string1:
    .word 3
.string1_raw:
    .asciz "%d\n"

.align 4
.string2:
    .word 12
.string2_raw:
    .asciz "read string:"

.align 4
.string3:
    .word 13
.string3_raw:
    .asciz "read boolean:"

.align 4
.string4:
    .word 5
.string4_raw:
    .asciz "false"

.align 4
.string5:
    .word 4
.string5_raw:
    .asciz "true"

.align 4
.string6:
    .word 23
.string6_raw:
    .asciz "should have 14 chars: '"

.align 4
.string7:
    .word 32
.string7_raw:
    .asciz "you should also see this 7 times"

.align 4
.string8:
    .word 27
.string8_raw:
    .asciz "you should see this 7 times"

.align 4
.string9:
    .word 1
.string9_raw:
    .asciz "x"

.align 4
.string10:
    .word 1
.string10_raw:
    .asciz "'"

.align 4
.string11:
    .word 38
.string11_raw:
    .asciz "                      -123456789abcde-"

.align 4
.string12:
    .word 8
.string12_raw:
    .asciz "omegalul"

.align 4
.string13:
    .word 4
.string13_raw:
    .asciz "kekw"

.align 4
.string14:
    .word 5
.string14_raw:
    .asciz "sadge"

.align 4
.string15:
    .word 7
.string15_raw:
    .asciz "poggers"

.align 4
.string16:
    .word 9
.string16_raw:
    .asciz "poggerino"

.align 4
.string17:
    .word 12
.string17_raw:
    .asciz "420 / 69 is:"

.align 4
.string18:
    .word 12
.string18_raw:
    .asciz "69 / 420 is:"

.align 4
.string19:
    .word 13
.string19_raw:
    .asciz "420 / -69 is:"

.align 4
.string20:
    .word 14
.string20_raw:
    .asciz "-420 / -69 is:"

.align 4
.string21:
    .word 13
.string21_raw:
    .asciz "-69 / 420 is:"

.align 4
.string22:
    .word 13
.string22_raw:
    .asciz "-420 / 69 is:"

.align 4
.string23:
    .word 10
.string23_raw:
    .asciz "0 / 69 is:"

.align 4
.string24:
    .word 12
.string24_raw:
    .asciz "69 / -69 is:"

.align 4
.string25:
    .word 2
.string25_raw:
    .asciz "%d"

.align 4
.string26:
    .word 3
.string26_raw:
    .asciz "%7s"

