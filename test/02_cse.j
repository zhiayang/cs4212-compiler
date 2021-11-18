// 02_cse.j

class Main
{
	Void main()
	{
		Int foo;
		Int bar;
		Int baz;
		Int aaa;
		Int bbb;
		Int ccc;
		Int ddd;
		Int eee;
		Int fff;
		Int ggg;
		Int hhh;
		Int iii;
		Int a;
		Int b;
		Int c;
		Int d;
		Int e;
		Int f;
		Int g;
		Int h;
		Int x;
		Foo foooo;

		foo = 69;
		bar = 420;
		baz = 1234;
		aaa = 100;
		bbb = 200;
		ccc = 300;
		ddd = 400;
		eee = 500;
		fff = 600;
		ggg = 700;
		hhh = 800;
		iii = 900;

		// this will result in _t0 = foo + bar; x = _t0 + baz.
		// this should let is CSE away 'a'
		x = foo + bar + baz;

		if(1 < 69) { println("kekw"); }
		else       { println("sadge"); }

		a = foo + bar;

		if(69 > 420) { println("what"); foo = 420; }
		else         { println("phew"); }

		// this *should* also be optimised away, because we would have
		// determined that the true case of the if is never possible.
		b = foo + bar;

		if(420 > 69) { println("cool"); foo = 100; }
		else         { println("asdf"); }

		// this one cannot be CSE-ed away
		c = foo + bar;

		println(a);
		println(b);
		println(c);
		println(x);


		// things with side effects cannot be CSE-ed away
		d = aaa + foooo.side_effect() + bbb;
		e = aaa + foooo.side_effect() + bbb;

		println(d);
		println(e);

		// even though these are complex, multiple passes of CSE and copy-propagation
		// should eliminate everything.
		f = ccc + ddd + eee + fff + ggg + hhh + iii;
		println(f);

		g = ccc + ddd + eee + fff + ggg + hhh + iii;
		println(g);

		// due to the associativity, if the first one (ccc) is assigned, nothing should be optimised:
		ccc = 1;
		h = ccc + ddd + eee + fff + ggg + hhh + iii;
		println(h);
	}
}

class Foo
{
	Int side_effect()
	{
		println("you should see this twice");
		return 69;
	}
}
