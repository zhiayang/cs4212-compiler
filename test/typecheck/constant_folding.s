.global main_dummy
.type main_dummy, %function
main_dummy:
	stmfd sp!, {v1, fp, lr}
	mov fp, sp
	sub sp, sp, #32
	@ prologue

.main_dummy_entry:
	@ a = 9490;
	mov a2, #9490
	@ b = -2987843;
	mov a3, #-2987843
	@ c = 3805066;
	mov a4, #3805066
	@ d = 3660264;
	mov v1, #3660264
	@ e = 1;
	mov v2, #1
	@ f = -1;
	mov v3, #-1
	@ x = true;
	mov v4, #1
	@ y = true;
	mov v5, #1
	@ return;
	b .main_dummy_epilogue

	@ epilogue
.main_dummy_epilogue:
	add sp, sp, #32
	ldmfd sp!, {v1, fp, pc}
	

	
.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	bl main_dummy

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4

