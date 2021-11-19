// 03_cse.j

class Main
{
	Void main()
	{
		Int a; Int b; Int c; Int d; Int e; Int f; Int g; Int h; Int i; Int j; Int k; Int l; Int m;
		Int n; Int o; Int p; Int q; Int r; Int s; Int t; Int u; Int v; Int w; Int x; Int y; Int z;

		Int aa; Int bb; Int cc; Int dd; Int ee; Int ff; Int gg; Int hh; Int ii; Int jj; Int kk; Int ll; Int mm;
		Int nn; Int oo; Int pp; Int qq; Int rr; Int ss; Int tt; Int uu; Int vv; Int ww; Int xx; Int yy; Int zz;

		a = 1;
		b = a + 2;
		c = b + 3;
		d = c + 4;
		e = d + 5;
		f = e + 6;

		g = a + b + c + d + e + f;

		h = 100;

		ee = a + b + c + d + e + f + g + h;

		// if we change the value of 'h' here, CSE should be impeded, but only at the final step
		h = 101;
		ff = a + b + c + d + e + f + g + h;

		// constant propagation should be strong enough to eliminate both the branch,
		// and subsequently propagate the store inside.

		if(69 < h) { h = 200; } else { h = 300; println("you should not see this"); }

		gg = a + b + c + d + e + f + g + h;

		xx = a + b + c + d + e + f + g;

		// every single one of these should be constants.
		println(f);
		println(g);
		println(ee);
		println(ff);
		println(gg);

		// this should kill any propagation of 'h'
		while(h > 100) { h = h - 50; }

		// this also kills propagation of g; it kills itself in the loop (which is a predecessor of the condition)
		while(g + 10000 < g) { println("this should not happen"); g = 100; }

		yy = a + b + c + d + e + f + g;

		println(h);
		println(gg);
		println(xx);
		println(yy);


		// test side-effect functions in a separate function
		new Foo().test_effects();
	}
}

class Foo
{
	Int effect1()
	{
		println("you should see this once");
		return 420;
	}

	Int effect2()
	{
		println("you should see this twice");
		return 69;
	}


	Void test_effects()
	{
		Int a; Int b; Int c; Int d; Int e; Int f; Int g; Int h; Int i; Int j; Int k; Int l; Int m;
		Int n; Int o; Int p; Int q; Int r; Int s; Int t; Int u; Int v; Int w; Int x; Int y; Int z;

		Int aa; Int bb; Int cc; Int dd; Int ee; Int ff; Int gg; Int hh; Int ii; Int jj; Int kk; Int ll; Int mm;
		Int nn; Int oo; Int pp; Int qq; Int rr; Int ss; Int tt; Int uu; Int vv; Int ww; Int xx; Int yy; Int zz;

		a = 1;
		b = a + 2;
		c = b + 3;
		d = c + 4;
		e = d + 5;
		f = e + 6;
		g = a + b + c + d + e + f;
		h = 100;

		// GCSE cannot eliminate the two function calls, though the front part will be shared.
		// and in fact will be constant-folded to a single constant.
		aa = b + c + d + e + f + g + effect2();
		bb = b + c + d + e + f + g + effect2();

		println(aa);
		println(bb);


		// due to the associativity and the way expressions are broken up, CSE cannot help here
		// we also don't know how to reassociate expressions, so constant folding is blocked too.
		cc = effect2() + a + b + c + d + e + f + g + h;
		dd = effect2() + a + b + c + d + e + f + g + h;

		println(cc);
		println(dd);
	}
}
